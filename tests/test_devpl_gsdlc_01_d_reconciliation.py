from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import replace
from pathlib import Path

import jsonschema
import pytest

from devpilot_core.application.services import ApplicationService
from devpilot_core.guided_sdlc import (
    ArtifactLifecycleStatus,
    EngineeringLifecycleStatus,
    GuidedSDLCService,
    ReadOnlyGitObserver,
    ReconciliationError,
    ReconciliationLimits,
    WorkspaceEngineeringState,
    WorkspaceEngineeringStateRepository,
    WorkspaceReconciler,
    WorkflowEngine,
)
from devpilot_core.guided_sdlc.reconciler import GitObservationError

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / ".devpilot/gsdlc/workflow_transition_catalog.json"
REPORT_SCHEMA = json.loads((ROOT / "docs/schemas/guided_sdlc_reconciliation_report.schema.json").read_text(encoding="utf-8"))


def run_git(root: Path, *args: str) -> str:
    cp = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)
    return cp.stdout.strip()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_platform(tmp_path: Path, *, registered: bool = True):
    platform = tmp_path / "platform"
    platform.mkdir()
    (platform / ".gitignore").write_text("outputs/\n", encoding="utf-8")
    run_git(platform, "init")
    run_git(platform, "config", "user.email", "devpilot@example.invalid")
    run_git(platform, "config", "user.name", "DevPilot Test")
    governed = platform / "requirements.md"
    governed.write_text("# Requirements\nv1\n", encoding="utf-8")
    other = platform / "notes.txt"
    other.write_text("notes\n", encoding="utf-8")
    run_git(platform, "add", "requirements.md", "notes.txt", ".gitignore")
    run_git(platform, "commit", "-m", "initial")
    registry_dir = platform / ".devpilot/workspaces"
    registry_dir.mkdir(parents=True)
    gsdlc_dir = platform / ".devpilot/gsdlc"
    gsdlc_dir.mkdir(parents=True)
    (gsdlc_dir / "workflow_transition_catalog.json").write_bytes(CATALOG.read_bytes())
    registry = {
        "schema_version": "1.0",
        "created_by": "DEVPL-GSDLC-01-D",
        "updated_at": "2026-08-16T00:00:00Z",
        "active_workspace_id": "ws-1" if registered else None,
        "defaults": {
            "deny_unregistered_workspaces": True,
            "cross_workspace_state_reads": False,
            "secret_sharing_allowed": False,
            "portfolio_status_read_only": True,
        },
        "security": {
            "network_used": False,
            "external_api_used": False,
            "shell_used": False,
            "remote_execution_used": False,
            "mutations_performed": False,
            "secrets_read": False,
        },
        "workspaces": [] if not registered else [{
            "workspace_id": "ws-1",
            "project_id": "project-1",
            "name": "Synthetic",
            "path": ".",
            "path_mode": "relative-to-registry-root",
            "status": "active",
            "risk_level": "medium",
            "default_effect": "deny",
            "state_path": ".devpilot/devpilot.db",
            "reports_path": "outputs/reports",
            "traces_path": "outputs/traces",
            "secrets_path": ".devpilot/providers.yaml",
            "secret_policy": "reference-only",
            "network_allowed": False,
            "external_api_allowed": False,
            "observability_required": True,
            "eval_required": True,
            "registered_at": "2026-08-16T00:00:00Z",
            "updated_at": "2026-08-16T00:00:00Z",
        }],
    }
    (registry_dir / "workspace_registry.json").write_text(json.dumps(registry), encoding="utf-8")
    run_git(platform, "add", ".devpilot/workspaces/workspace_registry.json", ".devpilot/gsdlc/workflow_transition_catalog.json")
    run_git(platform, "commit", "-m", "register workspace")
    branch = run_git(platform, "branch", "--show-current")
    head = run_git(platform, "rev-parse", "HEAD")
    repo = WorkspaceEngineeringStateRepository(platform)
    if not registered:
        return platform, repo, None
    binding = repo.binding("ws-1")
    state = WorkspaceEngineeringState.new(
        workspace_id="ws-1",
        project_id=binding.project_id,
        workspace_root_fingerprint=binding.root_fingerprint,
        created_at_utc="2026-08-16T00:00:00Z",
    )
    state = replace(
        state,
        lifecycle_status=EngineeringLifecycleStatus.IN_PROGRESS,
        phase=state.phase,
        git={"head": head, "branch": branch, "dirty": False, "fingerprint": "0" * 64},
        artifacts=({
            "artifact_id": "requirements",
            "lifecycle": ArtifactLifecycleStatus.APPROVED.value,
            "source_ref": "requirements.md",
            "fingerprint": sha(governed),
        },),
        source_fingerprints=({
            "source_ref": "requirements.md",
            "sha256": sha(governed),
        },),
    )
    repo.save(state)
    return platform, repo, state


def reconciler(repo: WorkspaceEngineeringStateRepository, observer: ReadOnlyGitObserver | None = None):
    return WorkspaceReconciler(repo, git_observer=observer)


