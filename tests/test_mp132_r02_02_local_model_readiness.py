"""R02-02 local model readiness: no provider calls unless explicit loopback probe."""
from pathlib import Path
import json
from fastapi.testclient import TestClient
from devpilot_core.modeling.local_model_readiness import project_local_readiness,host_resources
from devpilot_core.modeling.local_endpoint_policy import LocalEndpointPolicy
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.interfaces.api.contract_drift import ApiContractDriftGuard
from devpilot_core.identity.server_rbac import ServerRBACEnforcer
from devpilot_core.identity.auth_models import CSRF_COOKIE_NAME

ROOT=Path(__file__).resolve().parents[1]
ROUTE='/api/v1/settings/local-model-readiness/probe'
ORIGIN={'Origin':'http://127.0.0.1:5173'}

def test_no_probe_no_egress_and_task_denied():
    x=project_local_readiness(ROOT)
    assert len(x['providers'])==2 and x['network_scope']=='none'
    assert x['external_api_calls']==x['inference_calls']==x['source_writes']==0
    assert x['deterministic_route_available'] is True
    for row in x['providers']:
        assert row['supported'] and row['healthy'] is None
        assert not row['evaluated'] and not row['eligible']
        assert len(row['tasks'])==2 and all(not t['eligible'] for t in row['tasks'])
    assert x['host']['measured']['gpu'] is False and x['host']['gpu_vram_bytes'] is None

def test_unconfigured_has_no_probe_even_when_requested(tmp_path,monkeypatch):
    import devpilot_core.modeling.local_model_readiness as readiness
    # Fully configured root source is tested independently; empty directory is not an eligible runtime.
    class Discovery:
        def __init__(self,*args,**kwargs):pass
        def build(self):
            return type('Result',(),{'data':{'report':{'providers':[
              {'provider_id':'ollama','configured':False,'enabled':False,'healthy':None,'probe_attempted':False,'endpoint_policy':{'ok':False},'models':[],'model_discovered':False},
              {'provider_id':'lmstudio','configured':False,'enabled':False,'healthy':None,'probe_attempted':False,'endpoint_policy':{'ok':False},'models':[],'model_discovered':False}]}}})()
    monkeypatch.setattr(readiness,'LocalProviderDiscoveryService',Discovery)
    x=readiness.project_local_readiness(tmp_path,probe=True)
    assert x['network_scope']=='loopback-only' and all(not i['probe_attempted'] for i in x['providers'])
    assert all(i['healthy_state']=='NOT_TESTED' for i in x['providers'])

def test_healthy_does_not_grant_eval_or_runtime(monkeypatch):
    import devpilot_core.modeling.local_model_readiness as readiness
    class Discovery:
        def __init__(self,*args,**kwargs): pass
        def build(self):
            return type('Result',(),{'data':{'report':{'providers':[
              {'provider_id':'ollama','configured':True,'enabled':False,'healthy':True,'probe_attempted':True,'endpoint_policy':{'ok':True},'models':['sample:local'],'model_discovered':True}]}}})()
    monkeypatch.setattr(readiness,'LocalProviderDiscoveryService',Discovery)
    row=readiness.project_local_readiness(ROOT,probe=True)['providers'][0]
    assert row['healthy_state']=='HEALTHY' and row['models']==['sample:local']
    assert not row['eligible'] and not row['evaluated'] and not row['configured_enabled']

def test_remote_endpoint_denied_before_probe():
    p=LocalEndpointPolicy.load(ROOT)
    for url in ['https://example.com:11434','http://169.254.169.254:11434','http://localhost.evil.com:11434','http://127.0.0.1:11434@evil.com']:
        assert not p.evaluate('ollama',url).ok

def test_route_catalog_and_openapi():
    assert ApiContractDriftGuard(ROOT).run().ok
    policy=ServerRBACEnforcer(ROOT).route_policy('POST',ROUTE)
    assert policy and policy['human_session_required'] and not policy['legacy_token_allowed']
    assert policy['allowed_roles']==['owner']
    assert ROUTE in json.loads((ROOT/'docs/07_interfaces/openapi_v1.json').read_text())['paths']

def test_session_csrf_owner_gate(tmp_path,monkeypatch):
    client=TestClient(create_app(tmp_path,api_token='local-legacy'),base_url='http://127.0.0.1:8787')
    response=client.post(ROUTE,headers={'X-DevPilot-Token':'local-legacy'},json={})
    assert response.status_code==401
    owner=client.post('/api/v1/auth/bootstrap/owner',headers=ORIGIN,json={'username':'owner','display_name':'Owner','password':'Some-long-local-passphrase-123'})
    assert owner.status_code==201
    denied=client.post(ROUTE,headers=ORIGIN,json={})
    assert denied.status_code==403
    # Test no socket: inject a hermetic health response at the read-only service boundary.
    from devpilot_core.application.services import ApplicationService
    monkeypatch.setattr(ApplicationService,'settings_local_readiness',lambda self,probe=False:{'schema':'MP132.R02.02.local_readiness.v1','probe_requested':probe,'external_api_calls':0,'inference_calls':0,'providers':[]})
    ok=client.post(ROUTE,headers={**ORIGIN,'X-DevPilot-CSRF':client.cookies.get(CSRF_COOKIE_NAME)},json={})
    assert ok.status_code==200,ok.text
    assert ok.json()['data']['probe_requested'] is True

def test_ui_comprehensible_and_explicit():
    page=(ROOT/'ui/web/src/pages/SettingsView.ts').read_text()
    view=(ROOT/'ui/web/src/components/LocalReadinessView.ts').read_text()
    client=(ROOT/'ui/web/src/api/client.ts').read_text()
    assert 'probeLocalModelReadiness()' in page and 'settings-probe-local-models' in view
    assert 'aria-live' in view and 'ELIGIBLE' in view and 'EVALUATED' in view
    assert 'settings/local-model-readiness/probe' in client
    assert 'no' not in 'yes' # marker; no backend enablement API from local readiness
