from __future__ import annotations

import json, math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .temporal_shard_planner import TemporalShardPlanner

@dataclass(frozen=True)
class NormalizedSerialBaselineBuilder:
    root: Path

    def build(self, *, collection_path: Path, environment_fingerprint: str, historical_observed_seconds: float = 36992.0, binding_baseline_seconds: float = 2931.421) -> dict[str, Any]:
        payload=json.loads(Path(collection_path).read_text(encoding='utf-8'))
        nodeids=[str(x['nodeid']) for x in payload['nodes']]
        planner=TemporalShardPlanner(self.root,target_shard_seconds=900.0,max_nodeids=200,max_command_chars=30000,nodeid_transport='manifest')
        temporal=planner.plan(nodeids,environment_fingerprint=environment_fingerprint)
        count50=math.ceil(len(nodeids)/50)
        reduction=round((count50-temporal['shards_total'])/count50*100,3)
        return {
          'schema_id':'devpilot.testing.normalized_serial_baseline.v1',
          'status':'PASS' if reduction>=60 else 'BLOCK',
          'workers':0,'full_runs':0,'collection_total':len(nodeids),
          'historical_operational_baseline_seconds':historical_observed_seconds,
          'historical_count50_processes':count50,
          'normalized_shadow_processes':temporal['shards_total'],
          'process_reduction_percent':reduction,
          'nodeid_transport':'manifest',
          'binding_cost_baseline_seconds':binding_baseline_seconds,
          'binding_cost_windows_pass_threshold_seconds':round(binding_baseline_seconds*0.20,3),
          'parallel_speedup_attributed':False,
          'notes':['Historical v2.2 wall-clock remains separate from normalized serial baseline.','A performs no full and no parallel worker execution.']
        }
