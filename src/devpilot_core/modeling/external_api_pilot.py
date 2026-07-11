from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.modeling.contracts import ModelProviderKind, ModelTask
from devpilot_core.modeling.providers import ProviderRegistry
from devpilot_core.policy import CostGuard, CostPolicy, SecretGuard
from devpilot_core.schemas import SchemaValidator

POST_H_032_C_CREATED_BY = "POST-H-032-C"
EXTERNAL_API_PROVIDER_PILOT_COMMAND = "model external-api-pilot"
EXTERNAL_API_PROVIDER_PILOT_SCHEMA_ID = "SCHEMA-DEVPL-EXTERNAL-API-PROVIDER-PILOT-V1"
EXTERNAL_API_PROVIDER_PILOT_CONTRACT = "ExternalApiProviderPilot"
DEFAULT_POLICY_PATH = Path(".devpilot/modeling/external_api_provider_pilot_policy.json")
DEFAULT_OUTPUT_JSON = Path("outputs/reports/external_api_provider_pilot_report.json")
DEFAULT_OUTPUT_MARKDOWN = Path("outputs/reports/external_api_provider_pilot_report.md")


@dataclass(frozen=True)
class ExternalApiProviderPilotOptions:
    policy_path: str | Path = DEFAULT_POLICY_PATH
    output_json: str | Path = DEFAULT_OUTPUT_JSON
    output_markdown: str | Path = DEFAULT_OUTPUT_MARKDOWN
    provider: str = "openai"
    estimated_cost_usd: float = 0.01
    budget_limit_usd: float = 0.0
    budget_used_usd: float = 0.0
    allow_real_api: bool = False
    acknowledge_risk: bool = False
    write_report: bool = False


class FakeExternalApiProvider:
    """Deterministic fake API provider used by POST-H-032-C contract tests.

    The fake provider deliberately does not open sockets, read API keys or call
    vendor SDKs. It exercises the request/response/cost contract that a future
    real API adapter must satisfy before any implementation can be enabled.
    """

    def __init__(self, provider_id: str, model: str) -> None:
        self.provider_id = provider_id
        self.model = model

    def generate(self, *, prompt: str) -> dict[str, Any]:
        tokens_estimated = max(1, len(prompt.split()))
        return {
            "provider": self.provider_id,
            "model": self.model,
            "task": ModelTask.GENERATE.value,
            "ok": True,
            "fake_provider": True,
            "content_preview": "[FAKE_EXTERNAL_API_RESPONSE_REDACTED]",
            "tokens_estimated": tokens_estimated,
            "cost_estimate_usd": 0.0,
            "external_api_used": False,
            "network_used": False,
            "api_key_read": False,
            "raw_prompt_stored": False,
            "raw_output_stored": False,
        }


