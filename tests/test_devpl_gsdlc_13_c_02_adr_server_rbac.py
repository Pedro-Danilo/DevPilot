from pathlib import Path
import json

from devpilot_core.identity.auth_models import AuthenticatedPrincipal
from devpilot_core.identity.server_rbac import ServerRBACEnforcer

ROOT = Path(__file__).resolve().parents[1]
ROUTES = (
    "/api/v1/guided-sdlc/pre-code/architecture-adrs/prepare",
    "/api/v1/guided-sdlc/pre-code/architecture-adrs/approval-request",
    "/api/v1/guided-sdlc/pre-code/architecture-adrs/apply",
)
ACTION = "filesystem.pre_code_architecture_adr_bundle_apply"
WORKSPACE = "inventory-sales-local-greenfield"


def _principal(role: str) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        actor_id=f"actor-{role}",
        username=f"user-{role}",
        display_name=role,
        roles=(role,),
        workspace_scopes=(WORKSPACE,),
    )


def test_companion_routes_exist_in_api_and_server_rbac_catalogs() -> None:
    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    rbac = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    api_routes = {(x["method"], x["path"]) for x in api["routes"]}
    rbac_routes = {(x["method"], x["path"]) for x in rbac["route_policies"]}
    for route in ROUTES:
        assert ("POST", route) in api_routes
        assert ("POST", route) in rbac_routes


def test_companion_routes_are_owner_only_human_session_workspace_scoped() -> None:
    enforcer = ServerRBACEnforcer(ROOT)
    owner = _principal("owner")
    developer = _principal("developer")
    for route in ROUTES:
        allow = enforcer.authorize_route(owner, method="POST", path=route, workspace_id=WORKSPACE)
        deny = enforcer.authorize_route(developer, method="POST", path=route, workspace_id=WORKSPACE)
        assert allow.allowed is True
        assert allow.reason_code == "RBAC_ALLOW"
        assert deny.allowed is False
        assert deny.reason_code == "RBAC_ROLE_DENY"


def test_companion_sensitive_action_is_registered_and_owner_only() -> None:
    catalog = json.loads((ROOT / ".devpilot/approval/sensitive_action_catalog.json").read_text(encoding="utf-8"))
    rbac = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    assert any(x["action_id"] == ACTION for x in catalog["actions"])
    row = next(x for x in rbac["sensitive_action_policies"] if x["action_id"] == ACTION)
    assert row["allowed_roles"] == ["owner"]
    assert row["legacy_token_allowed"] is False
    assert row["workspace_scope_required"] is True

    enforcer = ServerRBACEnforcer(ROOT)
    assert enforcer.authorize_sensitive_action(_principal("owner"), action_id=ACTION, workspace_id=WORKSPACE).allowed is True
    assert enforcer.authorize_sensitive_action(_principal("developer"), action_id=ACTION, workspace_id=WORKSPACE).allowed is False
