from pathlib import Path
import json
from devpilot_core.testing.safe_parallel_full import SafeParallelFullPlanner, FullPerformanceAdjudicator, _collection_nodes
ROOT=Path(__file__).resolve().parents[1]
def collection():
 p=json.loads((ROOT/'.devpilot/testing/frx_v2_3_c_collection.json').read_text(encoding='utf-8')); return [x['nodeid'] for x in p['nodes']]
def test_e_plan_is_hybrid_exact_once_workers_two_and_no_execution():
 p=SafeParallelFullPlanner(ROOT).build(collection(),environment_fingerprint='windows-pytest-devpilot-gsdlc07e-v1')
 assert p['status']=='PASS' and p['execution_enabled'] is False and p['full_regression_runs_planned']==1 and p['max_workers']==2
 nodes=[n for w in p['safe_waves'] for n in w['nodeids']]+[n for s in p['serial_shards'] for n in s['nodeids']]
 assert len(nodes)==len(set(nodes))==p['collection_total']; assert p['serial_nodeid_transport']=='manifest'
def test_e_plan_never_parallelizes_unclassified_nodes():
 p=SafeParallelFullPlanner(ROOT).build(collection(),environment_fingerprint='windows-pytest-devpilot-gsdlc07e-v1')
 reg=json.loads((ROOT/'.devpilot/testing/test_isolation_registry.json').read_text()); by={x['nodeid']:x for x in reg['entries']}
 for n in [n for w in p['safe_waves'] for n in w['nodeids']]: assert by[n]['state']=='PROVEN_PARALLEL_SAFE' and by[n]['parallel_safe'] is True
def test_e_serial_lane_is_coarsened_manifest_based():
 p=SafeParallelFullPlanner(ROOT).build(collection(),environment_fingerprint='windows-pytest-devpilot-gsdlc07e-v1')
 assert p['serial_shards_total'] < max(1,(p['serial_total']+49)//50) and max(len(s['nodeids']) for s in p['serial_shards'])<=200
def test_e_performance_attribution_separates_three_metrics_and_available_not_default():
 p=SafeParallelFullPlanner(ROOT).build(collection(),environment_fingerprint='windows-pytest-devpilot-gsdlc07e-v1')
 r=FullPerformanceAdjudicator(30).adjudicate(plan=p,actual_wall_seconds=p['normalized_serial_reference_seconds']*0.8,accounting_total=p['collection_total'],collection_total=p['collection_total'],conflicts=0,source_drift=False,new_flakes=0,max_workers_observed=2,full_runs=1,second_full=False,strong_fingerprint_fallbacks=0)
 assert r['status']=='PASS' and r['decision']=='PASS/AVAILABLE-NOT-DEFAULT'; assert r['incremental_parallel_improvement_vs_normalized_serial_percent']==20.0
def test_e_safety_block_on_second_full_or_incomplete_accounting():
 p=SafeParallelFullPlanner(ROOT).build(collection(),environment_fingerprint='windows-pytest-devpilot-gsdlc07e-v1')
 r=FullPerformanceAdjudicator().adjudicate(plan=p,actual_wall_seconds=100,accounting_total=p['collection_total']-1,collection_total=p['collection_total'],conflicts=0,source_drift=False,new_flakes=0,max_workers_observed=2,full_runs=2,second_full=True,strong_fingerprint_fallbacks=0)
 assert r['status']=='BLOCK' and r['decision']=='BLOCK'

def test_e_collection_cli_accepts_raw_list_and_nodes_object():
 nodes=collection()[:3]
 assert _collection_nodes(nodes)==nodes
 assert _collection_nodes({'nodes':[{'nodeid':n} for n in nodes]})==nodes
