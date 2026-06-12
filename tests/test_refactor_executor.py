from __future__ import annotations

import json
from pathlib import Path

import pytest

from devpilot_core import cli
from devpilot_core.approval.service import ApprovalCliInput, ApprovalService
from devpilot_core.refactor import RefactorExecutor


def _project(root: Path) -> None:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='refactor-fixture'\n", encoding="utf-8")


def _write_smoke(root: Path) -> None:
    smoke = root / "tests" / "fixtures" / "smoke_pytest_project"
    smoke.mkdir(parents=True, exist_ok=True)
    (smoke / "test_smoke.py").write_text("def test_smoke():\n    assert True\n", encoding="utf-8")


def _write_target(root: Path, rel: str = "src/example.py") -> Path:
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("def sample():    \n    value = 1    \n    return value    \n", encoding="utf-8")
    return target


def _approve(root: Path, *, tool_id: str, subject: str) -> str:
    service = ApprovalService(root)
    requested = service.request(
        ApprovalCliInput(
            tool_id=tool_id,
            action="execute",
            subject=subject,
            actor="owner",
            reason="Approve controlled refactor sandbox test.",
            ttl_minutes=30,
        )
    )
    approval_id = requested.data["approval"]["approval_id"]
    approved = service.approve(approval_id, actor="owner", reason="Approved controlled refactor sandbox test.")
    assert approved.ok
    return approval_id


def test_refactor_sandbox_requires_scoped_approval(tmp_path: Path) -> None:
    _project(tmp_path)
    _write_target(tmp_path)

    result = RefactorExecutor(tmp_path).sandbox(target="src/example.py", plan_id="RF-001", approval_id=None)

    assert result.ok is False
    assert int(result.exit_code) == 2
    assert result.data["summary"]["sandbox_created"] is False
    assert any(finding.id == "APPROVAL_REQUIRED_MISSING" for finding in result.findings)


def test_refactor_sandbox_changes_only_sandbox_and_creates_changeset_and_rollback(tmp_path: Path) -> None:
    _project(tmp_path)
    target = _write_target(tmp_path)
    before = target.read_text(encoding="utf-8")
    approval_id = _approve(tmp_path, tool_id="refactor.sandbox", subject="refactor:RF-001:src/example.py")

    result = RefactorExecutor(tmp_path).sandbox(target="src/example.py", plan_id="RF-001", approval_id=approval_id)

    after = target.read_text(encoding="utf-8")
    assert result.ok is True
    assert before == after
    summary = result.data["summary"]
    assert summary["productive_workspace_unchanged"] is True
    assert summary["changed_files"] == 1
    assert summary["changeset_files"] == 1
    assert summary["rollback_plan_created"] is True
    assert summary["rollback_id"].startswith("rollback-")
    sandbox_workspace = tmp_path / summary["sandbox_workspace"]
    sandbox_text = (sandbox_workspace / "src/example.py").read_text(encoding="utf-8")
    assert "    \n" not in sandbox_text
    assert result.data["changeset"]["files"][0]["path"] == "src/example.py"
    assert result.data["changeset"]["files"][0]["before_sha256"] != result.data["changeset"]["files"][0]["after_sha256"]
    rollback_path = tmp_path / ".devpilot" / "rollback" / "points" / f"{summary['rollback_id']}.json"
    assert rollback_path.exists()


def test_refactor_sandbox_unknown_plan_id_blocks(tmp_path: Path) -> None:
    _project(tmp_path)
    _write_target(tmp_path)

    result = RefactorExecutor(tmp_path).sandbox(target="src/example.py", plan_id="RF-999", approval_id="APPROVAL-NOPE")

    assert result.ok is False
    assert int(result.exit_code) == 2
    assert any(finding.id == "REFACTOR_SANDBOX_PLAN_ID_INVALID" for finding in result.findings)


def test_refactor_sandbox_cleanup_removes_runtime_directory(tmp_path: Path) -> None:
    _project(tmp_path)
    _write_target(tmp_path)
    approval_id = _approve(tmp_path, tool_id="refactor.sandbox", subject="refactor:RF-001:src/example.py")

    result = RefactorExecutor(tmp_path).sandbox(target="src/example.py", plan_id="RF-001", approval_id=approval_id, cleanup=True)

    assert result.ok is True
    assert result.data["summary"]["cleanup_removed"] is True
    assert not (tmp_path / result.data["summary"]["sandbox_workspace"]).exists()


def test_refactor_sandbox_run_tests_requires_separate_tests_approval(tmp_path: Path) -> None:
    _project(tmp_path)
    _write_target(tmp_path)
    approval_id = _approve(tmp_path, tool_id="refactor.sandbox", subject="refactor:RF-001:src/example.py")

    result = RefactorExecutor(tmp_path).sandbox(target="src/example.py", plan_id="RF-001", approval_id=approval_id, run_tests=True)

    assert result.ok is False
    assert int(result.exit_code) == 2
    assert result.data["summary"]["tests_executed"] is False
    assert any(finding.id == "APPROVAL_REQUIRED_MISSING" for finding in result.findings)



def test_refactor_sandbox_can_run_approved_sandbox_tests(tmp_path: Path) -> None:
    _project(tmp_path)
    _write_smoke(tmp_path)
    _write_target(tmp_path)
    refactor_approval = _approve(tmp_path, tool_id="refactor.sandbox", subject="refactor:RF-001:src/example.py")
    tests_approval = _approve(tmp_path, tool_id="tests.run", subject="sandbox:smoke")

    result = RefactorExecutor(tmp_path).sandbox(
        target="src/example.py",
        plan_id="RF-001",
        approval_id=refactor_approval,
        run_tests=True,
        tests_approval_id=tests_approval,
    )

    assert result.ok is True
    assert result.data["summary"]["tests_executed"] is True
    assert result.data["summary"]["tests_ok"] is True
    assert any(finding.id == "REFACTOR_SANDBOX_TESTS_PASS" for finding in result.findings)

def test_refactor_sandbox_cli_json_and_write_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _project(tmp_path)
    _write_target(tmp_path)
    monkeypatch.chdir(tmp_path)
    approval_id = _approve(tmp_path, tool_id="refactor.sandbox", subject="refactor:RF-001:src/example.py")

    exit_code = cli.main([
        "refactor",
        "sandbox",
        "--target",
        "src/example.py",
        "--plan-id",
        "RF-001",
        "--approval-id",
        approval_id,
        "--json",
        "--write-report",
        "--cleanup",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "refactor sandbox"
    assert payload["data"]["summary"]["productive_workspace_unchanged"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/refactor_sandbox.json"
    assert (tmp_path / "outputs" / "reports" / "refactor_sandbox.json").exists()
