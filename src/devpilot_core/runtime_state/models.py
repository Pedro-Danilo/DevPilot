from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

RUNTIME_STATE_POLICY_CONTRACT = "RuntimeStatePolicy"
RUNTIME_STATE_INVENTORY_CONTRACT = "RuntimeStateInventory"
RUNTIME_STATE_INVENTORY_SCHEMA_ID = "SCHEMA-DEVPL-RUNTIME-STATE-INVENTORY-V1"
RUNTIME_STATE_INVENTORY_ID = "devpilot-runtime-state-inventory"
POST_H_008_B_CREATED_BY = "POST-H-008-B"


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class RuntimeViolationSeverity(str, Enum):
    INFO = "info"
    WARN = "warn"
    BLOCK = "block"


@dataclass(frozen=True)
class RuntimeArtifactClass:
    class_id: str
    paths: tuple[str, ...]
    source_of_truth: bool
    versionable: bool
    sensitive: bool
    retention_days: int
    cleanup_allowed: bool
    export_allowed: bool
    redaction_required: bool
    never_delete: bool
    classification: str
    description: str = ""
    notes: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RuntimeArtifactClass":
        return cls(
            class_id=str(payload["class_id"]),
            paths=tuple(str(item) for item in payload.get("paths", [])),
            source_of_truth=bool(payload.get("source_of_truth", False)),
            versionable=bool(payload.get("versionable", False)),
            sensitive=bool(payload.get("sensitive", False)),
            retention_days=int(payload.get("retention_days", 0)),
            cleanup_allowed=bool(payload.get("cleanup_allowed", False)),
            export_allowed=bool(payload.get("export_allowed", False)),
            redaction_required=bool(payload.get("redaction_required", False)),
            never_delete=bool(payload.get("never_delete", False)),
            classification=str(payload.get("classification", "runtime-generated")),
            description=str(payload.get("description", "")),
            notes=tuple(str(item) for item in payload.get("notes", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "class_id": self.class_id,
            "description": self.description,
            "paths": list(self.paths),
            "source_of_truth": self.source_of_truth,
            "versionable": self.versionable,
            "sensitive": self.sensitive,
            "retention_days": self.retention_days,
            "cleanup_allowed": self.cleanup_allowed,
            "export_allowed": self.export_allowed,
            "redaction_required": self.redaction_required,
            "never_delete": self.never_delete,
            "classification": self.classification,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class RuntimeStatePolicy:
    schema_version: str
    schema_id: str
    policy_id: str
    created_by: str
    status: str
    default_mode: str
    artifact_classes: tuple[RuntimeArtifactClass, ...]
    zip_hygiene: dict[str, Any]
    safety: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RuntimeStatePolicy":
        return cls(
            schema_version=str(payload["schema_version"]),
            schema_id=str(payload["schema_id"]),
            policy_id=str(payload["policy_id"]),
            created_by=str(payload.get("created_by", "")),
            status=str(payload.get("status", "")),
            default_mode=str(payload.get("default_mode", "dry-run")),
            artifact_classes=tuple(RuntimeArtifactClass.from_dict(item) for item in payload.get("artifact_classes", [])),
            zip_hygiene=dict(payload.get("zip_hygiene", {})),
            safety=dict(payload.get("safety", {})),
            metadata=dict(payload.get("metadata", {})),
        )

    def class_by_id(self) -> dict[str, RuntimeArtifactClass]:
        return {item.class_id: item for item in self.artifact_classes}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "schema_id": self.schema_id,
            "policy_id": self.policy_id,
            "created_by": self.created_by,
            "status": self.status,
            "default_mode": self.default_mode,
            "artifact_classes": [item.to_dict() for item in self.artifact_classes],
            "zip_hygiene": dict(self.zip_hygiene),
            "safety": dict(self.safety),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimeArtifact:
    path: str
    class_id: str
    classification: str
    size_bytes: int
    source_of_truth: bool
    versionable: bool
    sensitive: bool
    cleanup_allowed: bool
    export_allowed: bool
    redaction_required: bool
    never_delete: bool
    git_tracked: bool
    matched_patterns: tuple[str, ...]
    detected_in_source_tree: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "class_id": self.class_id,
            "classification": self.classification,
            "size_bytes": self.size_bytes,
            "source_of_truth": self.source_of_truth,
            "versionable": self.versionable,
            "sensitive": self.sensitive,
            "cleanup_allowed": self.cleanup_allowed,
            "export_allowed": self.export_allowed,
            "redaction_required": self.redaction_required,
            "never_delete": self.never_delete,
            "git_tracked": self.git_tracked,
            "matched_patterns": list(self.matched_patterns),
            "detected_in_source_tree": self.detected_in_source_tree,
        }


@dataclass(frozen=True)
class RuntimeClassSummary:
    class_id: str
    artifacts_total: int
    bytes_total: int
    versionable: bool
    cleanup_allowed: bool
    redaction_required: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "class_id": self.class_id,
            "artifacts_total": self.artifacts_total,
            "bytes_total": self.bytes_total,
            "versionable": self.versionable,
            "cleanup_allowed": self.cleanup_allowed,
            "redaction_required": self.redaction_required,
        }


@dataclass(frozen=True)
class RuntimeViolation:
    violation_id: str
    path: str
    severity: RuntimeViolationSeverity | str
    recommended_action: str
    class_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "violation_id": self.violation_id,
            "path": self.path,
            "severity": self.severity.value if isinstance(self.severity, RuntimeViolationSeverity) else str(self.severity),
            "recommended_action": self.recommended_action,
        }
        if self.class_id is not None:
            payload["class_id"] = self.class_id
        return payload
