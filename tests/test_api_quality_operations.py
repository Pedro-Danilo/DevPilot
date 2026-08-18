import json
from pathlib import Path
from fastapi.testclient import TestClient
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.approval.service import parse_scope
ROOT=Path(__file__).resolve().parents[1]; TOKEN='uoc009-test-token'
def h(): return {'Authorization':f'Bearer {TOKEN}'}
def test_uoc009_quality_routes_require_token_and_expose_catalog_baseline_impact() -> None:
    c=TestClient(create_app(root=ROOT,api_token=TOKEN)); assert c.get('/api/v1/quality/operations').status_code==401
    for path in ['/api/v1/quality/operations','/api/v1/quality/baseline']:
        r=c.get(path,headers=h()); assert r.status_code==200 and r.json()['ok'] is True
    r=c.post('/api/v1/quality/test-impact/plan',headers=h(),json={'changed_paths':['README.md']}); assert r.status_code==200 and r.json()['ok'] is True

def test_uoc009_quality_plan_rejects_unknown_operation_as_product_block() -> None:
    c=TestClient(create_app(root=ROOT,api_token=TOKEN)); r=c.post('/api/v1/quality/jobs/plan',headers=h(),json={'operation_id':'free-shell','workspace_id':'devpilot-local','parameters':{},'idempotency_key':'api-uoc009-unknown'}); assert r.status_code==200 and r.json()['exit_code']==2

def test_uoc009_quality_gate_approval_scope_contract_accepts_json_and_rejects_legacy_text() -> None:
    derived, findings=parse_scope('operation=quality-gate', tool_id='quality-gate.run', action='execute', subject='quality-gate')
    assert any(f.id=='APPROVAL_SCOPE_JSON_INVALID' for f in findings)
    scope=json.dumps({'operation_id':'quality-gate','workspace_id':'devpilot-local','source':'ui.quality'},sort_keys=True)
    parsed, findings=parse_scope(scope, tool_id='quality-gate.run', action='execute', subject='quality-gate')
    assert findings == []
    assert parsed['operation_id']=='quality-gate' and parsed['workspace_id']=='devpilot-local'
    c=TestClient(create_app(root=ROOT,api_token=TOKEN))
    token_only=c.post('/api/v1/approvals/request',headers=h(),json={'tool_id':'quality-gate.run','action':'execute','subject':'quality-gate','actor':'local-owner','reason':'legacy token must not become human authority','ttl_minutes':60,'scope':scope})
    assert token_only.status_code in {401,403}
    assert token_only.json()['findings'][0]['id'] in {'AUTH_HUMAN_SESSION_REQUIRED_BLOCK','RBAC_LEGACY_TOKEN_DENY'}
