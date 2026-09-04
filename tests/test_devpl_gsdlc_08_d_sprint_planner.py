from __future__ import annotations
import json
from pathlib import Path
import pytest
from devpilot_core.planning.sprint_planner import SprintPlanner, SprintPlanValidationService
from devpilot_core.planning.service import PlanningPolicyError
from devpilot_core.schemas.validator import SchemaValidator


def backlog():
    return {
      "backlog_id":"planning-backlog-001","version":"1.0.0",
      "stories":[
        {"id":"story-first","acceptance_criteria":["first accepted"]},
        {"id":"story-second","acceptance_criteria":["second accepted"]},
        {"id":"story-third","acceptance_criteria":["third accepted"]},
      ],
      "dependencies":[
        {"id":"dep-first-second","predecessor_id":"story-first","successor_id":"story-second","kind":"requires","rationale":"first before second"},
        {"id":"dep-second-third","predecessor_id":"story-second","successor_id":"story-third","kind":"requires","rationale":"second before third"},
      ],
    }


def plan(*, order=("story-first","story-second"), estimates=(3,5), readiness=("READY","READY"), limit=8, completed=()):
    rows=[]
    for sid,estimate,state in zip(order,estimates,readiness):
        rows.append({"story_id":sid,"estimate":estimate,"readiness":state,"blocking_reasons":[] if state=="READY" else ["explicit blocker"]})
    return {
      "schema_id":"SCHEMA-DEVPL-PLANNING-SPRINT-PLAN-V1","schema_version":"1.0.0","sprint_plan_id":"sprint-plan-001","version":"1.0.0","title":"Sprint 1","owner_role":"product-owner","lifecycle":"DRAFT",
      "backlog_reference":{"backlog_id":"planning-backlog-001","version":"1.0.0","lifecycle":"FROZEN","content_sha256":"a"*64},
      "capacity":{"unit":"points","limit":limit},"selected_stories":rows,"completed_story_ids":list(completed),
      "definition_of_ready":["acceptance criteria approved","dependencies known"],"definition_of_done":["tests PASS","evidence stored"],"test_intent_ids":["TEST-001"],"risk_focus_ids":["RISK-001"]
    }


def validate(p): return SprintPlanValidationService().evaluate(p,backlog=backlog(),dependencies=backlog()["dependencies"])


def test_ordered_ready_plan_is_executable_and_capacity_is_explicit():
    r=validate(plan()); assert r["status"]=="PASS" and r["executable"] is True and r["capacity_utilization_percent"]==100.0

def test_dependency_violation_blocks_when_successor_is_before_prerequisite():
    r=validate(plan(order=("story-second","story-first"),estimates=(5,3))); assert "SPRINT_DEPENDENCY_ORDER" in {x["code"] for x in r["findings"]}

def test_missing_prerequisite_blocks_unless_completed():
    r=validate(plan(order=("story-second",),estimates=(5,),readiness=("READY",),limit=5)); assert "SPRINT_PREREQUISITE_MISSING" in {x["code"] for x in r["findings"]}
    ok=validate(plan(order=("story-second",),estimates=(5,),readiness=("READY",),limit=5,completed=("story-first",))); assert ok["status"]=="PASS"

def test_capacity_overcommit_is_visible_blocker():
    r=validate(plan(limit=7)); assert r["overcommitted"] is True and "SPRINT_CAPACITY_OVERCOMMIT" in {x["code"] for x in r["findings"]}

def test_blocked_or_not_ready_story_never_enters_silently():
    r=validate(plan(readiness=("READY","BLOCKED"))); codes={x["code"] for x in r["findings"]}; assert "SPRINT_STORY_NOT_READY" in codes and r["status"]=="BLOCK"

def test_ready_story_cannot_hide_blocking_reasons():
    p=plan(); p["selected_stories"][0]["blocking_reasons"]=["hidden blocker"]
    assert "SPRINT_READY_HAS_BLOCKERS" in {x["code"] for x in validate(p)["findings"]}

def test_dor_dod_test_intent_and_risk_focus_are_required():
    p=plan(); p["definition_of_ready"]=[]; p["definition_of_done"]=[]; p["test_intent_ids"]=[]; p["risk_focus_ids"]=[]
    codes={x["code"] for x in validate(p)["findings"]}; assert {"SPRINT_DOR_REQUIRED","SPRINT_DOD_REQUIRED","SPRINT_TEST_INTENT_REQUIRED","SPRINT_RISK_FOCUS_REQUIRED"} <= codes

