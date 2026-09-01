from __future__ import annotations

import json
import subprocess
from pathlib import Path

import jsonschema
import pytest

from devpilot_core.testing.duration_registry import NodeDurationRegistry
from devpilot_core.testing.full_regression import FullRegressionSessionManager, TerminalOutcome, _source_descriptor
from devpilot_core.testing.full_regression_benchmark import (
    FullRegressionBenchmarkAnalyzer,
    FullRegressionBenchmarkError,
    OneFullAttemptGuard,
)


def _git(root: Path, *args: str) -> str:
    cp = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True)
    return cp.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "tests").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "pyproject.toml").write_text('[tool.pytest.ini_options]\ntestpaths=["tests"]\n', encoding="utf-8")
    (root / "tests/test_sample.py").write_text("def test_a(): assert True\ndef test_b(): assert True\n", encoding="utf-8")
    _git(root, "init")
    _git(root, "config", "user.email", "frx@example.invalid")
    _git(root, "config", "user.name", "FRX Test")
    _git(root, "config", "core.autocrlf", "true")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "baseline")
    return root


def test_git_semantic_source_fingerprint_ignores_crlf_but_detects_content(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    target = root / "src/example.py"
    target.write_text("value = 1\n", encoding="utf-8")
    _git(root, "add", "src/example.py")
    _git(root, "commit", "-m", "add example")
    first = _source_descriptor(root)
    target.write_bytes(b"value = 1\r\n")
    second = _source_descriptor(root)
    assert first["fingerprint_mode"] == "git-semantic-working-tree-v1"
    assert first["content_sha256"] == second["content_sha256"]
    target.write_bytes(b"value = 2\r\n")
    third = _source_descriptor(root)
    assert third["content_sha256"] != first["content_sha256"]


def test_temporal_full_plan_reorders_but_preserves_collection_exactly_once(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    reg = NodeDurationRegistry(root)
    reg.save(reg.empty())
    payload = {
        "environment_fingerprint": "duration-env",
        "samples": [
            {"nodeid": "tests/test_sample.py::test_a", "duration_seconds": 40.0},
            {"nodeid": "tests/test_sample.py::test_b", "duration_seconds": 1.0},
        ],
    }
    assert reg.ingest_payload(payload, source_receipt="fixture").accepted == 2
    manager = FullRegressionSessionManager(root)
    collected = manager.collect(session_id="temporal")
    assert collected.ok
    planned = manager.plan_temporal(session_id="temporal", registry_environment_fingerprint="duration-env", target_shard_seconds=10)
    assert planned.ok
    plan = json.loads((root / "outputs/testing/full_regression/temporal/plan.json").read_text(encoding="utf-8"))
    collection = json.loads((root / "outputs/testing/full_regression/temporal/collection.json").read_text(encoding="utf-8"))
    flattened = [node for shard in plan["shards"] for node in shard["nodeids"]]
    collected_nodes = [row["nodeid"] for row in collection["nodes"]]
    assert set(flattened) == set(collected_nodes)
    assert len(flattened) == len(set(flattened)) == len(collected_nodes)
    assert plan["parallel_workers"] == 1
    assert plan["scheduler_enabled_for_session"] is True
    assert plan["slow_singletons"] == 1
    schema = json.loads((Path(__file__).resolve().parents[1] / "docs/schemas/full_regression_temporal_shard_plan.schema.json").read_text())
    jsonschema.validate(plan, schema)


def test_one_full_marker_is_reusable_only_for_same_session_and_source(tmp_path: Path) -> None:
    marker = tmp_path / "marker.json"
    first = OneFullAttemptGuard.reserve(marker, session_id="FRX-V2-2-D-FULL-01", source_commit="abc")
    assert first.status == "PASS" and first.reused is False
    second = OneFullAttemptGuard.reserve(marker, session_id="FRX-V2-2-D-FULL-01", source_commit="abc")
    assert second.reused is True and second.marker["max_attempts"] == 1
    with pytest.raises(FullRegressionBenchmarkError):
        OneFullAttemptGuard.reserve(marker, session_id="FRX-V2-2-D-FULL-02", source_commit="abc")
    with pytest.raises(FullRegressionBenchmarkError):
        OneFullAttemptGuard.reserve(marker, session_id="FRX-V2-2-D-FULL-01", source_commit="other")


def test_benchmark_analyzer_emits_available_not_default_when_correct_but_threshold_missed(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    session_dir = root / "outputs/testing/full_regression/one"
    receipts = session_dir / "receipts"
    runtime = session_dir / "runtime"
    receipts.mkdir(parents=True)
    runtime.mkdir(parents=True)
    (root / "docs/audits").mkdir(parents=True)
    (root / ".devpilot/testing").mkdir(parents=True)
    baseline = {"shard_wall_seconds":{"sum":100.0,"max":50.0,"p95":50.0,"mean":25.0,"cv":0.5},"infra_abort_receipts_total":1,"resume_receipts_total":1}
    (root / "docs/audits/FRX_V2_2_D_BASELINE_07_E.json").write_text(json.dumps(baseline))
    policy = {"thresholds":{"min_max_shard_improvement_pct":25.0,"min_p95_shard_improvement_pct":25.0,"min_cv_improvement_pct":10.0,"max_infra_abort_receipts":1}}
    (root / ".devpilot/testing/frx_v2_2_d_adoption_policy.json").write_text(json.dumps(policy))
    (session_dir / "session.json").write_text(json.dumps({"collection_sha256":"a"*64,"collection_duration_seconds":2.0}))
    (session_dir / "collection.json").write_text(json.dumps({"nodeids_total":2}))
    (session_dir / "plan.json").write_text(json.dumps({"shards_total":2,"shard_plan_sha256":"b"*64,"planner":"deterministic-lpt-sequential","parallel_workers":1,"shards":[{"command_chars":100},{"command_chars":100}]}))
    (session_dir / "adjudication.json").write_text(json.dumps({"decision":"PASS","coverage_complete":True,"terminal_accounting":{"unexecuted_total":0,"fail_total":0,"error_total":0}}))
    for idx, duration in enumerate((45.0,45.0), start=1):
        outcome = runtime / f"s{idx}.outcomes.jsonl"
        outcome.write_text(json.dumps({"nodeid":f"tests/test_x.py::test_{idx}","outcome":"PASS","duration_seconds":40.0})+"\n")
        receipt={"duration_seconds":duration,"infra_abort":False,"source_mutation_detected":False,"attempt":1,"mode":"run","outcome_log_path":str(outcome.relative_to(root)).replace('\\','/')}
        (receipts / f"s{idx}.json").write_text(json.dumps(receipt))
    result = FullRegressionBenchmarkAnalyzer(root).analyze("one")
    assert result["status"] == "PASS"
    assert result["functional_pass"] is True
    assert result["adoption_decision"] == "PASS/AVAILABLE-NOT-DEFAULT"
    schema = json.loads((Path(__file__).resolve().parents[1] / "docs/schemas/frx_v2_2_d_full_benchmark.schema.json").read_text())
    jsonschema.validate(result, schema)


def test_current_07e_baseline_and_d_policy_are_consistent() -> None:
    root = Path(__file__).resolve().parents[1]
    baseline = json.loads((root / "docs/audits/FRX_V2_2_D_BASELINE_07_E.json").read_text())
    policy = json.loads((root / ".devpilot/testing/frx_v2_2_d_adoption_policy.json").read_text())
    compat = json.loads((root / ".devpilot/testing/frx_v2_2_d_environment_compatibility.json").read_text())
    assert baseline["receipts_total"] == 32
    assert baseline["infra_abort_receipts_total"] == 3
    assert baseline["shard_wall_seconds"]["max"] == pytest.approx(1800.032)
    assert baseline["shard_wall_seconds"]["p95"] == pytest.approx(1800.031)
    assert policy["workers"] == 1 and policy["second_full_allowed"] is False
    assert compat["duration_registry_environment"] == "windows-pytest-devpilot-gsdlc07e-v1"
    assert compat["required_python_major_minor"] == "3.12"
    assert compat["required_pytest_major"] == 9
    assert compat["strict_patch_match"] is False


def test_default_plan_uses_temporal_only_after_enabled_adoption(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    registry = NodeDurationRegistry(root)
    registry.save(registry.empty())
    assert registry.ingest_payload({
        "environment_fingerprint": "env-win",
        "samples": [
            {"nodeid": "tests/test_sample.py::test_a", "duration_seconds": 10.0},
            {"nodeid": "tests/test_sample.py::test_b", "duration_seconds": 20.0},
        ],
    }, source_receipt="adoption-fixture").accepted == 2
    cfg_path = root / ".devpilot/testing/temporal_planner_config.json"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = {"scheduler_enabled": False, "parallel_workers": 1, "registry_environment_fingerprint": "env-win", "target_shard_seconds": 300, "max_nodeids": 50, "max_command_chars": 7000}
    cfg_path.write_text(json.dumps(cfg) + "\n", encoding="utf-8")
    manager = FullRegressionSessionManager(root)
    assert manager.collect(session_id="adoption-default").ok
    count_result = manager.plan(session_id="adoption-default", shard_size=1, shard_timeout_seconds=900)
    assert count_result.ok
    count_plan = json.loads((root / "outputs/testing/full_regression/adoption-default/plan.json").read_text(encoding="utf-8"))
    assert count_plan["schema_id"] == "devpilot.testing.full_regression_shard_plan.v2_1"

    cfg["scheduler_enabled"] = True
    cfg_path.write_text(json.dumps(cfg) + "\n", encoding="utf-8")
    assert manager.collect(session_id="adoption-enabled").ok
    temporal_result = manager.plan(session_id="adoption-enabled", shard_timeout_seconds=900)
    assert temporal_result.ok
    temporal_plan = json.loads((root / "outputs/testing/full_regression/adoption-enabled/plan.json").read_text(encoding="utf-8"))
    assert temporal_plan["schema_id"] == "devpilot.testing.full_regression_temporal_shard_plan.v2_2"
    assert temporal_plan["parallel_workers"] == 1



def test_closure_consistency_reports_v2_2_full_budget() -> None:
    from devpilot_core.docs_governance.consistency import ClosureStateConsistencyValidator
    root = Path(__file__).resolve().parents[1]
    result = ClosureStateConsistencyValidator(root).run()
    assert result.ok, result.to_dict()
    assert result.data["summary"]["full_regression_runs_consumed"] == 0
