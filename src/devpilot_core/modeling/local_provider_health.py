from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.modeling.contracts import ModelProviderKind
from devpilot_core.modeling.providers import ProviderRegistry
from devpilot_core.schemas import SchemaValidator

POST_H_032_B_CREATED_BY = "POST-H-032-B"
LOCAL_LLM_PROVIDER_HEALTH_COMMAND = "model local-health"
LOCAL_LLM_PROVIDER_HEALTH_SCHEMA_ID = "SCHEMA-DEVPL-LOCAL-LLM-PROVIDER-HEALTH-REPORT-V1"
LOCAL_LLM_PROVIDER_HEALTH_CONTRACT = "LocalLlmProviderHealthReport"
DEFAULT_POLICY_PATH = Path(".devpilot/modeling/local_llm_provider_health_policy.json")
DEFAULT_OUTPUT_JSON = Path("outputs/reports/local_llm_provider_health_report.json")
DEFAULT_OUTPUT_MARKDOWN = Path("outputs/reports/local_llm_provider_health_report.md")
LOCAL_PROVIDER_IDS = ("ollama", "lmstudio")
LOCALHOST_NAMES = {"localhost", "127.0.0.1", "::1"}


@dataclass(frozen=True)
class LocalLlmProviderHealthOptions:
    policy_path: str | Path = DEFAULT_POLICY_PATH
    output_json: str | Path = DEFAULT_OUTPUT_JSON
    output_markdown: str | Path = DEFAULT_OUTPUT_MARKDOWN
    timeout_seconds: float = 0.2
    probe_enabled_local: bool = False
    write_report: bool = False


