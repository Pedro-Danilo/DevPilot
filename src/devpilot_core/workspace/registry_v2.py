from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect, SecretGuard
from devpilot_core.schemas import SchemaValidator
from devpilot_core.workspace.registry import MultiworkspaceRegistry, WorkspaceRegistryOptions

DEFAULT_WORKSPACE_REGISTRY_V2_SCHEMA = "docs/schemas/multiworkspace_registry_v2.schema.json"
WORKSPACE_REGISTRY_V2_SCHEMA_ID = "SCHEMA-DEVPL-MULTIWORKSPACE-REGISTRY-V2"
POST_H_016_A_CREATED_BY = "POST-H-016-A"


@dataclass(frozen=True)
class WorkspaceRegistryV2Options:
    """Options for validating a migrated Workspace Registry v2 view."""

    registry_path: str = ".devpilot/workspaces/workspace_registry.json"
    schema_path: str = DEFAULT_WORKSPACE_REGISTRY_V2_SCHEMA


class MultiworkspaceRegistryV2:
    """Read-only v1 -> v2 migration and validator for local workspace portfolio metadata."""

    def __init__(self, root: Path, *, options: WorkspaceRegistryV2Options | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or WorkspaceRegistryV2Options()
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()

    def migrate(self) -> CommandResult:
        """Build a deterministic v2 registry payload from the current v1 registry."""

        v1 = MultiworkspaceRegistry(
            self.root,
            options=WorkspaceRegistryOptions(
                registry_path=self.options.registry_path,
                schema_path="docs/schemas/multiworkspace_registry.schema.json",
            ),
        )
        v1_result = v1.validate()
        if not v1_result.ok:
            return CommandResult(
                command="workspace registry migrate v2",
                ok=False,
                exit_code=v1_result.exit_code,
                message="Workspace Registry v2 migration blocked because v1 validation failed.",
                data={"summary": _summary_template(self.options.registry_path, self.options.schema_path, v1_registry_valid=False)},
                findings=v1_result.findings,
            )

        registry_path = self._resolve(self.options.registry_path)
        try:
            source = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return CommandResult(
                command="workspace registry migrate v2",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Workspace Registry v1 JSON could not be loaded for migration.",
                data={"summary": _summary_template(self.options.registry_path, self.options.schema_path, v1_registry_valid=False)},
                findings=[Finding("WORKSPACE_REGISTRY_V2_SOURCE_INVALID_JSON", str(exc), Severity.ERROR, path=_rel(self.root, registry_path))],
            )

        payload = self._migrate_payload(source)
        summary = {
            **_summary_template(self.options.registry_path, self.options.schema_path, v1_registry_valid=True),
            "workspaces_total": len(payload.get("workspaces", [])),
            "active_workspace_id": payload.get("active_workspace_id"),
            "source_schema_version": source.get("schema_version"),
            "target_schema_version": payload.get("schema_version"),
            "migration_mode": "read-only",
            "mutations_performed": False,
        }
        return CommandResult(
            command="workspace registry migrate v2",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Workspace Registry v2 migration completed in memory; no files were written.",
            data={"summary": summary, "registry": payload},
            findings=[
                Finding(
                    "WORKSPACE_REGISTRY_V2_MIGRATION_PASS",
                    "Current v1 registry was interpreted as a v2-compatible in-memory payload.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def validate(self) -> CommandResult:
        """Validate the migrated v2 registry payload and POST-H-016-A no-go flags."""

        migration = self.migrate()
        if not migration.ok:
            return CommandResult(
                command="workspace registry validate v2",
                ok=False,
                exit_code=migration.exit_code,
                message=migration.message,
                data=migration.data,
                findings=migration.findings,
            )
        payload = copy.deepcopy(migration.data["registry"])
        return self.validate_payload(payload)

    def validate_payload(self, payload: dict[str, Any]) -> CommandResult:
        findings: list[Finding] = []
        registry_display = self.options.registry_path
        schema_display = self.options.schema_path

        for path_value, label in [(self.options.registry_path, "registry"), (self.options.schema_path, "schema")]:
            path = self._resolve(path_value)
            decision = self.path_guard.evaluate(path, action="read")
            if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
                return CommandResult(
                    command="workspace registry validate v2",
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message=f"Workspace Registry v2 {label} path was blocked by PathGuard.",
                    data={"summary": _summary_template(registry_display, schema_display, path_allowed=False)},
                    findings=[Finding("WORKSPACE_REGISTRY_V2_PATH_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata)],
                )
            if not path.exists():
                return CommandResult(
                    command="workspace registry validate v2",
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message=f"Workspace Registry v2 {label} file is missing.",
                    data={"summary": _summary_template(registry_display, schema_display, path_allowed=True)},
                    findings=[Finding("WORKSPACE_REGISTRY_V2_FILE_MISSING", f"Missing {label}: {_rel(self.root, path)}", Severity.BLOCK, path=_rel(self.root, path))],
                )

        schema_result = SchemaValidator(self.root).validate_payload(
            schema=self.options.schema_path,
            payload=payload,
            instance_label="workspace_registry_v2:migrated-payload",
        )
        if not schema_result.ok:
            findings.extend(schema_result.findings)

        redaction = self.secret_guard.redact(json.dumps(payload, ensure_ascii=False))
        if redaction.redactions:
            findings.append(
                Finding(
                    "WORKSPACE_REGISTRY_V2_SECRET_RISK_BLOCKED",
                    "SecretGuard detected secret-like material in Workspace Registry v2; store references only.",
                    Severity.BLOCK,
                    path=registry_display,
                    metadata={"redactions_total": redaction.redactions},
                )
            )

        defaults = payload.get("defaults", {}) if isinstance(payload, dict) else {}
        if defaults.get("deny_unregistered_workspaces") is not True:
            findings.append(Finding("WORKSPACE_REGISTRY_V2_UNREGISTERED_NOT_DENIED", "v2 requires deny_unregistered_workspaces=true.", Severity.BLOCK, path=registry_display))
        if defaults.get("cross_workspace_state_reads") is not False:
            findings.append(Finding("WORKSPACE_REGISTRY_V2_CROSS_STATE_READS_ENABLED", "v2 requires cross_workspace_state_reads=false.", Severity.BLOCK, path=registry_display))
        if defaults.get("cross_workspace_writes") is not False:
            findings.append(Finding("WORKSPACE_REGISTRY_V2_CROSS_WORKSPACE_WRITES_ENABLED", "v2 requires cross_workspace_writes=false.", Severity.BLOCK, path=registry_display))
        if defaults.get("secret_sharing_allowed") is not False:
            findings.append(Finding("WORKSPACE_REGISTRY_V2_SECRET_SHARING_ENABLED", "v2 requires secret_sharing_allowed=false.", Severity.BLOCK, path=registry_display))
        if defaults.get("portfolio_status_read_only") is not True:
            findings.append(Finding("WORKSPACE_REGISTRY_V2_PORTFOLIO_NOT_READ_ONLY", "v2 requires portfolio_status_read_only=true.", Severity.BLOCK, path=registry_display))

        security = payload.get("security", {}) if isinstance(payload, dict) else {}
        for flag in (
            "network_used",
            "external_api_used",
            "shell_used",
            "remote_execution_used",
            "connector_write_used",
            "plugin_execution_used",
            "mutations_performed",
            "source_mutations_performed",
            "secrets_read",
        ):
            if security.get(flag) is not False:
                findings.append(Finding("WORKSPACE_REGISTRY_V2_SECURITY_FLAG_BLOCKED", f"v2 security flag {flag} must remain false.", Severity.BLOCK, path=registry_display, metadata={"flag": flag}))

        workspaces = payload.get("workspaces") if isinstance(payload, dict) else []
        workspaces = workspaces if isinstance(workspaces, list) else []
        active_workspace_id = str(payload.get("active_workspace_id") or "")
        active_found = False
        seen: set[str] = set()
        duplicate_ids: list[str] = []
        path_isolation_passed = True

        for entry in workspaces:
            if not isinstance(entry, dict):
                findings.append(Finding("WORKSPACE_REGISTRY_V2_ENTRY_INVALID", "Each v2 workspace entry must be an object.", Severity.BLOCK, path=registry_display))
                continue
            workspace_id = str(entry.get("workspace_id") or "")
            if workspace_id in seen:
                duplicate_ids.append(workspace_id)
            seen.add(workspace_id)
            if workspace_id == active_workspace_id:
                active_found = True
            root_path = str(entry.get("root_path") or "")
            candidate = self._resolve(root_path)
            decision = self.path_guard.evaluate(candidate, action="read")
            if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
                path_isolation_passed = False
                findings.append(Finding("WORKSPACE_REGISTRY_V2_ROOT_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata={"workspace_id": workspace_id, **decision.metadata}))
            if entry.get("default_effect") != "deny":
                findings.append(Finding("WORKSPACE_REGISTRY_V2_ALLOW_BY_DEFAULT_BLOCKED", "v2 workspace entries must stay deny-by-default.", Severity.BLOCK, path=registry_display, metadata={"workspace_id": workspace_id}))
            if entry.get("secret_policy") != "reference-only":
                findings.append(Finding("WORKSPACE_REGISTRY_V2_SECRET_POLICY_REQUIRED", "v2 workspace entries may reference secrets only; secret_policy must be reference-only.", Severity.BLOCK, path=registry_display, metadata={"workspace_id": workspace_id}))

        if duplicate_ids:
            findings.append(Finding("WORKSPACE_REGISTRY_V2_DUPLICATE_WORKSPACE_ID", "Duplicate workspace ids are not allowed in v2.", Severity.BLOCK, path=registry_display, metadata={"workspace_ids": duplicate_ids}))
        if active_workspace_id and not active_found:
            findings.append(Finding("WORKSPACE_REGISTRY_V2_ACTIVE_WORKSPACE_MISSING", "active_workspace_id must reference a registered v2 workspace.", Severity.BLOCK, path=registry_display, metadata={"active_workspace_id": active_workspace_id}))

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.FAIL, Severity.ERROR}]
        summary = {
            **_summary_template(registry_display, schema_display, path_allowed=True, v1_registry_valid=True),
            "v2_schema_valid": schema_result.ok,
            "workspaces_total": len(workspaces),
            "active_workspace_id": active_workspace_id or None,
            "path_isolation_passed": path_isolation_passed,
            "blocked_findings_total": len(blocking),
            "migration_mode": "read-only",
            "mutations_performed": False,
        }
        ok = not blocking
        return CommandResult(
            command="workspace registry validate v2",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Workspace Registry v2 validation passed." if ok else "Workspace Registry v2 validation failed or blocked.",
            data={"summary": summary, "registry": payload},
            findings=findings
            or [
                Finding(
                    "WORKSPACE_REGISTRY_V2_VALIDATED",
                    "Workspace Registry v2 migration payload is valid, local-first, read-only and deny-by-default.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _migrate_payload(self, source: dict[str, Any]) -> dict[str, Any]:
        updated_at = str(source.get("updated_at") or "")
        workspaces: list[dict[str, Any]] = []
        for raw in source.get("workspaces", []):
            if not isinstance(raw, dict):
                continue
            root_path = str(raw.get("path") or ".")
            workspaces.append(
                {
                    "workspace_id": raw.get("workspace_id"),
                    "project_id": raw.get("project_id"),
                    "name": raw.get("name"),
                    "root_path": root_path,
                    "path_mode": raw.get("path_mode", "relative-to-registry-root"),
                    "project_file": ".devpilot/project.yaml",
                    "state_path": raw.get("state_path", ".devpilot/devpilot.db"),
                    "reports_path": raw.get("reports_path", "outputs/reports"),
                    "traces_path": raw.get("traces_path", "outputs/traces"),
                    "secrets_path": raw.get("secrets_path", ".devpilot/providers.yaml"),
                    "status": raw.get("status"),
                    "risk_level": raw.get("risk_level"),
                    "default_effect": raw.get("default_effect", "deny"),
                    "secret_policy": raw.get("secret_policy", "reference-only"),
                    "network_allowed": raw.get("network_allowed", False),
                    "external_api_allowed": raw.get("external_api_allowed", False),
                    "observability_required": raw.get("observability_required", True),
                    "eval_required": raw.get("eval_required", True),
                    "registered_at_utc": raw.get("registered_at"),
                    "last_validated_at_utc": None,
                    "source_registry_version": source.get("schema_version"),
                }
            )

        return {
            "schema_version": "2.0",
            "schema_id": WORKSPACE_REGISTRY_V2_SCHEMA_ID,
            "created_by": POST_H_016_A_CREATED_BY,
            "updated_at": updated_at,
            "active_workspace_id": source.get("active_workspace_id"),
            "defaults": {
                "deny_unregistered_workspaces": True,
                "cross_workspace_state_reads": False,
                "cross_workspace_writes": False,
                "secret_sharing_allowed": False,
                "portfolio_status_read_only": True,
            },
            "security": {
                "network_used": False,
                "external_api_used": False,
                "shell_used": False,
                "remote_execution_used": False,
                "connector_write_used": False,
                "plugin_execution_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "secrets_read": False,
            },
            "migration": {
                "source_registry_path": self.options.registry_path,
                "source_schema_version": source.get("schema_version"),
                "target_schema_version": "2.0",
                "mode": "read-only",
                "source_registry_preserved": True,
                "compatible_with_v1": True,
                "mutations_performed": False,
            },
            "workspaces": workspaces,
        }

    def _resolve(self, path: str | Path) -> Path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else self.root / candidate


def _summary_template(
    registry_path: str,
    schema_path: str,
    *,
    path_allowed: bool = True,
    v1_registry_valid: bool | None = None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "registry_path": registry_path,
        "schema_path": schema_path,
        "path_allowed": path_allowed,
        "read_only": True,
        "dry_run": True,
        "network_used": False,
        "external_api_used": False,
        "shell_used": False,
        "remote_execution_used": False,
        "connector_write_used": False,
        "plugin_execution_used": False,
        "mutations_performed": False,
        "source_mutations_performed": False,
        "secrets_read": False,
        "preliminary": True,
    }
    if v1_registry_valid is not None:
        summary["v1_registry_valid"] = v1_registry_valid
    return summary


def _exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
