from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.application.services import ApplicationService
from devpilot_core.modeling import LocalLlmProviderHealthReporter, ModelAdapterRouter, ModelRouterConfig
from devpilot_core.modeling.providers import ProviderRegistry

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_032_b_local_llm_provider_health_report_passes() -> None:
    result = LocalLlmProviderHealthReporter(ROOT).build()

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-032-B"
    assert summary["decision"] == "PASS"
    assert summary["required_local_providers_total"] == 2
    assert summary["required_local_providers_present_total"] == 2
    assert summary["local_enabled_total"] == 0
    assert summary["local_disabled_by_default_total"] == 2
    assert summary["non_localhost_endpoint_total"] == 0
    assert summary["local_requires_secret_total"] == 0
    assert summary["local_external_api_total"] == 0
    assert summary["external_api_used"] is False
    assert summary["real_server_required_for_tests"] is False
    assert summary["fake_provider_tests_supported"] is True
    assert summary["fallback_to_mock_allowed"] is True
    assert summary["fallback_to_mock_explicit"] is True
    assert summary["budget_ledger_zero_cost_supported"] is True


def test_post_h_032_b_provider_registry_defaults_stay_local_first() -> None:
    registry = ProviderRegistry.load(ROOT, prefer_example=True)
    assert registry.semantic_valid is True

    providers = registry.providers
    assert providers["mock"].enabled is True
    for provider_id in ("ollama", "lmstudio"):
        provider = providers[provider_id]
        assert provider.kind.value == "local"
        assert provider.enabled is False
        assert provider.external_api is False
        assert provider.requires_api_key is False
        assert provider.endpoint.startswith("http://localhost:")
        assert provider.estimated_cost_per_1k_tokens_usd == 0.0
    assert providers["openai"].enabled is False
    assert providers["gemini"].enabled is False


def test_post_h_032_b_schema_catalog_and_instances_are_registered() -> None:
    catalog = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    schemas = {item["schema_id"]: item for item in catalog["schemas"]}
    assert "SCHEMA-DEVPL-LOCAL-LLM-PROVIDER-HEALTH-REPORT-V1" in schemas
    assert schemas["SCHEMA-DEVPL-LOCAL-LLM-PROVIDER-HEALTH-REPORT-V1"]["contract"] == "LocalLlmProviderHealthReport"
    assert (ROOT / "docs/schemas/local_llm_provider_health_report.schema.json").is_file()
    assert (ROOT / ".devpilot/modeling/local_llm_provider_health_policy.json").is_file()

    result = LocalLlmProviderHealthReporter(ROOT).build()
    assert result.data["report"]["schema_id"] == "SCHEMA-DEVPL-LOCAL-LLM-PROVIDER-HEALTH-REPORT-V1"
    assert result.data["report"]["policy_path"] == ".devpilot/modeling/local_llm_provider_health_policy.json"


def test_post_h_032_b_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["model", "local-health", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["decision"] == "PASS"
    assert payload["data"]["summary"]["external_api_used"] is False
    assert payload["data"]["summary"]["network_used"] is False


def test_post_h_032_b_application_service_boundary() -> None:
    result = ApplicationService(ROOT).local_llm_provider_health()

    assert result.ok is True
    assert result.data["summary"]["decision"] == "PASS"
    assert result.data["summary"]["local_enabled_total"] == 0
    assert result.data["summary"]["external_api_used"] is False


def test_post_h_032_b_fallback_to_mock_is_explicit_for_enabled_unavailable_local_provider(tmp_path: Path) -> None:
    (tmp_path / ".devpilot").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/schemas").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='fallback-fixture'\n", encoding="utf-8")
    (tmp_path / ".devpilot/providers.yaml").write_text(
        '''schema_version: "2.0"
providers:
  - id: "mock"
    kind: "mock"
    enabled: true
    default_model: "mock-deterministic-v1"
    external_api: false
    requires_api_key: false
    estimated_cost_per_1k_tokens_usd: 0.0
    status: "implemented"
  - id: "ollama"
    kind: "local"
    enabled: true
    default_model: "fake-local"
    endpoint: "http://localhost:9"
    external_api: false
    requires_api_key: false
    estimated_cost_per_1k_tokens_usd: 0.0
    status: "implemented-initial"
''',
        encoding="utf-8",
    )
    router = ModelAdapterRouter(tmp_path, config=ModelRouterConfig(local_timeout_seconds=0.1, fallback_to_mock_on_local_unavailable=True))

    result = router.generate(prompt="fallback seguro", provider="ollama")

    assert result.ok is True
    assert result.data["summary"]["provider"] == "mock"
    assert result.data["summary"]["fallback_applied"] is True
    assert result.data["fallback"]["from_provider"] == "ollama"
    assert result.data["fallback"]["to_provider"] == "mock"
    assert result.data["fallback"]["external_api_used"] is False
    assert any(finding.id == "MODEL_FALLBACK_TO_MOCK_APPLIED" for finding in result.findings)
