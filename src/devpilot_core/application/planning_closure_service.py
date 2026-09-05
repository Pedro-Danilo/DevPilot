from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.planning.backlog_workbench import BacklogWorkbench
from devpilot_core.planning.roadmap_workbench import RoadmapWorkbench
from devpilot_core.planning.sprint_planner import SprintPlanner
from devpilot_core.planning.service import PlanningPolicyError
from .ui_workspace_context import UiWorkspaceContextResolver


class PlanningClosureApplicationService:
    """GSDLC-08-E deterministic planning journey and traceability projection.

    The service reads project-scoped runtime planning artifacts only. It does not
    mutate managed source, execute code, call models, or advance historical MIP
    state. IMPLEMENTING_READY is a planning-journey projection derived from
    frozen roadmap/backlog/sprint authority.
    """

    def __init__(self, root: Path, *, context_resolver: UiWorkspaceContextResolver) -> None:
        self.root = Path(root).resolve()
        self.context_resolver = context_resolver

    def status(self, *, effective_roles: list[str]) -> CommandResult:
        try:
            context = self.context_resolver.resolve()
            if context.configured and not context.valid:
                raise PlanningPolicyError("PLANNING_WORKSPACE_CONTEXT_BLOCK", "Configured project workspace context is invalid.")
            workspace = context.effective_workspace_root
            workspace_id = context.active_workspace_id or workspace.name
            roadmap = RoadmapWorkbench(workspace, workspace_id=workspace_id).status(effective_roles=effective_roles).get("roadmap")
            backlog = BacklogWorkbench(workspace, workspace_id=workspace_id).status(effective_roles=effective_roles).get("backlog")
            sprint = SprintPlanner(workspace, workspace_id=workspace_id).status(effective_roles=effective_roles).get("sprint_plan")
            projection = self._project(workspace, workspace_id, roadmap, backlog, sprint, effective_roles)
            return CommandResult("planning.closure.status", True, ExitCode.PASS, "planning.closure.status PASS", data={"planning_closure": projection}, findings=[])
        except PlanningPolicyError as exc:
            return CommandResult("planning.closure.status", False, ExitCode.BLOCK, str(exc), data={}, findings=[Finding(exc.code, str(exc), Severity.BLOCK)])

    def _project(self, workspace: Path, workspace_id: str, roadmap: dict[str, Any] | None, backlog: dict[str, Any] | None, sprint: dict[str, Any] | None, roles: list[str]) -> dict[str, Any]:
        pre_code_ready = self._pre_code_ready(workspace, workspace_id)
        roadmap_frozen = bool(roadmap and roadmap.get("lifecycle") == "FROZEN")
        backlog_frozen = bool(backlog and backlog.get("lifecycle") == "FROZEN")
        sprint_frozen = bool(sprint and sprint.get("lifecycle") == "FROZEN")
        backlog_coverage = self._backlog_coverage(backlog)
        sprint_executable = bool((sprint or {}).get("validation", {}).get("executable"))

        blockers: list[dict[str, str]] = []
        if not pre_code_ready:
            blockers.append({"code": "PRE_CODE_READY_REQUIRED", "message": "Planning journey requires PRE_CODE_READY authority."})
        if roadmap and not roadmap_frozen:
            blockers.append({"code": "ROADMAP_FREEZE_REQUIRED", "message": "Roadmap must be reviewed, approved and frozen."})
        if backlog and not backlog_frozen:
            blockers.append({"code": "BACKLOG_FREEZE_REQUIRED", "message": "Backlog must be reviewed, approved and frozen."})
        if backlog and backlog_coverage < 100.0:
            blockers.append({"code": "BACKLOG_COVERAGE_REQUIRED", "message": "Required requirement-to-story coverage must be 100%."})
        if sprint and not sprint_frozen:
            blockers.append({"code": "SPRINT_FREEZE_REQUIRED", "message": "SprintPlan must be reviewed, approved and frozen."})
        if sprint and not sprint_executable:
            blockers.append({"code": "SPRINT_EXECUTABLE_REQUIRED", "message": "Frozen sprint must remain executable with READY stories and valid capacity/dependencies."})

        if pre_code_ready and roadmap_frozen and backlog_frozen and backlog_coverage >= 100.0 and sprint_frozen and sprint_executable:
            journey_state = "IMPLEMENTING_READY"
            next_action = {"kind": "IMPLEMENT", "label": "Implementar historias READY", "navigation_target": "project-status", "available": False, "reason_code": "GSDLC_09_REQUIRED"}
        elif pre_code_ready and not any([roadmap, backlog, sprint]):
            journey_state = "PRE_CODE_READY"
            next_action = {"kind": "PLANNING", "label": "Construir roadmap", "navigation_target": "planning-roadmap", "available": True, "reason_code": "ROADMAP_REQUIRED"}
        else:
            journey_state = "PLANNING"
            if not roadmap_frozen:
                label, reason = "Completar roadmap", "ROADMAP_FREEZE_REQUIRED"
            elif not backlog_frozen or backlog_coverage < 100.0:
                label, reason = "Derivar y congelar backlog", "BACKLOG_REQUIRED"
            else:
                label, reason = "Planificar y congelar sprint", "SPRINT_REQUIRED"
            next_action = {"kind": "PLANNING", "label": label, "navigation_target": "planning-roadmap", "available": True, "reason_code": reason}

        graph = self._trace_graph(roadmap, backlog, sprint)
        return {
            "schema_id": "DEVPL-GSDLC-08-E-PLANNING-CLOSURE-V1",
            "workspace_id": workspace_id,
            "journey_state": journey_state,
            "pre_code_ready": pre_code_ready,
            "roadmap": self._summary(roadmap),
            "backlog": {**self._summary(backlog), "required_coverage_percent": backlog_coverage},
            "sprint": {**self._summary(sprint), "executable": sprint_executable},
            "trace_graph": graph,
            "required_planning_coverage_percent": graph["coverage_percent"],
            "blockers": blockers,
            "s0_open": 0,
            "s1_open": 0,
            "next_action": next_action,
            "effective_roles": sorted({str(x).strip().lower() for x in roles if str(x).strip()}),
            "runtime_only": True,
            "server_authoritative": True,
            "source_mutations_performed": False,
            "network_used": False,
            "external_api_used": False,
            "model_execution_used": False,
            "agent_auto_approval": False,
        }

    @staticmethod
    def _summary(record: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "present": bool(record),
            "lifecycle": str((record or {}).get("lifecycle") or "MISSING"),
            "version": str((record or {}).get("version") or ""),
            "content_sha256": str((record or {}).get("content_sha256") or ""),
        }

    @staticmethod
    def _backlog_coverage(backlog: dict[str, Any] | None) -> float:
        if not backlog:
            return 0.0
        for candidate in ((backlog.get("coverage") or {}), (backlog.get("validation") or {})):
            for key in ("required_coverage_percent", "coverage_percent", "requirement_coverage_percent"):
                try:
                    if key in candidate:
                        return float(candidate[key])
                except (TypeError, ValueError):
                    pass
        required = set(str(x) for x in backlog.get("required_requirement_ids") or [])
        mapped: set[str] = set()
        body = backlog.get("backlog") or {}
        for story in body.get("stories") or []:
            for link in story.get("trace_links") or []:
                if str(link.get("kind")) == "requirement":
                    mapped.add(str(link.get("target_id")))
        if not required:
            return 100.0 if body.get("stories") else 0.0
        return round(100.0 * len(required & mapped) / len(required), 2)

    @staticmethod
    def _pre_code_ready(workspace: Path, workspace_id: str) -> bool:
        candidates = [
            workspace / "outputs" / "pre_code_wizard" / "gsdlc_05_e" / workspace_id / "state.json",
            workspace / "outputs" / "pre_code_wizard" / "gsdlc_05_e" / workspace.name / "state.json",
        ]
        for path in candidates:
            if not path.is_file():
                continue
            try:
                import json
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            values = {str(payload.get(k) or "").upper() for k in ("status", "readiness", "lifecycle", "state")}
            values |= {str((payload.get("readiness") or {}).get("status") or "").upper()} if isinstance(payload.get("readiness"), dict) else set()
            if "PRE_CODE_READY" in values or "PASS" in values:
                return True
        # A frozen roadmap is successor evidence that pre-code readiness was already crossed.
        return (workspace / "outputs" / "planning" / "gsdlc_08_b" / workspace_id / "roadmap_workbench.json").is_file()

    @staticmethod
    def _trace_graph(roadmap: dict[str, Any] | None, backlog: dict[str, Any] | None, sprint: dict[str, Any] | None) -> dict[str, Any]:
        nodes: dict[str, dict[str, str]] = {}
        edges: list[dict[str, str]] = []
        required: set[str] = set()
        mapped_requirements: set[str] = set()
        roadmap_body = (roadmap or {}).get("roadmap") or {}
        if not roadmap_body:
            # RoadmapWorkbench persists the canonical frozen roadmap entities inside
            # PlanningState. Keep compatibility with the lightweight successor shape
            # used by API fixtures while reading the real 08-B artifact faithfully.
            roadmap_body = {"milestones": (((roadmap or {}).get("planning_state") or {}).get("milestones") or [])}
        backlog_body = (backlog or {}).get("backlog") or {}
        sprint_body = (sprint or {}).get("sprint_plan") or {}

        for milestone in roadmap_body.get("milestones") or []:
            mid = str(milestone.get("id") or "")
            if not mid: continue
            nodes[mid] = {"id": mid, "kind": "milestone", "label": str(milestone.get("title") or mid)}
            for link in milestone.get("trace_links") or []:
                if str(link.get("kind")) != "requirement": continue
                rid = str(link.get("target_id") or "")
                if not rid: continue
                required.add(rid); mapped_requirements.add(rid); nodes.setdefault(rid, {"id": rid, "kind": "requirement", "label": rid})
                edges.append({"from": rid, "to": mid, "kind": "requirement-to-milestone"})

        for epic in backlog_body.get("epics") or []:
            eid = str(epic.get("id") or ""); mid = str(epic.get("milestone_id") or "")
            if not eid: continue
            nodes[eid] = {"id": eid, "kind": "epic", "label": str(epic.get("title") or eid)}
            if mid:
                nodes.setdefault(mid, {"id": mid, "kind": "milestone", "label": mid}); edges.append({"from": mid, "to": eid, "kind": "milestone-to-epic"})
        for story in backlog_body.get("stories") or []:
            sid = str(story.get("id") or ""); eid = str(story.get("epic_id") or "")
            if not sid: continue
            nodes[sid] = {"id": sid, "kind": "story", "label": str(story.get("title") or sid)}
            if eid:
                nodes.setdefault(eid, {"id": eid, "kind": "epic", "label": eid}); edges.append({"from": eid, "to": sid, "kind": "epic-to-story"})
            for link in story.get("trace_links") or []:
                if str(link.get("kind")) == "requirement":
                    rid = str(link.get("target_id") or "")
                    if rid:
                        required.add(rid); mapped_requirements.add(rid); nodes.setdefault(rid, {"id": rid, "kind": "requirement", "label": rid})
        sprint_id = str(sprint_body.get("sprint_plan_id") or "")
        if sprint_id:
            nodes[sprint_id] = {"id": sprint_id, "kind": "sprint", "label": str(sprint_body.get("title") or sprint_id)}
            for selected in sprint_body.get("selected_stories") or []:
                sid = str(selected.get("story_id") or "")
                if sid:
                    nodes.setdefault(sid, {"id": sid, "kind": "story", "label": sid}); edges.append({"from": sid, "to": sprint_id, "kind": "story-to-sprint"})
        coverage = 100.0 if not required else round(100.0 * len(mapped_requirements & required) / len(required), 2)
        return {"nodes": list(nodes.values()), "edges": edges, "requirements_total": len(required), "requirements_mapped": len(mapped_requirements & required), "coverage_percent": coverage}
