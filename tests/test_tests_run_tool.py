from __future__ import annotations

import json
from pathlib import Path

import pytest

from devpilot_core import cli
from devpilot_core.approval.service import ApprovalCliInput, ApprovalService
from devpilot_core.testing import TestsRunTool


def _write_profiles(root: Path, *, profile_args: list[str] | None = None, timeout_seconds: int = 30) -> None:
    fixture_dir = root / "tests" / "mini"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    (fixture_dir / "test_sample.py").write_text("def test_sample():\n    assert True\n", encoding="utf-8")
    profiles_dir = root / ".devpilot" / "testing"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "profiles": [
            {
                "profile_id": "smoke",
                "description": "Synthetic profile for tests.run unit tests.",
                "pytest_args": profile_args or ["--version"],
                "cwd": ".",
                "timeout_seconds": timeout_seconds,
            }
        ],
    }
    (profiles_dir / "test_profiles.json").write_text(json.dumps(payload), encoding="utf-8")


def _approved_tests_run_id(root: Path, *, subject: str = "smoke") -> str:
    service = ApprovalService(root)
    requested = service.request(
        ApprovalCliInput(
            tool_id="tests.run",
            action="execute",
            subject=subject,
            actor="owner",
            reason="Approve local controlled tests.",
            ttl_minutes=30,
        )
    )
    approval_id = requested.data["approval"]["approval_id"]
    approved = service.approve(approval_id, actor="owner", reason="Approved local controlled tests.")
    assert approved.ok
    return approval_id


def test_tests_run_blocks_missing_approval(tmp_path: Path) -> None:
    _write_profiles(tmp_path)

    result = TestsRunTool(tmp_path).run(profile_id="smoke", approval_id=None)

    assert result.exit_code == 2
    assert result.data["summary"]["executed"] is False
    assert result.data["summary"]["blocked_by_policy"] is True
    assert any(finding.id == "APPROVAL_REQUIRED_MISSING" for finding in result.findings)


def test_tests_run_executes_approved_profile(tmp_path: Path) -> None:
    _write_profiles(tmp_path)
    approval_id = _approved_tests_run_id(tmp_path)

    result = TestsRunTool(tmp_path).run(profile_id="smoke", approval_id=approval_id)

    assert result.ok is True
    assert result.exit_code == 0
    assert result.data["summary"]["profile"] == "smoke"
    assert result.data["summary"]["allowed_by_policy"] is True
    assert result.data["summary"]["returncode"] == 0
    assert result.data["execution"]["data"]["execution"]["command_id"] == "python.pytest"
    assert any(finding.id == "TESTS_RUN_PASS" for finding in result.findings)


def test_tests_run_blocks_unknown_profile(tmp_path: Path) -> None:
    _write_profiles(tmp_path)
    approval_id = _approved_tests_run_id(tmp_path)

    result = TestsRunTool(tmp_path).run(profile_id="unknown", approval_id=approval_id)

    assert result.ok is False
    assert result.exit_code == 2
    assert any(finding.id == "TESTS_RUN_UNKNOWN_PROFILE" for finding in result.findings)


def test_tests_run_blocks_wrong_approval_scope(tmp_path: Path) -> None:
    _write_profiles(tmp_path)
    wrong_approval_id = _approved_tests_run_id(tmp_path, subject="unit")

    result = TestsRunTool(tmp_path).run(profile_id="smoke", approval_id=wrong_approval_id)

    assert result.ok is False
    assert result.exit_code == 2
    assert any(finding.id == "APPROVAL_SCOPE_MISMATCH" for finding in result.findings)


def test_tests_run_timeout_is_captured(tmp_path: Path) -> None:
    _write_profiles(tmp_path, profile_args=["-q", "tests/mini", "--collect-only"], timeout_seconds=30)
    approval_id = _approved_tests_run_id(tmp_path)

    result = TestsRunTool(tmp_path).run(profile_id="smoke", approval_id=approval_id, timeout_seconds=999)

    assert result.ok is False
    assert result.exit_code == 2
    assert any(finding.id == "SAFE_SUBPROCESS_TIMEOUT_INVALID" for finding in result.findings)


def test_tests_run_cli_profiles_and_run_with_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    _write_profiles(tmp_path)

    profiles_exit = cli.main(["tests", "profiles", "--json"])
    profiles_payload = json.loads(capsys.readouterr().out)
    assert profiles_exit == 0
    assert profiles_payload["command"] == "tests profiles"

    approval_id = _approved_tests_run_id(tmp_path)
    run_exit = cli.main(["tests", "run", "--profile", "smoke", "--approval-id", approval_id, "--json", "--write-report"])
    run_payload = json.loads(capsys.readouterr().out)

    assert run_exit == 0
    assert run_payload["command"] == "tests run"
    assert run_payload["data"]["summary"]["returncode"] == 0
    assert run_payload["data"]["reports"]["json"] == "outputs/reports/tests_run_smoke.json"
    assert (tmp_path / "outputs" / "reports" / "tests_run_smoke.json").is_file()
    assert (tmp_path / "outputs" / "traces" / "events.jsonl").is_file()
