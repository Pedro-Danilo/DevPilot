from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.modeling import BudgetLedger, CapabilityMatrix, ModelAdapterRouter, ModelHealthService, ModelRouterConfig


def _workspace(root: Path, *, lmstudio_enabled: bool = False, endpoint: str = "http://localhost:9") -> Path:
    (root / ".devpilot").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='model-governance-fixture'\n", encoding="utf-8")
    (root / ".devpilot" / "providers.yaml").write_text(
        f'''schema_version: "2.0"
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
    enabled: false
    default_model: "fake-llama"
    endpoint: "http://localhost:11434"
    external_api: false
    requires_api_key: false
    estimated_cost_per_1k_tokens_usd: 0.0
    status: "implemented-initial"
  - id: "lmstudio"
    kind: "local"
    enabled: {str(lmstudio_enabled).lower()}
    default_model: "fake-openai-compatible"
    endpoint: "{endpoint}"
    external_api: false
    requires_api_key: false
    estimated_cost_per_1k_tokens_usd: 0.0
    status: "implemented-initial"
  - id: "openai"
    kind: "api"
    enabled: false
    default_model: "gpt-placeholder"
    endpoint: "https://api.openai.com"
    external_api: true
    requires_api_key: true
    api_key_env: "OPENAI_API_KEY"
    estimated_cost_per_1k_tokens_usd: 0.01
    status: "disabled"
''',
        encoding="utf-8",
    )
    (root / ".devpilot" / "providers.yaml.example").write_text((root / ".devpilot" / "providers.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    return root


def test_model_health_service_reports_all_providers_without_external_api(tmp_path: Path) -> None:
    root = _workspace(tmp_path)

    result = ModelHealthService(root, timeout_seconds=0.1).check_all()

    assert result.ok is True
    assert result.data["summary"]["providers_total"] == 4
    assert result.data["summary"]["external_api_used"] is False
    rows = {row["provider"]: row for row in result.data["providers"]}
    assert rows["mock"]["availability"] == "available"
    assert rows["openai"]["availability"] == "blocked"
    assert rows["lmstudio"]["availability"] in {"available", "unavailable"}


def test_capability_matrix_reports_static_provider_capabilities(tmp_path: Path) -> None:
    root = _workspace(tmp_path)

    result = CapabilityMatrix(root).build()

    assert result.ok is True
    rows = {row["provider"]: row for row in result.data["capabilities"]}
    assert rows["mock"]["supports"]["generate"] is True
    assert rows["ollama"]["localhost_only"] is True
    assert rows["lmstudio"]["supports"]["embed"] is True
    assert rows["openai"]["external_api"] is True
    assert rows["openai"]["supports"]["generate"] is False
    assert result.data["summary"]["external_api_enabled_total"] == 0


def test_budget_ledger_initial_status_is_zero(tmp_path: Path) -> None:
    root = _workspace(tmp_path)

    result = BudgetLedger(root).status()

    assert result.ok is True
    assert result.data["summary"]["events_total"] == 0
    assert result.data["summary"]["estimated_cost_total_usd"] == 0.0
    assert result.data["summary"]["external_cost_total_usd"] == 0.0


def test_budget_ledger_records_redacted_cost_event_from_cli(tmp_path: Path, monkeypatch, capsys) -> None:
    root = _workspace(tmp_path)
    monkeypatch.chdir(root)

    exit_code = cli.main(["model", "generate", "--provider", "mock", "--prompt", "safe governance prompt", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True

    status_exit = cli.main(["model", "budget", "status", "--json"])
    status = json.loads(capsys.readouterr().out)

    assert status_exit == 0
    assert status["ok"] is True
    assert status["data"]["summary"]["events_total"] >= 1
    serialized = json.dumps(status, ensure_ascii=False)
    assert "safe governance prompt" not in serialized
    assert "prompt_stored" in serialized
    assert "sk-" not in serialized


def test_configured_fallback_to_mock_when_local_provider_unavailable(tmp_path: Path) -> None:
    root = _workspace(tmp_path, lmstudio_enabled=True, endpoint="http://localhost:9")
    router = ModelAdapterRouter(root, config=ModelRouterConfig(local_timeout_seconds=0.1, fallback_to_mock_on_local_unavailable=True))

    result = router.generate(prompt="fallback smoke", provider="lmstudio")

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["fallback_applied"] is True
    assert result.data["summary"]["fallback_from_provider"] == "lmstudio"
    assert result.data["summary"]["fallback_to_provider"] == "mock"
    assert any(finding.id == "MODEL_FALLBACK_TO_MOCK_APPLIED" for finding in result.findings)