class LocalLlmProviderHealthReporter:
    """Build the POST-H-032-B local LLM provider hardening report.

    The reporter validates source-controlled provider configuration and the
    POST-H-032-B policy for Ollama/LM Studio without requiring real model
    servers. By default it does not perform network probes. If an operator opts
    into probes, only enabled localhost providers are probed through the existing
    governed ModelAdapterRouter health boundary.
    """

    def __init__(self, root: Path, options: LocalLlmProviderHealthOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or LocalLlmProviderHealthOptions()
        self.policy_path = Path(self.options.policy_path)

    def build(self) -> CommandResult:
        findings: list[Finding] = []
        policy = self._load_policy(findings)
        registry = ProviderRegistry.load(self.root, prefer_example=True)
        findings.extend(registry.validation_findings)
        required_provider_ids = tuple(str(pid) for pid in policy.get("provider_ids", LOCAL_PROVIDER_IDS)) or LOCAL_PROVIDER_IDS
        providers = [self._provider_row(provider_id, registry, policy, findings) for provider_id in required_provider_ids]
        blocking = _blocking_findings(findings)
        summary = self._summary(policy, registry, providers, findings)
        status = "implemented-initial" if not blocking else "blocked"
        report = {
            "schema_version": "1.0",
            "schema_id": LOCAL_LLM_PROVIDER_HEALTH_SCHEMA_ID,
            "report_id": "devpilot-local-llm-provider-health-report",
            "created_by": POST_H_032_B_CREATED_BY,
            "status": status,
            "generated_at_utc": _now_utc(),
            "policy_path": _posix(self.policy_path),
            "provider_registry_path": registry.source_path,
            "summary": summary,
            "providers": providers,
            "fallback": {
                "provider": str(policy.get("mock_fallback_provider") or "mock"),
                "allowed": bool(policy.get("defaults", {}).get("fallback_to_mock_on_unavailable_allowed", True)),
                "explicit_required": bool(policy.get("defaults", {}).get("fallback_must_be_explicit", True)),
                "silent_fallback_allowed": False,
                "finding_id": "MODEL_FALLBACK_TO_MOCK_APPLIED",
            },
            "budget": {
                "ledger_supported": True,
                "local_monetary_cost_usd": 0.0,
                "external_cost_allowed": False,
                "budget_ledger_component": "devpilot_core.modeling.budget.BudgetLedger",
                "local_providers_have_zero_unit_cost": all(float(row.get("estimated_cost_per_1k_tokens_usd") or 0.0) == 0.0 for row in providers),
            },
            "safety": {
                "local_first": True,
                "read_only": not self.options.write_report,
                "dry_run": True,
                "models_called": False,
                "local_servers_required": False,
                "external_api_used": False,
                "network_used": bool(summary["network_used"]),
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "secrets_read": False,
                "raw_prompts_stored": False,
                "raw_outputs_stored": False,
                "source_mutations_performed": False,
                "llm_judge_used": False,
            },
            "findings": [finding.to_dict() for finding in findings] or [Finding("LOCAL_LLM_PROVIDER_HEALTH_PASS", "Local LLM provider hardening report passed.", Severity.INFO, metadata=summary).to_dict()],
            "notes": [
                "POST-H-032-B hardens Ollama/LM Studio provider governance; it does not require real local model servers in tests.",
                "Local providers remain disabled by default in source-controlled provider metadata.",
                "Fallback to mock is allowed only when explicit and auditable; silent success is not allowed.",
            ],
            "limitations": list(policy.get("limitations") or [
                "This is implemented-initial local provider hardening evidence, not a guarantee that a local model server is installed.",
                "Actual model generation still requires explicit local operator opt-in and existing ModelAdapterRouter guards.",
            ]),
        }
        schema_result = SchemaValidator(self.root).validate_payload(
            schema=LOCAL_LLM_PROVIDER_HEALTH_CONTRACT,
            payload=report,
            instance_label="in-memory-local-llm-provider-health-report",
        )
        if not schema_result.ok:
            findings.extend(_prefixed_findings(schema_result, "LOCAL_LLM_PROVIDER_HEALTH_SCHEMA"))
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
            reports = self._write_reports(report)
            report["summary"]["reports_written"] = True
            report["safety"]["read_only"] = False
        ok = not _blocking_findings(findings)
        return CommandResult(
            command=LOCAL_LLM_PROVIDER_HEALTH_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else exit_code_for_findings(_blocking_findings(findings), default_ok=False),
            message="Local LLM provider health hardening passed." if ok else "Local LLM provider health hardening has blocking findings.",
            data={"summary": report["summary"], "report": report, "policy": policy, "reports": reports},
            findings=findings or [Finding("LOCAL_LLM_PROVIDER_HEALTH_PASS", "Local LLM provider hardening report passed.", Severity.INFO, metadata=report["summary"])],
        )

    def _provider_row(self, provider_id: str, registry: ProviderRegistry, policy: dict[str, Any], findings: list[Finding]) -> dict[str, Any]:
        config = registry.get(provider_id)
        policy_by_id = {str(item.get("provider_id")): item for item in policy.get("providers", []) if isinstance(item, dict)}
        provider_policy = policy_by_id.get(provider_id, {})
        if config is None:
            findings.append(Finding("LOCAL_LLM_PROVIDER_MISSING", f"Required local provider is missing: {provider_id}", Severity.BLOCK, path=registry.source_path, metadata={"provider": provider_id}))
            return {
                "provider_id": provider_id,
                "kind": "local",
                "registered": False,
                "enabled": False,
                "disabled_by_default": True,
                "endpoint": None,
                "localhost_only": False,
                "requires_api_key": False,
                "external_api": False,
                "estimated_cost_per_1k_tokens_usd": 0.0,
                "availability": "missing",
                "health_check_mode": "missing-provider",
                "fake_test_compatible": True,
                "fallback_provider": "mock",
                "budget_ledger_cost_usd": 0.0,
                "blocking_findings": ["LOCAL_LLM_PROVIDER_MISSING"],
            }
        blocking_ids: list[str] = []
        endpoint = config.endpoint or provider_policy.get("default_endpoint")
        localhost_only = _is_local_http_endpoint(str(endpoint or ""))
        if config.kind != ModelProviderKind.LOCAL:
            blocking_ids.append("LOCAL_LLM_PROVIDER_KIND_INVALID")
            findings.append(Finding("LOCAL_LLM_PROVIDER_KIND_INVALID", f"Provider '{provider_id}' must be kind=local.", Severity.BLOCK, path=registry.source_path, metadata={"provider": provider_id}))
        if config.enabled:
            blocking_ids.append("LOCAL_LLM_PROVIDER_ENABLED_BY_DEFAULT")
            findings.append(Finding("LOCAL_LLM_PROVIDER_ENABLED_BY_DEFAULT", f"Provider '{provider_id}' must remain disabled by default in source-controlled metadata.", Severity.BLOCK, path=registry.source_path, metadata={"provider": provider_id}))
        if not localhost_only:
            blocking_ids.append("LOCAL_LLM_PROVIDER_NON_LOCALHOST_ENDPOINT")
            findings.append(Finding("LOCAL_LLM_PROVIDER_NON_LOCALHOST_ENDPOINT", f"Provider '{provider_id}' endpoint must be localhost-only HTTP.", Severity.BLOCK, path=registry.source_path, metadata={"provider": provider_id, "endpoint": endpoint}))
        if config.requires_api_key or config.external_api:
            blocking_ids.append("LOCAL_LLM_PROVIDER_SECRET_OR_EXTERNAL")
            findings.append(Finding("LOCAL_LLM_PROVIDER_SECRET_OR_EXTERNAL", f"Provider '{provider_id}' must not require secrets or external API.", Severity.BLOCK, path=registry.source_path, metadata={"provider": provider_id}))
        availability = "misconfigured" if blocking_ids else "disabled"
        health_check_mode = "blocked-misconfigured" if blocking_ids else "static-disabled"
        if config.enabled and not blocking_ids and self.options.probe_enabled_local:
            health_result = self._probe_provider(provider_id)
            summary = dict((health_result.data or {}).get("summary") or {})
            availability = str(summary.get("availability") or "unavailable")
            health_check_mode = "bounded-local-probe"
        return {
            "provider_id": provider_id,
            "kind": "local",
            "registered": True,
            "enabled": bool(config.enabled),
            "disabled_by_default": not bool(config.enabled),
            "endpoint": endpoint,
            "localhost_only": localhost_only,
            "requires_api_key": bool(config.requires_api_key),
            "external_api": bool(config.external_api),
            "estimated_cost_per_1k_tokens_usd": float(config.estimated_cost_per_1k_tokens_usd or 0.0),
            "availability": availability,
            "health_check_mode": health_check_mode,
            "fake_test_compatible": bool(provider_policy.get("tests_must_use_fake_server_or_disabled_config", True)),
            "fallback_provider": str(provider_policy.get("fallback_provider") or "mock"),
            "budget_ledger_cost_usd": 0.0,
            "status": config.status,
            "model": config.default_model,
            "blocking_findings": blocking_ids,
            "notes": [
                "Source-controlled defaults are validated only; real local servers are not required.",
                "Model calls remain governed by ModelAdapterRouter, SecretGuard, CostGuard and explicit provider enablement.",
            ],
        }

    def _probe_provider(self, provider_id: str) -> CommandResult:
        from devpilot_core.modeling.router import ModelAdapterRouter, ModelRouterConfig

        return ModelAdapterRouter(self.root, config=ModelRouterConfig(local_timeout_seconds=self.options.timeout_seconds, budget_ledger_enabled=False)).health(provider=provider_id)

    def _summary(self, policy: dict[str, Any], registry: ProviderRegistry, providers: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        defaults = policy.get("defaults", {}) if isinstance(policy.get("defaults"), dict) else {}
        blocking = _blocking_findings(findings)
        return {
            "created_by": POST_H_032_B_CREATED_BY,
            "status": "implemented-initial" if not blocking else "blocked",
            "decision": "PASS" if not blocking else "BLOCK",
            "providers_total": len(registry.providers),
            "local_providers_total": sum(1 for provider in registry.providers.values() if provider.kind == ModelProviderKind.LOCAL),
            "required_local_providers_total": len(providers),
            "required_local_providers_present_total": sum(1 for row in providers if row.get("registered")),
            "local_enabled_total": sum(1 for row in providers if row.get("enabled") is True),
            "local_disabled_by_default_total": sum(1 for row in providers if row.get("disabled_by_default") is True),
            "localhost_only_total": sum(1 for row in providers if row.get("localhost_only") is True),
            "non_localhost_endpoint_total": sum(1 for row in providers if row.get("localhost_only") is not True),
            "local_requires_secret_total": sum(1 for row in providers if row.get("requires_api_key") is True),
            "local_external_api_total": sum(1 for row in providers if row.get("external_api") is True),
            "external_api_used": False,
            "network_used": bool(self.options.probe_enabled_local and any(row.get("enabled") for row in providers)),
            "real_server_required_for_tests": bool(defaults.get("real_server_required_for_tests", False)),
            "fake_provider_tests_supported": bool(defaults.get("tests_use_fake_or_disabled_local_provider", True)),
            "fallback_to_mock_allowed": bool(defaults.get("fallback_to_mock_on_unavailable_allowed", True)),
            "fallback_to_mock_explicit": bool(defaults.get("fallback_must_be_explicit", True)),
            "budget_ledger_zero_cost_supported": bool(defaults.get("budget_ledger_zero_cost_required", True)) and all(float(row.get("estimated_cost_per_1k_tokens_usd") or 0.0) == 0.0 for row in providers),
            "blocking_findings_total": len(blocking),
            "findings_total": len(findings),
            "schema_valid": False,
            "reports_written": False,
            "preliminary": True,
        }

    def _load_policy(self, findings: list[Finding]) -> dict[str, Any]:
        try:
            return json.loads((self.root / self.policy_path).read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(Finding("LOCAL_LLM_PROVIDER_HEALTH_POLICY_LOAD_ERROR", f"Could not load local LLM provider health policy: {exc}", Severity.BLOCK, path=_posix(self.policy_path)))
            return {}

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        output_json = _safe_output_path(self.root, self.options.output_json)
        output_markdown = _safe_output_path(self.root, self.options.output_markdown)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_markdown.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(_json_dumps(report) + "\n", encoding="utf-8")
        output_markdown.write_text(render_local_llm_provider_health_markdown(report), encoding="utf-8")
        return {"json": _relative(output_json, self.root), "markdown": _relative(output_markdown, self.root)}


def render_local_llm_provider_health_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# POST-H-032-B — Local LLM provider hardening",
        "",
        f"- Decision: `{summary.get('decision')}`",
        f"- Required local providers: `{summary.get('required_local_providers_present_total')}/{summary.get('required_local_providers_total')}`",
        f"- Local providers enabled by default: `{summary.get('local_enabled_total')}`",
        f"- Non-localhost endpoints: `{summary.get('non_localhost_endpoint_total')}`",
        f"- Local providers requiring secrets: `{summary.get('local_requires_secret_total')}`",
        f"- External API used: `{summary.get('external_api_used')}`",
        f"- Real server required for tests: `{summary.get('real_server_required_for_tests')}`",
        f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
        "",
        "## Providers",
        "",
        "| Provider | Enabled | Endpoint | Localhost only | Availability | Fallback |",
        "| --- | ---: | --- | ---: | --- | --- |",
    ]
    for provider in report.get("providers", []):
        lines.append(
            f"| `{provider.get('provider_id')}` | `{provider.get('enabled')}` | `{provider.get('endpoint')}` | `{provider.get('localhost_only')}` | `{provider.get('availability')}` | `{provider.get('fallback_provider')}` |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "POST-H-032-B hardens local provider governance only. Ollama and LM Studio remain optional, disabled by default and bounded to localhost. Tests must use fake servers, disabled config or monkeypatching; real local model servers are not required.",
        "",
    ])
    return "\n".join(lines)


def _is_local_http_endpoint(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    return parsed.scheme == "http" and (parsed.hostname or "").lower() in LOCALHOST_NAMES


def _prefixed_findings(result: CommandResult, prefix: str) -> list[Finding]:
    return [
        Finding(id=f"{prefix}_{finding.id}", message=finding.message, severity=finding.severity, path=finding.path, metadata=finding.metadata)
        for finding in result.findings
    ]


def _blocking_findings(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]


def _safe_output_path(root: Path, path: str | Path) -> Path:
    rel = Path(path)
    if rel.is_absolute() or not str(rel).replace("\\", "/").startswith("outputs/"):
        raise ValueError(f"Output path must be relative and under outputs/: {path}")
    resolved = (root / rel).resolve()
    if root.resolve() not in resolved.parents and resolved != root.resolve():
        raise ValueError(f"Output path escapes workspace: {path}")
    return resolved


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _posix(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
