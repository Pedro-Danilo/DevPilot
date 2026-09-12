from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, resolve_route_policy

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    ("GET", "/api/v1/recovery"): "recovery.status",
    ("POST", "/api/v1/recovery/checkpoint"): "recovery.checkpoint",
    ("POST", "/api/v1/recovery/locks/acquire"): "recovery.lock.acquire",
    ("POST", "/api/v1/recovery/locks/release"): "recovery.lock.release",
    ("POST", "/api/v1/recovery/locks/recover"): "recovery.lock.recover",
}


def test_12_a_recovery_routes_cross_fail_closed_policy_engine() -> None:
    for key, operation in REQUIRED.items():
        assert key in API_ROUTE_POLICIES
        policy = resolve_route_policy(*key)
        assert policy is not None
        assert policy.operation == operation
        assert policy.external_api is False


def test_12_a_recovery_transport_registry_rbac_and_router_are_coherent() -> None:
    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    rbac = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    api_map = {(row["method"], row["path"]): row["operation"] for row in api["routes"]}
    rbac_map = {(row["method"], row["path"]): row["operation"] for row in rbac["route_policies"]}
    for key, operation in REQUIRED.items():
        assert api_map.get(key) == operation
        assert rbac_map.get(key) == operation
    router = (ROOT / "src/devpilot_core/interfaces/api/routers/recovery.py").read_text(encoding="utf-8")
    assert "Authenticated human session is required" in router
    assert "RECOVER_STALE_LOCK" in router
