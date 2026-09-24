from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

from devpilot_core.application.pre_code_semantic_model import (
    GENERATOR_ID,
    SCHEMA_ID,
    build_candidate_model,
    capability_actionable,
    normalize_owner_model,
    requirement_records,
    semantic_hash,
    validate_confirmed_model,
    validate_rendered_artifact,
)
from devpilot_core.application.services import ApplicationService
from devpilot_core.workspace.runtime_project_context import activate_project_runtime_context, bind_persisted_project_runtime

ROOT=Path(__file__).resolve().parents[1]
PILOT=(
    'Es una empresa unipersonal dedicada a la comercialización de una línea de productos de bienestar y cuidado personal, '
    'como cosméticos, productos para adelgazar, potenciadores y productos rejuvenecedores, que opera sin instalaciones físicas '
    'y realiza sus ventas mediante entrega a domicilio. La empresa necesita una aplicación sencilla que le permita administrar '
    'los productos disponibles, controlar sus existencias, registrar las ventas y actualizar automáticamente el inventario cada '
    'vez que se realice una venta, así como consultar información básica sobre las ventas e identificar oportunamente los '
    'productos con bajo nivel de stock para facilitar su reposición y mantener la continuidad de la operación.'
)


def _candidate(need: str=PILOT):
    return build_candidate_model(
        workspace_id='fixture',business_need=need,source_ref='.devpilot/project.yaml',source_sha256='a'*64,
        constraints={'local_first':True,'cloud_required':False},model_policy={'baseline':'mock-no-api'},
    )


def _confirm(model: dict) -> dict:
    m=deepcopy(model)
    if not m.get('actors'):
        m.setdefault('actors',[]).append({'id':'','kind':'ACTOR','statement':'Persona responsable de operar el proceso','status':'CONFIRMED'})
    if not m.get('outcomes'):
        m.setdefault('outcomes',[]).append({'id':'','kind':'OUTCOME','statement':'Reducir demoras operativas y mantener información confiable','status':'CONFIRMED'})
    for row in m.get('actors') or []: row['status']='CONFIRMED'
    for row in m.get('outcomes') or []: row['status']='CONFIRMED'
    for row in m.get('capabilities') or []:
        low=str(row.get('statement') or '').lower()
        if low.startswith('administrar los productos'):
            row['statement']='Crear, consultar y actualizar productos disponibles'
        elif low.startswith('controlar sus existencias'):
            row['statement']='Consultar existencias actuales por producto'
        row['status']='CONFIRMED'
    for row in m.get('open_questions') or []:
        row['status']='CONFIRMED'
        low=str(row.get('statement') or '').lower()
        if 'stock bajo' in low: row['decision']='Usar el umbral de reposición confirmado para cada producto.'
        elif 'información de ventas' in low or 'informacion de ventas' in low: row['decision']='Mostrar fecha, total y productos de las ventas del MVP.'
        elif 'actor' in low: row['decision']='La persona responsable de operar el proceso es el actor principal.'
        elif 'resultado de negocio' in low: row['decision']='Reducir demoras operativas y mantener información confiable.'
        else: row['decision']='El Owner confirma el comportamiento observable de la capability relacionada.'
    return normalize_owner_model(model,m)


def _platform(tmp_path: Path) -> Path:
    platform=tmp_path/'platform'
    shutil.copytree(ROOT,platform,ignore=shutil.ignore_patterns('.git','.venv','node_modules','outputs','.pytest_cache','__pycache__','*.pyc','*.db','*.db-*','dist'))
    return platform


