from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import jsonschema
import pytest

from devpilot_core.planning import (
    Dependency, Epic, Milestone, PlanningLifecycle, PlanningPolicyError, PlanningState, PlanningStateService,
    Sprint, Story, TraceKind, TraceLink,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "docs/schemas"
KNOWN = {("requirement", "REQ-001"), ("risk", "RISK-001"), ("adr", "ADR-001"), ("test-intent", "TEST-001")}


def good_state() -> PlanningState:
    return PlanningState(
        planning_id="planning-demo", version="1.0.0",
        milestones=(Milestone(id="mil-foundation", version="1.0.0", title="Foundation", owner_role="product-owner", outcome="Planning ready", exit_criteria=("scope approved",), trace_links=(TraceLink(TraceKind.REQUIREMENT, "REQ-001"),)),),
        epics=(Epic(id="epic-roadmap", version="1.0.0", title="Roadmap", owner_role="product-owner", milestone_id="mil-foundation", trace_links=(TraceLink(TraceKind.RISK, "RISK-001"),)),),
        stories=(Story(id="story-traceability", version="1.0.0", title="Trace planning", owner_role="developer", epic_id="epic-roadmap", acceptance_criteria=("Requirement is mapped",), trace_links=(TraceLink(TraceKind.REQUIREMENT, "REQ-001"), TraceLink(TraceKind.TEST_INTENT, "TEST-001"))),),
        sprints=(Sprint(id="sprint-one", version="1.0.0", title="Sprint 1", owner_role="product-owner", story_ids=("story-traceability",), capacity=8, trace_links=(TraceLink(TraceKind.ADR, "ADR-001"),)),),
        dependencies=(Dependency(id="dep-roadmap-story", predecessor_id="epic-roadmap", successor_id="story-traceability", rationale="Story follows epic"),),
    )


def test_08_a_all_six_planning_schemas_validate_representative_payloads():
    state = good_state()
    payloads = {
        "planning_milestone.schema.json": state.milestones[0].to_dict(),
        "planning_epic.schema.json": state.epics[0].to_dict(),
        "planning_story.schema.json": state.stories[0].to_dict(),
        "planning_sprint.schema.json": state.sprints[0].to_dict(),
        "planning_dependency.schema.json": state.dependencies[0].to_dict(),
        "planning_state.schema.json": state.to_dict(),
    }
    for name, payload in payloads.items():
        schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(payload)


def test_08_a_positive_contract_and_deterministic_dependency_order_pass():
    service = PlanningStateService()
    report = service.validate(good_state(), known_trace_refs=KNOWN)
    assert report.ok, report.to_dict()
    graph = service.graph.validate(good_state())
    assert graph.ok
    assert graph.topological_order == tuple(sorted(graph.topological_order, key=lambda x: graph.topological_order.index(x)))
    assert graph.cycle_nodes == ()


def test_08_a_duplicate_global_entity_id_blocks():
    state = good_state()
    state = replace(state, stories=(replace(state.stories[0], id="epic-roadmap"),))
    report = PlanningStateService().validate(state, known_trace_refs=KNOWN)
    assert not report.ok
    assert "PLANNING_ID_COLLISION" in {x.finding_id for x in report.findings}


def test_08_a_dependency_cycle_blocks():
    state = good_state()
    state = replace(state, dependencies=(
        Dependency(id="dep-a", predecessor_id="epic-roadmap", successor_id="story-traceability"),
        Dependency(id="dep-b", predecessor_id="story-traceability", successor_id="epic-roadmap"),
    ))
    report = PlanningStateService().validate(state, known_trace_refs=KNOWN)
    assert not report.ok
    assert "PLANNING_DEPENDENCY_CYCLE" in {x.finding_id for x in report.findings}


def test_08_a_orphan_dependency_blocks():
    state = replace(good_state(), dependencies=(Dependency(id="dep-orphan", predecessor_id="story-traceability", successor_id="story-missing"),))
    report = PlanningStateService().validate(state, known_trace_refs=KNOWN)
    assert not report.ok
    assert "PLANNING_DEPENDENCY_ORPHAN" in {x.finding_id for x in report.findings}


def test_08_a_orphan_trace_blocks():
    state = good_state()
    story = replace(state.stories[0], trace_links=(TraceLink(TraceKind.REQUIREMENT, "REQ-MISSING"),))
    report = PlanningStateService().validate(replace(state, stories=(story,)), known_trace_refs=KNOWN)
    assert not report.ok
    assert "PLANNING_TRACE_ORPHAN" in {x.finding_id for x in report.findings}


def test_08_a_story_without_requirement_trace_blocks_even_if_other_trace_exists():
    state = good_state()
    story = replace(state.stories[0], trace_links=(TraceLink(TraceKind.TEST_INTENT, "TEST-001"),))
    report = PlanningStateService().validate(replace(state, stories=(story,)), known_trace_refs=KNOWN)
    assert not report.ok
    assert "PLANNING_STORY_REQUIREMENT_TRACE_REQUIRED" in {x.finding_id for x in report.findings}


def test_08_a_illegal_transition_blocks():
    with pytest.raises(PlanningPolicyError) as exc:
        PlanningStateService().transition(good_state(), PlanningLifecycle.APPROVED, actor_id="owner-1", actor_role="owner")
    assert exc.value.code == "PLANNING_ILLEGAL_TRANSITION"


def test_08_a_agent_cannot_auto_approve():
    service = PlanningStateService()
    review = service.transition(good_state(), PlanningLifecycle.REVIEW, actor_id="architect-1", actor_role="architect")
    with pytest.raises(PlanningPolicyError) as exc:
        service.transition(review, PlanningLifecycle.APPROVED, actor_id="agent-1", actor_role="owner", actor_kind="agent")
    assert exc.value.code == "PLANNING_AGENT_APPROVAL_BLOCK"


def test_08_a_unauthorized_freeze_blocks_and_role_bound_human_freeze_passes():
    service = PlanningStateService()
    review = service.transition(good_state(), PlanningLifecycle.REVIEW, actor_id="architect-1", actor_role="architect")
    approved = service.transition(review, PlanningLifecycle.APPROVED, actor_id="po-1", actor_role="product-owner")
    with pytest.raises(PlanningPolicyError) as exc:
        service.transition(approved, PlanningLifecycle.FROZEN, actor_id="dev-1", actor_role="developer")
    assert exc.value.code == "PLANNING_APPROVAL_ROLE_BLOCK"
    frozen = service.transition(approved, PlanningLifecycle.FROZEN, actor_id="owner-1", actor_role="owner")
    assert frozen.lifecycle is PlanningLifecycle.FROZEN
    assert frozen.approval and frozen.approval.source_kind == "human"
    assert frozen.frozen_by and frozen.frozen_by.actor_role == "owner"
    assert service.validate(frozen, known_trace_refs=KNOWN).ok


def test_08_a_domain_service_is_pure_and_reports_no_source_mutation():
    service = PlanningStateService()
    report = service.validate(good_state(), known_trace_refs=KNOWN).to_dict()
    assert report["safety"]["source_mutations_performed"] is False
    assert report["safety"]["network_used"] is False
    assert report["safety"]["external_api_used"] is False


def test_08_a_contracts_and_schemas_are_registered_and_full_remains_zero():
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    assert state["gsdlc_08_activation_status"] == "CLOSED/PASS/WINDOWS-VALIDATED"
    assert state["gsdlc_08_a_full_regression_runs"] == 0
    assert state["gsdlc_08_a_browser_runs"] == 0
    catalog = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    ids = {x["schema_id"] for x in catalog["schemas"]}
    expected = {
        "SCHEMA-DEVPL-PLANNING-MILESTONE-V1", "SCHEMA-DEVPL-PLANNING-EPIC-V1", "SCHEMA-DEVPL-PLANNING-STORY-V1",
        "SCHEMA-DEVPL-PLANNING-SPRINT-V1", "SCHEMA-DEVPL-PLANNING-DEPENDENCY-V1", "SCHEMA-DEVPL-PLANNING-STATE-V1",
    }
    assert expected <= ids
    tcr = json.loads((ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8"))
    assert any(x["contract_id"] == "devpl-gsdlc-08-a-planning-domain" for x in tcr["contracts"])
    isolation = json.loads((ROOT / ".devpilot/testing/test_isolation_registry.json").read_text(encoding="utf-8"))
    by_nodeid = {x["nodeid"]: x for x in isolation["entries"]}
    new_nodes = [x for x in by_nodeid if x.startswith("tests/test_devpl_gsdlc_08_activation_rebind.py::") or x.startswith("tests/test_devpl_gsdlc_08_a_planning_domain.py::")]
    assert len(new_nodes) == 16
    assert all(by_nodeid[x]["state"] == "UNCLASSIFIED" and by_nodeid[x]["parallel_safe"] is False for x in new_nodes)
    isolation = json.loads((ROOT / ".devpilot/testing/test_isolation_registry.json").read_text(encoding="utf-8"))
    by_nodeid = {x["nodeid"]: x for x in isolation["entries"]}
    new_nodes = [x for x in by_nodeid if x.startswith("tests/test_devpl_gsdlc_08_activation_rebind.py::") or x.startswith("tests/test_devpl_gsdlc_08_a_planning_domain.py::")]
    assert len(new_nodes) == 16
    assert all(by_nodeid[x]["state"] == "UNCLASSIFIED" and by_nodeid[x]["parallel_safe"] is False for x in new_nodes)
