from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.application import ApplicationService
from devpilot_core.cli_models import ExitCode
from devpilot_core.schemas import SchemaRegistry, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def test_schema_validator_validates_command_result_instance(tmp_path: Path) -> None:
    instance = _write_json(tmp_path / "schema_list_command_result.json", SchemaRegistry(ROOT).list().to_dict())

    result = SchemaValidator(ROOT).validate(
        schema="docs/schemas/command_result.schema.json",
        instance=instance,
    )

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["valid"] is True
    assert result.data["summary"]["errors_total"] == 0
    assert any(finding.id == "SCHEMA_VALIDATION_PASS" for finding in result.findings)


def test_schema_validator_detects_invalid_finding_instance(tmp_path: Path) -> None:
    invalid_finding = _write_json(
        tmp_path / "invalid_finding.json",
        {"id": "BROKEN", "severity": "not-a-valid-severity"},
    )

    result = SchemaValidator(ROOT).validate(
        schema="SCHEMA-DEVPL-FINDING-V1",
        instance=invalid_finding,
    )

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["errors_total"] >= 1
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)
    assert any("message" in finding.message or "not-a-valid-severity" in finding.message for finding in result.findings)


def test_schema_validator_validates_application_response_instance(tmp_path: Path) -> None:
    service = ApplicationService(ROOT)
    response = service.as_application_response(service.application_contract(), operation="app.contract")
    instance = _write_json(tmp_path / "application_response.json", response.to_dict())

    result = SchemaValidator(ROOT).validate(
        schema="ApplicationResponse",
        instance=instance,
    )

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["schema"].endswith("application_response.schema.json")


def test_schema_validator_reports_invalid_json_without_stacktrace(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text('{"command": "broken", ', encoding="utf-8")

    result = SchemaValidator(ROOT).validate(
        schema="docs/schemas/command_result.schema.json",
        instance=invalid,
    )

    assert result.ok is False
    assert result.exit_code == ExitCode.ERROR
    assert any(finding.id == "SCHEMA_INSTANCE_INVALID_JSON" for finding in result.findings)


def test_schema_validate_cli_json_is_parseable(monkeypatch, capsys, tmp_path: Path) -> None:
    monkeypatch.chdir(ROOT)
    instance = _write_json(tmp_path / "command_result.json", SchemaRegistry(ROOT).list().to_dict())

    exit_code = cli.main([
        "schema",
        "validate",
        "--schema",
        "CommandResult",
        "--instance",
        str(instance),
        "--json",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "schema validate"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["valid"] is True


def test_schema_validate_cli_invalid_instance_blocks(monkeypatch, capsys, tmp_path: Path) -> None:
    monkeypatch.chdir(ROOT)
    instance = _write_json(tmp_path / "invalid_command_result.json", {"command": "x", "ok": "yes"})

    exit_code = cli.main([
        "schema",
        "validate",
        "--schema",
        "docs/schemas/command_result.schema.json",
        "--instance",
        str(instance),
        "--json",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["ok"] is False
    assert any(finding["id"] == "SCHEMA_VALIDATION_ERROR" for finding in payload["findings"])


def test_schema_validate_cli_write_report(monkeypatch, capsys, tmp_path: Path) -> None:
    monkeypatch.chdir(ROOT)
    instance = _write_json(tmp_path / "application_response.json", ApplicationService(ROOT).as_application_response(ApplicationService(ROOT).application_contract()).to_dict())

    exit_code = cli.main([
        "schema",
        "validate",
        "--schema",
        "docs/schemas/application_response.schema.json",
        "--instance",
        str(instance),
        "--json",
        "--write-report",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    reports = payload["data"]["reports"]
    assert reports["json"] == "outputs/reports/schema_validation.json"
    assert reports["markdown"] == "outputs/reports/schema_validation.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()


def test_schema_validator_validates_evidence_report_output(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    cli.main(["schema", "list", "--json", "--write-report"])
    capsys.readouterr()

    result = SchemaValidator(ROOT).validate(
        schema="EvidenceReport",
        instance="outputs/reports/schema_list.json",
    )

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
