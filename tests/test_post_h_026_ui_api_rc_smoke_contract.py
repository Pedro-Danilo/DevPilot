from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_API_ROUTE_IDS = {
    "api.health",
    "api.security.posture",
    "api.operator.dashboard",
    "api.reports.list",
    "api.traces.list",
    "api.approvals.list",
    "api.settings.providers",
    "api.actions.dry_run",
}
REQUIRED_UI_ROUTE_IDS = {"ui.dashboard", "ui.reports", "ui.traces", "ui.approvals", "ui.settings"}
REQUIRED_UI_MARKERS = {
    'data-ui-state="loading"',
    'data-ui-state="empty"',
    'data-ui-state="error"',
    "BLOCK",
    "Security posture",
    "Provider editor plan-only",
}
FORBIDDEN_SOURCE_MARKERS = {
    "devpilot_core",
    "child_process",
    "fs.readFile",
    "writeFile",
    "/patch/apply",
    "/rollback/execute",
    "/git/push",
}


def _load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_ui_api_rc_smoke_schema_is_registered() -> None:
    catalog = _load_json("docs/schemas/schema_catalog.json")
    schemas = {entry["schema_id"]: entry for entry in catalog["schemas"]}

    assert "SCHEMA-DEVPL-UI-API-RC-SMOKE-REPORT-V1" in schemas
    entry = schemas["SCHEMA-DEVPL-UI-API-RC-SMOKE-REPORT-V1"]
    assert entry["contract"] == "UiApiRcSmokeReport"
    assert (ROOT / entry["path"]).exists()


def test_ui_api_rc_smoke_route_contracts_cover_operator_flows() -> None:
    api_registry = _load_json(".devpilot/interfaces/api_route_contract_registry.json")
    ui_registry = _load_json(".devpilot/interfaces/ui_route_contract_registry.json")
    api_routes = {route["route_id"]: route for route in api_registry["routes"]}
    ui_routes = {route["route_id"]: route for route in ui_registry["routes"]}

    assert REQUIRED_API_ROUTE_IDS <= set(api_routes)
    assert REQUIRED_UI_ROUTE_IDS <= set(ui_routes)
    for route_id in REQUIRED_API_ROUTE_IDS:
        route = api_routes[route_id]
        assert route["local_only"] is True
        assert route["external_api_allowed"] is False
        assert route["remote_execution_allowed"] is False
        assert route["connector_write_allowed"] is False
        assert route["plugin_execution_allowed"] is False
    for route_id in REQUIRED_UI_ROUTE_IDS:
        route = ui_routes[route_id]
        state = route["state_contract"]
        assert route["local_only"] is True
        assert state["loading"] is True
        assert state["empty"] is True
        assert state["error"] is True
        assert state["block_visible"] is True
        assert route["external_api_allowed"] is False
        assert route["remote_execution_allowed"] is False
        assert route["connector_write_allowed"] is False
        assert route["plugin_execution_allowed"] is False


def test_ui_api_rc_smoke_web_ui_static_contract_is_api_only() -> None:
    sources = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in (ROOT / "ui/web/src").rglob("*.ts"))
    smoke = (ROOT / "ui/web/scripts/smoke-test.mjs").read_text(encoding="utf-8")
    bundle = sources + "\n" + smoke

    missing_markers = sorted(marker for marker in REQUIRED_UI_MARKERS if marker not in bundle)
    forbidden = sorted(marker for marker in FORBIDDEN_SOURCE_MARKERS if marker in sources)
    direct_runtime_reads = sorted(marker for marker in ("outputs/", ".devpilot/") if marker in sources)

    assert missing_markers == []
    assert forbidden == []
    assert direct_runtime_reads == []
    assert "http://127.0.0.1:8787/api/v1" in sources
    assert "X-DevPilot-Token" in sources


def test_post_h_026_c_is_registered_in_test_contracts() -> None:
    tcr_v1 = _load_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _load_json(".devpilot/testing/test_contract_registry_v2.json")
    v1_ids = {contract["contract_id"] for contract in tcr_v1["contracts"]}
    v2_ids = {contract["contract_id"] for contract in tcr_v2["contracts"]}

    assert "post-h-026-ui-api-rc-smoke" in v1_ids
    assert "post-h-026-ui-api-rc-smoke" in v2_ids
