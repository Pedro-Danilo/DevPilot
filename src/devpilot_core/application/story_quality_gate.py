from __future__ import annotations

import hashlib
import json
import os
import tempfile
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

RUNTIME_ROOT = Path("outputs/runtime/gsdlc10c_story_quality")
REPORT_SCHEMA_ID = "DEVPL-GSDLC-10-C-STORY-QUALITY-REPORT-V1"
TRACE_SCHEMA_ID = "DEVPL-GSDLC-10-C-REMEDIATION-TRACE-V1"
WAIVER_SCHEMA_ID = "DEVPL-GSDLC-10-C-QUALITY-WAIVER-V1"
ALLOWED_FINDING_ORIGINS = {"review", "security", "traceability", "policy"}
ALLOWED_SEVERITIES = {"S0", "S1", "S2", "S3"}
TERMINAL_PASS = {"PASS"}
BLOCKING_JOB_STATES = {"FAIL", "ERROR", "CANCELLED", "TIMED_OUT", "CANCEL_REQUESTED"}
PENDING_JOB_STATES = {"PLANNED", "APPROVED", "QUEUED", "RUNNING"}


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def _now() -> str:
    return _now_dt().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _sha(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


class StoryQualityRuntimeStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve() / RUNTIME_ROOT
        self.reports = self.root / "reports"
        self.findings = self.root / "findings"
        self.waivers = self.root / "waivers"
        self.traces = self.root / "remediation"

    def _load(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def save_report(self, record: dict[str, Any]) -> Path:
        path = self.reports / f"{record['report_id']}.json"
        _atomic_json(path, record)
        return path

    def load_report(self, report_id: str) -> dict[str, Any]:
        path = self.reports / f"{report_id}.json"
        if not path.is_file():
            raise KeyError(report_id)
        return self._load(path)

    def list_reports(self, test_plan_id: str | None = None) -> list[dict[str, Any]]:
        rows = [self._load(path) for path in sorted(self.reports.glob("story-quality-report-*.json"))] if self.reports.exists() else []
        if test_plan_id:
            rows = [row for row in rows if row.get("story_test_plan_id") == test_plan_id]
        return rows

    def save_finding(self, record: dict[str, Any]) -> Path:
        path = self.findings / f"{record['finding_id']}.json"
        _atomic_json(path, record)
        return path

    def load_finding(self, finding_id: str) -> dict[str, Any]:
        path = self.findings / f"{finding_id}.json"
        if not path.is_file():
            raise KeyError(finding_id)
        return self._load(path)

    def list_findings(self, test_plan_id: str) -> list[dict[str, Any]]:
        rows = [self._load(path) for path in sorted(self.findings.glob("quality-finding-*.json"))] if self.findings.exists() else []
        return [row for row in rows if row.get("story_test_plan_id") == test_plan_id]

    def save_waiver(self, record: dict[str, Any]) -> Path:
        path = self.waivers / f"{record['waiver_id']}.json"
        _atomic_json(path, record)
        return path

    def load_waiver(self, waiver_id: str) -> dict[str, Any]:
        path = self.waivers / f"{waiver_id}.json"
        if not path.is_file():
            raise KeyError(waiver_id)
        return self._load(path)

    def list_waivers(self, test_plan_id: str) -> list[dict[str, Any]]:
        rows = [self._load(path) for path in sorted(self.waivers.glob("quality-waiver-*.json"))] if self.waivers.exists() else []
        return [row for row in rows if row.get("story_test_plan_id") == test_plan_id]

    def save_trace(self, record: dict[str, Any]) -> Path:
        path = self.traces / f"{record['trace_id']}.json"
        _atomic_json(path, record)
        return path

    def load_trace(self, trace_id: str) -> dict[str, Any]:
        path = self.traces / f"{trace_id}.json"
        if not path.is_file():
            raise KeyError(trace_id)
        return self._load(path)

    def list_traces(self, report_id: str | None = None) -> list[dict[str, Any]]:
        rows = [self._load(path) for path in sorted(self.traces.glob("remediation-trace-*.json"))] if self.traces.exists() else []
        if report_id:
            rows = [row for row in rows if row.get("source_report_id") == report_id]
        return rows


class StoryQualityGateApplicationService:
    """GSDLC-10-C story-level deterministic quality decision and remediation loop.

    This service elevates the existing Quality/Job/StoryCode surfaces; it does not
    introduce a second test runner or source mutation path. All source remediation
    is handed back to GSDLC-09, while retests are planned through GSDLC-10-A/B.
    """

    def __init__(
        self,
        root: Path,
        *,
        story_test_plan_loader: Callable[..., CommandResult],
        validation_jobs_lister: Callable[..., CommandResult],
        validation_jobs_creator: Callable[..., CommandResult],
        agent_proposal_creator: Callable[..., CommandResult] | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.story_test_plan_loader = story_test_plan_loader
        self.validation_jobs_lister = validation_jobs_lister
        self.validation_jobs_creator = validation_jobs_creator
        self.agent_proposal_creator = agent_proposal_creator
        self.store = StoryQualityRuntimeStore(self.root)

    def record_finding(
        self,
        *,
        test_plan_id: str,
        test_plan_hash: str,
        origin: str,
        severity: str,
        message: str,
        actor: str,
        actor_role: str,
        source_ref: str | None = None,
        authority_source: str = "human-session",
    ) -> CommandResult:
        command = "story quality finding record"
        role_failure = self._human_role(command, actor_role, authority_source)
        if role_failure:
            return role_failure
        origin = str(origin).strip().lower()
        severity = str(severity).strip().upper()
        message = str(message).strip()
        if origin not in ALLOWED_FINDING_ORIGINS:
            return self._block(command, "GSDLC10C_FINDING_ORIGIN_BLOCK", "Finding origin must be review/security/traceability/policy.")
        if severity not in ALLOWED_SEVERITIES:
            return self._block(command, "GSDLC10C_FINDING_SEVERITY_BLOCK", "Finding severity must be S0/S1/S2/S3.")
        if not message or len(message) > 1000:
            return self._block(command, "GSDLC10C_FINDING_MESSAGE_BLOCK", "Finding message must contain 1..1000 characters.")
        plan, failure = self._approved_plan(command, test_plan_id, test_plan_hash)
        if failure:
            return failure
        assert plan is not None
        stable = {
            "story_test_plan_id": test_plan_id,
            "story_test_plan_hash": test_plan_hash,
            "origin": origin,
            "severity": severity,
            "message": message,
            "source_ref": str(source_ref or "manual-review"),
            "actor": actor,
        }
        finding_id = "quality-finding-" + _sha(stable)[:24]
        existing: dict[str, Any] | None = None
        try:
            existing = self.store.load_finding(finding_id)
        except KeyError:
            pass
        if existing:
            return self._pass(command, "Quality finding already exists; idempotent record returned.", {"quality_finding": existing, "idempotent": True})
        record = {
            "schema_id": "DEVPL-GSDLC-10-C-QUALITY-FINDING-V1",
            "finding_id": finding_id,
            **stable,
            "story_execution_id": plan.get("story_execution_id"),
            "status": "OPEN",
            "created_at_utc": _now(),
            "resolved_at_utc": None,
            "resolved_by_trace_id": None,
            "waivable": severity in {"S2", "S3"},
            "network_used": False,
            "external_api_used": False,
        }
        self.store.save_finding(record)
        return self._pass(command, "Quality finding recorded as an additional fail-closed input.", {"quality_finding": record, "idempotent": False})

    def evaluate(
        self,
        *,
        test_plan_id: str,
        test_plan_hash: str,
        actor: str,
        actor_role: str,
    ) -> CommandResult:
        command = "story quality evaluate"
        role_failure = self._human_role(command, actor_role, "human-session")
        if role_failure:
            return role_failure
        plan, failure = self._approved_plan(command, test_plan_id, test_plan_hash)
        if failure:
            return failure
        assert plan is not None
        jobs_result = self.validation_jobs_lister(test_plan_id=test_plan_id)
        if not jobs_result.ok:
            return CommandResult(command, False, jobs_result.exit_code, "Story validation jobs dependency blocked Quality Gate.", data=jobs_result.data, findings=jobs_result.findings)
        jobs = [dict(row) for row in (jobs_result.data or {}).get("jobs", [])]
        selected_jobs = self._latest_jobs_by_kind(jobs)
        derived_findings = self._job_findings(selected_jobs)
        derived_findings.extend(self._traceability_findings(plan, selected_jobs))
        supplemental = [deepcopy(row) for row in self.store.list_findings(test_plan_id)]
        waiver_rows = self._waiver_projection(test_plan_id)
        active_waivers = {str(row["finding_id"]): row for row in waiver_rows if row.get("effective")}

        findings: list[dict[str, Any]] = []
        for row in [*derived_findings, *supplemental]:
            item = deepcopy(row)
            item.setdefault("status", "OPEN")
            item.setdefault("waivable", str(item.get("severity")) in {"S2", "S3"})
            resolved = str(item.get("status")) == "RESOLVED"
            waiver = active_waivers.get(str(item.get("finding_id"))) if item.get("waivable") else None
            item["waived"] = bool(waiver) and not resolved
            item["waiver_id"] = None if waiver is None else waiver.get("waiver_id")
            item["blocking"] = not resolved and not item["waived"]
            findings.append(item)

        blockers = [row for row in findings if row.get("blocking")]
        severity_counts = {severity: sum(1 for row in findings if row.get("severity") == severity and row.get("blocking")) for severity in sorted(ALLOWED_SEVERITIES)}
        inputs = {
            "story_test_plan_id": test_plan_id,
            "story_test_plan_hash": test_plan_hash,
            "test_impact_report_hash": plan.get("test_impact_report_hash"),
            "source_change_plan_id": plan.get("source_change_plan_id"),
            "source_change_plan_hash": plan.get("source_change_plan_hash"),
            "changed_paths": sorted(str(x) for x in plan.get("changed_paths", [])),
            "jobs": [self._stable_job_input(row) for row in selected_jobs],
            "supplemental_findings": [self._stable_finding_input(row) for row in supplemental],
            "waivers": [self._stable_waiver_input(row) for row in waiver_rows],
        }
        inputs_hash = _sha(inputs)
        decision = "PASS" if not blockers and bool(selected_jobs) else "BLOCK"
        if not selected_jobs:
            missing = {
                "finding_id": "GSDLC10C_REQUIRED_VALIDATIONS_MISSING",
                "origin": "validation",
                "severity": "S1",
                "message": "No StoryValidationJobs are bound to the approved StoryTestPlan.",
                "source_ref": test_plan_id,
                "status": "OPEN",
                "waivable": False,
                "waived": False,
                "blocking": True,
            }
            findings.append(missing)
            blockers.append(missing)
            severity_counts["S1"] += 1
            decision = "BLOCK"
        report_stable = {
            "schema_id": REPORT_SCHEMA_ID,
            "story_test_plan_id": test_plan_id,
            "story_test_plan_hash": test_plan_hash,
            "story_execution_id": plan.get("story_execution_id"),
            "story_id": plan.get("story_id"),
            "inputs_hash": inputs_hash,
            "decision": decision,
            "commit_ready": decision == "PASS",
            "findings": findings,
            "severity_counts": severity_counts,
        }
        report_hash = _sha(report_stable)
        report_id = "story-quality-report-" + report_hash[:24]
        record = {
            **report_stable,
            "report_id": report_id,
            "report_hash": report_hash,
            "created_at_utc": _now(),
            "required_job_results": selected_jobs,
            "policy": {
                "s0_s1_waivable": False,
                "s2_s3_waiver_requires_owner_other_than_requester": True,
                "agent_model_can_waive": False,
                "required_validation_non_pass_blocks_commit_ready": True,
                "full_regression": False,
            },
            "waiver_decisions": waiver_rows,
            "remediation_advisor": self._advisor_projection(actor_role),
            "provenance": {
                "finding_to_remediation_to_retest": True,
                "source_mutation_route": "GSDLC-09 Story Code Workbench only",
                "retest_route": "GSDLC-10-A StoryTestPlan -> GSDLC-10-B typed jobs",
            },
            "network_used": False,
            "external_api_used": False,
            "source_mutations_performed": False,
            "full_regression_started": False,
        }
        self.store.save_report(record)
        msg = "StoryQualityGate PASS; COMMIT_READY may be offered." if decision == "PASS" else f"StoryQualityGate BLOCK with {len(blockers)} blocker(s)."
        return self._pass(command, msg, {"story_quality_report": record})

    def get_report(self, *, report_id: str) -> CommandResult:
        command = "story quality report get"
        try:
            report = self.store.load_report(report_id)
        except KeyError:
            return self._block(command, "GSDLC10C_REPORT_NOT_FOUND", "StoryQualityReport was not found.")
        current = self._current_inputs_hash(report)
        stale = current is None or current != report.get("inputs_hash")
        projected = deepcopy(report)
        projected["stale"] = stale
        if stale:
            projected["commit_ready"] = False
            projected["decision"] = "BLOCK"
            projected["stale_reason"] = "Quality inputs changed after report creation; re-evaluate before COMMIT_READY."
        return self._pass(command, "StoryQualityReport loaded with stale-input check.", {"story_quality_report": projected})

    def request_waiver(
        self,
        *,
        report_id: str,
        report_hash: str,
        finding_id: str,
        reason: str,
        ttl_minutes: int,
        actor: str,
        actor_role: str,
        authority_source: str = "human-session",
    ) -> CommandResult:
        command = "story quality waiver request"
        role_failure = self._human_role(command, actor_role, authority_source)
        if role_failure:
            return role_failure
        report, failure = self._exact_report(command, report_id, report_hash)
        if failure:
            return failure
        assert report is not None
        finding = next((row for row in report.get("findings", []) if row.get("finding_id") == finding_id), None)
        if not finding:
            return self._block(command, "GSDLC10C_WAIVER_FINDING_NOT_FOUND", "Waiver target finding is not present in the report.")
        if str(finding.get("severity")) in {"S0", "S1"} or not bool(finding.get("waivable")):
            return self._block(command, "GSDLC10C_S0_S1_WAIVER_BLOCK", "S0/S1 and non-waivable findings cannot be waived.")
        reason = str(reason).strip()
        if not reason:
            return self._block(command, "GSDLC10C_WAIVER_REASON_BLOCK", "Waiver request requires a reason.")
        ttl = max(1, min(int(ttl_minutes), 1440))
        stable = {"report_id": report_id, "report_hash": report_hash, "finding_id": finding_id, "requester": actor, "reason": reason}
        waiver_id = "quality-waiver-" + _sha(stable)[:24]
        try:
            existing = self.store.load_waiver(waiver_id)
            return self._pass(command, "Quality waiver request already exists.", {"quality_waiver": self._waiver_view(existing), "idempotent": True})
        except KeyError:
            pass
        created = _now_dt()
        record = {
            "schema_id": WAIVER_SCHEMA_ID,
            "waiver_id": waiver_id,
            "story_test_plan_id": report.get("story_test_plan_id"),
            "story_test_plan_hash": report.get("story_test_plan_hash"),
            "report_id": report_id,
            "report_hash": report_hash,
            "finding_id": finding_id,
            "finding_severity": finding.get("severity"),
            "scope": {"story_execution_id": report.get("story_execution_id"), "finding_id": finding_id},
            "reason": reason,
            "requester": actor,
            "requester_role": actor_role,
            "status": "PENDING",
            "created_at_utc": created.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "expires_at_utc": (created + timedelta(minutes=ttl)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "approver": None,
            "approved_at_utc": None,
            "authority_source": authority_source,
        }
        self.store.save_waiver(record)
        return self._pass(command, "Quality waiver request recorded; separate owner approval is required.", {"quality_waiver": self._waiver_view(record), "idempotent": False})

    def decide_waiver(
        self,
        *,
        waiver_id: str,
        decision: str,
        actor: str,
        actor_role: str,
        authority_source: str = "human-session",
    ) -> CommandResult:
        command = "story quality waiver decision"
        if authority_source != "human-session" or authority_source.startswith("agent") or authority_source.startswith("model"):
            return self._block(command, "GSDLC10C_AGENT_WAIVER_AUTHORITY_BLOCK", "Agent/model authority cannot create, approve or widen a Quality waiver.")
        if actor_role != "owner":
            return self._block(command, "GSDLC10C_WAIVER_APPROVER_ROLE_BLOCK", "Only owner may approve/reject a Quality waiver.")
        try:
            waiver = self.store.load_waiver(waiver_id)
        except KeyError:
            return self._block(command, "GSDLC10C_WAIVER_NOT_FOUND", "Quality waiver was not found.")
        if waiver.get("status") != "PENDING":
            return self._block(command, "GSDLC10C_WAIVER_STATE_BLOCK", "Quality waiver is no longer pending.")
        if actor == waiver.get("requester"):
            return self._block(command, "GSDLC10C_WAIVER_SELF_APPROVAL_BLOCK", "Waiver requester cannot approve their own waiver.")
        expires = _parse_ts(str(waiver.get("expires_at_utc") or ""))
        if expires is None or expires <= _now_dt():
            return self._block(command, "GSDLC10C_WAIVER_EXPIRED_BLOCK", "Expired waiver request cannot be approved.")
        decision = str(decision).upper()
        if decision not in {"APPROVE", "REJECT"}:
            return self._block(command, "GSDLC10C_WAIVER_DECISION_BLOCK", "Waiver decision must be APPROVE or REJECT.")
        waiver["status"] = "APPROVED" if decision == "APPROVE" else "REJECTED"
        waiver["approver"] = actor
        waiver["approver_role"] = actor_role
        waiver["approved_at_utc"] = _now()
        waiver["authority_source"] = authority_source
        self.store.save_waiver(waiver)
        return self._pass(command, f"Quality waiver {waiver['status']} by separate owner authority.", {"quality_waiver": self._waiver_view(waiver)})

    def plan_remediation(
        self,
        *,
        report_id: str,
        report_hash: str,
        finding_id: str,
        mode: str,
        actor: str,
        actor_role: str,
        instruction: str = "",
        source_id: str | None = None,
        agent_mode: str = "mock",
    ) -> CommandResult:
        command = "story quality remediation plan"
        role_failure = self._human_role(command, actor_role, "human-session")
        if role_failure:
            return role_failure
        report, failure = self._exact_report(command, report_id, report_hash)
        if failure:
            return failure
        assert report is not None
        finding = next((row for row in report.get("findings", []) if row.get("finding_id") == finding_id and row.get("blocking")), None)
        if not finding:
            return self._block(command, "GSDLC10C_REMEDIATION_FINDING_BLOCK", "Remediation requires an open blocking finding from the exact report.")
        mode = str(mode).lower()
        if mode not in {"manual", "agent"}:
            return self._block(command, "GSDLC10C_REMEDIATION_MODE_BLOCK", "Remediation mode must be manual or agent.")
        proposal: dict[str, Any] | None = None
        tool_authority = {
            "contract": "ToolIntent -> PolicyEngine -> RBAC -> Approval -> ToolExecutionDecision",
            "model_route_grants_quality_authority": False,
            "model_route_grants_source_write": False,
            "tool_executed": False,
        }
        if mode == "agent":
            if self.agent_proposal_creator is None:
                return self._block(command, "GSDLC10C_AGENT_REMEDIATION_UNAVAILABLE", "Proposal-only Story Agent service is unavailable.")
            instruction = str(instruction).strip()
            if not instruction:
                return self._block(command, "GSDLC10C_AGENT_REMEDIATION_INSTRUCTION_BLOCK", "Agent remediation requires an explicit bounded instruction.")
            proposed = self.agent_proposal_creator(agent_type="coding", mode=agent_mode, instruction=instruction, source_id=source_id, actor=actor, actor_role=actor_role)
            if not proposed.ok:
                return CommandResult(command, False, proposed.exit_code, "Agent remediation proposal was blocked by its governed boundary.", data=proposed.data, findings=proposed.findings)
            proposal = deepcopy((proposed.data or {}).get("proposal") or {})
            decision = proposal.get("tool_execution_decision") or {}
            if decision.get("model_route_granted_permission") is not False or decision.get("tool_executed") is True:
                return self._block(command, "GSDLC10C_AGENT_AUTHORITY_ESCALATION_BLOCK", "Agent/model route unexpectedly obtained execution authority.")
            tool_authority = {
                **tool_authority,
                "tool_intent": deepcopy(proposal.get("tool_intent") or {}),
                "tool_execution_decision": deepcopy(decision),
                "proposal_id": proposal.get("proposal_id"),
            }
        stable = {
            "source_report_id": report_id,
            "source_report_hash": report_hash,
            "finding_id": finding_id,
            "mode": mode,
            "actor": actor,
            "proposal_id": None if proposal is None else proposal.get("proposal_id"),
        }
        trace_id = "remediation-trace-" + _sha(stable)[:24]
        try:
            existing = self.store.load_trace(trace_id)
            return self._pass(command, "Remediation trace already exists; idempotent result returned.", {"remediation_trace": existing, "idempotent": True})
        except KeyError:
            pass
        trace = {
            "schema_id": TRACE_SCHEMA_ID,
            "trace_id": trace_id,
            **stable,
            "story_test_plan_id": report.get("story_test_plan_id"),
            "story_test_plan_hash": report.get("story_test_plan_hash"),
            "finding": deepcopy(finding),
            "status": "PROPOSED",
            "created_at_utc": _now(),
            "source_change_handoff": {
                "route": "/story-code",
                "authority": "GSDLC-09 SourceDraft -> SourceChangePlan -> dry-run -> approval -> atomic apply",
                "source_mutation_performed": False,
                "manual_or_agent_proposal_only": True,
            },
            "step_action_advisor": self._advisor_projection(actor_role),
            "agent_proposal": proposal,
            "tool_authority": tool_authority,
            "retest": None,
            "resolved_at_utc": None,
            "network_used": False,
            "external_api_used": False,
        }
        self.store.save_trace(trace)
        return self._pass(command, "Remediation proposal created; source changes remain governed by GSDLC-09.", {"remediation_trace": trace, "idempotent": False})

    def plan_impacted_retest(
        self,
        *,
        trace_id: str,
        new_test_plan_id: str,
        new_test_plan_hash: str,
        actor: str,
        actor_role: str,
    ) -> CommandResult:
        command = "story quality impacted retest plan"
        role_failure = self._human_role(command, actor_role, "human-session")
        if role_failure:
            return role_failure
        try:
            trace = self.store.load_trace(trace_id)
        except KeyError:
            return self._block(command, "GSDLC10C_REMEDIATION_TRACE_NOT_FOUND", "RemediationTrace was not found.")
        plan, failure = self._approved_plan(command, new_test_plan_id, new_test_plan_hash)
        if failure:
            return failure
        assert plan is not None
        if new_test_plan_hash == trace.get("story_test_plan_hash"):
            return self._block(command, "GSDLC10C_RETEST_STALE_PLAN_BLOCK", "Impacted retest requires a successor StoryTestPlan after remediation.")
        created = self.validation_jobs_creator(test_plan_id=new_test_plan_id, test_plan_hash=new_test_plan_hash, actor=actor, actor_role=actor_role)
        if not created.ok:
            return CommandResult(command, False, created.exit_code, "Impacted retest job planning was blocked.", data=created.data, findings=created.findings)
        jobs = [dict(row) for row in (created.data or {}).get("jobs", [])]
        trace["status"] = "RETEST_PLANNED"
        trace["retest"] = {
            "story_test_plan_id": new_test_plan_id,
            "story_test_plan_hash": new_test_plan_hash,
            "test_impact_report_hash": plan.get("test_impact_report_hash"),
            "changed_paths": list(plan.get("changed_paths") or []),
            "jobs": [{"job_id": row.get("job_id"), "kind": row.get("story_validation_kind"), "status": row.get("story_validation_status")} for row in jobs],
            "scope_policy": "successor StoryTestPlan recalculates Test Impact; only resulting typed jobs are planned",
            "rerun_everything": False,
            "full_regression": False,
            "planned_at_utc": _now(),
        }
        self.store.save_trace(trace)
        return self._pass(command, "Impacted retest planned from successor StoryTestPlan; no broad rerun requested.", {"remediation_trace": trace, "jobs": jobs})

    def complete_retest(self, *, trace_id: str, actor: str, actor_role: str) -> CommandResult:
        command = "story quality impacted retest complete"
        role_failure = self._human_role(command, actor_role, "human-session")
        if role_failure:
            return role_failure
        try:
            trace = self.store.load_trace(trace_id)
        except KeyError:
            return self._block(command, "GSDLC10C_REMEDIATION_TRACE_NOT_FOUND", "RemediationTrace was not found.")
        retest = dict(trace.get("retest") or {})
        plan_id = str(retest.get("story_test_plan_id") or "")
        if not plan_id:
            return self._block(command, "GSDLC10C_RETEST_NOT_PLANNED_BLOCK", "RemediationTrace has no impacted retest plan.")
        listed = self.validation_jobs_lister(test_plan_id=plan_id)
        if not listed.ok:
            return listed
        latest = self._latest_jobs_by_kind([dict(row) for row in (listed.data or {}).get("jobs", [])])
        non_pass = [row for row in latest if str(row.get("story_validation_status") or "").upper() != "PASS"]
        if not latest or non_pass:
            return self._block(command, "GSDLC10C_RETEST_NOT_PASS_BLOCK", "All impacted retest jobs must reach PASS before resolving the finding.")
        trace["status"] = "RESOLVED"
        trace["resolved_at_utc"] = _now()
        trace["resolved_by"] = actor
        trace["retest"]["completed_jobs"] = [{"job_id": row.get("job_id"), "kind": row.get("story_validation_kind"), "status": row.get("story_validation_status")} for row in latest]
        self.store.save_trace(trace)
        finding_id = str(trace.get("finding_id") or "")
        try:
            finding = self.store.load_finding(finding_id)
        except KeyError:
            finding = None
        if finding:
            finding["status"] = "RESOLVED"
            finding["resolved_at_utc"] = _now()
            finding["resolved_by_trace_id"] = trace_id
            self.store.save_finding(finding)
        return self._pass(command, "Impacted retest PASS; finding provenance closed.", {"remediation_trace": trace, "resolved_finding_id": finding_id})

    def list_remediation(self, *, report_id: str) -> CommandResult:
        rows = self.store.list_traces(report_id)
        return self._pass("story quality remediation list", "Remediation traces loaded.", {"report_id": report_id, "remediation_traces": rows})

    def _approved_plan(self, command: str, test_plan_id: str, test_plan_hash: str) -> tuple[dict[str, Any] | None, CommandResult | None]:
        loaded = self.story_test_plan_loader(test_plan_id=test_plan_id)
        if not loaded.ok:
            return None, self._block(command, "GSDLC10C_TEST_PLAN_DEPENDENCY_BLOCK", "StoryTestPlan dependency could not be loaded.")
        plan = deepcopy((loaded.data or {}).get("story_test_plan") or {})
        if plan.get("test_plan_hash") != test_plan_hash:
            return None, self._block(command, "GSDLC10C_TEST_PLAN_HASH_BLOCK", "StoryTestPlan hash is stale or mismatched.")
        if plan.get("status") != "APPROVED":
            return None, self._block(command, "GSDLC10C_TEST_PLAN_STATUS_BLOCK", "StoryQualityGate requires an APPROVED StoryTestPlan.")
        if bool((plan.get("full_regression_signal") or {}).get("execution_authorized")):
            return None, self._block(command, "GSDLC10C_FULL_AUTHORITY_BLOCK", "GSDLC-10-C cannot authorize Full Regression execution.")
        return plan, None

    def _exact_report(self, command: str, report_id: str, report_hash: str) -> tuple[dict[str, Any] | None, CommandResult | None]:
        try:
            report = self.store.load_report(report_id)
        except KeyError:
            return None, self._block(command, "GSDLC10C_REPORT_NOT_FOUND", "StoryQualityReport was not found.")
        if report.get("report_hash") != report_hash:
            return None, self._block(command, "GSDLC10C_REPORT_HASH_BLOCK", "StoryQualityReport hash mismatch or stale client state.")
        if self._current_inputs_hash(report) != report.get("inputs_hash"):
            return None, self._block(command, "GSDLC10C_STALE_QUALITY_REPORT_BLOCK", "StoryQualityReport inputs changed; re-evaluate before this action.")
        return report, None

    def _current_inputs_hash(self, report: dict[str, Any]) -> str | None:
        loaded = self.story_test_plan_loader(test_plan_id=str(report.get("story_test_plan_id") or ""))
        if not loaded.ok:
            return None
        plan = deepcopy((loaded.data or {}).get("story_test_plan") or {})
        if plan.get("test_plan_hash") != report.get("story_test_plan_hash"):
            return None
        listed = self.validation_jobs_lister(test_plan_id=str(report.get("story_test_plan_id") or ""))
        if not listed.ok:
            return None
        latest = self._latest_jobs_by_kind([dict(row) for row in (listed.data or {}).get("jobs", [])])
        supplemental = self.store.list_findings(str(report.get("story_test_plan_id") or ""))
        waivers = self._waiver_projection(str(report.get("story_test_plan_id") or ""))
        inputs = {
            "story_test_plan_id": report.get("story_test_plan_id"),
            "story_test_plan_hash": report.get("story_test_plan_hash"),
            "test_impact_report_hash": plan.get("test_impact_report_hash"),
            "source_change_plan_id": plan.get("source_change_plan_id"),
            "source_change_plan_hash": plan.get("source_change_plan_hash"),
            "changed_paths": sorted(str(x) for x in plan.get("changed_paths", [])),
            "jobs": [self._stable_job_input(row) for row in latest],
            "supplemental_findings": [self._stable_finding_input(row) for row in supplemental],
            "waivers": [self._stable_waiver_input(row) for row in waivers],
        }
        return _sha(inputs)

    @staticmethod
    def _latest_jobs_by_kind(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_kind: dict[str, dict[str, Any]] = {}
        for row in sorted(jobs, key=lambda item: (str(item.get("created_at") or ""), str(item.get("job_id") or ""))):
            kind = str(row.get("story_validation_kind") or row.get("capability_id") or "unknown")
            by_kind[kind] = row
        return [by_kind[key] for key in sorted(by_kind)]

    @staticmethod
    def _job_findings(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for job in jobs:
            status = str(job.get("story_validation_status") or job.get("status") or "UNKNOWN").upper()
            kind = str(job.get("story_validation_kind") or job.get("capability_id") or "unknown")
            if status in TERMINAL_PASS:
                continue
            if status in BLOCKING_JOB_STATES:
                severity = "S1"
                message = f"Required {kind} validation is {status}; COMMIT_READY is forbidden."
            elif status in PENDING_JOB_STATES:
                severity = "S1"
                message = f"Required {kind} validation is still {status}; COMMIT_READY waits for terminal PASS."
            else:
                severity = "S1"
                message = f"Required {kind} validation has unsupported state {status}; fail closed."
            rows.append({
                "finding_id": f"validation-{kind}-{str(job.get('job_id') or '')[:16]}",
                "origin": "validation",
                "severity": severity,
                "message": message,
                "source_ref": str(job.get("job_id") or ""),
                "status": "OPEN",
                "waivable": False,
            })
        return rows

    @staticmethod
    def _traceability_findings(plan: dict[str, Any], jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        required = ["story_execution_id", "story_id", "source_change_plan_id", "source_change_plan_hash", "test_impact_report_hash"]
        missing = [key for key in required if not plan.get(key)]
        mismatched = [str(row.get("job_id")) for row in jobs if row.get("story_test_plan_id") != plan.get("test_plan_id") or row.get("story_test_plan_hash") != plan.get("test_plan_hash")]
        rows: list[dict[str, Any]] = []
        if missing:
            rows.append({"finding_id": "traceability-plan-binding", "origin": "traceability", "severity": "S1", "message": "StoryQualityReport input is missing required traceability fields: " + ", ".join(missing), "source_ref": str(plan.get("test_plan_id") or ""), "status": "OPEN", "waivable": False})
        if mismatched:
            rows.append({"finding_id": "traceability-job-plan-binding", "origin": "traceability", "severity": "S1", "message": "StoryValidationJob plan binding mismatch: " + ", ".join(mismatched), "source_ref": str(plan.get("test_plan_id") or ""), "status": "OPEN", "waivable": False})
        return rows

    def _waiver_projection(self, test_plan_id: str) -> list[dict[str, Any]]:
        now = _now_dt()
        rows: list[dict[str, Any]] = []
        for waiver in self.store.list_waivers(test_plan_id):
            item = self._waiver_view(waiver)
            expires = _parse_ts(str(waiver.get("expires_at_utc") or ""))
            item["expired"] = expires is None or expires <= now
            item["effective"] = waiver.get("status") == "APPROVED" and not item["expired"] and waiver.get("finding_severity") in {"S2", "S3"} and waiver.get("approver") != waiver.get("requester") and waiver.get("authority_source") == "human-session"
            rows.append(item)
        return rows

    @staticmethod
    def _waiver_view(waiver: dict[str, Any]) -> dict[str, Any]:
        keys = ("schema_id", "waiver_id", "story_test_plan_id", "story_test_plan_hash", "report_id", "report_hash", "finding_id", "finding_severity", "scope", "reason", "requester", "requester_role", "status", "created_at_utc", "expires_at_utc", "approver", "approver_role", "approved_at_utc", "authority_source")
        return {key: deepcopy(waiver.get(key)) for key in keys if key in waiver}

    @staticmethod
    def _stable_job_input(job: dict[str, Any]) -> dict[str, Any]:
        summary = dict(job.get("result_summary") or {})
        return {
            "job_id": job.get("job_id"),
            "kind": job.get("story_validation_kind"),
            "status": str(job.get("story_validation_status") or job.get("status") or "").upper(),
            "story_test_plan_id": job.get("story_test_plan_id"),
            "story_test_plan_hash": job.get("story_test_plan_hash"),
            "artifact_refs": list(job.get("artifact_refs") or []),
            "result_summary": {key: summary.get(key) for key in sorted(summary)},
            "retry_count": int(job.get("retry_count") or 0),
            "retry_of_job_id": (job.get("operational") or {}).get("retry_of_job_id"),
        }

    @staticmethod
    def _stable_finding_input(row: dict[str, Any]) -> dict[str, Any]:
        return {key: row.get(key) for key in ("finding_id", "origin", "severity", "message", "source_ref", "status", "resolved_by_trace_id")}

    @staticmethod
    def _stable_waiver_input(row: dict[str, Any]) -> dict[str, Any]:
        return {key: row.get(key) for key in ("waiver_id", "finding_id", "finding_severity", "status", "requester", "approver", "expires_at_utc", "authority_source", "effective", "expired")}

    @staticmethod
    def _advisor_projection(actor_role: str) -> dict[str, Any]:
        return {
            "schema_id": "DEVPL-GSDLC-10-C-STEP-ACTION-ADVISOR-V1",
            "advisor_contract": "StepActionAdvisor",
            "status": "PASS" if actor_role in {"owner", "developer"} else "BLOCK",
            "recommended_action_id": "quality-remediation-manual",
            "actions": [
                {
                    "action_id": "quality-remediation-manual",
                    "kind": "MANUAL",
                    "label": "Corregir en Story Code Workbench",
                    "availability": "AVAILABLE" if actor_role in {"owner", "developer"} else "BLOCKED",
                    "navigation_target": "/story-code",
                    "source_mutation_authority": "GSDLC-09 policy/RBAC/approval",
                    "quality_authority_granted": False,
                },
                {
                    "action_id": "quality-remediation-agent-proposal",
                    "kind": "AGENT",
                    "label": "Solicitar propuesta agentic",
                    "availability": "AVAILABLE" if actor_role in {"owner", "developer"} else "BLOCKED",
                    "navigation_target": "/story-code",
                    "proposal_only": True,
                    "tool_contract": "ToolIntent",
                    "model_route_grants_quality_authority": False,
                    "model_route_grants_source_write": False,
                },
            ],
            "source_refs": ["src/devpilot_core/guided_sdlc/step_action_advisor.py", "src/devpilot_core/application/story_agent_assist_service.py"],
        }

    @staticmethod
    def _human_role(command: str, actor_role: str, authority_source: str) -> CommandResult | None:
        if authority_source != "human-session" or authority_source.startswith("agent") or authority_source.startswith("model"):
            return StoryQualityGateApplicationService._block(command, "GSDLC10C_AGENT_AUTHORITY_BLOCK", "Agent/model authority cannot make Quality decisions or mutate waiver state.")
        if actor_role not in {"owner", "developer"}:
            return StoryQualityGateApplicationService._block(command, "GSDLC10C_ROLE_BLOCK", "Story Quality operations require authenticated owner/developer human role.")
        return None

    @staticmethod
    def _pass(command: str, message: str, data: dict[str, Any]) -> CommandResult:
        return CommandResult(command, True, ExitCode.PASS, message, data={**data, "network_used": False, "external_api_used": False, "full_regression_started": False}, findings=[Finding("GSDLC10C_PASS", message, Severity.INFO)])

    @staticmethod
    def _block(command: str, code: str, message: str) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={"network_used": False, "external_api_used": False, "full_regression_started": False}, findings=[Finding(code, message, Severity.BLOCK)])
