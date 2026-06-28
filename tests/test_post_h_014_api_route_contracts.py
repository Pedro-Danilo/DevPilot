from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    src_path = str(SRC)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

import devpilot_core
from devpilot_core.interfaces.api import ApiRouteContractRegistryValidator
from devpilot_core.interfaces.api.contracts import collect_canonical_api_route_keys
from devpilot_core.schemas import SchemaValidator

REGISTRY_PATH = ROOT / ".devpilot/interfaces/api_route_contract_registry.json"


def read_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _assert_local_source_tree_imported() -> None:
    imported_from = Path(devpilot_core.__file__ or "").resolve()
    assert _is_under(imported_from, SRC), (
        "POST-H-014-A tests must import devpilot_core from the repo src/ tree, "
        f"but imported from {imported_from}. Run with PYTHONPATH=src or keep "
        "tests/conftest.py path bootstrap enabled."
    )


def fastapi_route_keys() -> set[str]:
    _assert_local_source_tree_imported()
    return collect_canonical_api_route_keys()


def registry_route_keys() -> set[str]:
    payload = read_registry()
    return {f"{item['method']} {item['path']}" for item in payload["routes"]}


def test_post_h_014_a_api_route_registry_validates_against_schema() -> None:
    _assert_local_source_tree_imported()
    result = SchemaValidator(ROOT).validate(
        schema="ApiRouteContractRegistry",
        instance=".devpilot/interfaces/api_route_contract_registry.json",
    )

    assert result.ok, result.to_dict()
    assert result.data["summary"]["valid"] is True


def test_post_h_014_a_fastapi_routes_match_registry() -> None:
    actual = fastapi_route_keys()
    expected = registry_route_keys()
    assert actual == expected, {
        "missing_in_registry": sorted(actual - expected),
        "stale_in_registry": sorted(expected - actual),
        "actual_total": len(actual),
        "expected_total": len(expected),
        "devpilot_core_imported_from": str(Path(devpilot_core.__file__ or "").resolve()),
        "route_inventory_source": "canonical_router_modules_plus_app_public_routes",
    }


def test_post_h_014_a_contract_validator_blocks_no_unregistered_or_unsafe_routes() -> None:
    _assert_local_source_tree_imported()
    result = ApiRouteContractRegistryValidator(ROOT).validate()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["routes_total"] == 32
    assert summary["fastapi_route_keys_total"] == 32
    assert summary["canonical_router_route_keys_total"] == 32
    assert summary["unregistered_routes_total"] == 0
    assert summary["stale_registry_routes_total"] == 0
    assert summary["remote_execution_allowed_total"] == 0
    assert summary["connector_write_allowed_total"] == 0
    assert summary["plugin_execution_allowed_total"] == 0
    assert summary["sensitive_routes_missing_auth_or_policy_total"] == 0
    assert summary["public_routes_total"] == 3
    assert summary["application_service_routes_total"] == 29


def test_post_h_014_a_every_service_route_is_application_service_and_policy_bound() -> None:
    payload = read_registry()
    routes = payload["routes"]
    service_routes = [route for route in routes if not route.get("public")]

    assert service_routes
    assert all(route["application_service_required"] is True for route in service_routes)
    assert all(route["response_contract"] == "ApplicationResponse" for route in service_routes)
    assert all(route["auth_required"] is True for route in service_routes)
    assert all(route["policy_check_required"] is True for route in service_routes)


def test_post_h_014_a_mutating_routes_are_explicitly_justified_and_local_only() -> None:
    payload = read_registry()
    mutating = [route for route in payload["routes"] if route["mutations_allowed"]]

    assert {route["route_id"] for route in mutating} == {
        "api.approvals.request",
        "api.approvals.approve",
        "api.approvals.deny",
    }
    for route in mutating:
        assert route["local_state_mutation_allowed"] is True
        assert route["destructive_action_allowed"] is False
        assert route["auth_required"] is True
        assert route["policy_check_required"] is True
        assert route["policy_action"] == "approval"
        assert route["mutation_exception_justification"]


def test_post_h_014_a_docs_contracts_and_backlog_are_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-014_ui_api_industrial_shell.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    interface_doc = (ROOT / "docs/07_interfaces/ui_api_industrial_shell.md").read_text(encoding="utf-8")
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")

    assert 'status: "approved"' in backlog
    assert 'current_micro_sprint: "POST-H-014-B"' in backlog
    assert 'next_micro_sprint: "POST-H-014-C"' in backlog
    assert "POST-H-014-A — Route Contract Registry y API inventory" in backlog
    assert "POST-H-014-A — Route Contract Registry y API inventory" in readme
    assert "POST-H-014-A — Route Contract Registry y API inventory" in runbook
    assert "ApiRouteContractRegistry" in interface_doc
    assert "post-h-014-api-route-contract-registry" in tcr_v1
    assert "post-h-014-api-route-contract-registry" in tcr_v2
