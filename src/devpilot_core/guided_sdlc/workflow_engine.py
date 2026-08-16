from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping

from .models import (
    ArtifactLifecycleStatus,
    EngineeringLifecycleStatus,
    GateStatus,
    MIPSoftwarePhase,
    RevalidationStatus,
    WorkspaceEngineeringState,
    contains_secret_like_material,
)


REPORT_SCHEMA_ID = "SCHEMA-DEVPL-GUIDED-SDLC-TRANSITION-REPORT-V1"
REPORT_SCHEMA_VERSION = "1.0"


class WorkflowEngineError(ValueError):
    pass


@dataclass(frozen=True)
class TransitionEvidence:
    prerequisites: Mapping[str, bool]
    gates: Mapping[str, str]
    artifacts: Mapping[str, str]
    approvals: Mapping[str, str]
    references: tuple[str, ...] = ()

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any] | None) -> "TransitionEvidence":
        data = dict(payload or {})
        allowed = {"prerequisites", "gates", "artifacts", "approvals", "references"}
        unexpected = sorted(set(data) - allowed)
        if unexpected:
            raise WorkflowEngineError(f"unexpected transition evidence fields: {unexpected}")
        secret_paths = contains_secret_like_material(data)
        if secret_paths:
            raise WorkflowEngineError(f"secret-like material is forbidden in transition evidence: {secret_paths[:5]}")
        prerequisites = dict(data.get("prerequisites") or {})
        gates = dict(data.get("gates") or {})
        artifacts = dict(data.get("artifacts") or {})
        approvals = dict(data.get("approvals") or {})
        refs_raw = data.get("references") or []
        if not isinstance(refs_raw, (list, tuple)):
            raise WorkflowEngineError("references must be an array")
        if not all(isinstance(v, bool) for v in prerequisites.values()):
            raise WorkflowEngineError("prerequisite values must be boolean")
        for key, value in gates.items():
            if str(value) not in {x.value for x in GateStatus}:
                raise WorkflowEngineError(f"unsupported gate status for {key}: {value}")
        artifact_values = {x.value for x in ArtifactLifecycleStatus}
        for key, value in artifacts.items():
            if str(value) not in artifact_values:
                raise WorkflowEngineError(f"unsupported artifact status for {key}: {value}")
        for key, value in approvals.items():
            if str(value) not in {"PENDING", "APPROVED", "DENIED", "REVOKED", "EXPIRED"}:
                raise WorkflowEngineError(f"unsupported approval status for {key}: {value}")
        return cls(
            prerequisites={str(k): bool(v) for k, v in prerequisites.items()},
            gates={str(k): str(v) for k, v in gates.items()},
            artifacts={str(k): str(v) for k, v in artifacts.items()},
            approvals={str(k): str(v) for k, v in approvals.items()},
            references=tuple(str(x) for x in refs_raw),
        )


@dataclass(frozen=True, order=True)
class TransitionBlocker:
    priority: int
    code: str
    category: str
    subject: str
    message: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "category": self.category,
            "subject": self.subject,
            "message": self.message,
            "priority": self.priority,
        }


