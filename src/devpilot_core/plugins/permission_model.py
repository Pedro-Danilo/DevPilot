from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect
from devpilot_core.schemas import SchemaValidator

_DEFAULT_PERMISSION_MODEL_PATH = ".devpilot/plugins/plugin_permission_model.json"
_DEFAULT_PERMISSION_MODEL_SCHEMA = "docs/schemas/plugin_permission_model.schema.json"
_DEFAULT_POLICY_MATRIX_PATH = ".devpilot/miasi/policy_matrix.json"

_DENY_CAPABILITY_FLAGS = (
    "plugin_execution_allowed",
    "dynamic_import_allowed",
    "subprocess_allowed",
    "network_allowed",
    "external_api_allowed",
    "filesystem_write_allowed",
    "shell_allowed",
    "remote_execution_allowed",
    "pip_install_allowed",
    "marketplace_enabled",
)
_CRITICAL_RISK_LEVELS = {"high", "critical"}
_ALLOWED_SAFE_SIDE_EFFECTS = {"none", "read", "report", "simulation"}
_REQUIRED_DENIED_PERMISSION_IDS = {
    "plugin.code.execute",
    "plugin.dynamic_import",
    "plugin.subprocess.run",
    "plugin.network.access",
    "plugin.filesystem.write",
    "plugin.dependency.install",
}


@dataclass(frozen=True)
class PluginPermissionModelOptions:
    """Paths used to validate the POST-H-019-B plugin permission model."""

    model_path: str = _DEFAULT_PERMISSION_MODEL_PATH
    schema_path: str = _DEFAULT_PERMISSION_MODEL_SCHEMA
    policy_matrix_path: str = _DEFAULT_POLICY_MATRIX_PATH


