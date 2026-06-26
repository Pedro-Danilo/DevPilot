from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from devpilot_core import cli
from devpilot_core.quality import QualityGate, QualityGateOptions
from devpilot_core.runtime_state import RuntimeStateHygieneGate, RuntimeStateHygieneOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _copy_policy(root: Path) -> None:
    (root / ".devpilot").mkdir(parents=True, exist_ok=True)
    policy = _read_json(".devpilot/runtime_state_policy.json")
    (root / ".devpilot" / "runtime_state_policy.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")


def _git_available() -> bool:
    return subprocess.run(["git", "--version"], capture_output=True, text=True, check=False).returncode == 0


def _git_init_commit(root: Path, paths: list[str]) -> None:
    if not _git_available():
        pytest.skip("git is not available in this environment")
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "devpilot.local@example.test"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "DevPilot Local"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", *paths], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=root, check=True, capture_output=True, text=True)


def test_runtime_state_hygiene_gate_passes_on_current_clean_source_archive_plan(monkeypatch) -> None:
    monkeypatch.chdir(ROOT)

    result = RuntimeStateHygieneGate(ROOT).run()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    hygiene = result.data["hygiene"]
    assert result.command == "runtime-state hygiene"
    assert summary["created_by"] == "POST-H-008-E"
    assert summary["read_only"] is True
    assert summary["dry_run"] is True
    assert summary["source_archive_plan_checked"] is True
    assert summary["source_archive_plan_clean"] is True
    assert summary["runtime_state_hygiene_passed"] is True
    assert summary["forbidden_archive_entries_total"] == 0
    assert summary["runtime_archive_entries_total"] == 0
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert hygiene["source_archive_plan"]["included_files_total"] > 0
    assert "outputs/" in hygiene["must_exclude"]
    assert ".devpilot/devpilot.db" in hygiene["must_exclude"]
    assert ".devpilot/agent_sessions/" in hygiene["must_exclude"]


def test_runtime_state_hygiene_write_report_matches_schema(monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = RuntimeStateHygieneGate(ROOT, RuntimeStateHygieneOptions(write_report=True)).run()

    assert result.ok is True, result.to_dict()
    reports = result.data["reports"]
    assert reports["json"] == "outputs/reports/runtime_state_hygiene_report.json"
    assert reports["markdown"] == "outputs/reports/runtime_state_hygiene_report.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()

    payload = _read_json(reports["json"])
    assert payload["created_by"] == "POST-H-008-E"
    assert payload["summary"]["reports_written"] is True
    assert payload["summary"]["release_archive_clean"] is True
    assert "Runtime state hygiene report" in (ROOT / reports["markdown"]).read_text(encoding="utf-8")

    schema_result = SchemaValidator(ROOT).validate(schema="RuntimeStateHygieneReport", instance=reports["json"])
    assert schema_result.ok is True, schema_result.to_dict()
    assert schema_result.data["summary"]["valid"] is True


def test_runtime_state_hygiene_cli_json_is_read_only_and_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    trace_path = ROOT / "outputs" / "traces" / "events.jsonl"
    before_exists = trace_path.exists()
    before_size = trace_path.stat().st_size if before_exists else 0

    exit_code = cli.main(["runtime-state", "hygiene", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "runtime-state hygiene"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["read_only"] is True
    assert payload["data"]["summary"]["reports_written"] is False
    assert payload["data"]["summary"]["destructive_cleanup_performed"] is False
    after_exists = trace_path.exists()
    after_size = trace_path.stat().st_size if after_exists else 0
    assert (after_exists, after_size) == (before_exists, before_size)


def test_runtime_state_hygiene_detects_versioned_runtime_artifacts_and_dirty_git_archive(tmp_path: Path) -> None:
    root = tmp_path
    _copy_policy(root)
    (root / "README.md").write_text("# fixture\n", encoding="utf-8")
    (root / "outputs" / "reports").mkdir(parents=True)
    (root / "outputs" / "reports" / "leaked.json").write_text("{}\n", encoding="utf-8")
    _git_init_commit(root, ["README.md", ".devpilot/runtime_state_policy.json", "outputs/reports/leaked.json"])

    result = RuntimeStateHygieneGate(root).run()

    assert result.ok is False
    assert int(result.exit_code) == 2
    summary = result.data["summary"]
    assert summary["versioned_runtime_artifacts_total"] == 1
    assert summary["git_archive_available"] is True
    assert summary["git_archive_checked"] is True
    assert summary["git_archive_clean"] is False
    assert summary["forbidden_archive_entries_total"] >= 1
    assert any(finding.id in {"RUNTIME_STATE_VERSIONED_ARTIFACTS_BLOCK", "GIT_ARCHIVE_FORBIDDEN_ENTRIES_BLOCK"} for finding in result.findings)


def test_runtime_state_hygiene_git_archive_clean_fixture_passes(tmp_path: Path) -> None:
    root = tmp_path
    _copy_policy(root)
    (root / "README.md").write_text("# fixture\n", encoding="utf-8")
    _git_init_commit(root, ["README.md", ".devpilot/runtime_state_policy.json"])

    result = RuntimeStateHygieneGate(root).run()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    assert summary["git_archive_available"] is True
    assert summary["git_archive_checked"] is True
    assert summary["git_archive_clean"] is True
    assert summary["release_archive_clean"] is True


def test_runtime_state_hygiene_quality_gate_hardening_includes_subgate(monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = QualityGate(ROOT, options=QualityGateOptions(profile="hardening")).run()

    assert result.ok is True, result.to_dict()
    subgate_ids = {item["id"] for item in result.data["subgates"]}
    assert "runtime-state-hygiene" in subgate_ids
    subgate = next(item for item in result.data["subgates"] if item["id"] == "runtime-state-hygiene")
    assert subgate["ok"] is True
    assert subgate["summary"]["runtime_state_hygiene_passed"] is True
