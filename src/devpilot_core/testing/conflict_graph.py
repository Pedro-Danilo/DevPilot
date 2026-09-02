from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .isolation_registry import IsolationState, TestIsolationRegistry
from .temporal_shard_planner import TemporalShardPlanner

DEFAULT_ISOLATION_REGISTRY = Path('.devpilot/testing/test_isolation_registry.json')
DEFAULT_DURATION_REGISTRY = Path('.devpilot/testing/node_duration_registry.json')
DEFAULT_SERIAL_BASELINE = Path('docs/audits/FRX_V2_3_A_NORMALIZED_SERIAL_BASELINE.json')


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8'))


def _file_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


@dataclass(frozen=True)
class ConflictGraph:
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]

    def conflicts(self, a: str, b: str) -> bool:
        key = tuple(sorted((a, b)))
        return key in set(self.edges)

    def to_dict(self) -> dict[str, Any]:
        return {'nodes': list(self.nodes), 'edges': [list(x) for x in self.edges], 'edges_total': len(self.edges)}


class ParallelShadowPlanner:
    """Deterministic read-only planner. It never starts a test worker."""

    version = '1.0.0'

    def __init__(self, root: Path):
        self.root = Path(root)

    @staticmethod
    def _resources(entry: dict[str, Any]) -> set[str]:
        return set(entry.get('isolation_domains') or []) | set(entry.get('resource_lock_keys') or [])

    @classmethod
    def build_conflict_graph(cls, entries: Iterable[dict[str, Any]]) -> ConflictGraph:
        safe = [e for e in entries if e.get('state') == IsolationState.PROVEN_PARALLEL_SAFE.value and e.get('parallel_safe') is True]
        safe = sorted(safe, key=lambda e: str(e.get('nodeid')))
        edges: list[tuple[str, str]] = []
        for i, left in enumerate(safe):
            lr = cls._resources(left)
            for right in safe[i + 1:]:
                if lr & cls._resources(right):
                    edges.append((str(left['nodeid']), str(right['nodeid'])))
        return ConflictGraph(tuple(str(e['nodeid']) for e in safe), tuple(edges))

    @staticmethod
    def _seconds(entry: dict[str, Any]) -> float:
        rec = entry.get('runtime_estimate') or {}
        return max(0.0, float(rec.get('seconds') or 0.0)) if rec.get('known') else 0.0

    @classmethod
    def _waves(cls, safe_entries: list[dict[str, Any]], graph: ConflictGraph, slots: int) -> list[dict[str, Any]]:
        ordered = sorted(safe_entries, key=lambda e: (-cls._seconds(e), str(e['nodeid'])))
        waves: list[dict[str, Any]] = []
        for entry in ordered:
            nodeid = str(entry['nodeid'])
            placed = False
            for wave in waves:
                if len(wave['nodeids']) >= slots:
                    continue
                if any(graph.conflicts(nodeid, other) for other in wave['nodeids']):
                    continue
                wave['nodeids'].append(nodeid)
                wave['node_runtime_seconds'].append(cls._seconds(entry))
                wave['predicted_seconds'] = max(wave['node_runtime_seconds']) if wave['node_runtime_seconds'] else 0.0
                placed = True
                break
            if not placed:
                waves.append({'nodeids': [nodeid], 'node_runtime_seconds': [cls._seconds(entry)], 'predicted_seconds': cls._seconds(entry)})
        for i, wave in enumerate(waves, 1):
            wave['wave_id'] = f'shadow-wave-{i:04d}'
        return waves

    def plan(self, isolation_payload: dict[str, Any], *, collection_nodeids: Iterable[str] | None = None, worker_slots_preview: int = 2, target_parallel_reduction_percent: float = 30.0, explicit_overhead_seconds: float = 0.0) -> dict[str, Any]:
        if worker_slots_preview != 2:
            raise ValueError('FRX-v2.3-C preview is fixed at 2 slots')
        registry_entries = list(isolation_payload.get('entries') or [])
        if not registry_entries or len(registry_entries) != len({str(e.get('nodeid')) for e in registry_entries}):
            raise ValueError('isolation registry must contain a unique non-empty collection')
        registry_by_nodeid = {str(e['nodeid']): e for e in registry_entries}
        if collection_nodeids is None:
            entries = registry_entries
            collection_sha = str(isolation_payload.get('collection_sha256') or '')
            implicit_unclassified_total = 0
        else:
            ordered = [str(x) for x in collection_nodeids]
            if not ordered or len(ordered) != len(set(ordered)):
                raise ValueError('current collection must be non-empty and unique')
            entries = []
            implicit_unclassified_total = 0
            for nodeid in ordered:
                if nodeid in registry_by_nodeid:
                    entries.append(registry_by_nodeid[nodeid])
                else:
                    item = TestIsolationRegistry.default_entry(nodeid)
                    item['implicit_unclassified'] = True
                    entries.append(item)
                    implicit_unclassified_total += 1
            collection_sha = TemporalShardPlanner.collection_sha256(ordered)
        graph = self.build_conflict_graph(entries)
        safe_entries = [e for e in entries if e.get('state') == IsolationState.PROVEN_PARALLEL_SAFE.value and e.get('parallel_safe') is True]
        serial_entries = [e for e in entries if e not in safe_entries]
        if any(e.get('state') != IsolationState.PROVEN_PARALLEL_SAFE.value or e.get('parallel_safe') is not True for e in safe_entries):
            raise ValueError('unsafe entry leaked into parallel candidates')
        waves = self._waves(safe_entries, graph, worker_slots_preview)
        for wave in waves:
            nodes = wave['nodeids']
            for i, left in enumerate(nodes):
                for right in nodes[i+1:]:
                    if graph.conflicts(left, right):
                        raise ValueError('conflict violation inside shadow wave')
        known_total = sum(self._seconds(e) for e in entries)
        safe_runtime = sum(self._seconds(e) for e in safe_entries)
        serial_runtime = sum(self._seconds(e) for e in serial_entries)
        wave_runtime = sum(float(w['predicted_seconds']) for w in waves)
        predicted = serial_runtime + wave_runtime + max(0.0, float(explicit_overhead_seconds))
        safe_fraction = 0.0 if known_total <= 0 else safe_runtime / known_total
        serial_fraction = 1.0 - safe_fraction if known_total > 0 else 1.0
        speedup = 0.0 if known_total <= 0 else max(0.0, (known_total - predicted) / known_total * 100.0)
        required_safe_fraction_ideal = min(1.0, max(0.0, target_parallel_reduction_percent / 50.0))
        feasible = safe_fraction >= required_safe_fraction_ideal and speedup >= target_parallel_reduction_percent

        isolation_sha = str(isolation_payload.get('registry_sha256') or _sha256_json(isolation_payload))
        duration_path = self.root / DEFAULT_DURATION_REGISTRY
        baseline_path = self.root / DEFAULT_SERIAL_BASELINE
        duration_sha = _file_sha256(duration_path)
        baseline_sha = _file_sha256(baseline_path)
        identity_payload = {
            'collection_sha256': collection_sha,
            'isolation_sha256': isolation_sha,
            'normalized_duration_registry_sha256': duration_sha,
            'serial_baseline_sha256': baseline_sha,
            'worker_slots_preview': worker_slots_preview,
            'planner_version': self.version,
        }
        plan_identity = _sha256_json(identity_payload)
        historical = json.loads(baseline_path.read_text(encoding='utf-8')).get('historical_operational_baseline_seconds')
        historical_improvement = None
        if historical and known_total > 0:
            historical_improvement = round((float(historical) - predicted) / float(historical) * 100.0, 3)

        return {
            'schema_id': 'devpilot.testing.parallel_shadow_plan.v1',
            'status': 'PASS',
            'planner_version': self.version,
            'plan_identity': plan_identity,
            'identity': identity_payload,
            'collection_total': len(entries),
            'registry_entries_total': len(registry_entries),
            'implicit_unclassified_total': implicit_unclassified_total,
            'safe_candidates_total': len(safe_entries),
            'serial_lane_total': len(serial_entries),
            'unknown_serial_total': sum(1 for e in serial_entries if e.get('state') == IsolationState.UNCLASSIFIED.value),
            'serial_required_total': sum(1 for e in serial_entries if e.get('state') == IsolationState.SERIAL_REQUIRED.value),
            'conflict_graph': graph.to_dict(),
            'shadow_waves': waves,
            'shadow_waves_total': len(waves),
            'worker_slots_preview': worker_slots_preview,
            'workers_executed': 0,
            'full_runs': 0,
            'runtime_known_seconds_total': round(known_total, 6),
            'safe_runtime_seconds': round(safe_runtime, 6),
            'serial_runtime_seconds': round(serial_runtime, 6),
            'runtime_weighted_safe_coverage_percent': round(safe_fraction * 100.0, 6),
            'serial_fraction_percent': round(serial_fraction * 100.0, 6),
            'lock_contention_edges_total': len(graph.edges),
            'predicted_parallel_known_runtime_seconds': round(predicted, 6),
            'projected_incremental_parallel_reduction_percent': round(speedup, 6),
            'historical_observed_total_improvement_projection_percent': historical_improvement,
            'normalized_serial_comparison_authoritative': True,
            'historical_observed_comparison_reporting_only': True,
            'amdahl_feasibility': {
                'target_parallel_reduction_percent': target_parallel_reduction_percent,
                'required_runtime_parallelizable_fraction_ideal': round(required_safe_fraction_ideal, 6),
                'actual_runtime_parallel_safe_fraction': round(safe_fraction, 6),
                'explicit_overhead_seconds': round(max(0.0, float(explicit_overhead_seconds)), 6),
                'feasible_for_canary': feasible,
                'decision': 'GO' if feasible else 'NO-GO',
                'reason': 'sufficient proven-safe runtime coverage' if feasible else 'proven-safe runtime coverage is insufficient for the target reduction',
            },
            'frx_v2_3_d_authorized': bool(feasible),
            'execution_disabled': True,
        }

    def execute(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError('FRX-v2.3-C is shadow-only; worker execution is disabled')
