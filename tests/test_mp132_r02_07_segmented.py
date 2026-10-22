"""COR207: generic segmentation profile, resumability, assembly and security."""
from __future__ import annotations
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from devpilot_core.application import r02_07_segmented as seg
from devpilot_core.application import r02_07_semantic as author

SCOPE = """## MVP
| ID | Capacidad | Prioridad | Justificación | Límite |
|---|---|---|---|---|
| SC-IN-01 | Administrar catálogo | P0 | Registrar productos | Crear y consultar productos |
| SC-IN-02 | Registrar ventas | P0 | Registrar ventas válidas | Sin alterar existencias si es rechazada |
## Criterios
| ID | Capacidad | Escenario |
|---|---|---|
| SC-AC-01 | Catálogo | Dado un producto válido, cuando el propietario registra catálogo, entonces consta en UI y consulta |
| SC-AC-02 | Ventas | Dada una venta válida, cuando se registra la venta, entonces existe asiento persistente |
## MVP+
| SC-DE-01 | Agentes avanzados | DIFERIDO |
"""
VISION = "## Visión\nControlar registro de productos y ventas con datos confiables y gobernanza del Owner.\n## Limitaciones\nLos agentes son consultivos y las acciones sensibles requieren autorización humana."

def rf_text(unit):
    source=unit['source_row'].split(' | ',1)[0]
    subject=source if unit['source_id']!='TRANSVERSAL' else unit['criteria'].replace(' | ',' ')[:70]
    ac=(f'Dado un escenario {subject} de negocio autorizado, cuando el propietario registra la operación '
        f'de {subject} bajo validación, entonces el resultado {subject} persiste y puede consultarse.')
    return (f"### {unit['rf_id']} — Operación de {subject}\n"
        "- Tipo: Requisito funcional verificable dentro del alcance aprobado de negocio.\n"
        f"- Justificación: Garantizar la trazabilidad de {subject} conforme a la necesidad original del propietario.\n"
        "- Prioridad: Propuesta P0 pendiente de confirmación por el Owner y su alcance.\n"
        f"- Método de verificación: Prueba automatizada de {subject} y consulta del estado persistido.\n"
        f"- Comportamiento: El Owner administra y registra {subject} en el sistema y consulta el resultado autorizado.\n"
        "- Precondiciones: Existe una entidad válida previamente identificada y permiso del propietario.\n"
        f"- Regla de negocio: Solo persisten operaciones válidas de {subject} según el Scope aprobado.\n"
        "- Excepción: Si no se cumplen las reglas o falta permiso, no se modifica el estado anterior.\n"
        f"- Criterio de aceptación: {ac}\n")

def global_text():
    return ("## Requisitos no funcionales\n"
        "- RNF-001 — Privacidad: resguardar información sensible del propietario. Verificación: prueba de acceso negativo.\n"
        "- RNF-002 — Integridad: conservar registros transaccionales coherentes. Verificación: prueba de estado persistente.\n"
        "- RNF-003 — Auditoría: registrar las operaciones identificables y autorizadas. Verificación: inspección de evidencias.\n"
        "## Restricciones\nLas tecnologías se decidirán en Architecture, sin inventar integraciones ni servicios externos.\n"
        "## Decisiones pendientes\nEl Owner deberá definir la política exacta de anulación y permisos antes de autorizar cambios sensibles.\n")

def args(tmp,scope=SCOPE, model='gemma3:4b', fail_on=None, secret=False):
    root=tmp
    context={'upstream':[('product-vision',VISION),('scope',scope)], 'upstream_hashes':{'product-vision':seg.sha(VISION),'scope':seg.sha(scope)},
             'source_sha256':'project.yaml:sha256:'+'a'*64,'predecessor_sha256':''}
    calls=[]
    class Fake:
        def _post_json(self,endpoint,payload,task):
            calls.append(payload)
            n=len(calls)
            if fail_on is not None and n==fail_on:return SimpleNamespace(ok=False,metadata={'error_type':'timeout'})
            unit=next((u for u in seg.plan_from_scope(scope,VISION) if u['rf_id'] in payload['prompt']),None)
            # Global unit deliberately has no RF.
            if '## Requisitos no funcionales' in payload['prompt']: text=global_text()
            else: text=rf_text(unit)
            if secret:text+='\nACCESS_TOKEN=abcdef123456789012345678\n'
            return SimpleNamespace(ok=True,metadata={'response':text,'done_reason':'stop','eval_count':170})
    failures=[]
    def record(code,details):failures.append((code,details))
    return context, Fake(), calls, failures, record

