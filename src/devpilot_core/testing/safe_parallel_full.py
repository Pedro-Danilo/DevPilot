from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .conflict_graph import ParallelShadowPlanner
from .isolation_registry import TestIsolationRegistry
from .temporal_shard_planner import TemporalShardPlanner

POLICY_PATH = Path('.devpilot/testing/frx_v2_3_e_policy.json')
BASELINE_PATH = Path('docs/audits/FRX_V2_3_A_NORMALIZED_SERIAL_BASELINE.json')
BR_SHADOW_PATH = Path('docs/audits/FRX_V2_3_BR_SUCCESSOR_SHADOW_PLAN.json')
D_REPORT_PATH = Path('docs/audits/FRX_V2_3_D_PARALLEL_CANARY_REPORT.json')


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))

def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()

def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True)
class SafeParallelFullPlanner:
    root: Path
    policy_path: Path = POLICY_PATH

    def build(self, nodeids: Iterable[str], *, environment_fingerprint: str) -> dict[str, Any]:
        root=Path(self.root).resolve(); ordered=[str(x) for x in nodeids]
        if not ordered or len(ordered)!=len(set(ordered)) or any('::' not in x for x in ordered):
            raise ValueError('collection must be non-empty, unique pytest nodeids')
        policy_rel=Path(self.policy_path); policy_file=policy_rel if policy_rel.is_absolute() else root/policy_rel
        policy=_load(policy_file); baseline=_load(root/BASELINE_PATH); br=_load(root/BR_SHADOW_PATH); d=_load(root/D_REPORT_PATH)
        if policy.get('full_regression_runs_consumed')!=0 or policy.get('full_regression_runs_allowed')!=1 or policy.get('second_full_allowed') is not False:
            raise ValueError('v2.3-E one-full budget is not pristine')
        if d.get('status')!='PASS' or d.get('decision')!='GO-E' or d.get('frx_v2_3_e_authorized') is not True or d.get('full_regression_runs')!=0:
            raise ValueError('FRX-v2.3-D Windows canary does not authorize E')
        if (br.get('amdahl_feasibility') or {}).get('decision')!='GO':
            raise ValueError('sealed BR feasibility no longer justifies one-full E')
        registry=TestIsolationRegistry(root).load()
        shadow=ParallelShadowPlanner(root).plan(registry,collection_nodeids=ordered,worker_slots_preview=2,target_parallel_reduction_percent=float(policy['default_enablement_threshold_percent']))
        safe=set(n for w in shadow.get('shadow_waves',[]) for n in w.get('nodeids',[]))
        serial=[n for n in ordered if n not in safe]
        temporal=TemporalShardPlanner(root,target_shard_seconds=float(policy['serial_lane']['target_shard_seconds']),max_nodeids=int(policy['serial_lane']['max_nodeids']),max_command_chars=30000,nodeid_transport='manifest').plan(serial,environment_fingerprint=environment_fingerprint) if serial else {'shards':[],'shards_total':0,'plan_sha256':_canonical_sha([])}
        flattened_safe=[n for w in shadow.get('shadow_waves',[]) for n in w.get('nodeids',[])]
        flattened_serial=[n for s in temporal.get('shards',[]) for n in s.get('nodeids',[])]
        all_nodes=flattened_safe+flattened_serial
        if len(all_nodes)!=len(ordered) or set(all_nodes)!=set(ordered) or len(all_nodes)!=len(set(all_nodes)):
            raise ValueError('hybrid plan does not cover collection exactly once')
        plan_core={
          'schema_id':'devpilot.testing.safe_parallel_full_plan.v1','version':'1.0.0','status':'PASS','execution_enabled':False,
          'full_regression_runs_planned':1,'max_workers':2,'second_full_allowed':False,'completion_first':True,
          'collection_total':len(ordered),'collection_sha256':TemporalShardPlanner.collection_sha256(ordered),
          'safe_total':len(flattened_safe),'serial_total':len(flattened_serial),'safe_waves':shadow.get('shadow_waves',[]),'safe_waves_total':len(shadow.get('shadow_waves',[])),
          'serial_shards':temporal.get('shards',[]),'serial_shards_total':int(temporal.get('shards_total',0)),'serial_nodeid_transport':'manifest',
          'conflict_graph':shadow.get('conflict_graph',{}),'runtime_weighted_safe_coverage_percent':shadow.get('runtime_weighted_safe_coverage_percent',0.0),
          'projected_incremental_parallel_reduction_percent':shadow.get('projected_incremental_parallel_reduction_percent',0.0),
          'sealed_inputs':{
            'policy_semantic_sha256':_sha(policy_file),'normalized_serial_baseline_semantic_sha256':_sha(root/BASELINE_PATH),
            'isolation_registry_semantic_sha256':_sha(root/'.devpilot/testing/test_isolation_registry.json'),'duration_registry_semantic_sha256':_sha(root/'.devpilot/testing/node_duration_registry.json'),
            'br_shadow_semantic_sha256':_sha(root/BR_SHADOW_PATH),'d_canary_report_semantic_sha256':_sha(root/D_REPORT_PATH),
          },
          'normalized_serial_reference_seconds':float(br.get('runtime_known_seconds_total') or 0.0),
          'historical_v2_2_observed_seconds':float(baseline.get('historical_operational_baseline_seconds') or 0.0),
          'default_enablement_threshold_percent':float(policy['default_enablement_threshold_percent']),
          'strong_fingerprint_fallbacks_expected':0,
        }
        return {**plan_core,'plan_sha256':_canonical_sha(plan_core)}

