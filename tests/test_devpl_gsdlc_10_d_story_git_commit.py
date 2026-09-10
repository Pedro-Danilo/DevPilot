from __future__ import annotations

import hashlib
from pathlib import Path

from devpilot_core.application.approval_service import ApprovalApplicationService
from devpilot_core.application.auth_service import AuthApplicationService
from devpilot_core.application.workspace_git_operations_service import WorkspaceGitOperationsApplicationService
from devpilot_core.cli_models import CommandResult, ExitCode
from devpilot_core.story_execution import StoryExecutionState, StoryExecutionStatus, StoryExecutionStore

from uoc006_fixtures import find_approval_id, git, uoc006_env


def ok(data: dict) -> CommandResult:
    return CommandResult("mock", True, ExitCode.PASS, "PASS", data=data)


def semantic_sha(path: Path) -> str:
    text = path.read_bytes().decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prepared(uoc006_env):
    platform = uoc006_env["platform"]
    workspace = uoc006_env["workspace"]
    auth = AuthApplicationService(platform)
    issue = auth.bootstrap_owner(username="owner", display_name="DevPilot Owner", password="TestOwnerPassword!2026")

    source_hash = "a" * 64
    test_hash = "b" * 64
    quality_hash = "c" * 64
    quality_inputs_hash = "d" * 64
    story_execution_id = "story-exec-10d1234567890abcdef1234"
    story_id = "story-10d"
    expected_content = semantic_sha(workspace / "docs" / "review.md")
    source_plan = {
        "plan_id": "source-plan-10d1234567890abcdef12",
        "plan_hash": source_hash,
        "workspace_id": workspace.name,
        "story_execution_id": story_execution_id,
        "exact_path_allowlist": ["docs/review.md"],
        "changes": [{
            "operation": "EDIT", "source_path": "docs/review.md", "target_path": "docs/review.md",
            "preimage_sha256": "e" * 64, "postimage_sha256": expected_content,
        }],
    }
    test_plan = {
        "test_plan_id": "story-test-plan-10d1234567890abcd",
        "test_plan_hash": test_hash,
        "status": "APPROVED",
        "story_execution_id": story_execution_id,
        "story_id": story_id,
        "source_change_plan_id": source_plan["plan_id"],
        "source_change_plan_hash": source_hash,
        "changed_paths": ["docs/review.md"],
    }
    state = {"stale": False}
    quality = {
        "report_id": "story-quality-report-10d1234567890ab",
        "report_hash": quality_hash,
        "inputs_hash": quality_inputs_hash,
        "story_test_plan_id": test_plan["test_plan_id"],
        "story_test_plan_hash": test_hash,
        "decision": "PASS", "commit_ready": True,
        "required_job_results": [
            {"job_id": "job-test-10d", "artifact_refs": ["evidence/test-10d.json"]},
            {"job_id": "job-lint-10d", "artifact_refs": ["evidence/lint-10d.json"]},
        ],
    }

    def source_loader(*, plan_id: str):
        assert plan_id == source_plan["plan_id"]
        return ok({"plan": source_plan})

    def test_loader(*, test_plan_id: str):
        assert test_plan_id == test_plan["test_plan_id"]
        return ok({"story_test_plan": test_plan})

    def quality_loader(*, report_id: str):
        assert report_id == quality["report_id"]
        return ok({"story_quality_report": {**quality, "stale": state["stale"]}})

    # Runtime-only StoryExecution artifacts are not source and must never enter
    # the exact Git delta. The product fixture normally carries this ignore in
    # its baseline; UOC-006's older fixture predates StoryExecution.
    info_exclude = workspace / ".git" / "info" / "exclude"
    info_exclude.write_text(info_exclude.read_text(encoding="utf-8") + "\noutputs/\n", encoding="utf-8")

    service = WorkspaceGitOperationsApplicationService(
        platform,
        approval_auth_store=auth.store,
        source_plan_loader=source_loader,
        story_test_plan_loader=test_loader,
        story_quality_report_loader=quality_loader,
    )
    context = service.context_resolver.resolve()
    wsid = str(context.active_workspace_id)
    source_plan["workspace_id"] = wsid
    store = StoryExecutionStore(workspace, workspace_id=wsid)
    store.save_state(StoryExecutionState(
        execution_id=story_execution_id, workspace_id=wsid, project_id="fixture-10d", story_id=story_id, story_version="1.0.0",
        status=StoryExecutionStatus.COMMIT_READY, sequence=4, dor_report_sha256="1" * 64,
        context_pack_id="story-context-10d1234567890ab", context_pack_sha256="2" * 64,
        created_at_utc="2026-09-10T12:00:00Z", updated_at_utc="2026-09-10T12:04:00Z",
    ))
    store.save_context({
        "fragments": [
            {"kind": "requirement", "target_id": "REQ-10D-001"},
            {"kind": "test-intent", "target_id": "TEST-10D-001"},
        ]
    })
    return service, auth, issue, state, quality


