"""COR214 - GLOBAL recovery: bounded, tamper-resistant, no implied approval."""
import importlib.util
import json
from pathlib import Path
import pytest

try:
    from devpilot_core.application import r02_07_segmented as seg
except ImportError:
    source=Path(__file__).resolve().parents[1]/'src/devpilot_core/application/r02_07_segmented.py'
    spec=importlib.util.spec_from_file_location('seg_cor214',source)
    seg=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seg)

PLAN='74b27b891ce2220164348d7dbb7ca3a4a7024fc521e121eb4514b78f6e85a7dd'
MODEL='gemma3:4b'
UNIT={'id':'GLOBAL','kind':'global','rf_id':'','source_id':'','criterion_id':'',
      'transverse_ids':'SC-AC-07,SC-AC-08',
      'criteria':'SC-AC-07 | Control de accesos y autorización FROZEN\nSC-AC-08 | Agentes y autorización limitada FROZEN'}
FIND1=['GLOBAL_ACCEPTANCE_NOT_COVERED','NFR_IDS_MISSING','NFR_VERIFICATION_MISSING']
FIND2=['GLOBAL_ACCEPTANCE_NOT_COVERED']

def receipts(tmp_path):
    rows=[]
    for i,codes in enumerate((FIND1,FIND2),1):
        p=tmp_path/f'GLOBAL.attempt-{i:02d}.json'
        record={'schema':'R0210.unit_failure.v1','plan_hash':PLAN,'unit_id':'GLOBAL',
            'rf_id':'','source_id':'','criterion_id':'','model':MODEL,
            'attempt':i,'code':'R0207_SEGMENT_NOT_CONFORMANT','finding_codes':codes,
            'field_diagnostics':{'GLOBAL_NFR_ROWS':'3','GLOBAL_NFR_VERIFIED':'3','GLOBAL_COVERAGE_MISSES':'2'} if i==2 else {}}
        p.write_text(json.dumps(record), encoding='utf8')
        rows.append(p)
    return rows

def test_exact_history_allows_one_explicit_repair(tmp_path):
    assert seg.is_global_coverage_repair_allowed(receipts(tmp_path),UNIT,PLAN,MODEL)

def test_no_receipts_or_other_unit_or_model_block(tmp_path):
    paths=receipts(tmp_path)
    assert not seg.is_global_coverage_repair_allowed([],UNIT,PLAN,MODEL)
    assert not seg.is_global_coverage_repair_allowed(paths,{**UNIT,'id':'SC-AC-07'},PLAN,MODEL)
    assert not seg.is_global_coverage_repair_allowed(paths,UNIT,PLAN,'other')

def test_tampered_second_receipt_blocks(tmp_path):
    paths=receipts(tmp_path)
    for k,v in [('plan_hash','f'*64),('code','OTHER'),('attempt',1),('model','other'),('finding_codes',['NFR_IDS_MISSING'])]:
        record=json.loads(paths[1].read_text());record[k]=v
        paths[1].write_text(json.dumps(record))
        assert not seg.is_global_coverage_repair_allowed(paths,UNIT,PLAN,MODEL)
        receipts(tmp_path)

def test_negative_missing_coverage_count_is_block(tmp_path):
    paths=receipts(tmp_path)
    record=json.loads(paths[1].read_text());record['field_diagnostics']['GLOBAL_COVERAGE_MISSES']='0'
    paths[1].write_text(json.dumps(record))
    assert not seg.is_global_coverage_repair_allowed(paths,UNIT,PLAN,MODEL)

def test_symlink_receipt_rejected_without_symlink_privilege(tmp_path,monkeypatch):
    paths=receipts(tmp_path)
    original=Path.is_symlink
    monkeypatch.setattr(Path,'is_symlink',lambda p: True if p==paths[1] else original(p))
    with pytest.raises(ValueError,match='R0207_SEGMENT_STATE_UNAVAILABLE'):
        seg.is_global_coverage_repair_allowed(paths,UNIT,PLAN,MODEL)

def test_scaffold_requires_exact_frozen_criteria():
    prompt=seg.global_coverage_repair_instruction(UNIT)
    assert '- SC-AC-07:' in prompt and '- SC-AC-08:' in prompt
    assert 'SC-AC-07 | Control de accesos' in prompt
    assert 'RNF-001' in prompt and '## Restricciones' in prompt
    for invalid in ({**UNIT,'criteria':'SC-AC-07 | Solo uno'},
                    {**UNIT,'transverse_ids':'SC-AC-07,SC-AC-07'},
                    {**UNIT,'criteria':'SC-AC-07 | X\nSC-AC-09 | Y'}):
        with pytest.raises(ValueError,match='R0214_GLOBAL_CRITERIA'):
            seg.global_coverage_repair_instruction(invalid)

