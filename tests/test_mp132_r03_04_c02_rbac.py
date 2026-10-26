"""R03-04 C02 P2: real route contract remains deny-by-default, Owner-only."""
from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.identity.auth_models import AuthenticatedPrincipal
from devpilot_core.identity.server_rbac import ServerRBACEnforcer
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES

ROOT = Path(__file__).resolve().parents[1]
ROUTE = "/api/v1/guided-sdlc/pre-code/technology-action"
METHOD = "POST"
OPERATION = "guided_sdlc.pre_code.technology_action"


def test_route_registered_in_all_three_contracts():
    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    rbac = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    spec = json.loads((ROOT / "docs/07_interfaces/openapi_v1.json").read_text(encoding="utf-8"))
    ar = {(x["method"], x["path"]): x for x in api["routes"]}
    rr = {(x["method"], x["path"]): x for x in rbac["route_policies"]}
    assert set(ar) == set(rr)
    assert len(ar) == len(rr)
    contract = ar[METHOD, ROUTE]
    policy = rr[METHOD, ROUTE]
    assert contract["operation"] == policy["operation"] == API_ROUTE_POLICIES[METHOD, ROUTE].operation == OPERATION
    assert spec["paths"][ROUTE]["post"]["summary"] == OPERATION
    assert contract["source_mutation_allowed"] is False
    assert contract["local_state_mutation_allowed"] is True
    assert not contract["external_api_allowed"]
    assert policy["allowed_roles"] == ["owner"]
    assert policy["human_session_required"] and policy["workspace_scope_required"]
    assert policy["deny_by_default"] and not policy["legacy_token_allowed"]
    assert api["summary"]["routes_total"] == rbac["summary"]["route_policies_total"] == len(ar)


def test_owner_is_authorized_non_owner_and_wrong_workspace_are_denied():
    enforcer = ServerRBACEnforcer(ROOT)
    workspace = enforcer.catalog["workspace"]["default_local_workspace_id"]
    def principal(role: str, scopes: tuple[str, ...]):
        return AuthenticatedPrincipal(actor_id="user-1", username="operator-test", display_name="Test", roles=(role,), workspace_scopes=scopes)
    allowed = enforcer.authorize_route(principal("owner", (workspace,)), method=METHOD, path=ROUTE, workspace_id=workspace)
    assert allowed.allowed and allowed.reason_code == "RBAC_ALLOW"
    denied = enforcer.authorize_route(principal("developer", (workspace,)), method=METHOD, path=ROUTE, workspace_id=workspace)
    assert not denied.allowed and denied.reason_code == "RBAC_ROLE_DENY"
    outside = enforcer.authorize_route(principal("owner", ("other-workspace",)), method=METHOD, path=ROUTE, workspace_id=workspace)
    assert not outside.allowed and outside.reason_code == "RBAC_WORKSPACE_SCOPE_DENY"
    assert not enforcer.legacy_token_allowed(method=METHOD, path=ROUTE)
