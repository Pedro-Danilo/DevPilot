"""R01-02 focal positive/negative tests, no network or app/source writes."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest

from devpilot_core.generation import (
    CandidateLifecycleConflict, CandidateLifecycleStore, CandidateOrigin,
    CandidateOriginKind, CandidateStatus, GenerationProvenance,
    GenerationRequest, LineageReason, ProviderClass,
    create_candidate, create_successor_candidate,
)


def inputs(id='req-1', context='a'*64):
    return GenerationRequest(
        request_id=id, artifact_type='story-proposal', profile_version='story-v1',
        dependency_profile_version='deps-v1', upstream_hashes={'story':context},
        owner_inputs={'requirement':'deterministic'}, policy_snapshot={'external_egress':'DENY'},
        budget_snapshot={'max_usd':0}, context_reference='context-v1',
    )


def candidate(req=None, prompt='prompt:v1', provider='local-deterministic'):
    req=req or inputs()
    origin=CandidateOrigin(kind=CandidateOriginKind.PROVIDER,
        provider_class=ProviderClass.DETERMINISTIC,provider_id=provider,
        model_id='template-v1')
    return create_candidate(request=req,payload={'proposal':'hello'},origin=origin,
        provenance=GenerationProvenance(prompt_ref=prompt,profile_ref=req.profile_version,
                                         context_ref=req.context_reference))


@pytest.fixture
def store(tmp_path):
    return CandidateLifecycleStore(tmp_path/'runtime'/'candidates.sqlite')


def test_terminal_restart_and_retries_return_one_candidate(store):
    req=inputs();c=candidate(req)
    assert store.put(request=req,candidate=c,idempotency_key='key-a')==c
    store.transition(candidate_id=c.candidate_id,expected_status=CandidateStatus.GENERATED,target_status=CandidateStatus.VALIDATED)
    store.transition(candidate_id=c.candidate_id,expected_status=CandidateStatus.VALIDATED,target_status=CandidateStatus.UNDER_REVIEW)
    selected=store.transition(candidate_id=c.candidate_id,expected_status=CandidateStatus.UNDER_REVIEW,target_status=CandidateStatus.SELECTED)
    reopened=CandidateLifecycleStore(store.path)
    assert reopened.put(request=req,candidate=c,idempotency_key='key-a')==selected
    assert reopened.put(request=req,candidate=c,idempotency_key='key-b')==selected
    assert reopened.transition(candidate_id=c.candidate_id,expected_status=CandidateStatus.UNDER_REVIEW,target_status=CandidateStatus.SELECTED)==selected
    assert reopened.receipt(c.candidate_id)['status']=='SELECTED'


def test_key_reused_for_new_input_blocked(store):
    store.put(request=inputs(),candidate=candidate(),idempotency_key='same')
    req=inputs(context='b'*64)
    with pytest.raises(CandidateLifecycleConflict,match='IDEMPOTENCY_CONTEXT_CONFLICT'):
        store.put(request=req,candidate=candidate(req),idempotency_key='same')


def test_provider_prompt_and_profile_cannot_collide(store):
    req=inputs();c=candidate(req)
    store.put(request=req,candidate=c,idempotency_key='same')
    for other in (candidate(req,prompt='prompt:v2'),candidate(req,provider='other')):
        with pytest.raises(CandidateLifecycleConflict,match='CONFLICT|COLLISION'):
            store.put(request=req,candidate=other,idempotency_key='same')


def test_changed_prompt_cannot_overwrite_identity_with_fresh_key(store):
    req=inputs();store.put(request=req,candidate=candidate(req),idempotency_key='one')
    with pytest.raises(CandidateLifecycleConflict,match='IMMUTABLE_CANDIDATE_COLLISION'):
        store.put(request=req,candidate=candidate(req,prompt='prompt:v2'),idempotency_key='two')


def test_lineage_persists_and_checks_parent(store):
    req=inputs();p=candidate(req)
    child=create_successor_candidate(parent=p,payload={'proposal':'edited'},origin=p.origin,
        reason=LineageReason.REGENERATION,actor_id='owner')
    with pytest.raises(CandidateLifecycleConflict,match='MISSING_LINEAGE_PARENT'):
        store.put(request=req,candidate=child,idempotency_key='child')
    store.put(request=req,candidate=p,idempotency_key='parent')
    saved=store.put(request=req,candidate=child,idempotency_key='child')
    assert saved.lineage.parent_candidate_id==p.candidate_id
    assert CandidateLifecycleStore(store.path).get(child.candidate_id)==saved


def test_expected_status_conflict_and_illegal_transition(store):
    req=inputs();c=candidate(req);store.put(request=req,candidate=c,idempotency_key='one')
    with pytest.raises(ValueError,match='illegal candidate lifecycle transition'):
        store.transition(candidate_id=c.candidate_id,expected_status=CandidateStatus.GENERATED,target_status=CandidateStatus.SELECTED)
    store.transition(candidate_id=c.candidate_id,expected_status=CandidateStatus.GENERATED,target_status=CandidateStatus.VALIDATED)
    with pytest.raises(CandidateLifecycleConflict,match='CONCURRENT_STATUS_CONFLICT'):
        store.transition(candidate_id=c.candidate_id,expected_status=CandidateStatus.GENERATED,target_status=CandidateStatus.UNDER_REVIEW)


def test_concurrent_idempotency_one_record(store):
    req=inputs();c=candidate(req)
    def job(i):return CandidateLifecycleStore(store.path).put(request=req,candidate=c,idempotency_key=f'key-{i}')
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(job,range(20)))
    assert all(x.candidate_id==c.candidate_id for x in results)
    with store._open() as db:
        assert db.execute('select count(*) from candidates').fetchone()[0]==1
        assert db.execute('select count(*) from replay_keys').fetchone()[0]==20


def test_bad_candidate_hash_blocks_without_writes(store):
    req=inputs();c=candidate(req)
    with pytest.raises(CandidateLifecycleConflict,match='CONTENT_HASH_DRIFT'):
        store.put(request=req,candidate=replace(c,payload={'evil':True}),idempotency_key='x')
    assert store.get(c.candidate_id) is None


def test_proof_has_reproducible_version_context_provider_prompt(store):
    req=inputs();c=candidate(req)
    store.put(request=req,candidate=c,idempotency_key='x')
    proof=store.receipt(c.candidate_id)
    assert proof['context_sha256'] and len(proof['context_sha256'])==64
    assert proof['input_sha256']==req.canonical_input_sha256
    assert proof['output_sha256']==c.content_sha256
    assert proof['provider_sha256'] and proof['prompt_sha256']
    assert proof['version']==1 and proof['profile_version']=='story-v1'
    assert proof['status']=='GENERATED'


def test_no_provider_or_source_authority_methods(store):
    assert set(x for x in dir(store) if x in ('apply','execute','approve','publish','git_commit','generate'))==set()
