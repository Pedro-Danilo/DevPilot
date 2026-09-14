from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from devpilot_core.reconciliation import AdvancedWorkspaceReconciliationService, ReconciliationStateError
from devpilot_core.recovery import WorkspaceLockService


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


def _git(root: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=check)
    return completed.stdout.strip()


def _workspace(tmp_path: Path, *, autocrlf: bool = False) -> tuple[Path, Path, _Resolver, AdvancedWorkspaceReconciliationService]:
    platform = tmp_path / "platform"
    workspace = tmp_path / "workspace" / "devpilot-local"
    platform.mkdir(parents=True)
    workspace.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(workspace)], check=True)
    _git(workspace, "config", "user.email", "gsdlc12b@example.invalid")
    _git(workspace, "config", "user.name", "GSDLC 12-B")
    if autocrlf:
        _git(workspace, "config", "core.autocrlf", "true")
    (workspace / "tracked.txt").write_text("v1\n", encoding="utf-8")
    _git(workspace, "add", "tracked.txt")
    _git(workspace, "commit", "-q", "-m", "initial")
    resolver = _Resolver(workspace)
    service = AdvancedWorkspaceReconciliationService(platform, context_resolver=resolver)
    return platform, workspace, resolver, service


def _baseline(service: AdvancedWorkspaceReconciliationService) -> dict:
    dry = service.baseline(actor="owner", session_created_at="2026-09-12T20:00:00Z", rotation_counter=0, execute=False, confirmation="")
    assert dry["status"] == "DRY_RUN"
    return service.baseline(actor="owner", session_created_at="2026-09-12T20:00:00Z", rotation_counter=0, execute=True, confirmation="CAPTURE_RECONCILIATION_BASELINE")


def _inspect(service: AdvancedWorkspaceReconciliationService) -> dict:
    return service.inspect(actor="owner", session_created_at="2026-09-12T20:00:00Z", rotation_counter=0)


def test_12_b_missing_baseline_is_explicit_read_only_block(tmp_path: Path) -> None:
    _, _, _, service = _workspace(tmp_path)
    report = _inspect(service)
    assert report["classification"] == "READ_ONLY_BLOCK"
    assert report["reason_codes"] == ["RECONCILIATION_BASELINE_MISSING"]
    assert report["recommended_next_action"] == "RESTORE_REVIEWABLE_GIT_AUTHORITY"


def test_12_b_clean_baseline_is_no_conflict_and_metadata_only(tmp_path: Path) -> None:
    platform, workspace, _, service = _workspace(tmp_path)
    before = _git(workspace, "status", "--porcelain")
    result = _baseline(service)
    assert result["baseline_written"] is True
    assert _git(workspace, "status", "--porcelain") == before == ""
    report = _inspect(service)
    assert report["classification"] == "NO_CONFLICT"
    assert report["safety"]["source_mutations_performed"] is False
    assert report["safety"]["git_mutations_performed"] is False
    assert (platform / "outputs/workspaces/devpilot-local/reconciliation/baseline.json").is_file()


def test_12_b_external_modify_requires_revalidation_and_invalidates_authority(tmp_path: Path) -> None:
    _, workspace, _, service = _workspace(tmp_path)
    _baseline(service)
    (workspace / "tracked.txt").write_text("external\n", encoding="utf-8")
    report = _inspect(service)
    assert report["classification"] == "REVALIDATE"
    assert "EXTERNAL_WORKTREE_EDIT" in report["reason_codes"]
    assert {row["authority"] for row in report["authority_invalidations"]} == {"approval", "preimage", "plan"}
    assert all(row["auto_reuse"] is False for row in report["authority_invalidations"])


def test_12_b_rename_and_delete_require_manual_reconciliation(tmp_path: Path) -> None:
    _, workspace, _, service = _workspace(tmp_path)
    _baseline(service)
    _git(workspace, "mv", "tracked.txt", "renamed.txt")
    report = _inspect(service)
    assert report["classification"] == "MANUAL_RECONCILIATION_REQUIRED"
    assert report["snapshot"]["change_counts"]["RENAME"] == 1
    _git(workspace, "reset", "--", "renamed.txt", check=False)  # test fixture cleanup only; not product code
    # Recreate a clean fixture using a commit, then delete externally.
    _git(workspace, "add", "-A")
    _git(workspace, "commit", "-q", "-m", "rename")
    service.adopt(actor="owner", session_created_at="2026-09-12T20:00:00Z", rotation_counter=0, execute=True, confirmation="ADOPT_RECONCILIATION_BASELINE")
    (workspace / "renamed.txt").unlink()
    deleted = _inspect(service)
    assert deleted["classification"] == "MANUAL_RECONCILIATION_REQUIRED"
    assert deleted["snapshot"]["change_counts"]["DELETE"] == 1


def test_12_b_external_fast_forward_requires_revalidation(tmp_path: Path) -> None:
    _, workspace, _, service = _workspace(tmp_path)
    _baseline(service)
    (workspace / "tracked.txt").write_text("v2\n", encoding="utf-8")
    _git(workspace, "add", "tracked.txt")
    _git(workspace, "commit", "-q", "-m", "external fast forward")
    report = _inspect(service)
    assert report["snapshot"]["head_relation"] == "FAST_FORWARD"
    assert report["classification"] == "REVALIDATE"


def test_12_b_rewind_requires_replan(tmp_path: Path) -> None:
    _, workspace, _, service = _workspace(tmp_path)
    (workspace / "tracked.txt").write_text("v2\n", encoding="utf-8")
    _git(workspace, "add", "tracked.txt")
    _git(workspace, "commit", "-q", "-m", "second")
    _baseline(service)
    parent = _git(workspace, "rev-parse", "HEAD^")
    _git(workspace, "checkout", "-q", "-B", "rewound", parent)
    report = _inspect(service)
    assert report["snapshot"]["head_relation"] == "REWIND"
    assert report["classification"] == "REPLAN_REQUIRED"


