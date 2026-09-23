from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.application.approval_service import ApprovalApplicationService
from devpilot_core.application.auth_service import AuthApplicationService
from devpilot_core.application.services import ApplicationService
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.workspace.runtime_project_context import activate_project_runtime_context, bind_persisted_project_runtime

ROOT=Path(__file__).resolve().parents[1]
PASSWORD='C01OwnerPassword!2026'


def _platform(tmp_path: Path) -> Path:
    platform=tmp_path/'platform'
    shutil.copytree(ROOT,platform,ignore=shutil.ignore_patterns('.git','.venv','node_modules','outputs','.pytest_cache','__pycache__','*.pyc','*.db','*.db-*','dist'))
    return platform


def _workspace(tmp_path: Path) -> Path:
    ws=tmp_path/'workspaces'/'inventory-sales-local-greenfield'
    for rel in ['.devpilot','docs/00_product','docs/01_requirements','docs/02_architecture','docs/03_security','docs/04_quality']:
        (ws/rel).mkdir(parents=True,exist_ok=True)
    (ws/'.devpilot/project.yaml').write_text(
        'project_id: inventory-sales-local-greenfield\n'
        'project_name: "Inventory Sales Local Greenfield"\n'
        'business_need: "Administrar productos, controlar stock, registrar ventas, actualizar inventario al vender, mostrar información básica de ventas e identificar productos con bajo stock."\n'
        'technology_decision_status: deferred-to-architecture\n'
        'model_policy:\n  baseline: "mock-no-api"\n  local_model: "optional-opt-in"\n  external_api: "approval-provenance-only"\n'
        'project_constraints:\n  local_first: true\n  cloud_required: false\n  operator_project_writes_allowed: false\n',encoding='utf-8')
    (ws/'.devpilot/workspace-registration.json').write_text(json.dumps({
        'workspace_id':'inventory-sales-local-greenfield','project_id':'inventory-sales-local-greenfield','root_path':str(ws.resolve())
    },indent=2)+'\n',encoding='utf-8')
    subprocess.run(['git','init','-q'],cwd=ws,check=True)
    subprocess.run(['git','config','user.email','fixture@example.invalid'],cwd=ws,check=True)
    subprocess.run(['git','config','user.name','Fixture'],cwd=ws,check=True)
    subprocess.run(['git','add','.'],cwd=ws,check=True)
    subprocess.run(['git','commit','-qm','baseline'],cwd=ws,check=True)
    return ws


def _activate(platform: Path, ws: Path, monkeypatch) -> None:
    activate_project_runtime_context(platform,ws,allowed_roots=(ws,))
    for name in ['DEVPILOT_ALLOWED_WORKSPACE_ROOTS','DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT','DEVPILOT_UI_WORKSPACE_REGISTRY_PATH','DEVPILOT_GUIDED_SDLC_WORKSPACE_REGISTRY_PATH']:
        monkeypatch.delenv(name,raising=False)
    binding=bind_persisted_project_runtime(platform)
    assert binding.applied


def test_api_start_reconciles_local_owner_to_server_active_workspace_and_precode_get_is_not_403(tmp_path,monkeypatch):
    platform=_platform(tmp_path); ws=_workspace(tmp_path)
    _activate(platform,ws,monkeypatch)
    auth=AuthApplicationService(platform)
    auth.bootstrap_owner(username='c01.owner',display_name='C01 Owner',password=PASSWORD)
    before=auth.store.get_identity('local-owner'); assert before and before.workspace_scopes==('devpilot-local',)
    app=create_app(platform,api_token='c01-token',auth_service=auth)
    after=auth.store.get_identity('local-owner'); assert after
    assert 'devpilot-local' in after.workspace_scopes and 'inventory-sales-local-greenfield' in after.workspace_scopes
    assert app.state.active_workspace_scope_reconciliation['status']=='PASS'
    client=TestClient(app)
    login=client.post('/api/v1/auth/login',json={'username':'c01.owner','password':PASSWORD},headers={'origin':'http://127.0.0.1:5173'})
    assert login.status_code==200,login.text
    pre=client.get('/api/v1/guided-sdlc/pre-code',headers={'origin':'http://127.0.0.1:5173'})
    assert pre.status_code==200,pre.text
    payload=pre.json()['data']['pre_code']
    assert payload['current_stage_id']=='product-vision'
    assert 'DEVPL_MOCK' in payload['stages'][0]['allowed_modes']
    assert payload['miasi']['status']=='NOT_EVALUATED' and payload['miasi']['gate_status']=='DEFERRED'



