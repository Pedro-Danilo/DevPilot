from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .service import PlanningPolicyError

REVIEW_ROLES = frozenset({"owner", "product-owner", "architect", "qa-reviewer"})
APPROVER_ROLES = frozenset({"owner", "product-owner"})
SPRINT_ID_PREFIX = "sprint-plan-"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_sha(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _safe_workspace_id(value: str) -> str:
    raw = str(value or "platform").strip() or "platform"
    normalized = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in raw)[:96].strip("-")
    return normalized or "platform"


class SprintPlanValidationService:
    """Deterministic readiness/capacity/dependency validation for GSDLC-08-D."""

    def evaluate(self, sprint_plan: dict[str, Any], *, backlog: dict[str, Any], dependencies: Iterable[dict[str, Any]] = ()) -> dict[str, Any]:
        findings: list[dict[str, str]] = []
        selected = list(sprint_plan.get("selected_stories") or [])
        selected_ids = [str(x.get("story_id") or "") for x in selected]
        completed = {str(x) for x in sprint_plan.get("completed_story_ids") or [] if str(x)}
        backlog_stories = {str(x.get("id") or ""): x for x in backlog.get("stories") or []}

        if str((sprint_plan.get("backlog_reference") or {}).get("lifecycle") or "") != "FROZEN":
            findings.append(self._finding("SPRINT_BACKLOG_FROZEN_REQUIRED", "block", "Sprint planning requires a FROZEN backlog authority."))
        if len(selected_ids) != len(set(selected_ids)):
            findings.append(self._finding("SPRINT_DUPLICATE_STORY", "block", "A story may be selected only once."))
        for row in selected:
            sid = str(row.get("story_id") or "")
            if sid not in backlog_stories:
                findings.append(self._finding("SPRINT_STORY_ORPHAN", "block", "Selected story is not present in the frozen backlog.", sid))
            readiness = str(row.get("readiness") or "")
            reasons = [str(x).strip() for x in row.get("blocking_reasons") or [] if str(x).strip()]
            if readiness != "READY":
                findings.append(self._finding("SPRINT_STORY_NOT_READY", "block", f"Selected story readiness is {readiness or 'UNSET'}; only READY stories may be scheduled.", sid))
                if not reasons:
                    findings.append(self._finding("SPRINT_BLOCKING_REASON_REQUIRED", "block", "NOT_READY/BLOCKED story must expose its blocking reason.", sid))
            elif reasons:
                findings.append(self._finding("SPRINT_READY_HAS_BLOCKERS", "block", "READY story cannot carry blocking reasons.", sid))

        capacity = sprint_plan.get("capacity") if isinstance(sprint_plan.get("capacity"), dict) else {}
        limit = int(capacity.get("limit") or 0)
        load = sum(int(x.get("estimate") or 0) for x in selected)
        utilization = round((100.0 * load / limit), 2) if limit else 0.0
        if limit <= 0:
            findings.append(self._finding("SPRINT_CAPACITY_INVALID", "block", "Capacity limit must be greater than zero."))
        if limit > 0 and load > limit:
            findings.append(self._finding("SPRINT_CAPACITY_OVERCOMMIT", "block", f"Planned load {load} exceeds capacity {limit}; overcommit must be resolved before approval."))

        index = {sid: pos for pos, sid in enumerate(selected_ids)}
        applicable_edges: list[dict[str, str]] = []
        for dep in dependencies:
            pred, succ = str(dep.get("predecessor_id") or ""), str(dep.get("successor_id") or "")
            if succ not in index:
                continue
            applicable_edges.append({"dependency_id": str(dep.get("id") or ""), "predecessor_id": pred, "successor_id": succ})
            if pred in completed:
                continue
            if pred not in index:
                findings.append(self._finding("SPRINT_PREREQUISITE_MISSING", "block", "Selected story prerequisite is neither completed nor scheduled in this sprint.", f"{pred}->{succ}"))
            elif index[pred] >= index[succ]:
                findings.append(self._finding("SPRINT_DEPENDENCY_ORDER", "block", "Prerequisite must be scheduled before its dependent story.", f"{pred}->{succ}"))

        for field, code, message in (
            ("definition_of_ready", "SPRINT_DOR_REQUIRED", "Definition of Ready must be versioned in the sprint plan."),
            ("definition_of_done", "SPRINT_DOD_REQUIRED", "Definition of Done must be versioned in the sprint plan."),
            ("test_intent_ids", "SPRINT_TEST_INTENT_REQUIRED", "At least one test intent is required."),
            ("risk_focus_ids", "SPRINT_RISK_FOCUS_REQUIRED", "At least one risk-focus reference is required."),
        ):
            if not [str(x).strip() for x in sprint_plan.get(field) or [] if str(x).strip()]:
                findings.append(self._finding(code, "block", message))

        blockers = [x for x in findings if x["severity"] == "block"]
        return {
            "schema_id": "DEVPL-GSDLC-08-D-SPRINT-VALIDATION-REPORT-V1",
            "status": "PASS" if not blockers else "BLOCK",
            "selected_story_ids": selected_ids,
            "selected_stories_total": len(selected_ids),
            "capacity_unit": str(capacity.get("unit") or ""),
            "capacity_limit": limit,
            "planned_load": load,
            "capacity_utilization_percent": utilization,
            "overcommitted": bool(limit and load > limit),
            "applicable_dependencies": applicable_edges,
            "findings": findings,
            "blockers_total": len(blockers),
            "executable": not blockers,
        }

    @staticmethod
    def _finding(code: str, severity: str, message: str, subject: str = "") -> dict[str, str]:
        return {"code": code, "severity": severity, "message": message, "subject": subject}


