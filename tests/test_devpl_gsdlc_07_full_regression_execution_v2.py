from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import jsonschema

from devpilot_core.cli_models import ExitCode
from devpilot_core.testing.full_regression import (
    FullRegressionSessionManager,
    ShardReceipt,
    TerminalOutcome,
    _canonical_bytes,
    _sha256_bytes,
    _utc_now,
)


def _make_test_repo(tmp_path: Path, body: str) -> Path:
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "pyproject.toml").write_text('[tool.pytest.ini_options]\ntestpaths=["tests"]\n', encoding="utf-8")
    (root / "tests" / "test_sample.py").write_text(body, encoding="utf-8")
    return root


def _load(root: Path, session_id: str, name: str) -> dict:
    return json.loads((root / "outputs/testing/full_regression" / session_id / name).read_text(encoding="utf-8"))


def _synthetic_receipt(manager: FullRegressionSessionManager, kwargs: dict, outcomes: dict[str, str], *, infra_abort: bool = False) -> ShardReceipt:
    session = kwargs["session"]
    plan = kwargs["plan"]
    shard = kwargs["shard"]
    now = _utc_now()
    observed = tuple(nodeid for nodeid, outcome in outcomes.items() if outcome != TerminalOutcome.UNEXECUTED.value)
    return ShardReceipt(
        session_id=session["session_id"],
        shard_id=shard["shard_id"],
        attempt=kwargs["attempt"],
        mode=kwargs["mode"],
        started_at=now,
        ended_at=now,
        duration_seconds=0.01,
        source_fingerprint_before=session["source_fingerprint"],
        source_fingerprint_after=session["source_fingerprint"],
        environment_fingerprint=session["environment_fingerprint"],
        collection_sha256=session["collection_sha256"],
        shard_plan_sha256=plan["shard_plan_sha256"],
        planned_nodeids=tuple(kwargs["nodeids"]),
        observed_nodeids=observed,
        outcomes=outcomes,
        returncode=2 if infra_abort else (1 if TerminalOutcome.FAIL.value in outcomes.values() else 0),
        timed_out=infra_abort,
        infra_abort=infra_abort,
        source_mutation_detected=False,
        junit_path=None,
        junit_sha256=None,
        outcome_log_path=None,
        outcome_log_sha256=None,
    )


def test_collection_is_stable_unique_and_hash_sealed(tmp_path: Path) -> None:
    root = _make_test_repo(tmp_path, "def test_a(): assert True\ndef test_b(): assert True\n")
    manager = FullRegressionSessionManager(root)
    result = manager.collect(session_id="stable")
    assert result.exit_code == ExitCode.PASS
    collection = _load(root, "stable", "collection.json")
    session = _load(root, "stable", "session.json")
    nodeids = [item["nodeid"] for item in collection["nodes"]]
    assert nodeids == ["tests/test_sample.py::test_a", "tests/test_sample.py::test_b"]
    assert len(nodeids) == len(set(nodeids))
    assert _sha256_bytes(_canonical_bytes(collection)) == session["collection_sha256"]


def test_plan_is_deterministic_and_preserves_collection_exactly_once(tmp_path: Path) -> None:
    root = _make_test_repo(tmp_path, "def test_a(): assert True\ndef test_b(): assert True\ndef test_c(): assert True\n")
    manager = FullRegressionSessionManager(root)
    assert manager.collect(session_id="plan").ok
    first = manager.plan(session_id="plan", shard_size=2)
    second = manager.plan(session_id="plan", shard_size=2)
    assert first.ok and second.ok
    plan = _load(root, "plan", "plan.json")
    flattened = [nodeid for shard in plan["shards"] for nodeid in shard["nodeids"]]
    collection = _load(root, "plan", "collection.json")
    assert flattened == [item["nodeid"] for item in collection["nodes"]]
    core = {k: v for k, v in plan.items() if k != "shard_plan_sha256"}
    assert _sha256_bytes(_canonical_bytes(core)) == plan["shard_plan_sha256"]


def test_completion_first_continues_after_ordinary_failure(tmp_path: Path) -> None:
    root = _make_test_repo(tmp_path, "def test_fail(): assert False\ndef test_pass(): assert True\n")
    manager = FullRegressionSessionManager(root)
    assert manager.collect(session_id="fail").ok
    assert manager.plan(session_id="fail", shard_size=1).ok
    calls = {"n": 0}

    def fake_execute(**kwargs):
        calls["n"] += 1
        nodeid = kwargs["nodeids"][0]
        outcome = TerminalOutcome.FAIL.value if calls["n"] == 1 else TerminalOutcome.PASS.value
        return _synthetic_receipt(manager, kwargs, {nodeid: outcome}), None

    manager._execute_shard = fake_execute  # type: ignore[method-assign]
    result = manager.run(session_id="fail", execute=True)
    assert result.exit_code == ExitCode.FAIL
    summary = result.data["summary"]
    assert summary["fail_total"] == 1
    assert summary["pass_total"] == 1
    assert summary["unexecuted_total"] == 0
    assert summary["receipts_total"] == 2


