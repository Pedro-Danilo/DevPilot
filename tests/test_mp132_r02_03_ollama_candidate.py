from pathlib import Path
from types import SimpleNamespace
import json,uuid,pytest
from devpilot_core.generation.ollama_product_definition import (
    OllamaProductDefinitionEvaluation,LocalCandidateBlock,parse_model_json,load_case)
from devpilot_core.modeling.providers import ProviderRegistry

ROOT=Path(__file__).resolve().parents[1]
GOOD=lambda ref:json.dumps({'title':'Visión de proyecto sintético','content':'# Visión\nSe permitirá registrar solicitud y proteger la privacidad mediante permisos para uso local. Incluye verificación.' ,'evidence_refs':[ref]})

def test_dataset_three_stages_and_two_negative():
 import json
 d=json.loads((ROOT/'evals/fixtures/r02_03_product_definition.json').read_text())
 assert len(d['cases'])==3 and len(d['negative_cases'])==2
 assert {c['stage'] for c in d['cases']}=={'product-vision','scope','requirements'}
 for c in d['cases']:assert parse_model_json(GOOD(c['evidence_ref']),expected_ref=c['evidence_ref'])

def test_schema_json_invalid_and_grounding_rejected():
 with pytest.raises(LocalCandidateBlock,match='PARSE_BLOCKED'):parse_model_json('{not json}',expected_ref='fixture:x')
 with pytest.raises(LocalCandidateBlock,match='UNSUPPORTED_REFERENCE_BLOCK'):parse_model_json(GOOD('fixture:inventado'),expected_ref='fixture:x')
 with pytest.raises(LocalCandidateBlock,match='SCHEMA_BLOCKED'):parse_model_json('{"title":"a"}',expected_ref='fixture:x')

@pytest.fixture
def root(tmp_path):
 (tmp_path/'evals/fixtures').mkdir(parents=True)
 (tmp_path/'evals/fixtures/r02_03_product_definition.json').write_bytes((ROOT/'evals/fixtures/r02_03_product_definition.json').read_bytes())
 return tmp_path

def test_dry_run_zero_provider_calls(root):
 class NoCall:
  def __init__(self,**kw):raise AssertionError('NETWORK_FORBIDDEN')
 result=OllamaProductDefinitionEvaluation(root,adapter_factory=NoCall).run(case_id='vision',model='qwen2.5:3b-instruct',request_id='a'*32)
 assert result['status']=='DRY_RUN' and result['network_calls']==0 and not (root/'outputs').exists()

class FakeAdapter:
 calls=0
 def __init__(self,**kwargs):pass
 def health(self):return SimpleNamespace(ok=True,data={'models':['qwen2.5:3b-instruct']})
 def _post_json(self,path,payload,task):
  FakeAdapter.calls+=1
  assert path=='/api/generate' and payload['format']=='json' and payload['stream'] is False
  marker=payload['prompt'].split('evidence_refs')[1]
  ref='fixture:loan-business-need-v1' if 'product-vision' in payload['prompt'] else 'fixture:loan-vision-v1' if 'scope' in payload['prompt'] else 'fixture:loan-scope-v1'
  return SimpleNamespace(ok=True,metadata={'response':GOOD(ref),'prompt_eval_count':23,'eval_count':42})

def test_real_one_shot_persists_and_replays(root):
 FakeAdapter.calls=0
 app=OllamaProductDefinitionEvaluation(root,adapter_factory=FakeAdapter)
 result=app.run(case_id='vision',model='qwen2.5:3b-instruct',request_id='b'*32,execute=True)
 assert result['status']=='REAL_CANDIDATE_GENERATED_UNREVIEWED' and result['candidate']['origin']['provider_class']=='local-model'
 assert result['external_api_calls']==0 and result['source_writes']==0 and FakeAdapter.calls==1
 assert (root/'outputs/mp132_r02_03/candidates'/('b'*32+'.json')).is_file()
 assert app.run(case_id='vision',model='qwen2.5:3b-instruct',request_id='b'*32,execute=True)['replayed']
 assert FakeAdapter.calls==1
 with pytest.raises(LocalCandidateBlock,match='REQUEST_ID_CONFLICT'):
  app.run(case_id='scope',model='qwen2.5:3b-instruct',request_id='b'*32,execute=True)

def test_model_missing_blocks_without_post(root):
 class Missing(FakeAdapter):
  def health(self):return SimpleNamespace(ok=True,data={'models':[]})
  def _post_json(self,*a,**kw):raise AssertionError('NO_NETWORK_POST')
 with pytest.raises(LocalCandidateBlock,match='MODEL_NOT_INSTALLED'):
  OllamaProductDefinitionEvaluation(root,adapter_factory=Missing).run(case_id='vision',model='qwen2.5:3b-instruct',request_id='c'*32,execute=True)

def test_remote_endpoint_blocks_before_adapter(root,monkeypatch):
 orig=ProviderRegistry.load(root).get('ollama')
 from dataclasses import replace
 class FakeReg:
  semantic_valid=True
  def get(self,pid):return replace(orig,endpoint='https://example.org')
 monkeypatch.setattr('devpilot_core.generation.ollama_product_definition.ProviderRegistry.load',lambda *args:FakeReg())
 with pytest.raises(LocalCandidateBlock,match='LOOPBACK_POLICY_BLOCK'):
  OllamaProductDefinitionEvaluation(root,adapter_factory=lambda **k: (_ for _ in ()).throw(AssertionError('NETWORK'))).run(case_id='vision',model='qwen2.5:3b-instruct',request_id='d'*32,execute=True)

def test_route_registered_and_rbac():
 docs=json.loads((ROOT/'docs/07_interfaces/openapi_v1.json').read_text())
 path='/api/v1/settings/ollama/product-definition/candidate'
 assert path in docs['paths']
 policies=json.loads((ROOT/'.devpilot/identity/server_rbac_policy_catalog.json').read_text())['route_policies']
 r=next(x for x in policies if x['path']==path)
 assert r['allowed_roles']==['owner'] and r['human_session_required'] and not r['legacy_token_allowed']
 assert r['deny_by_default']

def test_http_owner_csrf_and_dry_run_guard(tmp_path):
 from fastapi.testclient import TestClient
 from devpilot_core.interfaces.api.app import create_app
 from devpilot_core.identity.auth_models import CSRF_COOKIE_NAME
 route='/api/v1/settings/ollama/product-definition/candidate'
 headers={'Origin':'http://127.0.0.1:5173'}
 c=TestClient(create_app(tmp_path,api_token='legacy-only'),base_url='http://127.0.0.1:8787')
 body={'case_id':'vision','model':'qwen2.5:3b-instruct','request_id':'e'*32,'execute':False}
 assert c.post(route,headers={'X-DevPilot-Token':'legacy-only'},json=body).status_code==401
 assert c.post('/api/v1/auth/bootstrap/owner',headers=headers,json={'username':'owner','display_name':'Owner','password':'One-long-passphrase-r0203'}).status_code==201
 assert c.post(route,headers=headers,json=body).status_code==403
 (tmp_path/'evals/fixtures').mkdir(parents=True)
 (tmp_path/'evals/fixtures/r02_03_product_definition.json').write_bytes((ROOT/'evals/fixtures/r02_03_product_definition.json').read_bytes())
 allowed=c.post(route,headers={**headers,'X-DevPilot-CSRF':c.cookies.get(CSRF_COOKIE_NAME)},json=body)
 assert allowed.status_code==200,allowed.text
 assert allowed.json()['data']['status']=='DRY_RUN'
 assert not (tmp_path/'outputs').exists()
