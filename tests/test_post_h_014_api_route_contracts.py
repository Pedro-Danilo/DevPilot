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
    expected_total = len(read_registry()["routes"])
    assert expected_total >= 42
    assert summary["routes_total"] == expected_total
    assert summary["fastapi_route_keys_total"] == expected_total
    assert summary["canonical_router_route_keys_total"] == expected_total
    assert summary["unregistered_routes_total"] == 0
    assert summary["stale_registry_routes_total"] == 0
    assert summary["remote_execution_allowed_total"] == 0
    assert summary["connector_write_allowed_total"] == 0
    assert summary["plugin_execution_allowed_total"] == 0
    assert summary["sensitive_routes_missing_auth_or_policy_total"] == 0
    assert summary["public_routes_total"] == 6
    public_auth = {r["route_id"] for r in read_registry()["routes"] if r.get("public") and r.get("owner") == "interfaces.api.auth"}
    assert public_auth == {"api.auth.bootstrap-status", "api.auth.bootstrap-owner", "api.auth.login"}
    assert summary["application_service_routes_total"] == sum(1 for route in read_registry()["routes"] if route.get("application_service_required"))


def test_post_h_014_a_every_service_route_is_application_service_and_policy_bound() -> None:
    payload = read_registry()
    routes = payload["routes"]
    protected_routes = [route for route in routes if not route.get("public")]
    service_routes = [route for route in protected_routes if route["application_service_required"]]

    assert protected_routes
    assert service_routes
    auth_response_contracts = {"AuthSessionSafeEnvelope", "AuthSessionSafeEnvelope+SetCookie", "AuthRevocationSafeEnvelope", "RBACCapabilityView"}
    assert all(
        route["response_contract"] == "ApplicationResponse"
        or (route.get("owner") == "interfaces.api.auth" and route["response_contract"] in auth_response_contracts)
        for route in protected_routes
    )
    assert all(route["auth_required"] is True for route in protected_routes)
    assert all(route["policy_check_required"] is True for route in protected_routes)
    assert any(route["route_id"] == "api.security.posture" and route["application_service_required"] is False for route in protected_routes)


def test_post_h_014_a_mutating_routes_are_explicitly_justified_and_local_only() -> None:
    payload = read_registry()
    mutating = [route for route in payload["routes"] if route["mutations_allowed"]]
    mutating_ids = {route["route_id"] for route in mutating}

    # POST-H-014-A froze the original approval-store exceptions. Later UOC
    # sprints may add typed local mutations, so this historical contract must
    # preserve the safety invariant instead of freezing the route inventory.
    legacy_approval_routes = {
        "api.approvals.request",
        "api.approvals.approve",
        "api.approvals.deny",
    }
    assert legacy_approval_routes <= mutating_ids

    # Preserve the POST-H-014 safety invariant while allowing later typed
    # lifecycle capabilities. UOC-006 adds exactly three approval-gated Git
    # mutations; it does not authorize arbitrary Git write.
    source_mutating = [route for route in mutating if route.get("source_mutation_allowed") is True]
    flags = json.loads((ROOT / ".devpilot/interfaces/ui_operational_console_flags.json").read_text(encoding="utf-8"))
    git_enabled = next(item for item in flags["feature_flags"] if item["flag_id"] == "uoc.git.governed_operations")["enabled"] is True
    expected_source_mutating = {
        "api.workspace.edit-plans.apply",
        "api.workspace.edit-executions.rollback",
    }
    if git_enabled:
        expected_source_mutating |= {
            "api.workspace.git.stage",
            "api.workspace.git.commit",
            "api.workspace.git.branch-create",
        }
    assert {route["route_id"] for route in source_mutating} == expected_source_mutating

    for route in mutating:
        assert route["local_only"] is True
        assert route["local_state_mutation_allowed"] is True
        assert route["destructive_action_allowed"] is False
        if route.get("public"):
            assert route["route_id"] in {"api.auth.bootstrap-owner", "api.auth.login"}
            assert route.get("owner") == "interfaces.api.auth"
        else:
            assert route["auth_required"] is True
        if route.get("public"):
            assert route["policy_check_required"] is False
        else:
            assert route["policy_check_required"] is True
        assert route["external_api_allowed"] is False
        assert route["remote_execution_allowed"] is False
        assert route["connector_write_allowed"] is False
        assert route["plugin_execution_allowed"] is False
        assert route["mutation_exception_justification"]

    routes = {route["route_id"]: route for route in mutating}
    for route_id in legacy_approval_routes:
        assert routes[route_id]["policy_action"] == "approval"

    validation_execute = routes["api.workspace.validations.execute"]
    assert validation_execute.get("source_mutation_allowed") is not True
    assert "runtime-evidence" in validation_execute["tags"]

    for route in source_mutating:
        assert route["risk_level"] == "high"
        assert any(tag in {"uoc-005", "uoc-006"} for tag in route["tags"])
        assert str(route["policy_sensitivity"]).startswith("approval-bound-")
        # The API front-door uses a non-mutating policy precheck; exact human
        # approval is revalidated by the owning ApplicationService immediately
        # before the narrow source/index/ref mutation.
        assert route["policy_action"] == "read"


def test_post_h_014_a_docs_contracts_and_backlog_are_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-014_ui_api_industrial_shell.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    interface_doc = (ROOT / "docs/07_interfaces/ui_api_industrial_shell.md").read_text(encoding="utf-8")
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")

    assert 'status: "approved"' in backlog
    assert 'current_micro_sprint: "POST-H-014-E"' in backlog
    assert 'next_micro_sprint: "POST-H-015"' in backlog
    assert "POST-H-014-A — Route Contract Registry y API inventory" in backlog
    assert "POST-H-014-A — Route Contract Registry y API inventory" in readme
    assert "POST-H-014-A — Route Contract Registry y API inventory" in runbook
    assert "ApiRouteContractRegistry" in interface_doc
    assert "post-h-014-api-route-contract-registry" in tcr_v1
    assert "post-h-014-api-route-contract-registry" in tcr_v2
    assert "post-h-014-security-hardening" in tcr_v1
    assert "post-h-014-security-hardening" in tcr_v2
