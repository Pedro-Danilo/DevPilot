from __future__ import annotations

import json
from pathlib import Path

import pytest

from devpilot_core.testing.conflict_graph import ParallelShadowPlanner
from devpilot_core.testing.parallel_canary import (
    BoundedParallelCanaryRunner,
    ParallelCanaryBlock,
    ResourceLockTable,
)


ROOT = Path(__file__).resolve().parents[1]
LOCAL_NODE = "tests/test_post_h_020_compliance_mapping_quality_gate.py::test_post_h_020_d_compliance_mapping_quality_gate_passes"
READ_ONLY_NODE = "tests/test_post_h_018_connector_sandbox_gate.py::test_post_h_018_e_connector_sandbox_quality_gate_passes_without_network_or_write"


def _manifest(root: Path) -> dict:
    return json.loads((root / ".devpilot/testing/frx_v2_3_d_canary_manifest.json").read_text(encoding="utf-8"))


def _registry(root: Path) -> dict:
    return json.loads((root / ".devpilot/testing/test_isolation_registry.json").read_text(encoding="utf-8"))


def test_frx_v2_3_d_manifest_is_exactly_two_distinct_atomic_jobs() -> None:
    manifest = _manifest(ROOT)
    jobs = manifest["jobs"]
    assert len(jobs) == 2
    assert {job["nodeid"] for job in jobs} == {LOCAL_NODE, READ_ONLY_NODE}
    assert len({job["contract_id"] for job in jobs}) == 2
    assert manifest["policy"]["max_workers"] == 2
    assert manifest["policy"]["full_regression_runs"] == 0


def test_frx_v2_3_d_manifest_never_enables_shell_xdist_network_or_full() -> None:
    policy = _manifest(ROOT)["policy"]
    assert policy["shell_allowed"] is False
    assert policy["xdist_allowed"] is False
    assert policy["network_runtime_allowed"] is False
    assert policy["full_regression_runs"] == 0


def test_frx_v2_3_d_selected_jobs_are_proven_parallel_safe() -> None:
    registry = _registry(ROOT)
    by_nodeid = {entry["nodeid"]: entry for entry in registry["entries"]}
    for nodeid in (LOCAL_NODE, READ_ONLY_NODE):
        assert by_nodeid[nodeid]["state"] == "PROVEN_PARALLEL_SAFE"
        assert by_nodeid[nodeid]["parallel_safe"] is True
        assert by_nodeid[nodeid]["review"]["evidence_ids"]


def test_frx_v2_3_d_selected_jobs_have_no_conflict_edge() -> None:
    registry = _registry(ROOT)
    wanted = {LOCAL_NODE, READ_ONLY_NODE}
    entries = [entry for entry in registry["entries"] if entry["nodeid"] in wanted]
    graph = ParallelShadowPlanner.build_conflict_graph(entries)
    assert graph.nodes == tuple(sorted(wanted))
    assert graph.edges == ()


def test_frx_v2_3_d_preview_validates_br_authority_without_execution() -> None:
    preview = BoundedParallelCanaryRunner(ROOT).preview()
    assert preview["status"] == "PREVIEW"
    assert preview["decision"] == "PREVIEW"
    assert preview["jobs_total"] == 2
    assert preview["max_workers"] == 2
    assert preview["full_regression_runs"] == 0
    assert preview["conflict_violations"] == 0
    assert preview["validation"]["br_shadow_checked"] is True


def test_frx_v2_3_d_resource_lock_table_is_deterministic() -> None:
    table = ResourceLockTable()
    assert table.acquire("a", ["repo:x", "db:y"]) is True
    assert table.acquire("b", ["repo:x"]) is False
    table.release("a", ["repo:x", "db:y"])
    assert table.acquire("b", ["repo:x"]) is True
    assert [event["event"] for event in table.trace] == [
        "lock-request", "lock-acquired", "lock-request", "lock-blocked", "lock-released", "lock-request", "lock-acquired"
    ]


def test_frx_v2_3_d_terminal_receipt_reads_only_selected_node(tmp_path: Path) -> None:
    path = tmp_path / "outcomes.jsonl"
    path.write_text(
        json.dumps({"nodeid": "other", "outcome": "FAIL", "when": "call"}) + "\n"
        + json.dumps({"nodeid": LOCAL_NODE, "outcome": "PASS", "when": "call"}) + "\n",
        encoding="utf-8",
    )
    receipt = BoundedParallelCanaryRunner._terminal_receipt(path, LOCAL_NODE)
    assert receipt is not None
    assert receipt["outcome"] == "PASS"


def test_frx_v2_3_d_artifact_shape_requires_same_nodeids_and_artifacts() -> None:
    serial = {"jobs": [{"nodeid": LOCAL_NODE, "junit_exists": True, "outcomes_exists": True, "log_exists": True}]}
    parallel = {"jobs": [{"nodeid": LOCAL_NODE, "junit_exists": True, "outcomes_exists": True, "log_exists": True}]}
    assert BoundedParallelCanaryRunner._artifact_shape(serial) == BoundedParallelCanaryRunner._artifact_shape(parallel)
    parallel["jobs"][0]["junit_exists"] = False
    assert BoundedParallelCanaryRunner._artifact_shape(serial) != BoundedParallelCanaryRunner._artifact_shape(parallel)


def test_frx_v2_3_d_block_reason_includes_parallel_overhead() -> None:
    reason = BoundedParallelCanaryRunner._why_blocked(
        {
            "outcome_parity": True,
            "runtime_artifact_shape_parity": True,
            "source_clean": True,
            "secret_leakage": False,
            "conflict_violations": 0,
            "incremental_parallel_speedup_percent": 0.0,
        }
    )
    assert "parallel overhead" in reason


def test_frx_v2_3_d_rejects_manifest_that_expands_worker_bound(tmp_path: Path) -> None:
    manifest = _manifest(ROOT)
    manifest["policy"]["max_workers"] = 3
    target = tmp_path / "manifest.json"
    target.write_text(json.dumps(manifest), encoding="utf-8")
    runner = BoundedParallelCanaryRunner(ROOT, manifest_path=target.relative_to(ROOT) if target.is_relative_to(ROOT) else Path("missing"))
    # Use a runner rooted at tmp with the relevant file copied to make the test
    # independent from host path semantics.
    scratch = tmp_path / "repo"
    (scratch / ".devpilot/testing").mkdir(parents=True)
    (scratch / ".devpilot/testing/frx_v2_3_d_canary_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    bad = BoundedParallelCanaryRunner(scratch).preview()
    assert bad["status"] == "BLOCK"
    assert "workers=2" in bad["block_reason"]