def approve(service, auth, issue, result) -> str:
    assert result.ok, [f.to_dict() for f in result.findings]
    approval_id = find_approval_id(result.data)
    assert approval_id
    decided = ApprovalApplicationService(service.platform_root, auth_store=auth.store).decide_authenticated(
        approval_id=approval_id,
        decision="approved",
        principal=issue.context.principal,
        session=issue.context,
        caller_actor=None,
        reason="GSDLC-10-D fixture authenticated human approval",
    )
    assert decided.ok, [f.to_dict() for f in decided.findings]
    return approval_id


def make_plan(service, quality):
    result = service.plan_story_commit(
        quality_report_id=quality["report_id"], quality_report_hash=quality["report_hash"],
        commit_message="feat: close governed story 10d", author_name="DevPilot Owner", author_email="devpilot-owner@local.invalid",
        actor="owner", actor_role="owner",
    )
    assert result.ok, result.to_dict()
    return result.data["commit_plan"]


def stage_plan(service, auth, issue, plan):
    stage_approval = service.request_story_stage_approval(
        commit_plan_id=plan["commit_plan_id"], commit_plan_hash=plan["commit_plan_hash"], actor="owner", actor_role="owner", reason="Approve exact story staging"
    )
    stage_approval_id = approve(service, auth, issue, stage_approval)
    staged = service.stage_story(commit_plan_id=plan["commit_plan_id"], commit_plan_hash=plan["commit_plan_hash"], approval_id=stage_approval_id, actor="owner", actor_role="owner")
    assert staged.ok, staged.to_dict()
    return staged.data["stage_execution"]


def test_commit_plan_is_exact_quality_bound_and_zero_mutation(uoc006_env):
    service, _, _, _, quality = prepared(uoc006_env)
    before = git(uoc006_env["workspace"], "rev-parse", "HEAD")
    plan = make_plan(service, quality)
    assert plan["exact_paths"] == ["docs/review.md"] == plan["include_paths"]
    assert plan["exclude_paths"] == []
    assert plan["story_quality_report_hash"] == quality["report_hash"]
    assert plan["approval"]["required"] is True
    assert plan["approval"]["required_role"] == "owner"
    assert plan["approval"]["stage_approval_required"] is True
    assert plan["approval"]["commit_approval_required"] is True
    assert plan["approval"]["stage_and_commit_separate"] is True
    assert plan["approval"]["authority_source"] == "server-rbac-policy-approval"
    assert plan["approval"]["agent_granted_authority"] is False
    assert plan["safety"]["git_add_all_enabled"] is False
    assert plan["safety"]["push_enabled"] is False
    assert plan["traceability"]["requirement_ids"] == ["REQ-10D-001"]
    assert git(uoc006_env["workspace"], "diff", "--cached", "--name-only") == ""
    assert git(uoc006_env["workspace"], "rev-parse", "HEAD") == before


def test_unexpected_dirty_path_blocks_before_plan(uoc006_env):
    service, _, _, _, quality = prepared(uoc006_env)
    extra = uoc006_env["workspace"] / "unexpected.txt"
    extra.write_text("unexpected\n", encoding="utf-8")
    result = service.plan_story_commit(
        quality_report_id=quality["report_id"], quality_report_hash=quality["report_hash"], commit_message="feat: blocked",
        author_name="DevPilot Owner", author_email="devpilot-owner@local.invalid", actor="owner", actor_role="owner",
    )
    assert not result.ok
    assert any(f.id == "GSDLC10D_UNEXPECTED_DIRTY_PATH_BLOCK" for f in result.findings)
    assert git(uoc006_env["workspace"], "diff", "--cached", "--name-only") == ""