def test_backlog_must_be_frozen_authority():
    p=plan(); p["backlog_reference"]["lifecycle"]="APPROVED"
    assert "SPRINT_BACKLOG_FROZEN_REQUIRED" in {x["code"] for x in validate(p)["findings"]}

def test_human_review_approval_freeze_are_role_bound_and_hash_bound(tmp_path: Path):
    wb=SprintPlanner(tmp_path); wb.propose(sprint_plan=plan(),backlog=backlog(),dependencies=backlog()["dependencies"],actor_id="po-1",actor_role="product-owner")
    assert wb.review(actor_id="arch",actor_role="architect")["status"]=="PASS"
    with pytest.raises(PlanningPolicyError): wb.approve(actor_id="dev",actor_role="developer")
    with pytest.raises(PlanningPolicyError): wb.approve(actor_id="agent-1",actor_role="owner")
    approval=wb.approve(actor_id="owner-1",actor_role="owner"); frozen=wb.freeze(actor_id="owner-1",actor_role="owner")
    assert approval["content_sha256"]==frozen["content_sha256"] and frozen["revision"]==1
    artifact=json.loads((tmp_path/frozen["artifact_path"]).read_text()); assert artifact["freeze"]["immutable"] is True and artifact["lifecycle"]=="FROZEN"

def test_sprint_plan_schema_validates_successor_contract():
    root=Path(__file__).resolve().parents[1]
    result=SchemaValidator(root).validate_payload(schema="SCHEMA-DEVPL-PLANNING-SPRINT-PLAN-V1",payload=plan(),instance_label="sprint-plan-test")
    assert result.ok,[x.to_dict() for x in result.findings]

def test_08_d_contract_and_pre_full_handoff_are_registered_full_zero_browser_zero():
    root=Path(__file__).resolve().parents[1]; state=json.loads((root/'.devpilot/project_state.json').read_text())
    assert state["gsdlc_08_d_full_regression_runs"]==0 and state["gsdlc_08_d_browser_runs"]==0
    catalog=json.loads((root/'docs/schemas/schema_catalog.json').read_text()); assert "SCHEMA-DEVPL-PLANNING-SPRINT-PLAN-V1" in {x['schema_id'] for x in catalog['schemas']}
    tcr=json.loads((root/'.devpilot/testing/test_contract_registry_v2.json').read_text()); assert any(x['contract_id']=='devpl-gsdlc-08-d-sprint-planning-capacity-dependencies' for x in tcr['contracts'])
    handoff=json.loads((root/'docs/audits/DEVPL_GSDLC_08_D_PRE_FULL_HANDOFF.json').read_text()); assert handoff['full_budget']['consumed']==0 and handoff['full_budget']['remaining']==1 and handoff['parallel_mode']=='AVAILABLE-NOT-DEFAULT' and handoff['s0_open']==0 and handoff['s1_open']==0
    iso=json.loads((root/'.devpilot/testing/test_isolation_registry.json').read_text()); rows=[x for x in iso['entries'] if x['nodeid'].startswith('tests/test_devpl_gsdlc_08_d_sprint_planner.py::')]
    assert len(rows)==12 and all(x['state']=='UNCLASSIFIED' and x['parallel_safe'] is False for x in rows)

def test_application_service_exposes_sprint_planner_without_browser_route(tmp_path: Path):
    from devpilot_core.application import ApplicationRequest, ApplicationService
    from devpilot_core.application.services import _capabilities
    service=ApplicationService(Path(__file__).resolve().parents[1]); data=service.handle(ApplicationRequest(operation="planning.sprint.status",payload={"effective_roles":["product-owner"]},client="test",dry_run=True)).to_dict()
    assert data["ok"] is True
    caps={x.operation for x in _capabilities()}; assert {"planning.sprint.status","planning.sprint.propose","planning.sprint.review","planning.sprint.approve","planning.sprint.freeze"} <= caps
    assert not any("/planning/sprint" in str(getattr(x,"notes","")).lower() for x in _capabilities() if x.operation.startswith("planning.sprint."))
