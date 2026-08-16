from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

SCHEMA_ID = "SCHEMA-DEVPL-WORKSPACE-ENGINEERING-STATE-V1"
SCHEMA_VERSION = "1.0"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,256}$")
_SECRET_KEY_RE = re.compile(r"(?:password|passwd|secret|token|api[_-]?key|private[_-]?key|authorization|cookie)", re.I)
_SECRET_VALUE_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.I),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


class WorkspaceEngineeringStateError(ValueError):
    pass


class EngineeringLifecycleStatus(StrEnum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    READY_FOR_RELEASE = "READY_FOR_RELEASE"
    RELEASED = "RELEASED"


class MIPSoftwarePhase(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    INTAKE = "INTAKE"
    PROBLEM_DISCOVERY = "PROBLEM_DISCOVERY"
    BUSINESS_ANALYSIS = "BUSINESS_ANALYSIS"
    STAKEHOLDERS = "STAKEHOLDERS"
    REQUIREMENTS = "REQUIREMENTS"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    ARCHITECTURE = "ARCHITECTURE"
    DOMAIN_DESIGN = "DOMAIN_DESIGN"
    DATA_DESIGN = "DATA_DESIGN"
    INTERFACE_DESIGN = "INTERFACE_DESIGN"
    UX_UI_DESIGN = "UX_UI_DESIGN"
    QUALITY_PLAN = "QUALITY_PLAN"
    SECURITY_PLAN = "SECURITY_PLAN"
    TEST_PLAN = "TEST_PLAN"
    IMPLEMENTATION = "IMPLEMENTATION"
    INTEGRATION = "INTEGRATION"
    VERIFICATION = "VERIFICATION"
    VALIDATION = "VALIDATION"
    RELEASE = "RELEASE"
    DEPLOYMENT = "DEPLOYMENT"
    OPERATION = "OPERATION"
    MONITORING = "MONITORING"
    INCIDENT_MANAGEMENT = "INCIDENT_MANAGEMENT"
    MAINTENANCE = "MAINTENANCE"
    AUDIT = "AUDIT"
    RETIREMENT = "RETIREMENT"


class ArtifactLifecycleStatus(StrEnum):
    MISSING = "MISSING"
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    FINDINGS = "FINDINGS"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    FROZEN = "FROZEN"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"


class PlanningLifecycleStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    DRAFT = "DRAFT"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    FROZEN = "FROZEN"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"


class QualityLifecycleStatus(StrEnum):
    NOT_EVALUATED = "NOT_EVALUATED"
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"


class GateStatus(StrEnum):
    UNKNOWN = "UNKNOWN"
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"


class RevalidationStatus(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REQUIRED = "REQUIRED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


def _as_tuple_of_dicts(value: Any, field_name: str) -> tuple[dict[str, Any], ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise WorkspaceEngineeringStateError(f"{field_name} must be a list/tuple")
    result=[]
    for item in value:
        if not isinstance(item, Mapping):
            raise WorkspaceEngineeringStateError(f"{field_name} entries must be objects")
        result.append(dict(item))
    return tuple(result)


def contains_secret_like_material(value: Any, *, path: str = "$") -> list[str]:
    """Return paths containing forbidden secret-like keys/values.

    WorkspaceEngineeringState is intentionally metadata-only. This guard is
    conservative: secret-like content is rejected instead of redacted into a
    durable state record, so callers must store only references/fingerprints.
    """
    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            child = f"{path}.{key_text}"
            if _SECRET_KEY_RE.search(key_text):
                findings.append(child)
            findings.extend(contains_secret_like_material(item, path=child))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            findings.extend(contains_secret_like_material(item, path=f"{path}[{index}]"))
    elif isinstance(value, str):
        for pattern in _SECRET_VALUE_PATTERNS:
            if pattern.search(value):
                findings.append(path)
                break
    return findings


@dataclass(frozen=True)
class WorkspaceEngineeringState:
    workspace_id: str
    project_id: str
    workspace_root_fingerprint: str
    lifecycle_status: EngineeringLifecycleStatus
    phase: MIPSoftwarePhase
    current_step: str
    sequence: int
    created_at_utc: str
    updated_at_utc: str
    git: dict[str, Any] = field(default_factory=dict)
    artifacts: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    planning: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    quality: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    gates: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    blockers: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    revalidation: dict[str, Any] = field(default_factory=lambda: {"status": RevalidationStatus.NOT_REQUIRED.value, "reason_codes": []})
    source_fingerprints: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    next_action_ref: str | None = None
    schema_id: str = SCHEMA_ID
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_id != SCHEMA_ID or self.schema_version != SCHEMA_VERSION:
            raise WorkspaceEngineeringStateError("Unsupported WorkspaceEngineeringState schema identity")
        for label, value in (("workspace_id", self.workspace_id), ("project_id", self.project_id), ("current_step", self.current_step)):
            if not _ID_RE.fullmatch(value):
                raise WorkspaceEngineeringStateError(f"{label} must match {_ID_RE.pattern}")
        if not _SHA256_RE.fullmatch(self.workspace_root_fingerprint):
            raise WorkspaceEngineeringStateError("workspace_root_fingerprint must be lowercase SHA-256")
        if self.sequence < 0:
            raise WorkspaceEngineeringStateError("sequence must be >= 0")
        if not self.created_at_utc or not self.updated_at_utc:
            raise WorkspaceEngineeringStateError("created_at_utc and updated_at_utc are required")
        if self.next_action_ref is not None and not _ID_RE.fullmatch(self.next_action_ref):
            raise WorkspaceEngineeringStateError("next_action_ref must be a bounded identifier")
        if not isinstance(self.git, dict):
            raise WorkspaceEngineeringStateError("git must be an object")
        if not isinstance(self.revalidation, dict):
            raise WorkspaceEngineeringStateError("revalidation must be an object")
        if self.lifecycle_status == EngineeringLifecycleStatus.REVALIDATION_REQUIRED and self.revalidation.get("status") not in {"REQUIRED", "IN_PROGRESS"}:
            raise WorkspaceEngineeringStateError("REVALIDATION_REQUIRED lifecycle requires revalidation status REQUIRED/IN_PROGRESS")
        findings = contains_secret_like_material(self.to_payload())
        if findings:
            raise WorkspaceEngineeringStateError(f"secret-like material is forbidden in engineering state: {findings[:5]}")

    @classmethod
    def new(
        cls,
        *,
        workspace_id: str,
        project_id: str,
        workspace_root_fingerprint: str,
        created_at_utc: str,
        current_step: str = "idea-intake",
    ) -> "WorkspaceEngineeringState":
        return cls(
            workspace_id=workspace_id,
            project_id=project_id,
            workspace_root_fingerprint=workspace_root_fingerprint,
            lifecycle_status=EngineeringLifecycleStatus.NEW,
            phase=MIPSoftwarePhase.NOT_STARTED,
            current_step=current_step,
            sequence=0,
            created_at_utc=created_at_utc,
            updated_at_utc=created_at_utc,
            git={"head": None, "branch": None, "dirty": None, "fingerprint": None},
            revalidation={"status": RevalidationStatus.NOT_REQUIRED.value, "reason_codes": []},
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "WorkspaceEngineeringState":
        data=dict(payload)
        try:
            return cls(
                schema_id=str(data["schema_id"]),
                schema_version=str(data["schema_version"]),
                workspace_id=str(data["workspace_id"]),
                project_id=str(data["project_id"]),
                workspace_root_fingerprint=str(data["workspace_root_fingerprint"]),
                lifecycle_status=EngineeringLifecycleStatus(str(data["lifecycle_status"])),
                phase=MIPSoftwarePhase(str(data["phase"])),
                current_step=str(data["current_step"]),
                sequence=int(data["sequence"]),
                created_at_utc=str(data["created_at_utc"]),
                updated_at_utc=str(data["updated_at_utc"]),
                git=dict(data.get("git") or {}),
                artifacts=_as_tuple_of_dicts(data.get("artifacts"), "artifacts"),
                planning=_as_tuple_of_dicts(data.get("planning"), "planning"),
                quality=_as_tuple_of_dicts(data.get("quality"), "quality"),
                gates=_as_tuple_of_dicts(data.get("gates"), "gates"),
                blockers=_as_tuple_of_dicts(data.get("blockers"), "blockers"),
                revalidation=dict(data.get("revalidation") or {}),
                source_fingerprints=_as_tuple_of_dicts(data.get("source_fingerprints"), "source_fingerprints"),
                next_action_ref=data.get("next_action_ref"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, WorkspaceEngineeringStateError):
                raise
            raise WorkspaceEngineeringStateError(f"invalid WorkspaceEngineeringState payload: {exc}") from exc

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "workspace_root_fingerprint": self.workspace_root_fingerprint,
            "lifecycle_status": self.lifecycle_status.value,
            "phase": self.phase.value,
            "current_step": self.current_step,
            "sequence": self.sequence,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
            "git": dict(self.git),
            "artifacts": [dict(x) for x in self.artifacts],
            "planning": [dict(x) for x in self.planning],
            "quality": [dict(x) for x in self.quality],
            "gates": [dict(x) for x in self.gates],
            "blockers": [dict(x) for x in self.blockers],
            "revalidation": dict(self.revalidation),
            "source_fingerprints": [dict(x) for x in self.source_fingerprints],
            "next_action_ref": self.next_action_ref,
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def fingerprint(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()
