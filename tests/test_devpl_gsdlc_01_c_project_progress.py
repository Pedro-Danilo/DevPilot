from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import jsonschema

from devpilot_core.application.guided_sdlc_service import GuidedSDLCApplicationService
from devpilot_core.application.services import ApplicationService
from devpilot_core.guided_sdlc import (
    EngineeringLifecycleStatus,
    MIPSoftwarePhase,
    ProjectProgressEngine,
    WorkspaceEngineeringState,
    WorkspaceEngineeringStateRepository,
    WorkflowEngine,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / ".devpilot/gsdlc/workflow_transition_catalog.json"
STATUS_SCHEMA = json.loads((ROOT / "docs/schemas/guided_sdlc_project_status.schema.json").read_text(encoding="utf-8"))
ACTION_SCHEMA = json.loads((ROOT / "docs/schemas/guided_sdlc_next_action.schema.json").read_text(encoding="utf-8"))
SNAPSHOTS = json.loads((ROOT / "tests/fixtures/gsdlc01c/project_status_snapshots.json").read_text(encoding="utf-8"))


def engine() -> WorkflowEngine:
    return WorkflowEngine.from_catalog_path(CATALOG)


def new_state() -> WorkspaceEngineeringState:
    return WorkspaceEngineeringState.new(
        workspace_id="ws-1",
        project_id="project-1",
        workspace_root_fingerprint="0" * 64,
        created_at_utc="2026-08-16T00:00:00Z",
    )


def state_for(phase: str, step: str, lifecycle: str = "IN_PROGRESS") -> WorkspaceEngineeringState:
    state = new_state()
    kwargs = {
        "phase": MIPSoftwarePhase(phase),
        "current_step": step,
        "lifecycle_status": EngineeringLifecycleStatus(lifecycle),
        "sequence": 1,
        "updated_at_utc": "2026-08-16T01:00:00Z",
    }
    if lifecycle == "REVALIDATION_REQUIRED":
        kwargs["revalidation"] = {"status": "REQUIRED", "reason_codes": ["external-drift"]}
    return replace(state, **kwargs)


def projection(state: WorkspaceEngineeringState, expected: str | None = None):
    return ProjectProgressEngine(engine()).project(
        state,
        observed_at_utc="2026-08-16T02:00:00Z",
        expected_state_fingerprint=expected,
    )


def make_platform(tmp_path: Path) -> tuple[Path, WorkspaceEngineeringStateRepository, WorkspaceEngineeringState]:
    platform = tmp_path / "platform"
    platform.mkdir()
    (platform / ".gitignore").write_text("outputs/\n", encoding="utf-8")
    registry_dir = platform / ".devpilot/workspaces"
    registry_dir.mkdir(parents=True)
    gsdlc_dir = platform / ".devpilot/gsdlc"
    gsdlc_dir.mkdir(parents=True)
    (gsdlc_dir / "workflow_transition_catalog.json").write_bytes(CATALOG.read_bytes())
    registry = {
        "schema_version": "1.0",
        "created_by": "DEVPL-GSDLC-01-C",
        "updated_at": "2026-08-16T00:00:00Z",
        "active_workspace_id": "ws-1",
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
        "workspaces": [{
            "workspace_id": "ws-1",
            "project_id": "project-1",
            "name": "Test",
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
    repo = WorkspaceEngineeringStateRepository(platform)
    binding = repo.binding("ws-1")
    state = WorkspaceEngineeringState.new(
        workspace_id="ws-1",
        project_id=binding.project_id,
        workspace_root_fingerprint=binding.root_fingerprint,
        created_at_utc="2026-08-16T00:00:00Z",
    )
    repo.save(state)
    return platform, repo, state


def test_01_c_status_and_next_action_schemas_accept_deterministic_projection():
    p = projection(new_state())
    jsonschema.Draft202012Validator(STATUS_SCHEMA).validate(p.status.to_payload())
    jsonschema.Draft202012Validator(ACTION_SCHEMA).validate(p.next_action.to_payload())
    assert p.status.next_action_ref == p.next_action.action_id
    assert p.status.model_budget["status"] == "NOT_AVAILABLE"
    assert p.status.model_budget["reason_code"] == "GSDLC_06_NOT_IMPLEMENTED"
    assert p.status.miasi["status"] == "UNKNOWN"
    assert p.status.quality["status"] == "NOT_EVALUATED"


def test_01_c_progress_is_monotonic_bounded_and_terminal_is_100_percent():
    values = []
    phases = tuple(MIPSoftwarePhase)
    for index, phase in enumerate(phases):
        lifecycle = EngineeringLifecycleStatus.NEW if phase == MIPSoftwarePhase.NOT_STARTED else EngineeringLifecycleStatus.IN_PROGRESS
        if phase == MIPSoftwarePhase.RETIREMENT:
            lifecycle = EngineeringLifecycleStatus.RELEASED
        state = replace(
            new_state(),
            phase=phase,
            current_step="idea-intake" if phase == MIPSoftwarePhase.NOT_STARTED else phase.value.lower().replace("_", "-"),
            lifecycle_status=lifecycle,
            sequence=index,
        )
        values.append(projection(state).status.progress["percent"])
    assert values == sorted(values)
    assert values[0] == 0.0
    assert values[-1] == 100.0
    assert all(0.0 <= value <= 100.0 for value in values)


def test_01_c_semantic_snapshots_cover_new_gate_revalidation_and_terminal():
    for case in SNAPSHOTS["cases"]:
        raw = case["state"]
        state = state_for(raw["phase"], raw["current_step"], raw["lifecycle_status"]) if raw["phase"] != "NOT_STARTED" else new_state()
        p = projection(state)
        expected = case["expected"]
        if "progress_percent" in expected:
            assert p.status.progress["percent"] == expected["progress_percent"]
        assert p.next_action.kind == expected["next_kind"]
        assert p.next_action.reason_code == expected["reason_code"]


def test_01_c_blocker_order_is_stable_and_drives_next_action():
    state = replace(
        new_state(),
        blockers=(
            {"priority": 30, "code": "Z_BLOCK", "category": "artifact", "subject": "z", "message": "z"},
            {"priority": 10, "code": "A_BLOCK", "category": "policy", "subject": "a", "message": "a"},
        ),
    )
    first = projection(state)
    second = projection(state)
    assert [row["code"] for row in first.status.blockers] == ["A_BLOCK", "Z_BLOCK"]
    assert first.next_action.kind == "RESOLVE_BLOCKER"
    assert first.next_action.reason_code == "A_BLOCK"
    assert first.to_payload() == second.to_payload()


def test_01_c_revalidation_dominates_blockers_approvals_and_transition():
    state = state_for("REQUIREMENTS", "requirements", "REVALIDATION_REQUIRED")
    state = replace(
        state,
        blockers=({"priority": 1, "code": "OTHER", "category": "state", "subject": "x", "message": "other"},),
        planning=({"item_id": "plan-1", "status": "APPROVAL_REQUIRED", "approval_ref": "approval-1", "approval_status": "PENDING"},),
    )
    action = projection(state).next_action
    assert action.kind == "REVALIDATE"
    assert action.priority < 30
    assert action.available is False
    assert "GSDLC_01_D" in (action.disabled_reason or "")


def test_01_c_gate_block_dominates_pending_approval():
    state = state_for("INTAKE", "intake")
    state = replace(
        state,
        gates=({"gate_id": "gate:intake:exit", "status": "BLOCK"},),
        planning=({"item_id": "plan-1", "status": "APPROVAL_REQUIRED", "approval_ref": "approval-1", "approval_status": "PENDING"},),
    )
    action = projection(state).next_action
    assert action.kind == "RESOLVE_BLOCKER"
    assert action.reason_code == "GATE_BLOCK"


def test_01_c_pending_approval_priority_and_existing_approval_navigation():
    state = replace(
        new_state(),
        planning=({"item_id": "plan-1", "status": "APPROVAL_REQUIRED", "approval_ref": "approval-1", "approval_status": "PENDING"},),
    )
    action = projection(state).next_action
    assert action.kind == "OBTAIN_APPROVAL"
    assert action.approval_needed is True
    assert action.navigation_target == "ui.approvals"
    assert action.available is True
    assert action.executes_action is False if hasattr(action, "executes_action") else action.to_payload()["executes_action"] is False


def test_01_c_artifact_work_precedes_nominal_transition():
    state = replace(
        new_state(),
        artifacts=({"artifact_id": "idea-intake", "status": "DRAFT"},),
    )
    action = projection(state).next_action
    assert action.kind == "CONTINUE_STEP"
    assert action.reason_code == "ARTIFACT_WORK_PENDING"
    assert action.available is False


def test_01_c_gate_pass_makes_phase_complete_prerequisite_deterministically_true():
    state = state_for("INTAKE", "intake")
    state = replace(state, gates=({"gate_id": "gate:intake:exit", "status": "PASS"},))
    action = projection(state).next_action
    assert action.kind == "ADVANCE_TRANSITION"
    assert action.transition_id == "gsdlc.phase.intake.problem-discovery"
    assert action.target_phase == "PROBLEM_DISCOVERY"
    assert action.available is True


def test_01_c_unknown_state_is_explicit_and_never_fabricates_pass(tmp_path):
    platform, repo, _ = make_platform(tmp_path)
    repo.state_path("ws-1").write_text('{"schema_id":', encoding="utf-8")
    app = GuidedSDLCApplicationService(platform)
    result = app.project_status(workspace_id="ws-1", observed_at_utc="2026-08-16T02:00:00Z")
    assert result.ok is False
    assert result.data["reason"] == "unknown"
    assert result.data["phase"] == "UNKNOWN"
    assert result.data["quality"]["status"] == "UNKNOWN"
    assert result.data["model_budget"]["status"] == "NOT_AVAILABLE"


def test_01_c_freshness_uses_fingerprint_not_wall_clock_age():
    state = new_state()
    fp = state.fingerprint()
    fresh = projection(state, fp).status.freshness
    stale = projection(state, "f" * 64).status.freshness
    current = projection(state).status.freshness
    assert fresh["status"] == "FRESH"
    assert fresh["reason_code"] == "STATE_FINGERPRINT_MATCH"
    assert stale["status"] == "STALE"
    assert stale["reason_code"] == "STATE_FINGERPRINT_MISMATCH"
    assert current["status"] == "FRESH"
    assert current["reason_code"] == "COMPUTED_FROM_CURRENT_LOADED_STATE"


def test_01_c_status_is_read_only_and_restart_stable(tmp_path):
    platform, repo, state = make_platform(tmp_path)
    before = repo.state_path("ws-1").read_bytes()
    service = GuidedSDLCApplicationService(platform)
    first = service.project_status(workspace_id="ws-1", observed_at_utc="2026-08-16T02:00:00Z")
    second = service.project_status(workspace_id="ws-1", observed_at_utc="2026-08-16T02:00:00Z")
    after = repo.state_path("ws-1").read_bytes()
    assert first.ok is True
    assert first.data == second.data
    assert before == after
    assert WorkspaceEngineeringStateRepository(platform).load("ws-1").to_payload() == state.to_payload()


def test_01_c_application_boundary_adds_read_only_operations_but_no_http_route(tmp_path):
    platform, _, _ = make_platform(tmp_path)
    app = ApplicationService(platform)
    status = app.guided_sdlc_project_status(workspace_id="ws-1", observed_at_utc="2026-08-16T02:00:00Z")
    action = app.guided_sdlc_next_action(workspace_id="ws-1", observed_at_utc="2026-08-16T02:00:00Z")
    assert status.ok is True and action.ok is True

    contract = ApplicationService(ROOT).application_contract().to_dict()["data"]
    operations = {row["operation"] for row in contract["capabilities"]}
    routes = {row["operation"] for row in contract["routes"]}
    assert {"guided_sdlc.project.status", "guided_sdlc.next_action"}.issubset(operations)
    assert "guided_sdlc.project.status" not in routes
    assert "guided_sdlc.next_action" not in routes


def test_01_c_outputs_do_not_expose_runtime_payload_or_secret_values():
    state = replace(
        new_state(),
        git={"head": "a" * 40, "branch": "main", "dirty": False, "fingerprint": "b" * 64, "ignored_runtime": "must-not-leak"},
        quality=({"quality_id": "q1", "status": "PASS", "job_id": "runtime-job-must-not-leak"},),
    )
    raw = json.dumps(projection(state).to_payload(), sort_keys=True)
    assert "ignored_runtime" not in raw
    assert "runtime-job-must-not-leak" not in raw
    assert "Bearer " not in raw
    assert "sk-" not in raw


def test_01_c_terminal_release_has_no_fake_followup():
    state = state_for("RETIREMENT", "retirement", "RELEASED")
    p = projection(state)
    assert p.status.progress["terminal"] is True
    assert p.status.progress["percent"] == 100.0
    assert p.next_action.kind == "COMPLETE"
    assert p.next_action.mutating is False
    assert p.next_action.transition_id is None
