"""MP132 R00-03: verify governance authority without authorizing runtime operations."""
from pathlib import Path
import json,hashlib,re
from devpilot_core.docs_governance.mp132_historical import load_verified_r00_at_close
ROOT=Path(__file__).resolve().parents[1]
PREFIX="docs/programs/DEVPL_MP_SUCCESSOR_132/v1_1_0_owner_approved_133/"
def obj(rel):return json.loads((ROOT/rel).read_text(encoding="utf-8"))
def test_mp132_57_documents_byte_verified():
    frozen=load_verified_r00_at_close(ROOT)
    r=frozen['registry'];rows=frozen['rows']
    assert len(rows)==57
    assert len({x['doc_id'] for x in rows})==len({x['path'] for x in rows})==57
    # Strict original SHA-256 checks are performed by the verifier for all 56
    # non-self-hashed documents against the real R00 manifest (canonical LF).
    # The 57 original files, registry, state and overlay are all attested.
    assert len(frozen['provenance']['files'])==60
def test_mp132_authority_reconciled_and_guards_closed():
    frozen=load_verified_r00_at_close(ROOT)
    r=frozen['registry'];s=frozen['state'];o=frozen['overlay']
    assert len(r['documents'])==1752
    assert r['summary']['documents_total']==1752
    assert r['current_phase']==s['current_phase']=='DEVPL-MP-SUCCESSOR-132/R00-AUTHORITY-REBIND'
    assert r['current_micro_sprint']==s['current_micro_sprint']=='MP132-R00-03/AUTHORITY-PUBLICATION'
    assert s['mp_stop_status']==o['authority']['multiprovider_stop']=='OWNER_LIFTED_INCREMENT_GATES_REMAIN'
    assert s['mp_g5_adjudication']==o['authority']['g5']=='OWNER_RATIFIED_TECHNICAL_ONLY'
    assert s['mp_1b_activation']=='BLOCKED_UNTIL_SPECIFIC_INCREMENT_APPROVAL'
    assert o['mp132_successor']['mp_1b']=='NOT_AUTHORIZED'
    assert o['mp132_successor']['external_egress']=='DENIED'
    assert r['mp132_authority']['r00_02_gate']=='MIGRATED_B_PASS'
    assert r['mp132_authority']['v131']=='SUPERSEDED_FOR_PLANNING/HISTORICAL_ONLY'
    assert s['mp_current_authority_document']==r['mp132_authority']['program_path']
def test_mp132_legacy_snapshots_unchanged_and_no_live_external():
    s=obj('.devpilot/project_state.json');o=obj('.devpilot/docs_governance/rebaseline_p0_overlay.json');r=obj('.devpilot/docs_governance/source_registry.json')
    assert s['current_phase_at_sync1_merge']=='DEVPL-GSDLC-13'
    assert o['authority_at_sync1_merge']['multiprovider_stop']=='ACTIVE'
    assert o['authority_post_g5_pre_132']['g5']=='TECHNICAL_PASS_OWNER_RATIFICATION_PENDING'
    assert r['reb117_sync1_state']=='G5_TECHNICAL_PASS_OWNER_RATIFICATION_PENDING'
    assert r['reb117_mp_stop'].startswith('ACTIVE')
    assert o['mp132_successor']['v131']=='SUPERSEDED_FOR_PLANNING/HISTORICAL_ONLY'

def test_b_migration_adr_successors_registered():
    r=obj('.devpilot/docs_governance/source_registry.json')
    paths={x['path'] for x in r['documents']}
    for name in ('ADR_MP132_008_S1_141.md','ADR_MP132_008_S2_142.md'):
        p='docs/02_architecture/adrs/'+name
        assert p in paths and (ROOT/p).is_file()
