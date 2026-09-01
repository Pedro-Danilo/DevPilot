from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from devpilot_core.testing.duration_registry import NodeDurationRegistry
from devpilot_core.testing.temporal_shard_planner import TemporalPlannerError, TemporalShardPlanner


def _registry(root: Path, samples: list[tuple[str, float]], env: str = "env-a") -> NodeDurationRegistry:
    reg = NodeDurationRegistry(root, registry_path=root / "registry.json")
    payload = {"environment_fingerprint": env, "samples": [{"nodeid": n, "duration_seconds": d} for n, d in samples]}
    result = reg.ingest_payload(payload, source_receipt="fixture")
    assert result.accepted == len(samples)
    return reg


def test_determinism_ten_repeated_plans(tmp_path: Path):
    nodes = [(f"tests/test_x.py::test_{i}", float((i % 7) + 1)) for i in range(40)]
    reg = _registry(tmp_path, nodes)
    planner = TemporalShardPlanner(tmp_path, registry_path=reg.path, target_shard_seconds=20, max_nodeids=10, max_command_chars=1200)
    plans = [planner.plan([n for n, _ in nodes], environment_fingerprint="env-a") for _ in range(10)]
    assert len({plan["plan_sha256"] for plan in plans}) == 1


def test_no_duplicates_omissions_and_bounds(tmp_path: Path):
    nodes = [(f"tests/test_x.py::test_{i}", float(i + 1)) for i in range(25)]
    reg = _registry(tmp_path, nodes)
    planner = TemporalShardPlanner(tmp_path, registry_path=reg.path, target_shard_seconds=30, max_nodeids=7, max_command_chars=600)
    plan = planner.plan([n for n, _ in nodes], environment_fingerprint="env-a")
    flattened = [n for shard in plan["shards"] for n in shard["nodeids"]]
    assert sorted(flattened) == sorted(n for n, _ in nodes)
    assert len(flattened) == len(set(flattened))
    assert max(s["nodeids_total"] for s in plan["shards"]) <= 7
    assert max(s["command_chars"] for s in plan["shards"]) <= 600


def test_slow_node_over_target_is_singleton(tmp_path: Path):
    nodes = [("tests/test_x.py::test_slow", 301.0), ("tests/test_x.py::test_fast", 2.0)]
    reg = _registry(tmp_path, nodes)
    plan = TemporalShardPlanner(tmp_path, registry_path=reg.path).plan([n for n, _ in nodes], environment_fingerprint="env-a")
    slow = next(s for s in plan["shards"] if "tests/test_x.py::test_slow" in s["nodeids"])
    assert slow["slow_singleton"] is True
    assert slow["nodeids_total"] == 1


def test_all_unknown_cold_start_is_stable_and_bounded(tmp_path: Path):
    reg = NodeDurationRegistry(tmp_path, registry_path=tmp_path / "registry.json")
    reg.save(reg.empty())
    nodeids = [f"tests/test_x.py::test_{i:03d}" for i in reversed(range(20))]
    planner = TemporalShardPlanner(tmp_path, registry_path=reg.path, max_nodeids=5, max_command_chars=600)
    plan = planner.plan(nodeids, environment_fingerprint="env-a")
    flattened = [n for shard in plan["shards"] for n in shard["nodeids"]]
    assert plan["known_nodeids"] == 0 and plan["unknown_nodeids"] == 20
    assert flattened == sorted(nodeids)
    assert max(s["nodeids_total"] for s in plan["shards"]) <= 5


def test_mixed_confidence_is_reported(tmp_path: Path):
    reg = NodeDurationRegistry(tmp_path, registry_path=tmp_path / "registry.json")
    for idx in range(5):
        reg.ingest_payload({"environment_fingerprint":"env-a","samples":[{"nodeid":"tests/test_x.py::test_warm","duration_seconds":1+idx}]}, source_receipt=f"r{idx}")
    reg.ingest_payload({"environment_fingerprint":"env-a","samples":[{"nodeid":"tests/test_x.py::test_cold","duration_seconds":2}]}, source_receipt="cold")
    planner = TemporalShardPlanner(tmp_path, registry_path=reg.path, target_shard_seconds=10)
    plan = planner.plan(["tests/test_x.py::test_warm","tests/test_x.py::test_cold"], environment_fingerprint="env-a")
    counts = {}
    for shard in plan["shards"]:
        for key, value in shard["confidence_counts"].items(): counts[key] = counts.get(key, 0) + value
    assert counts["high"] == 1 and counts["low"] == 1


def test_collection_and_environment_mismatch_block(tmp_path: Path):
    nodes = [("tests/test_x.py::test_one", 1.0)]
    reg = _registry(tmp_path, nodes)
    planner = TemporalShardPlanner(tmp_path, registry_path=reg.path)
    with pytest.raises(TemporalPlannerError, match="collection/fingerprint mismatch"):
        planner.plan([nodes[0][0]], environment_fingerprint="env-a", expected_collection_sha256="deadbeef")
    with pytest.raises(TemporalPlannerError, match="environment fingerprint mismatch"):
        planner.plan([nodes[0][0]], environment_fingerprint="env-a", expected_environment_fingerprint="other")


def test_shadow_compare_improves_skewed_reference(tmp_path: Path):
    samples = [(f"tests/test_x.py::test_{i:03d}", 1.0) for i in range(98)] + [
        ("tests/test_x.py::test_slow_a", 250.0), ("tests/test_x.py::test_slow_b", 250.0)
    ]
    reg = _registry(tmp_path, samples)
    planner = TemporalShardPlanner(tmp_path, registry_path=reg.path, target_shard_seconds=100, max_nodeids=50, max_command_chars=5000)
    comparison = planner.shadow_compare([n for n, _ in samples], environment_fingerprint="env-a", baseline_shard_size=50)
    assert comparison["same_collection"] is True
    assert comparison["tests_executed"] is False
    assert comparison["temporal"]["predicted_max_seconds"] < comparison["baseline"]["predicted_max_seconds"]
    assert comparison["parallel_workers"] == 1


def test_real_registry_snapshot_plan_and_schema():
    root = Path(__file__).resolve().parents[1]
    telemetry = json.loads((root / ".devpilot/testing/frx_v2_2_b_initial_telemetry.json").read_text(encoding="utf-8"))
    nodeids = [item["nodeid"] for item in telemetry["samples"]]
    env = telemetry["environment_fingerprint"]
    planner = TemporalShardPlanner(root)
    plan = planner.plan(nodeids, environment_fingerprint=env)
    assert plan["collection_total"] == 2805
    assert plan["parallel_workers"] == 1 and plan["scheduler_enabled"] is False
    assert plan["slow_singletons"] > 0
    schema = json.loads((root / "docs/schemas/temporal_shard_plan.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(plan, schema)


def test_schema_catalog_registers_temporal_plan():
    root = Path(__file__).resolve().parents[1]
    catalog = json.loads((root / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    entries = [item for item in catalog["schemas"] if item.get("schema_id") == "SCHEMA-DEVPL-TEMPORAL-SHARD-PLAN-V1"]
    assert len(entries) == 1
    assert entries[0]["path"] == "docs/schemas/temporal_shard_plan.schema.json"
    assert catalog["schemas_total"] == len(catalog["schemas"])
