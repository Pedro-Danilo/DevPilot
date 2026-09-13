from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, resolve_route_policy

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    ("GET", "/api/v1/reconciliation"): "reconciliation.status",
    ("POST", "/api/v1/reconciliation/baseline"): "reconciliation.baseline",
    ("POST", "/api/v1/reconciliation/adopt"): "reconciliation.adopt",
}


def test_12_b_reconciliation_routes_cross_fail_closed_policy_engine() -> None:
    for key, operation in REQUIRED.items():
        assert key in API_ROUTE_POLICIES
        policy = resolve_route_policy(*key)
        assert policy is not None
        assert policy.operation == operation
        assert policy.external_api is False


def test_12_b_transport_registry_rbac_router_and_openapi_are_coherent() -> None:
    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    rbac = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    openapi = json.loads((ROOT / "docs/07_interfaces/openapi_v1.json").read_text(encoding="utf-8"))
    api_map = {(row["method"], row["path"]): row["operation"] for row in api["routes"]}
    rbac_map = {(row["method"], row["path"]): row["operation"] for row in rbac["route_policies"]}
    for key, operation in REQUIRED.items():
        assert api_map.get(key) == operation
        assert rbac_map.get(key) == operation
        assert key[1] in openapi["paths"]
    router = (ROOT / "src/devpilot_core/interfaces/api/routers/reconciliation.py").read_text(encoding="utf-8")
    assert "Authenticated human session is required" in router
    assert "execute: bool = False" in router
    assert "confirmation" in router


def test_12_b_current_rbac_has_no_stale_duplicate_recovery_action_policy() -> None:
    rbac = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    assert not any(row.get("action_id") == "recovery.lock.recover_stale" for row in rbac.get("sensitive_action_policies", []))
    recover = next(row for row in rbac["route_policies"] if row["operation"] == "recovery.lock.recover")
    assert set(recover["allowed_roles"]) == {"owner", "release-manager", "operator"}
    assert recover["human_session_required"] is True
