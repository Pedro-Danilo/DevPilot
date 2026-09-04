from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .service import PlanningPolicyError

AUTHORING_MODES = frozenset({"MANUAL", "DERIVED", "AGENT"})
AUTHOR_ROLES = frozenset({"owner", "product-owner", "architect", "developer"})
REVIEW_ROLES = frozenset({"owner", "product-owner", "architect", "qa-reviewer"})
APPROVER_ROLES = frozenset({"owner", "product-owner"})
PRIORITY_LEVELS = frozenset({"P0", "P1", "P2", "P3"})
TRACE_KINDS = frozenset({"requirement", "risk", "adr", "test-intent"})
ID_PATTERNS = {
    "backlog": re.compile(r"^planning-backlog-[a-z0-9-]{2,48}$"),
    "epic": re.compile(r"^epic-[a-z0-9-]{2,59}$"),
    "story": re.compile(r"^story-[a-z0-9-]{2,59}$"),
    "milestone": re.compile(r"^mil-[a-z0-9-]{2,59}$"),
    "dependency": re.compile(r"^dep-[a-z0-9-]{2,59}$"),
}
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_sha(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _safe_workspace_id(value: str) -> str:
    raw = str(value or "platform").strip() or "platform"
    normalized = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in raw)[:96].strip("-")
    return normalized or "platform"


def _norm_title(value: str) -> str:
    return " ".join(str(value).casefold().split())


@dataclass(frozen=True)
class BacklogFinding:
    code: str
    severity: str
    message: str
    subject: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "severity": self.severity, "message": self.message, "subject": self.subject}


