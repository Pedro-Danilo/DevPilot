from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import jsonschema
from fastapi.testclient import TestClient

from devpilot_core.application import AuthApplicationService, RBACApplicationService
from devpilot_core.application.guided_sdlc_service import GuidedSDLCApplicationService
from devpilot_core.guided_sdlc import AdvisorContext, ExecutionModeAdvisor, StepActionCatalog
from devpilot_core.guided_sdlc.models import EngineeringLifecycleStatus, MIPSoftwarePhase, WorkspaceEngineeringState
from devpilot_core.identity.auth_models import AuthenticatedPrincipal
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.interfaces.api.operator_flow_smoke import OPERATOR_FLOW_RUNTIME_SANDBOX_IGNORE_PATTERNS

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def ctx(step: str, *, role: str = "owner", provider: str = "AVAILABLE", budget: str = "PASS", artifact: str = "READY", miasi: str = "PASS") -> AdvisorContext:
    return AdvisorContext(
        workspace_id="devpilot-local",
        current_step=step,
        effective_roles=(role,),
        workspace_scopes=("devpilot-local",),
        artifact_readiness=artifact,
        miasi_gate_status=miasi,
        provider_status=provider,
        budget_status=budget,
        active_project_context=True,
    )


def test_05_d_catalog_schema_and_cross_registry_authority_pass():
    catalog = load(".devpilot/gsdlc/step_action_catalog.json")
    schema = load("docs/schemas/step_action_catalog.schema.json")
    jsonschema.Draft202012Validator(schema).validate(catalog)
    result = StepActionCatalog(ROOT).validate()
    assert result["status"] == "PASS"
    assert result["mip_steps_total"] == result["catalog_steps_total"] == 19
    assert result["actions_total"] == 136
    assert result["advisor_grants_capability"] is False
    assert result["server_policy_authoritative"] is True


def test_05_d_every_current_step_has_all_action_kinds_and_a_deterministic_route_or_explicit_block():
    catalog = load(".devpilot/gsdlc/step_action_catalog.json")
    expected = {"MANUAL", "PASTE", "UPLOAD_IMPORT", "EXTERNAL_EDITOR", "AGENT", "RAG", "TYPED_OPERATION"}
    advisor = ExecutionModeAdvisor(ROOT)
    for step in catalog["steps"]:
        assert expected <= {row["kind"] for row in step["actions"]}
        decision = advisor.advise(ctx(step["current_step"]))
        assert decision.status in {"PASS", "BLOCK"}
        if decision.status == "PASS":
            assert decision.recommended_action_id
            available = [row for row in decision.actions if row.availability == "AVAILABLE"]
            assert available and available[0].action_id == decision.recommended_action_id
        else:
            assert not decision.recommended_action_id


def test_05_d_ranking_is_stable_and_does_not_hide_alternatives():
    advisor = ExecutionModeAdvisor(ROOT)
    first = advisor.advise(ctx("requirements"))
    second = advisor.advise(ctx("requirements"))
    assert first.decision_fingerprint == second.decision_fingerprint
    assert first.recommended_action_id == "requirements.manual"
    assert [row.rank for row in first.actions] == sorted(row.rank for row in first.actions)
    assert {row.kind for row in first.actions} >= {"MANUAL", "PASTE", "UPLOAD_IMPORT", "EXTERNAL_EDITOR", "AGENT", "RAG", "TYPED_OPERATION"}


def test_05_d_wrong_role_policy_route_is_disabled_without_capability_grant():
    advisor = ExecutionModeAdvisor(ROOT)
    owner = advisor.advise(ctx("verification", role="owner"))
    developer = advisor.advise(ctx("verification", role="developer"))
    owner_quality = next(row for row in owner.actions if row.action_id == "verification.quality-execute")
    dev_quality = next(row for row in developer.actions if row.action_id == "verification.quality-execute")
    assert owner_quality.availability == "AVAILABLE" and owner_quality.executable is True
    assert owner_quality.approval_required is True
    assert dev_quality.availability == "UNAVAILABLE" and dev_quality.executable is False
    assert dev_quality.navigation_target is None
    assert "RBAC_ROLE_DENY" in {row.code for row in dev_quality.disabled_reasons}


def test_05_d_agent_and_rag_are_visible_but_never_executable_in_gsdlc_05():
    advisor = ExecutionModeAdvisor(ROOT)
    decision = advisor.advise(ctx("requirements", role="owner", provider="AVAILABLE", budget="PASS"))
    rows = [row for row in decision.actions if row.kind in {"AGENT", "RAG"}]
    assert {row.kind for row in rows} == {"AGENT", "RAG"}
    for row in rows:
        assert row.availability == "UNAVAILABLE" and row.executable is False and row.navigation_target is None
        assert row.risk.get("level") in {"high", "critical"}
        assert row.cost and row.tokens
        assert row.approval_required is True
        codes = {reason.code for reason in row.disabled_reasons}
        expected = "GSDLC_05_AGENT_EXECUTION_OUT_OF_SCOPE" if row.kind == "AGENT" else "GSDLC_05_RAG_EXECUTION_OUT_OF_SCOPE"
        assert expected in codes


