from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.interfaces.api import UiRouteContractRegistryValidator
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "ui" / "web"
REGISTRY_PATH = ROOT / ".devpilot/interfaces/ui_route_contract_registry.json"
API_REGISTRY_PATH = ROOT / ".devpilot/interfaces/api_route_contract_registry.json"

CRITICAL_UI_ROUTES = {"ui.dashboard", "ui.reports", "ui.traces", "ui.approvals", "ui.settings"}
NO_GO_FLAGS = ("remote_execution_allowed", "connector_write_allowed", "plugin_execution_allowed", "external_api_allowed")


def read_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def read_api_registry() -> dict:
    return json.loads(API_REGISTRY_PATH.read_text(encoding="utf-8"))


def read_web_source(relative_path: str) -> str:
    return (WEB / relative_path).read_text(encoding="utf-8")


def test_post_h_014_c_ui_route_contract_registry_validates_against_schema() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="UiRouteContractRegistry",
        instance=".devpilot/interfaces/ui_route_contract_registry.json",
    )

    assert result.ok, result.to_dict()
    assert result.data["summary"]["valid"] is True


def test_post_h_014_c_validator_blocks_no_unregistered_or_unsafe_ui_routes() -> None:
    result = UiRouteContractRegistryValidator(ROOT).validate()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["routes_total"] == 5
    assert summary["critical_routes_total"] == 5
    assert summary["missing_critical_routes_total"] == 0
    assert summary["unknown_api_routes_total"] == 0
    assert summary["no_go_violations_total"] == 0
    assert summary["missing_source_files_total"] == 0
    assert summary["missing_source_markers_total"] == 0
    assert summary["pages_missing_state_contracts_total"] == 0
    assert summary["pages_missing_status_visibility_total"] == 0
    assert summary["pages_missing_badges_total"] == 0
    assert summary["external_api_allowed"] is False


def test_post_h_014_c_every_critical_page_has_contract_and_api_bindings() -> None:
    registry = read_registry()
    api_route_ids = {route["route_id"] for route in read_api_registry()["routes"]}
    routes = {route["route_id"]: route for route in registry["routes"]}

    assert set(routes) == CRITICAL_UI_ROUTES
    for route_id, route in routes.items():
        assert route["critical"] is True, route_id
        assert route["local_only"] is True, route_id
        assert route["local_first_badge_required"] is True, route_id
        assert route["dry_run_badge_required"] is True, route_id
        assert route["no_remote_badge_required"] is True, route_id
        assert {"PASS", "BLOCK", "ERROR", "PENDING"}.issubset(set(route["status_visibility"])), route_id
        assert all(route[flag] is False for flag in NO_GO_FLAGS), route_id
        assert set(route["allowed_api_routes"]).issubset(api_route_ids), route_id


def test_post_h_014_c_mutation_controls_are_local_dry_run_or_plan_only() -> None:
    routes = {route["route_id"]: route for route in read_registry()["routes"]}

    approvals = routes["ui.approvals"]
    assert approvals["shows_mutation_controls"] is True
    assert approvals["mutation_controls"]["local_state_mutation_only"] is True
    assert approvals["mutation_controls"]["approval_required"] is True
    assert approvals["mutation_controls"]["destructive_action_allowed"] is False
    assert "api.actions.dry_run" in approvals["allowed_api_routes"]

    settings = routes["ui.settings"]
    assert settings["shows_mutation_controls"] is True
    assert settings["mutation_controls"]["plan_only"] is True
    assert settings["mutation_controls"]["destructive_action_allowed"] is False
    assert "api.settings.providers.plan" in settings["allowed_api_routes"]


def test_post_h_014_c_web_sources_show_badges_and_states() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in (WEB / "src").rglob("*.ts"))

    for route_id in CRITICAL_UI_ROUTES:
        assert route_id in combined
    for label in ["Local-first", "Dry-run", "No remote", "No connector write", "No plugin execution"]:
        assert label in combined
    for state in ["loading", "empty", "error"]:
        assert f"data-ui-state" in combined or f"ui-state--{state}" in combined
    assert "BLOCK/ERROR" in combined
    assert "devpilot_core" not in combined
    assert "child_process" not in combined
    assert "outputs/" not in combined
    assert ".devpilot/" not in combined


def test_post_h_014_c_smoke_script_and_package_track_contract() -> None:
    package = json.loads((WEB / "package.json").read_text(encoding="utf-8"))
    smoke = read_web_source("scripts/smoke-test.mjs")

    assert package["devpilot"]["sprint"] == "FUNC-SPRINT-73"  # historical Fase F compatibility remains stable
    assert package["devpilot"]["postH014C"] is True
    assert package["devpilot"]["postH014D"] is True
    assert package["devpilot"]["uiRouteContractRegistry"] is True
    assert package["devpilot"]["remoteExecutionEnabled"] is False
    assert package["devpilot"]["connectorWriteEnabled"] is False
    assert package["devpilot"]["pluginExecutionEnabled"] is False
    assert "SCHEMA-DEVPL-UI-ROUTE-CONTRACT-REGISTRY-V1" in smoke
    assert "ui.dashboard" in smoke
    assert "ui.settings" in smoke
    assert "remote_execution_allowed" in smoke


def test_post_h_014_c_docs_contracts_and_backlog_are_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-014_ui_api_industrial_shell.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    interface_doc = (ROOT / "docs/07_interfaces/ui_api_industrial_shell.md").read_text(encoding="utf-8")
    ui_runbook = (ROOT / "docs/05_operations/ui_api_local_runbook.md").read_text(encoding="utf-8")
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")

    assert 'current_micro_sprint: "POST-H-014-D"' in backlog
    assert 'next_micro_sprint: "POST-H-014-E"' in backlog
    assert "POST-H-014-C — UI Route Contract y shell de producto" in backlog
    assert "UiRouteContractRegistry" in readme
    assert "UiRouteContractRegistry" in runbook
    assert "UiRouteContractRegistry" in interface_doc
    assert "UiRouteContractRegistry" in ui_runbook
    assert "post-h-014-ui-route-contract" in tcr_v1
    assert "post-h-014-ui-route-contract" in tcr_v2
    assert "post-h-014-security-hardening" in tcr_v1
    assert "post-h-014-security-hardening" in tcr_v2