@dataclass(frozen=True)
class TransitionSpec:
    transition_id: str
    version: str
    source_phase: MIPSoftwarePhase
    source_step: str
    source_lifecycle_statuses: tuple[EngineeringLifecycleStatus, ...]
    target_phase: MIPSoftwarePhase
    target_step: str
    target_lifecycle_status: EngineeringLifecycleStatus
    required_prerequisites: tuple[str, ...]
    required_gates: tuple[dict[str, Any], ...]
    required_artifacts: tuple[dict[str, Any], ...]
    approval_required: bool
    approval_key: str | None
    approval_accepted_statuses: tuple[str, ...]
    risk_classification: str
    preview_allowed: bool
    evidence_refs: tuple[str, ...]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "TransitionSpec":
        data = dict(payload)
        try:
            source = dict(data["source"])
            target = dict(data["target"])
            approval = dict(data["approval"])
            source_lifecycle = tuple(EngineeringLifecycleStatus(str(x)) for x in source["lifecycle_statuses"])
            return cls(
                transition_id=str(data["transition_id"]),
                version=str(data["version"]),
                source_phase=MIPSoftwarePhase(str(source["phase"])),
                source_step=str(source["current_step"]),
                source_lifecycle_statuses=source_lifecycle,
                target_phase=MIPSoftwarePhase(str(target["phase"])),
                target_step=str(target["current_step"]),
                target_lifecycle_status=EngineeringLifecycleStatus(str(target["lifecycle_status"])),
                required_prerequisites=tuple(str(x) for x in data.get("required_prerequisites") or []),
                required_gates=tuple(dict(x) for x in data.get("required_gates") or []),
                required_artifacts=tuple(dict(x) for x in data.get("required_artifacts") or []),
                approval_required=bool(approval.get("required", False)),
                approval_key=(str(approval["approval_key"]) if approval.get("approval_key") is not None else None),
                approval_accepted_statuses=tuple(str(x) for x in approval.get("accepted_statuses") or []),
                risk_classification=str(data["risk_classification"]),
                preview_allowed=bool(data["preview_allowed"]),
                evidence_refs=tuple(str(x) for x in data.get("evidence_refs") or []),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise WorkflowEngineError(f"invalid transition spec: {exc}") from exc


class TransitionCatalog:
    def __init__(self, specs: list[TransitionSpec] | tuple[TransitionSpec, ...], *, catalog_id: str, catalog_version: str) -> None:
        ordered = tuple(specs)
        ids = [spec.transition_id for spec in ordered]
        if len(ids) != len(set(ids)):
            raise WorkflowEngineError("duplicate transition_id in catalog")
        self.catalog_id = catalog_id
        self.catalog_version = catalog_version
        self._specs = {spec.transition_id: spec for spec in ordered}

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "TransitionCatalog":
        data = dict(payload)
        if data.get("schema_id") != "SCHEMA-DEVPL-GUIDED-SDLC-TRANSITION-CATALOG-V1":
            raise WorkflowEngineError("unsupported transition catalog schema_id")
        if data.get("schema_version") != "1.0":
            raise WorkflowEngineError("unsupported transition catalog schema_version")
        rows = data.get("transitions")
        if not isinstance(rows, list) or not rows:
            raise WorkflowEngineError("transition catalog requires at least one transition")
        return cls(
            [TransitionSpec.from_payload(row) for row in rows],
            catalog_id=str(data["catalog_id"]),
            catalog_version=str(data["catalog_version"]),
        )

    @classmethod
    def load(cls, path: Path) -> "TransitionCatalog":
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WorkflowEngineError(f"transition catalog unreadable: {exc}") from exc
        if not isinstance(payload, dict):
            raise WorkflowEngineError("transition catalog root must be an object")
        return cls.from_payload(payload)

    def get(self, transition_id: str) -> TransitionSpec | None:
        return self._specs.get(transition_id)

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._specs))


