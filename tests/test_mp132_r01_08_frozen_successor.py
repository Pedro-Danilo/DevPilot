import copy
import pytest
from devpilot_core.application.artifact_lifecycle_service import ArtifactLifecycleService
from devpilot_core.application.frozen_successor import FrozenSuccessorPlanner, DependencyNode, DependencyEdge

SOURCE = '# Requirement\nOld behavior\n'

def case(kind='SEMANTIC', review=None):
    record={'artifact_id':'REQ-001','relative_path':'docs/req.md','state':'FROZEN',
            'content_hash': ArtifactLifecycleService.hash_normalized(SOURCE), 'provenance':{'artifact_version':3}}
    nodes=[DependencyNode('REQ-001','requirement','docs/req.md'),
           DependencyNode('ADR-001','adr','docs/adr.md'),
           DependencyNode('STORY-001','story','docs/story.md'),
           DependencyNode('TEST-001','test','tests/test_story.py'),
           DependencyNode('ADR-OTHER','adr','docs/unrelated.md')]
    edges=[DependencyEdge('REQ-001','ADR-001',('behavior',)),
           DependencyEdge('ADR-001','STORY-001',('behavior',)),
           DependencyEdge('STORY-001','TEST-001',('behavior',)),
           DependencyEdge('REQ-001','ADR-OTHER',('security',))]
    args=dict(original_record=record,original_content=SOURCE,
        successor_content='# Requirement\nNew behavior\n',successor_id='REQ-001-V4',
        successor_path='docs/req-v4.md',change_kind=kind,change_topics=('behavior',),
        reason='Requirement behavior must change',nodes=nodes,edges=edges,
        semantic_review_reference=review)
    return args

def test_selective_chain_and_no_mutations():
    args=case(); before=copy.deepcopy(args['original_record'])
    plan=FrozenSuccessorPlanner().plan(**args)
    assert [x['node_id'] for x in plan['impacts'] if x['decision']=='STALE_REVALIDATION_REQUIRED']==['ADR-001','STORY-001','TEST-001']
    assert [x['node_id'] for x in plan['impacts'] if x['decision']=='NO_IMPACT_WITH_REASON']==['ADR-OTHER']
    assert args['original_record']==before and plan['source_mutations_performed'] is False
    assert plan['successor']['artifact_version']==4 and plan['successor']['approval_required'] is True
    assert plan['successor']['publication_authorized'] is False

def test_no_cosmetic_fanout_with_evidence():
    p=FrozenSuccessorPlanner().plan(**case('COSMETIC','SEM-REVIEW-1234'))
    assert all(x['decision']=='NO_IMPACT_WITH_REASON' for x in p['impacts'])

def test_cosmetic_without_evidence_rejected():
    with pytest.raises(ValueError,match='EVIDENCE_REQUIRED'):FrozenSuccessorPlanner().plan(**case('COSMETIC'))

def test_replay_deterministic():
    args=case();s=FrozenSuccessorPlanner()
    assert s.plan(**args)==s.plan(**args)

def test_crlf_equivalent_preimage():
    args=case();args['original_content']=SOURCE.replace('\n','\r\n')
    assert FrozenSuccessorPlanner().plan(**args)['source']['state']=='FROZEN'

def test_preimage_drift():
    args=case();args['original_content']='Changed source'
    with pytest.raises(ValueError,match='FROZEN_SOURCE_DRIFT'):FrozenSuccessorPlanner().plan(**args)

def test_never_successor_same_path():
    args=case();args['successor_path']='docs/req.md'
    with pytest.raises(ValueError,match='NEW_ID_AND_PATH'):FrozenSuccessorPlanner().plan(**args)

def test_non_frozen_rejected():
    args=case();args['original_record']['state']='DRAFT'
    with pytest.raises(ValueError,match='SOURCE_NOT_FROZEN'):FrozenSuccessorPlanner().plan(**args)

def test_cycle_rejected():
    args=case();args['edges'].append(DependencyEdge('TEST-001','REQ-001',('behavior',)))
    with pytest.raises(ValueError,match='DEPENDENCY_CYCLE'):FrozenSuccessorPlanner().plan(**args)

def test_unknown_edge_rejected():
    args=case();args['edges'].append(DependencyEdge('REQ-001','UNKNOWN',('behavior',)))
    with pytest.raises(ValueError,match='UNKNOWN_DEPENDENCY_EDGE'):FrozenSuccessorPlanner().plan(**args)

def test_no_implicit_invalidations():
    args=case();args['change_topics']=('security',)
    p=FrozenSuccessorPlanner().plan(**args)
    assert [x['node_id'] for x in p['impacts'] if x['decision'].startswith('STALE')]==['ADR-OTHER']

def test_succ_path_unsafe():
    args=case();args['successor_path']='docs/../.git/config'
    with pytest.raises(ValueError,match='UNSAFE_RELATIVE_PATH'):FrozenSuccessorPlanner().plan(**args)

def test_topic_less_rejected():
    args=case();args['change_topics']=()
    with pytest.raises(ValueError,match='EMPTY_OR_INVALID_TOPICS'):FrozenSuccessorPlanner().plan(**args)

def test_collision_id_rejected():
    args=case();args['successor_id']='ADR-001'
    with pytest.raises(ValueError,match='SUCCESSOR_PATH_OR_ID_COLLISION'):FrozenSuccessorPlanner().plan(**args)

def test_absent_source_in_graph_rejected():
    args=case();args['nodes']=args['nodes'][1:]
    with pytest.raises(ValueError,match='SOURCE_NODE_MISSING'):FrozenSuccessorPlanner().plan(**args)
