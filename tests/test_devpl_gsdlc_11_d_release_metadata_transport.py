from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, resolve_route_policy

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    ("GET", "/api/v1/release/metadata"): "release.metadata.status",
    ("POST", "/api/v1/release/metadata/prepare"): "release.metadata.prepare",
    ("POST", "/api/v1/release/metadata/tag-plan"): "release.metadata.tag-plan",
    ("POST", "/api/v1/release/metadata/approve"): "release.metadata.approve",
    ("POST", "/api/v1/release/metadata/tag/execute"): "release.metadata.tag.execute",
}


def test_11d_release_metadata_routes_have_local_api_policy_binding() -> None:
    """Every browser-visible 11-D API route must cross the LocalAPI PolicyEngine boundary."""
    for key, operation in REQUIRED.items():
        assert key in API_ROUTE_POLICIES, f"missing API_ROUTE_POLICIES binding: {key}"
        policy = resolve_route_policy(*key)
        assert policy is not None
        assert policy.operation == operation
        assert policy.action == "read"
        assert policy.external_api is False


def test_11d_transport_policy_binding_matches_api_and_server_rbac_registries() -> None:
    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    rbac = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    api_routes = {(str(row.get("method", "")).upper(), str(row.get("path", ""))): str(row.get("operation", "")) for row in api.get("routes", [])}
    rbac_routes = {(str(row.get("method", "")).upper(), str(row.get("path", ""))): str(row.get("operation", "")) for row in rbac.get("route_policies", [])}
    for key, operation in REQUIRED.items():
        assert api_routes.get(key) == operation
        assert rbac_routes.get(key) == operation
        assert resolve_route_policy(*key) is not None
