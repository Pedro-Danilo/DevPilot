from __future__ import annotations

import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .full_regression import _canonical_bytes


class FullRegressionBenchmarkError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256(payload: Any) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    return float(ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)])


def _cv(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = statistics.mean(values)
    return 0.0 if mean == 0 else float(statistics.pstdev(values) / mean)


def _improvement(baseline: float, actual: float) -> float:
    return 0.0 if baseline == 0 else round(((baseline - actual) / baseline) * 100.0, 3)


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


@dataclass(frozen=True)
class AttemptMarkerResult:
    status: str
    reused: bool
    marker: dict[str, Any]


class OneFullAttemptGuard:
    """Immutable one-logical-full marker used by FRX-v2.2-D.

    Reinvocation with the same session/source reuses the marker. Any request for
    another session is rejected rather than silently consuming a second full.
    """

    SCHEMA_ID = "devpilot.frx.v2_2_d.one_full_marker.v1"

    @classmethod
    def reserve(cls, path: Path, *, session_id: str, source_commit: str) -> AttemptMarkerResult:
        path = Path(path)
        expected = {
            "schema_id": cls.SCHEMA_ID,
            "micro_sprint": "FRX-v2.2-D",
            "attempt": 1,
            "max_attempts": 1,
            "second_full_allowed": False,
            "session_id": session_id,
            "source_commit": source_commit,
        }
        if path.exists():
            current = json.loads(path.read_text(encoding="utf-8"))
            for key, value in expected.items():
                if current.get(key) != value:
                    raise FullRegressionBenchmarkError("one-full marker already binds a different logical full")
            return AttemptMarkerResult(status="PASS", reused=True, marker=current)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {**expected, "created_at": _now()}
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
        return AttemptMarkerResult(status="PASS", reused=False, marker=payload)


class FullRegressionBenchmarkAnalyzer:
    """Analyze one sealed sequential full against the immutable 07-E baseline."""

    def __init__(
        self,
        root: Path,
        *,
        runtime_root: Path = Path("outputs/testing/full_regression"),
        baseline_path: Path = Path("docs/audits/FRX_V2_2_D_BASELINE_07_E.json"),
        policy_path: Path = Path(".devpilot/testing/frx_v2_2_d_adoption_policy.json"),
    ) -> None:
        self.root = Path(root).resolve()
        self.runtime_root = runtime_root if runtime_root.is_absolute() else self.root / runtime_root
        self.baseline_path = baseline_path if baseline_path.is_absolute() else self.root / baseline_path
        self.policy_path = policy_path if policy_path.is_absolute() else self.root / policy_path

    def analyze(self, session_id: str) -> dict[str, Any]:
        session_dir = self.runtime_root / session_id
        required = ["session.json", "collection.json", "plan.json", "adjudication.json"]
        missing = [name for name in required if not (session_dir / name).is_file()]
        if missing:
            raise FullRegressionBenchmarkError(f"missing full artifacts: {missing}")
        session = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
        collection = json.loads((session_dir / "collection.json").read_text(encoding="utf-8"))
        plan = json.loads((session_dir / "plan.json").read_text(encoding="utf-8"))
        adjudication = json.loads((session_dir / "adjudication.json").read_text(encoding="utf-8"))
        baseline = json.loads(self.baseline_path.read_text(encoding="utf-8"))
        policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        receipts = sorted((session_dir / "receipts").glob("*.json")) if (session_dir / "receipts").is_dir() else []
        if not receipts:
            raise FullRegressionBenchmarkError("full benchmark has no shard receipts")

        shard_wall: list[float] = []
        lifecycle_wall: list[float] = []
        receipt_intervals: list[tuple[datetime, datetime]] = []
        node_runtime_total = 0.0
        process_overhead_total = 0.0
        source_guard_total = 0.0
        orchestrator_receipt_overhead_total = 0.0
        infra_abort_receipts = 0
        resume_receipts = 0
        source_mutation_receipts = 0
        for receipt_path in receipts:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            duration = float(receipt.get("duration_seconds") or 0.0)
            shard_wall.append(duration)
            lifecycle_duration = float(receipt.get("lifecycle_duration_seconds") or duration)
            lifecycle_wall.append(lifecycle_duration)
            source_guard_total += float(receipt.get("source_guard_before_seconds") or 0.0) + float(receipt.get("source_guard_after_seconds") or 0.0)
            orchestrator_receipt_overhead_total += float(receipt.get("orchestrator_overhead_seconds") or max(0.0, lifecycle_duration - duration))
            started = _parse_utc(receipt.get("lifecycle_started_at") or receipt.get("started_at"))
            ended = _parse_utc(receipt.get("lifecycle_ended_at") or receipt.get("ended_at"))
            if started is not None and ended is not None and ended >= started:
                receipt_intervals.append((started, ended))
            infra_abort_receipts += int(bool(receipt.get("infra_abort")))
            source_mutation_receipts += int(bool(receipt.get("source_mutation_detected")))
            resume_receipts += int(int(receipt.get("attempt") or 1) > 1 or receipt.get("mode") == "resume")
            node_runtime = 0.0
            outcome_log_rel = receipt.get("outcome_log_path")
            if outcome_log_rel:
                outcome_path = self.root / str(outcome_log_rel)
                if outcome_path.is_file():
                    for line in outcome_path.read_text(encoding="utf-8", errors="replace").splitlines():
                        try:
                            row = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        node_runtime += float(row.get("duration_seconds") or 0.0)
            node_runtime_total += node_runtime
            process_overhead_total += max(0.0, duration - node_runtime)

        receipt_intervals.sort(key=lambda item: item[0])
        observed_wall_seconds = 0.0
        inter_shard_gap_seconds = 0.0
        if receipt_intervals:
            observed_wall_seconds = max(0.0, (receipt_intervals[-1][1] - receipt_intervals[0][0]).total_seconds())
            previous_end = receipt_intervals[0][1]
            for started, ended in receipt_intervals[1:]:
                inter_shard_gap_seconds += max(0.0, (started - previous_end).total_seconds())
                if ended > previous_end:
                    previous_end = ended
        hidden_orchestrator_seconds = max(0.0, observed_wall_seconds - sum(shard_wall))
        hidden_overhead_ratio = 0.0 if observed_wall_seconds <= 0 else hidden_orchestrator_seconds / observed_wall_seconds
        actual_metrics = {
            "receipts_total": len(receipts),
            "planned_shards_total": int(plan.get("shards_total") or 0),
            "infra_abort_receipts_total": infra_abort_receipts,
            "resume_receipts_total": resume_receipts,
            "source_mutation_receipts_total": source_mutation_receipts,
            "collection_duration_seconds": round(float(session.get("collection_duration_seconds") or 0.0), 6),
            "node_runtime_seconds_total": round(node_runtime_total, 6),
            "process_overhead_seconds_total": round(process_overhead_total, 6),
            "lifecycle_wall_seconds_total": round(sum(lifecycle_wall), 6),
            "observed_end_to_end_wall_seconds": round(observed_wall_seconds, 6),
            "inter_shard_gap_seconds_total": round(inter_shard_gap_seconds, 6),
            "hidden_orchestrator_seconds_total": round(hidden_orchestrator_seconds, 6),
            "hidden_orchestrator_overhead_ratio": round(hidden_overhead_ratio, 6),
            "source_guard_seconds_total": round(source_guard_total, 6),
            "receipt_orchestrator_overhead_seconds_total": round(orchestrator_receipt_overhead_total, 6),
            "shard_wall_seconds": {
                "sum": round(sum(shard_wall), 6),
                "max": round(max(shard_wall), 6),
                "p95": round(_p95(shard_wall), 6),
                "mean": round(statistics.mean(shard_wall), 6),
                "cv": round(_cv(shard_wall), 6),
            },
            "command_chars": {
                "max": max(int(shard.get("command_chars") or 0) for shard in plan.get("shards", [])),
                "p95": round(_p95([float(shard.get("command_chars") or 0) for shard in plan.get("shards", [])]), 3),
            },
        }
        base_wall = baseline["shard_wall_seconds"]
        actual_wall = actual_metrics["shard_wall_seconds"]
        improvements = {
            "max_shard_pct": _improvement(float(base_wall["max"]), float(actual_wall["max"])),
            "p95_shard_pct": _improvement(float(base_wall["p95"]), float(actual_wall["p95"])),
            "cv_pct": _improvement(float(base_wall["cv"]), float(actual_wall["cv"])),
            "total_wall_pct": _improvement(float(base_wall["sum"]), float(actual_metrics["observed_end_to_end_wall_seconds"] or actual_wall["sum"])),
            "infra_abort_receipts_reduction": int(baseline["infra_abort_receipts_total"]) - infra_abort_receipts,
            "resume_receipts_reduction": int(baseline["resume_receipts_total"]) - resume_receipts,
        }
        terminal = adjudication.get("terminal_accounting") or {}
        functional_pass = (
            adjudication.get("decision") == "PASS"
            and bool(adjudication.get("coverage_complete"))
            and int(terminal.get("unexecuted_total") or 0) == 0
            and int(terminal.get("fail_total") or 0) == 0
            and int(terminal.get("error_total") or 0) == 0
            and source_mutation_receipts == 0
            and int(plan.get("parallel_workers") or 1) == 1
        )
        thresholds = policy["thresholds"]
        performance_pass = (
            improvements["max_shard_pct"] >= float(thresholds["min_max_shard_improvement_pct"])
            and improvements["p95_shard_pct"] >= float(thresholds["min_p95_shard_improvement_pct"])
            and improvements["cv_pct"] >= float(thresholds["min_cv_improvement_pct"])
            and infra_abort_receipts <= int(thresholds["max_infra_abort_receipts"])
            and improvements["total_wall_pct"] >= float(thresholds.get("min_total_wall_improvement_pct", -1000000.0))
            and actual_metrics["hidden_orchestrator_overhead_ratio"] <= float(thresholds.get("max_orchestrator_hidden_overhead_ratio", 1.0))
        )
        if not functional_pass:
            adoption = "BLOCK"
            status = "BLOCK"
        elif performance_pass:
            adoption = "PASS/ENABLED"
            status = "PASS"
        else:
            adoption = "PASS/AVAILABLE-NOT-DEFAULT"
            status = "PASS"
        core = {
            "schema_id": "devpilot.frx.v2_2_d.full_benchmark.v1",
            "status": status,
            "session_id": session_id,
            "generated_at": _now(),
            "collection_total": int(collection.get("nodeids_total") or 0),
            "collection_sha256": session.get("collection_sha256"),
            "shard_plan_sha256": plan.get("shard_plan_sha256"),
            "planner": plan.get("planner"),
            "parallel_workers": int(plan.get("parallel_workers") or 1),
            "logical_full_attempts": 1,
            "second_full": False,
            "functional_pass": functional_pass,
            "baseline": baseline,
            "actual": actual_metrics,
            "improvement_percent": improvements,
            "thresholds": thresholds,
            "performance_threshold_pass": performance_pass,
            "adoption_decision": adoption,
        }
        return {**core, "benchmark_sha256": _sha256(core)}