def test_stale_quality_and_wrong_role_and_agent_authority_block(uoc006_env):
    service, _, _, state, quality = prepared(uoc006_env)
    state["stale"] = True
    stale = service.plan_story_commit(
        quality_report_id=quality["report_id"], quality_report_hash=quality["report_hash"], commit_message="feat: blocked",
        author_name="DevPilot Owner", author_email="devpilot-owner@local.invalid", actor="owner", actor_role="owner",
    )
    assert not stale.ok and any(f.id == "GSDLC10D_STALE_QUALITY_BLOCK" for f in stale.findings)
    state["stale"] = False
    plan = make_plan(service, quality)
    wrong = service.request_story_stage_approval(commit_plan_id=plan["commit_plan_id"], commit_plan_hash=plan["commit_plan_hash"], actor="dev", actor_role="developer", reason="try")
    assert not wrong.ok and any(f.id == "GSDLC10D_WRONG_ROLE_BLOCK" for f in wrong.findings)
    agent = service.request_story_stage_approval(commit_plan_id=plan["commit_plan_id"], commit_plan_hash=plan["commit_plan_hash"], actor="agent", actor_role="owner", reason="try", authority_source="agent-runtime")
    assert not agent.ok and any(f.id == "GSDLC10D_AGENT_MODEL_AUTHORITY_BLOCK" for f in agent.findings)


def test_exact_stage_uses_separate_authenticated_approval_and_manifest(uoc006_env):
    service, auth, issue, _, quality = prepared(uoc006_env)
    plan = make_plan(service, quality)
    stage = stage_plan(service, auth, issue, plan)
    assert git(uoc006_env["workspace"], "diff", "--cached", "--name-only") == "docs/review.md"
    assert stage["staging_manifest"]["exact_paths"] == ["docs/review.md"]
    assert stage["staging_manifest"]["git_add_all"] is False
    assert stage["staging_manifest"]["shell"] is False
    assert stage["push_performed"] is False


def test_commit_requires_second_approval_and_creates_exact_git_record(uoc006_env):
    service, auth, issue, _, quality = prepared(uoc006_env)
    plan = make_plan(service, quality)
    stage = stage_plan(service, auth, issue, plan)
    stage_id = stage["stage_execution_id"]
    denied = service.commit_story(stage_execution_id=stage_id, approval_id=stage["stage_approval_id"], actor="owner", actor_role="owner")
    assert not denied.ok
    approval = service.request_story_commit_approval(stage_execution_id=stage_id, actor="owner", actor_role="owner", reason="Approve exact story commit")
    commit_approval_id = approve(service, auth, issue, approval)
    assert commit_approval_id != stage["stage_approval_id"]
    committed = service.commit_story(stage_execution_id=stage_id, approval_id=commit_approval_id, actor="owner", actor_role="owner")
    assert committed.ok, committed.to_dict()
    record = committed.data["git_commit_record"]
    assert record["committed_paths"] == ["docs/review.md"]
    assert record["parent_hash"] == str(uoc006_env["baseline"])
    assert record["traceability_complete"] is True
    assert record["requirement_ids"] == ["REQ-10D-001"]
    assert set(record["test_evidence_ids"]) == {"evidence/test-10d.json", "evidence/lint-10d.json"}
    assert record["push_performed"] is False and record["force_push_performed"] is False
    assert record["rebase_performed"] is False and record["reset_hard_performed"] is False and record["shell"] is False
    assert record["agent_granted_authority"] is False and record["model_route_granted_authority"] is False
    assert git(uoc006_env["workspace"], "status", "--porcelain") == ""
    assert StoryExecutionStore(uoc006_env["workspace"], workspace_id=plan["workspace_id"]).load_state().status is StoryExecutionStatus.DONE


def test_stale_quality_after_stage_blocks_commit_without_rerun_or_push(uoc006_env):
    service, auth, issue, state, quality = prepared(uoc006_env)
    plan = make_plan(service, quality)
    stage = stage_plan(service, auth, issue, plan)
    approval = service.request_story_commit_approval(stage_execution_id=stage["stage_execution_id"], actor="owner", actor_role="owner", reason="Approve commit")
    commit_approval_id = approve(service, auth, issue, approval)
    state["stale"] = True
    blocked = service.commit_story(stage_execution_id=stage["stage_execution_id"], approval_id=commit_approval_id, actor="owner", actor_role="owner")
    assert not blocked.ok and any(f.id == "GSDLC10D_STALE_QUALITY_BLOCK" for f in blocked.findings)
    assert git(uoc006_env["workspace"], "rev-parse", "HEAD") == str(uoc006_env["baseline"])
    assert git(uoc006_env["workspace"], "diff", "--cached", "--name-only") == "docs/review.md"
    assert blocked.data.get("full_regression_started") is False


