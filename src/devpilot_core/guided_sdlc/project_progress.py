from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .models import (
    ArtifactLifecycleStatus,
    EngineeringLifecycleStatus,
    GateStatus,
    MIPSoftwarePhase,
    QualityLifecycleStatus,
    RevalidationStatus,
    WorkspaceEngineeringState,
    contains_secret_like_material,
)
from .workflow_engine import (
    TransitionCatalog,
    TransitionEvidence,
    TransitionEvaluation,
    TransitionSpec,
    WorkflowEngine,
)

PROJECT_STATUS_SCHEMA_ID = "SCHEMA-DEVPL-GUIDED-SDLC-PROJECT-STATUS-V1"
PROJECT_STATUS_SCHEMA_VERSION = "1.0"
NEXT_ACTION_SCHEMA_ID = "SCHEMA-DEVPL-GUIDED-SDLC-NEXT-ACTION-V1"
NEXT_ACTION_SCHEMA_VERSION = "1.0"

_ACTION_PRIORITIES = {
    "INSPECT_STATE": 10,
    "REVALIDATE": 20,
    "RESOLVE_BLOCKER": 30,
    "OBTAIN_APPROVAL": 40,
    "CONTINUE_STEP": 50,
    "ADVANCE_TRANSITION": 60,
    "COMPLETE": 70,
}

_READY_ARTIFACT_STATUSES = {
    ArtifactLifecycleStatus.APPROVED.value,
    ArtifactLifecycleStatus.FROZEN.value,
}
_ATTENTION_ARTIFACT_STATUSES = {
    ArtifactLifecycleStatus.MISSING.value,
    ArtifactLifecycleStatus.FINDINGS.value,
    ArtifactLifecycleStatus.APPROVAL_REQUIRED.value,
    ArtifactLifecycleStatus.REVALIDATION_REQUIRED.value,
}
_QUALITY_ORDER = {
    QualityLifecycleStatus.BLOCK.value: 4,
    QualityLifecycleStatus.REVALIDATION_REQUIRED.value: 4,
    QualityLifecycleStatus.WARN.value: 3,
    QualityLifecycleStatus.PASS.value: 2,
    QualityLifecycleStatus.NOT_EVALUATED.value: 1,
}


class ProjectProgressError(ValueError):
    pass


def _bounded_text(value: Any, *, default: str = "unknown", max_len: int = 512) -> str:
    text = str(value if value is not None else default)
    return text[:max_len]


def _safe_identifier(row: Mapping[str, Any], *keys: str, default: str) -> str:
    for key in keys:
        if row.get(key):
            return _bounded_text(row[key], default=default, max_len=256)
    return default


def _sorted_unique_strings(values: Iterable[Any]) -> tuple[str, ...]:
    return tuple(sorted({_bounded_text(value, max_len=512) for value in values if value is not None}))


