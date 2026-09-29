from __future__ import annotations

import json
from pathlib import Path

import pytest
from types import SimpleNamespace

from devpilot_core.application.planning_authoring_service import PlanningAuthoringApplicationService
from devpilot_core.application.planning_candidate_provider import DeterministicPlanningCandidateProvider
from devpilot_core.application.planning_closure_service import PlanningClosureApplicationService
from devpilot_core.application.guided_sdlc_service import GuidedSDLCApplicationService
from devpilot_core.planning.backlog_workbench import BacklogWorkbench
from devpilot_core.planning.roadmap_workbench import RoadmapWorkbench
from devpilot_core.planning.sprint_planner import SprintPlanner
from devpilot_core.planning.service import PlanningPolicyError
from devpilot_core.interfaces.api.routers import planning as planning_router
from devpilot_core.interfaces.api import security as api_security


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fixture(tmp_path: Path, *, workspace_id: str = "inventory-sales-local-greenfield", requirement_ids: tuple[str, ...] = ("RF-001", "RF-002")):
    platform = tmp_path / "platform"
    workspace = tmp_path / workspace_id
    platform.mkdir(parents=True); workspace.mkdir(parents=True)
    _write(workspace / "docs/00_product/mvp_scope.md", "- CAP-001: administrar productos.\n- CAP-002: controlar existencias.\n")
    sections = []
    trace_rows = []
    tests = []
    for index, rid in enumerate(requirement_ids, start=1):
        cap = "CAP-001" if index % 2 else "CAP-002"
        sec = f"SEC-{index:03d}"
        test = f"TEST-{index:03d}"
        sections.append(
            f"### {rid}\n- **Statement:** Requirement {rid}\n- **Fuente:** {cap}\n- **Prioridad:** MUST\n- **Criterio de aceptación:** {rid} verificable\n"
        )
        trace_rows.append(f"| {rid} | {cap} | ARC-C02 | ADR-001 | {sec} / CTRL-{index:03d} | {test} |")
        tests.append(test)
    _write(workspace / "docs/01_requirements/requirements_specification.md", "# Requirements\n\n" + "\n".join(sections))
    _write(
        workspace / "docs/01_requirements/traceability_matrix.md",
        "| Requirement | Capability/source | Architecture | ADR | Security/control | Test intent |\n|---|---|---|---|---|---|\n" + "\n".join(trace_rows) + "\n",
    )
    _write(workspace / "docs/03_security/security_threat_model.md", "\n".join(f"SEC-{x:03d}" for x in range(1, len(requirement_ids)+1)) + "\n")
    _write(workspace / "docs/04_quality/test_strategy.md", "\n".join(tests) + "\n")
    _write(workspace / "docs/02_architecture/adrs/ADR-001-example.md", "# ADR-001\n")
    state = {"status":"PRE_CODE_READY","stages":{x:{"status":"FROZEN"} for x in ("product-vision","scope","requirements","architecture","security","test-strategy","traceability")}}
    _write(platform / f"outputs/pre_code_wizard/gsdlc_05_e/{workspace_id}/state.json", json.dumps(state))
    ctx = SimpleNamespace(configured=True, valid=True, effective_workspace_root=workspace, active_workspace_id=workspace_id)
    resolver = SimpleNamespace(resolve=lambda: ctx)
    return platform, workspace, workspace_id, resolver


def _freeze_roadmap(workspace: Path, workspace_id: str) -> None:
    wb = RoadmapWorkbench(workspace, workspace_id=workspace_id)
    assert wb.review(actor_id="owner-1", actor_role="owner")["status"] in {"PASS", "PASS-WITH-FINDINGS"}
    wb.approve(actor_id="owner-1", actor_role="owner")
    wb.freeze(actor_id="owner-1", actor_role="owner")


def _freeze_backlog(workspace: Path, workspace_id: str) -> None:
    wb = BacklogWorkbench(workspace, workspace_id=workspace_id)
    assert wb.review(actor_id="owner-1", actor_role="owner")["status"] == "PASS"
    wb.approve(actor_id="owner-1", actor_role="owner")
    wb.freeze(actor_id="owner-1", actor_role="owner")


