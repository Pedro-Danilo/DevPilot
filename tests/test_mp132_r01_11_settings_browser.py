"""R01-11: runtime API authority + browser surface contracts; localhost only."""
from __future__ import annotations
from pathlib import Path
from fastapi.testclient import TestClient
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.identity.auth_models import CSRF_COOKIE_NAME
from devpilot_core.interfaces.api.contract_drift import ApiContractDriftGuard

ROOT=Path(__file__).resolve().parents[1]
ORIGIN={'Origin':'http://127.0.0.1:5173'}


def login(tmp_path):
    client=TestClient(create_app(tmp_path,api_token='r11-legacy'),base_url='http://127.0.0.1:8787')
    result=client.post('/api/v1/auth/bootstrap/owner',json={'username':'owner','display_name':'Owner','password':'Some-long-local-passphrase-123'},headers=ORIGIN)
    assert result.status_code==201,result.text
    return client


def endpoint(action):return '/api/v1/settings/persistent/'+action


def mutation_headers(client):
    return {**ORIGIN,'X-DevPilot-CSRF':client.cookies.get(CSRF_COOKIE_NAME)}


def test_session_required_legacy_token_cannot_write(tmp_path):
    c=TestClient(create_app(tmp_path,api_token='r11-legacy'),base_url='http://127.0.0.1:8787')
    for method,action in [('get','effective'),('post','plan'),('post','apply')]:
        request=getattr(c,method)
        response=request(endpoint(action),headers={'X-DevPilot-Token':'r11-legacy'},**({'json':{'approve_write':True}} if method=='post' else {}))
        assert response.status_code==401
    assert not (tmp_path/'.devpilot/runtime/settings/settings.sqlite3').exists()


def test_browser_api_owner_plan_apply_reload_conflict(tmp_path):
    c=login(tmp_path)
    before=c.get(endpoint('effective'),params={'key':'ui.detail_level','scope':'platform','scope_id':'platform'})
    assert before.status_code==200 and before.json()['data']['target_revision']==0
    assert before.json()['data']['effective_value']=='guided'
    payload={'scope':'platform','scope_id':'platform','key':'ui.detail_level','value':'expert','expected_revision':0}
    plan=c.post(endpoint('plan'),headers=mutation_headers(c),json=payload)
    assert plan.status_code==200 and plan.json()['data']['write_performed'] is False
    assert not (tmp_path/'.devpilot/runtime/settings/settings.sqlite3').exists()
    denied=c.post(endpoint('apply'),headers=mutation_headers(c),json=payload)
    assert denied.status_code==403
    csrf_denied=c.post(endpoint('apply'),headers=ORIGIN,json={**payload,'approve_write':True})
    assert csrf_denied.status_code==403
    written=c.post(endpoint('apply'),headers=mutation_headers(c),json={**payload,'approve_write':True})
    assert written.status_code==200 and written.json()['data']['runtime_modified'] is False
    reread=c.get(endpoint('effective'),params={'key':'ui.detail_level','scope':'platform','scope_id':'platform'}).json()['data']
    assert reread['effective_value']=='expert' and reread['origin']=='platform:platform' and reread['target_revision']==1
    conflict=c.post(endpoint('apply'),headers=mutation_headers(c),json={**payload,'approve_write':True})
    assert conflict.status_code==409 and conflict.json()['data']['reason']=='REVISION_CONFLICT'


def test_policy_floor_and_cross_workspace(tmp_path):
    c=login(tmp_path)
    bad=c.post(endpoint('plan'),headers=mutation_headers(c),json={'scope':'platform','scope_id':'platform','key':'governance.external_network','value':'ALLOW','expected_revision':0})
    assert bad.status_code==403
    unknown=c.post(endpoint('plan'),headers=mutation_headers(c),json={'scope':'platform','scope_id':'platform','key':'secrets.api_key','value':'secret-value','expected_revision':0})
    assert unknown.status_code==403 and 'secret-value' not in unknown.text
    denied=c.get(endpoint('effective'),params={'key':'ui.detail_level','scope':'workspace','scope_id':'other-workspace','workspace_id':'other-workspace'})
    assert denied.status_code==403
    denied_plan=c.post(endpoint('plan'),headers=mutation_headers(c),json={'scope':'workspace','scope_id':'other-workspace','key':'ui.detail_level','value':'expert','expected_revision':0})
    assert denied_plan.status_code==403


def test_rbac_catalog_route_and_static_openapi_concordance():
    from devpilot_core.identity.server_rbac import ServerRBACEnforcer
    rbac=ServerRBACEnforcer(ROOT)
    for method,action in [('GET','effective'),('POST','plan'),('POST','apply')]:
        policy=rbac.route_policy(method,endpoint(action))
        assert policy and policy['human_session_required'] and not policy['legacy_token_allowed']
        if action=='apply':assert policy['allowed_roles']==['owner']
    assert ApiContractDriftGuard(ROOT).run().ok


def test_ui_has_accessible_sections_and_safe_client_boundary():
    home=(ROOT/'ui/web/src/components/PersistentSettingsHome.ts').read_text(encoding='utf-8')
    page=(ROOT/'ui/web/src/pages/SettingsView.ts').read_text(encoding='utf-8')
    client=(ROOT/'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    assert 'aria-live' in home and 'settings-write-confirm' in home and 'settings-plan-preview' in home
    assert 'aria-selected' in page and "event.key==='ArrowRight'" in page and "event.key!=='ArrowLeft'" in page
    assert "activeSettingsTab!=='providers'" in page and "activeSettingsTab!=='ai'" in page
    assert 'authJson<DevPilotApplicationResponse>' in client
    assert 'approve_write:true' in home
    assert 'settings/providers/revoke' in client and 'settings/persistent/apply' in client
