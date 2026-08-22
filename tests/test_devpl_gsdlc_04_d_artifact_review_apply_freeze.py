from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from devpilot_core.application.approval_service import ApprovalApplicationService
from devpilot_core.application.artifact_draft_service import ArtifactDraftApplicationService
from devpilot_core.application.artifact_import_service import ArtifactImportApplicationService
from devpilot_core.application.artifact_review_service import ArtifactReviewApplicationService
from devpilot_core.application.auth_service import AuthApplicationService
from devpilot_core.application.workspace_documents_service import WorkspaceDocumentsApplicationService
from devpilot_core.application.workspace_edit_execution_service import WorkspaceEditExecutionApplicationService
from devpilot_core.application.workspace_edit_plan_service import WorkspaceEditPlanApplicationService, ZERO_SHA256
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, resolve_route_policy
from devpilot_core.schemas import SchemaValidator

ROOT=Path(__file__).resolve().parents[1]
PASSWORD='TestOwnerPassword!2026'


def _copy_platform(tmp_path:Path)->Path:
    platform=tmp_path/'platform'
    shutil.copytree(ROOT/'.devpilot',platform/'.devpilot',ignore=shutil.ignore_patterns('*.db','*.db-*','outputs','__pycache__'))
    for rel in ['docs/schemas','docs/validation']:
        shutil.copytree(ROOT/rel,platform/rel)
    return platform


@pytest.fixture
def env(tmp_path:Path,monkeypatch:pytest.MonkeyPatch):
    platform=_copy_platform(tmp_path)
    ws=tmp_path/'workspace';(ws/'docs').mkdir(parents=True);(ws/'.devpilot').mkdir()
    (ws/'.devpilot/project.yaml').write_text('project_id: gsdlc04d-fixture\n',encoding='utf-8')
    (ws/'docs/existing.md').write_text('# Existing\n\nApproved existing source.\n',encoding='utf-8')
    subprocess.run(['git','init','-q'],cwd=ws,check=True);subprocess.run(['git','config','user.email','fixture@example.invalid'],cwd=ws,check=True);subprocess.run(['git','config','user.name','Fixture'],cwd=ws,check=True);subprocess.run(['git','add','.'],cwd=ws,check=True);subprocess.run(['git','commit','-qm','baseline'],cwd=ws,check=True)
    control=tmp_path/'control';monkeypatch.setenv('DEVPILOT_ALLOWED_WORKSPACE_ROOTS',str(ws));monkeypatch.setenv('DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT',str(ws));monkeypatch.setenv('DEVPILOT_UOC005_CONTROL_ROOT',str(control));monkeypatch.delenv('DEVPILOT_UI_WORKSPACE_REGISTRY_PATH',raising=False)
    auth=AuthApplicationService(platform);issue=auth.bootstrap_owner(username='owner.local',display_name='Local Owner',password=PASSWORD)
    docs=WorkspaceDocumentsApplicationService(platform);plans=WorkspaceEditPlanApplicationService(platform,documents=docs);execs=WorkspaceEditExecutionApplicationService(platform,documents=docs,plans=plans,approval_auth_store=auth.store);drafts=ArtifactDraftApplicationService(platform,documents=docs);imports=ArtifactImportApplicationService(platform,documents=docs);reviews=ArtifactReviewApplicationService(platform,documents=docs,drafts=drafts,imports=imports,plans=plans,executions=execs)
    return platform,ws,control,auth,issue,docs,plans,execs,imports,reviews


def valid_content(title='Review')->str:
    return f'''---\ndoc_id: "GSDLC-04-D-FIXTURE-{title.upper()}"\ntitle: "{title}"\nstatus: "draft"\nversion: "1.0.0"\nowner: "owner.local"\nupdated: "2026-08-22"\napproval: "pending"\n---\n# {title}\n\nThis governed artifact contains enough deterministic content for validation, review, approval, atomic apply and freeze acceptance.\n'''


def make_review(env, destination='docs/new.md', content=None):
    platform,ws,control,auth,issue,docs,plans,execs,imports,reviews=env
    actor=issue.context.principal.actor_id; role=issue.context.principal.roles[0]
    content=content or valid_content()
    kw=dict(source_type='PASTE',destination_path=destination,actor=actor,actor_role=role,session_principal=actor,text_content=content)
    preview=imports.preview(**kw);assert preview.ok,preview.to_dict()
    persisted=imports.persist(**kw,expected_preview_sha256=preview.data['preview']['preview_sha256']);assert persisted.ok,persisted.to_dict()
    started=reviews.start_import(import_id=persisted.data['import']['import_id'],actor=actor,actor_role=role,session_principal=actor)
    return started,persisted,actor,role


