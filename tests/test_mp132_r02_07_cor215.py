"""COR215: structured local proposal is never an automatic semantic PASS."""
import importlib.util
import json
from pathlib import Path
import pytest

source=Path(__file__).resolve().parents[1]/'src/devpilot_core/application/r02_07_segmented.py'
spec=importlib.util.spec_from_file_location('seg215_test',source)
seg=importlib.util.module_from_spec(spec)
spec.loader.exec_module(seg)
MODEL='gemma3:4b'

@pytest.fixture
def unit():
    return {'id':'GLOBAL','kind':'global','rf_id':'','source_id':'','criterion_id':'',
        'transverse_ids':'SC-AC-07,SC-AC-08',
        'criteria':'SC-AC-07 | El acceso a catálogo necesita autorización del cliente\nSC-AC-08 | Agentes consultivos sujetos a revisión y autorización del dueño'}

def proposed(unit):
    rows=seg._global_source_rows(unit)
    return {'nfrs':[
        {'control':'Limitar el acceso a catálogo según autorización documentada del cliente.',
         'verification':'Prueba de acceso denegado cuando no haya autorización.'},
        {'control':'Registrar trazabilidad consultiva de operaciones con integridad de registros.',
         'verification':'Inspección del registro de auditoría para identificar acciones.'},
        {'control':'Mantener integridad de las respuestas frente a entradas sin contexto.',
         'verification':'Prueba negativa de operaciones inconsistentes sin contexto.'}],
       'coverage':[
         {'criterion_id':'SC-AC-07','source_anchor':'acceso a catálogo',
          'control':'El acceso a catálogo deberá requerir autorización válida del cliente.',
          'verification':'Prueba de acceso a catálogo denegado sin autorización del cliente.',
          'status':'PROPOSED'},
         {'criterion_id':'SC-AC-08','source_anchor':'Agentes consultivos',
          'control':'Los agentes consultivos no ejecutan cambios sin autorización del dueño.',
          'verification':'Prueba negativa de agentes consultivos sin autorización del dueño.',
          'status':'PROPOSED'}],
       'restrictions':[], 'pending_decisions':[]}

def test_schema_derived_from_frozen(unit):
    schema=seg.structured_schema(unit)
    assert schema['properties']['coverage']['minItems']==2
    assert set(schema['properties']['coverage']['items']['properties']['criterion_id']['enum'])=={'SC-AC-07','SC-AC-08'}
    assert seg.STRUCTURED_PROFILE_VERSION!=seg.PROFILE_VERSION

def test_real_semantic_content_rendered_without_fabrication(unit):
    obj=proposed(unit)
    assert seg.validate_structured_global(obj,unit)==[]
    body=seg.render_structured_global(obj,unit)
    assert seg.validate_unit(body,unit)==[]
    assert body.count('RNF-')==3 and body.index('SC-AC-07')<body.index('SC-AC-08')

def test_missing_duplicate_or_unknown_identity_block(unit):
    import copy
    for modify in ('missing','duplicate','unknown'):
        obj=copy.deepcopy(proposed(unit))
        if modify=='missing':obj['coverage'].pop()
        if modify=='duplicate':obj['coverage'][1]['criterion_id']='SC-AC-07'
        if modify=='unknown':obj['coverage'][1]['criterion_id']='SC-AC-99'
        assert seg.validate_structured_global(obj,unit)
        with pytest.raises(ValueError,match='R0215_STRUCTURED_NOT_CONFORMANT'):
            seg.render_structured_global(obj,unit)

def test_wrong_source_anchor_does_not_count_as_coverage(unit):
    obj=proposed(unit)
    obj['coverage'][0]['source_anchor']='cliente extranjero'
    assert 'STRUCTURED_SOURCE_ANCHOR_INVALID' in seg.validate_structured_global(obj,unit)

def test_owner_decision_cannot_be_silent_pass(unit):
    obj=proposed(unit)
    obj['coverage'][0]['status']='DECISION_REQUIRED'
    assert 'STRUCTURED_DECISION_REQUIRED' in seg.validate_structured_global(obj,unit)

def test_missing_verification_does_not_pass(unit):
    obj=proposed(unit);obj['nfrs'][0]['verification']='El sistema responde con el proceso realizado.'
    assert set(seg.validate_structured_global(obj,unit)) & {'STRUCTURED_NFR_VERIFICATION','STRUCTURED_NFR_INCOMPLETE'}

