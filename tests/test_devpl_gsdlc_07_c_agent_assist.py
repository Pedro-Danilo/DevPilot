from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from devpilot_core.application import ApplicationService, AuthApplicationService
from devpilot_core.application.agent_assist_service import AgentAssistApplicationService
from devpilot_core.application.artifact_draft_service import ArtifactDraftApplicationService
from devpilot_core.application.artifact_import_service import ArtifactImportApplicationService
from devpilot_core.application.workspace_documents_service import WorkspaceDocumentsApplicationService
from devpilot_core.identity.auth_models import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, resolve_route_policy

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct horse battery staple"
ORIGIN = {"Origin": "http://127.0.0.1:5173"}


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / f"gsdlc07c-{tmp_path.name}"
    docs = root / "docs"; docs.mkdir(parents=True)
    (docs / "requirements.md").write_text("# Requirements\n\nInitial governed source.\n", encoding="utf-8")
    (docs / "architecture.json").write_text('{"version": 1}\n', encoding="utf-8")
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(root))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(root))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)
    yield root
    token = hashlib.sha256(root.name.encode("utf-8")).hexdigest()[:20]
    shutil.rmtree(ROOT / "outputs" / "drafts" / "gsdlc_04_b" / token, ignore_errors=True)
    shutil.rmtree(ROOT / "outputs" / "imports" / "gsdlc_04_c" / token, ignore_errors=True)
    shutil.rmtree(ROOT / "outputs" / "agent_assist" / "gsdlc_07_c", ignore_errors=True)


def services():
    docs = WorkspaceDocumentsApplicationService(ROOT)
    drafts = ArtifactDraftApplicationService(ROOT, documents=docs)
    imports = ArtifactImportApplicationService(ROOT, documents=docs)
    assist = AgentAssistApplicationService(ROOT, documents=docs, drafts=drafts, imports=imports)
    return docs, drafts, imports, assist


def document(docs: WorkspaceDocumentsApplicationService, path="docs/requirements.md") -> dict:
    listed = docs.list_documents(limit=100); assert listed.ok, listed.to_dict()
    node = next(x for x in listed.data["nodes"] if x.get("relative_path") == path)
    read = docs.read_document(node["document_id"]); assert read.ok, read.to_dict()
    return read.data["document"]


def plan(assist: AgentAssistApplicationService, doc: dict, **overrides):
    payload = dict(document_id=doc["document_id"], operation="improve", mode="mock", instruction="Improve clarity", current_content=doc["content"], expected_source_sha256=doc["sha256"], expected_revision_sha256=None, actor="local-owner", actor_role="owner", session_principal="local-owner")
    payload.update(overrides)
    return assist.plan(**payload)


def test_mock_plan_exposes_route_context_cost_and_limits_before_run(workspace: Path):
    docs, _, _, assist = services(); doc = document(docs)
    result = plan(assist, doc)
    assert result.ok, result.to_dict(); value = result.data["plan"]
    assert value["runtime"]["mode"] == "mock" and value["runtime"]["human_review_required"] is True
    assert value["model_route"]["provider_id"] and value["model_route"]["model_id"] and value["model_route"]["access_route_id"]
    assert value["context"]["status"] == "grounded" and value["context"]["sources"]
    assert "cost" in value and value["limits"]["max_steps"] >= 1
    assert value["model_route"]["tool_authority_granted"] is False and value["agent"]["can_approve"] is False


def test_fake_local_run_is_deterministic_untrusted_and_source_unchanged(workspace: Path):
    docs, _, _, assist = services(); doc = document(docs); before=(workspace/'docs/requirements.md').read_bytes()
    planned=plan(assist,doc,mode="fake-local"); assert planned.ok
    p=planned.data["plan"]; run=assist.run(plan_id=p["plan_id"],plan_sha256=p["plan_sha256"])
    assert run.ok, run.to_dict(); proposal=run.data["proposal"]
    assert proposal["status"] == "PROPOSED" and proposal["untrusted_output"] is True and proposal["human_review_required"] is True
    assert proposal["diff"] and proposal["source_mutations_performed"] is False and proposal["workspace_writes_performed"] is False
    assert (workspace/'docs/requirements.md').read_bytes()==before


