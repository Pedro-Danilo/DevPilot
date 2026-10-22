"""COR219: last bounded COR218 repair, exact prior budget and safe field diagnostics."""
from __future__ import annotations
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from devpilot_core.application.r02_07_quality import (
    inspect_requirements, repair_targets, repair_prompt, repair_schema,
    apply_repair_candidate, repair_change_diagnostics,
)


def source():
    return ('# Especificación de requisitos\n## Requerimientos no funcionales\n'
        '- RNF-001 — El sistema debe registrar ventas en el catálogo.; Verificación: Prueba de integración para registrar ventas correctamente y comprobar la persistencia.\n'
        '- RNF-002 — El sistema debe actualizar existencias después de ventas.; Verificación: Prueba de integración para actualizar existencias correctamente y comprobar las cantidades.\n'
        '- RNF-003 — El sistema debe alertar al propietario sobre el stock bajo.; Verificación: Prueba de integración para generar alertas correctamente y comprobar las notificaciones.\n'
        '- RNF-004 — El sistema debe proporcionar un asistente IA para informes.; Verificación: Prueba de integración para generar informes correctamente y revisar el resultado.\n')


def good():
    return {'repairs':[
        {'target_id':'RNF-001','control':'Las operaciones de ventas sensibles deben exigir autorización y denegar accesos no concedidos.',
         'verification':'Prueba negativa: un usuario sin autorización intenta acceder a una venta y recibe denegación sin modificaciones persistidas.'},
        {'target_id':'RNF-002','control':'La consistencia del inventario debe preservarse durante operaciones concurrentes sin producir saldos parciales.',
         'verification':'Prueba de concurrencia: ejecutar dos operaciones incompatibles y comprobar que solo los cambios confirmados afectan al saldo final.'},
        {'target_id':'RNF-003','control':'La interfaz operativa debe mantener accesibilidad mediante controles navegables con teclado y etiquetas perceptibles.',
         'verification':'Inspección de accesibilidad: recorrer los controles con teclado y comprobar focos visibles y nombres accesibles en cada operación.'},
        {'target_id':'RNF-004','control':'Los cambios sensibles en el inventario deben conservar trazabilidad auditada de actor, operación y resultado.',
         'verification':'Prueba de auditoría: registrar un cambio y verificar que el evento identifica operación, actor y resultado sin exponer secretos.'},
    ]}


def test_real_candidate_is_detected_without_copying_it_into_payload():
    src=source(); target=repair_targets(inspect_requirements(src,'## MVP+\nAgentes consultivos diferidos.'))
    assert set(target)=={f'RNF-{i:03}' for i in range(1,5)}
    task=repair_prompt(src,'## MVP\nVenta e inventario', '## Vision\nControl comercial',target)
    assert 'CONTRA-EJEMPLOS' in task and 'atributos' in task.lower()
    assert 'SCOPE FROZEN' in task and 'VISION FROZEN' in task
    assert len(task) < 20000
    assert repair_schema(target)['properties']['repairs']['minItems']==4


def test_identical_model_reply_produces_per_field_diagnostic():
    src=source();t=repair_targets(inspect_requirements(src))
    import re
    rows=re.findall(r'(?m)^- RNF-(\d{3}) — (.*?); Verificación: (.*)$',src)
    payload={'repairs':[{'target_id':'RNF-'+n,'control':c,'verification':v} for n,c,v in rows]}
    result=repair_change_diagnostics(src,payload,t)
    assert set(result)==set(t)
    assert all(not v['control_changed'] and not v['verification_changed'] for v in result.values())
    with pytest.raises(ValueError,match='R0218_REPAIR_NO_CHANGE'):
        apply_repair_candidate(src,payload,t)


def test_one_unchanged_target_is_blocked_even_when_other_three_change():
    src=source();t=repair_targets(inspect_requirements(src));payload=good()
    payload['repairs'][0]={'target_id':'RNF-001','control':'El sistema debe registrar ventas en el catálogo.',
     'verification':'Prueba de integración para registrar ventas correctamente y comprobar la persistencia.'}
    with pytest.raises(ValueError,match='R0219_REPAIR_TARGET_UNCHANGED'):
        apply_repair_candidate(src,payload,t)


def test_all_four_new_quality_attributes_pass_without_rf_mutation():
    src='### RF-001 — Registrar venta\n- Origen: SC-IN-01\n'+source()
    t=repair_targets(inspect_requirements(src,'## MVP+\nAgentes consultivos diferidos.'))
    delta=repair_change_diagnostics(src,good(),t)
    assert len(delta)==4 and all(v['control_changed'] and v['verification_changed'] for v in delta.values())
    edited=apply_repair_candidate(src,good(),t)
    assert edited.startswith('### RF-001 — Registrar venta\n- Origen: SC-IN-01')
    assert not [f for f in inspect_requirements(edited,'## MVP+\nAgentes consultivos diferidos.') if f['severity']=='BLOCK']


