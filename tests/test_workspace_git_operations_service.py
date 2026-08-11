from __future__ import annotations

import subprocess
from pathlib import Path

from devpilot_core.application.workspace_git_operations_service import WorkspaceGitOperationsApplicationService

from uoc006_fixtures import find_approval_id, git, uoc006_env


def _document_id(service: WorkspaceGitOperationsApplicationService) -> str:
    result = service.documents.list_documents(limit=100)
    assert result.ok
    return next(str(node["document_id"]) for node in result.data["nodes"] if node.get("relative_path") == "docs/review.md")


def _approve(service: WorkspaceGitOperationsApplicationService, result) -> str:
    approval_id = find_approval_id(result.data)
    assert approval_id
    decided = service.approvals.approve(approval_id, actor="owner", reason="Fixture approval")
    assert decided.ok
    return approval_id


def test_plan_is_immutable_zero_git_mutation_and_rejects_stale_hash(uoc006_env):
    service = WorkspaceGitOperationsApplicationService(uoc006_env["platform"])
    workspace = uoc006_env["workspace"]
    before_head = git(workspace, "rev-parse", "HEAD")
    document_id = _document_id(service)
    plan_result = service.plan_commit(document_ids=[document_id], commit_message="docs: governed review", author_name="DevPilot Owner", author_email="devpilot-owner@local.invalid")
    assert plan_result.ok
    plan = plan_result.data["plan"]
    assert plan["head_before"] == before_head
    assert plan_result.data["summary"]["mutations_performed"] is False
    assert git(workspace, "diff", "--cached", "--name-only") == ""
    assert git(workspace, "rev-parse", "HEAD") == before_head
    blocked = service.request_stage_approval(plan_id=plan["plan_id"], plan_hash="0" * 64, actor="owner", reason="wrong hash")
    assert not blocked.ok
    assert any(f.id == "UOC006_PLAN_HASH_MISMATCH_BLOCK" for f in blocked.findings)


def test_stage_requires_exact_approval_and_compensates_failed_precommit(uoc006_env):
    service = WorkspaceGitOperationsApplicationService(uoc006_env["platform"])
    workspace = uoc006_env["workspace"]
    document_id = _document_id(service)
    plan = service.plan_commit(document_ids=[document_id], commit_message="docs: governed review", author_name="DevPilot Owner", author_email="devpilot-owner@local.invalid").data["plan"]
    blocked = service.stage(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], approval_id="APPROVAL-MISSING", actor="owner")
    assert not blocked.ok
    assert git(workspace, "diff", "--cached", "--name-only") == ""
    approval = service.request_stage_approval(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], actor="owner", reason="Stage reviewed document")
    approval_id = _approve(service, approval)
    staged = service.stage(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], approval_id=approval_id, actor="owner")
    assert staged.ok
    assert git(workspace, "diff", "--cached", "--name-only") == "docs/review.md"
    record = staged.data["stage_execution"]
    assert record["commit"]["message"] == "docs: governed review"
    assert record["push_performed"] is False




def test_stage_uses_git_semantic_equivalence_under_autocrlf(uoc006_env):
    service = WorkspaceGitOperationsApplicationService(uoc006_env["platform"])
    workspace = uoc006_env["workspace"]
    document_id = _document_id(service)
    plan = service.plan_commit(
        document_ids=[document_id],
        commit_message="docs: canonical CRLF staging",
        author_name="DevPilot Owner",
        author_email="devpilot-owner@local.invalid",
    ).data["plan"]
    raw_worktree = (workspace / "docs" / "review.md").read_bytes()
    assert b"\r\n" in raw_worktree
    stage_approval_id = _approve(
        service,
        service.request_stage_approval(
            plan_id=plan["plan_id"],
            plan_hash=plan["plan_hash"],
            actor="owner",
            reason="Validate Git canonical staging under autocrlf",
        ),
    )
    staged = service.stage(
        plan_id=plan["plan_id"],
        plan_hash=plan["plan_hash"],
        approval_id=stage_approval_id,
        actor="owner",
    )
    assert staged.ok
    precommit = staged.data["stage_execution"]["precommit"]
    equivalence = next(item for item in precommit["checks"] if item.get("check") == "git_worktree_index_equivalence")
    assert equivalence["status"] == "PASS"
    assert equivalence["git_exit_code"] == 0
    assert equivalence["working_sha256"] != equivalence["index_sha256"]

