from __future__ import annotations

from pathlib import Path

import pytest

from devpilot_core.application import ApplicationService
from devpilot_core.cli_models import CommandResult, ExitCode
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.story_execution import StoryExecutionState, StoryExecutionStatus, StoryExecutionStore

ROOT = Path(__file__).resolve().parents[1]
KNOWN_PATH = "src/devpilot_core/application/quality_operations.py"


def _state(workspace: Path, status: StoryExecutionStatus, sequence: int) -> StoryExecutionStore:
    store = StoryExecutionStore(workspace, workspace_id=workspace.name)
    store.save_state(StoryExecutionState(
        execution_id="story-exec-10e1234567890abcdef1234",
        workspace_id=workspace.name,
        project_id="story-cycle-e2e-fixture",
        story_id="STORY-10E",
        story_version="1.0.0",
        status=status,
        sequence=sequence,
        dor_report_sha256="a" * 64,
        context_pack_id="story-context-10e1234567890abcdef12",
        context_pack_sha256="b" * 64,
        created_at_utc="2026-09-10T20:00:00+00:00",
        updated_at_utc="2026-09-10T20:00:00+00:00",
    ))
    return store


@pytest.fixture
def runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    workspace = tmp_path / "story-cycle-e2e-workspace"
    source = workspace / KNOWN_PATH
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("VALUE = 'legacy'\n", encoding="utf-8")
    (workspace / ".devpilot").mkdir(exist_ok=True)
    (workspace / ".devpilot/project.yaml").write_text(
        "project_id: story-cycle-e2e-fixture\nproject_name: Story Cycle E2E Fixture\nproject_type: software\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(workspace))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(workspace))
    monkeypatch.setenv("DEVPILOT_GSDLC09C_CONTROL_ROOT", str(tmp_path / "control"))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)
    app = ApplicationService(ROOT, approval_auth_store=LocalAuthStore(tmp_path / "auth"))
    return app, workspace


def _source_plan(app: ApplicationService) -> dict:
    listed = app.story_code_sources()
    row = next(x for x in listed.data["sources"] if x["relative_path"] == KNOWN_PATH)
    src = app.story_code_source_read(source_id=row["source_id"]).data["source"]
    draft = app.story_code_draft_save(
        operation="EDIT", content="VALUE = 'ready'\n", target_path=KNOWN_PATH,
        source_id=src["source_id"], expected_source_sha256=src["sha256"], expected_revision_sha256=None,
        actor="owner", actor_role="owner",
    ).data["draft"]
    return app.story_source_change_plan_create(draft_ids=[draft["draft_id"]], actor="owner", actor_role="owner").data["plan"]


def test_10e_test_plan_approval_advances_changes_ready_to_validating(runtime):
    app, workspace = runtime
    store = _state(workspace, StoryExecutionStatus.CHANGES_READY, 2)
    plan = _source_plan(app)
    test_plan = app.story_test_plan_create(source_plan_id=plan["plan_id"], source_plan_hash=plan["plan_hash"], actor="owner", actor_role="owner").data["story_test_plan"]
    approved = app.story_test_plan_decide(test_plan_id=test_plan["test_plan_id"], test_plan_hash=test_plan["test_plan_hash"], decision="APPROVE", actor="owner", actor_role="owner", reason="E2E validation starts")
    assert approved.ok, approved.to_dict()
    assert approved.data["story_state_transition"] == {"from":"CHANGES_READY","to":"VALIDATING","trigger":"approved-story-test-plan","runtime_only":True}
    assert store.load_state().status is StoryExecutionStatus.VALIDATING


def test_10e_successor_test_plan_is_allowed_while_validating(runtime):
    app, workspace = runtime
    _state(workspace, StoryExecutionStatus.VALIDATING, 3)
    plan = _source_plan(app)
    result = app.story_test_plan_create(source_plan_id=plan["plan_id"], source_plan_hash=plan["plan_hash"], actor="owner", actor_role="owner")
    assert result.ok, result.to_dict()
    assert result.data["story_test_plan"]["story_execution_id"] == "story-exec-10e1234567890abcdef1234"


class _QualityPass:
    def evaluate(self, **kwargs):
        return CommandResult("story quality evaluate", True, ExitCode.PASS, "PASS", data={"story_quality_report": {"decision":"PASS","commit_ready":True,"story_execution_id":"story-exec-10e1234567890abcdef1234"}})


