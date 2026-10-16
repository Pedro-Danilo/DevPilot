from pathlib import Path
from types import SimpleNamespace
import json
import pytest

from devpilot_core.generation.lmstudio_product_definition import LMStudioProductDefinitionEvaluation, LocalCandidateBlock, _extract_content
from devpilot_core.modeling.providers import ProviderRegistry

ROOT=Path(__file__).resolve().parents[1]

def root(tmp_path):
    (tmp_path/'evals/fixtures').mkdir(parents=True)
    (tmp_path/'evals/fixtures/r02_03_product_definition.json').write_bytes((ROOT/'evals/fixtures/r02_03_product_definition.json').read_bytes())
    return tmp_path

class FakeLM:
    posts=0
    def __init__(self, **kwargs):pass
    def health(self):return SimpleNamespace(ok=True,data={'models':['local-model']})
    def _post_json(self,path,payload,task):
        assert path=='/v1/chat/completions' and payload['stream'] is False
        assert payload['response_format']=={'type':'json_object'}
        FakeLM.posts+=1
        ref='fixture:loan-business-need-v1' if 'product-vision' in payload['messages'][0]['content'] else 'fixture:loan-vision-v1' if 'scope' in payload['messages'][0]['content'] else 'fixture:loan-scope-v1'
        obj={'title':'Propuesta sintética segura','content':'# Candidato\nSe debe verificar el objetivo de las solicitudes y los usuarios autorizados sin inventar datos externos.','evidence_refs':[ref]}
        return SimpleNamespace(ok=True,metadata={'choices':[{'message':{'content':json.dumps(obj)}}], 'usage':{'prompt_tokens':12,'completion_tokens':40}})

def test_dry_run_no_network(tmp_path):
    class NoNetwork:
        def __init__(self,**kw):raise AssertionError('unexpected network')
    result=LMStudioProductDefinitionEvaluation(root(tmp_path),adapter_factory=NoNetwork).run(case_id='vision',model='local-model',request_id='a'*32)
    assert result['status']=='DRY_RUN' and result['network_calls']==0
    assert not (tmp_path/'outputs').exists()

def test_live_fake_replay_exact_no_global_enablement(tmp_path):
    FakeLM.posts=0; a=LMStudioProductDefinitionEvaluation(root(tmp_path),adapter_factory=FakeLM)
    first=a.run(case_id='vision',model='local-model',request_id='b'*32,execute=True)
    assert first['status']=='REAL_CANDIDATE_GENERATED_UNREVIEWED'
    assert first['candidate']['origin']['provider_id']=='lmstudio'
    assert first['source_writes']==0 and not first['provider_enablement_changed']
    assert first['external_api_calls']==0 and FakeLM.posts==1
    assert a.run(case_id='vision',model='local-model',request_id='b'*32,execute=True)['replayed']
    assert FakeLM.posts==1
    with pytest.raises(LocalCandidateBlock,match='REQUEST_ID_CONFLICT'):
        a.run(case_id='scope',model='local-model',request_id='b'*32,execute=True)

def test_missing_model_fails_without_post(tmp_path):
    class Missing(FakeLM):
        def health(self):return SimpleNamespace(ok=True,data={'models':[]})
        def _post_json(self,*args,**kwargs):raise AssertionError('do not generate')
    with pytest.raises(LocalCandidateBlock,match='MODEL_NOT_INSTALLED'):
        LMStudioProductDefinitionEvaluation(root(tmp_path),adapter_factory=Missing).run(case_id='scope',model='local-model',request_id='c'*32,execute=True)

def test_remote_endpoint_rejected(tmp_path,monkeypatch):
    from dataclasses import replace
    cfg=ProviderRegistry.load(tmp_path).get('lmstudio')
    class FakeReg:
        semantic_valid=True
        def get(self,provider_id):return replace(cfg,endpoint='https://api.openai.com/v1')
    monkeypatch.setattr('devpilot_core.generation.lmstudio_product_definition.ProviderRegistry.load',lambda *args:FakeReg())
    with pytest.raises(LocalCandidateBlock,match='LOOPBACK_POLICY_BLOCK'):
        LMStudioProductDefinitionEvaluation(root(tmp_path),adapter_factory=FakeLM).run(case_id='vision',model='local-model',request_id='d'*32,execute=True)

def test_malformed_json_unsupported_evidence_and_bad_choices():
    from devpilot_core.generation.ollama_product_definition import parse_model_json
    for x in [None,{}, {'choices':[]},{'choices':[{'message':{}}]}]:
        with pytest.raises(LocalCandidateBlock,match='LMSTUDIO_CONTENT_INVALID'): _extract_content(x)
    with pytest.raises(LocalCandidateBlock,match='UNSUPPORTED_REFERENCE_BLOCK'):
        parse_model_json(json.dumps({'title':'Prueba en español','content':'A'*90,'evidence_refs':['fixture:inventado']}),expected_ref='fixture:loan-vision-v1')

def test_security_contract_and_separation():
    policy=json.loads((ROOT/'.devpilot/identity/server_rbac_policy_catalog.json').read_text())
    path='/api/v1/settings/lmstudio/product-definition/candidate'
    item=next(x for x in policy['route_policies'] if x['path']==path)
    assert item['allowed_roles']==['owner'] and item['human_session_required'] and not item['legacy_token_allowed']
    assert path in json.loads((ROOT/'docs/07_interfaces/openapi_v1.json').read_text())['paths']
    lab=(ROOT/'ui/web/src/pages/ModelLabView.ts').read_text()
    settings=(ROOT/'ui/web/src/pages/SettingsView.ts').read_text()
    assert 'renderOllamaCandidatePanel' in lab and 'renderLmstudioCandidatePanel' in lab
    assert 'renderOllamaCandidatePanel' not in settings
    assert "const providerSection=document.createElement('section')" in settings
    assert "href=\"/model-lab\"" in settings

def test_auth_and_csrf(tmp_path):
    from fastapi.testclient import TestClient
    from devpilot_core.interfaces.api.app import create_app
    from devpilot_core.identity.auth_models import CSRF_COOKIE_NAME
    url='/api/v1/settings/lmstudio/product-definition/candidate'
    c=TestClient(create_app(tmp_path,api_token='legacy-test'),base_url='http://127.0.0.1:8787')
    body={'case_id':'vision','model':'local-model','request_id':'e'*32,'execute':False}
    assert c.post(url,headers={'X-DevPilot-Token':'legacy-test'},json=body).status_code==401
    headers={'Origin':'http://127.0.0.1:5173'}
    assert c.post('/api/v1/auth/bootstrap/owner',headers=headers,json={'username':'owner','display_name':'Owner','password':'One-long-passphrase-r0204'}).status_code==201
    assert c.post(url,headers=headers,json=body).status_code==403
    root(tmp_path)
    resp=c.post(url,headers={**headers,'X-DevPilot-CSRF':c.cookies.get(CSRF_COOKIE_NAME)},json=body)
    assert resp.status_code==200,resp.text
    assert resp.json()['data']['status']=='DRY_RUN'
    assert not (tmp_path/'outputs').exists()
