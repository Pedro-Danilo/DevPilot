"""COR221: quality attribution, receipts, fail-closed and no silent retry."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from devpilot_core.application.r02_07_cor221 import (
    execute_structured_repair, prompt_for_target, schema_for_target,
)
from devpilot_core.application.r02_07_quality import inspect_requirements,repair_targets

SCOPE='''# MVP
| SC-IN-04 | Detectar stock bajo | P0 |
| SC-AC-05 | Stock bajo | Umbral configurable |
| SC-AC-07 | Permisos | Actor no autorizado debe ser rechazado |
| SC-AC-08 | Agentes diferidos | No hay capacidades de agente ejecutor |
- SC-DEF-01 — Agentes consultivos e informes avanzados diferidos.
'''
VISION='# Visión\nGestión prudente de stock y ventas, supervisada por Owner.\n'
ORIGINAL='''# Requisitos
## Requerimientos no funcionales
- RNF-001 — Integridad de inventario en ventas; Verificación: Prueba de conciliación saldo anterior, movimiento asociado y saldo esperado.
- RNF-002 — Consistencia de venta e inventario; Verificación: Prueba de conciliación saldo anterior, movimiento asociado y saldo esperado.
- RNF-003 — Detección de stock bajo y notificación; Verificación: Prueba de detección de stock bajo cuando la cantidad es inferior al umbral.
- RNF-004 — Asistencia de IA para informes; Verificación: Prueba funcional del asistente para generar informes.
'''
GOOD={
 'RNF-003':{'target_id':'RNF-003','quality_attribute':'consistencia',
    'control':'Consistencia de clasificación de existencias frente a una misma regla y un mismo umbral configurado, sin resultados contradictorios para un saldo confirmado.',
    'verification':'Prueba de repetición de consulta: fijar un saldo confirmado y umbral aprobado, evaluar varias veces la clasificación, comprobar que el estado se conserva sin contradicciones y registrar evidencias comparables.'},
 'RNF-004':{'target_id':'RNF-004','quality_attribute':'confidencialidad',
    'control':'Confidencialidad de los datos de ventas e inventario consultados por el propietario: la información sensible no se revela a un actor no autorizado.',
    'verification':'Prueba negativa de autorización: preparar cuentas con acceso permitido y denegado, solicitar la misma consulta y comprobar denegación sin revelación para actor no autorizado y resultado accesible al propietario autorizado.'},
}
class Fake:
 def __init__(self,bad=None):self.calls=[];self.bad=bad
 def _post_json(self,endpoint,payload,task):
    assert endpoint=='/api/generate'
    target=payload['format']['properties']['target_id']['enum'][0]
    self.calls.append(target)
    d=GOOD[target].copy()
    if target==self.bad:
       d['control']='Detección de stock bajo y notificación al propietario es una funcionalidad de negocio.'
    return SimpleNamespace(ok=True,metadata={'response':json.dumps(d),'done_reason':'stop'})

def test_two_scoped_proposals_and_exact_budget(tmp_path):
  targets=repair_targets(inspect_requirements(ORIGINAL,SCOPE))
  assert set(targets)=={'RNF-003','RNF-004'}
  fake=Fake()
  revised,info=execute_structured_repair(ORIGINAL,SCOPE,VISION,targets,'a'*64,'gemma3:4b',fake,tmp_path)
  assert fake.calls==['RNF-003','RNF-004'] and info['model_call_count']==2
  assert 'Asistencia de IA para informes' not in revised
  assert not [f for f in inspect_requirements(revised,SCOPE) if f['severity']=='BLOCK']
  rec=json.loads((tmp_path/'quality_repair_receipts'/('a'*64+'.cor221.json')).read_text())
  assert rec['status']=='PASS_VALIDATED' and rec['raw_response_stored'] is False
  with pytest.raises(ValueError,match='ALREADY_CONSUMED'):
      execute_structured_repair(ORIGINAL,SCOPE,VISION,targets,'a'*64,'gemma3:4b',fake,tmp_path)
  assert fake.calls==['RNF-003','RNF-004']

def test_rejection_contains_precise_gate_codes_no_second_call(tmp_path):
  targets=repair_targets(inspect_requirements(ORIGINAL,SCOPE));fake=Fake('RNF-003')
  with pytest.raises(ValueError,match='TARGET_REJECTED'):
      execute_structured_repair(ORIGINAL,SCOPE,VISION,targets,'b'*64,'gemma3:4b',fake,tmp_path)
  rec=json.loads((tmp_path/'quality_repair_receipts'/('b'*64+'.cor221.json')).read_text())
  assert rec['status']=='BLOCK' and rec['model_calls_started']==1 and fake.calls==['RNF-003']
  assert 'R0218_NFR_FUNCTIONAL_MASQUERADE' in rec['per_target'][0]['finding_codes']
  assert rec['raw_response_stored'] is False and 'prompt' not in json.dumps(rec).lower()

def test_crash_marker_never_replays(tmp_path):
  d=tmp_path/'quality_repair_receipts';d.mkdir()
  (d/('c'*64+'.cor221.json')).write_text('{"status":"STARTED"}')
  fake=Fake()
  with pytest.raises(ValueError,match='ALREADY_CONSUMED'):
      execute_structured_repair(ORIGINAL,SCOPE,VISION,repair_targets(inspect_requirements(ORIGINAL,SCOPE)),
                                'c'*64,'gemma3:4b',fake,tmp_path)
  assert fake.calls==[]

def test_scope_reference_required_before_call(tmp_path):
  fake=Fake()
  with pytest.raises(ValueError,match='SCOPE_REFERENCE_MISSING'):
      execute_structured_repair(ORIGINAL,'# sin criterios',VISION,{'RNF-003':set(),'RNF-004':set()},
                                'd'*64,'gemma3:4b',fake,tmp_path)
  assert fake.calls==[]

def test_single_target_is_rejected_without_calls(tmp_path):
  fake=Fake()
  with pytest.raises(ValueError,match='PRECONDITION'):
      execute_structured_repair(ORIGINAL,SCOPE,VISION,{'RNF-003':set()},'e'*64,'gemma3:4b',fake,tmp_path)
  assert fake.calls==[]

def test_target_specific_schema_and_prompt():
  assert schema_for_target('RNF-003')['properties']['quality_attribute']['enum']==['consistencia']
  assert schema_for_target('RNF-004')['properties']['quality_attribute']['enum']==['confidencialidad']
  msg=prompt_for_target('RNF-004',ORIGINAL,SCOPE,VISION)
  assert 'SC-AC-07' in msg and 'SC-AC-08' in msg and 'RNF-003 —' not in msg


def test_real_cor219_rnfs_in_memory():
  # This fixture preserves the actual two problematic nominalizations.
  body=ORIGINAL.replace('Detección de stock bajo y notificación','Detección de stock bajo y notificación al propietario')
  findings=inspect_requirements(body,SCOPE)
  assert {f['target'] for f in findings if f['severity']=='BLOCK'}=={'RNF-003','RNF-004'}

def test_successor_dispatch_only_after_consumed_cor220_failure(monkeypatch,tmp_path):
  from devpilot_core.application import r02_07_semantic as sem
  ws=tmp_path/'ws';(ws/'.devpilot').mkdir(parents=True)
  (ws/'.devpilot/project.yaml').write_text('project_id: admon_empresa_unipersonal_con_agentes\nbusiness_need: "Ventas e inventario con supervisión Owner."\n',encoding='utf8')
  for stage,content in [('product-vision',VISION),('scope',SCOPE)]:
    f=ws/sem.STAGE_PATHS[stage];f.parent.mkdir(parents=True,exist_ok=True);f.write_text(content,encoding='utf8')
  root=tmp_path/'repo'
  f=root/'outputs/pre_code_wizard/gsdlc_05_e/admon_empresa_unipersonal_con_agentes/state.json'
  f.parent.mkdir(parents=True)
  f.write_text(json.dumps({'workspace_id':'admon_empresa_unipersonal_con_agentes',
       'stages':{stage:{'status':'FROZEN','execution_id':'exec','approval_id':'approval',
         'content_sha256':sem._sha(body.encode())}
         for stage,body in [('product-vision',VISION),('scope',SCOPE)]}}),encoding='utf8')
  current=[Fake('RNF-003')]
  class Adapter:
    def __init__(self,*args,**kw):pass
    def _post_json(self,endpoint,payload,task):
      # COR220 returns 3 keys; COR221 returns 4 keys.
      target=payload['format']['properties']['target_id']['enum'][0]
      if 'quality_attribute' not in payload['format']['properties']:
        bad={'target_id':target,'control':'Detección de stock bajo y notificación al propietario',
             'verification':'Prueba de notificación: dado un umbral configurado comprobar que se genera alerta cuando el stock es bajo.'}
        current[0].calls.append(target)
        return SimpleNamespace(ok=True,metadata={'response':json.dumps(bad),'done_reason':'stop'})
      return current[0]._post_json(endpoint,payload,task)
  registry=SimpleNamespace(semantic_valid=True,get=lambda x:SimpleNamespace(
       external_api=False,requires_api_key=False,kind=SimpleNamespace(value='local'),endpoint='http://127.0.0.1:11434'))
  monkeypatch.setattr(sem.ProviderRegistry,'load',lambda root:registry)
  monkeypatch.setattr(sem,'evaluate_loopback_endpoint',lambda **kw:SimpleNamespace(ok=True))
  monkeypatch.setattr(sem,'OllamaAdapter',Adapter)
  monkeypatch.setattr(sem,'protect_generated_markdown',lambda root,content:(content,{'content_safety':'PASS'}))
  monkeypatch.setattr(sem,'requirements_output_findings',lambda content,scope:[])
  args=dict(workspace_id='admon_empresa_unipersonal_con_agentes',workspace_root=ws,stage_id='requirements',
            model='gemma3:4b',predecessor_sha256=sem._sha(ORIGINAL.encode()),previous_content=ORIGINAL)
  with pytest.raises(ValueError,match='R0220_QUALITY_BLOCK'):
    sem.generate_local_guided(root,**args)
  assert current[0].calls==['RNF-003']
  old=list((root/'outputs/mp132_r02_07/admon_empresa_unipersonal_con_agentes/requirements/quality_repair_receipts').glob('*.cor220.json'))
  assert len(old)==1
  current[0]=Fake()
  result=sem.generate_local_guided(root,**args)
  assert current[0].calls==['RNF-003','RNF-004']
  assert result['provenance']['authoring_route']=='R0221_LOCAL_MODEL_SCOPED_QUALITY'
  assert result['provenance']['repair_call_count']==2
  assert json.loads(old[0].read_text())['status']=='BLOCK'
  again=sem.generate_local_guided(root,**args)
  assert again['candidate_sha256']==result['candidate_sha256']
  assert current[0].calls==['RNF-003','RNF-004']
