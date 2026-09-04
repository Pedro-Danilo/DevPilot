from __future__ import annotations
import json
from pathlib import Path
import pytest
from devpilot_core.planning.backlog_workbench import BacklogWorkbench, RequirementCoverageService
from devpilot_core.planning.service import PlanningPolicyError
from devpilot_core.schemas.validator import SchemaValidator


def backlog(*, source="MANUAL", reqs=("REQ-001","REQ-002"), title2="Second story", dep=True):
    return {
      "backlog_id":"planning-backlog-001","version":"1.0.0",
      "epics":[{"id":"epic-foundation","version":"1.0.0","title":"Foundation","owner_role":"product-owner","milestone_id":"mil-foundation","trace_links":[{"kind":"requirement","target_id":"REQ-001"}],"priority":{"level":"P0","value_score":5,"risk_score":4,"rationale":"Core business foundation","source":source}}],
      "stories":[
        {"id":"story-first","version":"1.0.0","title":"First story","owner_role":"developer","epic_id":"epic-foundation","acceptance_criteria":["REQ-001 accepted"],"trace_links":[{"kind":"requirement","target_id":reqs[0]},{"kind":"adr","target_id":"ADR-001"},{"kind":"risk","target_id":"RISK-001"},{"kind":"test-intent","target_id":"TEST-001"}],"priority":{"level":"P0","value_score":5,"risk_score":4,"rationale":"Required first","source":source}},
        {"id":"story-second","version":"1.0.0","title":title2,"owner_role":"developer","epic_id":"epic-foundation","acceptance_criteria":["REQ-002 accepted"],"trace_links":[{"kind":"requirement","target_id":reqs[1]}],"priority":{"level":"P1","value_score":4,"risk_score":3,"rationale":"Required second","source":source}}
      ],
      "dependencies":[{"id":"dep-first-second","predecessor_id":"story-first","successor_id":"story-second","kind":"requires","rationale":"Second depends on first"}] if dep else []
    }

KW={"required_requirement_ids":["REQ-001","REQ-002"],"roadmap_milestone_ids":["mil-foundation"],"known_adr_ids":["ADR-001"],"known_risk_ids":["RISK-001"],"known_test_intent_ids":["TEST-001"]}

def test_requirement_coverage_is_100_and_matrix_is_explainable():
    report=RequirementCoverageService().evaluate(backlog(),expected_priority_source="MANUAL",**KW)
    assert report["status"]=="PASS" and report["requirement_coverage_percent"]==100.0 and report["unmapped_requirement_ids"]==[]
    assert {r["requirement_id"]:r["story_ids"] for r in report["requirement_to_story_matrix"]}=={"REQ-001":["story-first"],"REQ-002":["story-second"]}

def test_unmapped_requirement_blocks_review_and_approval(tmp_path: Path):
    bad=backlog(reqs=("REQ-001","REQ-001")); wb=BacklogWorkbench(tmp_path)
    wb.propose(mode="MANUAL",backlog=bad,actor_id="dev",actor_role="developer",**KW)
    review=wb.review(actor_id="arch",actor_role="architect")
    assert review["status"]=="BLOCK" and "REQ-002" in review["unmapped_blockers"]
    with pytest.raises(PlanningPolicyError): wb.approve(actor_id="owner",actor_role="owner")

def test_duplicate_story_and_dependency_gap_are_explicit_blockers():
    bad=backlog(title2="First story"); bad["dependencies"][0]["successor_id"]="story-missing"
    report=RequirementCoverageService().evaluate(bad,expected_priority_source="MANUAL",**KW)
    codes={x["code"] for x in report["findings"]}
    assert {"BACKLOG_DUPLICATE_STORY","BACKLOG_DEPENDENCY_GAP"} <= codes

def test_story_without_acceptance_criteria_blocks():
    bad=backlog(); bad["stories"][0]["acceptance_criteria"]=[]
    report=RequirementCoverageService().evaluate(bad,expected_priority_source="MANUAL",**KW)
    assert "BACKLOG_STORY_ACCEPTANCE_REQUIRED" in {x["code"] for x in report["findings"]}