def test_clean_no_drift_is_idempotent_and_schema_valid(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    first = reconciler(repo).inspect(state, updated_at_utc="2026-08-16T01:00:00Z")
    second = reconciler(repo).inspect(state, updated_at_utc="2026-08-16T02:00:00Z")
    assert first.report.decision == "NO_DRIFT"
    assert first.state_changed is False
    assert first.successor_state == state
    assert first.report.fingerprint() == second.report.fingerprint()
    jsonschema.Draft202012Validator(REPORT_SCHEMA).validate(first.report.to_payload())


def test_external_edit_of_approved_artifact_requires_revalidation(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    (platform / "requirements.md").write_text("# Requirements\nexternal edit\n", encoding="utf-8")
    result = reconciler(repo).inspect(state, updated_at_utc="2026-08-16T01:00:00Z")
    reasons = [x.reason_code for x in result.report.drift_entries]
    assert "APPROVED_ARTIFACT_HASH_CHANGED" in reasons
    assert "GIT_WORKTREE_DIRTY" in reasons
    assert result.successor_state.lifecycle_status == EngineeringLifecycleStatus.REVALIDATION_REQUIRED
    assert result.successor_state.artifacts[0]["lifecycle"] == ArtifactLifecycleStatus.REVALIDATION_REQUIRED.value
    assert result.successor_state.source_fingerprints == state.source_fingerprints
    assert result.successor_state.sequence == state.sequence + 1


def test_delete_governed_artifact_is_detected_without_data_loss_action(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    (platform / "requirements.md").unlink()
    result = reconciler(repo).inspect(state, updated_at_utc="2026-08-16T01:00:00Z")
    assert "GOVERNED_ARTIFACT_MISSING" in {x.reason_code for x in result.report.drift_entries}
    assert result.report.mutation_declaration["filesystem_source_written"] is False
    assert result.report.mutation_declaration["git_mutating_command_executed"] is False


def test_git_rename_is_detected_and_not_auto_rebound(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    run_git(platform, "mv", "requirements.md", "requirements-renamed.md")
    result = reconciler(repo).inspect(state, updated_at_utc="2026-08-16T01:00:00Z")
    entries = {x.reason_code: x for x in result.report.drift_entries}
    assert "GOVERNED_ARTIFACT_RENAMED" in entries
    assert entries["GOVERNED_ARTIFACT_RENAMED"].metadata["renamed_to"] == "requirements-renamed.md"
    assert result.successor_state.artifacts[0]["source_ref"] == "requirements.md"


def test_branch_switch_is_detected(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    run_git(platform, "switch", "-c", "external-branch")
    result = reconciler(repo).inspect(state, updated_at_utc="2026-08-16T01:00:00Z")
    assert "GIT_BRANCH_CHANGED" in {x.reason_code for x in result.report.drift_entries}


def test_new_commit_and_head_change_are_detected(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    (platform / "notes.txt").write_text("changed\n", encoding="utf-8")
    run_git(platform, "add", "notes.txt")
    run_git(platform, "commit", "-m", "external commit")
    result = reconciler(repo).inspect(state, updated_at_utc="2026-08-16T01:00:00Z")
    assert "GIT_HEAD_CHANGED" in {x.reason_code for x in result.report.drift_entries}


def test_dirty_untracked_workspace_is_detected(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    (platform / "untracked.txt").write_text("external\n", encoding="utf-8")
    result = reconciler(repo).inspect(state, updated_at_utc="2026-08-16T01:00:00Z")
    assert "GIT_WORKTREE_DIRTY" in {x.reason_code for x in result.report.drift_entries}


def test_path_escape_is_rejected(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    escaped = replace(
        state,
        artifacts=({
            "artifact_id": "escape",
            "lifecycle": ArtifactLifecycleStatus.APPROVED.value,
            "source_ref": "../outside.txt",
            "fingerprint": "0" * 64,
        },),
        source_fingerprints=({"source_ref": "../outside.txt", "sha256": "0" * 64},),
    )
    with pytest.raises(ReconciliationError, match="escapes workspace"):
        reconciler(repo).inspect(escaped, updated_at_utc="2026-08-16T01:00:00Z")


def test_symlink_component_is_rejected_via_boundary_guard(tmp_path: Path, monkeypatch):
    platform, repo, state = make_platform(tmp_path)
    original = Path.is_symlink
    def fake_is_symlink(self: Path) -> bool:
        if self.name == "linked":
            return True
        return original(self)
    monkeypatch.setattr(Path, "is_symlink", fake_is_symlink)
    (platform / "linked").mkdir()
    linked = replace(
        state,
        artifacts=({
            "artifact_id": "linked",
            "lifecycle": ArtifactLifecycleStatus.APPROVED.value,
            "source_ref": "linked/file.txt",
            "fingerprint": "0" * 64,
        },),
        source_fingerprints=({"source_ref": "linked/file.txt", "sha256": "0" * 64},),
    )
    with pytest.raises(ReconciliationError, match="symlink component"):
        reconciler(repo).inspect(linked, updated_at_utc="2026-08-16T01:00:00Z")


def test_unregistered_workspace_is_denied(tmp_path: Path):
    platform, repo, _ = make_platform(tmp_path, registered=False)
    state = WorkspaceEngineeringState.new(
        workspace_id="ws-1",
        project_id="project-1",
        workspace_root_fingerprint="0" * 64,
        created_at_utc="2026-08-16T00:00:00Z",
    )
    with pytest.raises(Exception, match="registered exactly once"):
        reconciler(repo).inspect(state, updated_at_utc="2026-08-16T01:00:00Z")


def test_git_timeout_is_fail_closed(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    def timeout_runner(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])
    observer = ReadOnlyGitObserver(timeout_seconds=0.5, runner=timeout_runner)
    with pytest.raises(GitObservationError, match="timed out"):
        reconciler(repo, observer).inspect(state, updated_at_utc="2026-08-16T01:00:00Z")


def test_file_size_bound_is_fail_closed(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    tiny = WorkspaceReconciler(repo, limits=ReconciliationLimits(max_file_bytes=1))
    with pytest.raises(ReconciliationError, match="max_file_bytes"):
        tiny.inspect(state, updated_at_utc="2026-08-16T01:00:00Z")


def test_preview_does_not_persist_and_execute_atomic_saves_state_only(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    (platform / "requirements.md").write_text("# Requirements\nexternal edit\n", encoding="utf-8")
    service = GuidedSDLCService(repo, WorkflowEngine.from_catalog_path(CATALOG))
    preview = service.reconcile(workspace_id="ws-1", updated_at_utc="2026-08-16T01:00:00Z", execute=False)
    assert preview.state_changed is True
    assert preview.state_persisted is False
    assert repo.load("ws-1").sequence == 0
    execute = service.reconcile(workspace_id="ws-1", updated_at_utc="2026-08-16T01:00:00Z", execute=True)
    assert execute.state_persisted is True
    stored = repo.load("ws-1")
    assert stored.sequence == 1
    assert stored.lifecycle_status == EngineeringLifecycleStatus.REVALIDATION_REQUIRED
    assert (platform / "requirements.md").read_text(encoding="utf-8") == "# Requirements\nexternal edit\n"


def test_revalidation_recomputes_project_status_and_next_action(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    (platform / "requirements.md").write_text("# Requirements\nexternal edit\n", encoding="utf-8")
    service = GuidedSDLCService(repo, WorkflowEngine.from_catalog_path(CATALOG))
    reconciliation, projection = service.reconcile_project_status(
        workspace_id="ws-1",
        updated_at_utc="2026-08-16T01:00:00Z",
        observed_at_utc="2026-08-16T01:00:01Z",
        execute=False,
    )
    assert reconciliation.report.required_revalidation is True
    assert projection.status.lifecycle_status == "REVALIDATION_REQUIRED"
    assert projection.next_action.kind == "REVALIDATE"


def test_application_service_boundary_exposes_preview_and_state_only_execute(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    (platform / "requirements.md").write_text("# Requirements\nexternal edit\n", encoding="utf-8")
    app = ApplicationService(platform)
    preview = app.guided_sdlc_reconcile_preview(
        workspace_id="ws-1",
        updated_at_utc="2026-08-16T01:00:00Z",
        observed_at_utc="2026-08-16T01:00:01Z",
    )
    assert preview.ok is True
    assert preview.data["execute"] is False
    execute = app.guided_sdlc_reconcile_execute(
        workspace_id="ws-1",
        updated_at_utc="2026-08-16T01:00:00Z",
        observed_at_utc="2026-08-16T01:00:01Z",
    )
    assert execute.ok is True
    assert execute.data["managed_workspace_source_mutated"] is False
    contract = app.application_contract()
    capability_ids = {row["operation"] for row in contract.data["capabilities"]}
    assert "guided_sdlc.reconcile.preview" in capability_ids
    assert "guided_sdlc.reconcile.execute" in capability_ids


def test_git_observer_never_invokes_mutating_commands(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    observer = ReadOnlyGitObserver()
    result = reconciler(repo, observer).inspect(state, updated_at_utc="2026-08-16T01:00:00Z")
    assert result.report.decision == "NO_DRIFT"
    flattened = {part for cmd in observer.commands_executed for part in cmd[1:]}
    assert not flattened.intersection({"reset", "checkout", "restore", "clean", "rebase", "merge", "stash", "add", "commit"})


def test_report_order_is_deterministic_for_same_drift(tmp_path: Path):
    platform, repo, state = make_platform(tmp_path)
    (platform / "requirements.md").write_text("# Requirements\nexternal edit\n", encoding="utf-8")
    (platform / "untracked.txt").write_text("external\n", encoding="utf-8")
    a = reconciler(repo).inspect(state, updated_at_utc="2026-08-16T01:00:00Z")
    b = reconciler(repo).inspect(state, updated_at_utc="2026-08-16T01:00:00Z")
    assert a.report.to_payload() == b.report.to_payload()
    assert a.successor_state.to_payload() == b.successor_state.to_payload()