def test_c04_authoring_uses_real_authority_provider_and_sequential_gates(tmp_path: Path) -> None:
    platform, workspace, wid, resolver = fixture(tmp_path)
    svc = PlanningAuthoringApplicationService(platform, context_resolver=resolver)
    status = svc.status(effective_roles=["owner"]).to_dict()["data"]["planning_authoring"]
    assert status["authority"]["requirement_ids"] == ["RF-001", "RF-002"]
    assert status["provider"]["provider_family"] == "PlanningCandidateProvider"
    assert status["provider"]["provider_id"] == "devpilot-local"
    assert status["provider"]["strategy_id"] == "deterministic-planning-template-v1"
    assert status["provider"]["model_execution_used"] is False
    assert status["availability"]["roadmap"]["devpilot_local"] is True
    assert status["availability"]["backlog"]["devpilot_local"] is False
    assert status["availability"]["roadmap"]["agent"] is False

    road = svc.generate_roadmap(actor_id="owner-1", actor_role="owner").to_dict()["data"]["planning_authoring"]
    assert road["authoring_mode"] == "DEVPL_LOCAL"
    assert road["required_requirement_ids"] == ["RF-001", "RF-002"]
    assert road["coverage"]["requirement_percent"] == 100.0
    assert road["provenance"]["source_label"] == "devpilot-local:deterministic-planning-template-v1"
    assert "REQ-001" not in json.dumps(road)

    blocked = svc.derive_backlog(actor_id="owner-1", actor_role="owner").to_dict()
    assert blocked["ok"] is False
    assert blocked["findings"][0]["id"] == "BACKLOG_ROADMAP_FROZEN_REQUIRED"

    rw = RoadmapWorkbench(workspace, workspace_id=wid)
    assert rw.review(actor_id="owner-1", actor_role="owner")["status"] in {"PASS", "PASS-WITH-FINDINGS"}
    rw.approve(actor_id="owner-1", actor_role="owner")
    with pytest.raises(PlanningPolicyError, match="Approved roadmap cannot return to DRAFT"):
        rw.propose(
            mode="DEVPL_LOCAL",
            roadmap=dict(road["planning_state"]),
            required_requirement_ids=road["required_requirement_ids"],
            required_risk_ids=road["required_risk_ids"],
            actor_id="owner-1",
            actor_role="owner",
            source_label="test-approved-downgrade",
        )
    rw.freeze(actor_id="owner-1", actor_role="owner")
    roadmap_root = workspace / "outputs/planning/gsdlc_08_b" / wid
    assert (roadmap_root / "roadmap.md").is_file()
    assert (roadmap_root / "revisions/roadmap-revision-0001.md").is_file()
    roadmap_md = (roadmap_root / "roadmap.md").read_text(encoding="utf-8")
    for token in ("doc_id:", "title:", 'status: "FROZEN"', "version:", "owner:", "updated:", "approval:", 'canonical_authority: "json"', "source_record_sha256:", "## Milestones"):
        assert token in roadmap_md

    back = svc.derive_backlog(actor_id="owner-1", actor_role="owner").to_dict()["data"]["planning_authoring"]
    assert back["authoring_mode"] == "DERIVED"
    assert back["coverage"]["requirement_coverage_percent"] == 100.0
    assert {x["id"] for x in back["backlog"]["stories"]} == {"story-rf-001", "story-rf-002"}
    assert back["provenance"]["source_label"] == "devpilot-local:deterministic-planning-template-v1"

    blocked_sprint = svc.derive_sprint(actor_id="owner-1", actor_role="owner").to_dict()
    assert blocked_sprint["ok"] is False
    assert blocked_sprint["findings"][0]["id"] == "SPRINT_BACKLOG_FROZEN_REQUIRED"

    bw = BacklogWorkbench(workspace, workspace_id=wid)
    assert bw.review(actor_id="owner-1", actor_role="owner")["status"] == "PASS"
    bw.approve(actor_id="owner-1", actor_role="owner")
    with pytest.raises(PlanningPolicyError, match="Approved backlog cannot return to DRAFT"):
        bw.propose(
            mode="DERIVED",
            backlog=dict(back["backlog"]),
            required_requirement_ids=back["required_requirement_ids"],
            roadmap_milestone_ids=back["roadmap_milestone_ids"],
            known_adr_ids=back["known_adr_ids"],
            known_risk_ids=back["known_risk_ids"],
            known_test_intent_ids=back["known_test_intent_ids"],
            actor_id="owner-1",
            actor_role="owner",
            source_label="test-approved-downgrade",
        )
    bw.freeze(actor_id="owner-1", actor_role="owner")
    backlog_root = workspace / "outputs/planning/gsdlc_08_c" / wid
    assert (backlog_root / "backlog.md").is_file()
    assert (backlog_root / "revisions/backlog-revision-0001.md").is_file()
    backlog_md = (backlog_root / "backlog.md").read_text(encoding="utf-8")
    assert 'status: "FROZEN"' in backlog_md
    assert "## Epics" in backlog_md and "## Stories" in backlog_md

    sprint = svc.derive_sprint(actor_id="owner-1", actor_role="owner", capacity_limit=2).to_dict()["data"]["planning_authoring"]
    assert sprint["validation"]["status"] == "PASS"
    assert sprint["validation"]["executable"] is True
    assert sprint["sprint_plan"]["generation_provenance"]["provider_id"] == "devpilot-local"
    assert len(sprint["sprint_plan"]["selected_stories"]) == 2

    sp = SprintPlanner(workspace, workspace_id=wid)
    assert sp.review(actor_id="owner-1", actor_role="owner")["status"] == "PASS"
    sp.approve(actor_id="owner-1", actor_role="owner")
    with pytest.raises(PlanningPolicyError, match="Approved SprintPlan cannot return to DRAFT"):
        sp.propose(
            sprint_plan=dict(sprint["sprint_plan"]),
            backlog=dict(sprint["backlog"]),
            dependencies=list(sprint.get("dependencies") or []),
            actor_id="owner-1",
            actor_role="owner",
        )
    sp.freeze(actor_id="owner-1", actor_role="owner")
    sprint_root = workspace / "outputs/planning/gsdlc_08_d" / wid
    assert (sprint_root / "sprint_plan.md").is_file()
    assert (sprint_root / "revisions/sprint-plan-revision-0001.md").is_file()
    sprint_md = (sprint_root / "sprint_plan.md").read_text(encoding="utf-8")
    assert 'status: "FROZEN"' in sprint_md
    assert "## Selected stories" in sprint_md and "Requirement RF-001" in sprint_md
    assert "## Definition of Ready" in sprint_md and "## Definition of Done" in sprint_md

    closure = PlanningClosureApplicationService(platform, context_resolver=resolver).status(effective_roles=["owner"]).to_dict()["data"]["planning_closure"]
    assert closure["journey_state"] == "IMPLEMENTING_READY"
    assert closure["required_planning_coverage_percent"] == 100.0
    assert closure["blockers"] == []
    assert closure["next_action"]["reason_code"] == "IMPLEMENTING_READY_STORY_CONTEXT_NEXT"
    assert closure["next_action"]["navigation_target"] == "ui.story-code-workbench"
    assert closure["next_action"]["available"] is True
    assert svc.status(effective_roles=["owner"]).to_dict()["data"]["planning_authoring"]["recommended_next"] == "story-code"