def test_priority_requires_rationale_scores_and_matching_provenance():
    bad=backlog(); bad["stories"][0]["priority"]={"level":"P0","value_score":9,"risk_score":4,"rationale":"","source":"AGENT"}
    report=RequirementCoverageService().evaluate(bad,expected_priority_source="MANUAL",**KW)
    codes={x["code"] for x in report["findings"]}
    assert {"BACKLOG_PRIORITY_SCORE_INVALID","BACKLOG_PRIORITY_RATIONALE_REQUIRED","BACKLOG_PRIORITY_PROVENANCE_MISMATCH"} <= codes

def test_manual_edits_prevail_over_agent_or_derived_same_version(tmp_path: Path):
    wb=BacklogWorkbench(tmp_path); wb.propose(mode="MANUAL",backlog=backlog(),actor_id="dev",actor_role="developer",**KW)
    for mode in ("AGENT","DERIVED"):
        with pytest.raises(PlanningPolicyError) as exc: wb.propose(mode=mode,backlog=backlog(source=mode),actor_id="dev",actor_role="developer",**KW)
        assert exc.value.code=="BACKLOG_MANUAL_PRECEDENCE_BLOCK"

def test_agent_is_draft_only_and_human_review_approval_freeze_are_role_bound(tmp_path: Path):
    wb=BacklogWorkbench(tmp_path); rec=wb.propose(mode="AGENT",backlog=backlog(source="AGENT"),actor_id="human-agent-proxy",actor_role="architect",**KW)
    assert rec["lifecycle"]=="DRAFT" and rec["provenance"]["agent_auto_approved"] is False
    assert wb.review(actor_id="qa",actor_role="qa-reviewer")["status"]=="PASS"
    with pytest.raises(PlanningPolicyError): wb.approve(actor_id="agent-1",actor_role="owner")
    wb.approve(actor_id="owner-1",actor_role="owner"); frozen=wb.freeze(actor_id="owner-1",actor_role="owner")
    assert frozen["revision"]==1 and json.loads((tmp_path/frozen["artifact_path"]).read_text())["freeze"]["immutable"] is True

def test_backlog_schema_validates_shared_payload():
    root=Path(__file__).resolve().parents[1]
    result=SchemaValidator(root).validate_payload(schema="SCHEMA-DEVPL-PLANNING-BACKLOG-V1",payload=backlog(),instance_label="backlog-test")
    assert result.ok,[x.to_dict() for x in result.findings]

def test_08_c_contract_is_registered_full_zero_and_browser_zero():
    root=Path(__file__).resolve().parents[1]; state=json.loads((root/'.devpilot/project_state.json').read_text())
    assert state["gsdlc_08_c_full_regression_runs"]==0 and state["gsdlc_08_c_browser_runs"]==0
    catalog=json.loads((root/'docs/schemas/schema_catalog.json').read_text()); assert "SCHEMA-DEVPL-PLANNING-BACKLOG-V1" in {x['schema_id'] for x in catalog['schemas']}
    tcr=json.loads((root/'.devpilot/testing/test_contract_registry_v2.json').read_text()); assert any(x['contract_id']=='devpl-gsdlc-08-c-backlog-derivation-prioritization' for x in tcr['contracts'])
    iso=json.loads((root/'.devpilot/testing/test_isolation_registry.json').read_text()); rows=[x for x in iso['entries'] if x['nodeid'].startswith('tests/test_devpl_gsdlc_08_c_backlog_workbench.py::')]
    assert len(rows)==10 and all(x['state']=='UNCLASSIFIED' and x['parallel_safe'] is False for x in rows)

def test_application_service_exposes_backlog_workbench_without_browser_route(tmp_path: Path):
    from devpilot_core.application import ApplicationRequest, ApplicationService
    root=Path(__file__).resolve().parents[1]
    service=ApplicationService(root)
    response=service.handle(ApplicationRequest(operation="planning.backlog.status",payload={"effective_roles":["developer"]},client="test",dry_run=True))
    data=response.to_dict() if hasattr(response,"to_dict") else response
    assert data["ok"] is True
    from devpilot_core.application.services import _capabilities
    caps={x.operation for x in _capabilities()}
    assert {"planning.backlog.status","planning.backlog.propose","planning.backlog.review","planning.backlog.approve","planning.backlog.freeze"} <= caps
