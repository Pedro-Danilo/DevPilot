"""COR218: domain-sensitive quality defects, safe field repair, no laundering."""
from pathlib import Path
import json
import re
import pytest
from devpilot_core.application.r02_07_quality import (
    inspect_requirements, repair_targets, repair_schema, apply_repair_candidate,
    repair_prompt,
)

ROOT=Path(__file__).resolve().parents[1]


def example(controls=None):
    controls=controls or [
        ('El sistema debe registrar las solicitudes de préstamo para el agente.',
         'Se realizará una prueba de integración para comprobar que la solicitud se registra.'),
        ('El sistema debe actualizar el estado de los préstamos aprobados.',
         'Se realizará una prueba funcional para comprobar el cambio del estado.'),
        ('El sistema debe mostrar las solicitudes pendientes al operador.',
         'Se realizará una prueba de aceptación para comprobar la lista de pendientes.'),
    ]
    return ('# Especificación de requisitos\n## Requerimientos no funcionales\n' +
            '\n'.join(f'- RNF-{n:03d} — {c}; Verificación: {v}'
                      for n,(c,v) in enumerate(controls,1)))


def replacements():
    return {'repairs':[
        {'target_id':'RNF-001','control':'El acceso a préstamos requiere autorización por rol conforme a la política pendiente de aprobación.',
         'verification':'Prueba negativa: operador sin autorización intenta acceder al préstamo y recibe denegación sin cambios persistidos.'},
        {'target_id':'RNF-002','control':'Las modificaciones concurrentes de préstamos preservan integridad y consistencia de su estado confirmado.',
         'verification':'Prueba de concurrencia: dos cambios incompatibles no dejan estados parciales ni operaciones duplicadas.'},
        {'target_id':'RNF-003','control':'La interfaz presenta textos y controles con accesibilidad comprobable mediante inspección objetiva.',
         'verification':'Inspección del recorrido con teclado y de etiquetas accesibles, con registro de casos y resultado verificable.'},
    ]}


def test_quality_detects_every_pilot_rnf_with_exact_targets():
    # The actual Windows candidate is not distributed in the payload, so this
    # test uses a synthetic representative reproduction of the observed defects.
    content=example()
    f=inspect_requirements(content)
    assert set(repair_targets(f))=={'RNF-001','RNF-002','RNF-003'}


def test_model_can_repair_without_modifying_rf_or_provenance():
    original='# Especificación de requisitos\n### RF-001 — Solicitud\n- Origen: SC-IN-01\n'+example()
    targets=repair_targets(inspect_requirements(original))
    revised=apply_repair_candidate(original,replacements(),targets)
    assert '### RF-001 — Solicitud\n- Origen: SC-IN-01' in revised
    assert len(re.findall(r'(?m)^- RNF-\d{3}',revised))==3
    assert not [x for x in inspect_requirements(revised) if x['severity']=='BLOCK']
    assert original.startswith(revised.split('## Requerimientos no funcionales')[0])


def test_rejects_off_target_patch():
    t=repair_targets(inspect_requirements(example()))
    bad=replacements();bad['repairs'][0]['target_id']='RNF-099'
    with pytest.raises(ValueError,match='R0218_REPAIR_IDENTITY'):
        apply_repair_candidate(example(),bad,t)


def test_rejects_missing_required_target():
    t=repair_targets(inspect_requirements(example()))
    bad=replacements();bad['repairs'].pop()
    with pytest.raises(ValueError,match='R0218_REPAIR_COVERAGE'):
        apply_repair_candidate(example(),bad,t)


def test_rejects_placeholder_and_unverifiable_content():
    t=repair_targets(inspect_requirements(example()))
    bad=replacements();bad['repairs'][1]['control']='TODO Completar políticas y permisos con suficiente longitud.'
    with pytest.raises(ValueError,match='R0218_REPAIR_CONTENT'):
        apply_repair_candidate(example(),bad,t)
    bad=replacements();bad['repairs'][1]['verification']='Se podrá revisar que el resultado sea correcto y apropiado en las situaciones descritas.'
    with pytest.raises(ValueError,match='R0218_REPAIR_VERIFICATION'):
        apply_repair_candidate(example(),bad,t)


def test_quality_flags_truncated_verification_and_deferred_ia():
    original=example([('El sistema debe proporcionar un asistente IA para generar informes.',
          'Se realizará una prueba de accesibilidad que el sistema,')]*3)
    scope='## MVP+\n- SC-DEF-01 — Agentes consultivos diferidos.\n'
    findings=inspect_requirements(original,scope)
    codes={f['id'] for f in findings}
    assert 'R0218_DEFERRED_CAPABILITY_COMMITTED' in codes
    assert 'R0218_VERIFICATION_TRUNCATED' in codes


def test_valid_security_and_nonfunctional_attributes_are_not_rejected():
    assert not [f for f in inspect_requirements(example(list((x['control'],x['verification']) for x in replacements()['repairs'])))
                if f['severity']=='BLOCK']


def test_second_domain_does_not_assume_inventory_or_stock():
    text=example()
    f=inspect_requirements(text)
    assert not any('STOCK' in x['id'] for x in f)
    assert set(repair_schema(repair_targets(f))['properties'])=={'repairs'}
    assert 'SCOPE FROZEN' in repair_prompt(text,'## MVP\nPréstamos de estudiantes', 'Vision',repair_targets(f))


