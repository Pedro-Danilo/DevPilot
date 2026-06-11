from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from devpilot_core import cli
from devpilot_core.approval import ApprovalRequest
from devpilot_core.approval.policy import ApprovalPolicyChecker, ApprovalPolicyInput
from devpilot_core.cli_models import ExitCode
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.store import LocalStore


def _payload(capsys: pytest.CaptureFixture[str]) -> dict:
    return json.loads(capsys.readouterr().out)


def _future(minutes: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _project(root: Path) -> None:
    (root / "docs").mkdir(exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")


def _approved_record(root: Path, *, approval_id: str = "APPROVAL-POLICY-VALID", tool_id: str = "tests.run", action: str = "execute", subject: str = "pytest") -> str:
    record = ApprovalRequest(
        approval_id=approval_id,
        subject=subject,
        tool_id=tool_id,
        action=action,
        actor="owner",
        reason="Approve scoped policy simulation.",
        scope={"tool_id": tool_id, "action": action, "subject": subject},
        expires_at=_future(30),
    ).to_record(approval_id=approval_id)
    created, _ = LocalStore(root).create_approval(record.to_dict())
    assert created is True
    current = LocalStore(root).get_approval(approval_id)
    assert current is not None
    LocalStore(root).update_approval({**current.to_dict(), "status": "approved", "decision_at": _future(10), "decided_by": "owner"})
    return approval_id


def test_policy_engine_blocks_approval_gated_action_without_approval(tmp_path: Path) -> None:
    _project(tmp_path)
    engine = PolicyEngine(tmp_path)

    result = engine.evaluate(PolicyRequest(action="execute", path=".", tool_id="tests.run", subject="pytest"))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    finding_ids = {finding.id for finding in result.findings}
    assert "APPROVAL_REQUIRED_MISSING" in finding_ids
    assert "POLICY_DANGEROUS_ACTION_BLOCKED" in finding_ids


def test_policy_engine_allows_scoped_approved_request_without_bypassing_other_guards(tmp_path: Path) -> None:
    _project(tmp_path)
    approval_id = _approved_record(tmp_path)
    engine = PolicyEngine(tmp_path)

    result = engine.evaluate(
        PolicyRequest(action="execute", path=".", tool_id="tests.run", subject="pytest", approval_id=approval_id)
    )

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["approval_valid"] is True
    decision_ids = {decision["rule_id"] for decision in result.data["decisions"]}
    assert "APPROVAL_VALID" in decision_ids
    assert "PATHGUARD_PASS" in decision_ids
    assert "POLICY_DANGEROUS_ACTION_BLOCKED" not in decision_ids


def test_approval_policy_checker_blocks_wrong_scope_and_expired_approval(tmp_path: Path) -> None:
    _project(tmp_path)
    approval_id = _approved_record(tmp_path, subject="unit")
    checker = ApprovalPolicyChecker(tmp_path)

    wrong_scope = checker.evaluate(ApprovalPolicyInput(action="execute", tool_id="tests.run", subject="pytest", approval_id=approval_id))

    assert wrong_scope.effect.value == "block"
    assert wrong_scope.rule_id == "APPROVAL_SCOPE_MISMATCH"

    current = LocalStore(tmp_path).get_approval(approval_id)
    assert current is not None
    LocalStore(tmp_path).update_approval({**current.to_dict(), "expires_at": "2000-01-01T00:00:00Z"})
    expired = checker.evaluate(ApprovalPolicyInput(action="execute", tool_id="tests.run", subject="unit", approval_id=approval_id))

    assert expired.effect.value == "block"
    assert expired.rule_id == "APPROVAL_EXPIRED"


def test_policy_simulate_cli_with_valid_approval_and_write_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    _project(tmp_path)

    request_exit = cli.main([
        "approval",
        "request",
        "--tool",
        "tests.run",
        "--action",
        "execute",
        "--subject",
        "pytest",
        "--reason",
        "Run controlled local tests",
        "--actor",
        "owner",
        "--json",
    ])
    request_payload = _payload(capsys)
    approval_id = request_payload["data"]["approval"]["approval_id"]
    approve_exit = cli.main(["approval", "approve", approval_id, "--actor", "owner", "--reason", "OK", "--json"])
    _payload(capsys)
    simulate_exit = cli.main([
        "policy",
        "simulate",
        "--tool",
        "tests.run",
        "--action",
        "execute",
        "--subject",
        "pytest",
        "--approval-id",
        approval_id,
        "--json",
        "--write-report",
    ])
    simulate_payload = _payload(capsys)

    assert request_exit == 0
    assert approve_exit == 0
    assert simulate_exit == 0
    assert simulate_payload["command"] == "policy simulate"
    assert simulate_payload["data"]["summary"]["approval_valid"] is True
    assert simulate_payload["data"]["reports"]["json"] == "outputs/reports/policy_simulate.json"


def test_policy_check_cli_blocks_missing_approval_for_execute(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    _project(tmp_path)

    exit_code = cli.main(["policy", "check", "execute", "--path", ".", "--tool", "tests.run", "--subject", "pytest", "--json"])
    payload = _payload(capsys)

    assert exit_code == 2
    assert payload["command"] == "policy check"
    assert any(finding["id"] == "APPROVAL_REQUIRED_MISSING" for finding in payload["findings"])
