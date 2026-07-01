from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.plugins.permission_model import PluginPermissionModel, PluginPermissionModelOptions
from devpilot_core.plugins.registry import PluginRegistry, PluginRegistryOptions
from devpilot_core.policy import PathGuard, PolicyEffect

DEFAULT_PLUGIN_REGISTRY_PATH = ".devpilot/plugins/plugin_registry.json"
DEFAULT_PLUGIN_MANIFEST_SCHEMA_PATH = "docs/schemas/plugin_manifest.schema.json"
DEFAULT_CONNECTOR_REGISTRY_PATH = ".devpilot/connectors/connector_registry.json"
DEFAULT_PLUGIN_PERMISSION_MODEL_PATH = ".devpilot/plugins/plugin_permission_model.json"
DEFAULT_PLUGIN_PERMISSION_MODEL_SCHEMA_PATH = "docs/schemas/plugin_permission_model.schema.json"

_SAFE_LOADING_MODES = {"metadata-only", "dry-run"}
_SAFE_ENTRYPOINT_PREFIXES = ("disabled://", "metadata://")
_SAFE_SIDE_EFFECTS = {"none", "read", "report", "simulation"}
_BLOCKING_SEVERITIES = {Severity.BLOCK, Severity.ERROR, Severity.FAIL}


@dataclass(frozen=True)
class PluginStaticValidatorOptions:
    """Paths used for POST-H-019-C metadata-only plugin static validation."""

    registry_path: str = DEFAULT_PLUGIN_REGISTRY_PATH
    schema_path: str = DEFAULT_PLUGIN_MANIFEST_SCHEMA_PATH
    connector_registry_path: str = DEFAULT_CONNECTOR_REGISTRY_PATH
    permission_model_path: str = DEFAULT_PLUGIN_PERMISSION_MODEL_PATH
    permission_model_schema_path: str = DEFAULT_PLUGIN_PERMISSION_MODEL_SCHEMA_PATH