def approve(platform:Path,auth:AuthApplicationService,issue,approval_id:str):
    r=ApprovalApplicationService(platform,auth_store=auth.store).decide_authenticated(approval_id=approval_id,decision='approved',principal=issue.context.principal,session=issue.context,caller_actor=None,reason='GSDLC-04-D fixture approval')
    assert r.ok,r.to_dict()


def test_import_review_builds_deterministic_create_plan_and_navigable_contract(env):
    started,persisted,actor,role=make_review(env)
    assert started.ok,started.to_dict(); r=started.data['review']; plan=r['plan']
    assert r['status']=='APPROVAL_REQUIRED';assert plan['document']['operation']=='create';assert plan['document']['document_sha_before']==ZERO_SHA256
    assert plan['plan_hash']==started.data['plan']['plan_hash'];assert '+# Review' in plan['diff']['content'];assert r['validation']['profile_id']=='generic-markdown';assert r['findings']==[]
    # 04-C evidence remains a historical DRAFT record; promotion lives in successor review state.
    fresh=env[-2].get(import_id=persisted.data['import']['import_id']);assert fresh.ok and fresh.data['import']['lifecycle_state']=='DRAFT'


def test_invalid_artifact_stops_in_findings_without_plan(env):
    started,_,_,_=make_review(env,destination='docs/bad.md',content='# Missing frontmatter\n')
    assert not started.ok; r=started.data['review'];assert r['status']=='FINDINGS';assert r['plan'] is None;assert any(x['line'] or x['section'] for x in r['findings'])


def test_stale_create_preimage_blocks_before_source_write(env):
    started,_,actor,_=make_review(env,destination='docs/stale.md');assert started.ok
    _,ws,_,_,_,_,plans,execs,_,_=env; plan=started.data['plan'];(ws/'docs/stale.md').write_text('external\n',encoding='utf-8')
    check=plans.recheck(plan_id=plan['plan_id'],plan_hash=plan['plan_hash']);assert not check.ok
    req=execs.request_apply_approval(plan_id=plan['plan_id'],plan_hash=plan['plan_hash'],actor=actor,reason='stale should block')
    assert not req.ok;assert (ws/'docs/stale.md').read_text()=='external\n'


def test_exact_approval_apply_and_freeze_new_artifact(env):
    started,_,actor,role=make_review(env,destination='docs/frozen.md');assert started.ok
    platform,ws,_,auth,issue,_,_,execs,_,reviews=env; plan=started.data['plan'];review_id=started.data['review']['review_id']
    absent=execs.apply(plan_id=plan['plan_id'],plan_hash=plan['plan_hash'],approval_id='',actor=actor);assert not absent.ok and not (ws/'docs/frozen.md').exists()
    req=execs.request_apply_approval(plan_id=plan['plan_id'],plan_hash=plan['plan_hash'],actor=actor,reason='Approve governed artifact');assert req.ok
    aid=req.data['approval']['approval_id'];approve(platform,auth,issue,aid)
    applied=execs.apply(plan_id=plan['plan_id'],plan_hash=plan['plan_hash'],approval_id=aid,actor=actor);assert applied.ok,applied.to_dict();assert (ws/'docs/frozen.md').is_file()
    schema=SchemaValidator(ROOT).validate_payload(schema='ArtifactApplyExecutionGSDLC04D',payload=applied.data['execution'],instance_label='gsdlc04d-create-execution');assert schema.ok,schema.to_dict()
    frozen=reviews.freeze(review_id=review_id,execution_id=applied.data['execution']['execution_id'],actor=actor,actor_role=role,session_principal=actor);assert frozen.ok,frozen.to_dict();assert frozen.data['review']['status']=='FROZEN';assert frozen.data['freeze_record']['approved_sha256']==hashlib.sha256((ws/'docs/frozen.md').read_bytes()).hexdigest()
    again=reviews.freeze(review_id=review_id,execution_id=applied.data['execution']['execution_id'],actor=actor,actor_role=role,session_principal=actor);assert again.ok