def _workspace(tmp_path: Path) -> Path:
    ws=tmp_path/'workspaces'/'semantic-fixture'
    for rel in ['.devpilot','docs','docs/standards','docs/00_product','docs/01_requirements','docs/02_architecture','docs/02_architecture/adrs','docs/03_security','docs/04_quality']:
        (ws/rel).mkdir(parents=True,exist_ok=True)
    (ws/'.devpilot/project.yaml').write_text(
        'project_id: semantic-fixture\nproject_name: "Semantic Fixture"\n'
        f'business_need: "{PILOT}"\n'
        'technology_decision_status: deferred-to-architecture\n'
        'model_policy:\n  baseline: "mock-no-api"\n  local_model: "optional-opt-in"\n  external_api: "approval-provenance-only"\n'
        'project_constraints:\n  local_first: true\n  cloud_required: false\n  operator_project_writes_allowed: false\n',encoding='utf-8')
    (ws/'.devpilot/workspace-registration.json').write_text(json.dumps({'workspace_id':ws.name,'project_id':ws.name,'root_path':str(ws.resolve())},indent=2)+'\n',encoding='utf-8')
    subprocess.run(['git','init','-q'],cwd=ws,check=True)
    subprocess.run(['git','config','user.email','fixture@example.invalid'],cwd=ws,check=True)
    subprocess.run(['git','config','user.name','Fixture'],cwd=ws,check=True)
    subprocess.run(['git','add','.'],cwd=ws,check=True); subprocess.run(['git','commit','-qm','baseline'],cwd=ws,check=True)
    return ws


def _activate(platform: Path, ws: Path, monkeypatch) -> None:
    activate_project_runtime_context(platform,ws,allowed_roots=(ws,))
    for name in ['DEVPILOT_ALLOWED_WORKSPACE_ROOTS','DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT','DEVPILOT_UI_WORKSPACE_REGISTRY_PATH','DEVPILOT_GUIDED_SDLC_WORKSPACE_REGISTRY_PATH']:
        monkeypatch.delenv(name,raising=False)
    assert bind_persisted_project_runtime(platform).applied


def test_semantic_model_schema_and_generator_are_versioned():
    model=_candidate()
    assert model['schema_id']==SCHEMA_ID
    assert model['generator']==GENERATOR_ID=='deterministic-semantic-model-template-v3'
    assert model['quality_state']=='REVIEW_REQUIRED'


def test_pilot_categories_are_not_capabilities():
    model=_candidate(); caps=' | '.join(x['statement'].lower() for x in model['capabilities'])
    assert 'como cosméticos' not in caps and 'productos para adelgazar' not in caps and 'productos rejuvenecedores' not in caps
    assert 'registrar las ventas' in caps and 'actualizar automáticamente el inventario' in caps


def test_descriptive_text_without_actions_fails_closed_with_open_question():
    model=_candidate('Una organización pequeña de carácter familiar dedicada a servicios profesionales.')
    assert model['capabilities']==[]
    assert any('capacidades concretas' in x['statement'].lower() and x['critical'] for x in model['open_questions'])


def test_alternate_domain_is_not_inventory_hardcoded():
    need='Una clínica necesita una aplicación que le permita registrar citas, consultar agenda y notificar recordatorios para reducir ausencias.'
    model=_candidate(need); text=json.dumps(model,ensure_ascii=False).lower()
    assert 'registrar citas' in text and 'consultar agenda' in text and 'notificar recordatorios' in text
    assert 'inventario' not in text and 'stock' not in text and 'ventas' not in text


def test_vague_capabilities_require_owner_rewrite():
    model=_candidate('Una empresa necesita una aplicación que le permita administrar productos para reducir demoras.')
    submitted=deepcopy(model)
    for x in submitted['actors']:
        x['status']='CONFIRMED'
    if not submitted['actors']:
        submitted['actors']=[{'id':'','kind':'ACTOR','statement':'Persona operadora','status':'CONFIRMED'}]
    for x in submitted['outcomes']: x['status']='CONFIRMED'
    for x in submitted['capabilities']: x['status']='CONFIRMED'
    for x in submitted['open_questions']:
        x['status']='CONFIRMED'; x['decision']='Confirmación genérica sin reescribir la capability.'
    confirmed=normalize_owner_model(model,submitted)
    ids={x['id'] for x in validate_confirmed_model(confirmed)}
    assert 'SEMANTIC_MODEL_CAPABILITY_ACTION_BLOCK' in ids


def test_confirmed_model_requires_actor_outcome_source_and_resolved_questions():
    model=_candidate(); confirmed=_confirm(model)
    assert validate_confirmed_model(confirmed)==[]
    broken=deepcopy(confirmed); broken['capabilities'][0]['source_ref']=''
    assert any(x['id']=='SEMANTIC_MODEL_SOURCE_EVIDENCE_BLOCK' for x in validate_confirmed_model(broken))
    broken2=deepcopy(confirmed); broken2['open_questions'][0]['status']='OPEN'; broken2['open_questions'][0]['decision']=''
    assert any(x['id']=='SEMANTIC_MODEL_CRITICAL_QUESTION_BLOCK' for x in validate_confirmed_model(broken2))


