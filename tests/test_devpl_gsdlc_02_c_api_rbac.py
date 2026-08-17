from pathlib import Path
from fastapi.testclient import TestClient
from devpilot_core.application import AuthApplicationService
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.interfaces.api.app import create_app

ROOT=Path(__file__).resolve().parents[1]

def client(tmp_path):
    store=LocalAuthStore(tmp_path); auth=AuthApplicationService(tmp_path,store=store)
    app=create_app(ROOT,api_token='legacy-token-test',auth_service=auth)
    return TestClient(app),store

def bootstrap(c):
    r=c.post('/api/v1/auth/bootstrap/owner',json={'username':'owner','display_name':'Owner','password':'A-very-long-local-password-123'},headers={'origin':'http://127.0.0.1:5173'})
    assert r.status_code==201

def test_capability_route_requires_human_session_and_legacy_token_is_403(tmp_path):
    c,_=client(tmp_path)
    r=c.get('/api/v1/auth/capabilities',headers={'X-DevPilot-Token':'legacy-token-test'})
    assert r.status_code in {401,403}
    bootstrap(c); r=c.get('/api/v1/auth/capabilities')
    assert r.status_code==200 and r.json()['capability_view']['server_authoritative'] is True

def test_direct_approval_bypass_with_legacy_token_is_denied(tmp_path):
    c,_=client(tmp_path)
    r=c.post('/api/v1/approvals/not-real/approve',headers={'X-DevPilot-Token':'legacy-token-test'})
    assert r.status_code in {401,403}

def test_developer_capability_view_matches_api_403_for_approval(tmp_path):
    c,store=client(tmp_path); bootstrap(c)
    # Internal authority mutation deliberately revokes owner session.
    store.update_identity_authority('local-owner',roles=('developer',),workspace_scopes=('devpilot-local',),changed_at='2030-01-01T00:00:00Z')
    # Login obtains a fresh session with developer authority.
    r=c.post('/api/v1/auth/login',json={'username':'owner','password':'A-very-long-local-password-123'},headers={'origin':'http://127.0.0.1:5173'}); assert r.status_code==200
    view=c.get('/api/v1/auth/capabilities').json()['capability_view']
    cap=[x for x in view['capabilities'] if x['path']=='/api/v1/approvals/{approval_id}/approve'][0]
    assert cap['allowed'] is False
    csrf=c.cookies.get('devpilot_csrf')
    resp=c.post('/api/v1/approvals/not-real/approve',headers={'origin':'http://127.0.0.1:5173','X-DevPilot-CSRF':csrf})
    assert resp.status_code==403


def test_cross_workspace_query_is_denied_server_side(tmp_path):
    c,_=client(tmp_path); bootstrap(c)
    r=c.get('/api/v1/workspace/status?workspace_id=other-workspace')
    assert r.status_code==403
    assert 'RBAC_WORKSPACE_SCOPE_DENY' in r.text
