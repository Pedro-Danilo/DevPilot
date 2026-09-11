from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_api_route_is_registered_read_only_human_session_project_scoped():
    api = load_json(".devpilot/interfaces/api_route_contract_registry.json")
    route = next(row for row in api["routes"] if row["route_id"] == "api.release.readiness")
    assert route["path"] == "/api/v1/release/readiness"
    assert route["method"] == "GET"
    assert route["mutations_allowed"] is False
    assert route["source_mutation_allowed"] is False
    assert route["external_api_allowed"] is False

    rbac = load_json(".devpilot/identity/server_rbac_policy_catalog.json")
    policy = next(row for row in rbac["route_policies"] if row["route_id"] == "api.release.readiness")
    assert policy["human_session_required"] is True
    assert policy["workspace_scope_required"] is True
    assert policy["legacy_token_allowed"] is False
    assert "release-manager" in policy["allowed_roles"] and "owner" in policy["allowed_roles"]


def test_ui_mapping_is_project_scoped_read_only_and_authority_separated():
    ui = load_json(".devpilot/interfaces/ui_route_contract_registry.json")
    route = next(row for row in ui["routes"] if row["route_id"] == "ui.release-readiness")
    assert route["path"] == "/release/readiness"
    assert route["allowed_api_routes"] == ["api.release.readiness"]
    assert route["shows_mutation_controls"] is False
    assert route["state_contract"]["unknown"] is True
    assert route["state_contract"]["approval_separated"] is True

    main = (ROOT / "ui/web/src/main.ts").read_text(encoding="utf-8")
    page = (ROOT / "ui/web/src/pages/ReleaseReadinessView.ts").read_text(encoding="utf-8")
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    assert "path: '/release/readiness'" in main and "scope: 'project'" in main
    assert "renderReleaseReadinessView" in main
    assert "async releaseReadiness()" in client and "'/release/readiness'" in client
    assert "readiness NO equivale a aprobación" in page
    assert "modelos/agentes" in page.lower()


def test_activation_rebind_keeps_repo420_and_zero_full_budget_in_11_a():
    state = load_json(".devpilot/project_state.json")
    assert state["current_repo"] == "repo_DevPilot_Local_420_DEVPL_GSDLC_10_E_STORY_CYCLE_BROWSER_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip"
    assert state["current_phase"] == "DEVPL-GSDLC-11"
    assert state["current_micro_sprint"] == "DEVPL-GSDLC-11-A"
    assert state["gsdlc_10_status"] == "CLOSED/PASS/WINDOWS-VALIDATED/COMPOSITE-RECOVERY"
    assert state["gsdlc_11_a_full_regression_runs"] == 0
    assert state["gsdlc_11_full_regression_budget_consumed"] == 0
    assert state["gsdlc_11_full_regression_budget_total"] == 1
    assert state["gsdlc_11_b_authorized"] is False
    package = load_json("ui/web/package.json")
    assert package["version"] == "0.31.0-gsdlc-11-a"
    assert package["devpilot"]["currentSprint"] == "DEVPL-GSDLC-11-A"


def test_schema_and_no_overclaim_contract_are_registered():
    schema = load_json("docs/schemas/release_readiness_projection.schema.json")
    assert schema["properties"]["state"]["enum"] == ["RELEASE_READY", "BLOCKED", "UNKNOWN"]
    claims = schema["properties"]["claims"]["properties"]
    assert claims["enterprise_ready_claim"]["const"] is False
    assert claims["compliance_certification_claim"]["const"] is False
    assert claims["public_release_claim"]["const"] is False
    authority = schema["properties"]["release_authority"]["properties"]
    assert authority["readiness_is_release_approval"]["const"] is False
    assert authority["model_or_agent_can_approve"]["const"] is False