def test_12_b_divergence_requires_manual_reconciliation(tmp_path: Path) -> None:
    _, workspace, _, service = _workspace(tmp_path)
    _baseline(service)
    initial = _git(workspace, "rev-parse", "HEAD")
    (workspace / "tracked.txt").write_text("branch-a\n", encoding="utf-8")
    _git(workspace, "add", "tracked.txt")
    _git(workspace, "commit", "-q", "-m", "branch a")
    service.adopt(actor="owner", session_created_at="2026-09-12T20:00:00Z", rotation_counter=0, execute=True, confirmation="ADOPT_RECONCILIATION_BASELINE")
    _git(workspace, "checkout", "-q", "-B", "branch-b", initial)
    (workspace / "other.txt").write_text("branch-b\n", encoding="utf-8")
    _git(workspace, "add", "other.txt")
    _git(workspace, "commit", "-q", "-m", "branch b")
    report = _inspect(service)
    assert report["snapshot"]["head_relation"] == "DIVERGED"
    assert report["classification"] == "MANUAL_RECONCILIATION_REQUIRED"


def test_12_b_detached_head_blocks_read_only(tmp_path: Path) -> None:
    _, workspace, _, service = _workspace(tmp_path)
    _baseline(service)
    _git(workspace, "checkout", "-q", "--detach")
    report = _inspect(service)
    assert report["classification"] == "READ_ONLY_BLOCK"
    assert report["reason_codes"] == ["DETACHED_HEAD"]


def test_12_b_dirty_worktree_cannot_be_silently_adopted(tmp_path: Path) -> None:
    _, workspace, _, service = _workspace(tmp_path)
    _baseline(service)
    (workspace / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    dry = service.adopt(actor="owner", session_created_at="2026-09-12T20:00:00Z", rotation_counter=0, execute=False, confirmation="")
    assert dry["plan"]["allowed"] is False
    with pytest.raises(ReconciliationStateError):
        service.adopt(actor="owner", session_created_at="2026-09-12T20:00:00Z", rotation_counter=0, execute=True, confirmation="ADOPT_RECONCILIATION_BASELINE")


def test_12_b_drafts_are_preserved_across_conflict(tmp_path: Path) -> None:
    platform, workspace, _, service = _workspace(tmp_path)
    _baseline(service)
    checkpoint = platform / "outputs/workspaces/devpilot-local/recovery/checkpoint.json"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_text(json.dumps({"draft_refs":["draft:story-12b"],"pending_work":[]}) + "\n", encoding="utf-8")
    (workspace / "tracked.txt").unlink()
    report = _inspect(service)
    assert report["classification"] == "MANUAL_RECONCILIATION_REQUIRED"
    assert report["draft_recovery"]["draft_refs"] == ["draft:story-12b"]
    assert report["draft_recovery"]["drafts_preserved"] is True
    assert report["draft_recovery"]["discard_performed"] is False


def test_12_b_multi_session_lock_blocks_duplicate_baseline_authority_write(tmp_path: Path) -> None:
    platform, _, resolver, service = _workspace(tmp_path)
    locks = WorkspaceLockService(platform, context_resolver=resolver)
    locks.acquire(action_id=service.LOCK_ACTION, actor="other", session_created_at="2026-09-12T20:00:00Z", rotation_counter=0, sensitive=True, ttl_seconds=300)
    with pytest.raises(ReconciliationStateError):
        service.baseline(actor="owner", session_created_at="2026-09-12T20:01:00Z", rotation_counter=0, execute=True, confirmation="CAPTURE_RECONCILIATION_BASELINE")

def test_12_b_crlf_physical_representation_does_not_create_false_reconciliation_drift(tmp_path: Path) -> None:
    _, workspace, _, service = _workspace(tmp_path)
    (workspace / ".gitattributes").write_text("*.txt text eol=crlf\n", encoding="utf-8")
    _git(workspace, "add", ".gitattributes")
    _git(workspace, "commit", "-q", "-m", "declare CRLF worktree policy")
    # A CRLF physical worktree can appear in porcelain as an unstaged MODIFY
    # while Git's normalized diff is empty. Physical EOL representation alone
    # is not engineering drift and must not block baseline capture.
    (workspace / "tracked.txt").write_bytes(b"v1\r\n")
    status = subprocess.run(["git", "-C", str(workspace), "status", "--porcelain=v1"], capture_output=True, text=True, check=True).stdout
    diff = subprocess.run(["git", "-C", str(workspace), "diff", "--quiet", "--no-ext-diff", "--", "tracked.txt"], check=False)
    assert "tracked.txt" in status
    assert diff.returncode == 0
    result = _baseline(service)
    assert result["status"] == "PASS"
    report = _inspect(service)
    assert report["classification"] == "NO_CONFLICT"
    assert report["snapshot"]["changes"] == []


def test_12_b_crlf_filter_does_not_hide_real_external_edit(tmp_path: Path) -> None:
    _, workspace, _, service = _workspace(tmp_path)
    (workspace / ".gitattributes").write_text("*.txt text eol=crlf\n", encoding="utf-8")
    _git(workspace, "add", ".gitattributes")
    _git(workspace, "commit", "-q", "-m", "declare CRLF worktree policy")
    (workspace / "tracked.txt").write_bytes(b"v1\r\n")
    _baseline(service)
    (workspace / "tracked.txt").write_bytes(b"external\r\n")
    report = _inspect(service)
    assert report["classification"] == "REVALIDATE"
    assert [row["path"] for row in report["snapshot"]["changes"]] == ["tracked.txt"]

