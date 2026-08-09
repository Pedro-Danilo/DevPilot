from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from devpilot_core.application.workspace_edit_plan_service import WorkspaceEditPlanApplicationService, MAX_PROPOSAL_BYTES
from devpilot_core.application.workspace_documents_service import WorkspaceDocumentsApplicationService
from uoc004_fixtures import create_uoc004_workspace, snapshot, sha

ROOT=Path(__file__).resolve().parents[1]

def service(tmp_path:Path, monkeypatch:pytest.MonkeyPatch):
    ws=create_uoc004_workspace(tmp_path/'inventory-sales-local')
    monkeypatch.setenv('DEVPILOT_ALLOWED_WORKSPACE_ROOTS',str(ws)); monkeypatch.setenv('DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT',str(ws))
    docs=WorkspaceDocumentsApplicationService(ROOT)
    listing=docs.list_documents(limit=100)
    by_path={n['relative_path']:n['document_id'] for n in listing.data['nodes'] if n.get('kind')=='document'}
    return WorkspaceEditPlanApplicationService(ROOT,documents=docs),ws,by_path

def test_markdown_plan_is_immutable_full_diff_and_zero_write(tmp_path:Path,monkeypatch:pytest.MonkeyPatch):
    svc,ws,ids=service(tmp_path,monkeypatch); path=ws/'docs/00_product/product_vision.md'; before=snapshot(ws); base=sha(path)
    proposed=path.read_text()+'\n## New section\n\nGoverned proposal.\n'
    result=svc.plan(document_id=ids['docs/00_product/product_vision.md'],document_sha_before=base,proposed_content=proposed)
    assert result.ok,[f.to_dict() for f in result.findings]
    plan=result.data['plan']; assert plan['document']['document_sha_before']==base; assert plan['diff']['truncated'] is False; assert '+## New section' in plan['diff']['content']
    assert plan['policy']['source_write_enabled'] is False; assert plan['patch_evidence']['executed'] is False; assert snapshot(ws)==before
    status=svc.get_plan(plan_id=plan['plan_id']); assert status.ok
    recheck=svc.recheck(plan_id=plan['plan_id'],plan_hash=plan['plan_hash']); assert recheck.ok and recheck.data['summary']['stale'] is False

def test_json_yaml_and_disallowed_txt(tmp_path:Path,monkeypatch:pytest.MonkeyPatch):
    svc,ws,ids=service(tmp_path,monkeypatch)
    jp=ws/'docs/01_requirements/requirements.json'; r=svc.plan(document_id=ids['docs/01_requirements/requirements.json'],document_sha_before=sha(jp),proposed_content='{"requirements":[{"id":"FR-001","title":"Changed"}]}\n'); assert r.ok
    yp=ws/'docs/02_architecture/config.yaml'; y=svc.plan(document_id=ids['docs/02_architecture/config.yaml'],document_sha_before=sha(yp),proposed_content='name: inventory-sales-local\nmode: governed\n'); assert y.ok
    tp=ws/'docs/notes.txt'; blocked=svc.plan(document_id=ids['docs/notes.txt'],document_sha_before=sha(tp),proposed_content='changed\n'); assert not blocked.ok

def test_blocks_stale_invalid_frontmatter_empty_secret_and_large(tmp_path:Path,monkeypatch:pytest.MonkeyPatch):
    svc,ws,ids=service(tmp_path,monkeypatch); p=ws/'docs/00_product/product_vision.md'; did=ids['docs/00_product/product_vision.md']; base=sha(p); original=p.read_text()
    p.write_text(original+'changed externally\n'); stale=svc.plan(document_id=did,document_sha_before=base,proposed_content=original+'proposal\n'); assert not stale.ok
    newbase=sha(p); invalid=svc.plan(document_id=did,document_sha_before=newbase,proposed_content='---\ndoc_id: [bad\n---\n# X\n'); assert not invalid.ok
    empty=svc.plan(document_id=did,document_sha_before=newbase,proposed_content=p.read_text()); assert not empty.ok
    secret=svc.plan(document_id=did,document_sha_before=newbase,proposed_content=p.read_text()+'\napi_key = sk-123456789012345678901234\n'); assert not secret.ok
    large=svc.plan(document_id=did,document_sha_before=newbase,proposed_content='x'*(MAX_PROPOSAL_BYTES+1)); assert not large.ok

def test_recheck_blocks_document_modified_after_plan_and_expired_plan(tmp_path:Path,monkeypatch:pytest.MonkeyPatch):
    svc,ws,ids=service(tmp_path,monkeypatch); p=ws/'docs/00_product/product_vision.md'; base=sha(p)
    result=svc.plan(document_id=ids['docs/00_product/product_vision.md'],document_sha_before=base,proposed_content=p.read_text()+'\nnew\n'); plan=result.data['plan']
    p.write_text(p.read_text()+'\nexternal\n'); stale=svc.recheck(plan_id=plan['plan_id'],plan_hash=plan['plan_hash']); assert not stale.ok; assert stale.data['summary']['stale'] is True
    svc._plans[plan['plan_id']]['expires_at']=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat().replace('+00:00','Z')
    expired=svc.get_plan(plan_id=plan['plan_id']); assert not expired.ok


def test_blocks_deleted_document_and_unknown_out_of_scope_id(tmp_path:Path,monkeypatch:pytest.MonkeyPatch):
    svc,ws,ids=service(tmp_path,monkeypatch)
    path=ws/'docs/00_product/product_vision.md'
    did=ids['docs/00_product/product_vision.md']
    base=sha(path)
    proposed=path.read_text()+'\nproposal\n'
    path.unlink()
    deleted=svc.plan(document_id=did,document_sha_before=base,proposed_content=proposed)
    assert not deleted.ok
    outside=svc.plan(document_id='doc_not_registered_outside_scope',document_sha_before=base,proposed_content=proposed)
    assert not outside.ok