def test_c04_product_lifecycle_emits_markdown_without_operator_reconcile(tmp_path: Path) -> None:
    """Normal product lifecycle writes human projections; operator reconcile is migration-only."""
    platform, workspace, wid, resolver = fixture(tmp_path)
    svc = PlanningAuthoringApplicationService(platform, context_resolver=resolver)

    svc.generate_roadmap(actor_id="owner-1", actor_role="owner")
    roadmap_root = workspace / "outputs/planning/gsdlc_08_b" / wid
    roadmap_md = roadmap_root / "roadmap.md"
    assert roadmap_md.is_file()
    assert 'status: "DRAFT"' in roadmap_md.read_text(encoding="utf-8")
    rw = RoadmapWorkbench(workspace, workspace_id=wid)
    rw.review(actor_id="owner-1", actor_role="owner")
    assert 'status: "REVIEW"' in roadmap_md.read_text(encoding="utf-8")
    rw.approve(actor_id="owner-1", actor_role="owner")
    assert 'status: "APPROVED"' in roadmap_md.read_text(encoding="utf-8")
    rw.freeze(actor_id="owner-1", actor_role="owner")
    assert 'status: "FROZEN"' in roadmap_md.read_text(encoding="utf-8")
    assert (roadmap_root / "revisions/roadmap-revision-0001.md").is_file()

    svc.derive_backlog(actor_id="owner-1", actor_role="owner")
    backlog_root = workspace / "outputs/planning/gsdlc_08_c" / wid
    backlog_md = backlog_root / "backlog.md"
    assert backlog_md.is_file()
    assert 'status: "DRAFT"' in backlog_md.read_text(encoding="utf-8")
    bw = BacklogWorkbench(workspace, workspace_id=wid)
    bw.review(actor_id="owner-1", actor_role="owner")
    assert 'status: "REVIEW"' in backlog_md.read_text(encoding="utf-8")
    bw.approve(actor_id="owner-1", actor_role="owner")
    assert 'status: "APPROVED"' in backlog_md.read_text(encoding="utf-8")
    bw.freeze(actor_id="owner-1", actor_role="owner")
    assert 'status: "FROZEN"' in backlog_md.read_text(encoding="utf-8")
    assert (backlog_root / "revisions/backlog-revision-0001.md").is_file()

    svc.derive_sprint(actor_id="owner-1", actor_role="owner", capacity_limit=2)
    sprint_root = workspace / "outputs/planning/gsdlc_08_d" / wid
    sprint_md = sprint_root / "sprint_plan.md"
    assert sprint_md.is_file()
    assert 'status: "DRAFT"' in sprint_md.read_text(encoding="utf-8")
    sp = SprintPlanner(workspace, workspace_id=wid)
    sp.review(actor_id="owner-1", actor_role="owner")
    assert 'status: "REVIEW"' in sprint_md.read_text(encoding="utf-8")
    sp.approve(actor_id="owner-1", actor_role="owner")
    assert 'status: "APPROVED"' in sprint_md.read_text(encoding="utf-8")
    sp.freeze(actor_id="owner-1", actor_role="owner")
    assert 'status: "FROZEN"' in sprint_md.read_text(encoding="utf-8")
    assert (sprint_root / "revisions/sprint-plan-revision-0001.md").is_file()

    # No call to reconcile_existing_planning_projections is needed anywhere in this journey.
    assert PlanningClosureApplicationService(platform, context_resolver=resolver).status(effective_roles=["owner"]).to_dict()["data"]["planning_closure"]["journey_state"] == "IMPLEMENTING_READY"

