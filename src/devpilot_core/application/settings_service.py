from __future__ import annotations

import copy
import json
import time
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.providers import ProviderRegistry, parse_provider_config_file, parse_provider_config_payload, validate_provider_configs
from devpilot_core.modeling.local_provider_discovery import LocalProviderDiscoveryService, LocalProviderDiscoveryOptions
from devpilot_core.modeling.external_provider_enablement import (
    ExternalProviderEnablementService, FakeConnectivityResponse, enablement_request_from_dict,
)
from devpilot_core.policy.cost_guard import load_cost_policy
from devpilot_core.policy.secrets import REDACTED, redact_sensitive_string
from devpilot_core.schemas.builtins import parse_workspace_project_yaml

from .ui_workspace_context import UiWorkspaceContextResolver
from .model_gateway_settings_service import ModelGatewaySettingsService

_PROVIDER_MUTABLE_FIELDS = {"enabled", "default_model", "endpoint"}
_SECRET_KEY_EXCEPTIONS = {"api_key_env", "token_env_var", "requires_api_key", "secret_reference", "secrets_redacted", "raw_secrets_exposed"}
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


def _duration_ms(started_at: float) -> int:
    return max(0, round((time.perf_counter() - started_at) * 1000))


class SettingsApplicationService:
    """Read-only and plan-only settings facade for the local API/Web UI.

    FUNC-SPRINT-72 deliberately exposes settings through ApplicationService so
    the Web UI never reads `.devpilot/` or provider files directly. Write-like
    configuration changes are returned as plans only and never mutate files.
    """

    def __init__(self, root: Path, *, context_resolver: UiWorkspaceContextResolver | None = None) -> None:
        self.root = Path(root).resolve()
        self.context_resolver = context_resolver or UiWorkspaceContextResolver(self.root)
        self.external_enablement = ExternalProviderEnablementService(self.root)

    def workspace(self) -> CommandResult:
        context = self.context_resolver.resolve()
        project_path = context.project_file if context.valid and context.project_file else self.root / ".devpilot" / "project.yaml"
        workspace_root = context.effective_workspace_root
        findings: list[Finding] = []
        try:
            payload = parse_workspace_project_yaml(project_path)
            ok = True
            message = "Workspace settings loaded safely."
        except Exception as exc:
            payload = {}
            ok = False
            message = "Workspace settings could not be loaded."
            findings.append(Finding(id="SETTINGS_WORKSPACE_LOAD_BLOCK", message=str(exc), severity=Severity.BLOCK, path=_relative(project_path, workspace_root)))
        redacted = _redact_settings_value(payload)
        summary = {
            "settings_domain": "workspace",
            "path": _relative(project_path, workspace_root),
            "scope": "active-workspace" if context.active_workspace_root else "platform",
            "workspace_context": context.summary(),
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
            findings.append(Finding(id="SETTINGS_WORKSPACE_READ_PASS", message="Workspace settings read-only projection passed.", severity=Severity.INFO, path=_relative(project_path, workspace_root)))
        findings.extend(context.findings)
        return CommandResult(
            command="settings workspace",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message=message,
            data={"summary": summary, "workspace": redacted, "workspace_context": context.summary(), "raw_text_preview": _redact_settings_value(_bounded_text(project_path, limit=6000)), "notes": ["Settings UI reads this via API only.", "Workspace context is read-only and may be external only when explicitly configured and PathGuard-approved.", "No workspace settings are written by FUNC-SPRINT-72."]},
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
        policy_path = self.root / ".devpilot" / "modeling" / "local_provider_endpoint_policy.json"
        if policy_path.is_file():
            discovery = LocalProviderDiscoveryService(self.root, LocalProviderDiscoveryOptions(probe=False)).build()
            redacted_data["local_provider_health"] = _redact_settings_value((discovery.data or {}).get("report", {}))
            summary["local_provider_health_available"] = True
            summary["local_provider_health_probe_requested"] = False
        else:
            summary["local_provider_health_available"] = False
        enablement = self.external_enablement.status()
        redacted_data["external_provider_enablement"] = _redact_settings_value(enablement.data)
        summary["external_enablement_state_available"] = True
        summary["external_runtime_network_enabled_total"] = int((enablement.data or {}).get("summary", {}).get("runtime_network_enabled_total", 0))
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


    def model_gateway_settings(self, *, preview_input_tokens: int = 1200, preview_output_tokens: int = 300) -> CommandResult:
        return ModelGatewaySettingsService(self.root).snapshot(preview_input_tokens=preview_input_tokens, preview_output_tokens=preview_output_tokens)

    def model_gateway_controlled_evaluation(self, *, payload: dict[str, Any]) -> CommandResult:
        capabilities = tuple(str(item) for item in (payload.get("required_capabilities") or ["text_generation"]))
        return ModelGatewaySettingsService(self.root).controlled_evaluation(
            mode=str(payload.get("mode") or "mock"),
            workload_id=str(payload.get("workload_id") or "gsdlc-06-e-ui-eval"),
            required_capabilities=capabilities,
            selected_access_route_id=(str(payload.get("selected_access_route_id")) if payload.get("selected_access_route_id") else None),
            estimated_input_tokens=int(payload.get("estimated_input_tokens") or 900),
            estimated_output_tokens=int(payload.get("estimated_output_tokens") or 200),
            max_cost_usd=(None if payload.get("max_cost_usd") is None else float(payload.get("max_cost_usd"))),
            hard_stop_case=bool(payload.get("hard_stop_case", False)),
        )

    def provider_enablement_status(self) -> CommandResult:
        return self.external_enablement.status()

    def provider_enablement_plan(self, *, payload: dict[str, Any]) -> CommandResult:
        try:
            request = enablement_request_from_dict(payload)
        except Exception as exc:
            return CommandResult(
                command="settings providers enablement plan", ok=False, exit_code=ExitCode.BLOCK,
                message="External provider enablement request is malformed.",
                data={"summary":{"write_performed":False,"secrets_redacted":True}},
                findings=[Finding("PROVIDER_ENABLEMENT_REQUEST_INVALID", str(exc), Severity.BLOCK)],
            )
        return self.external_enablement.plan(request)

    def provider_enablement_connectivity_test(self, *, payload: dict[str, Any]) -> CommandResult:
        try:
            request = enablement_request_from_dict(payload)
        except Exception as exc:
            return CommandResult(command="settings providers connectivity-test",ok=False,exit_code=ExitCode.BLOCK,message="Connectivity request is malformed.",data={"summary":{"network_used":False,"external_api_used":False,"secrets_redacted":True}},findings=[Finding("PROVIDER_CONNECTIVITY_REQUEST_INVALID",str(exc),Severity.BLOCK)])
        mode = str(payload.get("connectivity_mode") or "fake").strip().lower()
        if mode != "fake":
            return self.external_enablement.connectivity_test(request, transport=None)
        case = str(payload.get("simulation_case") or "success").strip().lower()
        def transport(**kwargs):
            del kwargs
            if case == "invalid-key":
                return FakeConnectivityResponse(False, 401, "unauthorized", 0)
            if case == "timeout":
                return FakeConnectivityResponse(False, 504, "bounded-timeout", 0)
            if case == "malformed":
                return FakeConnectivityResponse(False, 502, "malformed-provider-response", 0)
            return FakeConnectivityResponse(True, 200, "ok", 2)
        return self.external_enablement.connectivity_test(request, transport=transport)

    def provider_enablement_apply(self, *, payload: dict[str, Any], approval: dict[str, Any] | None, actor_id: str, role_at_execution: str) -> CommandResult:
        try:
            request = enablement_request_from_dict(payload)
        except Exception as exc:
            return CommandResult(command="settings providers enablement apply",ok=False,exit_code=ExitCode.BLOCK,message="Enablement request is malformed.",data={"summary":{"updated":False,"secrets_redacted":True}},findings=[Finding("PROVIDER_ENABLEMENT_REQUEST_INVALID",str(exc),Severity.BLOCK)])
        return self.external_enablement.apply_enable(request, approval=approval, actor_id=actor_id, role_at_execution=role_at_execution)

    def provider_enablement_disable(self, *, provider_id: str, actor_id: str, role_at_execution: str, reason: str, revoke: bool = False) -> CommandResult:
        return self.external_enablement.disable(provider_id=provider_id, actor_id=actor_id, role_at_execution=role_at_execution, reason=reason, revoke=revoke)

    def provider_plan(self, *, provider_id: str, changes: dict[str, Any] | None = None, actor: str = "ui-local", reason: str = "Settings UI plan-only provider change") -> CommandResult:
        started_at = time.perf_counter()
        provider_id = str(provider_id or "").strip().lower()
        changes = dict(changes or {})
        source = self.root / ".devpilot" / "providers.yaml"
        if not source.is_file():
            source = self.root / ".devpilot" / "providers.yaml.example"
        source_path = _relative(source, self.root)
        payload, configs, parse_findings = parse_provider_config_file(source)
        current = next((config for config in configs if config.provider_id == provider_id), None)
        findings: list[Finding] = list(parse_findings)
        if current is None:
            findings.append(Finding(id="SETTINGS_PROVIDER_NOT_FOUND_BLOCK", message=f"Provider '{provider_id}' does not exist in current provider settings.", severity=Severity.BLOCK, path=source_path, metadata={"provider_id": provider_id}))
            return CommandResult(
                command="settings providers plan",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Provider plan blocked because provider id was not found.",
                data={"summary": {"provider_id": provider_id, "write_performed": False, "plan_only": True, "validation_target": "synthetic-proposal", "duration_ms": _duration_ms(started_at), "preliminary": True}},
                findings=findings,
            )

        unsupported = sorted(set(changes) - _PROVIDER_MUTABLE_FIELDS)
        proposed_changes = {key: changes[key] for key in sorted(changes) if key in _PROVIDER_MUTABLE_FIELDS}
        for key, value in proposed_changes.items():
            if isinstance(value, str) and redact_sensitive_string(value)[1] > 0:
                findings.append(Finding(id="SETTINGS_PROVIDER_PLAN_SECRET_BLOCK", message=f"Proposed field '{key}' contains secret-like content.", severity=Severity.BLOCK, path=source_path, metadata={"provider_id": provider_id, "field": key}))
        if unsupported:
            findings.append(Finding(id="SETTINGS_PROVIDER_PLAN_UNSUPPORTED_FIELD_WARNING", message="Unsupported provider fields were ignored by the plan-only editor.", severity=Severity.WARNING, metadata={"unsupported_fields": unsupported}))
        if current.external_api and bool(proposed_changes.get("enabled", current.enabled)):
            findings.append(Finding(id="SETTINGS_PROVIDER_EXTERNAL_ENABLE_BLOCK", message="Settings UI cannot enable external API providers; use a later approval-gated workflow with CostGuard.", severity=Severity.BLOCK, path=source_path, metadata={"provider_id": provider_id}))

        synthetic_payload = copy.deepcopy(payload)
        synthetic_items: list[dict[str, Any]] = []
        provider_updated = False
        for raw_item in synthetic_payload.get("providers", []):
            if not isinstance(raw_item, dict):
                synthetic_items.append(raw_item)
                continue
            item = copy.deepcopy(raw_item)
            raw_id = str(item.get("id") or item.get("provider_id") or "").strip().lower()
            if raw_id == provider_id:
                item.update(proposed_changes)
                provider_updated = True
            synthetic_items.append(item)
        synthetic_payload["providers"] = synthetic_items
        if not provider_updated:
            findings.append(Finding(id="SETTINGS_PROVIDER_SYNTHETIC_TARGET_MISSING_BLOCK", message="The provider existed in parsed configs but not in the synthetic source payload.", severity=Severity.BLOCK, path=source_path, metadata={"provider_id": provider_id}))

        _, synthetic_configs, synthetic_parse_findings = parse_provider_config_payload(
            synthetic_payload,
            source_path=f"{source_path}#synthetic-proposal",
        )
        findings.extend(synthetic_parse_findings)
        findings.extend(validate_provider_configs(synthetic_configs, payload=synthetic_payload, source_path=f"{source_path}#synthetic-proposal"))
        proposed_config = next((config for config in synthetic_configs if config.provider_id == provider_id), None)
        if proposed_config is None:
            findings.append(Finding(id="SETTINGS_PROVIDER_SYNTHETIC_PARSE_BLOCK", message="The proposed provider configuration could not be parsed safely.", severity=Severity.BLOCK, path=source_path, metadata={"provider_id": provider_id}))

        current_data = _redact_settings_value(current.to_dict())
        proposed_data = _redact_settings_value(proposed_config.to_dict()) if proposed_config is not None else {}
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
        duration_ms = _duration_ms(started_at)
        plan = {
            "provider_id": provider_id,
            "actor": actor,
            "reason": reason,
            "source_path": source_path,
            "validation_target": "synthetic-proposal",
            "validation_steps": [
                "load-source-once",
                "apply-supported-proposed-changes-in-memory",
                "parse-synthetic-payload",
                "validate-synthetic-provider-configs",
                "redact-current-and-proposed",
                "return-plan-without-write",
            ],
            "current": current_data,
            "proposed_changes": _redact_settings_value(proposed_changes),
            "proposed_preview": proposed_data,
            "unsupported_fields": unsupported,
            "write_performed": False,
            "plan_only": True,
            "requires_approval": bool(proposed_changes),
            "external_api_enable_blocked": any(f.id in {"SETTINGS_PROVIDER_EXTERNAL_ENABLE_BLOCK", "MODEL_PROVIDER_EXTERNAL_ENABLED_BLOCKED"} for f in findings),
            "secrets_redacted": True,
            "duration_ms": duration_ms,
        }
        if not blocking:
            findings.insert(0, Finding(id="SETTINGS_PROVIDER_PLAN_PASS", message="Synthetic provider change plan validated without writing files.", severity=Severity.INFO, path=source_path, metadata={"provider_id": provider_id, "duration_ms": duration_ms}))
        return CommandResult(
            command="settings providers plan",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Provider change plan generated and validated without writing files." if not blocking else "Provider change plan was blocked by safety gates.",
            data={
                "summary": {
                    "settings_domain": "providers",
                    "provider_id": provider_id,
                    "write_performed": False,
                    "plan_only": True,
                    "validation_target": "synthetic-proposal",
                    "requires_approval": bool(proposed_changes),
                    "blocking_findings_total": len(blocking),
                    "duration_ms": duration_ms,
                    "preliminary": True,
                },
                "plan": plan,
                "notes": [
                    "POST-H-EVAL-002-01-D corrective 325 never writes .devpilot/providers.yaml.",
                    "External API providers remain disabled unless a future explicit approval-gated workflow changes that policy.",
                ],
            },
            findings=findings,
        )