@dataclass(frozen=True)
class NextAction:
    action_id: str
    kind: str
    priority: int
    reason_code: str
    explanation: str
    target_phase: str | None
    target_step: str | None
    transition_id: str | None
    navigation_target: str
    required_prerequisites: tuple[str, ...]
    approval_needed: bool
    mutating: bool
    dry_run_required: bool
    available: bool
    disabled_reason: str | None
    expected_evidence: tuple[str, ...]
    source_state_fingerprint: str | None
    schema_id: str = NEXT_ACTION_SCHEMA_ID
    schema_version: str = NEXT_ACTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.kind not in _ACTION_PRIORITIES:
            raise ProjectProgressError(f"unsupported next-action kind: {self.kind}")
        if self.priority != _ACTION_PRIORITIES[self.kind]:
            raise ProjectProgressError(f"priority mismatch for {self.kind}")
        findings = contains_secret_like_material(self.to_payload())
        if findings:
            raise ProjectProgressError(f"secret-like material forbidden in NextAction: {findings[:5]}")

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "action_id": self.action_id,
            "kind": self.kind,
            "priority": self.priority,
            "reason_code": self.reason_code,
            "explanation": self.explanation,
            "target_phase": self.target_phase,
            "target_step": self.target_step,
            "transition_id": self.transition_id,
            "navigation_target": self.navigation_target,
            "required_prerequisites": list(self.required_prerequisites),
            "approval_needed": self.approval_needed,
            "mutating": self.mutating,
            "dry_run_required": self.dry_run_required,
            "available": self.available,
            "disabled_reason": self.disabled_reason,
            "expected_evidence": list(self.expected_evidence),
            "source_state_fingerprint": self.source_state_fingerprint,
            "executes_action": False,
            "network_used": False,
            "external_api_used": False,
            "source_mutations_performed": False,
        }

    def fingerprint(self) -> str:
        raw = json.dumps(self.to_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProjectStatus:
    workspace_id: str
    project_id: str
    phase: str
    current_step: str
    lifecycle_status: str
    progress: dict[str, Any]
    mipsoftware: dict[str, Any]
    miasi: dict[str, Any]
    artifact_readiness: dict[str, Any]
    planning: dict[str, Any]
    blockers: tuple[dict[str, Any], ...]
    pending_approvals: tuple[dict[str, Any], ...]
    quality: dict[str, Any]
    git: dict[str, Any]
    revalidation: dict[str, Any]
    model_budget: dict[str, Any]
    freshness: dict[str, Any]
    source_refs: tuple[str, ...]
    next_action_ref: str
    reason: str | None
    schema_id: str = PROJECT_STATUS_SCHEMA_ID
    schema_version: str = PROJECT_STATUS_SCHEMA_VERSION

    def __post_init__(self) -> None:
        payload = self.to_payload()
        # `token_budget` is an intentional cost-control field, not a credential.
        # Remove only that numeric/null value from the generic secret-key scan.
        scan_payload = dict(payload)
        scan_budget = dict(scan_payload.get("model_budget") or {})
        scan_budget.pop("token_budget", None)
        scan_payload["model_budget"] = scan_budget
        findings = contains_secret_like_material(scan_payload)
        if findings:
            raise ProjectProgressError(f"secret-like material forbidden in ProjectStatus: {findings[:5]}")

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "phase": self.phase,
            "current_step": self.current_step,
            "lifecycle_status": self.lifecycle_status,
            "progress": dict(self.progress),
            "mipsoftware": dict(self.mipsoftware),
            "miasi": dict(self.miasi),
            "artifact_readiness": dict(self.artifact_readiness),
            "planning": dict(self.planning),
            "blockers": [dict(row) for row in self.blockers],
            "pending_approvals": [dict(row) for row in self.pending_approvals],
            "quality": dict(self.quality),
            "git": dict(self.git),
            "revalidation": dict(self.revalidation),
            "model_budget": dict(self.model_budget),
            "freshness": dict(self.freshness),
            "source_refs": list(self.source_refs),
            "next_action_ref": self.next_action_ref,
            "reason": self.reason,
            "network_used": False,
            "external_api_used": False,
            "source_mutations_performed": False,
        }

    def fingerprint(self) -> str:
        raw = json.dumps(self.to_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProjectProjection:
    status: ProjectStatus
    next_action: NextAction

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": self.status.to_payload(),
            "next_action": self.next_action.to_payload(),
        }


