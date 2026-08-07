from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_REPO = "repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load(path: str) -> dict:
    return json.loads(read(path))


def test_corrective_baseline_is_preserved_after_01_d_closure() -> None:
    state = load(".devpilot/project_state.json")
    assert state["post_h_eval_002_01_d_governance_repo"] == TARGET_REPO
    assert state["current_repo"].startswith("repo_DevPilot_Local_")
    assert state["current_micro_sprint"] in {"POST-H-EVAL-002-02-A", "POST-H-EVAL-002-02-B"}
    assert state["post_h_eval_002_01_d_closed"] is True
    assert state["post_h_eval_002_01_d_browser_acceptance_executed"] is True
    assert state["post_h_eval_002_01_d_next_authorized"] is True
    assert state["post_h_eval_002_01_d_required_retest_run_id"] == "PILOT-E2E-001-RUN-05B-RERUN-03"


def test_dashboard_removes_eager_embedded_views_and_bounds_fanout() -> None:
    source = read("ui/web/src/pages/Dashboard.ts")
    assert "renderReportTraceView" not in source
    assert "renderApprovalCenterView" not in source
    assert "renderSettingsView" not in source
    assert "runBounded" in source
    assert ",\n      2," in source
    assert "maximum 2" not in source  # Spanish UI text, implementation is structural.
    assert "renderRouteSummaries" in source


def test_reports_and_traces_are_route_specific() -> None:
    main = read("ui/web/src/main.ts")
    reports = read("ui/web/src/pages/ReportsView.ts")
    traces = read("ui/web/src/pages/TracesView.ts")
    assert "renderReportsView" in main
    assert "renderTracesView" in main
    assert "listTraces" not in reports
    assert "listReports" not in traces
    registry = load(".devpilot/interfaces/ui_route_contract_registry.json")
    by_id = {item["route_id"]: item for item in registry["routes"]}
    assert by_id["ui.reports"]["page_component"] == "ReportsView"
    assert by_id["ui.traces"]["page_component"] == "TracesView"
    assert "api.traces.list" not in by_id["ui.reports"]["allowed_api_routes"]
    assert "api.reports.list" not in by_id["ui.traces"]["allowed_api_routes"]


def test_settings_states_are_mutually_exclusive() -> None:
    source = read("ui/web/src/pages/SettingsView.ts")
    assert "type SettingsPhase = 'idle' | 'loading' | 'ready' | 'empty' | 'error'" in source
    assert "renderPhaseNotice" in source
    assert "data-ui-state=\"loading\"" not in source
    assert "data-ui-state=\"empty\"" not in source
    assert "data-ui-state=\"error\"" not in source
    assert "runBounded" in source


def test_no_go_gate_unknown_is_not_block() -> None:
    source = read("ui/web/src/components/OperatorGatePanel.ts")
    assert "'UNKNOWN'" in source
    assert "este estado no equivale a BLOCK" in source
    assert "'DISABLED BY POLICY'" in source


def test_timeout_keeps_eight_second_bound_and_adds_context() -> None:
    source = read("ui/web/src/api/client.ts")
    assert "DEFAULT_REQUEST_TIMEOUT_MS = 8000" in source
    assert "READINESS_REQUEST_TIMEOUT_MS = 30000" in source
    assert "ACTION_DRY_RUN_TIMEOUT_MS = 60000" in source
    assert "PROVIDER_PLAN_TIMEOUT_MS = 60000" in source
    assert "TRANSIENT_NETWORK_RETRY_DELAYS_MS = [500, 1000]" in source
    assert "endpoint: path" in source
    assert "action: 'retry'" in source
    assert "durationMs" in source


def test_corrective_static_contract_is_registered() -> None:
    package = load("ui/web/package.json")
    assert package["scripts"]["test:acceptance-corrective"] == "node scripts/acceptance-corrective.mjs"
    assert package["devpilot"]["dashboardMaxConcurrency"] == 2
    assert package["devpilot"]["dashboardEmbeddedDetailViews"] is False
    assert package["devpilot"]["reportsTracesSeparated"] is True
    assert package["devpilot"]["browserRetestRunId"] == "PILOT-E2E-001-RUN-05B-RERUN-03"
    assert package["devpilot"]["protectedWarmup"] is True
    assert package["devpilot"]["actionPendingFeedback"] is True


def test_partial_run_is_diagnostic_not_closure_evidence() -> None:
    manifest = load("docs/post_h_eval_002_01_d_ui_corrective_manifest.json")
    assert manifest["partial_run_analysis"]["requested_files_present"] == 5
    assert manifest["partial_run_analysis"]["requested_files_missing"] == ["process_lifecycle.json"]
    assert manifest["partial_run_analysis"]["http_requests_logged"] == 115
    assert manifest["partial_run_analysis"]["http_non_200_total"] == 0
    assert manifest["closure_state"]["closed"] is False
    assert manifest["closure_state"]["next_authorized"] is False