class SprintPlanner:
    """GSDLC-08-D runtime-only governed sprint planning/review/approval/freeze."""

    def __init__(self, workspace_root: Path, *, workspace_id: str = "platform") -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_id = _safe_workspace_id(workspace_id)
        self.runtime_root = self.workspace_root / "outputs" / "planning" / "gsdlc_08_d" / self.workspace_id
        self.state_path = self.runtime_root / "sprint_planner.json"
        self.report_path = self.runtime_root / "sprint_plan_validation_report.json"
        self.dependency_path = self.runtime_root / "dependency_check.json"
        self.revisions_root = self.runtime_root / "revisions"
        self.validator = SprintPlanValidationService()

    def status(self, *, effective_roles: Iterable[str]) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "status": "READY",
            "sprint_plan": self._load_state(),
            "validation": self._read_json(self.report_path),
            "runtime_only": True,
            "runtime_or_coding_action_enabled": False,
            "source_mutations_performed": False,
            "network_used": False,
            "external_api_used": False,
            "server_authoritative": True,
            "effective_roles": sorted({str(x).strip().lower() for x in effective_roles if str(x).strip()}),
        }

    def propose(self, *, sprint_plan: dict[str, Any], backlog: dict[str, Any], dependencies: Iterable[dict[str, Any]], actor_id: str, actor_role: str) -> dict[str, Any]:
        role = str(actor_role).strip().lower()
        if role not in APPROVER_ROLES:
            raise PlanningPolicyError("SPRINT_AUTHOR_ROLE_BLOCK", "Only owner/product-owner may create the governed sprint plan.")
        if str(actor_id).strip().lower().startswith("agent"):
            raise PlanningPolicyError("SPRINT_AGENT_AUTHOR_BLOCK", "Sprint scheduling requires a human owner/product-owner actor.")
        existing = self._load_state()
        version = str(sprint_plan.get("version") or "")
        if existing and existing.get("lifecycle") == "FROZEN" and version == str(existing.get("version") or ""):
            raise PlanningPolicyError("SPRINT_FROZEN_REVISION_REQUIRED", "Frozen SprintPlan is immutable; create a successor semantic version.")
        report = self.validator.evaluate(sprint_plan, backlog=backlog, dependencies=dependencies)
        record = {
            "schema_id": "DEVPL-GSDLC-08-D-SPRINT-PLANNER-V1",
            "schema_version": "1.0.0",
            "workspace_id": self.workspace_id,
            "sprint_plan_id": str(sprint_plan.get("sprint_plan_id") or ""),
            "version": version,
            "lifecycle": "DRAFT",
            "provenance": {"actor_id": actor_id, "actor_role": role, "source_kind": "human", "created_at": _utc_now(), "network_used": False, "external_api_used": False},
            "sprint_plan": sprint_plan,
            "backlog": backlog,
            "dependencies": list(dependencies),
            "validation": report,
            "content_sha256": _canonical_sha(sprint_plan),
            "review": None,
            "approval": None,
            "freeze": None,
        }
        self._atomic_json(self.state_path, record)
        for path in (self.report_path, self.dependency_path):
            if path.exists():
                path.unlink()
        return record

    def review(self, *, actor_id: str, actor_role: str) -> dict[str, Any]:
        role = str(actor_role).strip().lower()
        if role not in REVIEW_ROLES:
            raise PlanningPolicyError("SPRINT_REVIEW_ROLE_BLOCK", "Role is not authorized to review SprintPlan.")
        record = self._require_state()
        if record.get("lifecycle") not in {"DRAFT", "REVIEW"}:
            raise PlanningPolicyError("SPRINT_REVIEW_STATE_BLOCK", "Review requires DRAFT or REVIEW lifecycle.")
        report = self.validator.evaluate(dict(record.get("sprint_plan") or {}), backlog=dict(record.get("backlog") or {}), dependencies=list(record.get("dependencies") or []))
        review = {
            "review_id": "sprint-review-" + _canonical_sha({"plan": record.get("sprint_plan"), "report": report})[:20],
            "status": report["status"],
            "reviewed_at": _utc_now(),
            "reviewed_by": {"actor_id": actor_id, "actor_role": role},
            "content_sha256": record.get("content_sha256"),
            "findings": report.get("findings"),
        }
        record["lifecycle"] = "REVIEW"
        record["validation"] = report
        record["review"] = review
        self._atomic_json(self.state_path, record)
        self._atomic_json(self.report_path, report)
        self._atomic_json(self.dependency_path, {"schema_id":"DEVPL-GSDLC-08-D-DEPENDENCY-CHECK-V1","status":report["status"],"sprint_plan_id":record.get("sprint_plan_id"),"applicable_dependencies":report["applicable_dependencies"],"findings":[x for x in report["findings"] if x["code"].startswith("SPRINT_DEPENDENCY") or x["code"].startswith("SPRINT_PREREQUISITE")]})
        return review

    def approve(self, *, actor_id: str, actor_role: str) -> dict[str, Any]:
        role = str(actor_role).strip().lower()
        record = self._require_state()
        if role not in APPROVER_ROLES:
            raise PlanningPolicyError("SPRINT_APPROVAL_ROLE_BLOCK", "Only owner/product-owner may approve SprintPlan.")
        if str(actor_id).strip().lower().startswith("agent"):
            raise PlanningPolicyError("SPRINT_AGENT_APPROVAL_BLOCK", "Agent-originated actor cannot approve SprintPlan.")
        if record.get("lifecycle") != "REVIEW" or (record.get("review") or {}).get("status") != "PASS" or int((record.get("validation") or {}).get("blockers_total", 1)):
            raise PlanningPolicyError("SPRINT_REVIEW_PASS_REQUIRED", "Approval requires PASS review, READY stories, valid dependencies and capacity within limit.")
        approval = {"approval_id":"sprint-approval-"+_canonical_sha({"content":record.get("content_sha256"),"actor":actor_id})[:20],"actor_id":actor_id,"actor_role":role,"source_kind":"human","approved_at":_utc_now(),"content_sha256":record.get("content_sha256")}
        record["lifecycle"] = "APPROVED"
        record["approval"] = approval
        self._atomic_json(self.state_path, record)
        return approval

    def freeze(self, *, actor_id: str, actor_role: str) -> dict[str, Any]:
        role = str(actor_role).strip().lower()
        record = self._require_state()
        if role not in APPROVER_ROLES:
            raise PlanningPolicyError("SPRINT_FREEZE_ROLE_BLOCK", "Only owner/product-owner may freeze SprintPlan.")
        if record.get("lifecycle") != "APPROVED":
            raise PlanningPolicyError("SPRINT_FREEZE_STATE_BLOCK", "Freeze requires APPROVED lifecycle.")
        if (record.get("approval") or {}).get("content_sha256") != record.get("content_sha256"):
            raise PlanningPolicyError("SPRINT_APPROVAL_HASH_MISMATCH", "Approved content hash no longer matches SprintPlan.")
        self.revisions_root.mkdir(parents=True, exist_ok=True)
        number = len(list(self.revisions_root.glob("sprint-plan-revision-*.json"))) + 1
        path = self.revisions_root / f"sprint-plan-revision-{number:04d}.json"
        if path.exists():
            raise PlanningPolicyError("SPRINT_REVISION_COLLISION_BLOCK", "Frozen SprintPlan revision already exists.")
        frozen = {**record,"lifecycle":"FROZEN","freeze":{"revision":number,"actor_id":actor_id,"actor_role":role,"source_kind":"human","frozen_at":_utc_now(),"immutable":True,"content_sha256":record.get("content_sha256")}}
        self._atomic_json(path, frozen)
        self._atomic_json(self.state_path, frozen)
        return {"status":"PASS","revision":number,"content_sha256":record.get("content_sha256"),"artifact_path":str(path.relative_to(self.workspace_root)).replace("\\","/"),"sprint_plan":frozen}

    def _load_state(self) -> dict[str, Any] | None:
        return self._read_json(self.state_path)

    def _require_state(self) -> dict[str, Any]:
        state = self._load_state()
        if not state:
            raise PlanningPolicyError("SPRINT_STATE_REQUIRED", "Create SprintPlan DRAFT first.")
        return state

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        temp.replace(path)