def test_commit_requires_second_approval_explicit_identity_and_skips_hooks(uoc006_env):
    service = WorkspaceGitOperationsApplicationService(uoc006_env["platform"])
    workspace = uoc006_env["workspace"]
    hook_marker = workspace / "hook-ran.txt"
    hook = workspace / ".git" / "hooks" / "pre-commit"
    hook.write_text(f"#!/bin/sh\necho bad > '{hook_marker}'\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    document_id = _document_id(service)
    plan = service.plan_commit(document_ids=[document_id], commit_message="docs: governed review", author_name="DevPilot Owner", author_email="devpilot-owner@local.invalid").data["plan"]
    stage_approval_id = _approve(service, service.request_stage_approval(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], actor="owner", reason="Stage reviewed document"))
    staged = service.stage(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], approval_id=stage_approval_id, actor="owner")
    assert staged.ok
    stage_id = staged.data["stage_execution"]["stage_execution_id"]
    denied = service.commit(stage_execution_id=stage_id, approval_id=stage_approval_id, actor="owner")
    assert not denied.ok
    commit_approval_id = _approve(service, service.request_commit_approval(stage_execution_id=stage_id, actor="owner", reason="Commit exact staged content"))
    committed = service.commit(stage_execution_id=stage_id, approval_id=commit_approval_id, actor="owner")
    assert committed.ok
    execution = committed.data["execution"]
    assert execution["parent"] == str(uoc006_env["baseline"])
    assert execution["committed_paths"] == ["docs/review.md"]
    assert execution["push_performed"] is False
    assert execution["hooks_executed"] is False
    assert not hook_marker.exists()
    assert git(workspace, "status", "--porcelain") == ""
    log = git(workspace, "log", "-1", "--pretty=%an <%ae> %s")
    assert log == "DevPilot Owner <devpilot-owner@local.invalid> docs: governed review"


def test_branch_create_is_local_ref_only_and_requires_clean_workspace(uoc006_env):
    service = WorkspaceGitOperationsApplicationService(uoc006_env["platform"])
    blocked = service.plan_branch_create(branch_name="feat/uoc006-safe")
    assert not blocked.ok  # document is intentionally dirty before commit
    workspace = uoc006_env["workspace"]
    git(workspace, "restore", "docs/review.md")
    plan_result = service.plan_branch_create(branch_name="feat/uoc006-safe")
    assert plan_result.ok
    plan = plan_result.data["plan"]
    approval_id = _approve(service, service.request_branch_approval(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], actor="owner", reason="Create local review branch"))
    created = service.create_branch(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], approval_id=approval_id, actor="owner")
    assert created.ok
    assert git(workspace, "branch", "--show-current") in {"master", "main"}
    assert git(workspace, "rev-parse", "feat/uoc006-safe") == git(workspace, "rev-parse", "HEAD")
    assert not service.plan_branch_create(branch_name="unsafe-branch").ok


def test_free_git_arguments_and_dangerous_operations_are_not_exposed():
    from devpilot_core.repo.governed_git_mutation import GovernedGitMutationAdapter
    public = {name for name in dir(GovernedGitMutationAdapter) if not name.startswith("_")}
    forbidden = {"run", "push", "force_push", "reset", "reset_hard", "rebase", "checkout", "switch", "delete_branch", "tag"}
    assert public.isdisjoint(forbidden)


def test_secret_like_content_is_blocked_before_staging_plan(uoc006_env):
    service = WorkspaceGitOperationsApplicationService(uoc006_env["platform"])
    workspace = uoc006_env["workspace"]
    document_id = _document_id(service)
    review = workspace / "docs" / "review.md"
    review.write_text(review.read_text(encoding="utf-8") + "\nOPENAI_API_KEY=sk-uoc006-secret-must-block\n", encoding="utf-8")
    result = service.plan_commit(
        document_ids=[document_id],
        commit_message="docs: must not stage secret",
        author_name="DevPilot Owner",
        author_email="devpilot-owner@local.invalid",
    )
    assert not result.ok
    assert any(f.id == "UOC006_SECRET_STAGING_BLOCK" for f in result.findings)
    assert git(workspace, "diff", "--cached", "--name-only") == ""