VALID='''## Requisitos no funcionales
- RNF-001 — Acceso a información según autorización del titular y contexto FROZEN; Verificación: prueba negativa del control de acceso.
- RNF-002 — Registro auditable de operaciones sensibles con identidad autorizada; Verificación: inspección de registros de auditoría.
- RNF-003 — Integridad de cambios transaccionales autorizados sin escritura parcial; Verificación: prueba de reversión ante fallo.
## Restricciones
- SC-AC-07: control de acceso sujeto a restricciones FROZEN y evidencia de verificación mediante prueba de intento no autorizado.
## Decisiones pendientes
- SC-AC-08: decisión pendiente de política para acciones de agentes, sin autorizar ejecución de acciones sensibles; verificación mediante inspección de decisión.
'''

def test_global_conformity_still_enforced():
    assert seg.validate_unit(VALID,UNIT)==[]
    modified=VALID.replace('- SC-AC-08:', '- OTHER:')
    assert 'GLOBAL_ACCEPTANCE_NOT_COVERED' in seg.validate_unit(modified,UNIT)

def test_accepted_checkpoints_are_not_rewritten_by_normalization():
    data='### RF-001 — Hecho\n- Tipo: funcional\n'
    result,meta,codes=seg.bind_global_nfr_ids(data,{'kind':'functional'})
    assert result==data and not codes

class _Response:
    ok=True
    metadata={'response':VALID,'done_reason':'stop','eval_count':300}

class _Adapter:
    def __init__(self, response=VALID):
        self.calls=0;self.response=response;self.options=[]
    def _post_json(self,endpoint,payload,task=None):
        self.calls+=1
        self.options.append(payload['options'])
        return type('Reply',(),{'ok':True,'metadata':{'response':self.response,'done_reason':'stop','eval_count':320}})()

def _runtime_with_two_failures(tmp_path, monkeypatch):
    monkeypatch.setattr(seg,'plan_from_scope',lambda scope,vision:[UNIT])
    upstream={'scope':'Scope FROZEN','product-vision':'Vision FROZEN'}
    ctx={'upstream':upstream,'upstream_hashes':{'scope':'a'*64,'product-vision':'b'*64},
         'source_sha256':'c'*64,'predecessor_sha256':'d'*64}
    plan_input={'profile':seg.PROFILE_VERSION,'workspace_id':'pilot',
                'context_hashes':ctx['upstream_hashes'],'source':ctx['source_sha256'],
                'model':MODEL,'previous':ctx['predecessor_sha256'],'obligations':[UNIT]}
    ph=seg.sha(json.dumps(plan_input,sort_keys=True,ensure_ascii=False))
    folder=tmp_path/'outputs/mp132_r02_07/pilot/requirements_segments'/ph
    diag=folder/'diagnostics';diag.mkdir(parents=True)
    for i,source in enumerate(receipts(tmp_path),1):
        data=json.loads(source.read_text());data['plan_hash']=ph
        (diag/source.name).write_text(json.dumps(data),encoding='utf8')
    safety=lambda t:(t,{'content_safety':'PASS'})
    return ctx,folder,safety

def test_exact_third_attempt_succeeds_without_rewriting_existing_history(tmp_path,monkeypatch):
    ctx,folder,safety=_runtime_with_two_failures(tmp_path,monkeypatch)
    before=[(folder/'diagnostics'/f'GLOBAL.attempt-{i:02d}.json').read_bytes() for i in (1,2)]
    adapter=_Adapter()
    outcome=seg.execute_one(tmp_path,'pilot',ctx,adapter,None,MODEL,None,safety,lambda *a:None)
    assert not outcome['partial'] and adapter.calls==1
    assert adapter.options[0]['num_ctx']==6144
    assert (folder/'GLOBAL.json').is_file()
    assert (folder/'assembly_status.json').is_file()
    after=[(folder/'diagnostics'/f'GLOBAL.attempt-{i:02d}.json').read_bytes() for i in (1,2)]
    assert before==after
    second=seg.execute_one(tmp_path,'pilot',ctx,adapter,None,MODEL,None,safety,lambda *a:None)
    assert not second['partial'] and adapter.calls==1

def test_third_failure_exhausts_budget_without_fourth_inference(tmp_path,monkeypatch):
    ctx,folder,safety=_runtime_with_two_failures(tmp_path,monkeypatch)
    adapter=_Adapter(VALID.replace('- SC-AC-08:', '- N/A:'))
    with pytest.raises(ValueError,match='R0207_SEGMENT_NOT_CONFORMANT'):
        seg.execute_one(tmp_path,'pilot',ctx,adapter,None,MODEL,None,safety,lambda *a:None)
    assert adapter.calls==1 and (folder/'diagnostics/GLOBAL.attempt-03.json').is_file()
    with pytest.raises(ValueError,match='R0210_EXPLICIT_RETRY_BUDGET_EXHAUSTED'):
        seg.execute_one(tmp_path,'pilot',ctx,adapter,None,MODEL,None,safety,lambda *a:None)
    assert adapter.calls==1
