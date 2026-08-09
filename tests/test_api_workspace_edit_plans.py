from __future__ import annotations
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from devpilot_core.interfaces.api import create_app
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, API_TOKEN_HEADER
from devpilot_core.application.workspace_documents_service import WorkspaceDocumentsApplicationService
from uoc004_fixtures import create_uoc004_workspace, snapshot, sha
ROOT=Path(__file__).resolve().parents[1]; TOKEN='uoc004-test-token'

def client(tmp_path:Path,monkeypatch:pytest.MonkeyPatch,auth=True):
    ws=create_uoc004_workspace(tmp_path/'inventory-sales-local'); monkeypatch.setenv('DEVPILOT_ALLOWED_WORKSPACE_ROOTS',str(ws)); monkeypatch.setenv('DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT',str(ws))
    c=TestClient(create_app(ROOT,api_token=TOKEN));
    if auth:c.headers.update({API_TOKEN_HEADER:TOKEN})
    docs=WorkspaceDocumentsApplicationService(ROOT); listing=docs.list_documents(limit=100); ids={n['relative_path']:n['document_id'] for n in listing.data['nodes'] if n.get('kind')=='document'}
    return c,ws,ids

def test_api_plan_status_recheck_zero_write(tmp_path:Path,monkeypatch:pytest.MonkeyPatch):
    c,ws,ids=client(tmp_path,monkeypatch); before=snapshot(ws); p=ws/'docs/00_product/product_vision.md'
    response=c.post('/api/v1/workspace/edit-plans/plan',json={'operation':'workspace.edits.plan','payload':{'document_id':ids['docs/00_product/product_vision.md'],'document_sha_before':sha(p),'proposed_content':p.read_text()+'\nchange\n'},'dry_run':True})
    assert response.status_code==200,response.text; plan=response.json()['data']['plan']
    assert c.get(f"/api/v1/workspace/edit-plans/{plan['plan_id']}").status_code==200
    rr=c.post(f"/api/v1/workspace/edit-plans/{plan['plan_id']}/recheck",json={'operation':'workspace.edits.recheck','payload':{'plan_hash':plan['plan_hash']},'dry_run':True}); assert rr.status_code==200,rr.text
    assert snapshot(ws)==before

def test_api_security_and_operation_binding(tmp_path:Path,monkeypatch:pytest.MonkeyPatch):
    unauth,ws,ids=client(tmp_path,monkeypatch,False); p=ws/'docs/00_product/product_vision.md'; payload={'document_id':ids['docs/00_product/product_vision.md'],'document_sha_before':sha(p),'proposed_content':p.read_text()+'\nchange\n'}
    assert unauth.post('/api/v1/workspace/edit-plans/plan',json={'operation':'workspace.edits.plan','payload':payload}).status_code==401
    c,ws2,ids2=client(tmp_path/'b',monkeypatch,True); p2=ws2/'docs/00_product/product_vision.md'; mismatch=c.post('/api/v1/workspace/edit-plans/plan',json={'operation':'workspace.edits.recheck','payload':{'document_id':ids2['docs/00_product/product_vision.md'],'document_sha_before':sha(p2),'proposed_content':p2.read_text()+'\nchange\n'}}); assert mismatch.status_code in {400,403}

def test_uoc004_routes_have_explicit_policy_bindings():
    assert {('POST','/api/v1/workspace/edit-plans/plan'),('GET','/api/v1/workspace/edit-plans/{plan_id}'),('POST','/api/v1/workspace/edit-plans/{plan_id}/recheck')} <= set(API_ROUTE_POLICIES)
