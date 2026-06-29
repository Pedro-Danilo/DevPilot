from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "ui" / "web"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _read_web(path: str) -> str:
    return (WEB / path).read_text(encoding="utf-8")


def _read_json(path: str) -> dict:
    return json.loads(_read(path))


def test_post_h_015_d_operator_dashboard_ui_sources_are_api_only_and_visible() -> None:
    client = _read_web("src/api/client.ts")
    dashboard = _read_web("src/pages/Dashboard.ts")
    operator_dashboard = _read_web("src/pages/OperatorDashboard.ts")
    status_card = _read_web("src/components/OperatorStatusCard.ts")
    gate_panel = _read_web("src/components/OperatorGatePanel.ts")
    next_actions = _read_web("src/components/OperatorNextActions.ts")
    sources = "\n".join([client, dashboard, operator_dashboard, status_card, gate_panel, next_actions])

    assert "/operator/dashboard" in client
    assert "write_report" in client
    assert "renderOperatorDashboard" in dashboard
    assert "POST-H-015-D" in operator_dashboard
    assert "source_refs" in status_card
    assert "No-go gates" in gate_panel
    assert "remote_execution_enabled=false" in gate_panel
    assert "Next actions" in next_actions
    assert "dry-run" in next_actions
    assert "devpilot_core" not in sources
    assert "child_process" not in sources
    assert "outputs/" not in sources
    assert ".devpilot/" not in sources
    assert "/patch/apply" not in sources
    assert "/rollback/execute" not in sources


def test_post_h_015_d_ui_route_contract_extends_dashboard_without_new_critical_route() -> None:
    registry = _read_json(".devpilot/interfaces/ui_route_contract_registry.json")
    api_registry = _read_json(".devpilot/interfaces/api_route_contract_registry.json")
    api_route_ids = {route["route_id"] for route in api_registry["routes"]}
    routes = {route["route_id"]: route for route in registry["routes"]}
    assert registry["summary"]["routes_total"] == 5
    assert registry["summary"]["critical_routes_total"] == 5
    assert set(routes) == {"ui.dashboard", "ui.reports", "ui.traces", "ui.approvals", "ui.settings"}
    dashboard = routes["ui.dashboard"]
    assert "api.operator.dashboard" in dashboard["allowed_api_routes"]
    assert "ui/web/src/pages/OperatorDashboard.ts" in dashboard["source_files"]
    assert "ui/web/src/components/OperatorStatusCard.ts" in dashboard["source_files"]
    assert registry["summary"]["post_h_015_d_operator_dashboard_ui_registered"] is True
    for route in registry["routes"]:
        assert route["remote_execution_allowed"] is False
        assert route["connector_write_allowed"] is False
        assert route["plugin_execution_allowed"] is False
        assert route["external_api_allowed"] is False
        assert set(route["allowed_api_routes"]).issubset(api_route_ids)
        for source_file in route["source_files"]:
            assert route["route_id"] in _read(source_file)


def test_post_h_015_d_package_smoke_and_docs_are_synchronized() -> None:
    package = json.loads(_read_web("package.json"))
    smoke = _read_web("scripts/smoke-test.mjs")
    backlog = _read("docs/backlogs/POST-H-015_local_operator_dashboard.md")
    runbook = _read("docs/05_operations/local_operator_dashboard_runbook.md")
    readme = _read("README.md")
    tcr_v2 = _read(".devpilot/testing/test_contract_registry_v2.json")

    assert package["devpilot"]["postH015D"] is True
    assert package["devpilot"]["operatorDashboardUi"] is True
    assert "/operator/dashboard" in smoke
    assert "OperatorDashboard" in smoke
    assert 'current_micro_sprint: "POST-H-015-E"' in backlog
    assert 'next_micro_sprint: "POST-H-016-A"' in backlog
    assert "POST-H-015-D — UI operator dashboard" in runbook
    assert "POST-H-015-D — UI operator dashboard" in readme
    assert "POST-H-015-E — Quality gate y runbook operacional" in runbook
    assert "POST-H-015-E — Quality gate y runbook operacional" in readme
    assert "post-h-015-operator-dashboard-ui" in tcr_v2
