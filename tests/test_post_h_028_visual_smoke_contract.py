from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.interfaces.api import UiVisualSmokeOptions, UiVisualSmokeReporter
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


def test_ui_visual_smoke_report_passes_baseline_without_browser_dependency() -> None:
    result = UiVisualSmokeReporter(ROOT).run()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["decision"] == "PASS"
    assert summary["visual_smoke_passed"] is True
    assert summary["critical_views_total"] >= 6
    assert summary["critical_views_passed"] == summary["critical_views_total"]
    assert summary["operator_dashboard_embedded"] is True
    assert summary["empty_state_visible"] is True
    assert summary["error_state_visible"] is True
    assert summary["block_state_visible"] is True
    assert summary["unauthorized_state_visible"] is True
    assert summary["api_down_state_visible"] is True
    assert summary["screenshots_versioned"] is False
    assert summary["browser_tooling_required_for_core"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["source_mutations_performed"] is False


def test_ui_visual_smoke_report_writes_schema_valid_report_under_explicit_output(tmp_path: Path) -> None:
    output_json = tmp_path / "ui_visual_smoke_report.json"
    output_markdown = tmp_path / "ui_visual_smoke_report.md"
    result = UiVisualSmokeReporter(
        ROOT,
        UiVisualSmokeOptions(write_report=True, output_json=output_json, output_markdown=output_markdown),
    ).run()

    assert result.ok is True, result.to_dict()
    assert output_json.exists()
    assert output_markdown.exists()
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["schema_id"] == "SCHEMA-DEVPL-UI-VISUAL-SMOKE-REPORT-V1"
    assert payload["created_by"] == "POST-H-028-C"
    assert payload["summary"]["reports_written"] is True
    schema = SchemaValidator(ROOT).validate(schema="UiVisualSmokeReport", instance=output_json)
    assert schema.ok is True, schema.to_dict()


def test_ui_visual_smoke_cli_json_and_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    report = ROOT / "outputs" / "reports" / "ui_visual_smoke_report.json"
    if report.exists():
        report.unlink()

    exit_code = cli.main(["api", "visual-smoke-report", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "api visual-smoke-report"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["decision"] == "PASS"
    assert payload["data"]["summary"]["browser_tooling_required_for_core"] is False
    assert payload["data"]["reports"]["json"] == "outputs/reports/ui_visual_smoke_report.json"
    assert report.exists()


def test_ui_visual_smoke_browser_required_option_blocks_without_playwright() -> None:
    package = _read_web("package.json")
    result = UiVisualSmokeReporter(ROOT, UiVisualSmokeOptions(require_browser_tooling=True)).run()

    if "@playwright/test" in package:
        assert result.ok is True, result.to_dict()
    else:
        assert result.ok is False
        assert result.exit_code == ExitCode.BLOCK
        assert any(finding.id == "UI_VISUAL_SMOKE_BROWSER_TOOLING_REQUIRED_MISSING" for finding in result.findings)


def test_ui_visual_smoke_contract_files_and_package_scripts_are_synchronized() -> None:
    package = json.loads(_read_web("package.json"))
    smoke = _read_web("scripts/visual-smoke.mjs")
    client = _read_web("src/api/client.ts")
    gitignore = _read(".gitignore")
    web_gitignore = _read_web(".gitignore")

    assert package["devpilot"]["postH028C"] is True
    assert package["devpilot"]["uiVisualSmoke"] is True
    assert package["scripts"]["test:visual"] == "node scripts/visual-smoke.mjs"
    assert "DEVPL WEB UI VISUAL SMOKE TEST: PASS" in smoke
    assert "401/403" in client
    assert "API local down" in client
    assert "Unauthorized/Forbidden" in client
    assert (WEB / "playwright.config.ts").exists()
    assert (WEB / "tests" / "visual-smoke.spec.ts").exists()
    assert "outputs/ui-smoke/" in gitignore
    assert "ui/web/test-results/" in gitignore
    assert "test-results/" in web_gitignore
    assert "playwright-report/" in web_gitignore


def test_post_h_028_quality_gate_includes_b_and_c_subgates_without_running_full_gate() -> None:
    gate = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))
    subgate_ids = {subgate.id for subgate in gate._subgates()}

    assert "api-contract-drift-guard" in subgate_ids
    assert "local-api-security-hardening" in subgate_ids
    assert "ui-visual-smoke" in subgate_ids


def test_ui_visual_smoke_schema_and_registries_are_registered() -> None:
    schema_catalog = _json("docs/schemas/schema_catalog.json")
    source_registry = _json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = _read(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _read(".devpilot/testing/test_contract_registry_v2.json")
    state = _json(".devpilot/project_state.json")

    assert any(entry["schema_id"] == "SCHEMA-DEVPL-UI-VISUAL-SMOKE-REPORT-V1" for entry in schema_catalog["schemas"])
    assert any(doc["doc_id"] == "POST-H-028-C-VISUAL-SMOKE-REPORT" for doc in source_registry["documents"])
    assert "post-h-028-visual-smoke-tests" in tcr_v1
    assert "post-h-028-visual-smoke-tests" in tcr_v2
    assert state["current_micro_sprint"] == "POST-H-028-D"
    assert state["next_micro_sprint"] == "POST-H-028-E"
    assert state["post_h_028_ui_visual_smoke_available"] is True
    assert state["post_h_028_ui_visual_smoke_browser_required_for_core"] is False


def test_web_ui_visual_smoke_npm_script_is_explicit_opt_in() -> None:
    if os.environ.get("DEVPILOT_RUN_WEB_UI_VISUAL_TEST", "").strip().lower() not in {"1", "true", "yes", "on"}:
        return
    npm = shutil.which("npm.cmd") or shutil.which("npm.exe") or shutil.which("npm")
    assert npm is not None, "DEVPILOT_RUN_WEB_UI_VISUAL_TEST enabled, but npm was not found."
    completed = subprocess.run(
        [npm, "run", "test:visual"],
        cwd=WEB,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "DEVPL WEB UI VISUAL SMOKE TEST: PASS" in completed.stdout