def test_story_bound_max_32_does_not_expand_historical_uoc006_default():
    from devpilot_core.repo.governed_git_mutation import validate_paths
    assert len(validate_paths([f"src/f{i}.py" for i in range(20)])) == 20
    try:
        validate_paths([f"src/f{i}.py" for i in range(21)])
        assert False, "historical default should block >20"
    except ValueError:
        pass
    assert len(validate_paths([f"src/f{i}.py" for i in range(32)], max_paths=32)) == 32


def test_destructive_git_surface_remains_unavailable():
    from devpilot_core.repo.governed_git_mutation import GovernedGitMutationAdapter
    public = {name for name in dir(GovernedGitMutationAdapter) if not name.startswith("_")}
    assert public.isdisjoint({"run", "push", "force_push", "reset", "reset_hard", "rebase", "checkout", "switch", "delete_branch", "tag", "add_all"})


def test_story_git_routes_are_human_session_bound_and_owner_mutations_registered():
    import json
    from devpilot_core.interfaces.api.security import resolve_route_policy

    route_cases = [
        ("GET", "/api/v1/story/git/context", "story.git.context"),
        ("POST", "/api/v1/story/git/commit-plans", "story.git.commit_plan.create"),
        ("GET", "/api/v1/story/git/commit-plans/plan-x", "story.git.commit_plan.get"),
        ("POST", "/api/v1/story/git/commit-plans/plan-x/stage-approval-request", "story.git.stage_approval_request"),
        ("POST", "/api/v1/story/git/commit-plans/plan-x/stage", "story.git.stage"),
        ("POST", "/api/v1/story/git/stage-executions/stage-x/commit-approval-request", "story.git.commit_approval_request"),
        ("POST", "/api/v1/story/git/stage-executions/stage-x/commit", "story.git.commit"),
        ("GET", "/api/v1/story/git/executions/commit-x", "story.git.execution.get"),
    ]
    for method, path, operation in route_cases:
        policy = resolve_route_policy(method, path)
        assert policy is not None and policy.operation == operation

    catalog = json.loads((Path(__file__).parents[1] / ".devpilot" / "identity" / "server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    story_git = [r for r in catalog["route_policies"] if r["path"].startswith("/api/v1/story/git/")]
    assert len(story_git) == 8
    assert all(r["human_session_required"] and not r["legacy_token_allowed"] for r in story_git)
    governed = [r for r in story_git if r["method"] == "POST" and ("approval" in r["path"] or r["path"].endswith("/stage") or r["path"].endswith("/commit"))]
    assert len(governed) == 4 and all(r["allowed_roles"] == ["owner"] for r in governed)


def test_story_code_ui_reuses_workspace_git_panel_and_exposes_10d_safety_contract():
    repo = Path(__file__).parents[1]
    panel = (repo / "ui" / "web" / "src" / "components" / "WorkspaceGitOperationsPanel.ts").read_text(encoding="utf-8")
    story = (repo / "ui" / "web" / "src" / "pages" / "StoryCodeWorkbenchView.ts").read_text(encoding="utf-8")
    assert "storyMode?: boolean" in panel
    assert "createStoryGitOperationsPanel" in panel
    for marker in ["EXACT PATHS", "RBAC ×2", "NO PUSH", "NO FORCE", "NO REBASE", "FULL=0"]:
        assert marker in panel
    assert "authority=human-session" in panel
    assert "Agente/modelo puede proponer, nunca conceder permiso Git" in panel
    assert "stage_and_commit_separate" in panel
    story_section = panel.split("function createStoryGitOperationsPanel", 1)[1]
    assert "decideApproval(approval.approval_id, decision, { reason:" in story_section
    assert "decideApproval(approval.approval_id, decision, { actor: ACTOR" not in story_section
    client = (repo / "ui" / "web" / "src" / "api" / "client.ts").read_text(encoding="utf-8")
    decide_method = client.split("async decideApproval", 1)[1].split("async ", 1)[0]
    assert "{ reason: payload.reason }" in decide_method
    assert "this.post(`/approvals/${encodeURIComponent(approvalId)}/${decision}`, payload" not in decide_method
    assert "createWorkspaceGitOperationsPanel" in story and "storyMode:true" in story