def test_generic_profile_scope_2_capabilities(tmp_path):
    units=seg.plan_from_scope(SCOPE,VISION)
    assert [x['id'] for x in units]==['SC-AC-01','SC-AC-02','GLOBAL']
    assert all('SC-DE-01' not in u['source_row'] for u in units)
    context,adapter,calls,errors,record=args(tmp_path)
    for n in range(1,4):
        res=seg.execute_one(tmp_path,'project-X',context,adapter,None,'gemma3:4b',None,lambda c:(c,{'content_safety':'PASS'}),record)
        if n<3:assert res['partial'] and res['progress']['completed']==n
    assert not res['partial'] and len(calls)==3 and len(res['segment_receipts'])==3
    output=res['body']
    assert '## Propósito' in output and '## Requerimientos no funcionales' in output
    assert output.index('RF-001') < output.index('RF-002')
    assert set(x['id'] for x in seg.plan_from_scope(SCOPE,VISION))=={'SC-AC-01','SC-AC-02','GLOBAL'}
    assert author.requirements_output_findings(output,SCOPE)==[]
    assert seg.progress(tmp_path,'project-X')['status']=='COMPLETE'
    assert not errors

def test_resume_same_plan_does_not_repeat_completed_units(tmp_path):
    context,adapter,calls,failures,record=args(tmp_path)
    for _ in range(2):seg.execute_one(tmp_path,'project-X',context,adapter,None,'gemma3:4b',None,lambda c:(c,{'content_safety':'PASS'}),record)
    assert len(calls)==2
    seg.execute_one(tmp_path,'project-X',context,adapter,None,'gemma3:4b',None,lambda c:(c,{'content_safety':'PASS'}),record)
    result=seg.execute_one(tmp_path,'project-X',context,adapter,None,'gemma3:4b',None,lambda c:(c,{'content_safety':'PASS'}),record)
    assert result['partial'] is False and len(calls)==3

def test_invalid_unit_is_not_saved_and_next_call_retries_only_that_unit(tmp_path):
    ctx, adapter, calls,failures,record=args(tmp_path)
    class FailingOnce:
        n=0
        def _post_json(self,endpoint,payload,task):
            self.n+=1
            if self.n==2:return SimpleNamespace(ok=True,metadata={'response':'Enhorabuena, una maravillosa propuesta','done_reason':'stop'})
            return adapter._post_json(endpoint,payload,task)
    fake=FailingOnce()
    seg.execute_one(tmp_path,'project-Y',ctx,fake,None,'gemma3:4b',None,lambda c:(c,{'content_safety':'PASS'}),record)
    with pytest.raises(ValueError,match='NOT_CONFORMANT'):
        seg.execute_one(tmp_path,'project-Y',ctx,fake,None,'gemma3:4b',None,lambda c:(c,{'content_safety':'PASS'}),record)
    files=list((tmp_path/'outputs/mp132_r02_07/project-Y/requirements_segments').glob('*/SC-AC-*.json'))
    assert len(files)==1
    assert failures and failures[0][0]=='R0207_SEGMENT_NOT_CONFORMANT'
    seg.execute_one(tmp_path,'project-Y',ctx,fake,None,'gemma3:4b',None,lambda c:(c,{'content_safety':'PASS'}),record)
    assert len(list((tmp_path/'outputs/mp132_r02_07/project-Y/requirements_segments').glob('*/SC-AC-*.json')))==2