def test_http_devpl_mock_draft_is_project_scoped_csrf_bound_and_source_write_free(tmp_path,monkeypatch):
    platform=_platform(tmp_path); ws=_workspace(tmp_path); _activate(platform,ws,monkeypatch)
    auth=AuthApplicationService(platform)
    auth.bootstrap_owner(username='c01.owner',display_name='C01 Owner',password=PASSWORD)
    app=create_app(platform,api_token='c01-token',auth_service=auth)
    client=TestClient(app)
    login=client.post('/api/v1/auth/login',json={'username':'c01.owner','password':PASSWORD},headers={'origin':'http://127.0.0.1:5173'})
    assert login.status_code==200,login.text
    csrf=str(client.cookies.get('devpilot_csrf') or '')
    before=subprocess.check_output(['git','-C',str(ws),'status','--porcelain=v1','-z'])
    r=client.post('/api/v1/guided-sdlc/pre-code/stages/product-vision/draft',json={'mode':'DEVPL_MOCK','content':''},headers={'origin':'http://127.0.0.1:5173','X-DevPilot-CSRF':csrf})
    assert r.status_code==200,r.text
    payload=r.json(); assert payload['ok'] is True
    stage=payload['data']['stage']; assert stage['mode']=='DEVPL_MOCK' and stage['draft_content']
    assert stage['derivation']['network_used'] is False and stage['derivation']['external_api_used'] is False
    assert not (ws/'docs/00_product/product_vision.md').exists()
    assert subprocess.check_output(['git','-C',str(ws),'status','--porcelain=v1','-z'])==before==b''

def test_early_security_403_preserves_credentialed_cors_diagnostics(tmp_path,monkeypatch):
    platform=_platform(tmp_path); ws=_workspace(tmp_path); _activate(platform,ws,monkeypatch)
    auth=AuthApplicationService(platform); auth.bootstrap_owner(username='c01.owner',display_name='C01 Owner',password=PASSWORD)
    app=create_app(platform,api_token='c01-token',auth_service=auth); client=TestClient(app)
    # No human session: middleware blocks before router. Browser must still be able to read the 401/403 class response.
    r=client.get('/api/v1/guided-sdlc/pre-code',headers={'origin':'http://127.0.0.1:5173'})
    assert r.status_code==401
    assert r.headers.get('access-control-allow-origin')=='http://127.0.0.1:5173'
    assert r.headers.get('access-control-allow-credentials')=='true'


def test_devpl_mock_derives_product_vision_without_source_write_network_or_api(tmp_path,monkeypatch):
    platform=_platform(tmp_path); ws=_workspace(tmp_path); _activate(platform,ws,monkeypatch)
    service=ApplicationService(platform)
    before=subprocess.check_output(['git','-C',str(ws),'status','--porcelain=v1','-z'])
    result=service.guided_pre_code_save_draft(stage_id='product-vision',content='',mode='DEVPL_MOCK',actor='local-owner',actor_role='owner',session_principal='local-owner',effective_roles=['owner'],workspace_scopes=['inventory-sales-local-greenfield'])
    assert result.ok,result.to_dict()
    stage=result.data['stage']
    assert stage['mode']=='DEVPL_MOCK'
    assert stage['draft_content'] and '## Problema' in stage['draft_content'] and '## Visión' in stage['draft_content']
    assert 'Administrar productos' in stage['draft_content']
    d=stage['derivation']; assert d['provider']=='devpilot-local' and d['model']=='deterministic-context-template-v1'
    assert d['network_used'] is False and d['external_api_used'] is False and d['cost_usd']==0.0
    assert result.data['source_mutations_performed'] is False
    assert not (ws/'docs/00_product/product_vision.md').exists()
    assert subprocess.check_output(['git','-C',str(ws),'status','--porcelain=v1','-z'])==before==b''