def test_fault_after_create_write_compensates_to_absent_preimage(env):
    started,_,actor,_=make_review(env,destination='docs/fault.md');assert started.ok
    platform,ws,control,auth,issue,docs,plans,_,imports,reviews=env; plan=started.data['plan']
    fault=WorkspaceEditExecutionApplicationService(platform,documents=docs,plans=plans,approval_auth_store=auth.store,failure_injection_stage='after-write-before-validation')
    req=fault.request_apply_approval(plan_id=plan['plan_id'],plan_hash=plan['plan_hash'],actor=actor,reason='fault injection');assert req.ok
    aid=req.data['approval']['approval_id'];approve(platform,auth,issue,aid)
    result=fault.apply(plan_id=plan['plan_id'],plan_hash=plan['plan_hash'],approval_id=aid,actor=actor);assert not result.ok;assert result.data['execution']['status']=='rolled-back-automatic';assert not (ws/'docs/fault.md').exists();assert result.data['execution']['rollback']['restored_sha256']==ZERO_SHA256


def test_frozen_hash_drift_invalidates_successor_approval_state(env):
    started,_,actor,role=make_review(env,destination='docs/drift.md');platform,ws,_,auth,issue,_,_,execs,_,reviews=env;plan=started.data['plan'];rid=started.data['review']['review_id']
    req=execs.request_apply_approval(plan_id=plan['plan_id'],plan_hash=plan['plan_hash'],actor=actor,reason='freeze');aid=req.data['approval']['approval_id'];approve(platform,auth,issue,aid);applied=execs.apply(plan_id=plan['plan_id'],plan_hash=plan['plan_hash'],approval_id=aid,actor=actor);assert applied.ok
    assert reviews.freeze(review_id=rid,execution_id=applied.data['execution']['execution_id'],actor=actor,actor_role=role,session_principal=actor).ok
    (ws/'docs/drift.md').write_text((ws/'docs/drift.md').read_text()+"\nexternal edit\n",encoding='utf-8')
    rec=reviews.reconcile(review_id=rid,actor=actor,actor_role=role,session_principal=actor);assert rec.ok;assert rec.data['review']['status']=='REVALIDATION_REQUIRED';assert rec.data['review']['approval_valid'] is False


def test_route_security_contracts_for_review_are_explicit():
    routes={
      ('POST','/api/v1/workspace/artifact-reviews/imports/imp_x/start'):'workspace.artifact_reviews.start_import',
      ('POST','/api/v1/workspace/artifact-reviews/documents/doc_x/start'):'workspace.artifact_reviews.start_document',
      ('GET','/api/v1/workspace/artifact-reviews/arev_x'):'workspace.artifact_reviews.status',
      ('POST','/api/v1/workspace/artifact-reviews/arev_x/freeze'):'workspace.artifact_reviews.freeze',
      ('POST','/api/v1/workspace/artifact-reviews/arev_x/reconcile'):'workspace.artifact_reviews.reconcile',
    }
    for (method,path),operation in routes.items():
        policy=resolve_route_policy(method,path);assert policy is not None and policy.operation==operation
    assert len([x for x in API_ROUTE_POLICIES.values() if 'artifact_reviews' in x.operation])==5


def test_ui_review_flow_has_targeted_handoff_and_no_direct_authority():
    text=(ROOT/'ui/web/src/components/ArtifactReviewFlow.ts').read_text(encoding='utf-8')
    assert 'Validar DRAFT' in text and 'Solicitar approval' in text and 'Aplicar cambio aprobado' in text and 'Freeze hash aprobado' in text
    assert 'handoff=artifact-review' in text and 'showApproval' in text
    assert 'armApprovalCenterArtifactReviewHandoff' in text
    assert 'decideApproval' not in text and '.innerHTML' not in text
    assert 'ArtifactProfile' in text and 'diff completo' in text


def test_wrong_role_freeze_and_approval_reuse_after_drift_are_blocked(env):
    started,_,actor,role=make_review(env,destination='docs/reuse.md');assert started.ok
    platform,ws,_,auth,issue,_,_,execs,_,reviews=env;plan=started.data['plan'];rid=started.data['review']['review_id']
    req=execs.request_apply_approval(plan_id=plan['plan_id'],plan_hash=plan['plan_hash'],actor=actor,reason='exact binding');assert req.ok
    aid=req.data['approval']['approval_id'];approve(platform,auth,issue,aid)
    applied=execs.apply(plan_id=plan['plan_id'],plan_hash=plan['plan_hash'],approval_id=aid,actor=actor);assert applied.ok
    wrong=reviews.freeze(review_id=rid,execution_id=applied.data['execution']['execution_id'],actor=actor,actor_role='viewer',session_principal=actor);assert not wrong.ok
    frozen=reviews.freeze(review_id=rid,execution_id=applied.data['execution']['execution_id'],actor=actor,actor_role=role,session_principal=actor);assert frozen.ok
    (ws/'docs/reuse.md').write_text((ws/'docs/reuse.md').read_text(encoding='utf-8')+'\nexternal drift\n',encoding='utf-8')
    reuse=execs.apply(plan_id=plan['plan_id'],plan_hash=plan['plan_hash'],approval_id=aid,actor=actor);assert not reuse.ok
    assert reuse.findings and (ws/'docs/reuse.md').read_text(encoding='utf-8').endswith('external drift\n')
    reconciled=reviews.reconcile(review_id=rid,actor=actor,actor_role=role,session_principal=actor);assert reconciled.ok
    assert reconciled.data['review']['status']=='REVALIDATION_REQUIRED' and reconciled.data['review']['approval_valid'] is False


