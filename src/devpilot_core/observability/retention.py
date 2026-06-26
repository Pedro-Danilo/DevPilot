from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings

DEFAULT_OBSERVABILITY_RETENTION_POLICY = Path(".devpilot/observability/retention_policy.json")
OBSERVABILITY_RETENTION_POLICY_SCHEMA_ID = "SCHEMA-DEVPL-OBSERVABILITY-RETENTION-POLICY-V1"
OBSERVABILITY_RETENTION_POLICY_CONTRACT = "ObservabilityRetentionPolicy"
POST_H_010_A_CREATED_BY = "POST-H-010-A"

CRITICAL_TARGETS = {
    "events-jsonl",
    "trace-files",
    "devpilot-db",
    "agent-sessions",
    "generated-reports",
    "metrics-local-store",
}
CLEAN_ZIP_REQUIRED_PREFIXES = ("outputs/", ".devpilot/devpilot.db", ".devpilot/agent_sessions/")


@dataclass(frozen=True)
class RetentionRotation:
    enabled: bool
    strategy: str
    keep_rotated_files: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RetentionRotation":
        return cls(
            enabled=bool(payload.get("enabled", False)),
            strategy=str(payload.get("strategy", "none")),
            keep_rotated_files=int(payload.get("keep_rotated_files", 0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "strategy": self.strategy,
            "keep_rotated_files": self.keep_rotated_files,
        }


@dataclass(frozen=True)
class ObservabilityRetentionTarget:
    target_id: str
    path: str
    kind: str
    classification: str
    required: bool
    source_of_truth: bool
    versionable: bool
    contains_sensitive_payloads: bool
    redaction_required: bool
    retention_days: int
    max_size_mb: float
    rotation: RetentionRotation
    clean_zip_excluded: bool
    export_allowed: bool
    cleanup_allowed: bool
    raw_payload_storage_allowed: bool
    logical_scope: str | None = None
    notes: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ObservabilityRetentionTarget":
        return cls(
            target_id=str(payload.get("target_id", "")),
            path=str(payload.get("path", "")),
            kind=str(payload.get("kind", "")),
            classification=str(payload.get("classification", "")),
            required=bool(payload.get("required", False)),
            source_of_truth=bool(payload.get("source_of_truth", False)),
            versionable=bool(payload.get("versionable", False)),
            contains_sensitive_payloads=bool(payload.get("contains_sensitive_payloads", False)),
            redaction_required=bool(payload.get("redaction_required", False)),
            retention_days=int(payload.get("retention_days", 0)),
            max_size_mb=float(payload.get("max_size_mb", 0)),
            rotation=RetentionRotation.from_dict(dict(payload.get("rotation", {}))),
            clean_zip_excluded=bool(payload.get("clean_zip_excluded", False)),
            export_allowed=bool(payload.get("export_allowed", False)),
            cleanup_allowed=bool(payload.get("cleanup_allowed", False)),
            raw_payload_storage_allowed=bool(payload.get("raw_payload_storage_allowed", False)),
            logical_scope=str(payload["logical_scope"]) if payload.get("logical_scope") is not None else None,
            notes=tuple(str(item) for item in payload.get("notes", []) if isinstance(item, str)),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "target_id": self.target_id,
            "path": self.path,
            "kind": self.kind,
            "classification": self.classification,
            "required": self.required,
            "source_of_truth": self.source_of_truth,
            "versionable": self.versionable,
            "contains_sensitive_payloads": self.contains_sensitive_payloads,
            "redaction_required": self.redaction_required,
            "retention_days": self.retention_days,
            "max_size_mb": self.max_size_mb,
            "rotation": self.rotation.to_dict(),
            "clean_zip_excluded": self.clean_zip_excluded,
            "export_allowed": self.export_allowed,
            "cleanup_allowed": self.cleanup_allowed,
            "raw_payload_storage_allowed": self.raw_payload_storage_allowed,
            "notes": list(self.notes),
        }
        if self.logical_scope:
            payload["logical_scope"] = self.logical_scope
        return payload


@dataclass(frozen=True)
class ObservabilityRetentionPolicy:
    schema_version: str
    schema_id: str
    policy_id: str
    created_by: str
    status: str
    local_first: bool
    remote_export_enabled: bool
    default_mode: str
    targets: tuple[ObservabilityRetentionTarget, ...]
    safety: dict[str, Any]
    notes: tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ObservabilityRetentionPolicy":
        return cls(
            schema_version=str(payload.get("schema_version", "")),
            schema_id=str(payload.get("schema_id", "")),
            policy_id=str(payload.get("policy_id", "")),
            created_by=str(payload.get("created_by", "")),
            status=str(payload.get("status", "")),
            local_first=bool(payload.get("local_first", False)),
            remote_export_enabled=bool(payload.get("remote_export_enabled", False)),
            default_mode=str(payload.get("default_mode", "")),
            targets=tuple(ObservabilityRetentionTarget.from_dict(item) for item in payload.get("targets", []) if isinstance(item, dict)),
            safety=dict(payload.get("safety", {})),
            notes=tuple(str(item) for item in payload.get("notes", []) if isinstance(item, str)),
        )

    def by_target_id(self) -> dict[str, ObservabilityRetentionTarget]:
        return {target.target_id: target for target in self.targets}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "schema_id": self.schema_id,
            "policy_id": self.policy_id,
            "created_by": self.created_by,
            "status": self.status,
            "local_first": self.local_first,
            "remote_export_enabled": self.remote_export_enabled,
            "default_mode": self.default_mode,
            "targets": [target.to_dict() for target in self.targets],
            "safety": dict(self.safety),
            "notes": list(self.notes),
        }


def load_observability_retention_policy(
    root: Path,
    policy_path: str | Path = DEFAULT_OBSERVABILITY_RETENTION_POLICY,
) -> ObservabilityRetentionPolicy:
    """Load the source-controlled POST-H-010-A retention defaults.

    The loader performs no filesystem inventory and no cleanup. Later
    POST-H-010-B/C/D modules will consume this policy for inventory, dry-run
    cleanup planning and redacted export.
    """

    resolved = Path(root) / policy_path
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Observability retention policy must be a JSON object.")
    return ObservabilityRetentionPolicy.from_dict(payload)


class ObservabilityRetentionPolicyValidator:
    """Validate POST-H-010-A local observability retention defaults.

    This is a semantic validator layered on top of JSON Schema validation. It
    verifies DevPilot-specific no-go gates that are critical for local-first
    operation: no remote export, dry-run defaults, no raw prompts/outputs,
    critical targets present and clean ZIP exclusion for runtime artifacts.
    """

    def __init__(self, root: Path, *, policy_path: str | Path = DEFAULT_OBSERVABILITY_RETENTION_POLICY) -> None:
        self.root = Path(root).resolve()
        self.policy_path = Path(policy_path)

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        try:
            policy = load_observability_retention_policy(self.root, self.policy_path)
        except Exception as exc:
            finding = Finding(
                "OBSERVABILITY_RETENTION_POLICY_LOAD_ERROR",
                f"Observability retention policy could not be loaded: {exc}",
                Severity.ERROR,
                path=str(self.policy_path).replace("\\", "/"),
            )
            return CommandResult(
                "observability retention-policy validate",
                False,
                ExitCode.ERROR,
                "Observability retention policy could not be loaded.",
                data={"summary": self._empty_summary()},
                findings=[finding],
            )

        by_target = policy.by_target_id()
        missing = sorted(CRITICAL_TARGETS - set(by_target))
        if missing:
            findings.append(Finding(
                "OBSERVABILITY_RETENTION_CRITICAL_TARGETS_MISSING",
                "Critical observability retention targets are missing.",
                Severity.BLOCK,
                path=str(self.policy_path).replace("\\", "/"),
                metadata={"missing_targets": missing},
            ))

        if policy.remote_export_enabled:
            findings.append(Finding(
                "OBSERVABILITY_RETENTION_REMOTE_EXPORT_ENABLED",
                "Remote observability export must remain disabled in POST-H-010-A.",
                Severity.BLOCK,
                path=str(self.policy_path).replace("\\", "/"),
            ))
        if policy.default_mode != "dry-run":
            findings.append(Finding(
                "OBSERVABILITY_RETENTION_DEFAULT_MODE_UNSAFE",
                "Observability retention policy must default to dry-run.",
                Severity.BLOCK,
                path=str(self.policy_path).replace("\\", "/"),
                metadata={"default_mode": policy.default_mode},
            ))

        safety = policy.safety
        for key in ["raw_prompts_allowed", "raw_outputs_allowed", "secrets_allowed", "network_allowed", "external_api_allowed", "path_escape_allowed"]:
            if bool(safety.get(key)):
                findings.append(Finding(
                    "OBSERVABILITY_RETENTION_SAFETY_FLAG_UNSAFE",
                    f"Safety flag {key} must be false.",
                    Severity.BLOCK,
                    path=str(self.policy_path).replace("\\", "/"),
                    metadata={"flag": key, "value": safety.get(key)},
                ))
        for key in ["delete_requires_execute", "dry_run_required_by_default"]:
            if safety.get(key) is not True:
                findings.append(Finding(
                    "OBSERVABILITY_RETENTION_SAFETY_FLAG_MISSING",
                    f"Safety flag {key} must be true.",
                    Severity.BLOCK,
                    path=str(self.policy_path).replace("\\", "/"),
                    metadata={"flag": key, "value": safety.get(key)},
                ))

        for target in policy.targets:
            if target.source_of_truth or target.versionable:
                findings.append(Finding(
                    "OBSERVABILITY_RETENTION_RUNTIME_TARGET_VERSIONABLE",
                    "Observability retention targets must not be source-of-truth/versionable source artifacts.",
                    Severity.BLOCK,
                    path=target.path,
                    metadata={"target_id": target.target_id},
                ))
            if target.raw_payload_storage_allowed:
                findings.append(Finding(
                    "OBSERVABILITY_RETENTION_RAW_PAYLOAD_STORAGE_ALLOWED",
                    "Raw payload storage is not allowed for observability retention targets.",
                    Severity.BLOCK,
                    path=target.path,
                    metadata={"target_id": target.target_id},
                ))
            if _requires_clean_zip_exclusion(target.path) and not target.clean_zip_excluded:
                findings.append(Finding(
                    "OBSERVABILITY_RETENTION_CLEAN_ZIP_EXCLUSION_MISSING",
                    "Runtime observability target must be excluded from clean source ZIPs.",
                    Severity.BLOCK,
                    path=target.path,
                    metadata={"target_id": target.target_id},
                ))
            if target.contains_sensitive_payloads and not target.redaction_required:
                findings.append(Finding(
                    "OBSERVABILITY_RETENTION_REDACTION_MISSING",
                    "Sensitive observability target must require redaction.",
                    Severity.BLOCK,
                    path=target.path,
                    metadata={"target_id": target.target_id},
                ))

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        summary = {
            "created_by": POST_H_010_A_CREATED_BY,
            "status": policy.status,
            "policy_path": str(self.policy_path).replace("\\", "/"),
            "schema_id": policy.schema_id,
            "policy_id": policy.policy_id,
            "targets_total": len(policy.targets),
            "critical_targets_total": len(CRITICAL_TARGETS),
            "critical_targets_present_total": len(CRITICAL_TARGETS - set(missing)),
            "runtime_targets_total": len([target for target in policy.targets if not target.versionable and not target.source_of_truth]),
            "clean_zip_excluded_total": len([target for target in policy.targets if target.clean_zip_excluded]),
            "redaction_required_total": len([target for target in policy.targets if target.redaction_required]),
            "remote_export_enabled": policy.remote_export_enabled,
            "default_mode": policy.default_mode,
            "raw_prompts_allowed": bool(safety.get("raw_prompts_allowed")),
            "raw_outputs_allowed": bool(safety.get("raw_outputs_allowed")),
            "secrets_allowed": bool(safety.get("secrets_allowed")),
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "dry_run": True,
            "preliminary": True,
            "blocking_findings_total": len(blocking),
            "findings_total": len(findings),
        }
        return CommandResult(
            "observability retention-policy validate",
            not blocking,
            ExitCode.PASS if not blocking else exit_code_for_findings(blocking),
            "Observability retention policy passed." if not blocking else "Observability retention policy has blocking issues.",
            data={"summary": summary, "policy": policy.to_dict()},
            findings=findings or [Finding("OBSERVABILITY_RETENTION_POLICY_PASS", "Observability retention policy semantic checks passed.", Severity.INFO, metadata=summary)],
        )

    def _empty_summary(self) -> dict[str, Any]:
        return {
            "created_by": POST_H_010_A_CREATED_BY,
            "policy_path": str(self.policy_path).replace("\\", "/"),
            "targets_total": 0,
            "critical_targets_total": len(CRITICAL_TARGETS),
            "critical_targets_present_total": 0,
            "remote_export_enabled": None,
            "default_mode": None,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "dry_run": True,
            "preliminary": True,
            "blocking_findings_total": 1,
            "findings_total": 1,
        }


def _requires_clean_zip_exclusion(path: str) -> bool:
    normalized = path.replace("\\", "/").rstrip("/")
    return normalized.startswith("outputs/") or normalized == ".devpilot/devpilot.db" or normalized.startswith(".devpilot/agent_sessions")