def test_security_hold_never_persists_segment(tmp_path):
    ctx,adapter,call,errors,record=args(tmp_path)
    with pytest.raises(ValueError,match='SEGMENT_SECURITY_HOLD'):
        seg.execute_one(tmp_path,'project-Z',ctx,adapter,None,'gemma3:4b',None,
                 lambda c:(c+'\n[CONTENIDO_RETENIDO_POR_SEGURIDAD]',{'content_safety':'REDACTED_FOR_OWNER_REVIEW'}),record)
    assert not list((tmp_path/'outputs/mp132_r02_07/project-Z').glob('requirements_segments/*/SC-AC*.json'))

def test_tamper_checkpoint_blocks_resume(tmp_path):
    ctx,adapter,calls,err,record=args(tmp_path)
    seg.execute_one(tmp_path,'project-X',ctx,adapter,None,'gemma3:4b',None,lambda c:(c,{'content_safety':'PASS'}),record)
    path=next((tmp_path/'outputs/mp132_r02_07/project-X').rglob('SC-AC-01.json'))
    data=json.loads(path.read_text());data['body']='TEXTO ALTERADO';path.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='CHECKPOINT_DRIFT'):
        seg.execute_one(tmp_path,'project-X',ctx,adapter,None,'gemma3:4b',None,lambda c:(c,{'content_safety':'PASS'}),record)
    assert len(calls)==1

def test_different_project_capabilities_are_not_pilot_b_constants():
    scope='## MVP\n| ID | Capacidad | Prioridad | Límite |\n| SC-IN-01 | Reserva de salas | P0 | Sin doble asignación |\n| SC-IN-02 | Cancelaciones | P0 | Según autorización |\n## Criterios\n| SC-AC-01 | Reserva | Dada una sala, cuando se reserva, entonces registra reserva |\n| SC-AC-02 | Cancelaciones | Dada una reserva, cuando se cancela, entonces queda cancelada |\n## MVP+\n| SC-DE-01 | Integraciones | P1 |'
    units=seg.plan_from_scope(scope,'## Visión\nSistema de reservas')
    assert len(units)==3 and 'Reserva de salas' in units[0]['source_row']
    assert 'Catálogo' not in str(units)

def test_no_approval_or_project_write(tmp_path):
    ctx,adapter,calls,err,record=args(tmp_path)
    project=tmp_path/'external-project'; project.mkdir();(project/'document.md').write_text('FROZEN')
    seg.execute_one(tmp_path,'a',ctx,adapter,None,'gemma3:4b',None,lambda c:(c,{'content_safety':'PASS'}),record)
    assert (project/'document.md').read_text()=='FROZEN'
    assert not list(tmp_path.rglob('approvals.json'))

def test_segment_checkpoint_atomic_recovery(tmp_path):
    file=tmp_path/'state.json'; data={'state':'PASS'}
    temporary=file.with_name(file.name+'.new');temporary.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    seg.atomic_json(file,data)
    assert file.is_file() and not temporary.exists()
    assert json.loads(file.read_text())==data

def test_global_section_minimum_and_agent_security():
    unit={'kind':'global'}
    assert 'NFR_IDS_MISSING' in seg.validate_unit('## Requisitos no funcionales\nX\n## Restricciones\n'+('Control '*15)+'\n## Decisiones pendientes\n'+('Pendiente '*15),unit)
    u={'kind':'functional','rf_id':'RF-001','source_row':'Administrar catálogo','source_id':'SC-IN-01'}
    assert 'AGENT_AUTHORITY_CONTRADICTION' in seg.validate_unit(rf_text(u)+'\nLos agentes pueden publicar sin autorización.',u)