@dataclass(frozen=True)
class FullPerformanceAdjudicator:
    threshold_percent: float = 30.0
    def adjudicate(self, *, plan: dict[str,Any], actual_wall_seconds: float, accounting_total: int, collection_total: int, conflicts: int, source_drift: bool, new_flakes: int, max_workers_observed: int, full_runs: int, second_full: bool, strong_fingerprint_fallbacks: int) -> dict[str,Any]:
        hist=float(plan['historical_v2_2_observed_seconds']); norm=float(plan['normalized_serial_reference_seconds']); actual=float(actual_wall_seconds)
        pct=lambda a,b: round((a-b)/a*100.0,6) if a>0 else None
        safety=(accounting_total==collection_total and conflicts==0 and not source_drift and new_flakes==0 and max_workers_observed<=2 and full_runs==1 and not second_full and strong_fingerprint_fallbacks==0)
        inc=pct(norm,actual)
        decision='BLOCK' if not safety else ('PASS/DEFAULT-ENABLED' if inc is not None and inc>=self.threshold_percent else 'PASS/AVAILABLE-NOT-DEFAULT')
        return {
          'schema_id':'devpilot.testing.safe_parallel_full_performance_report.v1','status':'PASS' if safety else 'BLOCK','decision':decision,'safety_pass':safety,
          'total_improvement_vs_v2_2_observed_percent':pct(hist,actual),'serial_normalization_improvement_percent':pct(hist,norm),
          'incremental_parallel_improvement_vs_normalized_serial_percent':inc,'historical_v2_2_observed_seconds':hist,'normalized_serial_reference_seconds':norm,'actual_safe_parallel_full_wall_seconds':actual,
          'normalized_serial_reference_kind':'sealed-known-runtime-estimate-from-FRX-v2.3-BR; not a second comparison full','threshold_percent':self.threshold_percent,
          'accounting_total':accounting_total,'collection_total':collection_total,'conflicts':conflicts,'source_drift':source_drift,'new_flakes':new_flakes,'max_workers_observed':max_workers_observed,
          'full_regression_runs':full_runs,'second_full':second_full,'strong_fingerprint_fallbacks':strong_fingerprint_fallbacks,
        }

def _collection_nodes(payload: Any) -> list[str]:
    rows = payload.get('nodes') if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError('collection payload must be a nodeid list or an object with nodes[]')
    return [str(x['nodeid']) if isinstance(x, dict) else str(x) for x in rows]

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--collection',required=True); ap.add_argument('--environment-fingerprint',required=True); ap.add_argument('--out')
    a=ap.parse_args(); payload=_load(Path(a.collection)); nodes=_collection_nodes(payload)
    plan=SafeParallelFullPlanner(Path(a.root)).build(nodes,environment_fingerprint=a.environment_fingerprint)
    text=json.dumps(plan,indent=2,ensure_ascii=False)+'\n'; print(text,end='')
    if a.out: Path(a.out).write_text(text,encoding='utf-8',newline='\n')
    return 0

if __name__=='__main__': raise SystemExit(main())
