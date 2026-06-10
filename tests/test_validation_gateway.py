from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.validation import ValidationGateway

ROOT = Path(__file__).resolve().parents[1]


def test_validation_gateway_docs_preserves_readiness_warnings() -> None:
    result = ValidationGateway(ROOT).validate_docs()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.command == "validate docs"
    assert result.data["summary"]["validations_total"] == 2
    assert result.data["summary"]["warnings_total"] >= 1
    assert any(finding.id == "ARTIFACT_RECOMMENDED_SECTION_MISSING" for finding in result.findings)
    assert any(finding.metadata.get("source_command") == "readiness-check" for finding in result.findings)


def test_validation_gateway_contracts_runs_schema_contract_group() -> None:
    result = ValidationGateway(ROOT).validate_contracts()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.command == "validate contracts"
    assert result.data["summary"]["validations_total"] >= 9
    assert result.data["summary"]["validations_failed"] == 0
    assert any(step["id"] == "schema-registry" for step in result.data["validations"])
    assert any(str(step["id"]).startswith("manifest:docs/functional_sprint_23_manifest.json") for step in result.data["validations"])


def test_validation_gateway_all_combines_docs_and_contracts() -> None:
    result = ValidationGateway(ROOT).validate_all()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.command == "validate all"
    assert result.data["summary"]["validations_total"] == 2
    assert result.data["summary"]["warnings_total"] >= 1
    assert result.data["summary"]["mutations_performed"] is False
    assert {step["id"] for step in result.data["validations"]} == {"docs", "contracts"}


def test_validate_docs_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["validate", "docs", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "validate docs"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["scope"] == "docs"


def test_validate_contracts_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["validate", "contracts", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "validate contracts"
    assert payload["data"]["summary"]["validations_failed"] == 0


def test_validate_all_cli_write_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["validate", "all", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "validate all"
    assert payload["data"]["reports"]["json"] == "outputs/reports/validate_all.json"
    assert (ROOT / payload["data"]["reports"]["json"]).exists()
    assert (ROOT / payload["data"]["reports"]["markdown"]).exists()