def test_unrelated_criterion_rejected(unit):
    obj=proposed(unit);obj['coverage'][1]['control']='La calidad y velocidad de los equipos de oficina es evaluada.'
    obj['coverage'][1]['verification']='Prueba de calidad y velocidad de los equipos de oficina.'
    assert 'STRUCTURED_COVERAGE_GROUNDING_WEAK' in seg.validate_structured_global(obj,unit)

def test_prompt_does_not_claim_approval(unit):
    assert 'no inventes' in seg.structured_prompt(unit,'Contexto FROZEN').lower()
    assert 'SC-AC-07' in seg.structured_prompt(unit,'Contexto FROZEN')

def test_three_domains_contract_independence():
    for name,control in (
        ('atención a pacientes','El acceso a atención a pacientes requiere trazabilidad de solicitudes'),
        ('biblioteca académica','El acceso a biblioteca académica requiere trazabilidad de préstamos'),
        ('logística regional','El acceso a logística regional requiere trazabilidad de entregas')):
        u={'id':'GLOBAL','kind':'global','transverse_ids':'SC-AC-01',
           'criteria':f'SC-AC-01 | Control de acceso y trazabilidad de {name}'}
        obj={'nfrs':[
            {'control':f'El servicio de {name} debe mantener control documentado de clase {n}.',
             'verification':f'Prueba de trazabilidad en servicio de {name} para clase {n}.'} for n in range(3)],
             'coverage':[{'criterion_id':'SC-AC-01','source_anchor':'Control de acceso',
             'control':f'Control de acceso y trazabilidad de {name} mediante autorización verificable.',
             'verification':f'Prueba de acceso y trazabilidad en {name} sin autorización.',
             'status':'PROPOSED'}], 'restrictions':[],'pending_decisions':[]}
        assert seg.validate_structured_global(obj,u)==[]
        assert 'SC-AC-01' in seg.render_structured_global(obj,u)

def context_plan(unit):
    ctx={'upstream':{'scope':'Scope FROZEN','product-vision':'Vision FROZEN'},
         'upstream_hashes':{'scope':'a'*64,'product-vision':'b'*64},
         'source_sha256':'c'*64,'predecessor_sha256':'d'*64}
    input={'profile':seg.PROFILE_VERSION,'workspace_id':'pilot','context_hashes':ctx['upstream_hashes'],
           'source':ctx['source_sha256'],'model':MODEL,'previous':ctx['predecessor_sha256'],
           'obligations':[unit]}
    return ctx,seg.sha(json.dumps(input,ensure_ascii=False,sort_keys=True))

def setup_legacy(folder,unit,ph):
    diag=folder/'diagnostics';diag.mkdir(parents=True)
    for n,findings in enumerate((
       ['GLOBAL_ACCEPTANCE_NOT_COVERED','NFR_IDS_MISSING','NFR_VERIFICATION_MISSING'],
       ['GLOBAL_ACCEPTANCE_NOT_COVERED'],['GLOBAL_ACCEPTANCE_NOT_COVERED']),1):
        (diag/f'GLOBAL.attempt-{n:02d}.json').write_text(json.dumps({
            'schema':'R0210.unit_failure.v1','plan_hash':ph,'unit_id':'GLOBAL',
            'model':MODEL,'rf_id':'','source_id':'','criterion_id':'','attempt':n,
            'code':'R0207_SEGMENT_NOT_CONFORMANT','finding_codes':findings,
            'field_diagnostics':{'GLOBAL_NFR_ROWS':'3','GLOBAL_NFR_VERIFIED':'3',
                'GLOBAL_COVERAGE_MISSES':'2'} if n>1 else {}}))
    files=[diag/f'GLOBAL.attempt-{n:02d}.json' for n in range(1,4)]
    marker={'schema':'R0215.owner_structured_opt_in.v1','plan_hash':ph,'workspace_id':'pilot',
        'model':MODEL,'unit_id':'GLOBAL','profile':seg.STRUCTURED_PROFILE_VERSION,
        'max_calls':seg.STRUCTURED_MAX_ATTEMPTS,
        'legacy_receipt_hashes':[__import__('hashlib').sha256(f.read_bytes()).hexdigest() for f in files]}
    return marker

class Adapter:
    def __init__(self,body):self.body=body;self.calls=0;self.last=None
    def _post_json(self,endpoint,payload,task=None):
        self.calls+=1;self.last=payload
        return type('Reply',(),{'ok':True,'metadata':{'response':self.body,'done_reason':'stop'}})()