def test_05_d_provider_and_budget_fail_closed_are_explainable():
    advisor = ExecutionModeAdvisor(ROOT)
    decision = advisor.advise(ctx("requirements", provider="NOT_AVAILABLE", budget="EXHAUSTED"))
    for row in [x for x in decision.actions if x.kind in {"AGENT", "RAG"}]:
        codes = {reason.code for reason in row.disabled_reasons}
        assert "PROVIDER_UNAVAILABLE" in codes
        assert "BUDGET_EXHAUSTED" in codes


def test_05_d_artifact_state_is_authoritative_input_for_typed_operations_but_authoring_remains_remediation():
    advisor = ExecutionModeAdvisor(ROOT)
    decision = advisor.advise(ctx("requirements", artifact="UNKNOWN"))
    manual = next(row for row in decision.actions if row.kind == "MANUAL")
    typed = next(row for row in decision.actions if row.kind == "TYPED_OPERATION")
    assert manual.availability == "AVAILABLE"
    assert typed.availability == "UNAVAILABLE"
    assert "ARTIFACT_STATE_UNKNOWN" in {row.code for row in typed.disabled_reasons}


def test_05_d_unknown_step_is_explicit_block_not_synthesized_advice():
    decision = ExecutionModeAdvisor(ROOT).advise(ctx("not-a-real-step"))
    assert decision.status == "BLOCK"
    assert decision.recommended_action_id is None
    assert decision.actions == ()


def test_05_d_api_openapi_rbac_ui_and_application_contract_are_in_parity():
    api = load(".devpilot/interfaces/api_route_contract_registry.json")
    rbac = load(".devpilot/identity/server_rbac_policy_catalog.json")
    ui = load(".devpilot/interfaces/ui_route_contract_registry.json")
    openapi = load("docs/07_interfaces/openapi_v1.json")
    route = next(row for row in api["routes"] if row["route_id"] == "api.guided-sdlc.step-actions")
    policy = next(row for row in rbac["route_policies"] if row["route_id"] == route["route_id"])
    project_status = next(row for row in ui["routes"] if row["route_id"] == "ui.project-status")
    assert route["path"] == "/api/v1/guided-sdlc/step-actions" and route["method"] == "GET"
    assert policy["human_session_required"] is True and policy["legacy_token_allowed"] is False
    assert route["route_id"] in project_status["allowed_api_routes"]
    assert "/api/v1/guided-sdlc/step-actions" in openapi["paths"]
    assert openapi["paths"][route["path"]]["get"]["x-devpilot-auth"] == "human-session-required"
    assert openapi["paths"][route["path"]]["get"]["security"] == [{"HumanSessionCookie": []}]


def test_05_d_ui_renders_server_decisions_without_recalculating_authority():
    component = (ROOT / "ui/web/src/components/StepActionAdvisor.ts").read_text(encoding="utf-8")
    page = (ROOT / "ui/web/src/pages/ProjectStatusView.ts").read_text(encoding="utf-8")
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    assert "Qué puedes hacer ahora" in component
    for token in ["disabled_reasons", "approval_required", "side_effects", "cost", "tokens", "navigation_target"]:
        assert token in component
    assert "innerHTML" not in component
    assert ").stepActions()" in page
    assert "/guided-sdlc/step-actions" in client
    assert "No se habilita ninguna acción por fallback" in component


def test_05_d_application_service_uses_project_status_plus_authenticated_roles_and_scopes(tmp_path):
    for rel in [".devpilot", "docs/06_miasi"]:
        source = ROOT / rel
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            source,
            target,
            ignore=shutil.ignore_patterns(*OPERATOR_FLOW_RUNTIME_SANDBOX_IGNORE_PATTERNS),
        )
    fingerprint = hashlib.sha256(os.path.normcase(str(tmp_path.resolve())).encode("utf-8")).hexdigest()
    state = WorkspaceEngineeringState(
        workspace_id="devpilot-local", project_id="devpilot-local", workspace_root_fingerprint=fingerprint,
        lifecycle_status=EngineeringLifecycleStatus.IN_PROGRESS, phase=MIPSoftwarePhase.REQUIREMENTS,
        current_step="requirements", sequence=0, created_at_utc="2026-08-24T00:00:00Z", updated_at_utc="2026-08-24T00:00:00Z",
        git={"head":None,"branch":None,"dirty":None,"fingerprint":None},
        artifacts=({"artifact_id":"requirements-specification","status":"DRAFT","source_ref":None,"fingerprint":None},),
        planning=(), quality=(), gates=(), blockers=(), revalidation={"status":"NOT_REQUIRED","reason_codes":[]}, source_fingerprints=(), next_action_ref=None,
    )
    store = tmp_path / "outputs/workspaces/devpilot-local"
    store.mkdir(parents=True)
    (store / "engineering_state.json").write_text(json.dumps(state.to_payload(), indent=2), encoding="utf-8")
    miasi = {
        "schema_id":"SCHEMA-DEVPL-MIASI-APPLICABILITY-CONTEXT-V1","schema_version":"1.0","workspace_id":"devpilot-local",
        "project":{"declared_ai_usage":False,"capabilities":[],"risk_level":"low","evidence_refs":["fixture:project"]},
        "features":[],"risk_review_status":"NOT_REQUIRED","evidence_refs":["fixture:05-d"]
    }
    (store / "miasi_applicability_context.json").write_text(json.dumps(miasi, indent=2), encoding="utf-8")
    result = GuidedSDLCApplicationService(tmp_path).step_actions_primary(
        workspace_id="devpilot-local", observed_at_utc="2026-08-24T00:00:01Z",
        effective_roles=["owner"], workspace_scopes=["devpilot-local"],
    )
    assert result.ok is True
    assert result.data["server_authoritative"] is True and result.data["actor_neutral"] is False
    assert result.data["mutations_performed"] is False and result.data["network_used"] is False and result.data["external_api_used"] is False
    advisor = result.data["advisor"]
    assert advisor["status"] == "PASS" and advisor["recommended_action_id"] == "requirements.manual"
    assert all(not row["executable"] for row in advisor["actions"] if row["kind"] in {"AGENT", "RAG"})