class PluginPermissionModel:
    """Validate metadata-only plugin permissions without enabling execution.

    POST-H-019-B introduces a local permission model that separates permission
    declarations from executable authority. This validator is intentionally
    static: it reads JSON metadata, checks allow/deny semantics and returns
    findings. It never imports plugin code, starts subprocesses, performs
    network calls, installs dependencies or writes to plugin locations.
    """

    def __init__(self, root: Path, *, options: PluginPermissionModelOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or PluginPermissionModelOptions()
        self.path_guard = PathGuard(self.root)

    @property
    def model_path(self) -> Path:
        return self._resolve(self.options.model_path)

    @property
    def schema_path(self) -> Path:
        return self._resolve(self.options.schema_path)

    def validate(self) -> CommandResult:
        model_display = _rel(self.root, self.model_path)
        schema_display = _rel(self.root, self.schema_path)
        findings: list[Finding] = []

        for path, label in ((self.model_path, "permission model"), (self.schema_path, "permission model schema")):
            decision = self.path_guard.evaluate(path, action="read")
            if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
                return _result(
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message=f"Plugin {label} path was blocked by PathGuard.",
                    summary=_summary_template(model_display, schema_display, path_allowed=False),
                    findings=[Finding("PLUGIN_PERMISSION_MODEL_PATH_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata)],
                )
            if not path.exists():
                return _result(
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message=f"Plugin {label} file is missing.",
                    summary=_summary_template(model_display, schema_display, path_allowed=True),
                    findings=[Finding("PLUGIN_PERMISSION_MODEL_FILE_MISSING", f"Missing plugin {label}: {_rel(self.root, path)}", Severity.BLOCK, path=_rel(self.root, path))],
                )

        schema_result = SchemaValidator(self.root).validate(schema=self.options.schema_path, instance=self.options.model_path)
        if not schema_result.ok:
            findings.extend(schema_result.findings)

        try:
            model = self.load()
        except json.JSONDecodeError as exc:
            return _result(
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Plugin permission model is not valid JSON.",
                summary=_summary_template(model_display, schema_display, path_allowed=True),
                findings=[Finding("PLUGIN_PERMISSION_MODEL_INVALID_JSON", str(exc), Severity.ERROR, path=model_display)],
            )

        findings.extend(self._semantic_findings(model, path=model_display))
        blocking = _blocking(findings)
        summary = self._summary(model, model_display, schema_display, schema_valid=schema_result.ok, blocking_findings_total=len(blocking))
        return _result(
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else _exit_code(blocking),
            message="Plugin permission model validation passed." if not blocking else "Plugin permission model validation failed or blocked.",
            summary=summary,
            findings=findings or [Finding("PLUGIN_PERMISSION_MODEL_VALIDATED", "Plugin permission model is deny-by-default and non-executable.", Severity.INFO, metadata=summary)],
            model=model,
        )

    def load(self) -> dict[str, Any]:
        payload = json.loads(self.model_path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}

    def validate_registry_permissions(self, registry: dict[str, Any], *, registry_path: str) -> list[Finding]:
        """Validate plugin manifest permissions against the allowlist/denylist.

        A valid manifest may declare only permissions known by the model and only
        permissions whose model effect is `allow`. Denied permissions such as
        `plugin.code.execute` may exist in the model as no-go declarations, but
        a plugin manifest cannot request or enable them.
        """

        try:
            model = self.load()
        except Exception as exc:
            return [Finding("PLUGIN_PERMISSION_MODEL_LOAD_FAILED", f"Cannot load plugin permission model: {exc}", Severity.BLOCK, path=self.options.model_path)]

        permissions = _permission_index(model)
        alias_index = _alias_index(model)
        findings: list[Finding] = []
        unknown: list[str] = []
        denied_requested: list[str] = []
        unsafe_side_effects: list[str] = []
        unsafe_policy_bindings: list[str] = []
        missing_future_adr: list[str] = []
        policy_rule_ids = self._policy_rule_ids()

        for plugin in registry.get("plugins", []) if isinstance(registry.get("plugins"), list) else []:
            if not isinstance(plugin, dict):
                continue
            plugin_id = str(plugin.get("plugin_id", "<missing>"))
            for permission in plugin.get("permissions", []) or []:
                if not isinstance(permission, dict):
                    unknown.append(f"{plugin_id}:<invalid>")
                    continue
                raw_permission_id = str(permission.get("permission_id", "<missing>"))
                canonical_permission_id = self.resolve_permission_id(raw_permission_id)
                model_permission = permissions.get(canonical_permission_id)
                if model_permission is None:
                    unknown.append(f"{plugin_id}:{raw_permission_id}")
                    continue
                if raw_permission_id in alias_index:
                    findings.append(
                        Finding(
                            "PLUGIN_PERMISSION_ALIAS_USED",
                            "Plugin manifest permission uses a legacy alias; canonical plugin.* permission ids are preferred after POST-H-019-B.",
                            Severity.WARNING,
                            path=registry_path,
                            metadata={"plugin_id": plugin_id, "permission_id": raw_permission_id, "canonical_permission_id": canonical_permission_id},
                        )
                    )
                if model_permission.get("effect") != "allow" or permission.get("allowed") is not True:
                    denied_requested.append(f"{plugin_id}:{raw_permission_id}")
                if permission.get("side_effect") not in _ALLOWED_SAFE_SIDE_EFFECTS:
                    unsafe_side_effects.append(f"{plugin_id}:{raw_permission_id}:{permission.get('side_effect')}")
                for rule in permission.get("policy_rule_ids", []) or []:
                    if str(rule) not in policy_rule_ids:
                        unsafe_policy_bindings.append(f"{plugin_id}:{raw_permission_id}:{rule}")
                if model_permission.get("risk_level") in _CRITICAL_RISK_LEVELS and model_permission.get("blocked_until") != "future-adr":
                    missing_future_adr.append(canonical_permission_id)

        for finding_id, items, message in [
            ("PLUGIN_PERMISSION_UNKNOWN_BLOCKED", unknown, "Plugin manifests must not declare permissions outside the POST-H-019-B permission model."),
            ("PLUGIN_PERMISSION_DENIED_REQUESTED_BLOCKED", denied_requested, "Plugin manifests cannot request permissions denied by the permission model."),
            ("PLUGIN_PERMISSION_SIDE_EFFECT_BLOCKED", unsafe_side_effects, "Plugin manifest permissions must remain metadata-only/read/report/simulation."),
            ("PLUGIN_PERMISSION_POLICY_RULE_UNKNOWN", unsafe_policy_bindings, "Plugin permission policy rule ids must exist in the MIASI Policy Matrix."),
            ("PLUGIN_PERMISSION_CRITICAL_ADR_MISSING", missing_future_adr, "Critical plugin permissions must remain blocked until a future ADR."),
        ]:
            if items:
                findings.append(Finding(finding_id, message, Severity.BLOCK, path=registry_path, metadata={"items": sorted(set(items))[:50], "total": len(set(items))}))
        return findings

    def resolve_permission_id(self, permission_id: str) -> str:
        raw = str(permission_id).strip()
        try:
            model = self.load()
        except Exception:
            return raw
        aliases = _alias_index(model)
        return aliases.get(raw, raw)

    def allowed_permission_ids(self) -> set[str]:
        model = self.load()
        return {permission_id for permission_id, permission in _permission_index(model).items() if permission.get("effect") == "allow"}

    def denied_permission_ids(self) -> set[str]:
        model = self.load()
        return {permission_id for permission_id, permission in _permission_index(model).items() if permission.get("effect") == "deny"}

    def _semantic_findings(self, model: dict[str, Any], *, path: str) -> list[Finding]:
        findings: list[Finding] = []
        permissions = _permission_index(model)
        policy_rule_ids = self._policy_rule_ids()

        if model.get("default_effect") != "deny":
            findings.append(Finding("PLUGIN_PERMISSION_DEFAULT_DENY_REQUIRED", "Plugin permission model default_effect must be deny.", Severity.BLOCK, path=path))
        if model.get("unknown_permissions_effect") != "deny":
            findings.append(Finding("PLUGIN_PERMISSION_UNKNOWN_DENY_REQUIRED", "Unknown plugin permissions must be denied.", Severity.BLOCK, path=path))
        if model.get("critical_permissions_require_future_adr") is not True:
            findings.append(Finding("PLUGIN_PERMISSION_CRITICAL_ADR_REQUIRED", "Critical plugin permissions must require a future ADR.", Severity.BLOCK, path=path))
        for flag in _DENY_CAPABILITY_FLAGS:
            if model.get(flag) is not False:
                findings.append(Finding("PLUGIN_PERMISSION_CAPABILITY_FLAG_BLOCKED", f"{flag} must remain false in POST-H-019-B.", Severity.BLOCK, path=path, metadata={"flag": flag}))

        missing_required_denies = sorted(_REQUIRED_DENIED_PERMISSION_IDS - set(permissions))
        if missing_required_denies:
            findings.append(Finding("PLUGIN_PERMISSION_REQUIRED_DENY_MISSING", "The permission model must explicitly deny core execution/network/write permissions.", Severity.BLOCK, path=path, metadata={"items": missing_required_denies}))

        duplicate_aliases: list[str] = []
        seen_aliases: set[str] = set()
        for permission_id, permission in permissions.items():
            effect = permission.get("effect")
            risk_level = permission.get("risk_level")
            aliases = permission.get("aliases", []) or []
            for alias in aliases:
                alias_text = str(alias)
                if alias_text in seen_aliases:
                    duplicate_aliases.append(alias_text)
                seen_aliases.add(alias_text)
            if effect == "allow" and permission_id in _REQUIRED_DENIED_PERMISSION_IDS:
                findings.append(Finding("PLUGIN_PERMISSION_EXECUTION_ALLOW_BLOCKED", "Execution/network/write permission ids must not be allowed.", Severity.BLOCK, path=path, metadata={"permission_id": permission_id}))
            if effect == "allow" and risk_level in _CRITICAL_RISK_LEVELS:
                findings.append(Finding("PLUGIN_PERMISSION_CRITICAL_ALLOW_BLOCKED", "Critical plugin permissions must not be allow-listed in metadata-only mode.", Severity.BLOCK, path=path, metadata={"permission_id": permission_id, "risk_level": risk_level}))
            if effect == "deny" and risk_level in _CRITICAL_RISK_LEVELS:
                if permission.get("requires_approval") is not True or permission.get("blocked_until") != "future-adr":
                    findings.append(Finding("PLUGIN_PERMISSION_CRITICAL_DENY_NOT_GOVERNED", "Denied critical permissions must require approval and be blocked until a future ADR.", Severity.BLOCK, path=path, metadata={"permission_id": permission_id}))
            for rule in permission.get("policy_rule_ids", []) or []:
                if str(rule) not in policy_rule_ids:
                    findings.append(Finding("PLUGIN_PERMISSION_POLICY_RULE_UNKNOWN", "Permission model policy rule id is not in MIASI Policy Matrix.", Severity.BLOCK, path=path, metadata={"permission_id": permission_id, "rule_id": str(rule)}))
        if duplicate_aliases:
            findings.append(Finding("PLUGIN_PERMISSION_ALIAS_DUPLICATE", "Permission model aliases must be unique.", Severity.BLOCK, path=path, metadata={"items": sorted(set(duplicate_aliases))}))
        return findings

    def _summary(self, model: dict[str, Any], model_path: str, schema_path: str, *, schema_valid: bool, blocking_findings_total: int) -> dict[str, Any]:
        permissions = _permission_index(model)
        allowed = [permission for permission in permissions.values() if permission.get("effect") == "allow"]
        denied = [permission for permission in permissions.values() if permission.get("effect") == "deny"]
        critical = [permission for permission in permissions.values() if permission.get("risk_level") in _CRITICAL_RISK_LEVELS]
        return {
            **_summary_template(model_path, schema_path, path_allowed=True),
            "schema_valid": schema_valid,
            "model_id": model.get("model_id"),
            "created_by": model.get("created_by"),
            "status": model.get("status"),
            "default_effect": model.get("default_effect"),
            "unknown_permissions_effect": model.get("unknown_permissions_effect"),
            "permissions_total": len(permissions),
            "allowed_permissions_total": len(allowed),
            "denied_permissions_total": len(denied),
            "critical_permissions_total": len(critical),
            "blocked_permissions_total": len(denied),
            "blocking_findings_total": blocking_findings_total,
            "plugin_execution_allowed": model.get("plugin_execution_allowed"),
            "dynamic_import_allowed": model.get("dynamic_import_allowed"),
            "subprocess_allowed": model.get("subprocess_allowed"),
            "network_allowed": model.get("network_allowed"),
            "external_api_allowed": model.get("external_api_allowed"),
            "filesystem_write_allowed": model.get("filesystem_write_allowed"),
            "shell_allowed": model.get("shell_allowed"),
            "remote_execution_allowed": model.get("remote_execution_allowed"),
            "pip_install_allowed": model.get("pip_install_allowed"),
            "marketplace_enabled": model.get("marketplace_enabled"),
            "critical_permissions_require_future_adr": model.get("critical_permissions_require_future_adr"),
            "local_first": True,
            "dry_run": True,
            "read_only": True,
            "plugin_code_loaded": False,
            "arbitrary_code_execution_performed": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_used": False,
            "plugin_execution_used": False,
            "preliminary": True,
        }

    def _policy_rule_ids(self) -> set[str]:
        try:
            payload = json.loads(self._resolve(self.options.policy_matrix_path).read_text(encoding="utf-8"))
        except Exception:
            return set()
        return {str(item.get("rule_id")) for item in payload.get("rules", []) if isinstance(item, dict) and item.get("rule_id")}

    def _resolve(self, value: str | Path) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()


def _permission_index(model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    permissions: dict[str, dict[str, Any]] = {}
    for permission in model.get("permissions", []) or []:
        if isinstance(permission, dict) and permission.get("permission_id"):
            permissions[str(permission["permission_id"])] = permission
    return permissions


def _alias_index(model: dict[str, Any]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for permission_id, permission in _permission_index(model).items():
        for alias in permission.get("aliases", []) or []:
            aliases[str(alias)] = permission_id
    return aliases


def _summary_template(model_path: str, schema_path: str, *, path_allowed: bool) -> dict[str, Any]:
    return {
        "model_path": model_path,
        "schema_path": schema_path,
        "path_allowed": path_allowed,
        "plugin_execution_allowed": False,
        "dynamic_import_allowed": False,
        "subprocess_allowed": False,
        "network_allowed": False,
        "filesystem_write_allowed": False,
        "plugin_code_loaded": False,
        "arbitrary_code_execution_performed": False,
        "preliminary": True,
    }


def _result(
    *,
    ok: bool,
    exit_code: ExitCode,
    message: str,
    summary: dict[str, Any],
    findings: list[Finding],
    model: dict[str, Any] | None = None,
) -> CommandResult:
    data: dict[str, Any] = {"summary": summary}
    if model is not None:
        data["permissions"] = [
            {
                "permission_id": permission.get("permission_id"),
                "effect": permission.get("effect"),
                "risk_level": permission.get("risk_level"),
                "requires_approval": permission.get("requires_approval"),
                "blocked_until": permission.get("blocked_until"),
                "aliases": permission.get("aliases", []),
            }
            for permission in model.get("permissions", [])
            if isinstance(permission, dict)
        ]
    return CommandResult("plugin permission-model validate", ok, exit_code, message, data=data, findings=findings)


def _blocking(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.FAIL, Severity.ERROR}]


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