def test_three_failed_legacy_calls_are_not_reset_or_hidden(unit,tmp_path,monkeypatch):
    monkeypatch.setattr(seg,'plan_from_scope',lambda *args:[unit])
    ctx,ph=context_plan(unit)
    folder=tmp_path/'outputs/mp132_r02_07/pilot/requirements_segments'/ph
    marker=setup_legacy(folder,unit,ph)
    adapter=Adapter(json.dumps(proposed(unit),ensure_ascii=False))
    safety=lambda text:(text,{'content_safety':'PASS'})
    with pytest.raises(ValueError,match='EXPLICIT_RETRY_BUDGET_EXHAUSTED'):
        seg.execute_one(tmp_path,'pilot',ctx,adapter,None,MODEL,None,safety,lambda *a:None)
    assert adapter.calls==0
    seg.atomic_json(folder/'structured_authorization.json',marker)
    before=[(folder/'diagnostics'/f'GLOBAL.attempt-{n:02d}.json').read_bytes() for n in range(1,4)]
    outcome=seg.execute_one(tmp_path,'pilot',ctx,adapter,None,MODEL,None,safety,lambda *a:None)
    assert outcome['partial']==False
    assert adapter.last['format']['type']=='object'
    assert adapter.calls==1 and (folder/'GLOBAL.json').is_file()
    assert [ (folder/'diagnostics'/f'GLOBAL.attempt-{n:02d}.json').read_bytes() for n in range(1,4)]==before
    assert seg.read_json(folder/'GLOBAL.json')['identity_binding']['owner_review_required'] is True
    # Resume is fully idempotent, no second model call.
    assert not seg.execute_one(tmp_path,'pilot',ctx,adapter,None,MODEL,None,safety,lambda *a:None)['partial']
    assert adapter.calls==1

def test_two_structured_rejections_block_third_without_losing_legacy(unit,tmp_path,monkeypatch):
    monkeypatch.setattr(seg,'plan_from_scope',lambda *args:[unit])
    ctx,ph=context_plan(unit)
    folder=tmp_path/'outputs/mp132_r02_07/pilot/requirements_segments'/ph
    seg.atomic_json(folder/'structured_authorization.json',setup_legacy(folder,unit,ph))
    adapter=Adapter('{not-json')
    for n in (1,2):
        with pytest.raises(ValueError,match='R0207_SEGMENT_NOT_CONFORMANT'):
            seg.execute_one(tmp_path,'pilot',ctx,adapter,None,MODEL,None,lambda x:(x,{'content_safety':'PASS'}),lambda *a:None)
        assert seg.read_json(folder/f'diagnostics/GLOBAL_STRUCTURED.attempt-{n:02d}.json')['finding_codes']==['STRUCTURED_JSON_INVALID']
    with pytest.raises(ValueError,match='EXPLICIT_RETRY_BUDGET_EXHAUSTED'):
        seg.execute_one(tmp_path,'pilot',ctx,adapter,None,MODEL,None,lambda x:(x,{'content_safety':'PASS'}),lambda *a:None)
    assert adapter.calls==2

def test_tampered_source_or_receipt_disables_authorization(unit,tmp_path):
    ctx,ph=context_plan(unit)
    folder=tmp_path/'outputs/mp132_r02_07/pilot/requirements_segments'/ph
    seg.atomic_json(folder/'structured_authorization.json',setup_legacy(folder,unit,ph))
    assert seg.structured_authorized(folder,unit,ph,MODEL,'pilot')
    f=folder/'diagnostics/GLOBAL.attempt-03.json'
    data=json.loads(f.read_text());data['plan_hash']='0'*64;f.write_text(json.dumps(data))
    assert not seg.structured_authorized(folder,unit,ph,MODEL,'pilot')


def test_duplicate_nonfunctional_control_is_rejected(unit):
    obj=proposed(unit);obj['nfrs'][1]['control']=obj['nfrs'][0]['control']
    assert 'STRUCTURED_DUPLICATE_NFR' in seg.validate_structured_global(obj,unit)

def test_correct_prohibition_not_incorrectly_blocked(unit):
    obj=proposed(unit)
    obj['coverage'][1]['control']='Los agentes consultivos no ejecutan cambios sin autorización del dueño.'
    assert seg.validate_structured_global(obj,unit)==[]
    assert 'AGENT_AUTHORITY_CONTRADICTION' not in seg.validate_unit(seg.render_structured_global(obj,unit),unit)
