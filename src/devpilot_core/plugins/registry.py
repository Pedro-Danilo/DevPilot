from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.connectors.registry import ConnectorRegistry
from devpilot_core.observability import EventLogger
from devpilot_core.policy import PathGuard, PolicyEffect, PolicyEngine, PolicyRequest, SecretGuard
from devpilot_core.schemas import SchemaValidator
from devpilot_core.plugins.permission_model import PluginPermissionModel, PluginPermissionModelOptions

_DEFAULT_REGISTRY_PATH = ".devpilot/plugins/plugin_registry.json"
_DEFAULT_SCHEMA_PATH = "docs/schemas/plugin_manifest.schema.json"
_DEFAULT_CONNECTOR_REGISTRY_PATH = ".devpilot/connectors/connector_registry.json"
_DEFAULT_PERMISSION_MODEL_PATH = ".devpilot/plugins/plugin_permission_model.json"
_DEFAULT_PERMISSION_MODEL_SCHEMA = "docs/schemas/plugin_permission_model.schema.json"
_VALID_PLUGIN_STATUSES = {"disabled", "planned", "implemented-initial", "implemented", "experimental"}
_VALID_RISK_LEVELS = {"low", "medium", "medium_high", "high", "critical"}
_SAFE_SIDE_EFFECTS = {"none", "read", "report", "simulation"}
_SAFE_LOADING_MODES = {"metadata-only", "dry-run"}
_DISABLED_ENTRYPOINT_PREFIXES = ("disabled://", "metadata://")


@dataclass(frozen=True)
class PluginRegistryOptions:
    """Options for validating the local Plugin Registry."""

    registry_path: str = _DEFAULT_REGISTRY_PATH
    schema_path: str = _DEFAULT_SCHEMA_PATH
    connector_registry_path: str = _DEFAULT_CONNECTOR_REGISTRY_PATH
    permission_model_path: str = _DEFAULT_PERMISSION_MODEL_PATH
    permission_model_schema_path: str = _DEFAULT_PERMISSION_MODEL_SCHEMA


@dataclass(frozen=True)
class PluginDryRunOptions:
    """Options for a governed plugin loader dry-run."""

    plugin: str
    operation: str = "metadata"
    dry_run: bool = True
    registry_path: str = _DEFAULT_REGISTRY_PATH
    connector_registry_path: str = _DEFAULT_CONNECTOR_REGISTRY_PATH
    permission_model_path: str = _DEFAULT_PERMISSION_MODEL_PATH
    permission_model_schema_path: str = _DEFAULT_PERMISSION_MODEL_SCHEMA