class ProjectProgressEngine:
    """Deterministic projection over WorkspaceEngineeringState + WorkflowEngine.

    GSDLC-01-C is read-only: it derives status and recommendation but never
    persists state, executes transitions, calls an LLM, reads Git directly or
    invokes external services.
    """

    def __init__(self, workflow_engine: WorkflowEngine) -> None:
        self.workflow_engine = workflow_engine
        self.catalog = workflow_engine.catalog
        self._phases = tuple(MIPSoftwarePhase)

    def project(
        self,
        state: WorkspaceEngineeringState,
        *,
        observed_at_utc: str,
        expected_state_fingerprint: str | None = None,
    ) -> ProjectProjection:
        state_fp = state.fingerprint()
        next_action = self._next_action(state)
        status = ProjectStatus(
            workspace_id=state.workspace_id,
            project_id=state.project_id,
            phase=state.phase.value,
            current_step=state.current_step,
            lifecycle_status=state.lifecycle_status.value,
            progress=self._progress(state),
            mipsoftware=self._mipsoftware_summary(state),
            miasi=self._miasi_summary(),
            artifact_readiness=self._artifact_summary(state),
            planning=self._planning_summary(state),
            blockers=self._blockers(state),
            pending_approvals=self._pending_approvals(state),
            quality=self._quality_summary(state),
            git=self._git_summary(state),
            revalidation=self._revalidation_summary(state),
            model_budget={
                "status": "NOT_AVAILABLE",
                "reason_code": "GSDLC_06_NOT_IMPLEMENTED",
                "model_route": None,
                "token_budget": None,
                "cost_budget_usd": None,
            },
            freshness=self._freshness(
                state_fp,
                observed_at_utc=observed_at_utc,
                expected_state_fingerprint=expected_state_fingerprint,
            ),
            source_refs=_sorted_unique_strings(
                (
                    f"workspace-state:{state.schema_id}:{state.schema_version}:{state_fp}",
                    f"transition-catalog:{self.catalog.catalog_id}:{self.catalog.catalog_version}",
                    "standard:MIPS-DOC-003",
                    "architecture:ADR-GSDLC-001",
                )
            ),
            next_action_ref=next_action.action_id,
            reason=None,
        )
        return ProjectProjection(status=status, next_action=next_action)

    @staticmethod
    def unknown(
        *,
        workspace_id: str,
        observed_at_utc: str,
        reason_code: str = "WORKSPACE_ENGINEERING_STATE_UNKNOWN",
    ) -> ProjectProjection:
        action = NextAction(
            action_id="next.inspect-state",
            kind="INSPECT_STATE",
            priority=_ACTION_PRIORITIES["INSPECT_STATE"],
            reason_code=reason_code,
            explanation="Workspace engineering state cannot be projected deterministically.",
            target_phase=None,
            target_step=None,
            transition_id=None,
            navigation_target="project-status/state-diagnostics",
            required_prerequisites=(),
            approval_needed=False,
            mutating=False,
            dry_run_required=True,
            available=False,
            disabled_reason="STATE_AUTHORITY_UNAVAILABLE",
            expected_evidence=("workspace-engineering-state",),
            source_state_fingerprint=None,
        )
        status = ProjectStatus(
            workspace_id=workspace_id or "unknown",
            project_id="unknown",
            phase="UNKNOWN",
            current_step="unknown",
            lifecycle_status="UNKNOWN",
            progress={
                "completed_phases": None,
                "total_phase_transitions": len(tuple(MIPSoftwarePhase)) - 1,
                "percent": None,
                "terminal": False,
            },
            mipsoftware={"status": "UNKNOWN", "phase_number": None, "total_phases": len(tuple(MIPSoftwarePhase)) - 1},
            miasi={"status": "UNKNOWN", "reason_code": "MIASI_APPLICABILITY_NOT_MATERIALIZED_IN_STATE_V1"},
            artifact_readiness={"status": "UNKNOWN", "total": 0, "ready": 0, "attention": 0, "counts": {}},
            planning={"status": "UNKNOWN", "total": 0, "counts": {}},
            blockers=(),
            pending_approvals=(),
            quality={"status": "UNKNOWN", "reason_code": "STATE_AUTHORITY_UNAVAILABLE", "counts": {}, "references": []},
            git={"status": "UNKNOWN", "head": None, "branch": None, "dirty": None, "fingerprint": None},
            revalidation={"status": "UNKNOWN", "reason_codes": []},
            model_budget={
                "status": "NOT_AVAILABLE",
                "reason_code": "GSDLC_06_NOT_IMPLEMENTED",
                "model_route": None,
                "token_budget": None,
                "cost_budget_usd": None,
            },
            freshness={
                "status": "UNKNOWN",
                "reason_code": reason_code,
                "observed_at_utc": observed_at_utc,
                "state_fingerprint": None,
                "expected_state_fingerprint": None,
            },
            source_refs=("workspace-engineering-state:unavailable",),
            next_action_ref=action.action_id,
            reason="unknown",
        )
        return ProjectProjection(status=status, next_action=action)

    def _progress(self, state: WorkspaceEngineeringState) -> dict[str, Any]:
        try:
            index = self._phases.index(state.phase)
        except ValueError as exc:
            raise ProjectProgressError(f"phase not in MIPSoftware vocabulary: {state.phase}") from exc
        total = len(self._phases) - 1
        percent = round((index / total) * 100.0, 2) if total else 100.0
        terminal = state.phase == MIPSoftwarePhase.RETIREMENT and state.lifecycle_status == EngineeringLifecycleStatus.RELEASED
        return {
            "completed_phases": index,
            "total_phase_transitions": total,
            "percent": 100.0 if terminal else percent,
            "terminal": terminal,
        }

    def _mipsoftware_summary(self, state: WorkspaceEngineeringState) -> dict[str, Any]:
        index = self._phases.index(state.phase)
        return {
            "status": "ACTIVE" if state.phase != MIPSoftwarePhase.NOT_STARTED else "NOT_STARTED",
            "phase": state.phase.value,
            "phase_number": index - 1 if index > 0 else None,
            "total_phases": len(self._phases) - 1,
            "current_step": state.current_step,
            "source_standard": "MIPS-DOC-003",
        }

    @staticmethod
    def _miasi_summary() -> dict[str, Any]:
        # WorkspaceEngineeringState v1 has no canonical MIASI applicability
        # field. 01-C must not infer applicability from filenames/content.
        return {
            "status": "UNKNOWN",
            "reason_code": "MIASI_APPLICABILITY_NOT_MATERIALIZED_IN_STATE_V1",
            "source_ref": "ADR-0001/MIPSoftware+MIASI",
        }

    @staticmethod
    def _artifact_summary(state: WorkspaceEngineeringState) -> dict[str, Any]:
        counts: dict[str, int] = {}
        refs: list[str] = []
        for row in state.artifacts:
            status = _bounded_text(row.get("status"), default="UNKNOWN", max_len=64)
            counts[status] = counts.get(status, 0) + 1
            refs.append(_safe_identifier(row, "artifact_id", "id", "path", default="artifact:unknown"))
        total = len(state.artifacts)
        ready = sum(counts.get(status, 0) for status in _READY_ARTIFACT_STATUSES)
        attention = sum(counts.get(status, 0) for status in _ATTENTION_ARTIFACT_STATUSES)
        if total == 0:
            summary_status = "UNKNOWN"
        elif attention:
            summary_status = "ATTENTION_REQUIRED"
        elif ready == total:
            summary_status = "READY"
        else:
            summary_status = "IN_PROGRESS"
        return {
            "status": summary_status,
            "total": total,
            "ready": ready,
            "attention": attention,
            "counts": dict(sorted(counts.items())),
            "references": list(_sorted_unique_strings(refs)),
        }

    @staticmethod
    def _planning_summary(state: WorkspaceEngineeringState) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for row in state.planning:
            status = _bounded_text(row.get("status"), default="UNKNOWN", max_len=64)
            counts[status] = counts.get(status, 0) + 1
        return {
            "status": "UNKNOWN" if not state.planning else "MATERIALIZED",
            "total": len(state.planning),
            "counts": dict(sorted(counts.items())),
        }

    @staticmethod
    def _blockers(state: WorkspaceEngineeringState) -> tuple[dict[str, Any], ...]:
        rows: list[dict[str, Any]] = []
        for index, row in enumerate(state.blockers):
            rows.append(
                {
                    "priority": int(row.get("priority", 100)),
                    "code": _safe_identifier(row, "code", "reason_code", default=f"STATE_BLOCKER_{index:03d}"),
                    "category": _safe_identifier(row, "category", default="state"),
                    "subject": _safe_identifier(row, "subject", "artifact_id", "gate_id", default=state.workspace_id),
                    "message": _bounded_text(row.get("message"), default="Workspace state contains a blocker."),
                    "source": "workspace-state",
                }
            )
        for index, row in enumerate(state.gates):
            status = _bounded_text(row.get("status"), default=GateStatus.UNKNOWN.value, max_len=64)
            if status != GateStatus.BLOCK.value:
                continue
            rows.append(
                {
                    "priority": int(row.get("priority", 90)),
                    "code": "GATE_BLOCK",
                    "category": "gate",
                    "subject": _safe_identifier(row, "gate_id", "id", default=f"gate:{index:03d}"),
                    "message": "A materialized workspace gate is BLOCK.",
                    "source": "workspace-state",
                }
            )
        return tuple(sorted(rows, key=lambda row: (row["priority"], row["code"], row["category"], row["subject"], row["message"])))

    @staticmethod
    def _pending_approvals(state: WorkspaceEngineeringState) -> tuple[dict[str, Any], ...]:
        rows: list[dict[str, Any]] = []
        sources = (("artifact", state.artifacts), ("planning", state.planning), ("gate", state.gates))
        for source_kind, items in sources:
            for index, row in enumerate(items):
                status = _bounded_text(row.get("approval_status"), default="", max_len=64)
                lifecycle = _bounded_text(row.get("status"), default="", max_len=64)
                if status not in {"PENDING", "APPROVAL_REQUIRED"} and lifecycle != ArtifactLifecycleStatus.APPROVAL_REQUIRED.value:
                    continue
                source_id = _safe_identifier(
                    row,
                    "approval_ref",
                    "approval_id",
                    "artifact_id",
                    "item_id",
                    "gate_id",
                    "id",
                    default=f"{source_kind}:{index:03d}",
                )
                rows.append(
                    {
                        "reference": source_id,
                        "status": "PENDING",
                        "source_kind": source_kind,
                    }
                )
        return tuple(sorted(rows, key=lambda row: (row["reference"], row["source_kind"])))

    @staticmethod
    def _quality_summary(state: WorkspaceEngineeringState) -> dict[str, Any]:
        counts: dict[str, int] = {}
        refs: list[str] = []
        for index, row in enumerate(state.quality):
            status = _bounded_text(row.get("status"), default=QualityLifecycleStatus.NOT_EVALUATED.value, max_len=64)
            counts[status] = counts.get(status, 0) + 1
            refs.append(_safe_identifier(row, "quality_id", "report_id", "id", default=f"quality:{index:03d}"))
        if not counts:
            return {
                "status": QualityLifecycleStatus.NOT_EVALUATED.value,
                "reason_code": "QUALITY_NOT_MATERIALIZED",
                "counts": {},
                "references": [],
            }
        overall = max(counts, key=lambda status: (_QUALITY_ORDER.get(status, 0), status))
        return {
            "status": overall,
            "reason_code": "QUALITY_SUMMARY_FROM_WORKSPACE_STATE",
            "counts": dict(sorted(counts.items())),
            "references": list(_sorted_unique_strings(refs)),
        }

    @staticmethod
    def _git_summary(state: WorkspaceEngineeringState) -> dict[str, Any]:
        allowed = {key: state.git.get(key) for key in ("head", "branch", "dirty", "fingerprint")}
        known = any(value is not None for value in allowed.values())
        return {"status": "KNOWN" if known else "UNKNOWN", **allowed}

    @staticmethod
    def _revalidation_summary(state: WorkspaceEngineeringState) -> dict[str, Any]:
        return {
            "status": _bounded_text(state.revalidation.get("status"), default=RevalidationStatus.NOT_REQUIRED.value, max_len=64),
            "reason_codes": list(_sorted_unique_strings(state.revalidation.get("reason_codes") or [])),
        }

    @staticmethod
    def _freshness(
        state_fingerprint: str,
        *,
        observed_at_utc: str,
        expected_state_fingerprint: str | None,
    ) -> dict[str, Any]:
        if expected_state_fingerprint is not None and expected_state_fingerprint != state_fingerprint:
            status = "STALE"
            reason = "STATE_FINGERPRINT_MISMATCH"
        else:
            status = "FRESH"
            reason = "STATE_FINGERPRINT_MATCH" if expected_state_fingerprint else "COMPUTED_FROM_CURRENT_LOADED_STATE"
        return {
            "status": status,
            "reason_code": reason,
            "observed_at_utc": observed_at_utc,
            "state_fingerprint": state_fingerprint,
            "expected_state_fingerprint": expected_state_fingerprint,
        }

    def _next_action(self, state: WorkspaceEngineeringState) -> NextAction:
        fp = state.fingerprint()

        # 1. Revalidation dominates all nominal workflow actions.
        if state.lifecycle_status == EngineeringLifecycleStatus.REVALIDATION_REQUIRED or state.revalidation.get("status") in {
            RevalidationStatus.REQUIRED.value,
            RevalidationStatus.IN_PROGRESS.value,
        }:
            return NextAction(
                action_id="next.revalidate",
                kind="REVALIDATE",
                priority=_ACTION_PRIORITIES["REVALIDATE"],
                reason_code="REVALIDATION_REQUIRED",
                explanation="External or governed-state drift requires revalidation before nominal progress.",
                target_phase=state.phase.value,
                target_step=state.current_step,
                transition_id=None,
                navigation_target="project-status/revalidation",
                required_prerequisites=(),
                approval_needed=False,
                mutating=True,
                dry_run_required=True,
                available=False,
                disabled_reason="RECONCILIATION_EXECUTION_NOT_IMPLEMENTED_UNTIL_GSDLC_01_D",
                expected_evidence=("reconciliation-report",),
                source_state_fingerprint=fp,
            )

        # 2. Materialized blockers/gates.
        status_blockers = self._blockers(state)
        if status_blockers:
            first = status_blockers[0]
            return NextAction(
                action_id=f"next.resolve-blocker.{first['code'].lower()}",
                kind="RESOLVE_BLOCKER",
                priority=_ACTION_PRIORITIES["RESOLVE_BLOCKER"],
                reason_code=first["code"],
                explanation=first["message"],
                target_phase=state.phase.value,
                target_step=state.current_step,
                transition_id=None,
                navigation_target="project-status/blockers",
                required_prerequisites=(),
                approval_needed=False,
                mutating=True,
                dry_run_required=True,
                available=False,
                disabled_reason="BLOCKER_RESOLUTION_SURFACE_NOT_IMPLEMENTED_IN_GSDLC_01_C",
                expected_evidence=(first["subject"],),
                source_state_fingerprint=fp,
            )

        spec = self._source_transition(state)
        if spec is not None:
            evidence = self._evidence_from_state(state, spec)
            evaluation = self.workflow_engine.evaluate(state, spec.transition_id, evidence)
            gate_blockers = tuple(row for row in evaluation.blockers if row.category == "gate")
            if gate_blockers:
                first = gate_blockers[0]
                return NextAction(
                    action_id=f"next.resolve-gate.{first.subject}",
                    kind="RESOLVE_BLOCKER",
                    priority=_ACTION_PRIORITIES["RESOLVE_BLOCKER"],
                    reason_code=first.code,
                    explanation=first.message,
                    target_phase=state.phase.value,
                    target_step=state.current_step,
                    transition_id=spec.transition_id,
                    navigation_target="project-status/gates",
                    required_prerequisites=spec.required_prerequisites,
                    approval_needed=spec.approval_required,
                    mutating=True,
                    dry_run_required=True,
                    available=False,
                    disabled_reason="GATE_MUST_BE_RESOLVED_BEFORE_TRANSITION",
                    expected_evidence=tuple(spec.evidence_refs),
                    source_state_fingerprint=fp,
                )

        # 3. Pending approvals.
        approvals = self._pending_approvals(state)
        if approvals:
            first = approvals[0]
            return NextAction(
                action_id=f"next.obtain-approval.{first['reference']}",
                kind="OBTAIN_APPROVAL",
                priority=_ACTION_PRIORITIES["OBTAIN_APPROVAL"],
                reason_code="APPROVAL_PENDING",
                explanation="A referenced engineering item requires human approval.",
                target_phase=state.phase.value,
                target_step=state.current_step,
                transition_id=spec.transition_id if spec else None,
                navigation_target="ui.approvals",
                required_prerequisites=spec.required_prerequisites if spec else (),
                approval_needed=True,
                mutating=False,
                dry_run_required=True,
                available=True,
                disabled_reason=None,
                expected_evidence=(first["reference"],),
                source_state_fingerprint=fp,
            )

        # 4. Artifact/prerequisite work.
        if spec is not None:
            evaluation = self.workflow_engine.evaluate(state, spec.transition_id, self._evidence_from_state(state, spec))
            work_blockers = tuple(row for row in evaluation.blockers if row.category in {"artifact", "prerequisite"})
            if work_blockers:
                first = work_blockers[0]
                return NextAction(
                    action_id=f"next.continue-step.{state.current_step}",
                    kind="CONTINUE_STEP",
                    priority=_ACTION_PRIORITIES["CONTINUE_STEP"],
                    reason_code=first.code,
                    explanation=first.message,
                    target_phase=state.phase.value,
                    target_step=state.current_step,
                    transition_id=spec.transition_id,
                    navigation_target="guided-sdlc/current-step",
                    required_prerequisites=spec.required_prerequisites,
                    approval_needed=spec.approval_required,
                    mutating=True,
                    dry_run_required=True,
                    available=False,
                    disabled_reason="STEP_WORKBENCH_NOT_IMPLEMENTED_IN_GSDLC_01_C",
                    expected_evidence=tuple(spec.evidence_refs),
                    source_state_fingerprint=fp,
                )

        if self._artifact_summary(state)["status"] in {"ATTENTION_REQUIRED", "IN_PROGRESS"}:
            return NextAction(
                action_id=f"next.continue-step.{state.current_step}",
                kind="CONTINUE_STEP",
                priority=_ACTION_PRIORITIES["CONTINUE_STEP"],
                reason_code="ARTIFACT_WORK_PENDING",
                explanation="Workspace artifacts are not yet all in a ready state.",
                target_phase=state.phase.value,
                target_step=state.current_step,
                transition_id=spec.transition_id if spec else None,
                navigation_target="guided-sdlc/current-step",
                required_prerequisites=spec.required_prerequisites if spec else (),
                approval_needed=spec.approval_required if spec else False,
                mutating=True,
                dry_run_required=True,
                available=False,
                disabled_reason="STEP_WORKBENCH_NOT_IMPLEMENTED_IN_GSDLC_01_C",
                expected_evidence=("artifact-readiness",),
                source_state_fingerprint=fp,
            )

        # 5. Next valid transition.
        if spec is not None:
            evaluation = self.workflow_engine.evaluate(state, spec.transition_id, self._evidence_from_state(state, spec))
            if evaluation.allowed:
                return NextAction(
                    action_id=f"next.preview-transition.{spec.transition_id}",
                    kind="ADVANCE_TRANSITION",
                    priority=_ACTION_PRIORITIES["ADVANCE_TRANSITION"],
                    reason_code="TRANSITION_READY",
                    explanation="The deterministic workflow contract allows the next transition.",
                    target_phase=spec.target_phase.value,
                    target_step=spec.target_step,
                    transition_id=spec.transition_id,
                    navigation_target="guided-sdlc/transition-preview",
                    required_prerequisites=spec.required_prerequisites,
                    approval_needed=spec.approval_required,
                    mutating=True,
                    dry_run_required=True,
                    available=True,
                    disabled_reason=None,
                    expected_evidence=tuple(spec.evidence_refs),
                    source_state_fingerprint=fp,
                )

        # 6. Completed/released terminal.
        terminal = state.phase == MIPSoftwarePhase.RETIREMENT and state.lifecycle_status == EngineeringLifecycleStatus.RELEASED
        if terminal:
            return NextAction(
                action_id="next.complete",
                kind="COMPLETE",
                priority=_ACTION_PRIORITIES["COMPLETE"],
                reason_code="LIFECYCLE_COMPLETE",
                explanation="MIPSoftware lifecycle is at RETIREMENT/RELEASED with no successor transition.",
                target_phase=state.phase.value,
                target_step=state.current_step,
                transition_id=None,
                navigation_target="project-status",
                required_prerequisites=(),
                approval_needed=False,
                mutating=False,
                dry_run_required=False,
                available=True,
                disabled_reason=None,
                expected_evidence=("workspace-engineering-state",),
                source_state_fingerprint=fp,
            )

        # Honest unknown instead of inventing a transition.
        return NextAction(
            action_id="next.inspect-state",
            kind="INSPECT_STATE",
            priority=_ACTION_PRIORITIES["INSPECT_STATE"],
            reason_code="NEXT_ACTION_UNKNOWN",
            explanation="No deterministic next action can be derived from the current state and catalog.",
            target_phase=state.phase.value,
            target_step=state.current_step,
            transition_id=None,
            navigation_target="project-status/state-diagnostics",
            required_prerequisites=(),
            approval_needed=False,
            mutating=False,
            dry_run_required=True,
            available=False,
            disabled_reason="NO_MATCHING_VERSIONED_TRANSITION",
            expected_evidence=("workspace-engineering-state", "workflow-transition-catalog"),
            source_state_fingerprint=fp,
        )

    def _source_transition(self, state: WorkspaceEngineeringState) -> TransitionSpec | None:
        candidates = [
            spec
            for spec in self.catalog.specs()
            if spec.source_phase == state.phase
            and spec.source_step == state.current_step
            and state.lifecycle_status in spec.source_lifecycle_statuses
        ]
        if not candidates:
            return None
        return sorted(candidates, key=lambda spec: spec.transition_id)[0]

    @staticmethod
    def _evidence_from_state(state: WorkspaceEngineeringState, spec: TransitionSpec) -> TransitionEvidence:
        gates: dict[str, str] = {}
        for row in state.gates:
            gate_id = row.get("gate_id") or row.get("id")
            status = row.get("status")
            if gate_id and status:
                gates[str(gate_id)] = str(status)

        artifacts: dict[str, str] = {}
        for row in state.artifacts:
            artifact_id = row.get("artifact_id") or row.get("id")
            status = row.get("status")
            if artifact_id and status:
                artifacts[str(artifact_id)] = str(status)

        approvals: dict[str, str] = {}
        for row in (*state.artifacts, *state.planning, *state.gates):
            key = row.get("approval_key") or row.get("approval_id") or row.get("approval_ref")
            status = row.get("approval_status")
            if key and status:
                approvals[str(key)] = str(status)

        prerequisites: dict[str, bool] = {}
        for row in state.planning:
            key = row.get("prerequisite_id")
            if key is not None and isinstance(row.get("satisfied"), bool):
                prerequisites[str(key)] = bool(row["satisfied"])

        # Baseline B encodes phase:<slug>:complete plus gate:<slug>:exit.
        # A PASS exit gate is deterministic evidence that the corresponding
        # phase-complete prerequisite is satisfied. No LLM inference is used.
        for prereq in spec.required_prerequisites:
            if prereq in prerequisites:
                continue
            if prereq.startswith("phase:") and prereq.endswith(":complete"):
                slug = prereq[len("phase:") : -len(":complete")]
                prerequisites[prereq] = gates.get(f"gate:{slug}:exit") == GateStatus.PASS.value

        return TransitionEvidence(
            prerequisites=prerequisites,
            gates=gates,
            artifacts=artifacts,
            approvals=approvals,
            references=(),
        )
