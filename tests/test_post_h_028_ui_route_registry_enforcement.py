from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.interfaces.api import UiApiLocalHardeningGate, UiRouteEnforcementOptions, UiRouteEnforcementRunner
from devpilot_core.quality.gate import QualityGate, QualityGateOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "ui" / "web"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _read_web(path: str) -> str:
    return (WEB / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_ui_route_enforcement_passes_baseline_without_source_mutations() -> None:
    result = UiRouteEnforcementRunner(ROOT).run()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["decision"] == "PASS"
    assert summary["ui_route_registry_enforcement_passed"] is True
    assert summary["critical_routes_registered_total"] == summary["critical_routes_total"]
    assert summary["critical_view_files_registered_total"] == summary["critical_view_files_total"]
    assert summary["unregistered_api_refs_total"] == 0
    assert summary["missing_state_contracts_total"] == 0
    assert summary["no_go_violations_total"] == 0
    assert summary["forbidden_ui_actions_total"] == 0
    assert summary["filesystem_core_imports_total"] == 0
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["source_mutations_performed"] is False


def test_ui_route_enforcement_writes_schema_valid_report_under_explicit_output(tmp_path: Path) -> None:
    output_json = tmp_path / "ui_route_enforcement_report.json"
    output_markdown = tmp_path / "ui_route_enforcement_report.md"
    result = UiRouteEnforcementRunner(
        ROOT,
        UiRouteEnforcementOptions(write_report=True, output_json=output_json, output_markdown=output_markdown),
    ).run()

    assert result.ok is True, result.to_dict()
    assert output_json.exists()
    assert output_markdown.exists()
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_id"] == "SCHEMA-DEVPL-UI-ROUTE-ENFORCEMENT-REPORT-V1"
    assert payload["created_by"] == "POST-H-028-E"
    assert payload["summary"]["reports_written"] is True
    schema = SchemaValidator(ROOT).validate(schema="UiRouteEnforcementReport", instance=output_json)
    assert schema.ok is True, schema.to_dict()


def test_ui_route_enforcement_cli_json_and_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    report = ROOT / "outputs" / "reports" / "ui_route_enforcement_report.json"
    if report.exists():
        report.unlink()

    exit_code = cli.main(["api", "ui-route-enforcement", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "api ui-route-enforcement"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["decision"] == "PASS"
    assert payload["data"]["reports"]["json"] == "outputs/reports/ui_route_enforcement_report.json"
    assert report.exists()


def test_ui_route_enforcement_quality_gates_are_registered_without_running_full_gate() -> None:
    gate = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))
    subgate_ids = {subgate.id for subgate in gate._subgates()}

    assert "api-contract-drift-guard" in subgate_ids
    assert "local-api-security-hardening" in subgate_ids
    assert "ui-visual-smoke" in subgate_ids
    assert "operator-flow-smoke" in subgate_ids
    assert "ui-route-enforcement" in subgate_ids
    assert "ui-api-local-hardening" in subgate_ids

    route_subgate = {subgate.id: subgate for subgate in gate._subgates()}["ui-route-enforcement"].runner()
    assert route_subgate.ok is True, route_subgate.to_dict()

    aggregate = UiApiLocalHardeningGate(ROOT).run()
    assert aggregate.ok is True, aggregate.to_dict()
    assert aggregate.data["summary"]["quality_gate_subgate"] == "ui-api-local-hardening"
    assert aggregate.data["summary"]["ui_api_local_hardening_passed"] is True


def test_ui_route_enforcement_schema_registries_and_project_state_are_synchronized() -> None:
    schema_catalog = _json("docs/schemas/schema_catalog.json")
    source_registry = _json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = _read(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _read(".devpilot/testing/test_contract_registry_v2.json")
    state = _json(".devpilot/project_state.json")

    assert any(entry["schema_id"] == "SCHEMA-DEVPL-UI-ROUTE-ENFORCEMENT-REPORT-V1" for entry in schema_catalog["schemas"])
    assert any(doc["doc_id"] == "POST-H-028-E-UI-ROUTE-ENFORCEMENT-REPORT" for doc in source_registry["documents"])
    assert "post-h-028-ui-route-registry-enforcement" in tcr_v1
    assert "post-h-028-ui-route-registry-enforcement" in tcr_v2
    assert state["last_completed_sprint"] == "POST-H-028"
    assert state["next_sprint"] == "POST-H-029"
    assert state["current_micro_sprint"] == "POST-H-028-E"
    assert state["next_micro_sprint"] == "POST-H-029"
    assert state["post_h_028_status"] == "closed/ui-api-local-hardening"
    assert state["post_h_028_ui_route_enforcement_available"] is True
    assert state["post_h_028_ui_api_local_hardening_quality_gate_enabled"] is True
    assert state["post_h_028_closed"] is True


def test_ui_registry_shared_view_bindings_and_web_scripts_are_synchronized() -> None:
    registry = _json(".devpilot/interfaces/ui_route_contract_registry.json")
    package = json.loads(_read_web("package.json"))
    route_script = _read_web("scripts/route-enforcement-smoke.mjs")
    operator_script = _read_web("scripts/operator-flow-smoke.mjs")

    routes = {route["route_id"]: route for route in registry["routes"]}
    assert "api.traces.list" in routes["ui.reports"]["allowed_api_routes"]
    assert "api.reports.list" in routes["ui.traces"]["allowed_api_routes"]
    assert package["scripts"]["test:route-enforcement"] == "node scripts/route-enforcement-smoke.mjs"
    assert package["devpilot"]["postH028E"] is True
    assert package["devpilot"]["uiRouteEnforcement"] is True
    assert "DEVPL WEB UI ROUTE ENFORCEMENT SMOKE TEST: PASS" in route_script
    assert "fileURLToPath(import.meta.url)" in operator_script
    assert "new URL('..', import.meta.url).pathname" not in operator_script


def test_ui_route_enforcement_npm_script_is_explicit_opt_in() -> None:
    if os.environ.get("DEVPILOT_RUN_WEB_UI_ROUTE_ENFORCEMENT_TEST", "").strip().lower() not in {"1", "true", "yes", "on"}:
        return
    npm = shutil.which("npm.cmd") or shutil.which("npm.exe") or shutil.which("npm")
    assert npm is not None, "DEVPILOT_RUN_WEB_UI_ROUTE_ENFORCEMENT_TEST enabled, but npm was not found."
    completed = subprocess.run(
        [npm, "run", "test:route-enforcement"],
        cwd=WEB,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "DEVPL WEB UI ROUTE ENFORCEMENT SMOKE TEST: PASS" in completed.stdout