def test_ui_and_rbac_registries_bind_artifact_review_to_server_authority():
    ui=json.loads((ROOT/'.devpilot/interfaces/ui_capability_registry.json').read_text(encoding='utf-8'))
    route=next(x for x in ui['ui_routes'] if x['route_id']=='ui.workspace-documents')
    expected={
      'api.workspace.artifact-reviews.import-start','api.workspace.artifact-reviews.document-start','api.workspace.artifact-reviews.status',
      'api.workspace.artifact-reviews.freeze','api.workspace.artifact-reviews.reconcile','api.workspace.edit-plans.apply'
    }
    assert expected.issubset(set(route.get('allowed_api_route_ids',[])))
    cap=next(x for x in route['native_capabilities'] if x.get('capability_id')=='ui.workspace-documents.artifact-review')
    assert cap['source_write_engine'].startswith('UOC-005') and cap['targeted_approval_handoff'] is True
    rbac=json.loads((ROOT/'.devpilot/identity/server_rbac_policy_catalog.json').read_text(encoding='utf-8'))
    rows=rbac.get('routes') or rbac.get('policies') or rbac.get('route_policies') or []
    matched=[x for x in rows if isinstance(x,dict) and 'artifact-reviews' in str(x.get('path',''))]
    assert len(matched)==5 and all(x.get('human_session_required') is True and x.get('deny_by_default') is True for x in matched)
    sensitive=json.loads((ROOT/'.devpilot/approval/sensitive_action_catalog.json').read_text(encoding='utf-8'))
    assert 'filesystem.workspace_document_apply' in json.dumps(sensitive)

def test_browser_approval_transport_uses_server_session_actor_and_rejects_blank_hint():
    from pydantic import ValidationError
    from devpilot_core.interfaces.api.routers.workspace_edits import ApplyApprovalRequestBody

    flow=(ROOT/'ui/web/src/components/ArtifactReviewFlow.ts').read_text(encoding='utf-8')
    client=(ROOT/'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    assert "actor:''" not in flow
    assert 'serverAuthoritativePayload' in client
    assert 'actor?: string' in client

    with pytest.raises(ValidationError):
        ApplyApprovalRequestBody(
            plan_hash='a'*64,
            actor='',
            reason='Promover artefacto 04-D validado mediante apply gobernado y freeze.',
            ttl_minutes=15,
        )

    accepted=ApplyApprovalRequestBody(
        plan_hash='a'*64,
        reason='Promover artefacto 04-D validado mediante apply gobernado y freeze.',
        ttl_minutes=15,
    )
    assert accepted.actor is None



def test_artifact_review_approval_center_cross_tab_handoff_is_session_bound_and_project_scoped():
    client=(ROOT/'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    main=(ROOT/'ui/web/src/main.ts').read_text(encoding='utf-8')
    flow=(ROOT/'ui/web/src/components/ArtifactReviewFlow.ts').read_text(encoding='utf-8')
    view=(ROOT/'ui/web/src/pages/WorkspaceDocumentsView.ts').read_text(encoding='utf-8')
    assert 'APPROVAL_CENTER_ARTIFACT_REVIEW_HANDOFF_KEY' in client
    assert "handoff_kind: 'artifact-review'" in client
    assert "phase: 'project'" in client
    assert 'value.actor_id === session.principal.actor_id' in client
    assert 'value.session_created_at === session.created_at' in client
    assert 'Date.now() <= value.expires_at_ms' in client
    assert 'readApprovalCenterArtifactReviewHandoff(session, handoffApprovalId)' in main
    assert "handoffKind === 'artifact-review'" in main
    assert 'armApprovalCenterArtifactReviewHandoff(options.session,approvalId)' in flow
    assert 'session: AuthSessionContext' in flow
    assert 'renderWorkspaceDocumentsView(() => readStoredToken(), session)' in main
    assert 'renderWorkspaceDocumentsView(tokenProvider: () => string, session: AuthSessionContext)' in view
    assert 'createArtifactReviewFlow({ tokenProvider, session' in view
