from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(path:str):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

def test_mp1a_closure_contract_and_zero_model_full():
    text=(ROOT/'docs/audits/MP1A_CLOSURE.md').read_text(encoding='utf-8')
    for marker in ['MP-1A-01','MP-1A-02','MP-1A-03','MP-1A-04','Product Vision → MVP Scope → Requirements','real model calls = 0','ExternalModel = disabled','Full=0']:
        assert marker in text

def test_stop_gate_is_program_gate_and_sync1_only_resume():
    stop=load('docs/audits/MP1A_STOP_GATE.json')
    assert stop['schema_id']=='devpilot.mp1a.stop-gate.v1'
    assert stop['status'] in {'ARMED/WINDOWS-VALIDATION-PENDING','ACTIVE/STOP-MULTIPROVIDER'}
    assert stop['multiprovider_mutation_allowed_after_activation'] is False
    assert stop['next_track']=='deterministic'
    assert stop['sync_direction']=='deterministic->multiprovider'
    assert stop['resume_gate']=='SYNC-1 PASS'
    assert stop['required_before_resume']==['D05 CLOSED/PASS|PASS+FINDING','D06 CLOSED/PASS|PASS+FINDING','SYNC-1 PASS']

def test_findings_have_no_s0_s1_and_only_nonblocking_s2():
    f=load('docs/audits/MP1A_FINDINGS.json')
    assert f['s0_open']==0 and f['s1_open']==0
    assert all(x['severity']=='S2' and x['blocking_mp1a_closure'] is False for x in f['findings'])
    assert any(x['id']=='MP1A01-CROSS-STAGE-DECISION-LINEAGE' and x['status']=='RESOLVED-IN-MP-1A-02' for x in f['findings'])

def test_registry_points_to_mp1a04_and_contracts_exist():
    r=load('.devpilot/docs_governance/source_registry.json')
    assert r['current_micro_sprint']=='MP-1A-04'
    assert r['mp_1a_03_status']=='CLOSED/PASS/WINDOWS-ADJUDICATED'
    assert r['mp_1a_04_full_regression_runs']==0
    assert r['mp_1a_next_track']=='deterministic'
    paths={x['path'] for x in r['documents'] if isinstance(x,dict)}
    for p in ['docs/audits/MP1A_CLOSURE.md','docs/audits/MP1A_FINDINGS.json','docs/audits/MP1A_STOP_GATE.json','tests/test_mp1a04_closure_stop.py']:
        assert p in paths and (ROOT/p).exists()

def test_a03_is_windows_closed_and_provider_boundary_remains_generation_only():
    a03=(ROOT/'docs/audits/MP1A03_DETERMINISTIC_PROVIDER.md').read_text(encoding='utf-8')
    provider=(ROOT/'src/devpilot_core/generation/product_definition.py').read_text(encoding='utf-8')
    ui=(ROOT/'ui/web/src/pages/PreCodeWizardView.ts').read_text(encoding='utf-8')
    assert 'CLOSED / PASS / WINDOWS-ADJUDICATED' in a03
    for marker in ['provider source/apply/freeze authority: none','model calls: 0','external API/network: 0']:
        assert marker in a03
    for marker in ['source_write', 'apply_authority', 'freeze_authority']:
        assert marker in provider
    assert "LLM ejecutado ${d.model_execution_used?'sí':'no'}" in ui
    assert 'API externa ${d.external_api_used' in ui