def test_rf_risks_are_review_only_not_false_hard_fail():
    doc='### RF-003 — Inventario\n- Criterio de aceptación: El stock debe coincidir con la cantidad vendida.\n'
    result=inspect_requirements(doc)
    assert any(x['id']=='R0218_SUSPECT_INVENTORY_ARITHMETIC' and x['severity']=='REVIEW_REQUIRED' for x in result)


def test_duplicate_target_or_wrong_schema_are_denied():
    targets=repair_targets(inspect_requirements(example()))
    bad=replacements();bad['repairs'][1]['target_id']='RNF-001'
    with pytest.raises(ValueError,match='R0218_REPAIR_IDENTITY'):
        apply_repair_candidate(example(),bad,targets)
    with pytest.raises(ValueError,match='R0218_REPAIR_SCHEMA'):
        apply_repair_candidate(example(),{'repairs':[],'extra':'yes'},targets)


def test_local_repair_route_is_one_call_and_preserves_candidate_lineage(monkeypatch,tmp_path):
    """End-to-end through generate_local_guided with fake Ollama, no real network."""
    from types import SimpleNamespace
    import shutil
    from devpilot_core.application import r02_07_semantic as sem
    workspace=tmp_path/'ws';(workspace/'.devpilot').mkdir(parents=True)
    source=ROOT / 'tests' / 'test_mp132_r02_07_cor218.py'
    # Synthetic workspace identity: preserve the real parsing contract.
    (workspace/'.devpilot/project.yaml').write_text(
        'project_id: admon_empresa_unipersonal_con_agentes\n'
        'business_need: "Biblioteca universitaria: registrar solicitudes y prestar ejemplares."\n',encoding='utf8')
    scope='## MVP\n| SC-IN-01 | Solicitudes de libros | P0 | Registro. | MVP |\n## MVP+\n- Agentes consultivos diferidos.\n'
    vision='# Visión\nLa biblioteca gestiona solicitudes y préstamos de forma controlada.\n'
    for stage,text in [('product-vision',vision),('scope',scope)]:
        f=workspace/sem.STAGE_PATHS[stage];f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text,encoding='utf8')
    root=tmp_path/'repo'
    statefile=root/'outputs/pre_code_wizard/gsdlc_05_e/admon_empresa_unipersonal_con_agentes/state.json'
    statefile.parent.mkdir(parents=True)
    statefile.write_text(json.dumps({'workspace_id':'admon_empresa_unipersonal_con_agentes','stages':{
        stage:{'status':'FROZEN','execution_id':'exec','approval_id':'approval','content_sha256':sem._sha(txt.encode())}
        for stage,txt in [('product-vision',vision),('scope',scope)]}}),encoding='utf8')
    previous=example()
    prior_sha=sem._sha(previous.encode())
    calls=[]
    class Adapter:
        def __init__(self,*args,**kwargs):pass
        def _post_json(self,endpoint,payload,task):
            calls.append((endpoint,payload))
            return SimpleNamespace(ok=True,metadata={'response':json.dumps(replacements()),
                    'done_reason':'stop','eval_count':500,'total_duration':10000})
    registry=SimpleNamespace(semantic_valid=True,get=lambda x:SimpleNamespace(
        external_api=False,requires_api_key=False,kind=SimpleNamespace(value='local'),endpoint='http://127.0.0.1:11434'))
    monkeypatch.setattr(sem.ProviderRegistry,'load',lambda root:registry)
    monkeypatch.setattr(sem,'evaluate_loopback_endpoint',lambda **kw:SimpleNamespace(ok=True))
    monkeypatch.setattr(sem,'OllamaAdapter',Adapter)
    monkeypatch.setattr(sem,'protect_generated_markdown',lambda root,content:(content,{'content_safety':'PASS'}))
    # This synthetic body lacks the full 7-RF professional envelope. Postgate
    # remains covered by the unchanged dedicated semantic test modules.
    monkeypatch.setattr(sem,'requirements_output_findings',lambda content,scope:[])
    result=sem.generate_local_guided(root,workspace_id='admon_empresa_unipersonal_con_agentes',
        workspace_root=workspace,stage_id='requirements',model='gemma3:4b',
        predecessor_sha256=prior_sha,previous_content=previous)
    assert len(calls)==1
    assert calls[0][1]['format']['properties']['repairs']['minItems']==3
    assert result['provenance']['authoring_route']=='R0218_LOCAL_MODEL_FOCAL_REPAIR'
    assert result['provenance']['predecessor_sha256']==prior_sha
    assert result['provenance']['original_segment_checkpoints_preserved'] is True
    assert len(list((root/'outputs/mp132_r02_07/admon_empresa_unipersonal_con_agentes/requirements').glob('cand-*.md')))==1
    # Same input is cached; no additional model call.
    other=sem.generate_local_guided(root,workspace_id='admon_empresa_unipersonal_con_agentes',
        workspace_root=workspace,stage_id='requirements',model='gemma3:4b',
        predecessor_sha256=prior_sha,previous_content=previous)
    assert other['candidate_sha256']==result['candidate_sha256']
    assert len(calls)==1


def test_negative_agent_authority_is_not_misclassified_as_deferred_feature():
    scope='## MVP+\n- SC-DEF-01 — Agentes consultivos diferidos.'
    body=example([('El sistema debe impedir que agentes sin autorización alteren operaciones sensibles del inventario.',
        'Prueba negativa con agente sin autorización: operación denegada y datos sin mutación.')]*3)
    issues=inspect_requirements(body,scope)
    assert not any(f['id']=='R0218_DEFERRED_CAPABILITY_COMMITTED' for f in issues)
