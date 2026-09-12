from __future__ import annotations
import json
from pathlib import Path
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, resolve_route_policy
ROOT=Path(__file__).resolve().parents[1]
REQUIRED={("GET","/api/v1/release/closure"):"release.closure.status",("POST","/api/v1/release/closure/finalize"):"release.closure.finalize"}
def test_11e_release_closure_routes_cross_policy_engine():
    for key,op in REQUIRED.items():
        assert key in API_ROUTE_POLICIES
        p=resolve_route_policy(*key); assert p is not None and p.operation==op and p.external_api is False
def test_11e_release_closure_transport_registry_coherence():
    api=json.loads((ROOT/'.devpilot/interfaces/api_route_contract_registry.json').read_text());rbac=json.loads((ROOT/'.devpilot/identity/server_rbac_policy_catalog.json').read_text())
    ar={(x['method'],x['path']):x['operation'] for x in api['routes']};rr={(x['method'],x['path']):x['operation'] for x in rbac['route_policies']}
    for key,op in REQUIRED.items(): assert ar.get(key)==op and rr.get(key)==op