@dataclass(frozen=True)
class TransitionEvaluation:
    transition_id: str
    decision: str
    reason_codes: tuple[str, ...]
    blockers: tuple[TransitionBlocker, ...]
    approval_required: bool
    approval_key: str | None
    approval_status: str | None
    source_state_fingerprint: str
    source: dict[str, Any]
    target: dict[str, Any] | None
    preview_allowed: bool
    warnings: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    @property
    def allowed(self) -> bool:
        return self.decision == "PASS"

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_id": REPORT_SCHEMA_ID,
            "schema_version": REPORT_SCHEMA_VERSION,
            "transition_id": self.transition_id,
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "blockers": [row.to_payload() for row in self.blockers],
            "approval": {
                "required": self.approval_required,
                "key": self.approval_key,
                "status": self.approval_status,
            },
            "source_state_fingerprint": self.source_state_fingerprint,
            "source": dict(self.source),
            "target": dict(self.target) if self.target is not None else None,
            "preview_allowed": self.preview_allowed,
            "warnings": list(self.warnings),
            "evidence_refs": list(self.evidence_refs),
            "network_used": False,
            "external_api_used": False,
            "source_mutations_performed": False,
        }

    def fingerprint(self) -> str:
        data = json.dumps(self.to_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(data.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TransitionPreview:
    evaluation: TransitionEvaluation
    successor_state: WorkspaceEngineeringState | None

    def to_payload(self) -> dict[str, Any]:
        return {
            "evaluation": self.evaluation.to_payload(),
            "successor_state": self.successor_state.to_payload() if self.successor_state is not None else None,
        }


class WorkflowEngine:
    """Pure deterministic evaluator for Guided SDLC transitions.

    It never writes WorkspaceEngineeringState and never accepts an LLM/model
    decision as authority. The only inputs are versioned state, a versioned
    catalog and deterministic evidence.
    """

    def __init__(self, catalog: TransitionCatalog) -> None:
        self.catalog = catalog

    @classmethod
    def from_catalog_path(cls, path: Path) -> "WorkflowEngine":
        return cls(TransitionCatalog.load(path))

    def evaluate(
        self,
        state: WorkspaceEngineeringState,
        transition_id: str,
        evidence: TransitionEvidence | Mapping[str, Any] | None = None,
    ) -> TransitionEvaluation:
        ev = evidence if isinstance(evidence, TransitionEvidence) else TransitionEvidence.from_payload(evidence)
        spec = self.catalog.get(transition_id)
        source = {
            "phase": state.phase.value,
            "current_step": state.current_step,
            "lifecycle_status": state.lifecycle_status.value,
            "sequence": state.sequence,
        }
        if spec is None:
            blocker = TransitionBlocker(
                10,
                "TRANSITION_UNKNOWN",
                "catalog",
                transition_id,
                "Transition id is not present in the versioned catalog.",
            )
            return TransitionEvaluation(
                transition_id=transition_id,
                decision="BLOCK",
                reason_codes=("TRANSITION_UNKNOWN",),
                blockers=(blocker,),
                approval_required=False,
                approval_key=None,
                approval_status=None,
                source_state_fingerprint=state.fingerprint(),
                source=source,
                target=None,
                preview_allowed=False,
                warnings=(),
                evidence_refs=tuple(sorted(set(ev.references))),
            )

        blockers: list[TransitionBlocker] = []
        warnings: list[str] = []
        reason_codes: set[str] = set()
        approval_status: str | None = None

        if state.lifecycle_status == EngineeringLifecycleStatus.REVALIDATION_REQUIRED or str(state.revalidation.get("status")) in {
            RevalidationStatus.REQUIRED.value,
            RevalidationStatus.IN_PROGRESS.value,
        }:
            blockers.append(
                TransitionBlocker(
                    20,
                    "STATE_REVALIDATION_REQUIRED",
                    "state",
                    state.workspace_id,
                    "WorkspaceEngineeringState requires reconciliation/revalidation before transition.",
                )
            )
        if state.lifecycle_status == EngineeringLifecycleStatus.BLOCKED:
            blockers.append(
                TransitionBlocker(
                    21,
                    "STATE_BLOCKED",
                    "state",
                    state.workspace_id,
                    "WorkspaceEngineeringState lifecycle is BLOCKED.",
                )
            )
        if state.phase != spec.source_phase:
            blockers.append(
                TransitionBlocker(
                    30,
                    "SOURCE_PHASE_MISMATCH",
                    "source",
                    state.phase.value,
                    f"Transition expects phase {spec.source_phase.value}.",
                )
            )
        if state.current_step != spec.source_step:
            blockers.append(
                TransitionBlocker(
                    31,
                    "SOURCE_STEP_MISMATCH",
                    "source",
                    state.current_step,
                    f"Transition expects current_step {spec.source_step}.",
                )
            )
        if state.lifecycle_status not in spec.source_lifecycle_statuses:
            blockers.append(
                TransitionBlocker(
                    32,
                    "SOURCE_LIFECYCLE_MISMATCH",
                    "source",
                    state.lifecycle_status.value,
                    "Lifecycle status is not allowed by transition source contract.",
                )
            )

        for prereq in sorted(spec.required_prerequisites):
            if ev.prerequisites.get(prereq) is not True:
                blockers.append(
                    TransitionBlocker(
                        40,
                        "PREREQUISITE_NOT_SATISFIED",
                        "prerequisite",
                        prereq,
                        "Required deterministic prerequisite is missing or false.",
                    )
                )

        for gate_rule in sorted(spec.required_gates, key=lambda row: str(row.get("gate_id", ""))):
            gate_id = str(gate_rule.get("gate_id", ""))
            accepted = tuple(str(x) for x in gate_rule.get("accepted_statuses") or [])
            status = ev.gates.get(gate_id, GateStatus.UNKNOWN.value)
            if status not in accepted:
                code = "GATE_BLOCK" if status == GateStatus.BLOCK.value else "GATE_NOT_SATISFIED"
                blockers.append(
                    TransitionBlocker(
                        50,
                        code,
                        "gate",
                        gate_id,
                        f"Gate status {status} is not accepted; expected one of {list(accepted)}.",
                    )
                )
            elif status == GateStatus.WARN.value:
                warnings.append(f"GATE_WARN:{gate_id}")
                reason_codes.add("GATE_WARN_ACCEPTED")

        for artifact_rule in sorted(spec.required_artifacts, key=lambda row: str(row.get("artifact_id", ""))):
            artifact_id = str(artifact_rule.get("artifact_id", ""))
            accepted = tuple(str(x) for x in artifact_rule.get("accepted_statuses") or [])
            status = ev.artifacts.get(artifact_id)
            if status not in accepted:
                blockers.append(
                    TransitionBlocker(
                        60,
                        "ARTIFACT_NOT_READY",
                        "artifact",
                        artifact_id,
                        f"Artifact status {status!r} is not accepted; expected one of {list(accepted)}.",
                    )
                )

        if spec.approval_required:
            approval_status = ev.approvals.get(spec.approval_key or "")
            if approval_status not in spec.approval_accepted_statuses:
                blockers.append(
                    TransitionBlocker(
                        70,
                        "APPROVAL_REQUIRED",
                        "approval",
                        spec.approval_key or "",
                        f"Approval status {approval_status!r} is not accepted.",
                    )
                )

        ordered_blockers = tuple(sorted(blockers))
        if ordered_blockers:
            reason_codes.update(blocker.code for blocker in ordered_blockers)
            decision = "BLOCK"
        else:
            reason_codes.add("TRANSITION_ALLOWED")
            decision = "PASS"

        target = {
            "phase": spec.target_phase.value,
            "current_step": spec.target_step,
            "lifecycle_status": spec.target_lifecycle_status.value,
        }

        return TransitionEvaluation(
            transition_id=transition_id,
            decision=decision,
            reason_codes=tuple(sorted(reason_codes)),
            blockers=ordered_blockers,
            approval_required=spec.approval_required,
            approval_key=spec.approval_key,
            approval_status=approval_status,
            source_state_fingerprint=state.fingerprint(),
            source=source,
            target=target,
            preview_allowed=spec.preview_allowed,
            warnings=tuple(sorted(warnings)),
            evidence_refs=tuple(sorted(set(spec.evidence_refs + ev.references))),
        )

    def preview_advance(
        self,
        state: WorkspaceEngineeringState,
        transition_id: str,
        evidence: TransitionEvidence | Mapping[str, Any] | None = None,
        *,
        updated_at_utc: str,
    ) -> TransitionPreview:
        evaluation = self.evaluate(state, transition_id, evidence)
        if not evaluation.allowed or not evaluation.preview_allowed:
            return TransitionPreview(evaluation=evaluation, successor_state=None)
        spec = self.catalog.get(transition_id)
        if spec is None:
            return TransitionPreview(evaluation=evaluation, successor_state=None)
        successor = replace(
            state,
            lifecycle_status=spec.target_lifecycle_status,
            phase=spec.target_phase,
            current_step=spec.target_step,
            sequence=state.sequence + 1,
            updated_at_utc=updated_at_utc,
            blockers=(),
            next_action_ref=None,
        )
        return TransitionPreview(evaluation=evaluation, successor_state=successor)