def test_invalid_structured_output_and_insufficient_evidence_fail_closed(workspace: Path, monkeypatch: pytest.MonkeyPatch):
    docs, _, _, assist=services(); doc=document(docs); planned=plan(assist,doc); assert planned.ok
    p=planned.data['plan']; invalid=assist.run(plan_id=p['plan_id'],plan_sha256=p['plan_sha256'],simulate_invalid_output=True)
    assert invalid.ok is False and any(f.id=='GSDLC07C_STRUCTURED_OUTPUT_BLOCK' for f in invalid.findings)
    original = __import__('devpilot_core.application.agent_assist_service',fromlist=['ContextPackV2Builder']).ContextPackV2Builder.build
    def insufficient(self):
        r=original(self)
        if r.ok: r.data['context_pack']['status']='insufficient-evidence'; r.data['summary']['status']='insufficient-evidence'
        return r
    monkeypatch.setattr('devpilot_core.application.agent_assist_service.ContextPackV2Builder.build', insufficient)
    blocked=plan(assist,doc,instruction='zzzzuniquetermthatdoesnotexist')
    assert blocked.ok
    bp=blocked.data['plan']; run=assist.run(plan_id=bp['plan_id'],plan_sha256=bp['plan_sha256'])
    assert run.ok is False and any(f.id=='GSDLC07C_INSUFFICIENT_EVIDENCE_BLOCK' for f in run.findings)


def test_accept_reject_modify_preserve_human_review_and_draft_history(workspace: Path):
    docs, drafts, _, assist=services(); doc=document(docs); source_before=(workspace/'docs/requirements.md').read_bytes()
    # ACCEPT creates DRAFT revision with provenance.
    pp=plan(assist,doc); p=pp.data['plan']; rr=assist.run(plan_id=p['plan_id'],plan_sha256=p['plan_sha256']); prop=rr.data['proposal']
    accepted=assist.decide(proposal_id=prop['proposal_id'],proposal_sha256=prop['proposal_sha256'],decision='ACCEPT',actor='local-owner',actor_role='owner',session_principal='local-owner')
    assert accepted.ok and accepted.data['summary']['draft_revision_persisted'] is True
    draft=accepted.data['draft']; assert draft['lifecycle_state']=='DRAFT'; assert draft['revisions'][-1]['agent_provenance']['proposal_id']==prop['proposal_id']
    assert accepted.data['decision']['approved_state_granted'] is False and accepted.data['decision']['frozen_state_granted'] is False
    # REJECT does not add a revision.
    current=draft['current_revision_sha256']; content=draft['revisions'][-1]['content']
    pp2=plan(assist,doc,current_content=content,expected_revision_sha256=current,operation='critique'); p2=pp2.data['plan']; rr2=assist.run(plan_id=p2['plan_id'],plan_sha256=p2['plan_sha256']); prop2=rr2.data['proposal']
    before_count=len(drafts.get(document_id=doc['document_id']).data['draft']['revisions'])
    rejected=assist.decide(proposal_id=prop2['proposal_id'],proposal_sha256=prop2['proposal_sha256'],decision='REJECT',actor='local-owner',actor_role='owner',session_principal='local-owner')
    assert rejected.ok and rejected.data['summary']['draft_revision_persisted'] is False
    assert len(drafts.get(document_id=doc['document_id']).data['draft']['revisions'])==before_count
    # MODIFY creates a new DRAFT revision, never source approval.
    current_store=drafts.get(document_id=doc['document_id']).data['draft']; current_sha=current_store['current_revision_sha256']; current_content=current_store['revisions'][-1]['content']
    pp3=plan(assist,doc,current_content=current_content,expected_revision_sha256=current_sha); p3=pp3.data['plan']; rr3=assist.run(plan_id=p3['plan_id'],plan_sha256=p3['plan_sha256']); prop3=rr3.data['proposal']
    modified=current_content+'\nHuman refinement.\n'
    decision=assist.decide(proposal_id=prop3['proposal_id'],proposal_sha256=prop3['proposal_sha256'],decision='MODIFY',modified_content=modified,actor='local-owner',actor_role='owner',session_principal='local-owner')
    assert decision.ok and decision.data['draft']['revisions'][-1]['content']==modified
    assert decision.data['draft']['revisions'][-1]['agent_provenance']['decision']=='MODIFY'
    assert (workspace/'docs/requirements.md').read_bytes()==source_before


def test_manual_route_still_works_without_agent_provenance(workspace: Path):
    docs,drafts,_,_=services(); doc=document(docs)
    saved=drafts.save(document_id=doc['document_id'],content='manual draft',expected_source_sha256=doc['sha256'],expected_revision_sha256=None,actor='local-owner',actor_role='owner',session_principal='local-owner',event='SAVE')
    assert saved.ok and saved.data['draft']['revisions'][-1]['agent_provenance'] is None


def test_hidden_model_or_cost_is_not_possible_in_plan_schema(workspace: Path):
    docs,_,_,assist=services(); doc=document(docs); result=plan(assist,doc); assert result.ok
    p=result.data['plan']; assert p['model_route']['provider_id'] and p['model_route']['model_id'] and p['model_route']['access_route_id']
    assert isinstance(p['cost'],dict) and 'cost_state' in p['cost'] and 'cost_usd' in p['cost']