def test_semantic_hash_is_deterministic_for_same_confirmed_model():
    confirmed=_confirm(_candidate())
    assert semantic_hash(confirmed)==semantic_hash(deepcopy(confirmed))


def test_requirement_records_are_professional_minimum_and_traceable():
    confirmed=_confirm(_candidate()); records=requirement_records(confirmed)
    assert records
    for rec in records:
        assert rec['id'].startswith('RF-') and rec['type']=='FR' and rec['statement'].startswith('El sistema debe permitir')
        assert rec['source_capability_ids'] and rec['priority']=='MUST'
        assert rec['acceptance_criteria'] and rec['verification_method'] in {'TEST','DEMONSTRATION','INSPECTION','ANALYSIS'}
    assert all('cosméticos' not in r['statement'] for r in records)


def test_stock_question_decision_is_used_in_requirement_acceptance_criterion():
    confirmed=_confirm(_candidate()); records=requirement_records(confirmed)
    stock=next(r for r in records if 'stock' in r['statement'].lower())
    assert 'umbral de reposición' in stock['acceptance_criteria'][0]


def test_render_quality_gate_rejects_legacy_placeholder_requirement():
    confirmed=_confirm(_candidate())
    invalid='## Requerimientos funcionales del MVP\nEl sistema debe soportar de forma verificable: cosméticos.'
    ids={x['id'] for x in validate_rendered_artifact('requirements',invalid,confirmed)}
    assert 'SEMANTIC_REQUIREMENT_PLACEHOLDER_BLOCK' in ids


def test_product_vision_semantic_prepare_is_runtime_only_and_resume_aware(tmp_path,monkeypatch):
    platform=_platform(tmp_path); ws=_workspace(tmp_path); _activate(platform,ws,monkeypatch)
    svc=ApplicationService(platform); before=subprocess.check_output(['git','-C',str(ws),'status','--porcelain=v1','-z'])
    prepared=svc.guided_pre_code_save_draft(stage_id='product-vision',content='',mode='DEVPL_MOCK',actor='local-owner',actor_role='owner',session_principal='local-owner',effective_roles=['owner'],workspace_scopes=[ws.name])
    assert prepared.ok and prepared.data['semantic_model']['quality_state']=='REVIEW_REQUIRED'
    assert subprocess.check_output(['git','-C',str(ws),'status','--porcelain=v1','-z'])==before==b''
    svc2=ApplicationService(platform); status=svc2.guided_pre_code_status(effective_roles=['owner'],workspace_scopes=[ws.name])
    assert status.data['pre_code']['semantic_model']['semantic_model_sha256']==prepared.data['semantic_model']['semantic_model_sha256']


def test_confirmed_semantic_model_generates_deterministic_professional_vision(tmp_path,monkeypatch):
    platform=_platform(tmp_path); ws=_workspace(tmp_path); _activate(platform,ws,monkeypatch); svc=ApplicationService(platform)
    prep=svc.guided_pre_code_save_draft(stage_id='product-vision',content='',mode='DEVPL_MOCK',actor='local-owner',actor_role='owner',session_principal='local-owner',effective_roles=['owner'],workspace_scopes=[ws.name])
    confirmed=_confirm(prep.data['semantic_model'])
    one=svc.guided_pre_code_save_draft(stage_id='product-vision',content='',mode='DEVPL_MOCK',actor='local-owner',actor_role='owner',session_principal='local-owner',effective_roles=['owner'],workspace_scopes=[ws.name],semantic_model=confirmed)
    two=svc.guided_pre_code_save_draft(stage_id='product-vision',content='',mode='DEVPL_MOCK',actor='local-owner',actor_role='owner',session_principal='local-owner',effective_roles=['owner'],workspace_scopes=[ws.name])
    assert one.ok and two.ok
    assert one.data['stage']['draft_content']==two.data['stage']['draft_content']
    assert one.data['stage']['derivation']['canonical_input_sha256']==two.data['stage']['derivation']['canonical_input_sha256']
    text=one.data['stage']['draft_content']
    assert '## Usuario/actor' in text and '## Propuesta de valor' in text and 'Crear, consultar y actualizar productos disponibles' in text
    assert 'lifecycle_authority: "DevPilot runtime state"' in text
    mvp=text.split('## MVP',1)[1].split('## Indicadores',1)[0]
    assert 'como cosméticos' not in mvp and 'productos para adelgazar' not in mvp