def test_c01_local_derivation_is_sequential_and_generated_docs_validate(tmp_path,monkeypatch):
    platform=_platform(tmp_path); ws=_workspace(tmp_path); _activate(platform,ws,monkeypatch)
    service=ApplicationService(platform)
    # We verify generated proposals for all C-01 stages without bypassing stage order by freezing
    # test-local runtime rows/source inputs exactly as the real prior stage would leave them.
    actor='local-owner'
    vision=service.guided_pre_code_save_draft(stage_id='product-vision',content='',mode='DEVPL_MOCK',actor=actor,actor_role='owner',session_principal=actor,effective_roles=['owner'],workspace_scopes=[ws.name])
    assert vision.ok
    content=vision.data['stage']['draft_content']; (ws/'docs/00_product/product_vision.md').write_text(content,encoding='utf-8')
    state_path=platform/'outputs/pre_code_wizard/gsdlc_05_e'/ws.name/'state.json'; state=json.loads(state_path.read_text())
    state['stages']['product-vision']['status']='FROZEN'; state['stages']['product-vision']['approved_sha256']=__import__('hashlib').sha256(content.encode()).hexdigest(); state_path.write_text(json.dumps(state,indent=2)+'\n')
    scope=service.guided_pre_code_save_draft(stage_id='scope',content='',mode='DEVPL_MOCK',actor=actor,actor_role='owner',session_principal=actor,effective_roles=['owner'],workspace_scopes=[ws.name])
    assert scope.ok,scope.to_dict(); sc=scope.data['stage']['draft_content']; assert '## Out of scope' in sc
    (ws/'docs/00_product/mvp_scope.md').write_text(sc,encoding='utf-8'); state=json.loads(state_path.read_text()); state['stages']['scope']['status']='FROZEN'; state['stages']['scope']['approved_sha256']=__import__('hashlib').sha256(sc.encode()).hexdigest(); state_path.write_text(json.dumps(state,indent=2)+'\n')
    req=service.guided_pre_code_save_draft(stage_id='requirements',content='',mode='DEVPL_MOCK',actor=actor,actor_role='owner',session_principal=actor,effective_roles=['owner'],workspace_scopes=[ws.name])
    assert req.ok,req.to_dict(); rc=req.data['stage']['draft_content']
    assert '## Requerimientos funcionales del MVP' in rc and '**RF-001**' in rc and '## Criterios de bloqueo' in rc
    assert req.data['stage']['derivation']['source_refs'][-1]['path']=='docs/00_product/mvp_scope.md'


def test_precode_miasi_is_deferred_without_context_but_fail_closed_once_context_exists(tmp_path,monkeypatch):
    platform=_platform(tmp_path); ws=_workspace(tmp_path); _activate(platform,ws,monkeypatch)
    svc=ApplicationService(platform)
    status=svc.guided_pre_code_status(effective_roles=['owner'],workspace_scopes=[ws.name])
    assert status.ok
    m=status.data['pre_code']['miasi']; assert m['status']=='NOT_EVALUATED' and m['gate_status']=='DEFERRED' and m['pre_code_authoritative'] is False
    assert not any(x.get('stage_id')=='miasi-applicability' for x in status.data['pre_code']['readiness']['blockers'])
    ctx=platform/'outputs/workspaces'/ws.name/'miasi_applicability_context.json'; ctx.parent.mkdir(parents=True,exist_ok=True)
    ctx.write_text(json.dumps({'schema_id':'SCHEMA-DEVPL-MIASI-APPLICABILITY-CONTEXT-V1','schema_version':'1.0','workspace_id':ws.name,'project':{'declared_ai_usage':None,'capabilities':[],'risk_level':'low','evidence_refs':['c01:test']},'features':[],'risk_review_status':'NOT_REQUIRED','evidence_refs':['c01:test']},indent=2)+'\n')
    status2=svc.guided_pre_code_status(effective_roles=['owner'],workspace_scopes=[ws.name]); m2=status2.data['pre_code']['miasi']
    assert m2['pre_code_authoritative'] is True and m2['gate_status']=='BLOCK'
    assert any(x.get('stage_id')=='miasi-applicability' for x in status2.data['pre_code']['readiness']['blockers'])


