from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.modeling import ModelAdapterRouter, ProviderRegistry, parse_providers_yaml


def _minimal_workspace(root: Path) -> None:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / ".devpilot").mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='tmp-devpilot'\n", encoding="utf-8")
    (root / ".devpilot" / "providers.yaml.example").write_text(
        '''schema_version: "1.0"\nproviders:\n  - id: "mock"\n    kind: "mock"\n    enabled: true\n    default_model: "mock-deterministic-v1"\n    external_api: false\n    requires_api_key: false\n    estimated_cost_per_1k_tokens_usd: 0.0\n    status: "implemented"\n  - id: "openai"\n    kind: "api"\n    enabled: false\n    default_model: "gpt-placeholder"\n    external_api: true\n    requires_api_key: true\n    api_key_env: "OPENAI_API_KEY"\n    estimated_cost_per_1k_tokens_usd: 0.01\n    status: "disabled"\n''',
        encoding="utf-8",
    )


def test_provider_registry_loads_example_without_raw_secrets(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    registry = ProviderRegistry.load(tmp_path)

    result = registry.to_result()

    assert result.ok is True
    assert result.data["summary"]["providers_total"] == 2
    assert result.data["summary"]["api_providers_total"] == 1
    payload = json.dumps(result.to_dict())
    assert "sk-" not in payload
    assert "OPENAI_API_KEY" in payload


def test_mock_model_generate_is_deterministic_and_free(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    router = ModelAdapterRouter(tmp_path)

    first = router.generate(prompt="Diseñar agente documental local", provider="mock")
    second = router.generate(prompt="Diseñar agente documental local", provider="mock")

    assert first.ok is True
    assert second.ok is True
    assert first.data["result"]["content"] == second.data["result"]["content"]
    assert first.data["summary"]["external_api_used"] is False
    assert first.data["summary"]["cost_estimate_usd"] == 0.0


def test_mock_model_classify_uses_labels(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    router = ModelAdapterRouter(tmp_path)

    result = router.classify(text="Este cambio parece una feature documentada", labels=("bug", "feature"), provider="mock")

    assert result.ok is True
    assert result.data["result"]["label"] == "feature"


def test_mock_model_embed_is_stable(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    router = ModelAdapterRouter(tmp_path)

    first = router.embed(text="texto estable", provider="mock")
    second = router.embed(text="texto estable", provider="mock")

    assert first.ok is True
    assert first.data["result"]["embedding"] == second.data["result"]["embedding"]
    assert len(first.data["result"]["embedding"]) == 8


def test_model_router_blocks_secret_prompt(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    router = ModelAdapterRouter(tmp_path)

    result = router.generate(prompt="api_key=sk-1234567890abcdef", provider="mock")
    payload = json.dumps(result.to_dict())

    assert result.ok is False
    assert result.exit_code == 2
    assert result.findings[0].id == "SECRETGUARD_SECRET_DETECTED"
    assert "sk-1234567890abcdef" not in payload


def test_model_router_blocks_external_api_by_default(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    router = ModelAdapterRouter(tmp_path)

    result = router.generate(prompt="hello", provider="openai")

    assert result.ok is False
    assert result.exit_code == 2
    finding_ids = {finding.id for finding in result.findings}
    assert "COSTGUARD_EXTERNAL_API_BLOCKED" in finding_ids
    assert result.data["summary"]["external_api_used"] is False


def test_provider_parser_skips_raw_secret_provider(tmp_path: Path) -> None:
    config = tmp_path / "providers.yaml"
    config.write_text(
        '''schema_version: "1.0"\nproviders:\n  - id: "unsafe"\n    kind: "api"\n    enabled: true\n    default_model: "x"\n    api_key: "sk-1234567890abcdef"\n''',
        encoding="utf-8",
    )

    configs = parse_providers_yaml(config)

    assert configs == []


def test_model_cli_generate_classify_embed_and_reports_are_parseable(tmp_path: Path, monkeypatch, capsys) -> None:
    _minimal_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["model", "providers", "--json"])
    providers = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert providers["ok"] is True

    exit_code = cli.main(["model", "generate", "--prompt", "Crear propuesta local", "--json", "--write-report"])
    generate = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert generate["ok"] is True
    assert generate["data"]["reports"]["json"] == "outputs/reports/model_generate.json"

    exit_code = cli.main(["model", "classify", "--text", "bug detectado", "--labels", "bug,feature", "--json"])
    classify = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert classify["data"]["result"]["label"] == "bug"

    exit_code = cli.main(["model", "embed", "--text", "vector estable", "--json"])
    embed = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(embed["data"]["result"]["embedding"]) == 8