class PluginStaticValidator:
    """Validate plugin install simulations using manifest metadata only.

    POST-H-019-C treats a plugin install dry-run as a controlled classification
    of registered metadata. It validates registry/permission contracts and then
    builds install simulation records without loading plugin code, starting child
    processes, reading plugin entrypoint files, installing dependencies, writing
    plugin state or opening network connections.
    """

    def __init__(self, root: Path, *, options: PluginStaticValidatorOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or PluginStaticValidatorOptions()
        self.path_guard = PathGuard(self.root)

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        path_findings = self._path_findings()
        if path_findings:
            return _result(False, _exit_code(path_findings), "Plugin static validation blocked by path policy.", _summary_template(blocking_findings_total=len(path_findings)), findings=path_findings)

        registry_result = PluginRegistry(
            self.root,
            options=PluginRegistryOptions(
                registry_path=self.options.registry_path,
                schema_path=self.options.schema_path,
                connector_registry_path=self.options.connector_registry_path,
                permission_model_path=self.options.permission_model_path,
                permission_model_schema_path=self.options.permission_model_schema_path,
            ),
        ).validate()
        permission_result = PluginPermissionModel(
            self.root,
            options=PluginPermissionModelOptions(
                model_path=self.options.permission_model_path,
                schema_path=self.options.permission_model_schema_path,
            ),
        ).validate()
        findings.extend(registry_result.findings if not registry_result.ok else [])
        findings.extend(permission_result.findings if not permission_result.ok else [])
        if not registry_result.ok or not permission_result.ok:
            blocking = _blocking(findings)
            return _result(
                False,
                _exit_code(blocking),
                "Plugin static validation blocked because registry or permission model validation failed.",
                _summary_template(
                    registry_valid=registry_result.ok,
                    permission_model_valid=permission_result.ok,
                    blocking_findings_total=len(blocking),
                ),
                findings=findings,
            )

        registry = self._read_json(self.options.registry_path)
        permission_model = self._read_json(self.options.permission_model_path)
        permission_index = _permission_index(permission_model)
        alias_index = _alias_index(permission_model)
        plugins = [item for item in registry.get("plugins", []) if isinstance(item, dict)]
        plugin_records: list[dict[str, Any]] = []

        for plugin in plugins:
            record, record_findings = self._record_for_plugin(plugin, permission_index, alias_index)
            plugin_records.append(record)
            findings.extend(record_findings)

        blocking = _blocking(findings)
        metadata_only_total = sum(1 for item in plugin_records if item["metadata_only"] is True)
        install_simulated_total = sum(1 for item in plugin_records if item["install_simulated"] is True)
        execution_allowed_total = sum(1 for item in plugin_records if item["execution_allowed"] is True)
        summary = _summary_template(
            registry_valid=True,
            permission_model_valid=True,
            plugins_total=len(plugin_records),
            metadata_only_total=metadata_only_total,
            install_simulated_total=install_simulated_total,
            execution_allowed_total=execution_allowed_total,
            blocking_findings_total=len(blocking),
        )
        return _result(
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else _exit_code(blocking),
            message="Plugin static validation and install dry-run simulation passed." if not blocking else "Plugin static validation found blocking findings.",
            summary=summary,
            findings=findings or [Finding("PLUGIN_STATIC_VALIDATION_PASS", "All registered plugins are metadata-only and install-simulated without execution.", Severity.INFO, metadata=summary)],
            plugins=plugin_records,
        )

    def _path_findings(self) -> list[Finding]:
        findings: list[Finding] = []
        for raw_path, label in (
            (self.options.registry_path, "plugin registry"),
            (self.options.schema_path, "plugin schema"),
            (self.options.connector_registry_path, "connector registry"),
            (self.options.permission_model_path, "permission model"),
            (self.options.permission_model_schema_path, "permission model schema"),
        ):
            path = self._resolve(raw_path)
            decision = self.path_guard.evaluate(path, action="read")
            if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
                findings.append(Finding("PLUGIN_STATIC_PATH_BLOCKED", f"{label} path was blocked by PathGuard.", Severity.BLOCK, path=decision.subject, metadata=decision.metadata))
            elif not path.exists():
                findings.append(Finding("PLUGIN_STATIC_FILE_MISSING", f"Required {label} file is missing.", Severity.BLOCK, path=_rel(self.root, path)))
        return findings

    def _record_for_plugin(self, plugin: dict[str, Any], permission_index: dict[str, dict[str, Any]], alias_index: dict[str, str]) -> tuple[dict[str, Any], list[Finding]]:
        findings: list[Finding] = []
        plugin_id = str(plugin.get("plugin_id", "<missing>"))
        entrypoint = str(plugin.get("entrypoint", ""))
        loading_mode = str(plugin.get("loading_mode", ""))
        manifest_path = str(plugin.get("manifest_path", ""))
        metadata_only = plugin.get("execution_enabled") is False and loading_mode in _SAFE_LOADING_MODES and (not entrypoint or entrypoint.startswith(_SAFE_ENTRYPOINT_PREFIXES))
        manifest_reference_safe = manifest_path.startswith(f"{self.options.registry_path}#") or manifest_path.startswith(".devpilot/plugins/plugin_registry.json#")
        execution_allowed = plugin.get("execution_enabled") is True
        network_allowed = plugin.get("network_allowed") is True or plugin.get("external_api_allowed") is True
        filesystem_write_allowed = plugin.get("filesystem_write_allowed") is True
        dynamic_loading_declared = not (not entrypoint or entrypoint.startswith(_SAFE_ENTRYPOINT_PREFIXES))
        permissions: list[dict[str, Any]] = []

        if not metadata_only:
            findings.append(Finding("PLUGIN_STATIC_METADATA_ONLY_BLOCKED", "Plugin install dry-run requires metadata-only loading, disabled entrypoint and execution_enabled=false.", Severity.BLOCK, metadata={"plugin_id": plugin_id, "loading_mode": loading_mode, "entrypoint": entrypoint}))
        if not manifest_reference_safe:
            findings.append(Finding("PLUGIN_STATIC_MANIFEST_REFERENCE_BLOCKED", "Plugin manifest_path must reference plugin_registry.json metadata; install dry-run must not read arbitrary manifest files.", Severity.BLOCK, metadata={"plugin_id": plugin_id, "manifest_path": manifest_path}))
        if execution_allowed:
            findings.append(Finding("PLUGIN_STATIC_EXECUTION_ALLOWED_BLOCKED", "Plugin execution is blocked in POST-H-019-C install dry-run.", Severity.BLOCK, metadata={"plugin_id": plugin_id}))
        if network_allowed:
            findings.append(Finding("PLUGIN_STATIC_NETWORK_ALLOWED_BLOCKED", "Plugin install dry-run cannot allow network or external APIs.", Severity.BLOCK, metadata={"plugin_id": plugin_id}))
        if filesystem_write_allowed:
            findings.append(Finding("PLUGIN_STATIC_FILESYSTEM_WRITE_BLOCKED", "Plugin install dry-run cannot allow filesystem writes by plugins.", Severity.BLOCK, metadata={"plugin_id": plugin_id}))

        for permission in plugin.get("permissions", []) or []:
            if not isinstance(permission, dict):
                findings.append(Finding("PLUGIN_STATIC_PERMISSION_INVALID", "Plugin permission entries must be objects.", Severity.BLOCK, metadata={"plugin_id": plugin_id}))
                continue
            raw_permission_id = str(permission.get("permission_id", "<missing>"))
            canonical_permission_id = alias_index.get(raw_permission_id, raw_permission_id)
            model_permission = permission_index.get(canonical_permission_id, {})
            allowed_by_model = model_permission.get("effect") == "allow"
            safe_side_effect = permission.get("side_effect") in _SAFE_SIDE_EFFECTS
            if not allowed_by_model or permission.get("allowed") is not True:
                findings.append(Finding("PLUGIN_STATIC_PERMISSION_NOT_ALLOWED", "Install dry-run accepts only allow-listed metadata permissions.", Severity.BLOCK, metadata={"plugin_id": plugin_id, "permission_id": raw_permission_id, "canonical_permission_id": canonical_permission_id}))
            if not safe_side_effect:
                findings.append(Finding("PLUGIN_STATIC_PERMISSION_SIDE_EFFECT_BLOCKED", "Install dry-run accepts only none/read/report/simulation permission side effects.", Severity.BLOCK, metadata={"plugin_id": plugin_id, "permission_id": raw_permission_id, "side_effect": permission.get("side_effect")}))
            permissions.append(
                {
                    "permission_id": raw_permission_id,
                    "canonical_permission_id": canonical_permission_id,
                    "allowed_by_model": allowed_by_model,
                    "manifest_allowed": permission.get("allowed") is True,
                    "side_effect": permission.get("side_effect"),
                    "safe_side_effect": safe_side_effect,
                    "risk_level": model_permission.get("risk_level"),
                    "effect": model_permission.get("effect"),
                }
            )

        record = {
            "plugin_id": plugin_id,
            "name": plugin.get("name"),
            "version": plugin.get("version"),
            "status": plugin.get("status"),
            "risk_level": plugin.get("risk_level"),
            "metadata_only": metadata_only,
            "install_simulated": True,
            "install_state": "metadata-only-simulated" if metadata_only else "blocked",
            "executable_state": "blocked",
            "execution_allowed": execution_allowed,
            "dynamic_loading_declared": dynamic_loading_declared,
            "network_allowed": network_allowed,
            "external_api_allowed": plugin.get("external_api_allowed") is True,
            "filesystem_write_allowed": filesystem_write_allowed,
            "shell_allowed": plugin.get("shell_allowed") is True,
            "remote_execution_allowed": plugin.get("remote_execution_allowed") is True,
            "entrypoint_safe": not dynamic_loading_declared,
            "manifest_reference_safe": manifest_reference_safe,
            "plugin_code_loaded": False,
            "arbitrary_code_execution_performed": False,
            "dependencies_installed": False,
            "marketplace_used": False,
            "files_read": [self.options.registry_path, self.options.permission_model_path, self.options.connector_registry_path],
            "arbitrary_files_read": False,
            "permissions": permissions,
        }
        return record, findings

    def _read_json(self, path: str) -> dict[str, Any]:
        payload = json.loads(self._resolve(path).read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}

    def _resolve(self, value: str | Path) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()


def _permission_index(model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("permission_id")): item for item in model.get("permissions", []) if isinstance(item, dict) and item.get("permission_id")}


