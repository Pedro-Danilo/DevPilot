from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jsonschema
import pytest
from devpilot_core.application import ApplicationService
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.story_execution import StoryExecutionState, StoryExecutionStatus, StoryExecutionStore

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = {"Origin": "http://127.0.0.1:5173"}
PASSWORD = "A-very-long-local-password-10a"
KNOWN_PATH = "src/devpilot_core/application/quality_operations.py"
SENSITIVE_PATH = "src/devpilot_core/testing/impact_v2.py"
UNKNOWN_PATH = "src/unknown-gsdlc10a-fixture.py"


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "story-test-plan-workspace"
    for rel in [KNOWN_PATH, SENSITIVE_PATH, UNKNOWN_PATH]:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# fixture {rel}\nVALUE = 1\n", encoding="utf-8")
    (root / ".devpilot").mkdir(exist_ok=True)
    (root / ".devpilot/project.yaml").write_text(
        "project_id: story-test-plan-fixture\nproject_name: Story Test Plan Fixture\nproject_type: software\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(root))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(root))
    monkeypatch.setenv("DEVPILOT_GSDLC09C_CONTROL_ROOT", str(tmp_path / "control-10a"))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)
    StoryExecutionStore(root, workspace_id=root.name).save_state(
        StoryExecutionState(
            execution_id="story-exec-10a1234567890abcdef1234",
            workspace_id=root.name,
            project_id="story-test-plan-fixture",
            story_id="STORY-10A",
            story_version="1.0.0",
            status=StoryExecutionStatus.CHANGES_READY,
            sequence=2,
            dor_report_sha256="a" * 64,
            context_pack_id="story-context-10a1234567890abcdef12",
            context_pack_sha256="b" * 64,
            created_at_utc="2026-09-09T10:00:00+00:00",
            updated_at_utc="2026-09-09T10:10:00+00:00",
        )
    )
    return root


@pytest.fixture
def runtime(workspace: Path, tmp_path: Path):
    # Core StoryTestPlan tests deliberately avoid FastAPI/httpx.  The single HTTP
    # contract test imports TestClient lazily, so Windows selective validation
    # does not inherit an unrelated httpx dependency.
    store = LocalAuthStore(tmp_path / "auth10a")
    return ApplicationService(ROOT, approval_auth_store=store), store


def source(app: ApplicationService, rel: str) -> dict:
    listed = app.story_code_sources()
    assert listed.ok, listed.to_dict()
    row = next(x for x in listed.data["sources"] if x["relative_path"] == rel)
    got = app.story_code_source_read(source_id=row["source_id"])
    assert got.ok, got.to_dict()
    return got.data["source"]


def plan(app: ApplicationService, rel: str) -> dict:
    src = source(app, rel)
    draft = app.story_code_draft_save(
        operation="EDIT",
        content=src["content"] + "# changed\n",
        target_path=rel,
        source_id=src["source_id"],
        expected_source_sha256=src["sha256"],
        expected_revision_sha256=None,
        actor="local-owner",
        actor_role="owner",
    )
    assert draft.ok, draft.to_dict()
    created = app.story_source_change_plan_create(
        draft_ids=[draft.data["draft"]["draft_id"]], actor="local-owner", actor_role="owner"
    )
    assert created.ok, created.to_dict()
    return created.data["plan"]


def create_test_plan(app: ApplicationService, source_plan: dict, *, role: str = "owner") -> dict:
    result = app.story_test_plan_create(
        source_plan_id=source_plan["plan_id"],
        source_plan_hash=source_plan["plan_hash"],
        actor=f"local-{role}",
        actor_role=role,
    )
    assert result.ok, result.to_dict()
    return result.data["story_test_plan"]