def test_ui_exposes_local_derived_mode_provenance_and_precise_403_copy():
    view=(ROOT/'ui/web/src/pages/PreCodeWizardView.ts').read_text(encoding='utf-8')
    project_status=(ROOT/'ui/web/src/pages/ProjectStatusView.ts').read_text(encoding='utf-8')
    client=(ROOT/'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    types=(ROOT/'ui/web/src/api/types.ts').read_text(encoding='utf-8')
    services=(ROOT/'src/devpilot_core/application/services.py').read_text(encoding='utf-8')
    assert 'DevPilot · Mock local / sin API' in view
    assert 'Generar propuesta con DevPilot' in view
    assert 'Propuesta DevPilot local' in view and 'costo USD' in view
    assert 'RBAC/policy denegó el acceso a Pre-code (HTTP 403)' in view
    assert "'DEVPL_MOCK'" in types and 'draft_content' in types and 'derivation' in types
    assert "mode: 'MANUAL' | 'IMPORT' | 'DEVPL_MOCK'" in client
    assert 'propuesta local DevPilot para C-01' in project_status
    assert 'MANUAL/IMPORT/DEVPL_MOCK' in services


def test_c01_three_stage_devpl_mock_flow_uses_review_approval_apply_freeze(tmp_path,monkeypatch):
    platform=_platform(tmp_path); ws=_workspace(tmp_path); _activate(platform,ws,monkeypatch)
    auth=AuthApplicationService(platform)
    auth.bootstrap_owner(username='c01.owner',display_name='C01 Owner',password=PASSWORD)
    # create_app performs the same active-workspace scope reconciliation used by the real launcher
    # and revokes any session that still carries the old devpilot-local-only workspace scope.
    create_app(platform,api_token='c01-token',auth_service=auth)
    issue=auth.login(username='c01.owner',password=PASSWORD)
    service=ApplicationService(platform,approval_auth_store=auth.store)
    actor=issue.context.principal.actor_id
    expected=[
        ('product-vision','docs/00_product/product_vision.md'),
        ('scope','docs/00_product/mvp_scope.md'),
        ('requirements','docs/01_requirements/requirements_specification.md'),
    ]
    for stage_id,rel in expected:
        status=service.guided_pre_code_status(effective_roles=['owner'],workspace_scopes=[ws.name])
        assert status.ok,status.to_dict()
        assert status.data['pre_code']['current_stage_id']==stage_id
        draft=service.guided_pre_code_save_draft(
            stage_id=stage_id,content='',mode='DEVPL_MOCK',actor=actor,actor_role='owner',
            session_principal=actor,effective_roles=['owner'],workspace_scopes=[ws.name],
        )
        assert draft.ok,draft.to_dict()
        assert not (ws/rel).exists(), 'DEVPL_MOCK DRAFT must remain server-side until approval-bound apply'
        review=service.guided_pre_code_review(
            stage_id=stage_id,actor=actor,actor_role='owner',session_principal=actor,effective_roles=['owner'],
        )
        assert review.ok,review.to_dict()
        record=review.data['review']; assert record['status']=='APPROVAL_REQUIRED'
        req=service.guided_pre_code_request_approval(
            stage_id=stage_id,actor=actor,actor_role='owner',session_principal=actor,effective_roles=['owner'],
            reason=f'Approve {stage_id} in C01 local-derived acceptance fixture',
        )
        assert req.ok,req.to_dict(); approval_id=req.data['pre_code']['approval_id']
        decided=ApprovalApplicationService(platform,auth_store=auth.store).decide_authenticated(
            approval_id=approval_id,decision='approved',principal=issue.context.principal,session=issue.context,
            caller_actor=None,reason='C01 fixture owner approval',
        )
        assert decided.ok,decided.to_dict()
        applied=service.guided_pre_code_apply(
            stage_id=stage_id,actor=actor,actor_role='owner',session_principal=actor,effective_roles=['owner'],
        )
        assert applied.ok,applied.to_dict(); execution_id=applied.data['pre_code']['execution_id']
        assert (ws/rel).is_file()
        frozen=service.guided_pre_code_freeze(
            stage_id=stage_id,review_id=record['review_id'],execution_id=execution_id,actor=actor,actor_role='owner',
            session_principal=actor,effective_roles=['owner'],workspace_scopes=[ws.name],
        )
        assert frozen.ok,frozen.to_dict()
        row=next(x for x in frozen.data['pre_code']['stages'] if x['stage_id']==stage_id)
        assert row['status']=='FROZEN'
    final=service.guided_pre_code_status(effective_roles=['owner'],workspace_scopes=[ws.name])
    assert final.ok,final.to_dict()
    assert final.data['pre_code']['current_stage_id']=='architecture'
    assert final.data['pre_code']['miasi']['status']=='NOT_EVALUATED'
    assert final.data['pre_code']['miasi']['gate_status']=='DEFERRED'
    assert not (platform/'outputs/workspaces'/ws.name/'miasi_applicability_context.json').exists()
    assert not (ws/'.venv').exists()
    assert not (ws/'frontend/package.json').exists()
    assert not (ws/'backend/requirements.txt').exists()
