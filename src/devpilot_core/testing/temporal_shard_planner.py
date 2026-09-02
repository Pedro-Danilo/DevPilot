from __future__ import annotations

import hashlib
import json
import math
import statistics
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from .duration_registry import NodeDurationRegistry

TEMPORAL_PLANNER_VERSION = "1.1.0"
DEFAULT_TARGET_SHARD_SECONDS = 300.0
DEFAULT_MAX_NODEIDS = 50
DEFAULT_MAX_COMMAND_CHARS = 7000
DEFAULT_PARALLEL_WORKERS = 1


class TemporalPlannerError(ValueError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _p95(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(v) for v in values)
    return float(ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)])


def _cv(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    mean = statistics.mean(values)
    return 0.0 if mean == 0 else float(statistics.pstdev(values) / mean)


_BASE_COMMAND = subprocess.list2cmdline(["python", "-m", "pytest", "-q"])
_BASE_COMMAND_CHARS = len(_BASE_COMMAND)

def _node_arg_chars(nodeid: str) -> int:
    return len(subprocess.list2cmdline([nodeid]))

def _command_chars(nodeids: Sequence[str]) -> int:
    # list2cmdline quoting is per argument plus one separator, so this additive
    # form is exactly equivalent while avoiding repeated O(n) reconstruction.
    return _BASE_COMMAND_CHARS + sum(1 + _node_arg_chars(nodeid) for nodeid in nodeids)


@dataclass(frozen=True)
class NodeEstimate:
    nodeid: str
    known: bool
    estimate_seconds: float | None
    confidence: str
    classification: str


class TemporalShardPlanner:
    """Deterministic sequential LPT planner for FRX-v2.2-C shadow/canary use.

    It never executes tests and never changes the full-regression runtime planner.
    The only consumer allowed in v2.2-C is preview/shadow comparison and a bounded
    operator canary with workers=1.
    """

    def __init__(
        self,
        root: Path,
        *,
        registry_path: Path | None = None,
        target_shard_seconds: float = DEFAULT_TARGET_SHARD_SECONDS,
        max_nodeids: int = DEFAULT_MAX_NODEIDS,
        max_command_chars: int = DEFAULT_MAX_COMMAND_CHARS,
        nodeid_transport: str = "command-line",
    ) -> None:
        self.root = Path(root).resolve()
        self.registry = NodeDurationRegistry(self.root, registry_path=registry_path)
        self.target_shard_seconds = float(target_shard_seconds)
        self.max_nodeids = int(max_nodeids)
        self.max_command_chars = int(max_command_chars)
        self.nodeid_transport = str(nodeid_transport)
        self._validate_config()

    def _validate_config(self) -> None:
        if not math.isfinite(self.target_shard_seconds) or self.target_shard_seconds <= 0:
            raise TemporalPlannerError("target_shard_seconds must be positive")
        if self.max_nodeids <= 0 or self.max_nodeids > 500:
            raise TemporalPlannerError("max_nodeids must be between 1 and 500")
        if self.max_command_chars < 512 or self.max_command_chars > 30000:
            raise TemporalPlannerError("max_command_chars must be between 512 and 30000")
        if self.nodeid_transport not in {"command-line", "manifest"}:
            raise TemporalPlannerError("nodeid_transport must be command-line or manifest")

    @staticmethod
    def historical_collection_payload(nodeids: Sequence[str]) -> dict[str, Any]:
        nodes = [{"nodeid": str(nodeid), "ordinal": index} for index, nodeid in enumerate(nodeids, start=1)]
        return {
            "schema_id": "devpilot.testing.full_regression_collection.v2_1",
            "version": "2.1",
            "nodes": nodes,
            "nodeids_total": len(nodes),
        }

    @classmethod
    def collection_sha256(cls, nodeids: Sequence[str]) -> str:
        return _sha256(cls.historical_collection_payload(nodeids))

    @staticmethod
    def _estimate_from_registry(registry_data: dict[str, Any], nodeid: str, environment_fingerprint: str) -> NodeEstimate:
        rec = (((registry_data.get("environments") or {}).get(environment_fingerprint) or {}).get("nodes") or {}).get(nodeid)
        if not rec:
            return NodeEstimate(nodeid=nodeid, known=False, estimate_seconds=None, confidence="unknown", classification="unknown")
        return NodeEstimate(
            nodeid=nodeid,
            known=True,
            estimate_seconds=float(rec.get("robust_estimate") or 0.0),
            confidence=str(rec.get("confidence") or "unknown"),
            classification=str(rec.get("classification") or "unknown"),
        )

    def plan(
        self,
        nodeids: Sequence[str],
        *,
        environment_fingerprint: str,
        collection_sha256: str | None = None,
        expected_collection_sha256: str | None = None,
        expected_environment_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        ordered = [str(item) for item in nodeids]
        if not ordered:
            raise TemporalPlannerError("collection must contain at least one nodeid")
        if len(ordered) != len(set(ordered)):
            raise TemporalPlannerError("collection contains duplicate nodeids")
        if any(not item.strip() or "::" not in item for item in ordered):
            raise TemporalPlannerError("collection contains invalid pytest nodeid")
        computed_sha = self.collection_sha256(ordered)
        supplied_sha = collection_sha256 or computed_sha
        if supplied_sha != computed_sha:
            raise TemporalPlannerError("collection_sha256 does not match collection payload")
        if expected_collection_sha256 and expected_collection_sha256 != computed_sha:
            raise TemporalPlannerError("collection/fingerprint mismatch")
        if expected_environment_fingerprint and expected_environment_fingerprint != environment_fingerprint:
            raise TemporalPlannerError("environment fingerprint mismatch")

        registry_data = self.registry.load()
        estimates = [self._estimate_from_registry(registry_data, nodeid, environment_fingerprint) for nodeid in ordered]
        slow = sorted(
            [item for item in estimates if item.known and float(item.estimate_seconds or 0.0) > self.target_shard_seconds],
            key=lambda item: (-float(item.estimate_seconds or 0.0), item.nodeid),
        )
        known = sorted(
            [item for item in estimates if item.known and float(item.estimate_seconds or 0.0) <= self.target_shard_seconds],
            key=lambda item: (-float(item.estimate_seconds or 0.0), item.nodeid),
        )
        unknown = sorted([item for item in estimates if not item.known], key=lambda item: item.nodeid)

        shards: list[dict[str, Any]] = []
        for item in slow:
            shards.append(self._new_shard([item], slow_singleton=True))

        known_total = sum(float(item.estimate_seconds or 0.0) for item in known)
        target_bins = max(1, math.ceil(known_total / self.target_shard_seconds)) if known else 0
        bins: list[list[NodeEstimate]] = [[] for _ in range(target_bins)]
        loads: list[float] = [0.0 for _ in range(target_bins)]
        command_chars: list[int] = [_BASE_COMMAND_CHARS for _ in range(target_bins)]

        for item in known:
            delta_chars = 1 + _node_arg_chars(item.nodeid)
            candidates = [
                index
                for index, values in enumerate(bins)
                if len(values) < self.max_nodeids
                and (self.nodeid_transport == "manifest" or command_chars[index] + delta_chars <= self.max_command_chars)
            ]
            if not candidates:
                bins.append([])
                loads.append(0.0)
                command_chars.append(_BASE_COMMAND_CHARS)
                candidates = [len(bins) - 1]
            index = min(candidates, key=lambda idx: (loads[idx], len(bins[idx]), idx))
            bins[index].append(item)
            loads[index] += float(item.estimate_seconds or 0.0)
            command_chars[index] += delta_chars

        # Cold/unknown nodes never get invented durations. They are appended in stable
        # nodeid order to the least-populated non-slow shard that respects hard bounds.
        for item in unknown:
            delta_chars = 1 + _node_arg_chars(item.nodeid)
            candidates = [
                index
                for index, values in enumerate(bins)
                if len(values) < self.max_nodeids
                and (self.nodeid_transport == "manifest" or command_chars[index] + delta_chars <= self.max_command_chars)
            ]
            if not candidates:
                bins.append([])
                loads.append(0.0)
                command_chars.append(_BASE_COMMAND_CHARS)
                candidates = [len(bins) - 1]
            index = min(candidates, key=lambda idx: (len(bins[idx]), loads[idx], idx))
            bins[index].append(item)
            command_chars[index] += delta_chars

        shards.extend(self._new_shard(values, slow_singleton=False) for values in bins if values)
        for index, shard in enumerate(shards, start=1):
            shard["shard_id"] = f"temporal-{index:04d}"
            shard["ordinal"] = index

        flattened = [nodeid for shard in shards for nodeid in shard["nodeids"]]
        if sorted(flattened) != sorted(ordered) or len(flattened) != len(ordered):
            raise TemporalPlannerError("planner coverage invalid: omission or duplication detected")
        if any(shard["nodeids_total"] > self.max_nodeids for shard in shards):
            raise TemporalPlannerError("planner exceeded max_nodeids")
        if self.nodeid_transport == "command-line" and any(shard["command_chars"] > self.max_command_chars for shard in shards):
            raise TemporalPlannerError("planner exceeded max_command_chars")

        registry_provenance = {
            "schema_id": registry_data.get("schema_id"),
            "version": registry_data.get("version"),
            "canonical_sha256": _sha256(registry_data),
            "environment_fingerprint": environment_fingerprint,
        }
        core = {
            "schema_id": "devpilot.testing.temporal_shard_plan.v1",
            "version": TEMPORAL_PLANNER_VERSION,
            "planner": "deterministic-lpt-sequential",
            "mode": "shadow",
            "scheduler_enabled": False,
            "parallel_workers": DEFAULT_PARALLEL_WORKERS,
            "collection_sha256": computed_sha,
            "collection_total": len(ordered),
            "target_shard_seconds": self.target_shard_seconds,
            "max_nodeids": self.max_nodeids,
            "max_command_chars": self.max_command_chars,
            "nodeid_transport": self.nodeid_transport,
            "command_line_coupling": self.nodeid_transport == "command-line",
            "registry_provenance": registry_provenance,
            "shards": shards,
            "shards_total": len(shards),
            "known_nodeids": sum(1 for item in estimates if item.known),
            "unknown_nodeids": sum(1 for item in estimates if not item.known),
            "slow_singletons": len(slow),
        }
        return {**core, "plan_sha256": _sha256(core)}

    def _new_shard(self, values: Sequence[NodeEstimate], *, slow_singleton: bool) -> dict[str, Any]:
        nodeids = [item.nodeid for item in values]
        known_values = [float(item.estimate_seconds or 0.0) for item in values if item.known]
        confidence_counts: dict[str, int] = {}
        for item in values:
            confidence_counts[item.confidence] = confidence_counts.get(item.confidence, 0) + 1
        return {
            "shard_id": "",
            "ordinal": 0,
            "nodeids": nodeids,
            "nodeids_total": len(nodeids),
            "nodeids_sha256": _sha256(nodeids),
            "estimated_seconds": round(sum(known_values), 6),
            "known_count": sum(1 for item in values if item.known),
            "unknown_count": sum(1 for item in values if not item.known),
            "confidence_counts": dict(sorted(confidence_counts.items())),
            "command_chars": _command_chars(nodeids),
            "slow_singleton": slow_singleton,
        }

    def count_based_plan(self, nodeids: Sequence[str], *, environment_fingerprint: str, shard_size: int = 50) -> dict[str, Any]:
        if shard_size <= 0 or shard_size > 500:
            raise TemporalPlannerError("shard_size must be between 1 and 500")
        registry_data = self.registry.load()
        estimates = {nodeid: self._estimate_from_registry(registry_data, nodeid, environment_fingerprint) for nodeid in nodeids}
        shards = []
        for offset in range(0, len(nodeids), shard_size):
            chunk = list(nodeids[offset : offset + shard_size])
            values = [estimates[nodeid] for nodeid in chunk]
            shards.append(self._new_shard(values, slow_singleton=False))
        return {
            "planner": "historical-count-based",
            "shard_size": shard_size,
            "collection_sha256": self.collection_sha256(nodeids),
            "collection_total": len(nodeids),
            "shards": shards,
            "shards_total": len(shards),
        }

    @staticmethod
    def _metrics(plan: dict[str, Any]) -> dict[str, Any]:
        durations = [float(item.get("estimated_seconds") or 0.0) for item in plan.get("shards", [])]
        if not durations:
            return {"shards_total": 0, "predicted_max_seconds": 0.0, "predicted_p95_seconds": 0.0, "predicted_cv": 0.0, "predicted_mean_seconds": 0.0}
        return {
            "shards_total": len(durations),
            "predicted_max_seconds": round(max(durations), 6),
            "predicted_p95_seconds": round(_p95(durations), 6),
            "predicted_cv": round(_cv(durations), 6),
            "predicted_mean_seconds": round(statistics.mean(durations), 6),
        }

    def shadow_compare(
        self,
        nodeids: Sequence[str],
        *,
        environment_fingerprint: str,
        baseline_shard_size: int = 50,
        expected_collection_sha256: str | None = None,
        expected_environment_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        temporal = self.plan(
            nodeids,
            environment_fingerprint=environment_fingerprint,
            expected_collection_sha256=expected_collection_sha256,
            expected_environment_fingerprint=expected_environment_fingerprint,
        )
        baseline = self.count_based_plan(nodeids, environment_fingerprint=environment_fingerprint, shard_size=baseline_shard_size)
        base_metrics = self._metrics(baseline)
        temporal_metrics = self._metrics(temporal)

        def improvement(key: str) -> float:
            base = float(base_metrics[key])
            current = float(temporal_metrics[key])
            return 0.0 if base == 0 else round(((base - current) / base) * 100.0, 3)

        return {
            "schema_id": "devpilot.testing.temporal_shard_shadow_comparison.v1",
            "version": TEMPORAL_PLANNER_VERSION,
            "status": "PASS",
            "collection_sha256": temporal["collection_sha256"],
            "collection_total": temporal["collection_total"],
            "same_collection": temporal["collection_sha256"] == baseline["collection_sha256"],
            "tests_executed": False,
            "parallel_workers": 1,
            "baseline": {"planner": baseline["planner"], **base_metrics},
            "temporal": {"planner": temporal["planner"], **temporal_metrics, "slow_singletons": temporal["slow_singletons"]},
            "improvement_percent": {
                "predicted_max_seconds": improvement("predicted_max_seconds"),
                "predicted_p95_seconds": improvement("predicted_p95_seconds"),
                "predicted_cv": improvement("predicted_cv"),
            },
            "adoption_default": False,
        }


def load_collection_nodeids(path: Path) -> tuple[list[str], str | None, str | None]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload.get("nodes"), list):
        nodeids = [str(item["nodeid"]) for item in payload["nodes"]]
        return nodeids, payload.get("collection_sha256"), payload.get("environment_fingerprint")
    if isinstance(payload.get("samples"), list):
        nodeids = [str(item["nodeid"]) for item in payload["samples"]]
        return nodeids, payload.get("collection_sha256"), payload.get("environment_fingerprint")
    raise TemporalPlannerError("unsupported collection payload")