def test_c04_global_guided_next_action_reconciles_planning_closure(tmp_path: Path) -> None:
    platform, workspace, wid, resolver = fixture(tmp_path)
    svc = PlanningAuthoringApplicationService(platform, context_resolver=resolver)
    svc.generate_roadmap(actor_id="owner-1", actor_role="owner")
    _freeze_roadmap(workspace, wid)
    svc.derive_backlog(actor_id="owner-1", actor_role="owner")
    _freeze_backlog(workspace, wid)
    svc.derive_sprint(actor_id="owner-1", actor_role="owner", capacity_limit=2)
    sp = SprintPlanner(workspace, workspace_id=wid)
    sp.review(actor_id="owner-1", actor_role="owner")
    sp.approve(actor_id="owner-1", actor_role="owner")
    sp.freeze(actor_id="owner-1", actor_role="owner")

    guided = GuidedSDLCApplicationService(platform, context_resolver=resolver)
    status_payload = {"current_step": "planning-readiness", "progress": {"active_profile": "PRE_CODE"}}
    old_next = {"reason_code": "PRE_CODE_READY_PLANNING_NEXT"}
    reconciled = guided._apply_planning_journey_overlay(
        status_payload=status_payload,
        next_payload=old_next,
        pre_code={"pre_code_ready": True},
    )
    assert "planning_journey" not in status_payload
    assert status_payload["current_step"] == "story-context-readiness"
    assert reconciled["reason_code"] == "IMPLEMENTING_READY_STORY_CONTEXT_NEXT"
    assert reconciled["navigation_target"] == "ui.story-code-workbench"
    assert reconciled["available"] is True
    assert reconciled["mutating"] is False
    assert reconciled["executes_action"] is False


