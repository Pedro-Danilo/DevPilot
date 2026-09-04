from __future__ import annotations

import json
from pathlib import Path

import pytest

from devpilot_core.planning.roadmap_workbench import RoadmapWorkbench
from devpilot_core.planning.service import PlanningPolicyError
from devpilot_core.schemas.validator import SchemaValidator


def roadmap(*, include_risk: bool = True, version: str = "1.0.0") -> dict:
    links = [{"kind": "requirement", "target_id": "REQ-001"}]
    if include_risk:
        links.append({"kind": "risk", "target_id": "RISK-001"})
    return {
        "roadmap_id": "planning-roadmap-001",
        "version": version,
        "milestones": [
            {"id":"mil-foundation","version":"1.0.0","title":"Foundation","owner_role":"product-owner","outcome":"Ready","exit_criteria":["REQ covered"],"trace_links":links}
        ],
        "dependencies": [],
    }


def test_shared_schema_and_three_authoring_routes_are_draft(tmp_path: Path) -> None:
    wb = RoadmapWorkbench(tmp_path, workspace_id="ws-1")
    for mode in ("MANUAL", "IMPORT", "AGENT"):
        record = wb.propose(mode=mode, roadmap=roadmap(version=f"1.0.{1 if mode=='MANUAL' else 2 if mode=='IMPORT' else 3}"), required_requirement_ids=["REQ-001"], required_risk_ids=["RISK-001"], actor_id="human-1", actor_role="architect", source_label=mode)
        assert record["lifecycle"] == "DRAFT"
        assert record["authoring_mode"] == mode
        assert record["provenance"]["agent_auto_approved"] is False
        assert record["provenance"]["external_api_used"] is False
        assert record["planning_state"]["schema_id"] == "SCHEMA-DEVPL-PLANNING-STATE-V1"


def test_coverage_findings_are_explicit_and_missing_requirement_blocks_approval(tmp_path: Path) -> None:
    wb = RoadmapWorkbench(tmp_path)
    bad = roadmap(); bad["milestones"][0]["trace_links"] = [{"kind":"risk","target_id":"RISK-001"}]
    rec = wb.propose(mode="MANUAL", roadmap=bad, required_requirement_ids=["REQ-001"], required_risk_ids=["RISK-001"], actor_id="u", actor_role="architect")
    assert any(x["code"] == "ROADMAP_REQUIREMENT_COVERAGE_GAP" for x in rec["findings"])
    review = wb.review(actor_id="u", actor_role="architect")
    assert review["status"] == "BLOCK"
    with pytest.raises(PlanningPolicyError) as exc: wb.approve(actor_id="o", actor_role="owner")
    assert exc.value.code == "ROADMAP_REVIEW_PASS_REQUIRED"


def test_risk_gap_remains_visible_but_requirement_complete_can_approve(tmp_path: Path) -> None:
    wb = RoadmapWorkbench(tmp_path)
    rec = wb.propose(mode="IMPORT", roadmap=roadmap(include_risk=False), required_requirement_ids=["REQ-001"], required_risk_ids=["RISK-001"], actor_id="u", actor_role="developer")
    assert rec["coverage"]["requirement_percent"] == 100.0
    assert rec["coverage"]["risk_percent"] == 0.0
    review = wb.review(actor_id="u", actor_role="architect")
    assert review["status"] == "PASS-WITH-FINDINGS"
    approval = wb.approve(actor_id="owner-1", actor_role="owner")
    assert approval["source_kind"] == "human"


def test_agent_cannot_approve_and_freeze_is_human_role_bound_immutable_revision(tmp_path: Path) -> None:
    wb = RoadmapWorkbench(tmp_path)
    wb.propose(mode="AGENT", roadmap=roadmap(), required_requirement_ids=["REQ-001"], required_risk_ids=["RISK-001"], actor_id="agent-proxy-human", actor_role="architect", source_label="structured")
    wb.review(actor_id="reviewer", actor_role="architect")
    with pytest.raises(PlanningPolicyError): wb.approve(actor_id="agent", actor_role="architect")
    wb.approve(actor_id="po", actor_role="product-owner")
    frozen = wb.freeze(actor_id="po", actor_role="product-owner")
    assert frozen["revision"] == 1
    artifact = tmp_path / frozen["artifact_path"]
    assert artifact.is_file()
    assert json.loads(artifact.read_text())["freeze"]["immutable"] is True


def test_frozen_same_version_requires_successor_revision(tmp_path: Path) -> None:
    wb=RoadmapWorkbench(tmp_path)
    wb.propose(mode="MANUAL",roadmap=roadmap(),required_requirement_ids=["REQ-001"],required_risk_ids=["RISK-001"],actor_id="a",actor_role="architect")
    wb.review(actor_id="a",actor_role="architect"); wb.approve(actor_id="o",actor_role="owner"); wb.freeze(actor_id="o",actor_role="owner")
    with pytest.raises(PlanningPolicyError) as exc: wb.propose(mode="MANUAL",roadmap=roadmap(),required_requirement_ids=["REQ-001"],required_risk_ids=["RISK-001"],actor_id="a",actor_role="architect")
    assert exc.value.code == "ROADMAP_FROZEN_REVISION_REQUIRED"


def test_advisor_is_server_authority_description_not_capability_grant(tmp_path: Path) -> None:
    advisor=RoadmapWorkbench(tmp_path).advisor(effective_roles=["developer"])
    assert advisor["status"] == "PASS"
    assert len(advisor["actions"]) == 3
    assert advisor["authority"]["advisor_grants_capability"] is False
    assert advisor["safety"]["agent_auto_approval"] is False
    assert next(x for x in advisor["actions"] if x["kind"]=="AGENT")["agent_descriptor"]["human_review_required"] is True


def test_roadmap_schema_validates_shared_payload(tmp_path: Path) -> None:
    # Validate through the repo schema validator contract by copying only the schema root requirement.
    root=Path(__file__).resolve().parents[1]
    result=SchemaValidator(root).validate_payload(schema="SCHEMA-DEVPL-PLANNING-ROADMAP-V1", payload=roadmap(), instance_label="roadmap-test")
    assert result.ok, [x.to_dict() for x in result.findings]


def test_route_rbac_ui_and_safety_registries_are_reconciled() -> None:
    root=Path(__file__).resolve().parents[1]
    api=json.loads((root/'.devpilot/interfaces/api_route_contract_registry.json').read_text())
    rbac=json.loads((root/'.devpilot/identity/server_rbac_policy_catalog.json').read_text())
    ui=json.loads((root/'.devpilot/interfaces/ui_route_contract_registry.json').read_text())
    ids={"api.planning-roadmap.status","api.planning-roadmap.propose","api.planning-roadmap.review","api.planning-roadmap.approve","api.planning-roadmap.freeze"}
    assert ids <= {x['route_id'] for x in api['routes']}
    assert ids <= {x['route_id'] for x in rbac['route_policies']}
    route=next(x for x in ui['routes'] if x['route_id']=='ui.planning-roadmap')
    assert ids <= set(route['allowed_api_routes'])
    for row in api['routes']:
        if row['route_id'] in ids:
            assert row['external_api_allowed'] is False and row['source_mutation_allowed'] is False


def test_b_does_not_consume_full_regression() -> None:
    root=Path(__file__).resolve().parents[1]
    state=json.loads((root/'.devpilot/project_state.json').read_text())
    # During implementation this is PRE-WINDOWS; contract remains zero-run.
    assert state.get('gsdlc_08_b_full_regression_runs', 0) == 0