class PluginRegistry:
    """Validate and inspect FUNC-SPRINT-93 local plugin registry contracts.

    Sprint 93 deliberately implements metadata validation and a loader dry-run,
    not arbitrary plugin import/execution. Plugins remain local, deny-by-default,
    policy-bound and observable. A plugin dry-run emits trace evidence but never
    imports Python modules, starts processes, opens network connections or mutates
    the repository.
    """

    def __init__(self, root: Path, *, options: PluginRegistryOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or PluginRegistryOptions()
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()
        self.policy = PolicyEngine(self.root)

    @property
    def registry_path(self) -> Path:
        return self._resolve(self.options.registry_path)

    @property
    def schema_path(self) -> Path:
        return self._resolve(self.options.schema_path)

    @property
    def connector_registry_path(self) -> Path:
        return self._resolve(self.options.connector_registry_path)

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        registry_display = _rel(self.root, self.registry_path)
        schema_display = _rel(self.root, self.schema_path)
        connector_registry_display = _rel(self.root, self.connector_registry_path)
        permission_model_display = self.options.permission_model_path

        for path, label in [(self.registry_path, "registry"), (self.schema_path, "schema")]:
            decision = self.path_guard.evaluate(path, action="read")
            if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
                return CommandResult(
                    command="plugin validate",
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message=f"Plugin {label} path was blocked by PathGuard.",
                    data={"summary": _summary_template(registry_display, schema_display, connector_registry_display, path_allowed=False)},
                    findings=[Finding("PLUGIN_REGISTRY_PATH_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata)],
                )
            if not path.exists():
                return CommandResult(
                    command="plugin validate",
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message=f"Plugin {label} file is missing.",
                    data={"summary": _summary_template(registry_display, schema_display, connector_registry_display, path_allowed=True)},
                    findings=[Finding("PLUGIN_REGISTRY_FILE_MISSING", f"Missing plugin {label}: {_rel(self.root, path)}", Severity.BLOCK, path=_rel(self.root, path))],
                )

        try:
            registry_text = self.registry_path.read_text(encoding="utf-8")
            registry = json.loads(registry_text)
        except json.JSONDecodeError as exc:
            return CommandResult(
                command="plugin validate",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Plugin registry is not valid JSON.",
                data={"summary": _summary_template(registry_display, schema_display, connector_registry_display, path_allowed=True)},
                findings=[Finding("PLUGIN_REGISTRY_INVALID_JSON", str(exc), Severity.ERROR, path=registry_display)],
            )

        redaction = self.secret_guard.redact(registry_text)
        if redaction.redactions:
            findings.append(Finding("PLUGIN_REGISTRY_SECRET_RISK_BLOCKED", "SecretGuard detected secret-like material in Plugin Registry; manifests must store references only.", Severity.BLOCK, path=registry_display, metadata={"redactions_total": redaction.redactions}))

        schema_result = SchemaValidator(self.root).validate(schema=self.options.schema_path, instance=self.options.registry_path)
        if not schema_result.ok:
            findings.extend(schema_result.findings)

        permission_model = PluginPermissionModel(
            self.root,
            options=PluginPermissionModelOptions(
                model_path=self.options.permission_model_path,
                schema_path=self.options.permission_model_schema_path,
            ),
        )
        permission_model_result = permission_model.validate()
        if not permission_model_result.ok:
            findings.extend(permission_model_result.findings)
        findings.extend(permission_model.validate_registry_permissions(registry, registry_path=registry_display))

        connector_result = ConnectorRegistry(self.root).validate()
        connector_registry_valid = connector_result.ok
        if not connector_result.ok:
            findings.append(Finding("PLUGIN_CONNECTOR_REGISTRY_INVALID", "Plugin registry validation requires the Connector Registry to pass first.", Severity.BLOCK, path=connector_registry_display))

        connector_ids = self._connector_ids() if connector_registry_valid else set()
        policy_rule_ids = self._policy_rule_ids()
        plugins = registry.get("plugins") if isinstance(registry, dict) else []
        plugins = plugins if isinstance(plugins, list) else []
        defaults = registry.get("defaults", {}) if isinstance(registry, dict) else {}
        security = registry.get("security", {}) if isinstance(registry, dict) else {}
        status_counts: Counter[str] = Counter()
        risk_counts: Counter[str] = Counter()
        policy_missing: list[str] = []
        unknown_policy_rules: list[str] = []
        permission_policy_missing: list[str] = []
        unsafe_permissions: list[str] = []
        executable_plugins: list[str] = []
        unsafe_entrypoints: list[str] = []
        network_enabled: list[str] = []
        external_enabled: list[str] = []
        shell_enabled: list[str] = []
        remote_enabled: list[str] = []
        observability_missing: list[str] = []
        eval_missing: list[str] = []
        unknown_connectors: list[str] = []
        duplicate_plugin_ids: list[str] = []
        seen_plugin_ids: set[str] = set()

        if defaults.get("plugin_default_effect") != "deny":
            findings.append(Finding("PLUGIN_DEFAULT_EFFECT_BLOCKED", "Plugin default effect must be deny.", Severity.BLOCK, path=registry_display))
        if defaults.get("deny_unregistered_plugins") is not True:
            findings.append(Finding("UNREGISTERED_PLUGINS_NOT_DENIED", "Unregistered plugins must be denied.", Severity.BLOCK, path=registry_display))
        if defaults.get("executable_loading_default") is not False:
            findings.append(Finding("PLUGIN_EXECUTABLE_LOADING_DEFAULT_BLOCKED", "Executable plugin loading must be disabled by default.", Severity.BLOCK, path=registry_display))
        if defaults.get("permission_model_required") is not True:
            findings.append(Finding("PLUGIN_PERMISSION_MODEL_REQUIRED", "Plugin Registry must require the POST-H-019-B permission model.", Severity.BLOCK, path=registry_display))
        if defaults.get("unknown_permissions_effect") != "deny":
            findings.append(Finding("PLUGIN_UNKNOWN_PERMISSIONS_DENY_REQUIRED", "Unknown plugin permissions must be denied by default.", Severity.BLOCK, path=registry_display))
        if defaults.get("critical_permissions_require_future_adr") is not True:
            findings.append(Finding("PLUGIN_CRITICAL_PERMISSIONS_ADR_REQUIRED", "Critical plugin permissions must require a future ADR.", Severity.BLOCK, path=registry_display))
        if registry.get("permission_model_path") != self.options.permission_model_path:
            findings.append(Finding("PLUGIN_PERMISSION_MODEL_PATH_MISMATCH", "Plugin Registry must reference the canonical POST-H-019-B permission model path.", Severity.BLOCK, path=registry_display, metadata={"expected": self.options.permission_model_path, "actual": registry.get("permission_model_path")}))
        if security.get("plugin_code_loaded") is not False or security.get("arbitrary_code_execution_performed") is not False:
            findings.append(Finding("PLUGIN_CODE_LOADING_PERFORMED_BLOCKED", "Sprint 93 must not load or execute arbitrary plugin code.", Severity.BLOCK, path=registry_display))
        for flag in ["network_used", "external_api_used", "shell_used", "remote_execution_used", "secrets_allowed", "dynamic_import_allowed", "subprocess_allowed", "filesystem_write_allowed", "pip_install_allowed", "marketplace_enabled"]:
            if security.get(flag) is not False:
                findings.append(Finding("PLUGIN_SECURITY_FLAG_BLOCKED", f"Plugin registry security flag {flag} must remain false.", Severity.BLOCK, path=registry_display, metadata={"flag": flag}))

        for plugin in plugins:
            if not isinstance(plugin, dict):
                findings.append(Finding("PLUGIN_ENTRY_INVALID", "Each plugin entry must be an object.", Severity.BLOCK, path=registry_display))
                continue
            plugin_id = str(plugin.get("plugin_id", "<missing>"))
            if plugin_id in seen_plugin_ids:
                duplicate_plugin_ids.append(plugin_id)
            seen_plugin_ids.add(plugin_id)
            status = str(plugin.get("status", ""))
            risk = str(plugin.get("risk_level", ""))
            if status in _VALID_PLUGIN_STATUSES:
                status_counts[status] += 1
            if risk in _VALID_RISK_LEVELS:
                risk_counts[risk] += 1
            if plugin.get("default_effect") != "deny":
                findings.append(Finding("PLUGIN_ALLOW_BY_DEFAULT_BLOCKED", "Every plugin must be deny-by-default.", Severity.BLOCK, path=registry_display, metadata={"plugin_id": plugin_id}))
            plugin_policy_rules = plugin.get("policy_rule_ids") or []
            if not plugin_policy_rules:
                policy_missing.append(plugin_id)
            unknown_policy_rules.extend([f"{plugin_id}:{rule}" for rule in plugin_policy_rules if rule not in policy_rule_ids])
            if plugin.get("execution_enabled") is not False:
                executable_plugins.append(plugin_id)
            loading_mode = str(plugin.get("loading_mode", ""))
            entrypoint = str(plugin.get("entrypoint", ""))
            if loading_mode not in _SAFE_LOADING_MODES or (entrypoint and not entrypoint.startswith(_DISABLED_ENTRYPOINT_PREFIXES)):
                unsafe_entrypoints.append(plugin_id)
            if plugin.get("network_allowed") is not False:
                network_enabled.append(plugin_id)
            if plugin.get("external_api_allowed") is not False:
                external_enabled.append(plugin_id)
            if plugin.get("shell_allowed") is not False:
                shell_enabled.append(plugin_id)
            if plugin.get("remote_execution_allowed") is not False:
                remote_enabled.append(plugin_id)
            if plugin.get("observability_required") is not True:
                observability_missing.append(plugin_id)
            if plugin.get("eval_required") is not True:
                eval_missing.append(plugin_id)
            for permission in plugin.get("permissions", []) or []:
                permission_id = str(permission.get("permission_id", "<missing>")) if isinstance(permission, dict) else "<invalid>"
                permission_rules = permission.get("policy_rule_ids", []) if isinstance(permission, dict) else []
                side_effect = permission.get("side_effect") if isinstance(permission, dict) else None
                if not permission_rules:
                    permission_policy_missing.append(f"{plugin_id}:{permission_id}")
                unknown_policy_rules.extend([f"{plugin_id}:{permission_id}:{rule}" for rule in permission_rules if rule not in policy_rule_ids])
                if permission.get("allowed") is not True or side_effect not in _SAFE_SIDE_EFFECTS:
                    unsafe_permissions.append(f"{plugin_id}:{permission_id}")
            for connector_id in plugin.get("connectors", []) or []:
                if str(connector_id) not in connector_ids:
                    unknown_connectors.append(f"{plugin_id}:{connector_id}")

        for finding_id, items, message in [
            ("PLUGIN_ID_DUPLICATE", duplicate_plugin_ids, "Plugin identifiers must be unique."),
            ("PLUGIN_POLICY_MISSING", policy_missing, "Every plugin must declare policy_rule_ids."),
            ("PLUGIN_POLICY_UNKNOWN", unknown_policy_rules, "Plugin policy rules must exist in MIASI Policy Matrix."),
            ("PLUGIN_PERMISSION_POLICY_MISSING", permission_policy_missing, "Every plugin permission must declare policy_rule_ids."),
            ("PLUGIN_PERMISSION_UNSAFE_BLOCKED", unsafe_permissions, "Sprint 93 permissions must remain safe read/report/simulation operations."),
            ("PLUGIN_EXECUTION_ENABLED_BLOCKED", executable_plugins, "Plugin executable loading must remain disabled in Sprint 93."),
            ("PLUGIN_ENTRYPOINT_UNSAFE_BLOCKED", unsafe_entrypoints, "Plugin entrypoints must be metadata-only/disabled and must not be importable code targets."),
            ("PLUGIN_NETWORK_ENABLED_BLOCKED", network_enabled, "Plugins must not enable network by default."),
            ("PLUGIN_EXTERNAL_API_ENABLED_BLOCKED", external_enabled, "Plugins must not enable external APIs."),
            ("PLUGIN_SHELL_ENABLED_BLOCKED", shell_enabled, "Plugins must not enable shell execution."),
            ("PLUGIN_REMOTE_EXECUTION_BLOCKED", remote_enabled, "Plugins must not enable remote execution."),
            ("PLUGIN_OBSERVABILITY_MISSING", observability_missing, "Every plugin must require observability."),
            ("PLUGIN_EVAL_MISSING", eval_missing, "Every plugin must require evaluation."),
            ("PLUGIN_CONNECTOR_UNKNOWN", unknown_connectors, "Plugin connector references must exist in Connector Registry."),
        ]:
            if items:
                findings.append(Finding(finding_id, message, Severity.BLOCK, path=registry_display, metadata={"items": items[:50], "total": len(items)}))

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.FAIL, Severity.ERROR}]
        summary = {
            **_summary_template(registry_display, schema_display, connector_registry_display, path_allowed=True),
            "schema_valid": schema_result.ok,
            "connector_registry_valid": connector_registry_valid,
            "plugins_total": len(plugins),
            "status_counts": dict(sorted(status_counts.items())),
            "risk_counts": dict(sorted(risk_counts.items())),
            "policy_bindings_total": sum(len(plugin.get("policy_rule_ids", []) or []) for plugin in plugins if isinstance(plugin, dict)),
            "permission_bindings_total": sum(len(permission.get("policy_rule_ids", []) or []) for plugin in plugins if isinstance(plugin, dict) for permission in (plugin.get("permissions", []) or []) if isinstance(permission, dict)),
            "permission_model_valid": permission_model_result.ok,
            "permission_model_path": permission_model_display,
            "permission_model_permissions_total": permission_model_result.data.get("summary", {}).get("permissions_total", 0),
            "unknown_permissions_effect": permission_model_result.data.get("summary", {}).get("unknown_permissions_effect"),
            "blocked_findings_total": len(blocking),
            "plugin_code_loaded": False,
            "arbitrary_code_execution_performed": False,
            "network_used": False,
            "external_api_used": False,
            "shell_used": False,
            "remote_execution_used": False,
            "preliminary": True,
        }
        ok = not blocking
        return CommandResult(
            command="plugin validate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Plugin Registry validation passed." if ok else "Plugin Registry validation failed or blocked.",
            data={"summary": summary, "plugins": [_public_plugin(plugin) for plugin in plugins if isinstance(plugin, dict)]},
            findings=findings or [Finding("PLUGIN_REGISTRY_VALIDATED", "Plugin Registry is valid, policy-bound and non-executable by default.", Severity.INFO, metadata=summary)],
        )

    def list(self) -> CommandResult:
        validation = self.validate()
        if not validation.ok:
            return CommandResult(
                command="plugin list",
                ok=False,
                exit_code=validation.exit_code,
                message="Plugin list blocked because Plugin Registry validation failed.",
                data={"summary": validation.data.get("summary", {})},
                findings=validation.findings,
            )
        return CommandResult(
            command="plugin list",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Plugin Registry listed successfully.",
            data=validation.data,
            findings=[Finding("PLUGIN_LIST_PASS", "Plugin Registry listed public metadata only.", Severity.INFO, metadata=validation.data.get("summary", {}))],
        )

    def dry_run(self, options: PluginDryRunOptions) -> CommandResult:
        plugin_id = _canonical_id(options.plugin)
        operation_id = _canonical_id(options.operation)
        validation = PluginRegistry(
            self.root,
            options=PluginRegistryOptions(
                registry_path=options.registry_path,
                connector_registry_path=options.connector_registry_path,
                permission_model_path=self.options.permission_model_path,
                permission_model_schema_path=self.options.permission_model_schema_path,
            ),
        ).validate()
        if not validation.ok:
            result = CommandResult(
                command="plugin dry-run",
                ok=False,
                exit_code=validation.exit_code,
                message="Plugin dry-run blocked because Plugin Registry validation failed.",
                data={"summary": {"plugin_id": plugin_id, "operation_id": operation_id, "registry_valid": False, "dry_run": options.dry_run}},
                findings=validation.findings,
            )
            return self._emit_plugin_event(result, plugin_id=plugin_id, operation_id=operation_id)

        registry = self._load_registry(options.registry_path)
        plugin = self._find_plugin(registry, plugin_id)
        if plugin is None:
            result = CommandResult(
                command="plugin dry-run",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Plugin dry-run blocked: plugin is not registered.",
                data={"summary": _dry_run_summary(plugin_id, operation_id, options.dry_run, registry_valid=True)},
                findings=[Finding("PLUGIN_NOT_REGISTERED", "Only registered plugins can be dry-run loaded.", Severity.BLOCK, metadata={"plugin_id": plugin_id})],
            )
            return self._emit_plugin_event(result, plugin_id=plugin_id, operation_id=operation_id)

        permissions = [item for item in plugin.get("permissions", []) or [] if isinstance(item, dict)]
        permission_model = PluginPermissionModel(
            self.root,
            options=PluginPermissionModelOptions(
                model_path=self.options.permission_model_path,
                schema_path=self.options.permission_model_schema_path,
            ),
        )
        canonical_operation_id = permission_model.resolve_permission_id(operation_id)
        permission = next((item for item in permissions if item.get("permission_id") in {operation_id, canonical_operation_id}), None)
        if permission is None:
            result = CommandResult(
                command="plugin dry-run",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Plugin dry-run blocked: operation is not declared as a permission.",
                data={"summary": _dry_run_summary(plugin_id, operation_id, options.dry_run, registry_valid=True)},
                findings=[Finding("PLUGIN_OPERATION_NOT_REGISTERED", "Plugin operation must be declared in the plugin permissions list or as a POST-H-019-B permission alias.", Severity.BLOCK, metadata={"plugin_id": plugin_id, "operation_id": operation_id, "canonical_operation_id": canonical_operation_id})],
            )
            return self._emit_plugin_event(result, plugin_id=plugin_id, operation_id=operation_id)

        findings = self._dry_run_governance_findings(plugin, permission, dry_run=options.dry_run)
        policy_result = self.policy.evaluate(
            PolicyRequest(
                action="read",
                path=".devpilot/plugins/plugin_registry.json",
                text=None,
                dry_run=True,
                tool_id="plugin.loader.dry_run",
                subject=f"{plugin_id}:{operation_id}",
                metadata={
                    "component": "PluginRegistry",
                    "sprint": "FUNC-SPRINT-93",
                    "plugin_id": plugin_id,
                    "operation_id": operation_id,
                    "canonical_operation_id": canonical_operation_id,
                    "plugin_code_loaded": False,
                    "arbitrary_code_execution_performed": False,
                    "network_used": False,
                    "external_api_used": False,
                },
            )
        )
        if not policy_result.ok:
            findings.extend(policy_result.findings)

        blocked = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        if blocked:
            result = CommandResult(
                command="plugin dry-run",
                ok=False,
                exit_code=_exit_code(blocked),
                message="Plugin dry-run blocked by registry or policy.",
                data={"summary": {**_dry_run_summary(plugin_id, operation_id, options.dry_run, registry_valid=True), "policy_checked": True, "policy_allowed": policy_result.ok}},
                findings=findings,
            )
            return self._emit_plugin_event(result, plugin_id=plugin_id, operation_id=operation_id)

        result = CommandResult(
            command="plugin dry-run",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Plugin loader dry-run completed without loading arbitrary code.",
            data={
                "summary": {
                    **_dry_run_summary(plugin_id, operation_id, options.dry_run, registry_valid=True),
                    "policy_checked": True,
                    "policy_allowed": True,
                    "trace_event_emitted": False,
                    "plugin_status": plugin.get("status"),
                    "loading_mode": plugin.get("loading_mode"),
                    "permission_side_effect": permission.get("side_effect"),
                    "canonical_permission_id": permission.get("permission_id"),
                    "permission_model_valid": True,
                },
                "plugin": _public_plugin(plugin),
                "permission": _public_permission(permission),
                "loader": {
                    "mode": "dry-run-metadata-only",
                    "simulated": True,
                    "plugin_code_loaded": False,
                    "arbitrary_code_execution_performed": False,
                    "network_used": False,
                    "external_api_used": False,
                    "shell_used": False,
                    "remote_execution_used": False,
                    "mutations_performed": False,
                    "loaded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                },
                "policy": policy_result.data.get("summary", {}),
            },
            findings=[Finding("PLUGIN_LOADER_DRY_RUN_COMPLETED", "Plugin loader dry-run emitted governed metadata without importing or executing plugin code.", Severity.INFO, metadata={"plugin_id": plugin_id, "operation_id": operation_id})],
        )
        return self._emit_plugin_event(result, plugin_id=plugin_id, operation_id=operation_id)

    def _dry_run_governance_findings(self, plugin: dict[str, Any], permission: dict[str, Any], *, dry_run: bool) -> list[Finding]:
        plugin_id = str(plugin.get("plugin_id"))
        operation_id = str(permission.get("permission_id"))
        findings: list[Finding] = []
        if not dry_run:
            findings.append(Finding("PLUGIN_DRY_RUN_REQUIRED", "Sprint 93 plugin loader supports only --dry-run metadata validation.", Severity.BLOCK, metadata={"plugin_id": plugin_id, "operation_id": operation_id}))
        if plugin.get("execution_enabled") is not False:
            findings.append(Finding("PLUGIN_EXECUTION_ENABLED_BLOCKED", "Plugin execution remains disabled in Sprint 93.", Severity.BLOCK, metadata={"plugin_id": plugin_id}))
        if plugin.get("loading_mode") not in _SAFE_LOADING_MODES:
            findings.append(Finding("PLUGIN_LOADING_MODE_UNSAFE", "Plugin loading mode must remain metadata-only or dry-run.", Severity.BLOCK, metadata={"plugin_id": plugin_id}))
        entrypoint = str(plugin.get("entrypoint", ""))
        if entrypoint and not entrypoint.startswith(_DISABLED_ENTRYPOINT_PREFIXES):
            findings.append(Finding("PLUGIN_ENTRYPOINT_UNSAFE_BLOCKED", "Plugin entrypoint cannot target importable code in Sprint 93.", Severity.BLOCK, metadata={"plugin_id": plugin_id, "entrypoint": entrypoint}))
        if permission.get("allowed") is not True or permission.get("side_effect") not in _SAFE_SIDE_EFFECTS:
            findings.append(Finding("PLUGIN_PERMISSION_UNSAFE_BLOCKED", "Plugin permission is not safe for metadata-only dry-run loading.", Severity.BLOCK, metadata={"plugin_id": plugin_id, "operation_id": operation_id}))
        return findings

    def _emit_plugin_event(self, result: CommandResult, *, plugin_id: str, operation_id: str) -> CommandResult:
        try:
            event = EventLogger(self.root).emit_result(result, event_type="plugin.dry_run.evaluated", subject=f"{plugin_id}:{operation_id}")
            data = dict(result.data or {})
            summary = dict(data.get("summary") or {})
            summary["trace_event_emitted"] = True
            summary["event_id"] = event.event_id
            summary["event_path"] = event.path
            data["summary"] = summary
            return CommandResult(result.command, result.ok, result.exit_code, result.message, data=data, findings=result.findings)
        except Exception as exc:  # pragma: no cover - best effort observability.
            data = dict(result.data or {})
            summary = dict(data.get("summary") or {})
            summary["trace_event_emitted"] = False
            summary["trace_error"] = type(exc).__name__
            data["summary"] = summary
            return CommandResult(result.command, result.ok, result.exit_code, result.message, data=data, findings=result.findings)

    def _connector_ids(self) -> set[str]:
        try:
            registry = json.loads(self.connector_registry_path.read_text(encoding="utf-8"))
        except Exception:
            return set()
        return {str(item.get("connector_id")) for item in registry.get("connectors", []) if isinstance(item, dict) and item.get("connector_id")}

    def _policy_rule_ids(self) -> set[str]:
        try:
            payload = json.loads((self.root / ".devpilot/miasi/policy_matrix.json").read_text(encoding="utf-8"))
        except Exception:
            return set()
        return {str(item.get("rule_id")) for item in payload.get("rules", []) if isinstance(item, dict) and item.get("rule_id")}

    def _load_registry(self, registry_path: str) -> dict[str, Any]:
        path = self._resolve(registry_path)
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _find_plugin(registry: dict[str, Any], plugin_id: str) -> dict[str, Any] | None:
        for plugin in registry.get("plugins", []):
            if isinstance(plugin, dict) and plugin.get("plugin_id") == plugin_id:
                return plugin
        return None

    def _resolve(self, value: str | Path) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()


def _summary_template(registry_path: str, schema_path: str, connector_registry_path: str, *, path_allowed: bool) -> dict[str, Any]:
    return {
        "registry_path": registry_path,
        "schema_path": schema_path,
        "connector_registry_path": connector_registry_path,
        "path_allowed": path_allowed,
        "plugin_code_loaded": False,
        "arbitrary_code_execution_performed": False,
        "network_used": False,
        "external_api_used": False,
        "preliminary": True,
    }


def _dry_run_summary(plugin_id: str, operation_id: str, dry_run: bool, *, registry_valid: bool) -> dict[str, Any]:
    return {
        "plugin_id": plugin_id,
        "operation_id": operation_id,
        "dry_run": dry_run,
        "registry_valid": registry_valid,
        "plugin_code_loaded": False,
        "arbitrary_code_execution_performed": False,
        "network_used": False,
        "external_api_used": False,
        "shell_used": False,
        "remote_execution_used": False,
        "mutations_performed": False,
        "preliminary": True,
    }


def _public_plugin(plugin: dict[str, Any]) -> dict[str, Any]:
    return {
        "plugin_id": plugin.get("plugin_id"),
        "name": plugin.get("name"),
        "version": plugin.get("version"),
        "owner": plugin.get("owner"),
        "status": plugin.get("status"),
        "risk_level": plugin.get("risk_level"),
        "default_effect": plugin.get("default_effect"),
        "loading_mode": plugin.get("loading_mode"),
        "permissions_total": len(plugin.get("permissions", []) or []),
        "policy_rule_ids": plugin.get("policy_rule_ids", []),
        "connectors": plugin.get("connectors", []),
        "execution_enabled": plugin.get("execution_enabled"),
        "network_allowed": plugin.get("network_allowed"),
        "external_api_allowed": plugin.get("external_api_allowed"),
        "observability_required": plugin.get("observability_required"),
        "eval_required": plugin.get("eval_required"),
    }


def _public_permission(permission: dict[str, Any]) -> dict[str, Any]:
    return {
        "permission_id": permission.get("permission_id"),
        "capability": permission.get("capability"),
        "side_effect": permission.get("side_effect"),
        "allowed": permission.get("allowed"),
        "policy_rule_ids": permission.get("policy_rule_ids", []),
    }


def _canonical_id(value: str) -> str:
    return value.strip().lower().replace("-", "_")


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