class _QualityBlock:
    def evaluate(self, **kwargs):
        return CommandResult("story quality evaluate", True, ExitCode.PASS, "BLOCK decision", data={"story_quality_report": {"decision":"BLOCK","commit_ready":False,"story_execution_id":"story-exec-10e1234567890abcdef1234"}})


def test_10e_fresh_quality_pass_advances_validating_to_commit_ready(runtime):
    app, workspace = runtime
    store = _state(workspace, StoryExecutionStatus.VALIDATING, 3)
    app._story_quality_gate = _QualityPass()
    result = app.story_quality_evaluate(test_plan_id="plan-e", test_plan_hash="f"*64, actor="owner", actor_role="owner")
    assert result.ok
    assert result.data["story_state_transition"]["to"] == "COMMIT_READY"
    assert store.load_state().status is StoryExecutionStatus.COMMIT_READY


def test_10e_quality_block_keeps_story_validating(runtime):
    app, workspace = runtime
    store = _state(workspace, StoryExecutionStatus.VALIDATING, 3)
    app._story_quality_gate = _QualityBlock()
    result = app.story_quality_evaluate(test_plan_id="plan-e", test_plan_hash="f"*64, actor="owner", actor_role="owner")
    assert result.ok
    assert "story_state_transition" not in result.data
    assert store.load_state().status is StoryExecutionStatus.VALIDATING


def test_10e_story_workbench_allows_governed_remediation_while_validating():
    text=(ROOT/"ui/web/src/pages/StoryCodeWorkbenchView.ts").read_text(encoding="utf-8")
    assert "sourceChangeAllowed=new Set(['IN_PROGRESS','VALIDATING'])" in text
    assert "validationAllowed=new Set(['CHANGES_READY','VALIDATING'])" in text
    assert "new Set(['IN_PROGRESS','CHANGES_READY','VALIDATING'])" in text
    assert "Story VALIDATING" in text


def test_10e_quality_remediation_handoff_survives_ui_navigation_without_becoming_authority():
    client=(ROOT/'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    panel=(ROOT/'ui/web/src/components/StoryQualityGatePanel.ts').read_text(encoding='utf-8')
    assert "QUALITY_REMEDIATION_HANDOFF_KEY = 'devpilot.gsdlc10e.qualityRemediationHandoff.v1'" in client
    assert 'writeQualityRemediationHandoff' in panel
    assert 'readQualityRemediationHandoff' in panel
    assert "client().storyQualityRemediations(handoff.source_report_id)" in panel
    assert "client().storyTestPlan(report.story_test_plan_id)" in panel
    assert "client().storyCodeSources()" in panel
    assert "changedPaths.length!==1" in panel
    assert "rows.find(row=>row.trace_id===handoff.remediation_trace_id)" in panel
    assert "successorId=context.test_plan_id" in panel and "successorHash=context.test_plan_hash" in panel
    assert "clearQualityRemediationHandoff()" in panel
    assert "Recuperar remediación E2E" in panel
    assert 'agent_tool_intent:trace.agent_proposal?.tool_intent??null' in panel
    assert 'agent_tool_execution_decision:trace.agent_proposal?.tool_execution_decision??null' in panel


def test_10e_project_status_projects_story_done_as_next_story_or_sprint_ready(runtime, monkeypatch: pytest.MonkeyPatch):
    app, workspace = runtime
    _state(workspace, StoryExecutionStatus.DONE, 5)
    result = app.guided_sdlc_project_status_primary(
        workspace_id=workspace.name,
        observed_at_utc="2026-09-10T20:30:00+00:00",
    )
    assert result.ok, result.to_dict()
    planning = result.data["project_status"]["planning"]
    assert planning["current_story"]["status"] == "DONE"
    assert planning["story_cycle"] == {
        "status": "STORY_COMPLETE",
        "next_selection_ready": True,
        "next_kind": "NEXT_STORY_OR_SPRINT",
        "navigation_target": "planning-roadmap",
        "reason_code": "CURRENT_STORY_DONE",
        "read_only": True,
        "server_authoritative": True,
        "source_mutations_performed": False,
    }
    page=(ROOT/'ui/web/src/pages/ProjectStatusView.ts').read_text(encoding='utf-8')
    assert 'Continuar con siguiente story/sprint' in page
    assert 'data.storyCycleStatus' not in page
    assert 'story.dataset.currentStoryStatus' in page
    assert 'cycleState.dataset.storyCycleStatus' in page