class RequirementCoverageService:
    """Deterministic requirement→story coverage and backlog contract validator."""

    def evaluate(
        self,
        backlog: dict[str, Any],
        *,
        required_requirement_ids: Iterable[str],
        roadmap_milestone_ids: Iterable[str] = (),
        known_adr_ids: Iterable[str] = (),
        known_risk_ids: Iterable[str] = (),
        known_test_intent_ids: Iterable[str] = (),
        expected_priority_source: str | None = None,
    ) -> dict[str, Any]:
        findings: list[BacklogFinding] = []
        required = sorted({str(x) for x in required_requirement_ids if str(x)})
        milestones = {str(x) for x in roadmap_milestone_ids if str(x)}
        known_by_kind = {
            "requirement": set(required),
            "adr": {str(x) for x in known_adr_ids if str(x)},
            "risk": {str(x) for x in known_risk_ids if str(x)},
            "test-intent": {str(x) for x in known_test_intent_ids if str(x)},
        }
        backlog_id = str(backlog.get("backlog_id") or "")
        version = str(backlog.get("version") or "")
        if not ID_PATTERNS["backlog"].fullmatch(backlog_id):
            findings.append(BacklogFinding("BACKLOG_ID_INVALID", "block", "backlog_id must match the stable planning-backlog-* contract.", backlog_id))
        if not SEMVER.fullmatch(version):
            findings.append(BacklogFinding("BACKLOG_VERSION_INVALID", "block", "Backlog version must be semantic x.y.z.", version))

        epics = list(backlog.get("epics") or [])
        stories = list(backlog.get("stories") or [])
        dependencies = list(backlog.get("dependencies") or [])
        epic_ids = [str(x.get("id") or "") for x in epics]
        story_ids = [str(x.get("id") or "") for x in stories]
        all_ids = epic_ids + story_ids
        for duplicate in sorted({x for x in all_ids if x and all_ids.count(x) > 1}):
            findings.append(BacklogFinding("BACKLOG_ID_COLLISION", "block", "Epic/story ids must be globally unique.", duplicate))

        for epic in epics:
            eid = str(epic.get("id") or "")
            if not ID_PATTERNS["epic"].fullmatch(eid):
                findings.append(BacklogFinding("BACKLOG_EPIC_ID_INVALID", "block", "Epic id does not match stable-id contract.", eid))
            milestone_id = str(epic.get("milestone_id") or "")
            if not ID_PATTERNS["milestone"].fullmatch(milestone_id):
                findings.append(BacklogFinding("BACKLOG_EPIC_MILESTONE_INVALID", "block", "Epic requires a valid roadmap milestone_id.", eid))
            elif milestones and milestone_id not in milestones:
                findings.append(BacklogFinding("BACKLOG_EPIC_ROADMAP_ORPHAN", "block", "Epic points to a milestone not present in the frozen roadmap authority.", eid))
            self._validate_priority(epic, findings, expected_priority_source)
            self._validate_trace_links(epic, findings, known_by_kind)

        seen_titles: dict[str, str] = {}
        matrix = {req: [] for req in required}
        epic_set = set(epic_ids)
        story_set = set(story_ids)
        for story in stories:
            sid = str(story.get("id") or "")
            if not ID_PATTERNS["story"].fullmatch(sid):
                findings.append(BacklogFinding("BACKLOG_STORY_ID_INVALID", "block", "Story id does not match stable-id contract.", sid))
            epic_id = str(story.get("epic_id") or "")
            if epic_id not in epic_set:
                findings.append(BacklogFinding("BACKLOG_STORY_EPIC_ORPHAN", "block", "Story references an unknown epic.", sid))
            criteria = [str(x).strip() for x in story.get("acceptance_criteria") or [] if str(x).strip()]
            if not criteria:
                findings.append(BacklogFinding("BACKLOG_STORY_ACCEPTANCE_REQUIRED", "block", "Story requires at least one acceptance criterion.", sid))
            title_key = _norm_title(story.get("title") or "")
            if title_key:
                if title_key in seen_titles:
                    findings.append(BacklogFinding("BACKLOG_DUPLICATE_STORY", "block", "Two stories have the same normalized title.", f"{seen_titles[title_key]}|{sid}"))
                else:
                    seen_titles[title_key] = sid
            self._validate_priority(story, findings, expected_priority_source)
            self._validate_trace_links(story, findings, known_by_kind)
            req_links = sorted({str(x.get("target_id")) for x in story.get("trace_links") or [] if str(x.get("kind")) == "requirement" and str(x.get("target_id") or "")})
            if not req_links:
                findings.append(BacklogFinding("BACKLOG_STORY_REQUIREMENT_TRACE_REQUIRED", "block", "Story requires at least one requirement trace link.", sid))
            for req in req_links:
                if req in matrix:
                    matrix[req].append(sid)

        dep_ids: list[str] = []
        adjacency = {node: set() for node in sorted(set(all_ids)) if node}
        indegree = {node: 0 for node in adjacency}
        for dep in dependencies:
            did = str(dep.get("id") or "")
            dep_ids.append(did)
            if not ID_PATTERNS["dependency"].fullmatch(did):
                findings.append(BacklogFinding("BACKLOG_DEPENDENCY_ID_INVALID", "block", "Dependency id does not match stable-id contract.", did))
            pred, succ = str(dep.get("predecessor_id") or ""), str(dep.get("successor_id") or "")
            if pred not in adjacency or succ not in adjacency:
                findings.append(BacklogFinding("BACKLOG_DEPENDENCY_GAP", "block", "Dependency endpoint does not exist in backlog epics/stories.", did))
                continue
            if pred == succ:
                findings.append(BacklogFinding("BACKLOG_DEPENDENCY_SELF", "block", "Self dependency is forbidden.", did))
                continue
            if succ not in adjacency[pred]:
                adjacency[pred].add(succ); indegree[succ] += 1
        for duplicate in sorted({x for x in dep_ids if x and dep_ids.count(x) > 1}):
            findings.append(BacklogFinding("BACKLOG_DEPENDENCY_ID_COLLISION", "block", "Dependency ids must be unique.", duplicate))
        ready = sorted(node for node, degree in indegree.items() if degree == 0)
        visited: list[str] = []
        while ready:
            node = ready.pop(0); visited.append(node)
            for target in sorted(adjacency[node]):
                indegree[target] -= 1
                if indegree[target] == 0:
                    ready.append(target); ready.sort()
        for node, degree in sorted(indegree.items()):
            if degree > 0:
                findings.append(BacklogFinding("BACKLOG_DEPENDENCY_CYCLE", "block", "Backlog dependency graph contains a cycle.", node))

        missing = [req for req, mapped in matrix.items() if not mapped]
        for req in missing:
            findings.append(BacklogFinding("BACKLOG_REQUIREMENT_UNMAPPED", "block", "Mandatory requirement is not mapped to any story.", req))
        coverage = round(((len(required) - len(missing)) / len(required) * 100.0) if required else 100.0, 2)
        blockers = [x for x in findings if x.severity == "block"]
        return {
            "schema_id": "DEVPL-GSDLC-08-C-REQUIREMENT-COVERAGE-REPORT-V1",
            "status": "PASS" if not blockers else "BLOCK",
            "required_requirements_total": len(required),
            "mapped_requirements_total": len(required) - len(missing),
            "requirement_coverage_percent": coverage,
            "unmapped_requirement_ids": missing,
            "requirement_to_story_matrix": [{"requirement_id": req, "story_ids": sorted(matrix[req]), "covered": bool(matrix[req])} for req in required],
            "epics_total": len(epics),
            "stories_total": len(stories),
            "dependencies_total": len(dependencies),
            "blockers_total": len(blockers),
            "findings": [x.to_dict() for x in findings],
            "topological_order": visited if len(visited) == len(adjacency) else [],
        }

    @staticmethod
    def _validate_priority(row: dict[str, Any], findings: list[BacklogFinding], expected_source: str | None) -> None:
        subject = str(row.get("id") or "")
        priority = row.get("priority") if isinstance(row.get("priority"), dict) else {}
        if str(priority.get("level") or "") not in PRIORITY_LEVELS:
            findings.append(BacklogFinding("BACKLOG_PRIORITY_LEVEL_INVALID", "block", "Priority level must be P0/P1/P2/P3.", subject))
        for key in ("value_score", "risk_score"):
            value = priority.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
                findings.append(BacklogFinding("BACKLOG_PRIORITY_SCORE_INVALID", "block", f"{key} must be an integer from 1 to 5.", subject))
        if not str(priority.get("rationale") or "").strip():
            findings.append(BacklogFinding("BACKLOG_PRIORITY_RATIONALE_REQUIRED", "block", "Priority must include a human-readable rationale.", subject))
        source = str(priority.get("source") or "").upper()
        if source not in AUTHORING_MODES:
            findings.append(BacklogFinding("BACKLOG_PRIORITY_SOURCE_INVALID", "block", "Priority source must be MANUAL, DERIVED or AGENT.", subject))
        elif expected_source and source != expected_source:
            findings.append(BacklogFinding("BACKLOG_PRIORITY_PROVENANCE_MISMATCH", "block", "Priority provenance must match the authoring route.", subject))

    @staticmethod
    def _validate_trace_links(row: dict[str, Any], findings: list[BacklogFinding], known_by_kind: dict[str, set[str]]) -> None:
        subject = str(row.get("id") or "")
        for link in row.get("trace_links") or []:
            kind, target = str(link.get("kind") or ""), str(link.get("target_id") or "")
            if kind not in TRACE_KINDS or not target:
                findings.append(BacklogFinding("BACKLOG_TRACE_INVALID", "block", "Trace link kind/target is invalid.", subject))
                continue
            known = known_by_kind.get(kind, set())
            if known and target not in known:
                findings.append(BacklogFinding("BACKLOG_TRACE_ORPHAN", "block", "Trace target is not present in the supplied authoritative set.", f"{subject}:{kind}:{target}"))


