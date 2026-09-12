from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from devpilot_core.recovery import RecoveryStateError, ResumeService, WorkspaceLockService


class _Context:
    configured = True
    valid = True
    active_workspace_id = "devpilot-local"

    def __init__(self, root: Path) -> None:
        self.active_workspace_root = root


class _Resolver:
    def __init__(self, root: Path) -> None:
        self.context = _Context(root)

    def resolve(self) -> _Context:
        return self.context


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True)
    return completed.stdout.strip()


def _workspace(tmp_path: Path) -> tuple[Path, Path, _Resolver]:
    platform = tmp_path / "platform"
    workspace = tmp_path / "workspace" / "devpilot-local"
    platform.mkdir(parents=True)
    workspace.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(workspace)], check=True)
    _git(workspace, "config", "user.email", "gsdlc12a@example.invalid")
    _git(workspace, "config", "user.name", "GSDLC 12-A")
    (workspace / "draft.txt").write_text("draft\n", encoding="utf-8")
    _git(workspace, "add", "draft.txt")
    _git(workspace, "commit", "-q", "-m", "initial")
    return platform, workspace, _Resolver(workspace)


def _iso(delta_seconds: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=delta_seconds)).isoformat().replace("+00:00", "Z")


def test_12_a_checkpoint_survives_session_restart_without_browser_authority_or_source_mutation(tmp_path: Path) -> None:
    platform, workspace, resolver = _workspace(tmp_path)
    before = _git(workspace, "status", "--porcelain")
    service = ResumeService(platform, context_resolver=resolver)
    checkpoint = service.checkpoint(
        actor="owner",
        session_created_at="2026-09-12T10:00:00Z",
        rotation_counter=0,
        draft_refs=["draft:story-12a"],
        pending_work=[
            {"work_id": "draft.review", "kind": "draft", "safe_to_resume": True, "sensitive": False},
            {"work_id": "workspace.sensitive.demo", "kind": "execute", "safe_to_resume": True, "sensitive": True},
        ],
        evidence_refs=["evidence:checkpoint-before-restart"],
        recovery_reason="browser-restart-acceptance",
    )
    assert checkpoint["schema_version"] == "1.0"
    assert checkpoint["browser_storage_authority"] is False
    assert checkpoint["runtime_db_snapshot_used"] is False
    assert checkpoint["source_mutations_performed"] is False
    assert _git(workspace, "status", "--porcelain") == before

    recovered = service.status(actor="owner", session_created_at="2026-09-12T10:05:00Z", rotation_counter=1)
    assert recovered["session_changed"] is True
    by_id = {row["work_id"]: row for row in recovered["pending_work"]}
    assert by_id["draft.review"]["recovery_state"] == "SAFE_TO_RESUME"
    assert by_id["draft.review"]["auto_execute"] is False
    assert by_id["workspace.sensitive.demo"]["recovery_state"] == "REVALIDATION_REQUIRED"
    assert by_id["workspace.sensitive.demo"]["auto_execute"] is False
    assert recovered["browser_storage_authority"] is False
    assert recovered["runtime_db_snapshot_used"] is False

    checkpoint_path = platform / "outputs" / "workspaces" / "devpilot-local" / "recovery" / "checkpoint.json"
    assert checkpoint_path.is_file()
    assert not list(platform.rglob("auth.db*"))
    assert not list(platform.rglob("devpilot.db*"))


def test_12_a_source_drift_and_expired_approval_abort_incomplete_work(tmp_path: Path) -> None:
    platform, workspace, resolver = _workspace(tmp_path)
    service = ResumeService(platform, context_resolver=resolver)
    service.checkpoint(
        actor="owner",
        session_created_at="2026-09-12T10:00:00Z",
        rotation_counter=0,
        pending_work=[
            {
                "work_id": "approval.bound.execute",
                "kind": "execute",
                "sensitive": True,
                "approval_id": "APPROVAL-12A",
                "approval_actor": "owner",
                "approval_expires_at": _iso(-30),
            }
        ],
    )
    expired = service.status(actor="owner", session_created_at="2026-09-12T10:01:00Z", rotation_counter=0)
    assert expired["pending_work"][0]["recovery_state"] == "ABORTED_REQUIRES_REPLAN"
    assert expired["pending_work"][0]["reason_code"] == "APPROVAL_EXPIRED"

    (workspace / "draft.txt").write_text("changed\n", encoding="utf-8")
    _git(workspace, "add", "draft.txt")
    _git(workspace, "commit", "-q", "-m", "external change")
    drifted = service.status(actor="owner", session_created_at="2026-09-12T10:01:00Z", rotation_counter=0)
    assert drifted["git_match"] is False
    assert drifted["pending_work"][0]["recovery_state"] == "ABORTED_REQUIRES_REPLAN"
    assert drifted["pending_work"][0]["reason_code"] == "SOURCE_IDENTITY_CHANGED"


def test_12_a_secret_like_material_is_rejected_from_durable_checkpoint(tmp_path: Path) -> None:
    platform, _workspace_root, resolver = _workspace(tmp_path)
    service = ResumeService(platform, context_resolver=resolver)
    with pytest.raises(RecoveryStateError):
        service.checkpoint(
            actor="owner",
            session_created_at="2026-09-12T10:00:00Z",
            rotation_counter=0,
            pending_work=[{"work_id": "safe.demo", "approval_actor": "sk-test-secret-value"}],
        )


def test_12_a_lock_ownership_duplicate_negative_and_explicit_stale_recovery(tmp_path: Path) -> None:
    platform, _workspace_root, resolver = _workspace(tmp_path)
    locks = WorkspaceLockService(platform, context_resolver=resolver)
    first = locks.acquire(
        action_id="workspace.sensitive.demo",
        actor="owner",
        session_created_at="2026-09-12T10:00:00Z",
        rotation_counter=0,
        sensitive=True,
        ttl_seconds=300,
    )
    assert first["owned_by_current_session"] is True
    assert first["reused"] is False
    heartbeat = locks.acquire(
        action_id="workspace.sensitive.demo",
        actor="owner",
        session_created_at="2026-09-12T10:00:00Z",
        rotation_counter=0,
        sensitive=True,
        ttl_seconds=300,
    )
    assert heartbeat["reused"] is True

    with pytest.raises(RecoveryStateError):
        locks.acquire(
            action_id="workspace.sensitive.demo",
            actor="owner",
            session_created_at="2026-09-12T11:00:00Z",
            rotation_counter=1,
            sensitive=True,
            ttl_seconds=300,
        )

    lock_files = list((platform / "outputs/workspaces/devpilot-local/recovery/locks").glob("*.json"))
    assert len(lock_files) == 1
    payload = json.loads(lock_files[0].read_text(encoding="utf-8"))
    payload["expires_at_utc"] = "2000-01-01T00:00:00Z"
    lock_files[0].write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(RecoveryStateError):
        locks.acquire(
            action_id="workspace.sensitive.demo",
            actor="owner",
            session_created_at="2026-09-12T11:00:00Z",
            rotation_counter=1,
            sensitive=True,
            ttl_seconds=300,
        )
    with pytest.raises(RecoveryStateError):
        locks.recover_stale(action_id="workspace.sensitive.demo", actor="owner", roles=["owner"], confirmation="NO")
    recovered = locks.recover_stale(
        action_id="workspace.sensitive.demo",
        actor="owner",
        roles=["owner"],
        confirmation="RECOVER_STALE_LOCK",
    )
    assert recovered["recovered"] is True
    assert recovered["requires_operation_revalidation"] is True
    assert recovered["auto_execute"] is False
    assert not lock_files[0].exists()