def test_infra_abort_preserves_progress_and_resume_same_session(tmp_path: Path) -> None:
    root = _make_test_repo(tmp_path, "def test_a(): assert True\ndef test_b(): assert True\n")
    manager = FullRegressionSessionManager(root)
    assert manager.collect(session_id="resume").ok
    assert manager.plan(session_id="resume", shard_size=1).ok
    first = {"done": False}

    def abort_once(**kwargs):
        nodeid = kwargs["nodeids"][0]
        if not first["done"]:
            first["done"] = True
            return _synthetic_receipt(manager, kwargs, {nodeid: TerminalOutcome.UNEXECUTED.value}, infra_abort=True), "synthetic infra abort"
        return _synthetic_receipt(manager, kwargs, {nodeid: TerminalOutcome.PASS.value}), None

    manager._execute_shard = abort_once  # type: ignore[method-assign]
    blocked = manager.run(session_id="resume", execute=True)
    assert blocked.exit_code == ExitCode.BLOCK

    def succeed(**kwargs):
        return _synthetic_receipt(manager, kwargs, {nodeid: TerminalOutcome.PASS.value for nodeid in kwargs["nodeids"]}), None

    manager._execute_shard = succeed  # type: ignore[method-assign]
    resumed = manager.resume(session_id="resume", execute=True)
    assert resumed.exit_code == ExitCode.PASS
    status = manager.status(session_id="resume")
    assert status.data["summary"]["unexecuted_total"] == 0
    assert status.data["summary"]["pass_total"] == 2
    assert status.data["summary"]["logical_attempts"] == 1


def test_fingerprint_mismatch_blocks_resume(tmp_path: Path) -> None:
    root = _make_test_repo(tmp_path, "def test_a(): assert True\n")
    manager = FullRegressionSessionManager(root)
    assert manager.collect(session_id="drift").ok
    assert manager.plan(session_id="drift", shard_size=1).ok
    (root / "src" / "changed.py").write_text("x=1\n", encoding="utf-8")
    result = manager.resume(session_id="drift", execute=True)
    assert result.exit_code == ExitCode.BLOCK
    assert any(f.id == "FRX2_SOURCE_FINGERPRINT_MISMATCH" for f in result.findings)


def test_partial_session_cannot_adjudicate_pass(tmp_path: Path) -> None:
    root = _make_test_repo(tmp_path, "def test_a(): assert True\ndef test_b(): assert True\n")
    manager = FullRegressionSessionManager(root)
    assert manager.collect(session_id="partial").ok
    assert manager.plan(session_id="partial", shard_size=1).ok

    def succeed(**kwargs):
        return _synthetic_receipt(manager, kwargs, {nodeid: TerminalOutcome.PASS.value for nodeid in kwargs["nodeids"]}), None

    manager._execute_shard = succeed  # type: ignore[method-assign]
    assert manager.run(session_id="partial", execute=True, max_shards=1).ok
    result = manager.adjudicate(session_id="partial")
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["unexecuted_total"] == 1


def test_receipts_and_final_adjudication_are_schema_valid(tmp_path: Path) -> None:
    root = _make_test_repo(tmp_path, "def test_a(): assert True\n")
    manager = FullRegressionSessionManager(root)
    assert manager.collect(session_id="schema").ok
    assert manager.plan(session_id="schema", shard_size=1).ok

    def succeed(**kwargs):
        return _synthetic_receipt(manager, kwargs, {nodeid: TerminalOutcome.PASS.value for nodeid in kwargs["nodeids"]}), None

    manager._execute_shard = succeed  # type: ignore[method-assign]
    assert manager.run(session_id="schema", execute=True).ok
    assert manager.adjudicate(session_id="schema").ok
    source_root = Path(__file__).resolve().parents[1]
    pairs = [
        ("session.json", "full_regression_session.schema.json"),
        ("collection.json", "full_regression_collection.schema.json"),
        ("plan.json", "full_regression_shard_plan.schema.json"),
        ("adjudication.json", "full_regression_adjudication.schema.json"),
    ]
    for artifact, schema_name in pairs:
        payload = _load(root, "schema", artifact)
        schema = json.loads((source_root / "docs/schemas" / schema_name).read_text(encoding="utf-8"))
        jsonschema.validate(payload, schema)
    receipt = next((root / "outputs/testing/full_regression/schema/receipts").glob("*.json"))
    receipt_schema = json.loads((source_root / "docs/schemas/full_regression_shard_receipt.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(json.loads(receipt.read_text(encoding="utf-8")), receipt_schema)


def test_run_without_execute_is_preview_only(tmp_path: Path) -> None:
    root = _make_test_repo(tmp_path, "def test_a(): assert True\n")
    manager = FullRegressionSessionManager(root)
    assert manager.collect(session_id="preview").ok
    assert manager.plan(session_id="preview", shard_size=1).ok
    result = manager.run(session_id="preview", execute=False)
    assert result.ok
    assert result.data["summary"]["tests_executed"] is False
    assert result.data["summary"]["receipts_total"] == 0
