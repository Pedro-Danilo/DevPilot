from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.schemas import BuiltinContractValidator, SchemaValidator
from devpilot_core.schemas.builtins import parse_provider_config_yaml, parse_workspace_project_yaml

ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def test_validate_miasi_structural_contracts_cli_pass(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["schema", "validate-miasi", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "schema validate-miasi"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["validations_total"] == 3
    assert payload["data"]["summary"]["validations_failed"] == 0


def test_validate_workspace_contract_cli_pass(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["schema", "validate-workspace", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "schema validate-workspace"
    assert payload["data"]["summary"]["source_format"] == "yaml"
    assert payload["data"]["summary"]["valid"] is True


def test_validate_providers_contract_cli_pass(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["schema", "validate-providers", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "schema validate-providers"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["valid"] is True


def test_validate_manifest_contracts_for_phase_a_manifests(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    for manifest in [
        "docs/functional_sprint_19_manifest.json",
        "docs/functional_sprint_20_manifest.json",
        "docs/functional_sprint_21_manifest.json",
        "docs/functional_sprint_22_manifest.json",
    ]:
        exit_code = cli.main(["schema", "validate-manifest", manifest, "--json"])
        payload = json.loads(capsys.readouterr().out)
        assert exit_code == 0, manifest
        assert payload["ok"] is True, manifest
        assert payload["data"]["summary"]["valid"] is True, manifest


def test_invalid_miasi_tool_registry_is_blocked(tmp_path: Path) -> None:
    invalid = {
        "schema_version": "1.0",
        "source_document": "docs/06_miasi/tool_registry.md",
        "created_by": "FUNC-SPRINT-11",
        "description": "Broken registry for contract test.",
        "tools": [
            {
                "name": "missing_tool_id",
                "phase": "MVP",
                "side_effect": "read",
                "risk_level": "low",
                "status": "implemented",
                "requires_approval": False,
                "policy_rule_ids": ["DOC_READ_ALLOW"],
            }
        ],
    }
    path = _write_json(tmp_path / "broken_tool_registry.json", invalid)

    result = SchemaValidator(ROOT).validate(schema="MiasiToolRegistry", instance=path)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)


def test_provider_config_with_raw_secret_is_blocked(tmp_path: Path) -> None:
    unsafe = tmp_path / "providers.yaml.example"
    unsafe.write_text(
        """schema_version: "1.0"
providers:
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
    notes:
      - "Unsafe fixture."
""",
        encoding="utf-8",
    )
    payload = parse_provider_config_yaml(unsafe)

    result = SchemaValidator(ROOT).validate_payload(schema="ProviderConfig", payload=payload, instance_label=str(unsafe))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)


def test_workspace_parser_exposes_expected_contract_shape() -> None:
    payload = parse_workspace_project_yaml(ROOT / ".devpilot/project.yaml")

    assert payload["schema_version"] == "1.0"
    assert payload["project"]["id"] == "devpilot-local"
    assert payload["miasi"]["required"] is True
    assert payload["runtime"]["dry_run_default"] is True


def test_builtin_contract_validator_write_report_paths(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["schema", "validate-miasi", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["data"]["reports"]["json"] == "outputs/reports/schema_validate_miasi.json"
    assert (ROOT / payload["data"]["reports"]["json"]).exists()
    assert (ROOT / payload["data"]["reports"]["markdown"]).exists()