def test_end_to_end_requirements_segmented_uses_frozen_and_only_final_draft(tmp_path):
    pid='admon_empresa_unipersonal_con_agentes'
    platform=tmp_path/'platform';platform.mkdir();workspace=tmp_path/'workspace';(workspace/'.devpilot').mkdir(parents=True)
    (workspace/'.devpilot/project.yaml').write_text('placeholder: local')
    for stage,path,text in [('product-vision','docs/00_product/product_vision.md',VISION),('scope','docs/00_product/mvp_scope.md',SCOPE)]:
        p=workspace/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    state=platform/'outputs/pre_code_wizard/gsdlc_05_e'/pid/'state.json';state.parent.mkdir(parents=True)
    state.write_text(json.dumps({'workspace_id':pid,'stages':{
       'product-vision':{'status':'FROZEN','execution_id':'exec-vis','approval_id':'appr-vis','content_sha256':author._sha(VISION.encode())},
       'scope':{'status':'FROZEN','execution_id':'exec-scp','approval_id':'appr-scp','content_sha256':author._sha(SCOPE.encode())}}}))
    ctx,adapter,calls,failures,record=args(tmp_path)
    adapter.health=lambda:SimpleNamespace(ok=True,data={'models':['gemma3:4b']})
    fakecfg=SimpleNamespace(external_api=False,requires_api_key=False,kind=SimpleNamespace(value='local'),endpoint='http://127.0.0.1:11434')
    registry=SimpleNamespace(semantic_valid=True,get=lambda key:fakecfg)
    with patch.object(author,'parse_project_yaml_metadata',return_value={'project_id':pid,'business_need':'Control de productos, ventas e inventario bajo supervisión.'}),patch.object(author.ProviderRegistry,'load',return_value=registry),patch.object(author,'evaluate_loopback_endpoint',return_value=SimpleNamespace(ok=True)),patch.object(author,'OllamaAdapter',return_value=adapter):
        for n in (1,2):
            out=author.generate_local_guided(platform,workspace_id=pid,workspace_root=workspace,stage_id='requirements',model='gemma3:4b')
            assert out['partial'] and out['progress']['completed']==n
            assert not list((platform/'outputs/mp132_r02_07'/pid/'requirements').glob('cand-*.md'))
        out=author.generate_local_guided(platform,workspace_id=pid,workspace_root=workspace,stage_id='requirements',model='gemma3:4b')
        assert 'candidate_path' in out and 'content' in out and len(out['provenance']['segmented_receipts'])==3
        assert out['provenance']['external_api_used'] is False
        assert len(calls)==3
        assert author.requirements_output_findings(out['content'],SCOPE)==[]
        repeat=author.generate_local_guided(platform,workspace_id=pid,workspace_root=workspace,stage_id='requirements',model='gemma3:4b')
        assert repeat['candidate_sha256']==out['candidate_sha256'] and len(calls)==3
    assert (workspace/'docs/00_product/mvp_scope.md').read_text()==SCOPE


def test_mixed_acceptance_per_scope_and_cross_criteria():
    # Synthetic second domain: do not hardcode the product/project name.
    scope="""## MVP
| ID | Capacidad | Prioridad | Límite |
|---|---|---|---|
| SC-IN-01 | Administrar catálogo | P0 | Crear y consultar |
| SC-IN-02 | Registrar ventas | P0 | Ventas válidas |
| SC-IN-03 | Consultar existencias | P0 | Estado actual |
## Criterios
| ID | Capacidad | Escenario |
|---|---|---|
| SC-AC-01 | Catálogo | Dado un catálogo válido, cuando se registra producto, entonces consultable |
| SC-AC-02 | Ventas | Dada una venta válida, cuando se registra, entonces persiste |
| SC-AC-03 | Caso negativo | Dada venta inválida, cuando se rechaza, entonces no cambia existencia |
| SC-AC-04 | Permisos | Dado actor no autorizado, cuando modifica, entonces no cambia datos |
## MVP+
| SC-DE-01 | Agentes | DIFERIDO |
"""
    units=seg.plan_from_scope(scope,VISION)
    assert set(x['source_id'] for x in units)=={'SC-IN-01','SC-IN-02','SC-IN-03','TRANSVERSAL',''}
    assert {u['criterion_id'] for u in units if u['criterion_id']}=={'SC-AC-01','SC-AC-02','SC-AC-03'}
    assert 'SC-AC-04' in units[-1]['transverse_ids']
    assert len(units)==5
    assert units[-1]['kind']=='global'


