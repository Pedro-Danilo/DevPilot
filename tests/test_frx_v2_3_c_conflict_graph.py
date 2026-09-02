from __future__ import annotations
import copy, json
from pathlib import Path
import pytest
from devpilot_core.schemas import SchemaValidator
from devpilot_core.testing.conflict_graph import ParallelShadowPlanner
from devpilot_core.testing.isolation_registry import TestIsolationRegistry, IsolationState
ROOT=Path(__file__).resolve().parents[1]

def e(node, state='UNCLASSIFIED', seconds=10.0, locks=None, domains=None):
    base=TestIsolationRegistry.default_entry(node,runtime_estimate={'known':True,'seconds':seconds,'confidence':'high','source_environment':'fixture','last_seen':'x'})
    if state=='PROVEN_PARALLEL_SAFE':
        return TestIsolationRegistry.review_entry(base,decision=state,reviewer='owner',reason='fixture',reviewed_at='x',evidence_ids=['focal'],resource_lock_keys=locks or [],isolation_domains=domains or [])
    if state=='SERIAL_REQUIRED':
        return TestIsolationRegistry.review_entry(base,decision=state,reviewer='owner',reason='fixture',reviewed_at='x',evidence_ids=[],resource_lock_keys=locks or [],isolation_domains=domains or [])
    return base

def payload(entries):
    base=json.loads((ROOT/'.devpilot/testing/test_isolation_registry.json').read_text(encoding='utf-8'))
    base['entries']=entries; base['collection_sha256']='f'*64; base['registry_sha256']='e'*64
    return base

def test_shared_lock_creates_conflict_edge():
    g=ParallelShadowPlanner.build_conflict_graph([e('a::t','PROVEN_PARALLEL_SAFE',locks=['db:x']),e('b::t','PROVEN_PARALLEL_SAFE',locks=['db:x'])])
    assert g.edges==(('a::t','b::t'),)

def test_distinct_resources_do_not_conflict():
    g=ParallelShadowPlanner.build_conflict_graph([e('a::t','PROVEN_PARALLEL_SAFE',locks=['db:a']),e('b::t','PROVEN_PARALLEL_SAFE',locks=['db:b'])])
    assert g.edges==()

def test_unknown_and_serial_required_never_enter_parallel_graph():
    g=ParallelShadowPlanner.build_conflict_graph([e('a::t'),e('b::t','SERIAL_REQUIRED'),e('c::t','PROVEN_PARALLEL_SAFE')])
    assert g.nodes==('c::t',)

def test_conflicting_safe_nodes_never_share_wave():
    p=ParallelShadowPlanner(ROOT).plan(payload([e('a::t','PROVEN_PARALLEL_SAFE',10,locks=['x']),e('b::t','PROVEN_PARALLEL_SAFE',9,locks=['x']),e('c::t','PROVEN_PARALLEL_SAFE',8,locks=['y'])]))
    for w in p['shadow_waves']:
        assert not {'a::t','b::t'} <= set(w['nodeids'])

def test_planning_is_deterministic():
    x=payload([e('a::t','PROVEN_PARALLEL_SAFE',10),e('b::t','PROVEN_PARALLEL_SAFE',8),e('c::t',seconds=7)])
    a=ParallelShadowPlanner(ROOT).plan(copy.deepcopy(x)); b=ParallelShadowPlanner(ROOT).plan(copy.deepcopy(x))
    assert a['plan_identity']==b['plan_identity'] and a['shadow_waves']==b['shadow_waves']

def test_predicted_makespan_sanity_for_two_slots():
    p=ParallelShadowPlanner(ROOT).plan(payload([e('a::t','PROVEN_PARALLEL_SAFE',10),e('b::t','PROVEN_PARALLEL_SAFE',8),e('c::t','SERIAL_REQUIRED',5)]))
    assert p['predicted_parallel_known_runtime_seconds']==15.0
    assert p['workers_executed']==0

def test_execution_is_hard_disabled():
    with pytest.raises(RuntimeError): ParallelShadowPlanner(ROOT).execute()

def test_current_repo_shadow_plan_is_safe_no_go_and_unknown_serial():
    p=json.loads((ROOT/'.devpilot/testing/frx_v2_3_c_shadow_plan.json').read_text(encoding='utf-8'))
    assert p['status']=='PASS' and p['collection_total']>=2872
    assert p['registry_entries_total']==2872
    assert p['implicit_unclassified_total']>=1
    assert p['safe_candidates_total']==0 and p['serial_lane_total']==p['collection_total']
    assert p['unknown_serial_total']==p['collection_total']
    assert p['shadow_waves_total']==0 and p['workers_executed']==0 and p['full_runs']==0
    assert p['amdahl_feasibility']['decision']=='NO-GO' and p['frx_v2_3_d_authorized'] is False

def test_repo_shadow_schema_passes():
    result=SchemaValidator(ROOT).validate(schema='docs/schemas/parallel_shadow_plan.schema.json',instance='.devpilot/testing/frx_v2_3_c_shadow_plan.json')
    assert result.ok, result.to_dict()

def test_plan_identity_has_all_four_authorities():
    p=json.loads((ROOT/'.devpilot/testing/frx_v2_3_c_shadow_plan.json').read_text(encoding='utf-8'))
    assert set(p['identity']) >= {'collection_sha256','isolation_sha256','normalized_duration_registry_sha256','serial_baseline_sha256'}

def test_historical_baseline_is_reporting_only():
    p=json.loads((ROOT/'.devpilot/testing/frx_v2_3_c_shadow_plan.json').read_text(encoding='utf-8'))
    assert p['normalized_serial_comparison_authoritative'] is True
    assert p['historical_observed_comparison_reporting_only'] is True
