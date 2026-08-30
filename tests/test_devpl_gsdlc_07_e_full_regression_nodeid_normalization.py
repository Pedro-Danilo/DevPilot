from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.testing.full_regression import FullRegressionSessionManager, _normalize_nodeid_path_only
from devpilot_core.testing.full_regression_collect_plugin import _normalize_nodeid_path_only as plugin_normalize


def test_nodeid_normalization_preserves_param_escape_sequences() -> None:
    raw = r"tests\test_api_security.py::test_case[tab\tinside-control\x7f]"
    expected = r"tests/test_api_security.py::test_case[tab\tinside-control\x7f]"

    assert _normalize_nodeid_path_only(raw) == expected
    assert plugin_normalize(raw) == expected
    assert "tab/tinside" not in expected
    assert "control/x7f" not in expected


def test_full_session_can_reselect_param_ids_with_backslash_escapes(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    tests_dir = root / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_param_ids.py").write_text(
        "import pytest\n\n"
        "@pytest.mark.parametrize('value', ['tab\\tinside', 'control\\x7f'])\n"
        "def test_param(value):\n"
        "    assert value\n",
        encoding="utf-8",
    )

    runtime = tmp_path / "runtime"
    manager = FullRegressionSessionManager(root, runtime_root=runtime)
    collected = manager.collect(session_id="nodeid-normalization", targets=("tests/test_param_ids.py",), timeout_seconds=120)
    assert collected.ok, collected.message

    collection = json.loads((runtime / "nodeid-normalization" / "collection.json").read_text(encoding="utf-8"))
    nodeids = [item["nodeid"] for item in collection["nodes"]]
    assert len(nodeids) == 2
    assert any(r"tab\tinside" in nodeid for nodeid in nodeids)
    assert any(r"control\x7f" in nodeid for nodeid in nodeids)
    assert all("tab/tinside" not in nodeid and "control/x7f" not in nodeid for nodeid in nodeids)

    planned = manager.plan(session_id="nodeid-normalization", shard_size=10, shard_timeout_seconds=120)
    assert planned.ok, planned.message
    ran = manager.run(session_id="nodeid-normalization", execute=True, timeout_seconds=120)
    assert ran.ok, ran.message
    adjudicated = manager.adjudicate(session_id="nodeid-normalization")
    assert adjudicated.ok, adjudicated.message
    summary = adjudicated.data["summary"]
    assert summary["collection_total"] == 2
    assert summary["pass_total"] == 2
    assert summary["coverage_percent"] == 100.0