def test_c04_story_context_step_action_advisor_is_actionable_and_not_stale_precode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    guided = GuidedSDLCApplicationService(tmp_path)
    fake_status = SimpleNamespace(
        data={
            "workspace_id": "inventory-sales-local-greenfield",
            "project_status": {
                "current_step": "story-context-readiness",
                "pre_code_profile": {"all_stages_frozen": True, "pre_code_ready": True},
            },
        }
    )
    monkeypatch.setattr(guided, "project_status_primary", lambda **_kwargs: fake_status)
    result = guided.step_actions_primary(
        workspace_id="inventory-sales-local-greenfield",
        observed_at_utc="2026-09-29T12:00:00Z",
        effective_roles=["owner"],
        workspace_scopes=["inventory-sales-local-greenfield"],
    ).to_dict()
    assert result["ok"] is True
    advisor = result["data"]["advisor"]
    assert result["data"]["current_step"] == "story-context-readiness"
    assert advisor["recommended_action_id"] == "typed.implementing-ready-story-context"
    action = advisor["actions"][0]
    assert action["label"] == "Abrir Story Code Workbench"
    assert action["navigation_target"] == "ui.story-code-workbench"
    assert action["availability"] == "AVAILABLE"
    assert action["executable"] is True
    assert "siguiente frontera es Planning" not in action["purpose"]


def test_c04_provider_generates_project_generic_ids_for_distinct_workspaces(tmp_path: Path) -> None:
    outputs = []
    for name in ("alpha-greenfield", "beta-service"):
        platform, _workspace, _wid, resolver = fixture(tmp_path / name, workspace_id=name)
        svc = PlanningAuthoringApplicationService(platform, context_resolver=resolver)
        template = svc.status(effective_roles=["owner"]).to_dict()["data"]["planning_authoring"]["templates"]["roadmap"]
        outputs.append(template["roadmap_id"])
    assert outputs == ["planning-alpha-greenfield-roadmap", "planning-beta-service-roadmap"]
    assert outputs[0] != outputs[1]


def test_c04_requirement_authority_supports_rf_rnf_req_without_placeholder_invention(tmp_path: Path) -> None:
    ids = ("RF-101", "RNF-010", "REQ-ABC-1")
    platform, _workspace, _wid, resolver = fixture(tmp_path, workspace_id="generic-project", requirement_ids=ids)
    svc = PlanningAuthoringApplicationService(platform, context_resolver=resolver)
    status = svc.status(effective_roles=["owner"]).to_dict()["data"]["planning_authoring"]
    assert status["authority"]["requirement_ids"] == list(ids)
    roadmap = status["templates"]["roadmap"]
    traced = {link["target_id"] for m in roadmap["milestones"] for link in m["trace_links"] if link["kind"] == "requirement"}
    assert traced == set(ids)
    assert "REQ-001" not in traced


def test_c04_production_authoring_has_no_inventory_sales_fixture_coupling() -> None:
    root = Path(__file__).resolve().parents[1]
    for rel in (
        "src/devpilot_core/application/planning_authoring_service.py",
        "src/devpilot_core/application/planning_candidate_provider.py",
    ):
        text = (root / rel).read_text(encoding="utf-8").casefold()
        assert "inventory-sales" not in text


