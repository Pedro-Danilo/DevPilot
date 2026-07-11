from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.interfaces.api import OperatorFlowSmokeOptions, OperatorFlowSmokeRunner
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


def test_operator_flow_smoke_passes_baseline_without_source_mutations() -> None:
    result = OperatorFlowSmokeRunner(ROOT).run()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["decision"] == "PASS"
    assert summary["operator_flow_smoke_passed"] is True
    assert summary["minimal_flows_passed"] == summary["minimal_flows_total"]
    assert summary["api_down_visible"] is True
    assert summary["token_missing_blocked"] is True
    assert summary["token_invalid_blocked"] is True
    assert summary["token_missing_visible"] is True
    assert summary["token_invalid_visible"] is True
    assert summary["raw_stack_traces_visible"] is False
    assert summary["reports_empty_state_visible"] is True
    assert summary["traces_empty_state_visible"] is True
    assert summary["approval_lifecycle_passed"] is True
    assert summary["approval_runtime_sandbox_used"] is True
    assert summary["dry_run_actions_allowed_total"] == 3
    assert summary["forbidden_action_blocked"] is True
    assert summary["settings_redacted"] is True
    assert summary["settings_plan_only"] is True
    assert summary["operator_dashboard_no_go_visible"] is True
    assert summary["operator_dashboard_next_actions_visible"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["source_mutations_performed"] is False


def test_operator_flow_smoke_writes_schema_valid_report_under_explicit_output(tmp_path: Path) -> None:
    output_json = tmp_path / "operator_flow_smoke_report.json"
    output_markdown = tmp_path / "operator_flow_smoke_report.md"
    result = OperatorFlowSmokeRunner(
        ROOT,
        OperatorFlowSmokeOptions(write_report=True, output_json=output_json, output_markdown=output_markdown),
    ).run()

    assert result.ok is True, result.to_dict()
    assert output_json.exists()
    assert output_markdown.exists()
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_id"] == "SCHEMA-DEVPL-OPERATOR-FLOW-SMOKE-REPORT-V1"
    assert payload["created_by"] == "POST-H-028-D"
    assert payload["summary"]["reports_written"] is True
    schema = SchemaValidator(ROOT).validate(schema="OperatorFlowSmokeReport", instance=output_json)
    assert schema.ok is True, schema.to_dict()


def test_operator_flow_smoke_cli_json_and_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    report = ROOT / "outputs" / "reports" / "operator_flow_smoke_report.json"
    if report.exists():
        report.unlink()

    exit_code = cli.main(["api", "operator-flow-smoke", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "api operator-flow-smoke"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["decision"] == "PASS"
    assert payload["data"]["summary"]["approval_runtime_sandbox_used"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/operator_flow_smoke_report.json"
    assert report.exists()


def test_operator_flow_quality_gate_includes_d_subgate_without_running_full_gate() -> None:
    gate = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))
    subgate_ids = {subgate.id for subgate in gate._subgates()}

    assert "api-contract-drift-guard" in subgate_ids
    assert "local-api-security-hardening" in subgate_ids
    assert "ui-visual-smoke" in subgate_ids
    assert "operator-flow-smoke" in subgate_ids


def test_operator_flow_schema_and_registries_are_registered() -> None:
    schema_catalog = _json("docs/schemas/schema_catalog.json")
    source_registry = _json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = _read(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _read(".devpilot/testing/test_contract_registry_v2.json")
    state = _json(".devpilot/project_state.json")

    assert any(entry["schema_id"] == "SCHEMA-DEVPL-OPERATOR-FLOW-SMOKE-REPORT-V1" for entry in schema_catalog["schemas"])
    assert any(doc["doc_id"] == "POST-H-028-D-OPERATOR-FLOW-SMOKE-REPORT" for doc in source_registry["documents"])
    assert "post-h-028-operator-flows-error-states" in tcr_v1
    assert "post-h-028-operator-flows-error-states" in tcr_v2
    assert state.get("post_h_028_current_micro_sprint") == "POST-H-028-E"
    assert state.get("post_h_028_next_micro_sprint") == "POST-H-029"
    assert state["post_h_028_operator_flow_smoke_available"] is True
    assert state["post_h_028_operator_flow_smoke_quality_gate_enabled"] is True
    assert state["post_h_028_operator_flow_smoke_runtime_sandbox_used"] is True


def test_web_ui_operator_flow_markers_and_safe_action_allowlist_are_synchronized() -> None:
    client = _read_web("src/api/client.ts")
    approvals = _read_web("src/pages/ApprovalCenterView.ts")
    action_form = _read_web("src/components/DryRunActionForm.ts")
    package = json.loads(_read_web("package.json"))
    smoke = _read_web("scripts/operator-flow-smoke.mjs")

    assert "API local down" in client
    assert "Unauthorized/Forbidden 401/403" in client
    assert "token local faltante o inválido" in client
    assert "0.0.0.0 como solución" not in client
    assert "no uses bind no-local como solución" in client
    assert "actor: 'local-owner'" in approvals
    assert "approval pending" in approvals
    assert "patch apply" in action_form
    assert "BLOCK visible" in action_form
    assert "patch-apply</option>" not in action_form
    assert package["scripts"]["test:operator-flows"] == "node scripts/operator-flow-smoke.mjs"
    assert package["devpilot"]["postH028D"] is True
    assert package["devpilot"]["operatorFlowSmoke"] is True
    assert "DEVPL WEB UI OPERATOR FLOW SMOKE TEST: PASS" in smoke


def test_operator_flow_smoke_npm_script_is_explicit_opt_in() -> None:
    if os.environ.get("DEVPILOT_RUN_WEB_UI_OPERATOR_FLOW_TEST", "").strip().lower() not in {"1", "true", "yes", "on"}:
        return
    npm = shutil.which("npm.cmd") or shutil.which("npm.exe") or shutil.which("npm")
    assert npm is not None, "DEVPILOT_RUN_WEB_UI_OPERATOR_FLOW_TEST enabled, but npm was not found."
    completed = subprocess.run(
        [npm, "run", "test:operator-flows"],
        cwd=WEB,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "DEVPL WEB UI OPERATOR FLOW SMOKE TEST: PASS" in completed.stdout