def test_no_duplicate_or_fifth_attempt_created_from_source(monkeypatch,tmp_path):
    """The path remains one COR218 input; no new attempt-1 namespace."""
    from devpilot_core.application import r02_07_semantic as sem
    workspace=tmp_path/'ws';(workspace/'.devpilot').mkdir(parents=True)
    (workspace/'.devpilot/project.yaml').write_text(
        'project_id: admon_empresa_unipersonal_con_agentes\n'
        'business_need: "Biblioteca: registrar préstamos y sus solicitudes."\n', encoding='utf8')
    vision='# Visión\nBiblioteca con acceso seguro y préstamos verificables.\n'
    scope='## MVP\n| SC-IN-01 | Registrar solicitudes y préstamos | P0 | MVP |\n## MVP+\nAgentes consultivos diferidos.\n'
    for stage,txt in [('product-vision',vision),('scope',scope)]:
        p=workspace/sem.STAGE_PATHS[stage];p.parent.mkdir(parents=True,exist_ok=True);p.write_text(txt,encoding='utf8')
    root=tmp_path/'repo';st=root/'outputs/pre_code_wizard/gsdlc_05_e/admon_empresa_unipersonal_con_agentes/state.json';st.parent.mkdir(parents=True)
    st.write_text(json.dumps({'workspace_id':'admon_empresa_unipersonal_con_agentes','stages':{
        stage:{'status':'FROZEN','execution_id':'exec','approval_id':'ok','content_sha256':sem._sha(txt.encode())}
        for stage,txt in [('product-vision',vision),('scope',scope)]}}),encoding='utf8')
    old=source();sha=sem._sha(old.encode());calls=[]
    import re
    rows=re.findall(r'(?m)^- RNF-(\d{3}) — (.*?); Verificación: (.*)$',old)
    same={'repairs':[{'target_id':'RNF-'+n,'control':c,'verification':v} for n,c,v in rows]}
    answers=[same,good()]
    class Adapter:
        def __init__(self,*args,**kwargs):pass
        def _post_json(self,endpoint,payload,task):
            calls.append(payload)
            return SimpleNamespace(ok=True,metadata={'response':json.dumps(answers.pop(0)),
                'done_reason':'stop','eval_count':200,'total_duration':3000})
    registry=SimpleNamespace(semantic_valid=True,get=lambda _:SimpleNamespace(
        external_api=False,requires_api_key=False,kind=SimpleNamespace(value='local'),endpoint='http://127.0.0.1:11434'))
    monkeypatch.setattr(sem.ProviderRegistry,'load',lambda x:registry)
    monkeypatch.setattr(sem,'evaluate_loopback_endpoint',lambda **kw:SimpleNamespace(ok=True))
    monkeypatch.setattr(sem,'OllamaAdapter',Adapter)
    monkeypatch.setattr(sem,'protect_generated_markdown',lambda root,c:(c,{'content_safety':'PASS'}))
    monkeypatch.setattr(sem,'requirements_output_findings',lambda c,scope:[])
    kw={'workspace_id':'admon_empresa_unipersonal_con_agentes','workspace_root':workspace,
        'stage_id':'requirements','model':'gemma3:4b','predecessor_sha256':sha,'previous_content':old}
    with pytest.raises(ValueError,match='R0218_REPAIR_NO_CHANGE'):
        sem.generate_local_guided(root,**kw)
    # Second Owner action uses same historical input hash and is last allowed.
    response=sem.generate_local_guided(root,**kw)
    assert response['provenance']['authoring_route']=='R0218_LOCAL_MODEL_FOCAL_REPAIR'
    assert len(calls)==2 and calls[0]['prompt']==calls[1]['prompt']
    receipts=list((root/'outputs/mp132_r02_07/admon_empresa_unipersonal_con_agentes/requirements/quality_repair_receipts').glob('*.json'))
    assert len(receipts)==2
    assert {json.loads(x.read_text())['attempt'] for x in receipts}=={1,2}
    safe=json.loads(next(x for x in receipts if 'attempt-02' in x.name).read_text())
    assert len(safe['per_target_change_flags'])==4
    assert safe['raw_response_stored'] is False
    sem.generate_local_guided(root,**kw)
    assert len(calls)==2
