from pathlib import Path
import json
import pytest
from devpilot_core.identity.auth_models import AuthenticatedPrincipal
from devpilot_core.identity.server_rbac import ServerRBACEnforcer
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.identity.session_service import LocalAuthService, SessionInvalid

ROOT=Path(__file__).resolve().parents[1]

def principal(role='owner', scopes=('devpilot-local',)):
    return AuthenticatedPrincipal('actor-test','test','Test',(role,),tuple(scopes))

def test_policy_catalog_maps_every_current_route_and_sensitive_action():
    api=json.loads((ROOT/'.devpilot/interfaces/api_route_contract_registry.json').read_text())
    sens=json.loads((ROOT/'.devpilot/approval/sensitive_action_catalog.json').read_text())
    cat=json.loads((ROOT/'.devpilot/identity/server_rbac_policy_catalog.json').read_text())
    assert {(x['method'],x['path']) for x in api['routes']} == {(x['method'],x['path']) for x in cat['route_policies']}
    assert {x['action_id'] for x in sens['actions']} == {x['action_id'] for x in cat['sensitive_action_policies']}
    frozen=json.loads((ROOT/'.devpilot/interfaces/api_route_contract_registry_gsdlc02d_at_close.json').read_text())
    assert len(frozen['routes'])==97
    assert len(sens['actions'])>=16
    assert len(cat['sensitive_action_policies'])==len(sens['actions'])
    assert len(api['routes'])>=len(frozen['routes'])
    assert cat['summary']['unmapped_routes_total']==0 and cat['summary']['unmapped_sensitive_actions_total']==0

def test_unknown_route_action_and_role_are_deny_by_default():
    e=ServerRBACEnforcer(ROOT)
    assert not e.authorize_route(principal(),method='DELETE',path='/api/v1/not-real').allowed
    assert not e.authorize_sensitive_action(principal(),action_id='unknown.action').allowed
    assert not e.authorize_route(principal('made-up-role'),method='GET',path='/api/v1/workspace/status').allowed

def test_workspace_scope_cross_workspace_is_denied():
    e=ServerRBACEnforcer(ROOT)
    d=e.authorize_route(principal('owner',('workspace-a',)),method='GET',path='/api/v1/workspace/status',workspace_id='workspace-b')
    assert not d.allowed and d.reason_code=='RBAC_WORKSPACE_SCOPE_DENY'

def test_legacy_reviewer_alias_is_qa_not_security_reviewer():
    e=ServerRBACEnforcer(ROOT); p=principal('reviewer')
    assert e.canonical_roles(p)==('qa-reviewer',)
    d=e.authorize_route(p,method='POST',path='/api/v1/approvals/abc/approve',workspace_id='devpilot-local')
    assert not d.allowed

def test_maintainer_legacy_role_is_not_runtime_principal_and_sensitive_successor_is_owner_only():
    e=ServerRBACEnforcer(ROOT)
    assert e.canonical_roles(principal('maintainer'))==()
    for action in ('patch.apply','refactor.execute','filesystem.delete'):
        assert e.authorize_sensitive_action(principal('owner'),action_id=action,workspace_id='devpilot-local').allowed
        assert not e.authorize_sensitive_action(principal('developer'),action_id=action,workspace_id='devpilot-local').allowed

def test_legacy_token_never_allowed_for_human_auth_or_approval_authority():
    e=ServerRBACEnforcer(ROOT)
    assert not e.legacy_token_allowed(method='POST',path='/api/v1/approvals/a/approve')
    assert not e.legacy_token_allowed(method='GET',path='/api/v1/auth/capabilities')
    assert e.legacy_token_allowed(method='GET',path='/api/v1/workspace/status')

def test_role_change_revokes_sessions_and_stale_snapshot_fails_closed(tmp_path):
    store=LocalAuthStore(tmp_path); svc=LocalAuthService(tmp_path,store=store)
    issue=svc.bootstrap_owner(username='owner',display_name='Owner',password='A-very-long-local-password-123')
    changed='2030-01-01T00:00:00Z'
    revoked=store.update_identity_authority('local-owner',roles=('developer',),workspace_scopes=('devpilot-local',),changed_at=changed)
    assert revoked==1
    with pytest.raises(SessionInvalid):svc.resolve(issue.token)

def test_capability_view_is_sanitized_and_server_authoritative():
    e=ServerRBACEnforcer(ROOT); v=e.capability_view(principal('developer'),workspace_id='devpilot-local')
    assert v['server_authoritative'] is True and v['legacy_token_human_authority'] is False and v['secret_exposed'] is False
    ap=[x for x in v['capabilities'] if x['path']=='/api/v1/approvals/{approval_id}/approve'][0]
    assert ap['allowed'] is False and ap['reason_code']=='RBAC_ROLE_DENY'


def test_exhaustive_canonical_role_route_and_sensitive_action_matrix_is_total():
    e=ServerRBACEnforcer(ROOT)
    cat=json.loads((ROOT/'.devpilot/identity/server_rbac_policy_catalog.json').read_text())
    decisions=0
    for role in cat['canonical_roles']:
        p=principal(role)
        for route in cat['route_policies']:
            if route.get('public'):
                continue
            d=e.authorize_route(p,method=route['method'],path=route['path'],workspace_id='devpilot-local')
            assert d.reason_code in {'RBAC_ALLOW','RBAC_ROLE_DENY','RBAC_WORKSPACE_SCOPE_DENY'}
            decisions+=1
        for action in cat['sensitive_action_policies']:
            d=e.authorize_sensitive_action(p,action_id=action['action_id'],workspace_id='devpilot-local')
            assert d.reason_code in {'RBAC_ALLOW','RBAC_ROLE_DENY','RBAC_WORKSPACE_SCOPE_DENY'}
            decisions+=1
    protected_total=sum(1 for route in cat['route_policies'] if not route.get('public'))
    assert decisions == len(cat['canonical_roles']) * (protected_total + len(cat['sensitive_action_policies']))
