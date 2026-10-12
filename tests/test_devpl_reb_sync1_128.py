from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_sync1_one_generation_authority_and_no_early_mp_activation():
    from devpilot_core.generation.contracts import GenerationRequest, ArtifactCandidateEnvelope
    from devpilot_core.application.story_implementation_candidate_service import StoryImplementationCandidateApplicationService
    from devpilot_core.application.story_general_provider import GeneralStoryProvider
    assert GenerationRequest and ArtifactCandidateEnvelope and GeneralStoryProvider and StoryImplementationCandidateApplicationService
    doc=(ROOT/'docs/02_architecture/adrs/ADR-DEVPL-REB-SYNC1-128.md').read_text(encoding='utf-8')
    assert 'experimental' in doc and 'STOP' in doc and 'ArtifactCandidateEnvelope' in doc
    assert 'No hay permiso para activar ExternalModel' in doc

def test_sync1_registry_retains_both_historic_authorities_and_identity():
    r=json.loads((ROOT/'.devpilot/docs_governance/source_registry.json').read_text(encoding='utf-8'))
    s=json.loads((ROOT/'.devpilot/project_state.json').read_text(encoding='utf-8'))
    pairs=[(x['doc_id'],x['path']) for x in r['documents']]
    assert len(pairs)==len(set(pairs))
    assert len(pairs)>=1686
    assert r['last_registered_sprint']==s['last_registered_sprint']
    assert r['mp_1a_last_registered_sprint_at_sync1']=='MP-1A-04'
    assert r['reb117_sync1_state']=='CANDIDATE_PENDING_WINDOWS_VALIDATION_AND_G5'
    assert all(any(d['path']==path for d in r['documents']) and (ROOT/path).is_file() for path in [
      'src/devpilot_core/generation/contracts.py',
      'src/devpilot_core/application/story_general_provider.py',
      'docs/program_rebaseline_117/SYNC1_HANDOFF_128.md'])

def test_sync1_handoff_requires_program_successor_and_preserves_stop():
    h=(ROOT/'docs/program_rebaseline_117/SYNC1_HANDOFF_128.md').read_text(encoding='utf-8')
    assert 'MP-1B' in h and 'BLOCKED' in h
    assert 'Pilot A no consiguió MVP E2E' in h
    assert 'G5 PASS' in h
