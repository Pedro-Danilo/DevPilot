from pathlib import Path
from fastapi.testclient import TestClient
from devpilot_core.interfaces.api.app import create_app
ROOT=Path(__file__).resolve().parents[1]; TOKEN='uoc010-test-token'
def h(): return {'Authorization':f'Bearer {TOKEN}'}

def test_uoc010_ai_routes_require_token_and_expose_status_catalog() -> None:
    c=TestClient(create_app(root=ROOT,api_token=TOKEN)); assert c.get('/api/v1/ai/status').status_code==401
    for p in ['/api/v1/ai/status','/api/v1/ai/operations']:
        r=c.get(p,headers=h()); assert r.status_code==200 and r.json()['ok'] is True

def test_uoc010_rag_query_plan_and_unknown_operation_contract() -> None:
    c=TestClient(create_app(root=ROOT,api_token=TOKEN))
    body={'operation_id':'rag-query','workspace_id':'devpilot-local','parameters':{'query':'DevPilot','top_k':2,'index_source':'canonical'},'idempotency_key':'api-uoc010-rag'}
    r=c.post('/api/v1/ai/jobs/plan',headers=h(),json=body); assert r.status_code==200 and r.json()['ok'] is True
    x=c.post('/api/v1/ai/jobs/plan',headers=h(),json={**body,'operation_id':'free-tool','idempotency_key':'api-uoc010-block'}); assert x.status_code==200 and x.json()['exit_code']==2

def test_uoc010_external_api_provider_cannot_be_planned() -> None:
    c=TestClient(create_app(root=ROOT,api_token=TOKEN)); r=c.post('/api/v1/ai/jobs/plan',headers=h(),json={'operation_id':'agent-run','workspace_id':'devpilot-local','parameters':{'agent_id':'requirements.agent','task_id':'summarize-gaps','target_id':'requirements','provider_id':'openai','memory_opt_in':False},'idempotency_key':'api-uoc010-openai','approval_id':'APPROVAL-FAKE'})
    assert r.status_code==200 and r.json()['exit_code']==2 and 'External API' in r.json()['message']
