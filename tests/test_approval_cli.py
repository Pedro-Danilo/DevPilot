from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from devpilot_core import cli
from devpilot_core.approval import ApprovalRequest
from devpilot_core.store import LocalStore


def _payload(capsys: pytest.CaptureFixture[str]) -> dict:
    return json.loads(capsys.readouterr().out)


def _future(minutes: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def test_approval_request_list_show_approve_and_revoke_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)

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
        "Validar cambios locales",
        "--actor",
        "owner",
        "--scope",
        '{"profile":"unit","cwd":"."}',
        "--ttl-minutes",
        "30",
        "--json",
    ])
    request_payload = _payload(capsys)
    approval_id = request_payload["data"]["approval"]["approval_id"]

    list_exit = cli.main(["approval", "list", "--status", "requested", "--json"])
    list_payload = _payload(capsys)

    show_exit = cli.main(["approval", "show", approval_id, "--json"])
    show_payload = _payload(capsys)

    approve_exit = cli.main(["approval", "approve", approval_id, "--actor", "owner", "--reason", "Revisión OK", "--json"])
    approve_payload = _payload(capsys)

    revoke_exit = cli.main(["approval", "revoke", approval_id, "--actor", "owner", "--reason", "Ya no aplica", "--json"])
    revoke_payload = _payload(capsys)

    assert request_exit == 0
    assert request_payload["command"] == "approval request"
    assert request_payload["data"]["approval"]["status"] == "requested"
    assert request_payload["data"]["approval"]["scope"]["profile"] == "unit"
    assert list_exit == 0
    assert list_payload["data"]["summary"]["approvals_total"] == 1
    assert show_exit == 0
    assert show_payload["data"]["approval"]["approval_id"] == approval_id
    assert approve_exit == 0
    assert approve_payload["command"] == "approval approve"
    assert approve_payload["data"]["approval"]["status"] == "approved"
    assert revoke_exit == 0
    assert revoke_payload["command"] == "approval revoke"
    assert revoke_payload["data"]["approval"]["status"] == "revoked"


def test_approval_cli_blocks_approval_without_reason_or_expired_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    expired = ApprovalRequest(
        approval_id="APPROVAL-CLI-EXPIRED",
        subject="pytest",
        tool_id="tests.run",
        action="execute",
        actor="owner",
        reason="Created for expiry test.",
        scope={"profile": "unit"},
        expires_at=_future(1),
    ).to_record()
    LocalStore(tmp_path).create_approval(expired.to_dict())
    current = LocalStore(tmp_path).get_approval("APPROVAL-CLI-EXPIRED")
    assert current is not None
    old = (datetime.now(timezone.utc) - timedelta(minutes=10)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    LocalStore(tmp_path).update_approval({**current.to_dict(), "expires_at": old, "reason": current.reason})

    exit_code = cli.main([
        "approval",
        "approve",
        "APPROVAL-CLI-EXPIRED",
        "--actor",
        "owner",
        "--reason",
        "Too late",
        "--json",
    ])
    payload = _payload(capsys)

    assert exit_code == 2
    assert payload["command"] == "approval approve"
    assert any(finding["id"] == "APPROVAL_EXPIRED" for finding in payload["findings"])


def test_approval_cli_write_report_and_redacts_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main([
        "approval",
        "request",
        "--tool",
        "tests.run",
        "--action",
        "execute",
        "--subject",
        "pytest",
        "--reason",
        "token sk-1234567890abcdef",
        "--actor",
        "owner",
        "--json",
        "--write-report",
    ])
    captured = capsys.readouterr().out
    payload = json.loads(captured)

    assert exit_code == 0
    assert "sk-1234567890abcdef" not in captured
    assert payload["data"]["reports"]["json"] == "outputs/reports/approval_request.json"
    assert (tmp_path / "outputs" / "reports" / "approval_request.json").is_file()
    assert (tmp_path / "outputs" / "traces" / "events.jsonl").is_file()