def test_05_d_rbac_application_facade_exposes_canonical_roles_used_by_step_actions_route():
    principal = AuthenticatedPrincipal(
        actor_id="local-owner", username="owner.local", display_name="Owner",
        roles=("owner",), workspace_scopes=("devpilot-local",),
    )
    assert RBACApplicationService(ROOT).canonical_roles(principal) == ("owner",)


def test_05_d_step_actions_http_route_does_not_raise_server_error(tmp_path):
    for rel in [".devpilot", "docs/06_miasi"]:
        source = ROOT / rel
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            source,
            target,
            ignore=shutil.ignore_patterns(*OPERATOR_FLOW_RUNTIME_SANDBOX_IGNORE_PATTERNS),
        )
    fingerprint = hashlib.sha256(os.path.normcase(str(tmp_path.resolve())).encode("utf-8")).hexdigest()
    out = tmp_path / "outputs/workspaces/devpilot-local"
    out.mkdir(parents=True)
    state = WorkspaceEngineeringState(
        workspace_id="devpilot-local", project_id="devpilot-local", workspace_root_fingerprint=fingerprint,
        lifecycle_status=EngineeringLifecycleStatus.IN_PROGRESS, phase=MIPSoftwarePhase.REQUIREMENTS,
        current_step="requirements", sequence=0, created_at_utc="2026-08-25T00:00:00Z", updated_at_utc="2026-08-25T00:00:01Z",
        git={"head":None,"branch":None,"dirty":None,"fingerprint":None},
        artifacts=({"artifact_id":"requirements-specification","status":"APPROVED","source_ref":None,"fingerprint":None},),
        planning=(), quality=(), gates=(), blockers=(), revalidation={"status":"NOT_REQUIRED","reason_codes":[]}, source_fingerprints=(), next_action_ref=None,
    )
    (out / "engineering_state.json").write_text(json.dumps(state.to_payload(), indent=2), encoding="utf-8")
    (out / "miasi_applicability_context.json").write_text(json.dumps({
        "schema_id":"SCHEMA-DEVPL-MIASI-APPLICABILITY-CONTEXT-V1","schema_version":"1.0","workspace_id":"devpilot-local",
        "project":{"declared_ai_usage":False,"capabilities":[],"risk_level":"low","evidence_refs":["fixture:05d-recovery"]},
        "features":[],"risk_review_status":"NOT_REQUIRED","evidence_refs":["fixture:05d-recovery"]
    }, indent=2), encoding="utf-8")
    assert not list(tmp_path.rglob("auth.db*"))
    assert not list(tmp_path.rglob("devpilot.db*"))
    auth = AuthApplicationService(tmp_path)
    client = TestClient(create_app(tmp_path, api_token="legacy-05d-recovery", auth_service=auth), raise_server_exceptions=False)
    created = client.post("/api/v1/auth/bootstrap/owner", json={
        "username":"owner.local", "display_name":"Owner", "password":"A-very-long-local-password-123"
    }, headers={"origin":"http://127.0.0.1:5173"})
    assert created.status_code == 201, created.text
    response = client.get("/api/v1/guided-sdlc/step-actions")
    assert response.status_code != 500, response.text
    assert response.status_code in {200, 403}, response.text
    body = response.json()
    assert body["operation"] == "guided_sdlc.step_actions"
    if response.status_code == 200:
        assert body["data"]["server_authoritative"] is True
        assert body["data"]["advisor"]["recommended_action_id"] == "requirements.manual"
    else:
        assert body["findings"][0]["id"] == "API_POLICY_BINDING_BLOCK"
