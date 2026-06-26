from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

from devpilot_core import cli
from devpilot_core.runtime_state import RuntimeStateCleanupOptions, RuntimeStateCleanupPlanner
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _make_runtime_root(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / ".devpilot").mkdir()
    (root / ".devpilot" / "testing").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "src" / "devpilot_core").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "outputs" / "reports").mkdir(parents=True)
    (root / "outputs" / "traces").mkdir(parents=True)
    (root / ".pytest_cache" / "v").mkdir(parents=True)
    (root / "pkg" / "__pycache__").mkdir(parents=True)

    shutil.copy(ROOT / ".devpilot" / "runtime_state_policy.json", root / ".devpilot" / "runtime_state_policy.json")
    (root / ".devpilot" / "project_state.json").write_text('{"state":"source"}\n', encoding="utf-8")
    (root / ".devpilot" / "testing" / "test_contract_registry.json").write_text('{"contracts":[]}\n', encoding="utf-8")
    (root / "docs" / "design.md").write_text("# source\n", encoding="utf-8")
    (root / "src" / "devpilot_core" / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "tests" / "test_module.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (root / "outputs" / "reports" / "old_report.json").write_text("{}\n", encoding="utf-8")
    (root / "outputs" / "traces" / "old_events.jsonl").write_text('{"event":"x"}\n', encoding="utf-8")
    (root / ".pytest_cache" / "v" / "cache.txt").write_text("cache\n", encoding="utf-8")
    (root / "pkg" / "__pycache__" / "module.cpython-311.pyc").write_bytes(b"pyc")

    old = time.time() - 60 * 86400
    for rel in [
        "outputs/reports/old_report.json",
        "outputs/traces/old_events.jsonl",
        ".pytest_cache/v/cache.txt",
        "pkg/__pycache__/module.cpython-311.pyc",
    ]:
        os.utime(root / rel, (old, old))
    return root


def test_runtime_state_cleanup_plan_classifies_safe_approval_and_never_delete(tmp_path: Path) -> None:
    root = _make_runtime_root(tmp_path)

    result = RuntimeStateCleanupPlanner(root).run()

    assert result.ok is True, result.to_dict()
    plan = result.data["cleanup_plan"]
    summary = result.data["summary"]
    assert result.command == "runtime-state cleanup-plan"
    assert summary["created_by"] == "POST-H-008-C"
    assert summary["dry_run"] is True
    assert summary["execute_requested"] is False
    assert summary["cleanup_execution_enabled"] is False
    assert summary["source_of_truth_never_delete"] is True
    assert summary["safe_cleanup_total"] >= 2
    assert summary["requires_approval_total"] >= 1
    assert summary["never_delete_total"] >= 3

    safe_paths = {item["path"] for item in plan["groups"]["safe_cleanup"]}
    approval_paths = {item["path"] for item in plan["groups"]["requires_approval"]}
    never_paths = {item["path"] for item in plan["groups"]["never_delete"]}
    assert "outputs/reports/old_report.json" in safe_paths
    assert ".pytest_cache/v/cache.txt" in safe_paths
    assert "outputs/traces/old_events.jsonl" in approval_paths
    assert "src/devpilot_core/module.py" in never_paths
    assert "docs/design.md" in never_paths
    assert ".devpilot/runtime_state_policy.json" in never_paths
    assert all(not item["source_of_truth"] for item in plan["groups"]["safe_cleanup"])


def test_runtime_state_cleanup_plan_write_report_matches_schema(monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = RuntimeStateCleanupPlanner(ROOT, RuntimeStateCleanupOptions(write_report=True)).run()

    assert result.ok is True, result.to_dict()
    reports = result.data["reports"]
    assert reports["json"] == "outputs/reports/runtime_state_cleanup_plan.json"
    assert reports["markdown"] == "outputs/reports/runtime_state_cleanup_plan.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()

    payload = json.loads((ROOT / reports["json"]).read_text(encoding="utf-8"))
    assert payload["created_by"] == "POST-H-008-C"
    assert payload["summary"]["reports_written"] is True
    assert "Runtime state cleanup plan" in (ROOT / reports["markdown"]).read_text(encoding="utf-8")

    schema_result = SchemaValidator(ROOT).validate(schema="RuntimeStateCleanupPlan", instance=reports["json"])
    assert schema_result.ok is True, schema_result.to_dict()


def test_runtime_state_cleanup_cli_dry_run_is_default_and_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    trace_path = ROOT / "outputs" / "traces" / "events.jsonl"
    before = (trace_path.exists(), trace_path.stat().st_size if trace_path.exists() else 0)

    exit_code = cli.main(["runtime-state", "cleanup", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "runtime-state cleanup-plan"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["dry_run"] is True
    assert payload["data"]["summary"]["execute_requested"] is False
    assert payload["data"]["summary"]["destructive_cleanup_performed"] is False
    after = (trace_path.exists(), trace_path.stat().st_size if trace_path.exists() else 0)
    assert after == before


def test_runtime_state_cleanup_execute_requires_confirmation(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["runtime-state", "cleanup", "--execute", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["data"]["summary"]["execution_blocked"] is True
    assert payload["data"]["summary"]["deletions_performed_total"] == 0
    assert any(finding["id"] == "RUNTIME_STATE_CLEANUP_CONFIRMATION_REQUIRED" for finding in payload["findings"])


def test_runtime_state_cleanup_execute_deletes_only_safe_cleanup(tmp_path: Path) -> None:
    root = _make_runtime_root(tmp_path)
    result = RuntimeStateCleanupPlanner(
        root,
        RuntimeStateCleanupOptions(execute=True, confirm_cleanup=True),
    ).run()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    assert summary["cleanup_execution_enabled"] is True
    assert summary["deletions_performed_total"] >= 2
    assert not (root / "outputs" / "reports" / "old_report.json").exists()
    assert not (root / ".pytest_cache" / "v" / "cache.txt").exists()
    assert (root / "outputs" / "traces" / "old_events.jsonl").exists()
    assert (root / "src" / "devpilot_core" / "module.py").exists()
    assert (root / "docs" / "design.md").exists()