def _alias_index(model: dict[str, Any]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for item in model.get("permissions", []) if isinstance(model.get("permissions"), list) else []:
        if not isinstance(item, dict):
            continue
        permission_id = str(item.get("permission_id", ""))
        for alias in item.get("aliases", []) or []:
            aliases[str(alias)] = permission_id
    return aliases


def _summary_template(**overrides: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "created_by": "POST-H-019-C",
        "status": "implemented-initial",
        "preliminary": True,
        "registry_valid": False,
        "permission_model_valid": False,
        "plugins_total": 0,
        "metadata_only_total": 0,
        "install_simulated_total": 0,
        "execution_allowed_total": 0,
        "blocking_findings_total": 0,
        "plugin_code_loaded": False,
        "arbitrary_code_execution_performed": False,
        "network_used": False,
        "external_api_used": False,
        "mutations_performed": False,
        "shell_used": False,
        "remote_execution_used": False,
        "dependencies_installed": False,
        "marketplace_used": False,
        "arbitrary_files_read": False,
    }
    summary.update(overrides)
    return summary


def _result(ok: bool, exit_code: ExitCode, message: str, summary: dict[str, Any], *, findings: list[Finding], plugins: list[dict[str, Any]] | None = None) -> CommandResult:
    return CommandResult(
        command="plugin static-validate",
        ok=ok,
        exit_code=exit_code,
        message=message,
        data={"summary": summary, "plugins": plugins or []},
        findings=findings,
    )


def _blocking(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity in _BLOCKING_SEVERITIES]


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