def test_01_known_delta_produces_deterministic_hash_bound_explainable_plan(workspace: Path, runtime) -> None:
    app, _ = runtime
    source_plan = plan(app, KNOWN_PATH)
    first = create_test_plan(app, source_plan)
    second = create_test_plan(app, source_plan)
    assert first["test_plan_id"] == second["test_plan_id"]
    assert first["test_plan_hash"] == second["test_plan_hash"]
    assert first["source_change_plan_id"] == source_plan["plan_id"]
    assert first["source_change_plan_hash"] == source_plan["plan_hash"]
    assert first["changed_paths"] == [KNOWN_PATH]
    assert first["matched_contracts"] and first["required_tests"]
    assert first["unknown_impact"]["paths"] == []
    assert first["full_regression_signal"]["informational_only"] is True
    assert first["full_regression_signal"]["execution_authorized"] is False
    assert first["full_regression_signal"]["logical_full_runs_allowed_in_gsdlc_10_a"] == 0
    assert first["policy"]["free_form_test_command_allowed"] is False
    assert first["safety"]["tests_executed"] is False
    assert first["safety"]["network_used"] is False
    assert first["test_impact_report_hash"]
    schema = json.loads((ROOT / "docs/schemas/story_test_plan.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(first, schema)
    impact_schema = json.loads((ROOT / "docs/schemas/story_test_impact_report.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(first["test_impact_report"], impact_schema)


def test_02_stale_change_plan_hash_blocks(workspace: Path, runtime) -> None:
    app, _ = runtime
    source_plan = plan(app, KNOWN_PATH)
    result = app.story_test_plan_create(
        source_plan_id=source_plan["plan_id"], source_plan_hash="0" * 64, actor="owner", actor_role="owner"
    )
    assert not result.ok
    assert any(f.id == "GSDLC10A_STALE_CHANGE_PLAN_HASH_BLOCK" for f in result.findings)


def test_03_story_must_be_changes_ready(workspace: Path, runtime) -> None:
    app, _ = runtime
    source_plan = plan(app, KNOWN_PATH)
    store = StoryExecutionStore(workspace, workspace_id=workspace.name)
    current = store.load_state()
    assert current is not None
    store.save_state(StoryExecutionState(
        execution_id=current.execution_id, workspace_id=current.workspace_id, project_id=current.project_id,
        story_id=current.story_id, story_version=current.story_version, status=StoryExecutionStatus.IN_PROGRESS,
        sequence=1, dor_report_sha256=current.dor_report_sha256, context_pack_id=current.context_pack_id,
        context_pack_sha256=current.context_pack_sha256, created_at_utc=current.created_at_utc,
        updated_at_utc="2026-09-09T10:11:00+00:00", history=(),
    ))
    result = app.story_test_plan_create(
        source_plan_id=source_plan["plan_id"], source_plan_hash=source_plan["plan_hash"], actor="owner", actor_role="owner"
    )
    assert not result.ok
    assert any(f.id == "GSDLC10A_STORY_NOT_CHANGES_READY_BLOCK" for f in result.findings)


def test_04_unknown_path_is_fail_closed_and_requires_explicit_human_reason(workspace: Path, runtime) -> None:
    app, _ = runtime
    source_plan = plan(app, UNKNOWN_PATH)
    test_plan = create_test_plan(app, source_plan)
    assert test_plan["status"] == "REVIEW_REQUIRED"
    assert test_plan["unknown_impact"]["paths"] == [UNKNOWN_PATH]
    assert test_plan["unknown_impact"]["fail_closed"] is True
    blocked = app.story_test_plan_decide(
        test_plan_id=test_plan["test_plan_id"], test_plan_hash=test_plan["test_plan_hash"],
        decision="APPROVE", actor="owner", actor_role="owner", reason="",
    )
    assert not blocked.ok
    assert any(f.id == "GSDLC10A_UNKNOWN_REVIEW_REASON_BLOCK" for f in blocked.findings)
    approved = app.story_test_plan_decide(
        test_plan_id=test_plan["test_plan_id"], test_plan_hash=test_plan["test_plan_hash"],
        decision="APPROVE", actor="owner", actor_role="owner", reason="Owner manually reviewed unknown path impact.",
    )
    assert approved.ok and approved.data["story_test_plan"]["status"] == "APPROVED"


def test_05_sensitive_delta_cannot_be_under_tested_or_waived(workspace: Path, runtime) -> None:
    app, _ = runtime
    source_plan = plan(app, SENSITIVE_PATH)
    test_plan = create_test_plan(app, source_plan)
    assert test_plan["sensitive_impact"]["present"] is True
    assert test_plan["required_tests"]
    assert test_plan["effective_required_tests"] == test_plan["required_tests"]
    assert all(not test_plan["test_policy"][x]["waivable"] for x in test_plan["required_tests"])
    blocked = app.story_test_plan_decide(
        test_plan_id=test_plan["test_plan_id"], test_plan_hash=test_plan["test_plan_hash"], decision="WAIVE",
        actor="owner", actor_role="owner", reason="try", waived_test_ids=[test_plan["required_tests"][0]], ttl_minutes=60,
    )
    assert not blocked.ok
    assert any(f.id == "GSDLC10A_SENSITIVE_WAIVER_BLOCK" for f in blocked.findings)


def test_06_wrong_role_and_agent_authority_cannot_approve_or_waive(workspace: Path, runtime) -> None:
    app, _ = runtime
    source_plan = plan(app, KNOWN_PATH)
    test_plan = create_test_plan(app, source_plan)
    developer_approve = app.story_test_plan_decide(
        test_plan_id=test_plan["test_plan_id"], test_plan_hash=test_plan["test_plan_hash"], decision="APPROVE",
        actor="developer", actor_role="developer", reason="developer try",
    )
    assert not developer_approve.ok and any(f.id == "GSDLC10A_APPROVAL_ROLE_BLOCK" for f in developer_approve.findings)
    agent = app.story_test_plan_decide(
        test_plan_id=test_plan["test_plan_id"], test_plan_hash=test_plan["test_plan_hash"], decision="REJECT",
        actor="agent", actor_role="owner", authority_source="agent-runtime", reason="model says no",
    )
    assert not agent.ok and any(f.id == "GSDLC10A_AGENT_AUTHORITY_BLOCK" for f in agent.findings)


def test_07_owner_waiver_is_bounded_reasoned_and_expiry_blocks_later_approval(workspace: Path, runtime) -> None:
    app, _ = runtime
    source_plan = plan(app, KNOWN_PATH)
    test_plan = create_test_plan(app, source_plan)
    waivable = next(x for x in test_plan["required_tests"] if test_plan["test_policy"][x]["waivable"])
    waived = app.story_test_plan_decide(
        test_plan_id=test_plan["test_plan_id"], test_plan_hash=test_plan["test_plan_hash"], decision="WAIVE",
        actor="owner", actor_role="owner", reason="Temporary bounded waiver for non-sensitive P1 test.",
        waived_test_ids=[waivable], ttl_minutes=60,
    )
    assert waived.ok, waived.to_dict()
    projected = waived.data["story_test_plan"]
    assert waivable not in projected["effective_required_tests"]
    record_path = workspace / "outputs/story_execution/gsdlc_10_a" / workspace.name / "test_plans" / f"{test_plan['test_plan_id']}.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["waivers"][0]["expires_at_utc"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    expired = app.story_test_plan_decide(
        test_plan_id=test_plan["test_plan_id"], test_plan_hash=test_plan["test_plan_hash"], decision="APPROVE",
        actor="owner", actor_role="owner", reason="approve",
    )
    assert not expired.ok and any(f.id == "GSDLC10A_EXPIRED_WAIVER_BLOCK" for f in expired.findings)


def test_08_api_human_session_contract_and_story_plan_endpoints(workspace: Path, runtime, tmp_path: Path) -> None:
    from fastapi.testclient import TestClient
    from devpilot_core.application import AuthApplicationService
    from devpilot_core.interfaces.api.app import create_app

    _, store = runtime
    auth = AuthApplicationService(tmp_path / "auth10a-api", store=store)
    client = TestClient(create_app(ROOT, api_token="legacy-10a", auth_service=auth))
    response = client.post(
        "/api/v1/auth/bootstrap/owner",
        json={"username": "owner10a", "display_name": "Owner 10A", "password": PASSWORD},
        headers=ORIGIN,
    )
    assert response.status_code == 201, response.text
    app = ApplicationService(ROOT, approval_auth_store=store)
    source_plan = plan(app, KNOWN_PATH)
    csrf_headers = {"Origin": ORIGIN["Origin"], "X-DevPilot-CSRF": str(client.cookies.get("devpilot_csrf") or "")}
    created = client.post(
        f"/api/v1/story/code/change-plans/{source_plan['plan_id']}/test-plan",
        json={"plan_hash": source_plan["plan_hash"]}, headers=csrf_headers,
    )
    assert created.status_code == 200, created.text
    test_plan = created.json()["data"]["story_test_plan"]
    got = client.get(f"/api/v1/story/code/test-plans/{test_plan['test_plan_id']}", headers=ORIGIN)
    assert got.status_code == 200, got.text
    approved = client.post(
        f"/api/v1/story/code/test-plans/{test_plan['test_plan_id']}/decision",
        json={"test_plan_hash": test_plan["test_plan_hash"], "decision": "APPROVE", "reason": "Owner reviewed test plan."},
        headers=csrf_headers,
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["data"]["story_test_plan"]["status"] == "APPROVED"


def test_09_ui_static_contract_exposes_validate_explainability_and_no_free_form_test_command() -> None:
    text = (ROOT / "ui/web/src/pages/StoryCodeWorkbenchView.ts").read_text(encoding="utf-8")
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    for marker in ["Validar story", "StoryTestPlan", "Required tests", "Recommended tests", "unknown impact", "SENSITIVE", "informative only", "execution_authorized"]:
        assert marker in text
    for marker in ["restoreApplyContext", "listApprovals", "sessionStorage", "storySourceChangePlan", "story_execution_id", "APPLY_CONTEXT_SESSION_KEY", "armApprovalCenterArtifactReviewHandoff", "handoff=artifact-review", "Abrir Approval Center dirigido", "storyStatus", "CHANGES_READY", "SourceChangePlan restaurado para validación"]:
        assert marker in text
    assert "validateStory.disabled=!canAuthor||!plan||storyStatus!=='CHANGES_READY'" in text
    assert "validateStory.disabled=!canAuthor||!plan||!execution" not in text
    assert "new Set(['IN_PROGRESS','CHANGES_READY']).has(currentStatus)" in text
    assert "row?.metadata?.plan_hash" in text
    assert "boundHash!==String(candidate.plan_hash??'')" in text
    assert "requestApproval.disabled=!isOwner||!plan||storyStatus!=='IN_PROGRESS'" in text
    assert "apply.disabled=!isOwner||!plan||!approvalInput.value.trim()||storyStatus!=='IN_PROGRESS'" in text
    for marker in ["storyTestPlanCreate", "storyTestPlanDecision", "/test-plan", "/test-plans/"]:
        assert marker in client
    assert "test command" not in text.lower()
    assert "shell" not in text.lower() or "SIN TERMINAL" in text


def test_10_a_closed_and_current_successor_preserves_full_budget_zero() -> None:
    # HCA: 10-A closure is historical-freeze; current GSDLC-10 pointer is current-active.
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    assert state["gsdlc_current_backlog"] == "DEVPL-GSDLC-10"
    assert state["gsdlc_10_a_status"] == "CLOSED/PASS/WINDOWS-VALIDATED"
    assert state["gsdlc_10_b_status"].startswith("CLOSED/PASS/WINDOWS-VALIDATED")
    assert state["gsdlc_current_micro_sprint"] == "DEVPL-GSDLC-10-C"
    assert state["gsdlc_10_c_authorized"] is True
    assert state["gsdlc_10_status"].startswith("APPROVED/ACTIVE/GSDLC-10-C")
    assert state["gsdlc_10_a_full_regression_runs"] == 0
    assert state["gsdlc_10_a_full_regression_runs_allowed"] == 0
    assert state["gsdlc_10_c_full_regression_runs_allowed"] == 0
