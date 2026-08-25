from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import jsonschema
import pytest

from devpilot_core.guided_sdlc import (
    EngineeringLifecycleStatus,
    MIPGateEvaluator,
    MIPProgressModel,
    MIPWaiver,
    MIPWorkflowRegistry,
    MIPWorkflowRegistryError,
    WorkspaceEngineeringState,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / ".devpilot/gsdlc/mip_workflow_registry.json"
SCHEMA = ROOT / "docs/schemas/mip_workflow_registry.schema.json"


def registry_payload() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def state_for(registry: MIPWorkflowRegistry, phase_name: str) -> WorkspaceEngineeringState:
    phase = registry.by_phase[phase_name]
    if phase["terminal_in_registry"]:
        lifecycle = EngineeringLifecycleStatus.READY_FOR_RELEASE
    else:
        spec = registry.enriched_transition_catalog().get(phase["transition_id"])
        assert spec is not None
        lifecycle = spec.source_lifecycle_statuses[0]
    base = WorkspaceEngineeringState.new(
        workspace_id="workspace-test",
        project_id="project-test",
        workspace_root_fingerprint="0" * 64,
        created_at_utc="2026-08-24T12:00:00+00:00",
    )
    return replace(
        base,
        phase=__import__("devpilot_core.guided_sdlc", fromlist=["MIPSoftwarePhase"]).MIPSoftwarePhase(phase_name),
        current_step=phase["current_step"],
        lifecycle_status=lifecycle,
    )


def passing_evidence(phase: dict) -> dict:
    return {
        "prerequisites": {key: True for key in phase["required_prerequisites"]},
        "gates": {phase["exit_gate"]["gate_id"]: "PASS"},
        "artifacts": {row["artifact_id"]: "FROZEN" for row in phase["required_artifacts"]},
        "approvals": {},
        "references": ["test:deterministic"],
    }


def test_05_b_schema_registry_and_coverage_pass():
    data = registry_payload()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(data)
    registry = MIPWorkflowRegistry(ROOT)
    coverage = registry.coverage_report()
    assert coverage["status"] == "PASS"
    assert coverage["phases_total"] == 19
    assert coverage["transitions_total"] == 18
    assert coverage["required_phases_skippable_without_gate"] == 0
    assert coverage["weights_total_bps"] == 10000
    assert coverage["llm_authority"] is False
    assert coverage["production_waivable_gate_ids"] == []


def test_05_b_nominal_transition_reuses_workspace_state_and_existing_engine():
    registry = MIPWorkflowRegistry(ROOT)
    evaluator = MIPGateEvaluator(registry)
    state = state_for(registry, "INTAKE")
    phase = registry.by_phase["INTAKE"]
    result = evaluator.evaluate(state, passing_evidence(phase))
    assert result.decision == "PASS", result.to_dict()
    assert result.transition_id == "gsdlc.phase.intake.problem-discovery"
    preview = evaluator.preview_advance(state, passing_evidence(phase), updated_at_utc="2026-08-24T12:01:00+00:00")
    assert preview is not None and preview.successor_state is not None
    assert preview.successor_state.phase.value == "PROBLEM_DISCOVERY"
    assert preview.successor_state.sequence == state.sequence + 1


def test_05_b_required_phase_cannot_be_skipped():
    registry = MIPWorkflowRegistry(ROOT)
    evaluator = MIPGateEvaluator(registry)
    state = state_for(registry, "INTAKE")
    phase = registry.by_phase["INTAKE"]
    result = evaluator.evaluate(
        state,
        passing_evidence(phase),
        transition_id="gsdlc.phase.problem-discovery.business-analysis",
    )
    assert result.decision == "BLOCK"
    assert {b["code"] for b in result.blockers} == {"MIP_REQUIRED_PHASE_SKIP"}


def test_05_b_gate_missing_and_block_are_explainable_with_remediation():
    registry = MIPWorkflowRegistry(ROOT)
    evaluator = MIPGateEvaluator(registry)
    state = state_for(registry, "REQUIREMENTS")
    phase = registry.by_phase["REQUIREMENTS"]
    ev = passing_evidence(phase)
    ev["gates"] = {}
    result = evaluator.evaluate(state, ev)
    assert result.decision == "BLOCK"
    assert "GATE_NOT_SATISFIED" in {b["code"] for b in result.blockers}
    assert "RESOLVE_GATE" in {a["kind"] for a in result.remediation_actions}

    ev = passing_evidence(phase)
    ev["gates"][phase["exit_gate"]["gate_id"]] = "BLOCK"
    result = evaluator.evaluate(state, ev)
    assert "GATE_BLOCK" in {b["code"] for b in result.blockers}


def test_05_b_artifact_missing_or_not_ready_blocks():
    registry = MIPWorkflowRegistry(ROOT)
    evaluator = MIPGateEvaluator(registry)
    state = state_for(registry, "BUSINESS_ANALYSIS")
    phase = registry.by_phase["BUSINESS_ANALYSIS"]
    ev = passing_evidence(phase)
    victim = phase["required_artifacts"][0]["artifact_id"]
    del ev["artifacts"][victim]
    result = evaluator.evaluate(state, ev)
    assert result.decision == "BLOCK"
    assert victim in {b["subject"] for b in result.blockers if b["code"] == "ARTIFACT_NOT_READY"}
    assert "COMPLETE_OR_APPROVE_ARTIFACT" in {a["kind"] for a in result.remediation_actions}


def test_05_b_production_policy_denies_owner_bypass_even_with_typed_waiver():
    registry = MIPWorkflowRegistry(ROOT)
    evaluator = MIPGateEvaluator(registry)
    state = state_for(registry, "INTAKE")
    phase = registry.by_phase["INTAKE"]
    ev = passing_evidence(phase)
    ev["gates"] = {}
    waiver = MIPWaiver(
        waiver_id="w-001",
        workspace_id=state.workspace_id,
        transition_id=phase["transition_id"],
        gate_id=phase["exit_gate"]["gate_id"],
        owner="owner.local",
        rationale="test",
        issued_at_utc="2026-08-24T11:00:00+00:00",
        expires_at_utc="2026-08-25T11:00:00+00:00",
        policy_ref="policy:test",
        audit_ref="audit:test",
    )
    result = evaluator.evaluate(state, ev, waiver=waiver, observed_at_utc="2026-08-24T12:00:00+00:00")
    assert result.decision == "BLOCK"
    assert result.waiver["reason"] == "WAIVER_POLICY_DENY"
    assert result.waiver["applied"] is False


def test_05_b_typed_waiver_only_works_when_successor_policy_explicitly_allows_gate():
    data = registry_payload()
    gate_id = data["phases"][0]["exit_gate"]["gate_id"]
    data["phases"][0]["exit_gate"]["waiver_allowed"] = True
    data["waiver_policy"]["production_waivable_gate_ids"] = [gate_id]
    registry = MIPWorkflowRegistry(ROOT, data)
    evaluator = MIPGateEvaluator(registry)
    state = state_for(registry, "INTAKE")
    phase = registry.by_phase["INTAKE"]
    ev = passing_evidence(phase)
    ev["gates"] = {}
    base = {
        "waiver_id": "w-allowed",
        "workspace_id": state.workspace_id,
        "transition_id": phase["transition_id"],
        "gate_id": gate_id,
        "owner": "owner.local",
        "rationale": "bounded successor policy fixture",
        "issued_at_utc": "2026-08-24T11:00:00+00:00",
        "expires_at_utc": "2026-08-25T11:00:00+00:00",
        "policy_ref": "policy:successor-test",
        "audit_ref": "audit:w-allowed",
    }
    result = evaluator.evaluate(state, ev, waiver=base, observed_at_utc="2026-08-24T12:00:00+00:00")
    assert result.decision == "PASS", result.to_dict()
    assert result.waiver["applied"] is True

    expired = dict(base, expires_at_utc="2026-08-24T11:30:00+00:00")
    assert evaluator.evaluate(state, ev, waiver=expired, observed_at_utc="2026-08-24T12:00:00+00:00").decision == "BLOCK"
    wrong_scope = dict(base, gate_id="gate:other:exit")
    assert evaluator.evaluate(state, ev, waiver=wrong_scope, observed_at_utc="2026-08-24T12:00:00+00:00").decision == "BLOCK"
    wrong_workspace = dict(base, workspace_id="workspace-other")
    assert evaluator.evaluate(state, ev, waiver=wrong_workspace, observed_at_utc="2026-08-24T12:00:00+00:00").decision == "BLOCK"


def test_05_b_cycle_detection_is_fail_closed():
    data = registry_payload()
    data["phases"][0]["next_phase"] = "INTAKE"
    with pytest.raises(MIPWorkflowRegistryError, match="cycle"):
        MIPWorkflowRegistry(ROOT, data)


def test_05_b_progress_is_registry_weighted_deterministic_and_stable():
    registry = MIPWorkflowRegistry(ROOT)
    model = MIPProgressModel(registry)
    req = state_for(registry, "REQUIREMENTS")
    first = model.project(req)
    second = model.project(req)
    assert first == second
    assert first["status"] == "PASS"
    assert first["completed_bps"] == sum(x["weight_bps"] for x in registry.phases[:4])
    assert first["policy_id"] == "equal-phase-bps-v1"

    release = state_for(registry, "RELEASE")
    final = model.project(release)
    assert final["terminal"] is True
    assert final["completed_bps"] == 10000
    assert final["percent"] == 100.0


def test_05_b_predecessor_registry_must_be_owner_approved(tmp_path: Path):
    # The current repo is approved. A synthetic predecessor downgrade must fail closed.
    data = registry_payload()
    pred = ROOT / ".devpilot/gsdlc/executable_standard_registry.json"
    original = json.loads(pred.read_text(encoding="utf-8"))
    downgraded = copy.deepcopy(original)
    downgraded["status"] = "draft/pending-owner-approval"
    downgraded["registry_authoritative"] = False
    # Point at a temporary copy through a relative repo-local path.
    temp = ROOT / ".devpilot/gsdlc/_test_unapproved_registry.json"
    try:
        temp.write_text(json.dumps(downgraded), encoding="utf-8")
        data["predecessor_registry"]["path"] = ".devpilot/gsdlc/_test_unapproved_registry.json"
        with pytest.raises(MIPWorkflowRegistryError, match="owner-approved"):
            MIPWorkflowRegistry(ROOT, data)
    finally:
        temp.unlink(missing_ok=True)


def test_05_b_evaluation_never_uses_llm_network_or_external_api_authority():
    registry = MIPWorkflowRegistry(ROOT)
    evaluator = MIPGateEvaluator(registry)
    state = state_for(registry, "ARCHITECTURE")
    result = evaluator.evaluate(state, passing_evidence(registry.by_phase["ARCHITECTURE"]))
    payload = result.to_dict()
    assert payload["network_used"] is False
    assert payload["external_api_used"] is False
    assert payload["model_execution_used"] is False
    assert registry.payload["safety"]["llm_decides_gates"] is False
