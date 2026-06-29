from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli import main
from devpilot_core.cli_models import ExitCode
from devpilot_core.interfaces.api import UiApiIndustrialShellGate, UiApiIndustrialShellGateOptions
from devpilot_core.quality import QualityGate, QualityGateOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_014_e_ui_api_shell_gate_passes_and_writes_schema_valid_report() -> None:
    result = UiApiIndustrialShellGate(ROOT, UiApiIndustrialShellGateOptions(write_report=True)).run()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-014-E"
    assert summary["quality_gate_subgate"] == "ui-api-industrial-shell"
    assert summary["api_registry_ok"] is True
    assert summary["ui_registry_ok"] is True
    assert summary["ui_smoke_ok"] is True
    assert summary["documentation_ok"] is True
    assert summary["registries_synchronized"] is True
    assert summary["api_routes_total"] == 33
    assert summary["ui_routes_total"] == 5
    assert summary["no_go_violations_total"] == 0
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["remote_execution_enabled"] is False
    assert summary["connector_write_enabled"] is False
    assert summary["plugin_execution_enabled"] is False
    assert result.data["reports"]["json"] == "outputs/reports/ui_api_shell_report.json"

    report_path = ROOT / result.data["reports"]["json"]
    assert report_path.exists()
    schema_result = SchemaValidator(ROOT).validate(schema="UiApiShellReport", instance=result.data["reports"]["json"])
    assert schema_result.ok, schema_result.to_dict()


def test_post_h_014_e_quality_gate_hardening_includes_ui_api_shell_subgate() -> None:
    hardening_gate = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))
    hardening_subgates = hardening_gate._subgates()
    hardening_ids = [subgate.id for subgate in hardening_subgates]
    assert "ui-api-industrial-shell" in hardening_ids

    industrial_gate = QualityGate(ROOT, options=QualityGateOptions(profile="industrial"))
    industrial_ids = [subgate.id for subgate in industrial_gate._subgates()]
    assert "ui-api-industrial-shell" in industrial_ids

    ui_api_subgate = next(
        subgate for subgate in hardening_subgates if subgate.id == "ui-api-industrial-shell"
    )
    assert ui_api_subgate.critical is True

    result = ui_api_subgate.runner()
    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["quality_gate_subgate"] == "ui-api-industrial-shell"
    assert result.data["summary"]["no_go_violations_total"] == 0


def test_post_h_014_e_api_shell_gate_cli_generates_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = main(["api", "shell-gate", "--json", "--write-report", "--no-ui-smoke"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["command"] == "quality ui-api-industrial-shell"
    assert payload["data"]["summary"]["created_by"] == "POST-H-014-E"
    assert payload["data"]["reports"]["json"] == "outputs/reports/ui_api_shell_report.json"
    assert (ROOT / "outputs/reports/ui_api_shell_report.json").exists()


def test_post_h_014_e_contract_docs_and_registries_are_synchronized() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    ui_runbook = (ROOT / "docs/05_operations/ui_api_local_runbook.md").read_text(encoding="utf-8")
    interface_doc = (ROOT / "docs/07_interfaces/ui_api_industrial_shell.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-014_ui_api_industrial_shell.md").read_text(encoding="utf-8")
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")
    catalog = (ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8")

    assert "POST-H-014-E — Quality gate UI/API industrial shell" in readme
    assert "POST-H-014-E — Quality gate UI/API industrial shell" in runbook
    assert "ui-api-industrial-shell" in ui_runbook
    assert "POST-H-014-E" in interface_doc
    assert 'current_micro_sprint: "POST-H-014-E"' in backlog
    assert 'implementation_status: "closed"' in backlog
    assert "post-h-014-ui-api-shell-quality-gate" in tcr_v1
    assert "post-h-014-ui-api-shell-quality-gate" in tcr_v2
    assert "SCHEMA-DEVPL-UI-API-SHELL-REPORT-V1" in catalog
