"""Post-G5 current authority and historical lineage; no model execution."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def test_current_and_historical_authorities_are_separate():
    r=read('.devpilot/docs_governance/source_registry.json')
    s=read('.devpilot/project_state.json')
    o=read('.devpilot/docs_governance/rebaseline_p0_overlay.json')
    assert r['reb117_sync1_state_at_merge']=='CANDIDATE_PENDING_WINDOWS_VALIDATION_AND_G5'
    assert r['reb117_sync1_state']=='G5_TECHNICAL_PASS_OWNER_RATIFICATION_PENDING'
    assert r['reb117_d05']=='CLOSED/PARTIAL_ACCEPTANCE/NOT_MVP'
    assert r['reb117_d06']=='CLOSED/PASS_WITH_DOCUMENTED_LIMITS/S1-S6'
    assert r['reb117_mp_source_registry']=='IMPORTED_AT_SYNC1/1690_ENTRIES'
    assert r['reb117_mp_stop'].startswith('ACTIVE') and r['reb117_mp_1b'].startswith('BLOCKED')
    assert r['current_phase']==s['current_phase']
    assert r['current_repo']==s['current_repo']=='evolution/multiprovider-v2'
    assert r['current_micro_sprint']==s['current_micro_sprint']=='MP132-R00-03/AUTHORITY-PUBLICATION'
    assert r['mp_last_completed_micro_sprint']==s['mp_last_completed_micro_sprint']=='MP-1A-04'
    assert r['last_registered_sprint']==s['last_registered_sprint']=='DEVPL-GSDLC-08-E'
    assert o['authority_post_g5_pre_132']['g5']=='TECHNICAL_PASS_OWNER_RATIFICATION_PENDING'
    assert o['authority']['g5']=='OWNER_RATIFIED_TECHNICAL_ONLY'
    assert o['authority']['mp_1b'].startswith('BLOCKED')
    assert o['authority_at_sync1_merge']['g5']=='PENDING'
    assert s['current_phase_at_sync1_merge']=='DEVPL-GSDLC-13'
    assert s['mp_stop_status']=='OWNER_LIFTED_INCREMENT_GATES_REMAIN'
    assert s['mp_1b_activation'].startswith('BLOCKED')

def test_no_synthetic_delivery_claims_and_documents_registered():
    r=read('.devpilot/docs_governance/source_registry.json')
    pairs={(x['doc_id'],x['path']) for x in r['documents']}
    assert len(pairs)==len(r['documents'])==1752
    for doc_id,path in [
       ('DEVPL-REB-POST-G5-130','docs/program_rebaseline_117/POST_G5_AUTHORITY_REBIND_130.md'),
       ('DEVPL-MP-OWNER-REBIND-130','docs/program_rebaseline_117/DECISION_OWNER_REBIND_130.md'),
       ('ADR-DEVPL-MP-POST-SYNC1-130','docs/02_architecture/adrs/ADR-DEVPL-MP-POST-SYNC1-130.md')]:
        assert (doc_id,path) in pairs
        assert (ROOT/path).is_file()
    assert 'OWNER_RATIFICATION_PENDING' in r['reb117_sync1_state']
    assert not r['reb117_mp_1b'].startswith('ACTIVE')
