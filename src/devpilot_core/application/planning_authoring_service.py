from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.planning.backlog_workbench import BacklogWorkbench
from devpilot_core.planning.roadmap_workbench import RoadmapWorkbench
from devpilot_core.planning.service import PlanningPolicyError
from devpilot_core.planning.sprint_planner import SprintPlanner

from .planning_candidate_provider import DeterministicPlanningCandidateProvider, PlanningCandidateProvider
from .ui_workspace_context import UiWorkspaceContextResolver

_REQUIREMENT_ID = re.compile(r"^(?:RF|RNF|REQ)-[A-Z0-9][A-Z0-9._-]*$", re.IGNORECASE)
_CAP = re.compile(r"CAP-[A-Z0-9][A-Z0-9._-]*", re.IGNORECASE)
_ADR = re.compile(r"ADR-[A-Z0-9][A-Z0-9._-]*", re.IGNORECASE)
_RISK = re.compile(r"(?:SEC|RISK)-[A-Z0-9][A-Z0-9._-]*", re.IGNORECASE)
_TEST = re.compile(r"(?:TEST|TI)-[A-Z0-9][A-Z0-9._-]*", re.IGNORECASE)


class PlanningAuthoringApplicationService:
    """Bounded C-04 planning authoring bridge.

    This service turns the already-FROZEN project authorities into runtime-only
    Roadmap/Backlog/Sprint DRAFT candidates.  It grants no source-write, model,
    network or approval authority.  Existing Workbench review/approval/freeze
    contracts remain authoritative.
    """

    def __init__(self, root: Path, *, context_resolver: UiWorkspaceContextResolver, candidate_provider: PlanningCandidateProvider | None = None) -> None:
        self.root = Path(root).resolve()
        self.context_resolver = context_resolver
        self.candidate_provider = candidate_provider or DeterministicPlanningCandidateProvider()

    def status(self, *, effective_roles: list[str]) -> CommandResult:
        return self._call("planning.authoring.status", lambda: self._status_payload(effective_roles=effective_roles))

    def generate_roadmap(self, *, actor_id: str, actor_role: str) -> CommandResult:
        return self._call("planning.roadmap.generate", lambda: self._generate_roadmap(actor_id=actor_id, actor_role=actor_role))

    def derive_backlog(self, *, actor_id: str, actor_role: str) -> CommandResult:
        return self._call("planning.backlog.derive", lambda: self._derive_backlog(actor_id=actor_id, actor_role=actor_role))

    def derive_sprint(self, *, actor_id: str, actor_role: str, capacity_limit: int = 8) -> CommandResult:
        return self._call("planning.sprint.derive", lambda: self._derive_sprint(actor_id=actor_id, actor_role=actor_role, capacity_limit=capacity_limit))


    def roadmap_binding(self) -> dict[str, Any]:
        workspace_root, workspace_id = self._workspace()
        self._assert_pre_code_ready(workspace_id)
        return self._authority_snapshot(workspace_root, workspace_id)

    def backlog_binding(self) -> dict[str, Any]:
        workspace_root, workspace_id = self._workspace()
        self._assert_pre_code_ready(workspace_id)
        snapshot = self._authority_snapshot(workspace_root, workspace_id)
        roadmap = self._load_json(self._runtime_paths(workspace_root, workspace_id)["roadmap"])
        if not roadmap or roadmap.get("lifecycle") != "FROZEN":
            raise PlanningPolicyError("BACKLOG_ROADMAP_FROZEN_REQUIRED", "Backlog authoring is locked until Roadmap is FROZEN.")
        planning_state = roadmap.get("planning_state") if isinstance(roadmap.get("planning_state"), dict) else {}
        milestone_ids = [str(x.get("id") or "") for x in planning_state.get("milestones") or [] if isinstance(x, dict) and x.get("id")]
        return {**snapshot, "roadmap_record": roadmap, "roadmap_milestone_ids": milestone_ids}

    def sprint_binding(self) -> dict[str, Any]:
        workspace_root, workspace_id = self._workspace()
        self._assert_pre_code_ready(workspace_id)
        snapshot = self._authority_snapshot(workspace_root, workspace_id)
        backlog = self._load_json(self._runtime_paths(workspace_root, workspace_id)["backlog"])
        if not backlog or backlog.get("lifecycle") != "FROZEN":
            raise PlanningPolicyError("SPRINT_BACKLOG_FROZEN_REQUIRED", "Sprint authoring is locked until Backlog is FROZEN.")
        body = backlog.get("backlog") if isinstance(backlog.get("backlog"), dict) else {}
        return {**snapshot, "backlog_record": backlog, "backlog": body, "dependencies": list(body.get("dependencies") or [])}
    def authorities(self) -> dict[str, Any]:
        workspace_root, workspace_id = self._workspace()
        self._assert_pre_code_ready(workspace_id)
        return self._authority_snapshot(workspace_root, workspace_id)

    def _workspace(self) -> tuple[Path, str]:
        context = self.context_resolver.resolve()
        if context.configured and not context.valid:
            raise PlanningPolicyError("PLANNING_WORKSPACE_CONTEXT_BLOCK", "Configured project workspace context is invalid.")
        workspace_root = Path(context.effective_workspace_root).resolve()
        workspace_id = str(context.active_workspace_id or workspace_root.name)
        return workspace_root, workspace_id

    def _assert_pre_code_ready(self, workspace_id: str) -> None:
        path = self.root / "outputs" / "pre_code_wizard" / "gsdlc_05_e" / workspace_id / "state.json"
        if not path.is_file():
            raise PlanningPolicyError("PLANNING_PRE_CODE_STATE_REQUIRED", "Planning requires a PRE_CODE_READY runtime state.")
        state = json.loads(path.read_text(encoding="utf-8"))
        stages = state.get("stages") if isinstance(state.get("stages"), dict) else {}
        required = ("product-vision", "scope", "requirements", "architecture", "security", "test-strategy", "traceability")
        if str(state.get("status") or "") != "PRE_CODE_READY" or any(str((stages.get(x) or {}).get("status") or "") != "FROZEN" for x in required):
            raise PlanningPolicyError("PLANNING_PRE_CODE_READY_REQUIRED", "Planning authoring requires PRE_CODE_READY with all seven pre-code stages FROZEN.")

    @staticmethod
    def _read(path: Path) -> str:
        if not path.is_file():
            raise PlanningPolicyError("PLANNING_AUTHORITY_SOURCE_MISSING", f"Required authority source is missing: {path.as_posix()}")
        return path.read_text(encoding="utf-8")

    def _authority_snapshot(self, workspace_root: Path, workspace_id: str) -> dict[str, Any]:
        req_text = self._read(workspace_root / "docs" / "01_requirements" / "requirements_specification.md")
        scope_text = self._read(workspace_root / "docs" / "00_product" / "mvp_scope.md")
        trace_text = self._read(workspace_root / "docs" / "01_requirements" / "traceability_matrix.md")
        security_text = self._read(workspace_root / "docs" / "03_security" / "security_threat_model.md")
        test_text = self._read(workspace_root / "docs" / "04_quality" / "test_strategy.md")
        adr_root = workspace_root / "docs" / "02_architecture" / "adrs"

        headings = list(re.finditer(r"(?ms)^###\s+([^\s]+)\s*\n(.*?)(?=^###\s+[^\s]+\s*$|^##\s|\Z)", req_text))
        requirements: list[dict[str, Any]] = []
        for match in headings:
            requirement_id = str(match.group(1)).strip().upper()
            if not _REQUIREMENT_ID.fullmatch(requirement_id):
                continue
            body = match.group(2)
            requirements.append({
                "id": requirement_id,
                "statement": self._field(body, "Statement"),
                "source": self._field(body, "Fuente") or "UNMAPPED",
                "acceptance_criterion": self._field(body, "Criterio de aceptación"),
                "priority": self._field(body, "Prioridad") or "MUST",
            })
        if not requirements:
            raise PlanningPolicyError(
                "PLANNING_REQUIREMENTS_PARSE_BLOCK",
                "No supported Requirement IDs (RF-*, RNF-* or REQ-*) could be parsed from the FROZEN Requirements artifact.",
            )
        requirement_ids = [x["id"] for x in requirements]
        requirement_set = set(requirement_ids)

        capabilities: dict[str, str] = {}
        for line in scope_text.splitlines():
            match = re.match(r"^-\s*(CAP-[A-Z0-9][A-Z0-9._-]*):\s*(.+?)\s*$", line, flags=re.IGNORECASE)
            if match:
                capabilities[match.group(1).upper()] = match.group(2).rstrip(".")

        trace: dict[str, dict[str, list[str]]] = {}
        for line in trace_text.splitlines():
            if not line.lstrip().startswith("|"):
                continue
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(cells) < 6:
                continue
            requirement_id = cells[0].strip().upper()
            if requirement_id not in requirement_set:
                continue
            trace[requirement_id] = {
                "capabilities": sorted({x.upper() for x in _CAP.findall(cells[1])}),
                "adrs": sorted({x.upper() for x in _ADR.findall(cells[3])}),
                "risks": sorted({x.upper() for x in _RISK.findall(cells[4])}),
                "test_intents": sorted({x.upper() for x in _TEST.findall(cells[5])}),
            }

        traced_adrs = {x for row in trace.values() for x in row.get("adrs", [])}
        traced_risks = {x for row in trace.values() for x in row.get("risks", [])}
        traced_tests = {x for row in trace.values() for x in row.get("test_intents", [])}
        file_adrs = {x.upper() for path in adr_root.glob("ADR-*.md") for x in _ADR.findall(path.name)} if adr_root.is_dir() else set()
        adr_ids = sorted(file_adrs | traced_adrs)
        risk_ids = sorted({x.upper() for x in _RISK.findall(security_text)} | traced_risks)
        test_ids = sorted({x.upper() for x in _TEST.findall(test_text)} | traced_tests)
        mapped_risks = sorted(traced_risks)

        return {
            "workspace_id": workspace_id,
            "requirements": requirements,
            "requirement_ids": requirement_ids,
            "capabilities": capabilities,
            "traceability": trace,
            "known_adr_ids": adr_ids,
            "known_risk_ids": risk_ids,
            "required_roadmap_risk_ids": mapped_risks,
            "known_test_intent_ids": test_ids,
            "source_paths": [
                "docs/00_product/mvp_scope.md",
                "docs/01_requirements/requirements_specification.md",
                "docs/01_requirements/traceability_matrix.md",
                "docs/02_architecture/adrs/",
                "docs/03_security/security_threat_model.md",
                "docs/04_quality/test_strategy.md",
            ],
            "network_used": False,
            "external_api_used": False,
            "model_execution_used": False,
            "agent_execution_used": False,
        }

    @staticmethod
    def _field(body: str, label: str) -> str:
        match = re.search(rf"(?m)^-\s*\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$", body)
        return match.group(1).strip().rstrip(".") if match else ""

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any] | None:
        if not path.is_file():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None

    def _runtime_paths(self, workspace_root: Path, workspace_id: str) -> dict[str, Path]:
        return {
            "roadmap": workspace_root / "outputs" / "planning" / "gsdlc_08_b" / workspace_id / "roadmap_workbench.json",
            "backlog": workspace_root / "outputs" / "planning" / "gsdlc_08_c" / workspace_id / "backlog_workbench.json",
            "sprint": workspace_root / "outputs" / "planning" / "gsdlc_08_d" / workspace_id / "sprint_planner.json",
        }

    def _status_payload(self, *, effective_roles: list[str]) -> dict[str, Any]:
        workspace_root, workspace_id = self._workspace()
        snapshot = self._authority_snapshot(workspace_root, workspace_id)
        pre_code_ready = True
        try:
            self._assert_pre_code_ready(workspace_id)
        except PlanningPolicyError:
            pre_code_ready = False
        paths = self._runtime_paths(workspace_root, workspace_id)
        roadmap = self._load_json(paths["roadmap"])
        backlog = self._load_json(paths["backlog"])
        sprint = self._load_json(paths["sprint"])
        roadmap_frozen = bool(roadmap and roadmap.get("lifecycle") == "FROZEN")
        backlog_frozen = bool(backlog and backlog.get("lifecycle") == "FROZEN")
        sprint_frozen = bool(sprint and sprint.get("lifecycle") == "FROZEN")
        roles = sorted({str(x).strip().lower() for x in effective_roles if str(x).strip()})
        templates: dict[str, Any] = {"roadmap": self.candidate_provider.generate_roadmap(snapshot), "backlog": None, "sprint": None}
        if roadmap_frozen and roadmap:
            templates["backlog"] = self.candidate_provider.derive_backlog(snapshot, roadmap)
        if backlog_frozen and backlog:
            templates["sprint"] = self.candidate_provider.derive_sprint(snapshot, backlog, capacity_limit=8)
        return {
            "workspace_id": workspace_id,
            "pre_code_ready": pre_code_ready,
            "authority": snapshot,
            "provider": self.candidate_provider.projection(),
            "templates": templates,
            "lifecycle": {
                "roadmap": str((roadmap or {}).get("lifecycle") or "MISSING"),
                "backlog": str((backlog or {}).get("lifecycle") or "MISSING"),
                "sprint": str((sprint or {}).get("lifecycle") or "MISSING"),
            },
            "availability": {
                "roadmap": {
                    "devpilot_local": pre_code_ready,
                    "manual": pre_code_ready,
                    "import": pre_code_ready,
                    "agent": False,
                    "agent_reason": "Agent-assisted planning authoring is not executable in the current authority; no model/agent runtime is bound to this surface.",
                },
                "backlog": {
                    "devpilot_local": roadmap_frozen,
                    "manual": roadmap_frozen,
                    "agent": False,
                    "blocked_reason": None if roadmap_frozen else "Roadmap must be FROZEN first.",
                },
                "sprint": {
                    "devpilot_local": backlog_frozen,
                    "manual": backlog_frozen,
                    "blocked_reason": None if backlog_frozen else "Backlog must be FROZEN first.",
                },
            },
            "recommended_next": "roadmap" if not roadmap_frozen else ("backlog" if not backlog_frozen else ("sprint" if not sprint_frozen else "story-code")),
            "effective_roles": roles,
            "runtime_only": True,
            "source_mutations_performed": False,
            "network_used": False,
            "external_api_used": False,
        }

    def _generate_roadmap(self, *, actor_id: str, actor_role: str) -> dict[str, Any]:
        workspace_root, workspace_id = self._workspace()
        self._assert_pre_code_ready(workspace_id)
        snapshot = self._authority_snapshot(workspace_root, workspace_id)
        wb = RoadmapWorkbench(workspace_root, workspace_id=workspace_id)
        return wb.propose(
            mode="DEVPL_LOCAL",
            roadmap=self.candidate_provider.generate_roadmap(snapshot),
            required_requirement_ids=snapshot["requirement_ids"],
            required_risk_ids=snapshot["required_roadmap_risk_ids"],
            actor_id=actor_id,
            actor_role=actor_role,
            source_label=f"{self.candidate_provider.provider_id}:{self.candidate_provider.strategy_id}",
        )

    def _derive_backlog(self, *, actor_id: str, actor_role: str) -> dict[str, Any]:
        workspace_root, workspace_id = self._workspace()
        self._assert_pre_code_ready(workspace_id)
        snapshot = self._authority_snapshot(workspace_root, workspace_id)
        roadmap_path = self._runtime_paths(workspace_root, workspace_id)["roadmap"]
        roadmap = self._load_json(roadmap_path)
        if not roadmap or roadmap.get("lifecycle") != "FROZEN":
            raise PlanningPolicyError("BACKLOG_ROADMAP_FROZEN_REQUIRED", "Backlog authoring is locked until Roadmap is FROZEN.")
        planning_state = roadmap.get("planning_state") if isinstance(roadmap.get("planning_state"), dict) else {}
        milestone_ids = [str(x.get("id") or "") for x in planning_state.get("milestones") or [] if isinstance(x, dict) and x.get("id")]
        wb = BacklogWorkbench(workspace_root, workspace_id=workspace_id)
        return wb.propose(
            mode="DERIVED",
            backlog=self.candidate_provider.derive_backlog(snapshot, roadmap),
            required_requirement_ids=snapshot["requirement_ids"],
            roadmap_milestone_ids=milestone_ids,
            known_adr_ids=snapshot["known_adr_ids"],
            known_risk_ids=snapshot["known_risk_ids"],
            known_test_intent_ids=snapshot["known_test_intent_ids"],
            actor_id=actor_id,
            actor_role=actor_role,
            source_label=f"{self.candidate_provider.provider_id}:{self.candidate_provider.strategy_id}",
        )

    def _derive_sprint(self, *, actor_id: str, actor_role: str, capacity_limit: int) -> dict[str, Any]:
        workspace_root, workspace_id = self._workspace()
        self._assert_pre_code_ready(workspace_id)
        snapshot = self._authority_snapshot(workspace_root, workspace_id)
        backlog_path = self._runtime_paths(workspace_root, workspace_id)["backlog"]
        backlog_record = self._load_json(backlog_path)
        if not backlog_record or backlog_record.get("lifecycle") != "FROZEN":
            raise PlanningPolicyError("SPRINT_BACKLOG_FROZEN_REQUIRED", "Sprint authoring is locked until Backlog is FROZEN.")
        backlog = backlog_record.get("backlog") if isinstance(backlog_record.get("backlog"), dict) else {}
        wb = SprintPlanner(workspace_root, workspace_id=workspace_id)
        return wb.propose(
            sprint_plan=self.candidate_provider.derive_sprint(snapshot, backlog_record, capacity_limit=capacity_limit),
            backlog=backlog,
            dependencies=list(backlog.get("dependencies") or []),
            actor_id=actor_id,
            actor_role=actor_role,
        )

    def _call(self, operation: str, fn) -> CommandResult:
        try:
            data = fn()
            return CommandResult(operation, True, ExitCode.PASS, f"{operation} PASS", data={"planning_authoring": data}, findings=[])
        except PlanningPolicyError as exc:
            return CommandResult(operation, False, ExitCode.BLOCK, str(exc), data={}, findings=[Finding(exc.code, str(exc), Severity.BLOCK)])
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return CommandResult(operation, False, ExitCode.BLOCK, str(exc), data={}, findings=[Finding("PLANNING_AUTHORING_INPUT_INVALID", str(exc), Severity.BLOCK)])
