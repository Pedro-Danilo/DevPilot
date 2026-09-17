from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")

def test_shared_operational_primitives_exist():
    src = text("ui/web/src/components/OperationalPatterns.ts")
    for token in ["renderOperationState", "renderPrimaryAction", "renderGateSummary", "renderApprovalSummary", "renderDiffSummary", "renderLongRunningOperation", "renderProgressiveEvidence", "renderOperationalSurfaceSummary"]:
        assert f"function {token}" in src
    for state in ["loading", "empty", "ready", "pending", "running", "pass", "warn", "block", "error", "recovery", "stale", "revalidation"]:
        assert state in src

def test_priority_surfaces_adopt_shared_summary():
    paths = [
        "ui/web/src/pages/StoryCodeWorkbenchView.ts", "ui/web/src/pages/ApprovalCenterView.ts",
        "ui/web/src/pages/JobsView.ts", "ui/web/src/pages/QualityOperationsView.ts",
        "ui/web/src/pages/ReleaseReadinessView.ts", "ui/web/src/pages/ReleasePackageView.ts",
        "ui/web/src/pages/ReleaseLifecycleView.ts", "ui/web/src/pages/ReleaseClosureView.ts",
        "ui/web/src/pages/RecoveryView.ts", "ui/web/src/pages/AiOperationsView.ts",
        "ui/web/src/components/ArtifactReconciliationUX.ts",
    ]
    for rel in paths:
        assert "renderOperationalSurfaceSummary" in text(rel), rel

def test_reports_and_traces_remain_diagnostic_heavy():
    assert "renderOperationalSurfaceSummary" not in text("ui/web/src/pages/ReportsView.ts")
    assert "renderOperationalSurfaceSummary" not in text("ui/web/src/pages/TracesView.ts")

def test_no_route_or_api_contract_change_in_delta_primitives():
    src = text("ui/web/src/components/OperationalPatterns.ts")
    assert "fetch(" not in src
    assert "DevPilotApiClient" not in src
    assert "localStorage" not in src
    assert "sessionStorage" not in src

def test_current_authority_rebound_to_d():
    import json
    state=json.loads(text(".devpilot/project_state.json"))
    assert state["ux_p0_c_status"] == "CLOSED/PASS/WINDOWS-VALIDATED"
    assert state["current_micro_sprint"] == "DEVPL-UX-P0-D"
    assert state["next_micro_sprint"] == "DEVPL-UX-P0-E"
    assert state["ux_p0_d_full_regression_runs"] == 0
