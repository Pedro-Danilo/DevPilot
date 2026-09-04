from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .models import Dependency, DependencyKind, Milestone, PlanningLifecycle, PlanningState, TraceKind, TraceLink
from .service import PlanningPolicyError, PlanningStateService

AUTHORING_MODES = frozenset({"MANUAL", "IMPORT", "AGENT"})
AUTHOR_ROLES = frozenset({"owner", "product-owner", "architect", "developer"})
APPROVER_ROLES = frozenset({"owner", "product-owner"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_sha(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _safe_workspace_id(value: str) -> str:
    raw = str(value or "platform").strip() or "platform"
    normalized = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in raw)[:96].strip("-")
    return normalized or "platform"


@dataclass(frozen=True)
class RoadmapFinding:
    code: str
    severity: str
    message: str
    subject: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "severity": self.severity, "message": self.message, "subject": self.subject}


class RoadmapWorkbench:
    """GSDLC-08-B runtime-only governed roadmap authoring.

    DRAFT/review state lives under outputs and never mutates managed source.
    All authoring modes normalize into the same PlanningState contract. The
    AGENT route accepts structured output only; it does not grant tool, model,
    network or approval authority. Human approval/freeze stays server-side.
    """

    def __init__(self, workspace_root: Path, *, workspace_id: str = "platform") -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_id = _safe_workspace_id(workspace_id)
        self.runtime_root = self.workspace_root / "outputs" / "planning" / "gsdlc_08_b" / self.workspace_id
        self.state_path = self.runtime_root / "roadmap_workbench.json"
        self.review_path = self.runtime_root / "roadmap_review.json"
        self.revisions_root = self.runtime_root / "revisions"
        self.domain = PlanningStateService()

    def status(self, *, effective_roles: Iterable[str]) -> dict[str, Any]:
        state = self._load_state()
        review = self._read_json(self.review_path)
        return {
            "workspace_id": self.workspace_id,
            "status": "READY",
            "roadmap": state,
            "review": review,
            "advisor": self.advisor(effective_roles=effective_roles),
            "runtime_only": True,
            "source_mutations_performed": False,
            "network_used": False,
            "external_api_used": False,
            "model_execution_used": False,
            "server_authoritative": True,
        }

    def advisor(self, *, effective_roles: Iterable[str]) -> dict[str, Any]:
        roles = tuple(sorted({str(x).strip().lower() for x in effective_roles if str(x).strip()}))
        allowed = bool(set(roles) & AUTHOR_ROLES)
        actions = []
        labels = {
            "MANUAL": ("roadmap.manual", "Escribir roadmap", 10),
            "IMPORT": ("roadmap.import", "Importar roadmap local", 20),
            "AGENT": ("roadmap.agent", "Usar propuesta de agente", 30),
        }
        for mode in ("MANUAL", "IMPORT", "AGENT"):
            action_id, label, rank = labels[mode]
            reasons = [] if allowed else [{"code": "RBAC_AUTHOR_ROLE_REQUIRED", "message": "La autoría de roadmap requiere owner, product-owner, architect o developer.", "subject": mode}]
            actions.append({
                "action_id": action_id,
                "kind": mode,
                "label": label,
                "purpose": "Crear una propuesta DRAFT con el mismo contrato de roadmap y provenance explícita.",
                "availability": "AVAILABLE" if allowed else "UNAVAILABLE",
                "executable": allowed,
                "disabled_reasons": reasons,
                "prerequisites": [],
                "required_roles": sorted(AUTHOR_ROLES),
                "effective_roles": list(roles),
                "risk": {"level": "low", "policy_refs": ["GSDLC-08-B"]},
                "side_effects": ["runtime-draft-write"],
                "approval_required": False,
                "network_required": False,
                "external_api_required": False,
                "cost": {"applicable": False, "value": None, "unit": "USD", "reason": "local/mock first"},
                "tokens": {"applicable": False, "value": None, "unit": "tokens", "reason": "structured proposal ingestion; no model execution required"},
                "rank": rank,
                "recommended": mode == "MANUAL" and allowed,
                "navigation_target": f"/planning/roadmap?mode={mode}",
                "configuration_target": None,
                "typed_operation_id": f"planning.roadmap.propose.{mode.lower()}",
                "api_route_id": "api.planning-roadmap.propose",
                "source_refs": ["02_PROMPT_DEVPL_GSDLC_08_B_v1_0_1_REBOUND_REPO399.md"],
                "agent_descriptor": ({
                    "display_name": "Structured Planning Agent Proposal",
                    "runtime_agent_id": "structured-output-only",
                    "enabled": True,
                    "reason": "GSDLC-08-B accepts structured agent output as DRAFT; no model/tool authority is granted.",
                    "required_model_capabilities": [],
                    "tool_allowlist": [],
                    "policy_status": "DRAFT-HUMAN-REVIEW-REQUIRED",
                    "human_review_required": True,
                    "approval_authority": "server-human-owner-or-product-owner",
                    "model_route_grants_tool_permission": False,
                    "tool_execution_authority": False,
                } if mode == "AGENT" else None),
            })
        payload = {"workspace_id": self.workspace_id, "current_step": "PLANNING_ROADMAP", "status": "PASS" if allowed else "BLOCK", "actions": actions}
        return {
            **payload,
            "recommended_action_id": "roadmap.manual" if allowed else None,
            "decision_fingerprint": _canonical_sha(payload),
            "authority": {"server_rbac_authoritative": True, "advisor_grants_capability": False},
            "safety": {"source_write": False, "agent_auto_approval": False, "network_used": False, "external_api_used": False},
        }

    def propose(
        self,
        *,
        mode: str,
        roadmap: dict[str, Any],
        required_requirement_ids: Iterable[str],
        required_risk_ids: Iterable[str],
        actor_id: str,
        actor_role: str,
        source_label: str = "",
    ) -> dict[str, Any]:
        mode = str(mode).strip().upper()
        role = str(actor_role).strip().lower()
        if mode not in AUTHORING_MODES:
            raise PlanningPolicyError("ROADMAP_AUTHORING_MODE_BLOCK", "Roadmap mode must be MANUAL, IMPORT or AGENT.")
        if role not in AUTHOR_ROLES:
            raise PlanningPolicyError("ROADMAP_AUTHOR_ROLE_BLOCK", "Actor role is not authorized to author roadmap proposals.")
        existing = self._load_state()
        if existing and str(existing.get("lifecycle")) == "FROZEN":
            incoming_version = str(roadmap.get("version") or "")
            if incoming_version == str(existing.get("version") or ""):
                raise PlanningPolicyError("ROADMAP_FROZEN_REVISION_REQUIRED", "Frozen roadmap is immutable; create a new semantic version for a new revision.")
        state = self._parse_state(roadmap)
        if state.lifecycle is not PlanningLifecycle.DRAFT:
            state = replace(state, lifecycle=PlanningLifecycle.DRAFT, approval=None, frozen_by=None)
        known = [(TraceKind.REQUIREMENT.value, x) for x in required_requirement_ids] + [(TraceKind.RISK.value, x) for x in required_risk_ids]
        domain_report = self.domain.validate(state, known_trace_refs=known)
        coverage = self._coverage(state, required_requirement_ids, required_risk_ids)
        findings = self._findings(domain_report.to_dict().get("findings", []), coverage)
        record = {
            "schema_id": "DEVPL-GSDLC-08-B-ROADMAP-WORKBENCH-V1",
            "schema_version": "1.0.0",
            "workspace_id": self.workspace_id,
            "roadmap_id": state.planning_id,
            "version": state.version,
            "lifecycle": "DRAFT",
            "authoring_mode": mode,
            "provenance": {
                "mode": mode,
                "source_label": str(source_label),
                "actor_id": actor_id,
                "actor_role": role,
                "agent_output": mode == "AGENT",
                "agent_auto_approved": False,
                "network_used": False,
                "external_api_used": False,
                "model_execution_used": False,
                "created_at": _utc_now(),
            },
            "required_requirement_ids": sorted({str(x) for x in required_requirement_ids}),
            "required_risk_ids": sorted({str(x) for x in required_risk_ids}),
            "planning_state": state.to_dict(),
            "coverage": coverage,
            "findings": [x.to_dict() for x in findings],
            "content_sha256": _canonical_sha(state.to_dict()),
            "review": None,
            "approval": None,
            "freeze": None,
        }
        self._atomic_json(self.state_path, record)
        if self.review_path.exists():
            self.review_path.unlink()
        return record

    def review(self, *, actor_id: str, actor_role: str) -> dict[str, Any]:
        record = self._require_state()
        state = self._state_from_record(record)
        if state.lifecycle is PlanningLifecycle.DRAFT:
            state = self.domain.transition(state, PlanningLifecycle.REVIEW, actor_id=actor_id, actor_role=actor_role, actor_kind="human")
        elif state.lifecycle is not PlanningLifecycle.REVIEW:
            raise PlanningPolicyError("ROADMAP_REVIEW_STATE_BLOCK", "Review requires DRAFT or REVIEW roadmap state.")
        known = [(TraceKind.REQUIREMENT.value, x) for x in record.get("required_requirement_ids", [])] + [(TraceKind.RISK.value, x) for x in record.get("required_risk_ids", [])]
        domain_report = self.domain.validate(state, known_trace_refs=known)
        coverage = self._coverage(state, record.get("required_requirement_ids", []), record.get("required_risk_ids", []))
        findings = self._findings(domain_report.to_dict().get("findings", []), coverage)
        blocking = [x for x in findings if x.severity == "block"]
        review = {
            "review_id": "roadmap-review-" + _canonical_sha({"state": state.to_dict(), "coverage": coverage})[:20],
            "status": "BLOCK" if blocking else ("PASS-WITH-FINDINGS" if findings else "PASS"),
            "reviewed_at": _utc_now(),
            "reviewed_by": {"actor_id": actor_id, "actor_role": actor_role},
            "content_sha256": _canonical_sha(state.to_dict()),
            "coverage": coverage,
            "findings": [x.to_dict() for x in findings],
            "diff": self._diff_summary(record.get("planning_state") or {}, state.to_dict()),
        }
        record["planning_state"] = state.to_dict()
        record["lifecycle"] = "REVIEW"
        record["coverage"] = coverage
        record["findings"] = [x.to_dict() for x in findings]
        record["review"] = review
        self._atomic_json(self.state_path, record)
        self._atomic_json(self.review_path, review)
        return review

    def approve(self, *, actor_id: str, actor_role: str) -> dict[str, Any]:
        record = self._require_state()
        review = record.get("review") or {}
        if str(review.get("status")) not in {"PASS", "PASS-WITH-FINDINGS"}:
            raise PlanningPolicyError("ROADMAP_REVIEW_PASS_REQUIRED", "Approval requires a completed PASS review.")
        if float((record.get("coverage") or {}).get("requirement_percent", 0.0)) < 100.0:
            raise PlanningPolicyError("ROADMAP_REQUIREMENT_COVERAGE_BLOCK", "Human approval cannot bypass missing mandatory requirement coverage.")
        state = self._state_from_record(record)
        if state.lifecycle is not PlanningLifecycle.REVIEW:
            raise PlanningPolicyError("ROADMAP_APPROVAL_STATE_BLOCK", "Approval requires REVIEW lifecycle.")
        state = self.domain.transition(state, PlanningLifecycle.APPROVED, actor_id=actor_id, actor_role=actor_role, actor_kind="human")
        approval = {"approval_id": "roadmap-approval-" + _canonical_sha({"state": state.to_dict(), "actor": actor_id})[:20], "actor_id": actor_id, "actor_role": actor_role, "source_kind": "human", "approved_at": _utc_now(), "content_sha256": _canonical_sha(state.to_dict())}
        record["planning_state"] = state.to_dict(); record["lifecycle"] = "APPROVED"; record["approval"] = approval
        self._atomic_json(self.state_path, record)
        return approval

    def freeze(self, *, actor_id: str, actor_role: str) -> dict[str, Any]:
        record = self._require_state()
        state = self._state_from_record(record)
        if state.lifecycle is not PlanningLifecycle.APPROVED:
            raise PlanningPolicyError("ROADMAP_FREEZE_STATE_BLOCK", "Freeze requires APPROVED lifecycle.")
        state = self.domain.transition(state, PlanningLifecycle.FROZEN, actor_id=actor_id, actor_role=actor_role, actor_kind="human")
        self.revisions_root.mkdir(parents=True, exist_ok=True)
        existing = sorted(self.revisions_root.glob("roadmap-revision-*.json"))
        revision_number = len(existing) + 1
        frozen = {
            **record,
            "planning_state": state.to_dict(),
            "lifecycle": "FROZEN",
            "freeze": {"revision": revision_number, "actor_id": actor_id, "actor_role": actor_role, "source_kind": "human", "frozen_at": _utc_now(), "immutable": True},
        }
        revision_path = self.revisions_root / f"roadmap-revision-{revision_number:04d}.json"
        if revision_path.exists():
            raise PlanningPolicyError("ROADMAP_REVISION_COLLISION_BLOCK", "Frozen roadmap revision already exists.")
        self._atomic_json(revision_path, frozen)
        self._atomic_json(self.state_path, frozen)
        return {"status": "PASS", "revision": revision_number, "artifact_path": str(revision_path.relative_to(self.workspace_root)).replace("\\", "/"), "roadmap": frozen}

    def _parse_state(self, payload: dict[str, Any]) -> PlanningState:
        milestones = []
        for row in payload.get("milestones") or []:
            milestones.append(Milestone(
                id=str(row.get("id") or ""), version=str(row.get("version") or "1.0.0"), title=str(row.get("title") or ""), owner_role=str(row.get("owner_role") or "product-owner").lower(),
                outcome=str(row.get("outcome") or ""), exit_criteria=tuple(str(x) for x in row.get("exit_criteria") or []), lifecycle=PlanningLifecycle.DRAFT,
                trace_links=tuple(TraceLink(kind=str(x.get("kind") or ""), target_id=str(x.get("target_id") or "")) for x in row.get("trace_links") or []),
            ))
        dependencies = tuple(Dependency(id=str(row.get("id") or ""), predecessor_id=str(row.get("predecessor_id") or ""), successor_id=str(row.get("successor_id") or ""), kind=DependencyKind(str(row.get("kind") or "requires")), rationale=str(row.get("rationale") or "")) for row in payload.get("dependencies") or [])
        return PlanningState(planning_id=str(payload.get("roadmap_id") or payload.get("planning_id") or ""), version=str(payload.get("version") or "1.0.0"), lifecycle=PlanningLifecycle.DRAFT, milestones=tuple(milestones), dependencies=dependencies)

    def _state_from_record(self, record: dict[str, Any]) -> PlanningState:
        payload = dict(record.get("planning_state") or {})
        state = self._parse_state({"roadmap_id": payload.get("planning_id"), "version": payload.get("version"), "milestones": payload.get("milestones"), "dependencies": payload.get("dependencies")})
        state = replace(state, lifecycle=PlanningLifecycle(str(payload.get("lifecycle") or record.get("lifecycle") or "DRAFT")))
        approval = payload.get("approval")
        frozen = payload.get("frozen_by")
        from .models import PlanningApproval
        if approval:
            state = replace(state, approval=PlanningApproval(actor_id=str(approval.get("actor_id") or ""), actor_role=str(approval.get("actor_role") or ""), source_kind=str(approval.get("source_kind") or "human")))
        if frozen:
            state = replace(state, frozen_by=PlanningApproval(actor_id=str(frozen.get("actor_id") or ""), actor_role=str(frozen.get("actor_role") or ""), source_kind=str(frozen.get("source_kind") or "human")))
        return state

    def _coverage(self, state: PlanningState, requirements: Iterable[str], risks: Iterable[str]) -> dict[str, Any]:
        req = sorted({str(x) for x in requirements}); risk = sorted({str(x) for x in risks})
        traced_req = {link.target_id for milestone in state.milestones for link in milestone.trace_links if str(link.kind.value if hasattr(link.kind, "value") else link.kind) == TraceKind.REQUIREMENT.value}
        traced_risk = {link.target_id for milestone in state.milestones for link in milestone.trace_links if str(link.kind.value if hasattr(link.kind, "value") else link.kind) == TraceKind.RISK.value}
        missing_req = [x for x in req if x not in traced_req]; missing_risk = [x for x in risk if x not in traced_risk]
        return {
            "requirements_total": len(req), "requirements_covered": len(req) - len(missing_req), "requirement_percent": round(((len(req)-len(missing_req))/len(req)*100.0) if req else 100.0, 2), "missing_requirement_ids": missing_req,
            "risks_total": len(risk), "risks_covered": len(risk) - len(missing_risk), "risk_percent": round(((len(risk)-len(missing_risk))/len(risk)*100.0) if risk else 100.0, 2), "missing_risk_ids": missing_risk,
        }

    def _findings(self, domain_findings: Iterable[dict[str, Any]], coverage: dict[str, Any]) -> tuple[RoadmapFinding, ...]:
        findings = [RoadmapFinding(str(x.get("finding_id") or "PLANNING_CONTRACT_BLOCK"), "block", str(x.get("message") or "Planning contract invalid."), str(x.get("subject") or "")) for x in domain_findings]
        for req in coverage.get("missing_requirement_ids", []): findings.append(RoadmapFinding("ROADMAP_REQUIREMENT_COVERAGE_GAP", "block", "Mandatory requirement is not covered by any roadmap milestone.", str(req)))
        for risk in coverage.get("missing_risk_ids", []): findings.append(RoadmapFinding("ROADMAP_RISK_COVERAGE_GAP", "warning", "Risk is not covered by any roadmap milestone; finding remains visible for human review.", str(risk)))
        return tuple(findings)

    @staticmethod
    def _diff_summary(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
        before_sha = _canonical_sha(before); after_sha = _canonical_sha(after)
        return {"before_sha256": before_sha, "after_sha256": after_sha, "changed": before_sha != after_sha, "review_required": True}

    def _load_state(self) -> dict[str, Any] | None:
        return self._read_json(self.state_path)

    def _require_state(self) -> dict[str, Any]:
        state = self._load_state()
        if not state: raise PlanningPolicyError("ROADMAP_DRAFT_REQUIRED", "Roadmap DRAFT does not exist.")
        return state

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | None:
        if not path.is_file(): return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None

    @staticmethod
    def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, path)