def test_route_security_registry_and_ui_contract_are_explicit():
    expected={
      ('POST','/api/v1/workspace/artifact-assist/documents/{document_id}/plan'),
      ('POST','/api/v1/workspace/artifact-assist/plans/{plan_id}/run'),
      ('POST','/api/v1/workspace/artifact-assist/proposals/{proposal_id}/decision'),
      ('GET','/api/v1/workspace/artifact-assist/proposals/{proposal_id}'),
    }
    assert expected <= set(API_ROUTE_POLICIES)
    assert resolve_route_policy('POST','/api/v1/workspace/artifact-assist/documents/doc_x/plan').operation=='workspace.artifact_assist.plan'
    assert resolve_route_policy('POST','/api/v1/workspace/artifact-assist/plans/aip_x/run').operation=='workspace.artifact_assist.run'
    assert resolve_route_policy('POST','/api/v1/workspace/artifact-assist/proposals/aiprop_x/decision').operation=='workspace.artifact_assist.decision'
    assert resolve_route_policy('GET','/api/v1/workspace/artifact-assist/proposals/aiprop_x').operation=='workspace.artifact_assist.get'
    api=json.loads((ROOT/'.devpilot/interfaces/api_route_contract_registry.json').read_text()); rb=json.loads((ROOT/'.devpilot/identity/server_rbac_policy_catalog.json').read_text()); ui=json.loads((ROOT/'.devpilot/interfaces/ui_route_contract_registry.json').read_text())
    ids={x['route_id'] for x in api['routes'] if x['route_id'].startswith('api.workspace.artifact-assist.')}; assert len(ids)==4
    policies={x['route_id']:x for x in rb['route_policies']}; assert all(policies[x]['human_session_required'] and not policies[x]['legacy_token_allowed'] for x in ids)
    route=next(x for x in ui['routes'] if x['route_id']=='ui.workspace-documents'); assert ids <= set(route['allowed_api_routes']) and 'ui/web/src/components/ArtifactAIPanel.ts' in route['source_files']


def test_artifact_ai_panel_is_plan_first_diff_review_and_no_approval_button():
    panel=(ROOT/'ui/web/src/components/ArtifactAIPanel.ts').read_text(encoding='utf-8')
    view=(ROOT/'ui/web/src/pages/WorkspaceDocumentsView.ts').read_text(encoding='utf-8')
    assert '1 · Preparar PLAN' in panel and '2 · RUN hermético' in panel
    assert 'UNTRUSTED' in panel and 'DRAFT ONLY' in panel and 'APPROVED/FROZEN' in panel
    assert 'ACCEPT' in panel and 'REJECT' in panel and 'MODIFY' in panel and 'artifact-ai-diff' in panel
    assert '.innerHTML =' not in panel and '.innerHTML=' not in panel
    assert 'createArtifactAIPanel' in view and 'manualEditor, editPlanner, aiPanel' in view


def _human_client(tmp_path: Path) -> TestClient:
    store=LocalAuthStore(tmp_path/'auth'); auth=AuthApplicationService(tmp_path/'auth',store=store)
    client=TestClient(create_app(ROOT,api_token='legacy-gsdlc07c',auth_service=auth))
    boot=client.post('/api/v1/auth/bootstrap/owner',json={'username':'owner.local','display_name':'Local Owner','password':PASSWORD},headers=ORIGIN); assert boot.status_code==201,boot.text
    return client


def csrf(client: TestClient)->dict[str,str]: return {'Origin':ORIGIN['Origin'],CSRF_HEADER_NAME:str(client.cookies.get(CSRF_COOKIE_NAME))}


def test_api_agent_assist_requires_human_session_and_returns_plan(workspace: Path,tmp_path: Path):
    legacy=TestClient(create_app(ROOT,api_token='legacy-gsdlc07c'))
    listed=legacy.get('/api/v1/workspace/documents?limit=100',headers={'X-DevPilot-Token':'legacy-gsdlc07c'}); doc=next(x for x in listed.json()['data']['nodes'] if x.get('relative_path')=='docs/requirements.md')
    read=legacy.get(f"/api/v1/workspace/documents/{doc['document_id']}",headers={'X-DevPilot-Token':'legacy-gsdlc07c'}).json()['data']['document']
    body={'operation':'improve','mode':'mock','instruction':'Improve clarity','current_content':read['content'],'expected_source_sha256':read['sha256'],'expected_revision_sha256':None}
    blocked=legacy.post(f"/api/v1/workspace/artifact-assist/documents/{doc['document_id']}/plan",headers={'X-DevPilot-Token':'legacy-gsdlc07c'},json=body); assert blocked.status_code in {401,403}
    client=_human_client(tmp_path); response=client.post(f"/api/v1/workspace/artifact-assist/documents/{doc['document_id']}/plan",headers=csrf(client),json=body)
    assert response.status_code==200,response.text; assert response.json()['data']['plan']['runtime']['human_review_required'] is True