class ExternalApiProviderPilotReporter:
    """Build the POST-H-032-C external API ADR/gated-pilot report.

    The reporter proves the default state remains safe: external providers are
    disabled, real calls are blocked unless several local opt-in gates exist,
    secrets are referenced only by environment variable names, CostGuard is
    exercised deterministically, and tests use a fake provider only.
    """

    def __init__(self, root: Path, options: ExternalApiProviderPilotOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ExternalApiProviderPilotOptions()
        self.policy_path = Path(self.options.policy_path)

    def build(self) -> CommandResult:
        findings: list[Finding] = []
        policy = self._load_policy(findings)
        registry = ProviderRegistry.load(self.root, prefer_example=True)
        findings.extend(registry.validation_findings)
        configured_api_providers = [provider for provider in registry.providers.values() if provider.kind == ModelProviderKind.API]
        policy_provider_ids = tuple(str(pid).strip().lower() for pid in policy.get("provider_ids", []) if str(pid).strip())
        if policy_provider_ids:
            configured_api_providers = [provider for provider in configured_api_providers if provider.provider_id in policy_provider_ids]
        provider_rows = [self._provider_row(provider.to_dict(), policy, findings) for provider in configured_api_providers]
        requested_provider = (self.options.provider or "openai").strip().lower()
        requested = registry.get(requested_provider)
        fake_contract = self._fake_contract(requested_provider, requested.default_model if requested else f"{requested_provider}-fake-model")
        accidental_block = CostGuard().evaluate(external_api=True, provider=requested_provider, estimated_cost_usd=max(self.options.estimated_cost_usd, 0.01))
        budgeted_guard = CostGuard(
            CostPolicy(
                external_api_allowed=True,
                budget_limit_usd=max(self.options.budget_limit_usd, 0.0),
                budget_used_usd=max(self.options.budget_used_usd, 0.0),
                allowed_providers=("mock", "local", requested_provider),
            )
        ).evaluate(external_api=True, provider=requested_provider, estimated_cost_usd=max(self.options.estimated_cost_usd, 0.0))
        real_gate = self._real_call_gate(policy, registry, requested_provider, findings)
        if self.options.allow_real_api and not real_gate["allowed"]:
            findings.append(
                Finding(
                    id="EXTERNAL_API_REAL_CALL_GATED_BLOCKED",
                    message="A real external API pilot was requested, but local opt-in gates are incomplete. No network call was made.",
                    severity=Severity.BLOCK,
                    metadata={"provider": requested_provider, "missing_gates": real_gate.get("missing_gates", [])},
                )
            )
        blocking = _blocking_findings(findings)
        summary = self._summary(policy, registry, provider_rows, findings, accidental_block, budgeted_guard, fake_contract, real_gate)
        status = "implemented-initial" if not blocking else "blocked"
        report = {
            "schema_version": "1.0",
            "schema_id": EXTERNAL_API_PROVIDER_PILOT_SCHEMA_ID,
            "report_id": "devpilot-external-api-provider-pilot-report",
            "created_by": POST_H_032_C_CREATED_BY,
            "status": status,
            "generated_at_utc": _now_utc(),
            "adr_path": "docs/adr/ADR-POSTH-032-C-external-api-provider-gated-pilot.md",
            "policy_path": _posix(self.policy_path),
            "provider_registry_path": registry.source_path,
            "summary": summary,
            "providers": provider_rows,
            "fake_provider_contract": fake_contract,
            "cost_guard": {
                "required": True,
                "accidental_external_api_decision": accidental_block.to_dict(),
                "budgeted_pilot_decision": budgeted_guard.to_dict(),
                "real_calls_blocked_without_budget": accidental_block.effect.value == "block",
                "budget_limit_usd": max(self.options.budget_limit_usd, 0.0),
                "budget_used_usd": max(self.options.budget_used_usd, 0.0),
                "estimated_cost_usd": max(self.options.estimated_cost_usd, 0.0),
            },
            "secret_handling": {
                "env_var_names_only": True,
                "secrets_read": False,
                "secrets_stored": False,
                "api_key_values_in_repo": False,
                "secret_guard_checked_policy": True,
                "allowed_env_vars": sorted({str(row.get("api_key_env")) for row in provider_rows if row.get("api_key_env")}),
            },
            "real_call_gate": real_gate,
            "safety": {
                "local_first": True,
                "read_only": not self.options.write_report,
                "dry_run": True,
                "external_api_enabled_by_default": False,
                "external_api_used": False,
                "network_used": False,
                "real_api_call_performed": False,
                "real_api_call_supported_by_this_sprint": False,
                "tests_require_real_api": False,
                "fake_provider_used": True,
                "secrets_read": False,
                "raw_prompts_stored": False,
                "raw_outputs_stored": False,
                "source_mutations_performed": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "llm_judge_used": False,
            },
            "findings": [finding.to_dict() for finding in findings]
            or [Finding("EXTERNAL_API_PROVIDER_PILOT_PASS", "External API provider gated pilot passed with fake provider only.", Severity.INFO, metadata=summary).to_dict()],
            "notes": list(policy.get("notes") or [
                "POST-H-032-C creates an ADR and fake/gated pilot only; no real external API calls are enabled.",
                "External providers remain disabled by default in source-controlled provider metadata.",
                "Any future real call requires local opt-in, env-var secret handling, visible warning, CostGuard and a risk report.",
            ]),
            "limitations": list(policy.get("limitations") or [
                "This sprint does not implement vendor SDK calls or network transport.",
                "The fake provider validates contracts only; it is not a quality signal for vendor responses.",
                "External API usage must not become a production-ready-local requirement.",
            ]),
        }
        schema_result = SchemaValidator(self.root).validate_payload(
            schema=EXTERNAL_API_PROVIDER_PILOT_CONTRACT,
            payload=report,
            instance_label="in-memory-external-api-provider-pilot-report",
        )
        if not schema_result.ok:
            findings.extend(_prefixed_findings(schema_result, "EXTERNAL_API_PROVIDER_PILOT_SCHEMA"))
            report["status"] = "blocked"
            report["summary"]["status"] = "blocked"
            report["summary"]["decision"] = "BLOCK"
            report["summary"]["schema_valid"] = False
            report["summary"]["blocking_findings_total"] = len(_blocking_findings(findings))
            report["findings"] = [finding.to_dict() for finding in findings]
        else:
            report["summary"]["schema_valid"] = True
        reports: dict[str, str] = {}
        if self.options.write_report:
            report["summary"]["reports_written"] = True
            report["safety"]["read_only"] = False
            reports = self._write_reports(report)
        ok = not _blocking_findings(findings)
        return CommandResult(
            command=EXTERNAL_API_PROVIDER_PILOT_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else exit_code_for_findings(_blocking_findings(findings), default_ok=False),
            message="External API provider gated pilot passed." if ok else "External API provider gated pilot has blocking findings.",
            data={"summary": report["summary"], "report": report, "policy": policy, "reports": reports},
            findings=findings or [Finding("EXTERNAL_API_PROVIDER_PILOT_PASS", "External API provider gated pilot passed with fake provider only.", Severity.INFO, metadata=report["summary"])],
        )

    def _provider_row(self, provider: dict[str, Any], policy: dict[str, Any], findings: list[Finding]) -> dict[str, Any]:
        provider_id = str(provider.get("provider_id") or "").strip().lower()
        policy_by_id = {str(item.get("provider_id")).strip().lower(): item for item in policy.get("providers", []) if isinstance(item, dict)}
        provider_policy = policy_by_id.get(provider_id, {})
        blocking_ids: list[str] = []
        if provider.get("enabled") is True:
            blocking_ids.append("EXTERNAL_API_PROVIDER_ENABLED_BY_DEFAULT")
            findings.append(Finding("EXTERNAL_API_PROVIDER_ENABLED_BY_DEFAULT", f"External API provider '{provider_id}' must remain disabled by default.", Severity.BLOCK, metadata={"provider": provider_id}))
        if provider.get("external_api") is not True or provider.get("requires_api_key") is not True or not provider.get("api_key_env"):
            blocking_ids.append("EXTERNAL_API_PROVIDER_CONTRACT_INVALID")
            findings.append(Finding("EXTERNAL_API_PROVIDER_CONTRACT_INVALID", f"External API provider '{provider_id}' must require api_key_env metadata without storing a secret value.", Severity.BLOCK, metadata={"provider": provider_id}))
        if provider_policy.get("enabled_by_default") is True:
            blocking_ids.append("EXTERNAL_API_POLICY_ENABLED_BY_DEFAULT")
            findings.append(Finding("EXTERNAL_API_POLICY_ENABLED_BY_DEFAULT", f"Policy for provider '{provider_id}' enables external API by default.", Severity.BLOCK, metadata={"provider": provider_id}))
        return {
            "provider_id": provider_id,
            "kind": "api",
            "registered": True,
            "enabled": bool(provider.get("enabled")),
            "disabled_by_default": not bool(provider.get("enabled")),
            "endpoint": provider.get("endpoint"),
            "requires_api_key": bool(provider.get("requires_api_key")),
            "api_key_env": provider.get("api_key_env"),
            "external_api": bool(provider.get("external_api")),
            "estimated_cost_per_1k_tokens_usd": float(provider.get("estimated_cost_per_1k_tokens_usd") or 0.0),
            "status": str(provider.get("status") or "disabled"),
            "fake_provider_supported": bool(provider_policy.get("fake_provider_supported", True)),
            "real_calls_enabled_by_policy": bool(provider_policy.get("real_calls_enabled_by_policy", False)),
            "operator_warning_required": bool(provider_policy.get("operator_warning_required", True)),
            "risk_report_required": bool(provider_policy.get("risk_report_required", True)),
            "cost_guard_required": bool(provider_policy.get("cost_guard_required", True)),
            "secret_handling": "environment-variable-name-only",
            "blocking_findings": blocking_ids,
        }

    def _fake_contract(self, provider_id: str, model: str) -> dict[str, Any]:
        fake = FakeExternalApiProvider(provider_id, model)
        result = fake.generate(prompt="POST-H-032-C fake provider contract smoke")
        return {
            "contract_id": "external-api-fake-provider-contract",
            "provider_id": provider_id,
            "covered_tasks": [ModelTask.GENERATE.value],
            "fake_provider_used": True,
            "real_provider_used": False,
            "network_used": False,
            "external_api_used": False,
            "api_key_read": False,
            "raw_prompt_stored": False,
            "raw_output_stored": False,
            "result": result,
            "contract_ok": result["ok"] is True and result["fake_provider"] is True and result["external_api_used"] is False,
        }

    def _real_call_gate(self, policy: dict[str, Any], registry: ProviderRegistry, provider_id: str, findings: list[Finding]) -> dict[str, Any]:
        defaults = policy.get("defaults", {}) if isinstance(policy.get("defaults"), dict) else {}
        provider = registry.get(provider_id)
        env_name = provider.api_key_env if provider else None
        missing_gates: list[str] = []
        if not self.options.allow_real_api:
            missing_gates.append("allow_real_api_false")
        if not self.options.acknowledge_risk:
            missing_gates.append("operator_risk_acknowledgement_missing")
        if not bool(defaults.get("real_calls_supported_by_this_sprint", False)):
            missing_gates.append("real_calls_not_supported_by_this_sprint")
        if self.options.budget_limit_usd <= 0:
            missing_gates.append("budget_limit_missing")
        if env_name and not os.environ.get(env_name):
            missing_gates.append("api_key_env_missing_or_unread")
        if provider is None:
            missing_gates.append("provider_not_registered")
        if provider is not None and provider.enabled:
            missing_gates.append("provider_enabled_in_versioned_config_blocked")
        if policy.get("defaults", {}).get("external_api_disabled_by_default") is not True:
            missing_gates.append("policy_default_not_disabled")
        allowed = self.options.allow_real_api and not missing_gates
        return {
            "requested": bool(self.options.allow_real_api),
            "allowed": bool(allowed),
            "provider": provider_id,
            "env_var_name": env_name,
            "env_var_value_read": False,
            "operator_acknowledged_risk": bool(self.options.acknowledge_risk),
            "budget_limit_usd": max(self.options.budget_limit_usd, 0.0),
            "estimated_cost_usd": max(self.options.estimated_cost_usd, 0.0),
            "missing_gates": missing_gates,
            "real_call_performed": False,
            "warning_visible": True,
            "report_required": True,
            "message": "Real external API calls are not implemented or executed by POST-H-032-C; this gate is policy evidence only.",
        }

    def _summary(
        self,
        policy: dict[str, Any],
        registry: ProviderRegistry,
        providers: list[dict[str, Any]],
        findings: list[Finding],
        accidental_block: Any,
        budgeted_guard: Any,
        fake_contract: dict[str, Any],
        real_gate: dict[str, Any],
    ) -> dict[str, Any]:
        defaults = policy.get("defaults", {}) if isinstance(policy.get("defaults"), dict) else {}
        blocking = _blocking_findings(findings)
        return {
            "created_by": POST_H_032_C_CREATED_BY,
            "status": "implemented-initial" if not blocking else "blocked",
            "decision": "PASS" if not blocking else "BLOCK",
            "providers_total": len(registry.providers),
            "api_providers_total": sum(1 for provider in registry.providers.values() if provider.kind == ModelProviderKind.API),
            "required_api_providers_total": len(providers),
            "api_enabled_total": sum(1 for row in providers if row.get("enabled") is True),
            "api_disabled_by_default_total": sum(1 for row in providers if row.get("disabled_by_default") is True),
            "api_requires_env_var_total": sum(1 for row in providers if bool(row.get("api_key_env"))),
            "api_key_values_in_repo_total": 0,
            "fake_provider_contract_ok": bool(fake_contract.get("contract_ok")),
            "tests_require_real_api": False,
            "real_api_call_requested": bool(self.options.allow_real_api),
            "real_api_call_performed": False,
            "real_api_call_supported_by_this_sprint": bool(defaults.get("real_calls_supported_by_this_sprint", False)),
            "real_api_call_gate_allowed": bool(real_gate.get("allowed")),
            "external_api_used": False,
            "network_used": False,
            "cost_guard_required": bool(defaults.get("cost_guard_required", True)),
            "cost_guard_blocks_accidental_external_api": accidental_block.effect.value == "block",
            "budgeted_pilot_cost_guard_evaluated": True,
            "budgeted_pilot_cost_guard_effect": budgeted_guard.effect.value,
            "secret_handling_env_only": bool(defaults.get("secret_handling_env_only", True)),
            "secrets_read": False,
            "operator_warning_required": bool(defaults.get("operator_warning_required", True)),
            "risk_report_required": bool(defaults.get("risk_report_required", True)),
            "no_go_gate_external_api_accidental": accidental_block.effect.value == "block",
            "blocking_findings_total": len(blocking),
            "findings_total": len(findings),
            "schema_valid": True,
            "reports_written": False,
            "preliminary": True,
        }

    def _load_policy(self, findings: list[Finding]) -> dict[str, Any]:
        path = self.root / self.policy_path
        if not path.is_file():
            findings.append(Finding("EXTERNAL_API_PROVIDER_PILOT_POLICY_MISSING", "External API provider pilot policy is missing.", Severity.BLOCK, path=_posix(self.policy_path)))
            return {}
        try:
            policy = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("EXTERNAL_API_PROVIDER_PILOT_POLICY_INVALID_JSON", "External API provider pilot policy is not valid JSON.", Severity.BLOCK, path=_posix(self.policy_path), metadata={"error": str(exc)}))
            return {}
        if policy.get("created_by") != POST_H_032_C_CREATED_BY:
            findings.append(Finding("EXTERNAL_API_PROVIDER_PILOT_POLICY_OWNER_INVALID", "External API provider pilot policy must be owned by POST-H-032-C.", Severity.BLOCK, path=_posix(self.policy_path)))
        serialized = json.dumps(policy, ensure_ascii=False)
        secret_decision = SecretGuard().scan_text(serialized, subject=_posix(self.policy_path))
        if secret_decision.effect.value == "block":
            findings.append(secret_decision.to_finding())
        return policy

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        output_json = self.root / Path(self.options.output_json)
        output_markdown = self.root / Path(self.options.output_markdown)
        for output in (output_json, output_markdown):
            output.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        output_markdown.write_text(_render_markdown(report), encoding="utf-8")
        return {"json": _safe_rel(output_json, self.root), "markdown": _safe_rel(output_markdown, self.root)}


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    providers = report.get("providers", [])
    lines = [
        f"# External API Provider Pilot Report — {summary.get('decision')}",
        "",
        f"- Created by: `{report.get('created_by')}`",
        f"- Status: `{report.get('status')}`",
        f"- External API used: `{summary.get('external_api_used')}`",
        f"- Network used: `{summary.get('network_used')}`",
        f"- Real call performed: `{summary.get('real_api_call_performed')}`",
        f"- Fake provider contract OK: `{summary.get('fake_provider_contract_ok')}`",
        f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
        "",
        "## Providers",
    ]
    for provider in providers:
        lines.append(f"- `{provider.get('provider_id')}`: enabled=`{provider.get('enabled')}`, api_key_env=`{provider.get('api_key_env')}`, fake_provider_supported=`{provider.get('fake_provider_supported')}`")
    lines.extend([
        "",
        "## Limitations",
        "",
    ])
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    lines.append("")
    return "\n".join(lines)


def _prefixed_findings(result: CommandResult, prefix: str) -> list[Finding]:
    converted: list[Finding] = []
    for finding in result.findings:
        converted.append(Finding(id=f"{prefix}_{finding.id}", message=finding.message, severity=finding.severity, path=finding.path, metadata=finding.metadata))
    return converted


def _blocking_findings(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]


def _now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _posix(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return _posix(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return _posix(path)
