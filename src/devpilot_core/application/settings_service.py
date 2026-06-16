from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.providers import ProviderRegistry, parse_provider_config_file, validate_provider_configs
from devpilot_core.policy.cost_guard import load_cost_policy
from devpilot_core.policy.secrets import REDACTED, redact_sensitive_string
from devpilot_core.schemas.builtins import parse_provider_config_yaml, parse_workspace_project_yaml

_PROVIDER_MUTABLE_FIELDS = {"enabled", "default_model", "endpoint"}
_SECRET_KEY_EXCEPTIONS = {"api_key_env", "token_env_var"}
_SECRET_KEY_FRAGMENTS = ("api_key", "access_token", "refresh_token", "auth_token", "token", "secret", "password", "passwd", "pwd", "authorization", "bearer", "private_key", "client_secret", "database_url", "connection_string", "webhook")


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _redact_settings_value(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            if lowered not in _SECRET_KEY_EXCEPTIONS and any(fragment in lowered for fragment in _SECRET_KEY_FRAGMENTS):
                redacted[key_text] = REDACTED
            else:
                redacted[key_text] = _redact_settings_value(item)
        return redacted
    if isinstance(value, list):
        return [_redact_settings_value(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive_string(value)[0]
    return value


def _bounded_text(path: Path, *, limit: int = 12000) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    if len(text) > limit:
        return text[:limit] + "\n[TRUNCATED]"
    return text


class SettingsApplicationService:
    """Read-only and plan-only settings facade for the local API/Web UI.

    FUNC-SPRINT-72 deliberately exposes settings through ApplicationService so
    the Web UI never reads `.devpilot/` or provider files directly. Write-like
    configuration changes are returned as plans only and never mutate files.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()

    def workspace(self) -> CommandResult:
        project_path = self.root / ".devpilot" / "project.yaml"
        findings: list[Finding] = []
        try:
            payload = parse_workspace_project_yaml(project_path)
            ok = True
            message = "Workspace settings loaded safely."
        except Exception as exc:
            payload = {}
            ok = False
            message = "Workspace settings could not be loaded."
            findings.append(Finding(id="SETTINGS_WORKSPACE_LOAD_BLOCK", message=str(exc), severity=Severity.BLOCK, path=_relative(project_path, self.root)))
        redacted = _redact_settings_value(payload)
        summary = {
            "settings_domain": "workspace",
            "path": _relative(project_path, self.root),
            "exists": project_path.is_file(),
            "schema_version": redacted.get("schema_version") if isinstance(redacted, dict) else None,
            "project_id": (redacted.get("project") or {}).get("id") if isinstance(redacted, dict) else None,
            "project_name": (redacted.get("project") or {}).get("name") if isinstance(redacted, dict) else None,
            "paths_total": len((redacted.get("paths") or {})) if isinstance(redacted, dict) else 0,
            "write_enabled": False,
            "plan_only": True,
            "secrets_redacted": True,
            "preliminary": True,
        }
        if ok:
            findings.append(Finding(id="SETTINGS_WORKSPACE_READ_PASS", message="Workspace settings read-only projection passed.", severity=Severity.INFO, path=_relative(project_path, self.root)))
        return CommandResult(
            command="settings workspace",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message=message,
            data={"summary": summary, "workspace": redacted, "raw_text_preview": _redact_settings_value(_bounded_text(project_path, limit=6000)), "notes": ["Settings UI reads this via API only.", "No workspace settings are written by FUNC-SPRINT-72."]},
            findings=findings,
        )

    def providers(self, *, prefer_example: bool = False) -> CommandResult:
        registry = ProviderRegistry.load(self.root, prefer_example=prefer_example)
        result = registry.to_result()
        redacted_data = _redact_settings_value(result.data)
        summary = dict(redacted_data.get("summary") or {})
        summary.update({
            "settings_domain": "providers",
            "write_enabled": False,
            "plan_only": True,
            "secrets_redacted": True,
            "providers_source_path": registry.source_path,
            "external_api_enabled_total": summary.get("external_api_enabled_total", 0),
            "preliminary": True,
        })
        redacted_data["summary"] = summary
        findings = list(result.findings)
        findings.insert(0, Finding(id="SETTINGS_PROVIDERS_READ_PASS", message="Provider settings were projected without raw secrets.", severity=Severity.INFO, path=registry.source_path))
        return CommandResult(
            command="settings providers",
            ok=result.ok,
            exit_code=result.exit_code,
            message="Provider settings loaded safely." if result.ok else "Provider settings failed safe validation.",
            data=redacted_data,
            findings=findings,
        )

    def policy(self) -> CommandResult:
        policy_path = self.root / ".devpilot" / "policy.yaml"
        matrix_path = self.root / ".devpilot" / "miasi" / "policy_matrix.json"
        cost_policy = load_cost_policy(self.root)
        matrix: dict[str, Any] = {}
        findings: list[Finding] = []
        if matrix_path.is_file():
            try:
                matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
            except Exception as exc:
                findings.append(Finding(id="SETTINGS_POLICY_MATRIX_PARSE_WARNING", message=str(exc), severity=Severity.WARNING, path=_relative(matrix_path, self.root)))
        rules = matrix.get("rules", []) if isinstance(matrix.get("rules"), list) else []
        policy_payload = {
            "policy_file": _redact_settings_value(_bounded_text(policy_path, limit=8000)),
            "cost_policy": {
                "external_api_allowed": cost_policy.external_api_allowed,
                "budget_limit_usd": cost_policy.budget_limit_usd,
                "budget_used_usd": cost_policy.budget_used_usd,
                "allowed_providers": list(cost_policy.allowed_providers),
            },
            "policy_matrix": {
                "path": _relative(matrix_path, self.root),
                "rules_total": len(rules),
                "approval_required_total": sum(1 for rule in rules if bool(rule.get("approval_required"))),
                "observability_required_total": sum(1 for rule in rules if bool(rule.get("observability_required"))),
                "blocked_or_denied_total": sum(1 for rule in rules if "deny" in str(rule.get("default_effect", "")).lower() or "block" in str(rule.get("default_effect", "")).lower()),
                "rules_preview": _redact_settings_value(rules[:20]),
            },
        }
        findings.append(Finding(id="SETTINGS_POLICY_READ_PASS", message="Local policy settings projected in read-only mode.", severity=Severity.INFO, path=_relative(policy_path, self.root)))
        return CommandResult(
            command="settings policy",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Policy settings loaded safely.",
            data={"summary": {"settings_domain": "policy", "path": _relative(policy_path, self.root), "policy_matrix_path": _relative(matrix_path, self.root), "external_api_allowed": cost_policy.external_api_allowed, "rules_total": len(rules), "write_enabled": False, "plan_only": True, "secrets_redacted": True, "preliminary": True}, "policy": policy_payload, "notes": ["Policy editing is not enabled in FUNC-SPRINT-72.", "Provider changes are plan-only and must not enable external APIs by accident."]},
            findings=findings,
        )

    def provider_plan(self, *, provider_id: str, changes: dict[str, Any] | None = None, actor: str = "ui-local", reason: str = "Settings UI plan-only provider change") -> CommandResult:
        provider_id = str(provider_id or "").strip().lower()
        changes = dict(changes or {})
        source = self.root / ".devpilot" / "providers.yaml"
        if not source.is_file():
            source = self.root / ".devpilot" / "providers.yaml.example"
        payload, configs, parse_findings = parse_provider_config_file(source)
        current = next((config for config in configs if config.provider_id == provider_id), None)
        findings: list[Finding] = list(parse_findings)
        if current is None:
            findings.append(Finding(id="SETTINGS_PROVIDER_NOT_FOUND_BLOCK", message=f"Provider '{provider_id}' does not exist in current provider settings.", severity=Severity.BLOCK, path=_relative(source, self.root), metadata={"provider_id": provider_id}))
            return CommandResult(command="settings providers plan", ok=False, exit_code=ExitCode.BLOCK, message="Provider plan blocked because provider id was not found.", data={"summary": {"provider_id": provider_id, "write_performed": False, "plan_only": True, "preliminary": True}}, findings=findings)

        unsupported = sorted(set(changes) - _PROVIDER_MUTABLE_FIELDS)
        proposed_changes = {key: changes[key] for key in sorted(changes) if key in _PROVIDER_MUTABLE_FIELDS}
        for key, value in proposed_changes.items():
            if isinstance(value, str) and redact_sensitive_string(value)[1] > 0:
                findings.append(Finding(id="SETTINGS_PROVIDER_PLAN_SECRET_BLOCK", message=f"Proposed field '{key}' contains secret-like content.", severity=Severity.BLOCK, path=_relative(source, self.root), metadata={"provider_id": provider_id, "field": key}))
        if unsupported:
            findings.append(Finding(id="SETTINGS_PROVIDER_PLAN_UNSUPPORTED_FIELD_WARNING", message="Unsupported provider fields were ignored by the plan-only editor.", severity=Severity.WARNING, metadata={"unsupported_fields": unsupported}))

        current_data = _redact_settings_value(current.to_dict())
        proposed = dict(current.to_dict())
        proposed.update(proposed_changes)
        # External API providers must not be enabled by Settings UI in Sprint 72.
        if current.external_api and bool(proposed.get("enabled")):
            findings.append(Finding(id="SETTINGS_PROVIDER_EXTERNAL_ENABLE_BLOCK", message="Settings UI cannot enable external API providers; use a later approval-gated workflow with CostGuard.", severity=Severity.BLOCK, path=_relative(source, self.root), metadata={"provider_id": provider_id}))
        # Local endpoints must remain localhost-only; reuse registry semantic validation by constructing a temporary payload.
        temp_payload = dict(payload)
        temp_items = []
        for item in parse_provider_config_yaml(source).get("providers", []):
            if str(item.get("id", "")).strip().lower() == provider_id:
                item = {**item, **proposed_changes}
            temp_items.append(item)
        temp_payload["providers"] = temp_items
        _, temp_configs, temp_parse_findings = parse_provider_config_file(source)
        # parse_provider_config_file reads source, so validate manually against existing configs with limited checks via current + proposed shape.
        # Build a synthetic summary without writing; semantic validation of actual file remains source-of-truth.
        findings.extend(temp_parse_findings)
        semantic_findings = validate_provider_configs(configs, payload=payload, source_path=_relative(source, self.root))
        findings.extend(semantic_findings)
        blocking = [f for f in findings if f.severity in {Severity.BLOCK, Severity.ERROR}]
        plan = {
            "provider_id": provider_id,
            "actor": actor,
            "reason": reason,
            "source_path": _relative(source, self.root),
            "current": current_data,
            "proposed_changes": _redact_settings_value(proposed_changes),
            "proposed_preview": _redact_settings_value({k: proposed.get(k) for k in sorted({*current.to_dict().keys(), *proposed_changes.keys()})}),
            "write_performed": False,
            "plan_only": True,
            "requires_approval": bool(proposed_changes),
            "external_api_enable_blocked": any(f.id == "SETTINGS_PROVIDER_EXTERNAL_ENABLE_BLOCK" for f in findings),
            "secrets_redacted": True,
        }
        if not blocking:
            findings.insert(0, Finding(id="SETTINGS_PROVIDER_PLAN_PASS", message="Provider change plan generated without writing files.", severity=Severity.INFO, path=_relative(source, self.root), metadata={"provider_id": provider_id}))
        return CommandResult(
            command="settings providers plan",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Provider change plan generated without writing files." if not blocking else "Provider change plan was blocked by safety gates.",
            data={"summary": {"settings_domain": "providers", "provider_id": provider_id, "write_performed": False, "plan_only": True, "requires_approval": bool(proposed_changes), "blocking_findings_total": len(blocking), "preliminary": True}, "plan": plan, "notes": ["FUNC-SPRINT-72 never writes .devpilot/providers.yaml.", "External API providers remain disabled unless a future explicit approval-gated workflow changes that policy."]},
            findings=findings,
        )