def test_c04_api_and_server_rbac_register_real_authoring_routes() -> None:
    root = Path(__file__).resolve().parents[1]
    paths = {(r.methods and next(iter(r.methods)), r.path) for r in planning_router.router.routes if getattr(r, "methods", None)}
    expected = {
        ("GET", "/api/v1/planning/authoring-context"),
        ("POST", "/api/v1/planning/roadmap/generate"),
        ("POST", "/api/v1/planning/backlog/derive"),
        ("POST", "/api/v1/planning/sprint/derive"),
    }
    assert expected <= paths
    for key in expected:
        assert key in api_security.API_ROUTE_POLICIES
    rbac = json.loads((root / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    route_keys = {(x["method"], x["path"]): x for x in rbac["route_policies"]}
    for key in expected:
        row = route_keys[key]
        assert row["human_session_required"] is True
        assert row["legacy_token_allowed"] is False
        assert row["workspace_scope_required"] is True


def test_c04_ui_contract_exposes_real_provider_and_removes_false_agent_placeholder_authority() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "ui/web/src/pages/RoadmapWorkbenchView.ts").read_text(encoding="utf-8")
    assert "Generar propuesta con DevPilot" in text
    assert "Importar JSON local" in text
    assert "type='file'" in text or "picker.type='file'" in text
    assert "Agent-assisted (no disponible)" in text
    assert "BLOCKED BY SEQUENCE" in text
    assert "Ver/editar JSON técnico avanzado" in text
    assert "Propuesta legible de Roadmap" in text
    assert "Propuesta legible de Backlog" in text
    assert "Propuesta legible de Sprint" in text
    assert "Editar esta propuesta en Manual" in text
    assert "route.disabled=!unlocked" in text
    assert "capacity.disabled=!unlocked" in text
    assert "v==='IMPORT'&&!picker.files?.[0]" in text
    assert "Provider" in text and "provider_id" in text and "strategy_id" in text
    assert "renderPlanningGuidance" in text
    assert "planningProgress" in text and "planningJourneyState" in text
    assert "13-D-01: Story context pack" not in text
    assert "Planning completado" in text
    assert "Story Code Workbench" in text
    assert "current.closure?.next_action?.label" in text
    assert "REQ-001" not in text and "RISK-001" not in text
    for token in (
        "Backlog aún no materializado",
        "Sprint aún no materializado",
        "Guardar Sprint DRAFT manual",
        "Edición manual guiada de Sprint",
        "Pendientes para sprints posteriores",
        "human artifact: roadmap.md",
        "human artifact: backlog.md",
        "human artifact: sprint_plan.md",
    ):
        assert token in text
    assert "!['MISSING','DRAFT'].includes(lifecycle)" in text
    assert "!['MISSING','DRAFT'].includes(lc)" in text
    closure_service = (root / "src/devpilot_core/application/planning_closure_service.py").read_text(encoding="utf-8")
    guided_service = (root / "src/devpilot_core/application/guided_sdlc_service.py").read_text(encoding="utf-8")
    authoring_service = (root / "src/devpilot_core/application/planning_authoring_service.py").read_text(encoding="utf-8")
    project_status_view = (root / "ui/web/src/pages/ProjectStatusView.ts").read_text(encoding="utf-8")
    step_action_view = (root / "ui/web/src/components/StepActionAdvisor.ts").read_text(encoding="utf-8")
    nav_presentation = (root / "ui/web/src/ux/navigationPresentation.ts").read_text(encoding="utf-8")
    assert "IMPLEMENTING_READY_STORY_CONTEXT_NEXT" in closure_service
    assert '"ui.story-code-workbench"' in closure_service
    assert "_apply_planning_journey_overlay" in guided_service
    assert "next_payload = self._apply_planning_journey_overlay" in guided_service
    assert "story-context-readiness" in guided_service
    assert 'else "story-code"' in authoring_service
    assert "atImplementationBoundary" in project_status_view
    assert "navigationPathFromServerTarget" in project_status_view
    assert "function navigationPath(target" not in project_status_view
    assert "navigationPathFromServerTarget" in step_action_view
    assert "'ui.story-code-workbench': '/story/code'" in nav_presentation
    assert 'typed.implementing-ready-story-context' in guided_service
    assert '"navigation_target": "ui.story-code-workbench"' in guided_service
    projection = (root / "src/devpilot_core/planning/human_projection.py").read_text(encoding="utf-8")
    assert 'canonical_authority: "json"' in projection
    assert "source_record_sha256" in projection
    assert "reconcile_existing_planning_projections" in projection
    css = (root / "ui/web/src/planning.css").read_text(encoding="utf-8")
    assert ".roadmap-workbench [hidden]{display:none!important}" in css
    assert ".planning-sprint-story-option" in css
    adr = (root / "docs/02_architecture/adrs/ADR-DEVPL-GSDLC-13-C-04-planning-canonical-json-human-projections.md").read_text(encoding="utf-8")
    report = (root / "docs/audits/DEVPL_GSDLC_13_C_04_C04_BR_105_IMPLEMENTATION_REPORT.md").read_text(encoding="utf-8")
    for doc in (adr, report):
        for token in ("doc_id:", "title:", "status:", "version:", "owner:", "updated:", "approval:"):
            assert token in doc
    assert "JSON remains the sole canonical authority" in adr
    assert "full regression: 0" in report
    registry = json.loads((root / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8"))
    registry_ids = {item["doc_id"] for item in registry["documents"]}
    assert "ADR-DEVPL-GSDLC-13-C-04-PLANNING-HUMAN-PROJECTIONS" in registry_ids
    assert "DEVPL-GSDLC-13-C-04-C04-BR-105-IMPLEMENTATION-REPORT" in registry_ids
