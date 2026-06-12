from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.modeling import ModelAdapterRouter, ProviderRegistry
from devpilot_core.schemas import SchemaValidator
from devpilot_core.schemas.builtins import parse_provider_config_yaml

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_provider_example_validates_with_dedicated_and_generic_cli(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    dedicated_exit = cli.main(["schema", "validate-providers", "--json"])
    dedicated = json.loads(capsys.readouterr().out)
    assert dedicated_exit == 0
    assert dedicated["ok"] is True
    assert dedicated["data"]["summary"]["valid"] is True

    generic_exit = cli.main([
        "schema",
        "validate",
        "--schema",
        "docs/schemas/provider_config.schema.json",
        "--instance",
        ".devpilot/providers.yaml.example",
        "--json",
    ])
    generic = json.loads(capsys.readouterr().out)
    assert generic_exit == 0
    assert generic["ok"] is True
    assert generic["data"]["summary"]["valid"] is True


def test_provider_registry_keeps_safe_defaults_and_external_disabled() -> None:
    registry = ProviderRegistry.load(ROOT)
    result = registry.to_result()

    assert result.ok is True
    assert result.data["summary"]["schema_version"] == "2.0"
    assert result.data["summary"]["semantic_valid"] is True
    assert result.data["summary"]["mock_enabled"] is True
    assert result.data["summary"]["external_api_enabled_total"] == 0

    providers = {provider.provider_id: provider for provider in registry.providers.values()}
    assert providers["mock"].enabled is True
    assert providers["ollama"].kind.value == "local"
    assert providers["ollama"].enabled is False
    assert providers["lmstudio"].endpoint == "http://localhost:1234"
    assert providers["openai"].enabled is False
    assert providers["openai"].external_api is True
    assert providers["openai"].status == "disabled"


def test_mock_generate_classify_embed_still_pass_without_network(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    for args in [
        ["model", "generate", "--provider", "mock", "--prompt", "hello", "--json"],
        ["model", "classify", "--provider", "mock", "--text", "document", "--labels", "docs,code", "--json"],
        ["model", "embed", "--provider", "mock", "--text", "DevPilot", "--json"],
    ]:
        exit_code = cli.main(args)
        payload = json.loads(capsys.readouterr().out)
        assert exit_code == 0, args
        assert payload["ok"] is True, args
        assert payload["data"]["summary"]["provider"] == "mock"
        assert payload["data"]["summary"]["external_api_used"] is False


def test_provider_config_raw_secret_is_schema_blocked(tmp_path: Path) -> None:
    unsafe = _write(
        tmp_path / "providers.yaml.example",
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
  - id: "unsafe"
    kind: "api"
    enabled: false
    default_model: "unsafe-model"
    endpoint: "https://example.invalid"
    external_api: true
    requires_api_key: true
    api_key_env: "UNSAFE_API_KEY"
    api_key: "sk-real-secret-should-not-be-here"
    estimated_cost_per_1k_tokens_usd: 0.1
    status: "disabled"
''',
    )
    payload = parse_provider_config_yaml(unsafe)
    result = SchemaValidator(ROOT).validate_payload(schema="ProviderConfig", payload=payload, instance_label=str(unsafe))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)


def test_local_provider_remote_endpoint_is_schema_blocked(tmp_path: Path) -> None:
    unsafe = _write(
        tmp_path / "providers.yaml.example",
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
    enabled: false
    default_model: "qwen"
    endpoint: "http://192.168.1.10:11434"
    external_api: false
    requires_api_key: false
    estimated_cost_per_1k_tokens_usd: 0.0
    status: "planned"
''',
    )
    payload = parse_provider_config_yaml(unsafe)
    result = SchemaValidator(ROOT).validate_payload(schema="ProviderConfig", payload=payload, instance_label=str(unsafe))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)


def test_external_provider_enabled_is_schema_blocked(tmp_path: Path) -> None:
    unsafe = _write(
        tmp_path / "providers.yaml.example",
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
  - id: "openai"
    kind: "api"
    enabled: true
    default_model: "gpt-placeholder"
    endpoint: "https://api.openai.com"
    external_api: true
    requires_api_key: true
    api_key_env: "OPENAI_API_KEY"
    estimated_cost_per_1k_tokens_usd: 0.01
    status: "disabled"
''',
    )
    payload = parse_provider_config_yaml(unsafe)
    result = SchemaValidator(ROOT).validate_payload(schema="ProviderConfig", payload=payload, instance_label=str(unsafe))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)


def test_router_blocks_semantically_invalid_local_provider_config(tmp_path: Path) -> None:
    root = tmp_path
    (root / ".devpilot").mkdir()
    _write(root / "pyproject.toml", "[project]\nname='fixture'\n")
    _write(root / "docs/.keep", "")
    _write(
        root / ".devpilot/providers.yaml",
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
    enabled: false
    default_model: "qwen"
    endpoint: "http://example.com:11434"
    external_api: false
    requires_api_key: false
    estimated_cost_per_1k_tokens_usd: 0.0
    status: "planned"
''',
    )

    result = ModelAdapterRouter(root).generate(prompt="hello", provider="mock")

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "MODEL_PROVIDER_LOCAL_ENDPOINT_NOT_LOCAL_BLOCKED" for finding in result.findings)
