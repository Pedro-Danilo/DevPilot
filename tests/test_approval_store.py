from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from devpilot_core.approval import ApprovalDecision, ApprovalRequest, ApprovalStatus, ApprovalStore
from devpilot_core.cli_models import ExitCode
from devpilot_core.store import LocalStore


def future_iso(minutes: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def approval_request(**overrides: object) -> ApprovalRequest:
    payload = {
        "subject": "pytest unit suite",
        "tool_id": "tests.run",
        "action": "execute",
        "actor": "owner",
        "reason": "Validate local changes before controlled execution.",
        "scope": {"profile": "unit", "cwd": "."},
        "expires_at": future_iso(),
        "metadata": {"test": True},
    }
    payload.update(overrides)
    return ApprovalRequest(**payload)  # type: ignore[arg-type]


def test_approval_models_are_json_serializable() -> None:
    request = approval_request()
    record = request.to_record(approval_id="APPROVAL-TEST-001")
    decision = ApprovalDecision(
        approval_id=record.approval_id,
        status=ApprovalStatus.APPROVED.value,
        actor="owner",
        reason="Reviewed and approved.",
    )

    assert request.validate() == []
    assert record.validate() == []
    assert decision.validate() == []
    assert record.to_dict()["approval_id"] == "APPROVAL-TEST-001"
    assert record.to_dict()["scope"] == {"profile": "unit", "cwd": "."}


def test_approval_request_requires_scope_and_expiration() -> None:
    no_scope = approval_request(scope={})
    findings = no_scope.validate()
    assert any(finding.id == "APPROVAL_SCOPE_REQUIRED" for finding in findings)

    expired = approval_request(expires_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    findings = expired.validate()
    assert any(finding.id == "APPROVAL_EXPIRY_IN_PAST" for finding in findings)


def test_local_store_initializes_approval_operational_schema(tmp_path: Path) -> None:
    store = LocalStore(tmp_path)
    result = store.initialize()

    assert result.ok is True
    status = store.status()
    assert status.data["summary"]["schema_version"] == "0002_approval_operational_v1"
    assert "approvals" in status.data["tables"]


def test_approval_store_creates_lists_and_returns_idempotent_record(tmp_path: Path) -> None:
    store = ApprovalStore(tmp_path)
    request = approval_request(approval_id="APPROVAL-IDEMPOTENT-001")

    first = store.request(request)
    second = store.request(request)
    listed = store.list(status=ApprovalStatus.REQUESTED.value)

    assert first.ok is True
    assert first.data["summary"]["created"] is True
    assert second.ok is True
    assert second.data["summary"]["created"] is False
    assert second.findings[0].id == "APPROVAL_REQUEST_IDEMPOTENT"
    assert listed.data["summary"]["approvals_total"] == 1
    assert listed.data["approvals"][0]["approval_id"] == "APPROVAL-IDEMPOTENT-001"
    assert listed.data["approvals"][0]["scope"] == {"profile": "unit", "cwd": "."}


def test_approval_store_transitions_once_and_blocks_overwrite(tmp_path: Path) -> None:
    store = ApprovalStore(tmp_path)
    created = store.request(approval_request(approval_id="APPROVAL-TRANSITION-001"))
    assert created.ok

    approved = store.decide(
        ApprovalDecision(
            approval_id="APPROVAL-TRANSITION-001",
            status=ApprovalStatus.APPROVED.value,
            actor="owner",
            reason="Scope reviewed.",
        )
    )
    denied_after_approved = store.decide(
        ApprovalDecision(
            approval_id="APPROVAL-TRANSITION-001",
            status=ApprovalStatus.DENIED.value,
            actor="owner",
            reason="Attempted overwrite.",
        )
    )

    assert approved.ok is True
    assert approved.data["approval"]["status"] == "approved"
    assert approved.data["approval"]["decided_by"] == "owner"
    assert denied_after_approved.ok is False
    assert denied_after_approved.exit_code == ExitCode.BLOCK
    assert any(finding.id == "APPROVAL_TRANSITION_INVALID" for finding in denied_after_approved.findings)


def test_approval_store_blocks_expired_transition(tmp_path: Path) -> None:
    store = ApprovalStore(tmp_path)
    expired_at = (datetime.now(timezone.utc) + timedelta(seconds=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    # Store the record directly through LocalStore to simulate old requested data
    # that expires before a future CLI approval attempt.
    record = approval_request(approval_id="APPROVAL-EXPIRED-001", expires_at=expired_at).to_record()
    created, _ = LocalStore(tmp_path).create_approval(record.to_dict())
    assert created is True

    # Force expiration deterministically by updating the raw row.
    old = (datetime.now(timezone.utc) - timedelta(minutes=5)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    existing = LocalStore(tmp_path).get_approval("APPROVAL-EXPIRED-001")
    assert existing is not None
    expired_record = {
        **existing.to_dict(),
        "status": ApprovalStatus.REQUESTED.value,
        "expires_at": old,
        "reason": existing.reason,
    }
    LocalStore(tmp_path).update_approval(expired_record)

    approved = store.decide(
        ApprovalDecision(
            approval_id="APPROVAL-EXPIRED-001",
            status=ApprovalStatus.APPROVED.value,
            actor="owner",
            reason="Too late.",
        )
    )

    assert approved.ok is False
    assert approved.exit_code == ExitCode.BLOCK
    assert any(finding.id == "APPROVAL_EXPIRED" for finding in approved.findings)


def test_old_approval_schema_is_migrated_without_dropping_rows(tmp_path: Path) -> None:
    db = tmp_path / ".devpilot" / "devpilot.db"
    db.parent.mkdir(parents=True)
    import sqlite3

    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            CREATE TABLE approvals (
                approval_id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                subject TEXT,
                status TEXT NOT NULL,
                requested_at TEXT NOT NULL,
                approved_at TEXT,
                approver TEXT,
                reason TEXT,
                metadata_json TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        conn.execute(
            "INSERT INTO approvals (approval_id, action, subject, status, requested_at, reason) VALUES (?, ?, ?, ?, ?, ?)",
            ("APPROVAL-LEGACY-001", "execute", "legacy", "requested", future_iso(), "legacy row"),
        )
        conn.commit()

    status = LocalStore(tmp_path).status()
    migrated = LocalStore(tmp_path).get_approval("APPROVAL-LEGACY-001")

    assert status.ok is True
    assert migrated is not None
    assert migrated.approval_id == "APPROVAL-LEGACY-001"
    assert migrated.action == "execute"
    assert migrated.scope == {}
