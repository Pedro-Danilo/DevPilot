from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from devpilot_core.application import ApplicationService, AuthApplicationService
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.story_execution import StoryExecutionState, StoryExecutionStatus, StoryExecutionStore

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = {"Origin": "http://127.0.0.1:5173"}
PASSWORD = "A-very-long-local-password-09e"

@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root=tmp_path/'story-closure-workspace'; (root/'.devpilot').mkdir(parents=True); (root/'src').mkdir()
    (root/'.devpilot/project.yaml').write_text('project_id: story-closure-fixture\nproject_name: Story Closure Fixture\nproject_type: software\n',encoding='utf-8')
    (root/'src/app.py').write_text('def answer():\n    return 42\n',encoding='utf-8')
    monkeypatch.setenv('DEVPILOT_ALLOWED_WORKSPACE_ROOTS',str(root)); monkeypatch.setenv('DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT',str(root)); monkeypatch.setenv('DEVPILOT_GSDLC09C_CONTROL_ROOT',str(tmp_path/'control-09e')); monkeypatch.delenv('DEVPILOT_UI_WORKSPACE_REGISTRY_PATH',raising=False)
    store=StoryExecutionStore(root,workspace_id=root.name)
    store.save_state(StoryExecutionState(execution_id='story-exec-09e1234567890abcdef1234',workspace_id=root.name,project_id='story-closure-fixture',story_id='STORY-09E',story_version='1.0.0',status=StoryExecutionStatus.IN_PROGRESS,sequence=1,dor_report_sha256='a'*64,context_pack_id='story-context-09e1234567890abcdef12',context_pack_sha256='b'*64,created_at_utc='2026-09-08T18:00:00+00:00',updated_at_utc='2026-09-08T18:00:00+00:00'))
    return root

@pytest.fixture
def runtime(workspace: Path,tmp_path: Path):
    store=LocalAuthStore(tmp_path/'auth09e'); auth=AuthApplicationService(tmp_path/'auth09e',store=store); client=TestClient(create_app(ROOT,api_token='legacy-09e',auth_service=auth))
    r=client.post('/api/v1/auth/bootstrap/owner',json={'username':'owner09e','display_name':'Owner 09E','password':PASSWORD},headers=ORIGIN); assert r.status_code==201,r.text
    return ApplicationService(ROOT,approval_auth_store=store),client

def csrf(client:TestClient)->dict[str,str]: return {'Origin':ORIGIN['Origin'],'X-DevPilot-CSRF':str(client.cookies.get('devpilot_csrf') or '')}
def source(app:ApplicationService)->dict:
    row=next(x for x in app.story_code_sources().data['sources'] if x['relative_path']=='src/app.py'); return app.story_code_source_read(source_id=row['source_id']).data['source']
def plan(app:ApplicationService,content:str)->dict:
    src=source(app); d=app.story_code_draft_save(operation='EDIT',content=content,target_path='src/app.py',source_id=src['source_id'],expected_source_sha256=src['sha256'],expected_revision_sha256=None,actor='local-owner',actor_role='owner'); assert d.ok,d.to_dict(); p=app.story_source_change_plan_create(draft_ids=[d.data['draft']['draft_id']],actor='local-owner',actor_role='owner'); assert p.ok,p.to_dict(); return p.data['plan']
def approve(app:ApplicationService,client:TestClient,p:dict)->str:
    r=app.story_source_change_apply_approval_request(plan_id=p['plan_id'],plan_hash=p['plan_hash'],actor='local-owner',actor_role='owner',reason='09-E reviewed exact plan'); assert r.ok,r.to_dict(); aid=r.data['approval']['approval_id']; d=client.post(f'/api/v1/approvals/{aid}/approve',json={'reason':'Owner accepts 09-E plan'},headers=csrf(client)); assert d.status_code==200,d.text; return aid

def test_01_approved_atomic_apply_advances_active_story_to_changes_ready(workspace:Path,runtime)->None:
    app,client=runtime; p=plan(app,'def answer():\n    return 43\n'); r=app.story_source_change_apply(plan_id=p['plan_id'],plan_hash=p['plan_hash'],approval_id=approve(app,client,p),actor='local-owner',actor_role='owner'); assert r.ok,r.to_dict(); assert r.data['story_execution_state']['status']=='CHANGES_READY'; assert r.data['story_state_transition']['trigger']=='approved-atomic-source-apply'; state=StoryExecutionStore(workspace,workspace_id=workspace.name).load_state(); assert state and state.status is StoryExecutionStatus.CHANGES_READY and state.sequence==2

def test_02_wrong_role_or_blocked_apply_does_not_advance_story(workspace:Path,runtime)->None:
    app,_=runtime; p=plan(app,'def answer():\n    return 44\n'); r=app.story_source_change_apply(plan_id=p['plan_id'],plan_hash=p['plan_hash'],approval_id='missing',actor='developer',actor_role='developer'); assert not r.ok; state=StoryExecutionStore(workspace,workspace_id=workspace.name).load_state(); assert state and state.status is StoryExecutionStatus.IN_PROGRESS

def test_03_rollback_restores_source_and_story_state_remains_monotonic(workspace:Path,runtime)->None:
    app,client=runtime; before=(workspace/'src/app.py').read_bytes(); p=plan(app,'def answer():\n    return 45\n'); applied=app.story_source_change_apply(plan_id=p['plan_id'],plan_hash=p['plan_hash'],approval_id=approve(app,client,p),actor='local-owner',actor_role='owner'); ex=applied.data['execution']; rr=app.story_source_change_rollback_approval_request(execution_id=ex['execution_id'],actor='local-owner',actor_role='owner',reason='09-E rollback verification'); assert rr.ok; aid=rr.data['approval']['approval_id']; d=client.post(f'/api/v1/approvals/{aid}/approve',json={'reason':'Owner approves rollback'},headers=csrf(client)); assert d.status_code==200; rb=app.story_source_change_rollback(execution_id=ex['execution_id'],approval_id=aid,actor='local-owner',actor_role='owner'); assert rb.ok and rb.data['source_hash_parity'] is True and (workspace/'src/app.py').read_bytes()==before; state=StoryExecutionStore(workspace,workspace_id=workspace.name).load_state(); assert state and state.status is StoryExecutionStatus.CHANGES_READY

def test_04_project_status_ui_renders_current_story_status() -> None:
    text=(ROOT/'ui/web/src/pages/ProjectStatusView.ts').read_text(encoding='utf-8'); assert 'project-status-current-story' in text and 'data.currentStoryStatus' not in text; assert 'current?.status' in text and 'Current story' in text

def test_05_full_regression_profile_is_current_and_one_run_only() -> None:
    import json
    ptr=json.loads((ROOT/'.devpilot/testing/full_regression_execution_profile_current.json').read_text()); reg=json.loads((ROOT/'.devpilot/testing/full_regression_execution_profile_registry.json').read_text()); assert ptr['status']=='current-active' and ptr['current_profile_id']=='frx-v2.4-current'; profile=next(x for x in reg['profiles'] if x['profile_id']==ptr['current_profile_id']); assert profile['profile_sha256']==ptr['current_profile_sha256']; assert profile['full_regression_runs_allowed']==1 and profile['second_full_allowed'] is False and reg['consumer_contract']['profile_id_only'] is True