class BacklogWorkbench:
    """GSDLC-08-C governed runtime-only backlog derivation/review/freeze."""

    def __init__(self, workspace_root: Path, *, workspace_id: str = "platform") -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_id = _safe_workspace_id(workspace_id)
        self.runtime_root = self.workspace_root / "outputs" / "planning" / "gsdlc_08_c" / self.workspace_id
        self.state_path = self.runtime_root / "backlog_workbench.json"
        self.review_path = self.runtime_root / "backlog_validation_report.json"
        self.matrix_path = self.runtime_root / "requirement_to_story_matrix.json"
        self.revisions_root = self.runtime_root / "revisions"
        self.coverage = RequirementCoverageService()

    def status(self, *, effective_roles: Iterable[str]) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "status": "READY",
            "backlog": self._load_state(),
            "review": self._read_json(self.review_path),
            "runtime_only": True,
            "source_mutations_performed": False,
            "network_used": False,
            "external_api_used": False,
            "server_authoritative": True,
            "effective_roles": sorted({str(x).strip().lower() for x in effective_roles if str(x).strip()}),
        }

    def propose(
        self,
        *,
        mode: str,
        backlog: dict[str, Any],
        required_requirement_ids: Iterable[str],
        roadmap_milestone_ids: Iterable[str],
        known_adr_ids: Iterable[str] = (),
        known_risk_ids: Iterable[str] = (),
        known_test_intent_ids: Iterable[str] = (),
        actor_id: str,
        actor_role: str,
        source_label: str = "",
    ) -> dict[str, Any]:
        mode, role = str(mode).strip().upper(), str(actor_role).strip().lower()
        if mode not in AUTHORING_MODES:
            raise PlanningPolicyError("BACKLOG_AUTHORING_MODE_BLOCK", "Backlog mode must be MANUAL, DERIVED or AGENT.")
        if role not in AUTHOR_ROLES:
            raise PlanningPolicyError("BACKLOG_AUTHOR_ROLE_BLOCK", "Actor role is not authorized to author backlog proposals.")
        existing = self._load_state()
        incoming_version = str(backlog.get("version") or "")
        if existing and str(existing.get("lifecycle")) == "FROZEN" and incoming_version == str(existing.get("version") or ""):
            raise PlanningPolicyError("BACKLOG_FROZEN_REVISION_REQUIRED", "Frozen backlog is immutable; create a new semantic version.")
        if existing and str(existing.get("authoring_mode")) == "MANUAL" and mode in {"DERIVED", "AGENT"} and incoming_version == str(existing.get("version") or ""):
            raise PlanningPolicyError("BACKLOG_MANUAL_PRECEDENCE_BLOCK", "Manual edits prevail; DERIVED/AGENT cannot overwrite the same manual semantic version.")

        report = self.coverage.evaluate(
            backlog,
            required_requirement_ids=required_requirement_ids,
            roadmap_milestone_ids=roadmap_milestone_ids,
            known_adr_ids=known_adr_ids,
            known_risk_ids=known_risk_ids,
            known_test_intent_ids=known_test_intent_ids,
            expected_priority_source=mode,
        )
        record = {
            "schema_id": "DEVPL-GSDLC-08-C-BACKLOG-WORKBENCH-V1",
            "schema_version": "1.0.0",
            "workspace_id": self.workspace_id,
            "backlog_id": str(backlog.get("backlog_id") or ""),
            "version": incoming_version,
            "lifecycle": "DRAFT",
            "authoring_mode": mode,
            "provenance": {"mode": mode, "source_label": str(source_label), "actor_id": actor_id, "actor_role": role, "agent_output": mode == "AGENT", "agent_auto_approved": False, "created_at": _utc_now(), "network_used": False, "external_api_used": False},
            "required_requirement_ids": sorted({str(x) for x in required_requirement_ids}),
            "roadmap_milestone_ids": sorted({str(x) for x in roadmap_milestone_ids}),
            "known_adr_ids": sorted({str(x) for x in known_adr_ids}),
            "known_risk_ids": sorted({str(x) for x in known_risk_ids}),
            "known_test_intent_ids": sorted({str(x) for x in known_test_intent_ids}),
            "backlog": backlog,
            "coverage": report,
            "content_sha256": _canonical_sha(backlog),
            "manual_precedence": True,
            "review": None,
            "approval": None,
            "freeze": None,
        }
        self._atomic_json(self.state_path, record)
        for path in (self.review_path, self.matrix_path):
            if path.exists(): path.unlink()
        return record

    def review(self, *, actor_id: str, actor_role: str) -> dict[str, Any]:
        role = str(actor_role).strip().lower()
        if role not in REVIEW_ROLES:
            raise PlanningPolicyError("BACKLOG_REVIEW_ROLE_BLOCK", "Role is not authorized to review backlog.")
        record = self._require_state()
        if record.get("lifecycle") not in {"DRAFT", "REVIEW"}:
            raise PlanningPolicyError("BACKLOG_REVIEW_STATE_BLOCK", "Review requires DRAFT or REVIEW lifecycle.")
        report = self.coverage.evaluate(
            dict(record.get("backlog") or {}),
            required_requirement_ids=record.get("required_requirement_ids") or [],
            roadmap_milestone_ids=record.get("roadmap_milestone_ids") or [],
            known_adr_ids=record.get("known_adr_ids") or [],
            known_risk_ids=record.get("known_risk_ids") or [],
            known_test_intent_ids=record.get("known_test_intent_ids") or [],
            expected_priority_source=str(record.get("authoring_mode") or ""),
        )
        blocking = int(report.get("blockers_total", 0)) > 0
        review = {
            "review_id": "backlog-review-" + _canonical_sha({"backlog": record.get("backlog"), "report": report})[:20],
            "status": "BLOCK" if blocking else "PASS",
            "reviewed_at": _utc_now(),
            "reviewed_by": {"actor_id": actor_id, "actor_role": role},
            "content_sha256": record.get("content_sha256"),
            "requirement_coverage_percent": report.get("requirement_coverage_percent"),
            "unmapped_blockers": report.get("unmapped_requirement_ids"),
            "findings": report.get("findings"),
        }
        record["lifecycle"] = "REVIEW"; record["coverage"] = report; record["review"] = review
        self._atomic_json(self.state_path, record); self._atomic_json(self.review_path, report)
        self._atomic_json(self.matrix_path, {"schema_id":"DEVPL-GSDLC-08-C-REQUIREMENT-TO-STORY-MATRIX-V1","status":report["status"],"backlog_id":record.get("backlog_id"),"requirement_coverage_percent":report["requirement_coverage_percent"],"rows":report["requirement_to_story_matrix"]})
        return review

    def approve(self, *, actor_id: str, actor_role: str) -> dict[str, Any]:
        role = str(actor_role).strip().lower(); record = self._require_state()
        if role not in APPROVER_ROLES:
            raise PlanningPolicyError("BACKLOG_APPROVAL_ROLE_BLOCK", "Only owner/product-owner may approve backlog.")
        if str(record.get("authoring_mode")) == "AGENT" and str(actor_id).strip().lower().startswith("agent"):
            raise PlanningPolicyError("BACKLOG_AGENT_APPROVAL_BLOCK", "Agent-originated actor cannot approve backlog.")
        review = record.get("review") or {}; coverage = record.get("coverage") or {}
        if review.get("status") != "PASS" or float(coverage.get("requirement_coverage_percent", 0.0)) < 100.0 or int(coverage.get("blockers_total", 1)):
            raise PlanningPolicyError("BACKLOG_REVIEW_PASS_REQUIRED", "Approval requires PASS review, 100% required coverage and zero blockers.")
        if record.get("lifecycle") != "REVIEW":
            raise PlanningPolicyError("BACKLOG_APPROVAL_STATE_BLOCK", "Approval requires REVIEW lifecycle.")
        approval = {"approval_id":"backlog-approval-"+_canonical_sha({"content":record.get("content_sha256"),"actor":actor_id})[:20],"actor_id":actor_id,"actor_role":role,"source_kind":"human","approved_at":_utc_now(),"content_sha256":record.get("content_sha256")}
        record["lifecycle"]="APPROVED"; record["approval"]=approval; self._atomic_json(self.state_path,record); return approval

    def freeze(self, *, actor_id: str, actor_role: str) -> dict[str, Any]:
        role = str(actor_role).strip().lower(); record = self._require_state()
        if role not in APPROVER_ROLES:
            raise PlanningPolicyError("BACKLOG_FREEZE_ROLE_BLOCK", "Only owner/product-owner may freeze backlog.")
        if record.get("lifecycle") != "APPROVED":
            raise PlanningPolicyError("BACKLOG_FREEZE_STATE_BLOCK", "Freeze requires APPROVED lifecycle.")
        self.revisions_root.mkdir(parents=True, exist_ok=True)
        number = len(list(self.revisions_root.glob("backlog-revision-*.json"))) + 1
        path = self.revisions_root / f"backlog-revision-{number:04d}.json"
        if path.exists(): raise PlanningPolicyError("BACKLOG_REVISION_COLLISION_BLOCK", "Frozen backlog revision already exists.")
        frozen = {**record,"lifecycle":"FROZEN","freeze":{"revision":number,"actor_id":actor_id,"actor_role":role,"source_kind":"human","frozen_at":_utc_now(),"immutable":True}}
        self._atomic_json(path,frozen); self._atomic_json(self.state_path,frozen)
        return {"status":"PASS","revision":number,"artifact_path":str(path.relative_to(self.workspace_root)).replace("\\","/"),"backlog":frozen}

    def _load_state(self) -> dict[str, Any] | None: return self._read_json(self.state_path)
    def _require_state(self) -> dict[str, Any]:
        state=self._load_state()
        if not state: raise PlanningPolicyError("BACKLOG_DRAFT_REQUIRED", "Backlog DRAFT does not exist.")
        return state
    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | None:
        if not path.is_file(): return None
        data=json.loads(path.read_text(encoding="utf-8")); return data if isinstance(data,dict) else None
    @staticmethod
    def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp")
        tmp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n"); os.replace(tmp,path)
