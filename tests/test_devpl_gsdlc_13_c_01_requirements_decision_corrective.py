from __future__ import annotations

from copy import deepcopy

from devpilot_core.application.pre_code_semantic_model import (
    build_candidate_model,
    normalize_owner_model,
    observable_actions_from_decision,
    prepare_draft_first_model,
    requirement_records,
    unresolved_decisions_for_stage,
    validate_model_for_stage,
)

PILOT=(
    'Es una empresa unipersonal dedicada a la comercialización de una línea de productos de bienestar y cuidado personal, '
    'como cosméticos, productos para adelgazar, potenciadores y productos rejuvenecedores, que opera sin instalaciones físicas '
    'y realiza sus ventas mediante entrega a domicilio. La empresa necesita una aplicación sencilla que le permita administrar '
    'los productos disponibles, controlar sus existencias, registrar las ventas y actualizar automáticamente el inventario cada '
    'vez que se realice una venta, así como consultar información básica sobre las ventas e identificar oportunamente los '
    'productos con bajo nivel de stock para facilitar su reposición y mantener la continuidad de la operación.'
)


def _model():
    return prepare_draft_first_model(build_candidate_model(
        workspace_id='fixture', business_need=PILOT, source_ref='.devpilot/project.yaml', source_sha256='a'*64,
        constraints={'local_first':True,'cloud_required':False}, model_policy={'baseline':'mock-no-api'},
    ))


def _owner_answers(model):
    submitted=deepcopy(model)
    answers={
        'Q-001':'Incluye crear, consultar, modificar y retirar productos disponibles. Retirar un producto significa que deja de estar disponible para nuevas ventas, conservando su información histórica.',
        'Q-002':'Incluye consultar la existencia actual de cada producto, registrar entradas de inventario y realizar ajustes manuales de existencia cuando corresponda.',
        'Q-003':'La consulta debe permitir visualizar las ventas registradas, incluyendo como mínimo fecha y hora de la venta, productos vendidos, cantidad de cada producto y precio unitario.',
        'Q-004':'Un producto se considera de stock bajo cuando su existencia actual es menor o igual a su nivel mínimo de stock definido para ese producto.',
    }
    for q in submitted['open_questions']:
        q['decision']=answers[q['id']]
        q['status']='CONFIRMED'
        q['owner_confirmed']=True
    return normalize_owner_model(model, submitted)


def test_natural_owner_decision_extracts_observable_actions_without_parser_shaped_wording():
    actions=observable_actions_from_decision('Incluye crear, consultar, modificar y retirar productos disponibles.')
    assert actions==[
        'crear productos disponibles',
        'consultar productos disponibles',
        'modificar productos disponibles',
        'retirar productos disponibles',
    ]


def test_natural_owner_decisions_make_requirements_semantic_model_approval_ready():
    confirmed=_owner_answers(_model())
    assert unresolved_decisions_for_stage(confirmed,'requirements')==[]
    assert validate_model_for_stage(confirmed,'requirements')==[]


def test_vague_capabilities_expand_to_traceable_observable_requirement_records():
    confirmed=_owner_answers(_model())
    records=requirement_records(confirmed)
    cap1=[r for r in records if r['source_capability_ids']==['CAP-001']]
    cap2=[r for r in records if r['source_capability_ids']==['CAP-002']]
    assert len(cap1)==4
    assert len(cap2)==3
    statements='\n'.join(r['statement'].lower() for r in records)
    for phrase in ('crear productos disponibles','consultar productos disponibles','modificar productos disponibles','retirar productos disponibles','consultar la existencia actual de cada producto','registrar entradas de inventario','realizar ajustes manuales de existencia'):
        assert phrase in statements
    assert all(r['priority']=='MUST' and r['acceptance_criteria'] and r['verification_method'] in {'TEST','DEMONSTRATION','INSPECTION','ANALYSIS'} for r in records)
    assert any('conservando su información histórica' in str(r.get('owner_decision_context') or '') for r in cap1)


def test_unanswered_requirement_decisions_remain_fail_closed():
    model=_model()
    ids={x['id'] for x in validate_model_for_stage(model,'requirements')}
    assert 'SEMANTIC_MODEL_CRITICAL_QUESTION_BLOCK' in ids
