from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import jsonschema
import pytest

from devpilot_core.application.guided_sdlc_service import GuidedSDLCApplicationService
from devpilot_core.application.services import ApplicationService
from devpilot_core.guided_sdlc import (
    EngineeringLifecycleStatus,
    GuidedSDLCService,
    MIPSoftwarePhase,
    TransitionCatalog,
    TransitionEvidence,
    TransitionSpec,
    WorkflowEngine,
    WorkflowEngineError,
    WorkspaceEngineeringState,
    WorkspaceEngineeringStateRepository,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / ".devpilot/gsdlc/workflow_transition_catalog.json"
CATALOG_SCHEMA = json.loads((ROOT / "docs/schemas/guided_sdlc_transition_catalog.schema.json").read_text(encoding="utf-8"))
REPORT_SCHEMA = json.loads((ROOT / "docs/schemas/guided_sdlc_transition_report.schema.json").read_text(encoding="utf-8"))
CASES = json.loads((ROOT / "tests/fixtures/gsdlc01b/transition_eval_cases.json").read_text(encoding="utf-8"))


def make_platform(tmp_path: Path) -> tuple[Path, WorkspaceEngineeringStateRepository, WorkspaceEngineeringState]:
    platform = tmp_path / "platform"
    platform.mkdir()
    (platform / ".gitignore").write_text("outputs/\n", encoding="utf-8")
    registry_dir = platform / ".devpilot/workspaces"
    registry_dir.mkdir(parents=True)
    gsdlc_dir = platform / ".devpilot/gsdlc"
    gsdlc_dir.mkdir(parents=True)
    (gsdlc_dir / "workflow_transition_catalog.json").write_bytes(CATALOG_PATH.read_bytes())
    entry = {
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
    }
    registry = {
        "schema_version": "1.0",
        "created_by": "DEVPL-GSDLC-01-B",
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
        "workspaces": [entry],
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


def engine() -> WorkflowEngine:
    return WorkflowEngine.from_catalog_path(CATALOG_PATH)


def state_for_phase(state: WorkspaceEngineeringState, phase: str, step: str, *, sequence: int = 1):
    return replace(
        state,
        lifecycle_status=EngineeringLifecycleStatus.IN_PROGRESS,
        phase=MIPSoftwarePhase(phase),
        current_step=step,
        sequence=sequence,
        updated_at_utc="2026-08-16T01:00:00Z",
    )


def test_01_b_catalog_schema_and_transition_ids_are_unique_and_complete():
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(CATALOG_SCHEMA).validate(payload)
    ids = [row["transition_id"] for row in payload["transitions"]]
    assert len(ids) == 26
    assert len(ids) == len(set(ids))
    assert ids[0] == "gsdlc.phase.start-intake"
    assert payload["scope"].startswith("generic sequential phase transitions")
    assert "DEVPL-GSDLC-05" in payload["scope"]


def test_01_b_start_intake_passes_without_llm_or_side_effects(tmp_path):
    _, _, state = make_platform(tmp_path)
    result = engine().evaluate(state, "gsdlc.phase.start-intake", {})
    jsonschema.Draft202012Validator(REPORT_SCHEMA).validate(result.to_payload())
    assert result.allowed is True
    assert result.reason_codes == ("TRANSITION_ALLOWED",)
    assert result.blockers == ()
    assert result.to_payload()["network_used"] is False
    assert result.to_payload()["external_api_used"] is False
    assert result.to_payload()["source_mutations_performed"] is False


def test_01_b_required_prerequisite_and_gate_are_fail_closed(tmp_path):
    _, _, base = make_platform(tmp_path)
    state = state_for_phase(base, "INTAKE", "intake")
    transition = "gsdlc.phase.intake.problem-discovery"

    missing = engine().evaluate(state, transition, {})
    assert missing.decision == "BLOCK"
    assert "PREREQUISITE_NOT_SATISFIED" in missing.reason_codes
    assert "GATE_NOT_SATISFIED" in missing.reason_codes

    prereq_only = engine().evaluate(
        state,
        transition,
        {"prerequisites": {"phase:intake:complete": True}},
    )
    assert prereq_only.decision == "BLOCK"
    assert "GATE_NOT_SATISFIED" in prereq_only.reason_codes

    allowed = engine().evaluate(
        state,
        transition,
        {
            "prerequisites": {"phase:intake:complete": True},
            "gates": {"gate:intake:exit": "PASS"},
        },
    )
    assert allowed.decision == "PASS"


def test_01_b_gate_warn_and_block_behavior_is_contract_driven(tmp_path):
    _, _, base = make_platform(tmp_path)
    state = state_for_phase(base, "INTAKE", "intake")
    transition = "gsdlc.phase.intake.problem-discovery"
    warn_default = engine().evaluate(
        state,
        transition,
        {
            "prerequisites": {"phase:intake:complete": True},
            "gates": {"gate:intake:exit": "WARN"},
        },
    )
    assert warn_default.decision == "BLOCK"
    assert "GATE_NOT_SATISFIED" in warn_default.reason_codes

    payload = {
        "schema_id": "SCHEMA-DEVPL-GUIDED-SDLC-TRANSITION-CATALOG-V1",
        "schema_version": "1.0",
        "catalog_id": "TEST",
        "catalog_version": "1.0.0",
        "transitions": [{
            "transition_id": "test.warn",
            "version": "1.0.0",
            "source": {"phase": "INTAKE", "current_step": "intake", "lifecycle_statuses": ["IN_PROGRESS"]},
            "target": {"phase": "PROBLEM_DISCOVERY", "current_step": "problem-discovery", "lifecycle_status": "IN_PROGRESS"},
            "required_prerequisites": [],
            "required_gates": [{"gate_id": "gate:test", "accepted_statuses": ["PASS", "WARN"]}],
            "required_artifacts": [],
            "approval": {"required": False, "approval_key": None, "accepted_statuses": []},
            "risk_classification": "low",
            "preview_allowed": True,
            "evidence_refs": ["test"],
        }],
    }
    custom = WorkflowEngine(TransitionCatalog.from_payload(payload))
    warn_allowed = custom.evaluate(state, "test.warn", {"gates": {"gate:test": "WARN"}})
    assert warn_allowed.decision == "PASS"
    assert warn_allowed.warnings == ("GATE_WARN:gate:test",)
    assert "GATE_WARN_ACCEPTED" in warn_allowed.reason_codes

    block = custom.evaluate(state, "test.warn", {"gates": {"gate:test": "BLOCK"}})
    assert block.decision == "BLOCK"
    assert "GATE_BLOCK" in block.reason_codes


def test_01_b_unknown_transition_illegal_skip_and_source_mismatch_block(tmp_path):
    _, _, state = make_platform(tmp_path)
    unknown = engine().evaluate(state, "gsdlc.phase.does-not-exist", {})
    assert unknown.decision == "BLOCK"
    assert unknown.reason_codes == ("TRANSITION_UNKNOWN",)

    skip = engine().evaluate(
        state,
        "gsdlc.phase.requirements.risk-analysis",
        {
            "prerequisites": {"phase:requirements:complete": True},
            "gates": {"gate:requirements:exit": "PASS"},
        },
    )
    assert skip.decision == "BLOCK"
    assert "SOURCE_PHASE_MISMATCH" in skip.reason_codes
    assert "SOURCE_STEP_MISMATCH" in skip.reason_codes


def test_01_b_revalidation_and_blocked_lifecycle_preempt_nominal_transition(tmp_path):
    _, _, base = make_platform(tmp_path)
    revalidation = replace(
        state_for_phase(base, "INTAKE", "intake"),
        lifecycle_status=EngineeringLifecycleStatus.REVALIDATION_REQUIRED,
        revalidation={"status": "REQUIRED", "reason_codes": ["EXTERNAL_DRIFT"]},
    )
    ev = {"prerequisites": {"phase:intake:complete": True}, "gates": {"gate:intake:exit": "PASS"}}
    result = engine().evaluate(revalidation, "gsdlc.phase.intake.problem-discovery", ev)
    assert result.decision == "BLOCK"
    assert "STATE_REVALIDATION_REQUIRED" in result.reason_codes

    blocked = replace(
        state_for_phase(base, "INTAKE", "intake"),
        lifecycle_status=EngineeringLifecycleStatus.BLOCKED,
    )
    result2 = engine().evaluate(blocked, "gsdlc.phase.intake.problem-discovery", ev)
    assert result2.decision == "BLOCK"
    assert "STATE_BLOCKED" in result2.reason_codes


def test_01_b_approval_and_artifact_requirements_supported_deterministically(tmp_path):
    _, _, base = make_platform(tmp_path)
    state = state_for_phase(base, "INTAKE", "intake")
    payload = {
        "schema_id": "SCHEMA-DEVPL-GUIDED-SDLC-TRANSITION-CATALOG-V1",
        "schema_version": "1.0",
        "catalog_id": "TEST-AUTHORITY",
        "catalog_version": "1.0.0",
        "transitions": [{
            "transition_id": "test.authority",
            "version": "1.0.0",
            "source": {"phase": "INTAKE", "current_step": "intake", "lifecycle_statuses": ["IN_PROGRESS"]},
            "target": {"phase": "PROBLEM_DISCOVERY", "current_step": "problem-discovery", "lifecycle_status": "IN_PROGRESS"},
            "required_prerequisites": [],
            "required_gates": [],
            "required_artifacts": [{"artifact_id": "idea_intake", "accepted_statuses": ["APPROVED", "FROZEN"]}],
            "approval": {"required": True, "approval_key": "approval:intake", "accepted_statuses": ["APPROVED"]},
            "risk_classification": "medium",
            "preview_allowed": True,
            "evidence_refs": [],
        }],
    }
    custom = WorkflowEngine(TransitionCatalog.from_payload(payload))
    blocked = custom.evaluate(state, "test.authority", {"artifacts": {"idea_intake": "DRAFT"}})
    assert blocked.decision == "BLOCK"
    assert "ARTIFACT_NOT_READY" in blocked.reason_codes
    assert "APPROVAL_REQUIRED" in blocked.reason_codes

    allowed = custom.evaluate(
        state,
        "test.authority",
        {"artifacts": {"idea_intake": "APPROVED"}, "approvals": {"approval:intake": "APPROVED"}},
    )
    assert allowed.decision == "PASS"


def test_01_b_evaluate_and_preview_are_idempotent_and_do_not_mutate_input(tmp_path):
    _, _, state = make_platform(tmp_path)
    before = state.to_payload()
    ev = {}
    first = engine().evaluate(state, "gsdlc.phase.start-intake", ev)
    second = engine().evaluate(state, "gsdlc.phase.start-intake", ev)
    assert first.to_payload() == second.to_payload()
    assert first.fingerprint() == second.fingerprint()

    p1 = engine().preview_advance(
        state, "gsdlc.phase.start-intake", ev, updated_at_utc="2026-08-16T02:00:00Z"
    )
    p2 = engine().preview_advance(
        state, "gsdlc.phase.start-intake", ev, updated_at_utc="2026-08-16T02:00:00Z"
    )
    assert p1.to_payload() == p2.to_payload()
    assert p1.successor_state is not None
    assert p1.successor_state.phase == MIPSoftwarePhase.INTAKE
    assert p1.successor_state.sequence == state.sequence + 1
    assert state.to_payload() == before


def test_01_b_blocker_order_and_reason_codes_are_stable(tmp_path):
    _, _, base = make_platform(tmp_path)
    state = state_for_phase(base, "INTAKE", "wrong-step")
    a = engine().evaluate(state, "gsdlc.phase.intake.problem-discovery", {})
    b = engine().evaluate(state, "gsdlc.phase.intake.problem-discovery", {})
    assert a.reason_codes == b.reason_codes
    assert [x.to_payload() for x in a.blockers] == [x.to_payload() for x in b.blockers]
    assert [x.priority for x in a.blockers] == sorted(x.priority for x in a.blockers)


def test_01_b_model_or_agent_authority_field_is_rejected():
    with pytest.raises(WorkflowEngineError, match="unexpected transition evidence fields"):
        TransitionEvidence.from_payload({"model_decision": "PASS"})
    with pytest.raises(WorkflowEngineError, match="unexpected transition evidence fields"):
        TransitionEvidence.from_payload({"agent_decision": "PASS"})


def test_01_b_secret_like_transition_evidence_is_rejected():
    with pytest.raises(WorkflowEngineError, match="secret-like material"):
        TransitionEvidence.from_payload({"references": ["Bearer super-secret-token-12345"]})


def test_01_b_guided_service_preview_does_not_persist(tmp_path):
    platform, repo, state = make_platform(tmp_path)
    service = GuidedSDLCService.from_platform_root(platform)
    preview = service.preview_transition(
        workspace_id="ws-1",
        transition_id="gsdlc.phase.start-intake",
        evidence={},
        updated_at_utc="2026-08-16T03:00:00Z",
    )
    assert preview.successor_state is not None
    reloaded = repo.load("ws-1")
    assert reloaded.to_payload() == state.to_payload()


def test_01_b_application_boundary_exposes_read_only_operations_but_no_http_route(tmp_path):
    platform, _, _ = make_platform(tmp_path)
    app = GuidedSDLCApplicationService(platform)
    result = app.evaluate_transition(
        workspace_id="ws-1", transition_id="gsdlc.phase.start-intake", evidence={}
    )
    assert result.ok is True
    assert result.exit_code.value == 0

    contract = ApplicationService(ROOT).application_contract().to_dict()["data"]
    operations = {row["operation"] for row in contract["capabilities"]}
    routes = {row["operation"] for row in contract["routes"]}
    assert "guided_sdlc.transition.evaluate" in operations
    assert "guided_sdlc.transition.preview" in operations
    assert "guided_sdlc.transition.evaluate" not in routes
    assert "guided_sdlc.transition.preview" not in routes


def test_01_b_transition_case_fixture_is_complete_and_machine_readable(tmp_path):
    _, _, base = make_platform(tmp_path)
    eng = engine()
    observed = []
    for case in CASES["cases"]:
        state = base
        if case["state"].get("phase"):
            state = state_for_phase(
                base,
                case["state"]["phase"],
                case["state"]["current_step"],
                sequence=case["state"].get("sequence", 1),
            )
        if case["state"].get("lifecycle_status") == "REVALIDATION_REQUIRED":
            state = replace(
                state,
                lifecycle_status=EngineeringLifecycleStatus.REVALIDATION_REQUIRED,
                revalidation={"status": "REQUIRED", "reason_codes": ["fixture"]},
            )
        result = eng.evaluate(state, case["transition_id"], case.get("evidence") or {})
        observed.append((case["case_id"], result.decision, list(result.reason_codes)))
        assert result.decision == case["expected_decision"]
        for code in case.get("expected_reason_codes", []):
            assert code in result.reason_codes
    assert len(observed) == CASES["cases_total"]


def test_01_b_transition_matrix_coverage_report_matches_catalog():
    report = json.loads((ROOT / "docs/audits/DEVPL_GSDLC_01_B_TRANSITION_MATRIX_COVERAGE.json").read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    assert report["catalog_transitions_total"] == len(catalog["transitions"]) == 26
    assert report["nominal_mipsoftware_phase_edges_covered"] == 26
    assert report["llm_transition_authority"] is False
    assert report["source_mutation_by_engine"] is False