def test_semantic_quality_gate_blocks_tampered_runtime_model_before_review(tmp_path,monkeypatch):
    platform=_platform(tmp_path); ws=_workspace(tmp_path); _activate(platform,ws,monkeypatch); svc=ApplicationService(platform)
    prep=svc.guided_pre_code_save_draft(stage_id='product-vision',content='',mode='DEVPL_MOCK',actor='local-owner',actor_role='owner',session_principal='local-owner',effective_roles=['owner'],workspace_scopes=[ws.name])
    generated=svc.guided_pre_code_save_draft(stage_id='product-vision',content='',mode='DEVPL_MOCK',actor='local-owner',actor_role='owner',session_principal='local-owner',effective_roles=['owner'],workspace_scopes=[ws.name],semantic_model=_confirm(prep.data['semantic_model']))
    assert generated.ok
    state_path=platform/'outputs/pre_code_wizard/gsdlc_05_e'/ws.name/'state.json'; state=json.loads(state_path.read_text())
    state['semantic_model']['capabilities'][0]['statement']='cosméticos'; state_path.write_text(json.dumps(state,indent=2)+'\n')
    review=svc.guided_pre_code_review(stage_id='product-vision',actor='local-owner',actor_role='owner',session_principal='local-owner',effective_roles=['owner'])
    assert not review.ok and any(x.id=='GSDLC13C01_SEMANTIC_QUALITY_BLOCK' for x in review.findings)


def test_governed_c01_reopen_archives_runtime_and_does_not_mutate_project_source(tmp_path,monkeypatch):
    platform=_platform(tmp_path); ws=_workspace(tmp_path); _activate(platform,ws,monkeypatch); svc=ApplicationService(platform)
    state=svc.pre_code_wizard._initial_state(ws.name)
    files={'product-vision':'docs/00_product/product_vision.md','scope':'docs/00_product/mvp_scope.md','requirements':'docs/01_requirements/requirements_specification.md'}
    for sid,rel in files.items():
        target=ws/rel; target.write_bytes(f'{sid} approved bytes\n'.encode()); sha=hashlib.sha256(target.read_bytes()).hexdigest()
        state['stages'][sid]['status']='FROZEN'; state['stages'][sid]['approved_sha256']=sha
    state['status']='IN_PROGRESS'; svc.pre_code_wizard._write_state(ws.name,state)
    before={rel:(ws/rel).read_bytes() for rel in files.values()}; git_before=subprocess.check_output(['git','-C',str(ws),'status','--porcelain=v1','-z'])
    result=svc.pre_code_wizard.reopen_c01_for_retest(actor='local-owner',actor_role='owner',session_principal='local-owner',effective_roles=['owner'],workspace_scopes=[ws.name],reason='semantic corrective retest')
    assert result.ok,result.to_dict(); assert result.data['project_source_mutations']==0
    after=svc.pre_code_wizard._load_state(ws.name); assert after['semantic_model'] is None
    assert all(after['stages'][sid]['status']=='MISSING' for sid in files)
    assert all(after['stages'][sid]['retest_baseline_approved_sha256'] for sid in files)
    assert before=={rel:(ws/rel).read_bytes() for rel in files.values()}
    assert subprocess.check_output(['git','-C',str(ws),'status','--porcelain=v1','-z'])==git_before
    assert list((platform/'outputs/pre_code_wizard/gsdlc_05_e'/ws.name/'history').glob('c01_before_retest_*_state.json'))


def test_ui_contains_semantic_review_and_diff_explainability_contract():
    view=(ROOT/'ui/web/src/pages/PreCodeWizardView.ts').read_text(encoding='utf-8')
    assert 'Base semántica derivada' in view
    assert 'Confirmar base semántica y generar DRAFT' in view
    assert 'source actual → DRAFT propuesto' in view or 'baseline vacío → DRAFT propuesto' in view
    assert 'este plan/diff deja de representar el cambio aprobado' in view
