"""COR220: independently generated RNF controls, no silent retry or partial DRAFT."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from devpilot_core.application.r02_07_cor220 import (
    execute_structured_repair, prompt_for_target, schema_for_target,
)
from devpilot_core.application.r02_07_quality import inspect_requirements,repair_targets

SCOPE='## MVP\nSC-IN-01 catálogo y ventas.\n## MVP+\n- SC-DEF-01 agentes consultivos e informes avanzados diferidos.\n'
VISION='# Visión\nSistema de inventario con decisiones Owner.\n'
ORIGINAL='''# Especificación de requisitos
## Requerimientos no funcionales
- RNF-001 — Integridad de datos de inventario; Verificación: Prueba integrada de saldo anterior, movimiento asociado y saldo posterior esperado.
- RNF-002 — Consistencia de datos de ventas; Verificación: Prueba de conciliación entre venta, movimiento y saldo posterior esperado.
- RNF-003 — Detección de stock bajo y notificación al propietario; Verificación: Prueba de emisión de alertas ante un umbral.
- RNF-004 — Asistencia de IA para generación de informes; Verificación: Prueba de que el asistente genera borradores.
'''
RESPONSES={
 'RNF-003': {'target_id':'RNF-003',
             'control':'Disponibilidad de las notificaciones operativas en fallos transitorios de conectividad, sin pérdida de avisos confirmados.',
             'verification':'Prueba de desconexión durante una notificación pendiente: verificar que el aviso se conserva y se entrega tras restablecer la conectividad; comprobar ausencia de duplicados.'},
 'RNF-004': {'target_id':'RNF-004',
             'control':'Confidencialidad del acceso a los datos de inventario y ventas durante consultas del propietario autenticado.',
             'verification':'Prueba negativa: con sesión sin permisos, intentar consultar datos de ventas; confirmar denegación y ausencia de revelación, y verificar que una sesión autorizada sí obtiene su información.'}}

class Fake:
 def __init__(self,fail_target=None):self.calls=[];self.fail_target=fail_target
 def _post_json(self,endpoint,payload,task):
  assert endpoint=='/api/generate'
  target=payload['format']['properties']['target_id']['enum'][0]
  self.calls.append(target)
  assert payload['options']['num_predict']==950
  p=dict(RESPONSES[target])
  if target==self.fail_target:p['control']='Detección de stock bajo y notificación al propietario'
  return SimpleNamespace(ok=True,metadata={'response':json.dumps(p), 'done_reason':'stop'})

def run(tmp_path,fail_target=None):
 targets=repair_targets(inspect_requirements(ORIGINAL,SCOPE))
 assert sorted(targets)==['RNF-003','RNF-004']
 fake=Fake(fail_target)
 return execute_structured_repair(ORIGINAL,SCOPE,VISION,targets,'a'*64,'gemma3:4b',fake,tmp_path),fake

def test_two_independent_calls_generate_quality_only(tmp_path):
 (result,summary),fake=run(tmp_path)
 assert fake.calls==['RNF-003','RNF-004']
 assert summary['model_call_count']==2
 assert all(x not in result for x in ['Asistencia de IA para generación de informes','Detección de stock bajo y notificación al propietario'])
 assert result.split('RNF-003')[0]==ORIGINAL.split('RNF-003')[0]
 assert not [f for f in inspect_requirements(result,SCOPE) if f['severity']=='BLOCK']
 receipt=json.loads((tmp_path/('quality_repair_receipts/'+'a'*64+'.cor220.json')).read_text())
 assert receipt['status']=='PASS_VALIDATED' and receipt['raw_response_stored'] is False
 assert not any('control' in x for x in receipt['per_target'])
 with pytest.raises(ValueError,match='ALREADY_CONSUMED'):run(tmp_path)

def test_partial_failure_persists_and_never_retries(tmp_path):
 targets=repair_targets(inspect_requirements(ORIGINAL,SCOPE));fake=Fake('RNF-004')
 with pytest.raises(ValueError,match='R0220_QUALITY_BLOCK'):
  execute_structured_repair(ORIGINAL,SCOPE,VISION,targets,'b'*64,'gemma3:4b',fake,tmp_path)
 rec=json.loads((tmp_path/('quality_repair_receipts/'+'b'*64+'.cor220.json')).read_text())
 assert rec['status']=='BLOCK' and rec['model_calls_started']==2
 assert rec['per_target'][0]['status']=='PASS' and rec['per_target'][1]['status']=='BLOCK'
 with pytest.raises(ValueError,match='ALREADY_CONSUMED'):
  execute_structured_repair(ORIGINAL,SCOPE,VISION,targets,'b'*64,'gemma3:4b',fake,tmp_path)
 assert len(fake.calls)==2

def test_crash_marker_blocks_retry_before_provider_call(tmp_path):
 folder=tmp_path/'quality_repair_receipts';folder.mkdir()
 (folder/('c'*64+'.cor220.json')).write_text('{"schema":"R0220.structured_repair.v1","status":"STARTED"}')
 fake=Fake()
 with pytest.raises(ValueError,match='ALREADY_CONSUMED'):
  execute_structured_repair(ORIGINAL,SCOPE,VISION,{'RNF-003':{'control','verification'}},'c'*64,'gemma3:4b',fake,tmp_path)
 assert not fake.calls

def test_reject_budget_over_two_without_call(tmp_path):
 fake=Fake()
 with pytest.raises(ValueError,match='BOUNDED_TARGETS_REQUIRED'):
  execute_structured_repair(ORIGINAL,SCOPE,VISION,{'RNF-001':set(),'RNF-002':set(),'RNF-003':set()},'d'*64,'gemma3:4b',fake,tmp_path)
 assert not fake.calls

def test_prompt_is_individual_and_scope_bound():
 out=prompt_for_target('RNF-004',ORIGINAL,SCOPE,VISION,['R0218_DEFERRED_CAPABILITY_COMMITTED'])
 assert 'RNF-004' in out and 'SC-DEF-01' in out and 'RNF-003 —' not in out
 assert schema_for_target('RNF-004')['properties']['target_id']['enum']==['RNF-004']

def test_proposed_rnf_from_other_domain():
 doc='- RNF-001 — Confidencialidad de expedientes médicos; Verificación: Prueba de acceso sin permisos; comprobar que ningún expediente se revela.\n'
 assert not [x for x in inspect_requirements(doc,'') if x['severity']=='BLOCK']

def test_end_to_end_new_route_with_2_calls_and_same_input_cache(monkeypatch,tmp_path):
    """Contract through existing Multiprovider service, not a shadow endpoint."""
    from devpilot_core.application import r02_07_semantic as sem
    workspace=tmp_path/'ws';(workspace/'.devpilot').mkdir(parents=True)
    (workspace/'.devpilot/project.yaml').write_text(
        'project_id: admon_empresa_unipersonal_con_agentes\n'
        'business_need: "Ventas e inventario local con permisos."\n',encoding='utf8')
    scope='## MVP\n| SC-IN-01 | Catálogo de productos | P0 | Registro de catálogo | MVP |\n## MVP+\n- SC-DEF-01 — Asistencia de IA diferida.\n'
    vision='# Visión\nVentas e inventario auditables con supervisión Owner.\n'
    for stage,body in [('product-vision',vision),('scope',scope)]:
        p=workspace/sem.STAGE_PATHS[stage];p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body,encoding='utf8')
    root=tmp_path/'repo'
    state=root/'outputs/pre_code_wizard/gsdlc_05_e/admon_empresa_unipersonal_con_agentes/state.json'
    state.parent.mkdir(parents=True)
    state.write_text(json.dumps({'workspace_id':'admon_empresa_unipersonal_con_agentes','stages':{
        name:{'status':'FROZEN','execution_id':'exec','approval_id':'approval','content_sha256':sem._sha(body.encode())}
        for name,body in [('product-vision',vision),('scope',scope)]}}),encoding='utf8')
    fake=Fake()
    class Adapter:
        def __init__(self,*args,**kwargs):pass
        def _post_json(self,endpoint,payload,task):return fake._post_json(endpoint,payload,task)
    registry=SimpleNamespace(semantic_valid=True,get=lambda x:SimpleNamespace(
        external_api=False,requires_api_key=False,kind=SimpleNamespace(value='local'),endpoint='http://127.0.0.1:11434'))
    monkeypatch.setattr(sem.ProviderRegistry,'load',lambda root:registry)
    monkeypatch.setattr(sem,'evaluate_loopback_endpoint',lambda **kw:SimpleNamespace(ok=True))
    monkeypatch.setattr(sem,'OllamaAdapter',Adapter)
    monkeypatch.setattr(sem,'protect_generated_markdown',lambda root,content:(content,{'content_safety':'PASS'}))
    monkeypatch.setattr(sem,'requirements_output_findings',lambda content,scope:[])
    original=ORIGINAL
    result=sem.generate_local_guided(root,workspace_id='admon_empresa_unipersonal_con_agentes',
        workspace_root=workspace,stage_id='requirements',model='gemma3:4b',
        predecessor_sha256=sem._sha(original.encode()),previous_content=original)
    assert fake.calls==['RNF-003','RNF-004']
    assert result['provenance']['authoring_route']=='R0220_LOCAL_MODEL_PER_RNF'
    assert result['provenance']['repair_call_count']==2
    assert result['provenance']['original_segment_checkpoints_preserved']
    assert result['provenance']['semantic_quality_approval'] is False
    same=sem.generate_local_guided(root,workspace_id='admon_empresa_unipersonal_con_agentes',
        workspace_root=workspace,stage_id='requirements',model='gemma3:4b',
        predecessor_sha256=sem._sha(original.encode()),previous_content=original)
    assert same['candidate_sha256']==result['candidate_sha256']
    assert len(fake.calls)==2