def test_real_cor207_candidate_fails_new_contract_without_rewriting_it():
    u={'id':'SC-AC-01','kind':'functional','rf_id':'RF-001','source_id':'SC-IN-01',
       'source_row':'Administrar catálogo | Crear y actualizar productos',
       'criterion_id':'SC-AC-01','criteria':'Catálogo | Registrar productos válidos y poder consultarlos',
       'relation_status':'PROPOSED_LABEL_MATCH'}
    old=("### RF-001 — Registrar Ventas y Existencias\n- Origen: SC-IN-01.\n"
        "- Comportamiento: El sistema registra ventas y actualiza existencias asociadas a un producto identificado.\n"
        "- Precondiciones: Hay un producto en el catálogo de productos.\n"
        "- Regla de negocio: Una venta válida actualiza las existencias del producto.\n"
        "- Excepción: Si no existe el producto, rechaza la venta.\n"
        "- Criterio de aceptación: Dado un producto válido, cuando registra una venta, entonces descuenta existencias.\n")
    issues=seg.validate_unit(old,u)
    assert 'CAPABILITY_BEHAVIOR_MISMATCH' in issues and 'TYPE' in issues and 'METHOD' in issues


def test_project_scopes_have_distinct_plans_and_no_implicit_trust():
    scope=SCOPE.replace('Administrar catálogo','Administrar archivos').replace('Catálogo |','Archivos |')
    assert seg.sha(str(seg.plan_from_scope(scope,VISION)))!=seg.sha(str(seg.plan_from_scope(SCOPE,VISION)))
    units=seg.plan_from_scope(scope,VISION)
    assert 'Archivos' in str(units) and 'Catálogo' not in str(units)


def test_cor210_failure_receipts_are_safe_and_checkpoint_recoverable(tmp_path):
    context, adapter, calls, failures, record = args(tmp_path)
    class AlwaysInvalid:
        def _post_json(self, endpoint, payload, task):
            if not calls:
                return adapter._post_json(endpoint,payload,task)
            calls.append(payload)
            return SimpleNamespace(ok=True,metadata={'response':'Respuesta conversacional: ACCESS_TOKEN=do-not-echo','done_reason':'stop', 'eval_count':77})
    # First unit succeeds, second is invalid twice; never persisted as checkpoint.
    bad=AlwaysInvalid()
    seg.execute_one(tmp_path,'project-R',context,bad,None,'gemma3:4b',None,lambda s:(s,{'content_safety':'PASS'}),record)
    for _ in range(2):
        with pytest.raises(ValueError,match='NOT_CONFORMANT'):
            seg.execute_one(tmp_path,'project-R',context,bad,None,'gemma3:4b',None,lambda s:(s,{'content_safety':'PASS'}),record)
    with pytest.raises(ValueError,match='RETRY_BUDGET_EXHAUSTED'):
        seg.execute_one(tmp_path,'project-R',context,bad,None,'gemma3:4b',None,lambda s:(s,{'content_safety':'PASS'}),record)
    root=tmp_path/'outputs/mp132_r02_07/project-R/requirements_segments'
    saved=list(root.glob('*/SC-AC-*.json'))
    reports=list(root.glob('*/diagnostics/*.json'))
    assert len(saved)==1 and len(reports)==2
    assert all('do-not-echo' not in p.read_text() and '\"prompt\":' not in p.read_text() for p in reports)
    assert all('UNIT_LENGTH' in p.read_text() for p in reports)
    assert len(calls)==3


def test_cor210_plan_preserved_after_failure(tmp_path):
    ctx,adapter,calls,errors,record=args(tmp_path)
    seg.execute_one(tmp_path,'project-R',ctx,adapter,None,'gemma3:4b',None,lambda s:(s,{'content_safety':'PASS'}),record)
    item=seg.progress(tmp_path,'project-R')
    assert item['completed']==1 and item['total']==3
    assert item['status']=='IN_PROGRESS'
    assert seg.PROFILE_VERSION=='r0207-acceptance-units-mip-v2'
