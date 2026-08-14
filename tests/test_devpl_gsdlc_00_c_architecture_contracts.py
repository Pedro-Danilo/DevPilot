from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def text(rel:str)->str:
    return (ROOT/rel).read_text(encoding="utf-8")

def data(rel:str)->dict:
    return json.loads(text(rel))

ADR_PATHS=[
 "docs/02_architecture/adrs/ADR-GSDLC-001-guided-sdlc-engine.md",
 "docs/02_architecture/adrs/ADR-GSDLC-002-state-separation.md",
 "docs/02_architecture/adrs/ADR-GSDLC-003-local-authenticated-operator-boundary.md",
 "docs/02_architecture/adrs/ADR-GSDLC-004-ui-complete-normal-journey.md",
]

def test_gsdlc_00_c_four_adrs_are_explicitly_planned_not_runtime():
    for rel in ADR_PATHS:
        value=text(rel)
        assert 'status: "reviewed"' in value
        assert 'runtime_implemented: false' in value
        assert "planned-GSDLC" in value

def test_gsdlc_00_c_guided_boundary_never_bypasses_application_service():
    target=data(".devpilot/gsdlc/architecture_target_contract.json")
    assert target["guided_sdlc"]["application_service_required"] is True
    assert target["guided_sdlc"]["deterministic_transitions"] is True
    assert target["guided_sdlc"]["llm_transition_authority"] is False
    chain=target["entry_boundary"]["mandatory_chain"]
    assert chain.index("ApplicationService") < chain.index("GuidedSDLCService")
    forbidden=set(target["entry_boundary"]["forbidden_bypasses"])
    assert {"React->filesystem","React->Git","React->core","browser->arbitrary shell"}.issubset(forbidden)

def test_gsdlc_00_c_state_domains_have_distinct_owners_and_reconciliation():
    target=data(".devpilot/gsdlc/architecture_target_contract.json")
    domains=target["state_domains"]
    assert [d["name"] for d in domains]==["PlatformState","WorkspaceEngineeringState","RuntimeOperationalState"]
    assert len({d["owner"] for d in domains})==3
    engineering=domains[1]
    assert "REVALIDATION_REQUIRED" in engineering["reconciliation"]
    assert "credentials" in engineering["must_not_contain"]

def test_gsdlc_00_c_local_auth_successor_does_not_enable_multiuser_or_enterprise():
    target=data(".devpilot/gsdlc/architecture_target_contract.json")
    auth=target["local_auth_successor"]
    assert auth["runtime_enabled"] is False
    for key in ["enterprise_iam","tenancy","sso","oidc","public_api","non_local_api"]:
        assert auth[key] is False
    assert "client cannot assert approver identity" in auth["approval_actor_binding"]
    historical=text("docs/adr/ADR-POSTH-034-D-multiuser-auth-boundary.md")
    assert 'decision_status: "continue-blocked"' in historical
    assert 'multiuser_auth_enabled: false' in historical
    identity=data(".devpilot/identity/identity_registry.json")
    assert identity["defaults"]["auth_remote_enabled"] is False
    assert identity["defaults"]["credentials_stored"] is False

def test_gsdlc_00_c_step_action_advisor_is_deterministic():
    target=data(".devpilot/gsdlc/architecture_target_contract.json")
    advisor=target["step_action_advisor"]
    assert advisor["deterministic"] is True
    assert advisor["llm_decides_availability"] is False
    assert set(["MANUAL","PASTE","UPLOAD_IMPORT","EXTERNAL_EDITOR","AGENT","RAG","TYPED_OPERATION"]).issubset(advisor["modes"])
    assert "disabled reasons" in advisor["outputs"]

def test_gsdlc_00_c_c4_target_uses_explicit_status_legend_and_current_ui_is_not_erased():
    for rel in ["docs/02_architecture/c4_context.md","docs/02_architecture/c4_container.md","docs/02_architecture/c4_component.md"]:
        value=text(rel)
        for status in ["implemented-current","planned-GSDLC","blocked-by-policy","future-out-of-scope"]:
            assert status in value
    ui=data(".devpilot/interfaces/ui_capability_registry.json")
    assert ui["summary"]["ui_routes_total"] >= 9
    assert ui["summary"]["ui_routes_mapped_total"] == ui["summary"]["ui_routes_total"]

def test_gsdlc_00_c_application_boundary_and_no_arbitrary_shell_are_preserved():
    boundary=text("docs/02_architecture/application_service_boundary_map.md")
    assert "UI project-centric" in boundary
    assert "→ ApplicationService" in boundary
    assert "→ GuidedSDLCService" in boundary
    shell=text("docs/architecture/adr_ui_no_arbitrary_shell.md").lower()
    assert "no arbitrary shell" in shell or "prohibit-arbitrary-shell" in shell
    target=data(".devpilot/gsdlc/architecture_target_contract.json")
    assert target["no_go"]["arbitrary_shell"] is False

def test_gsdlc_00_c_project_state_advances_only_contract_state():
    state=data(".devpilot/project_state.json")
    assert state["gsdlc_00_b_status"]=="closed/PASS"
    assert state["gsdlc_00_b_implementation_commit"]=="a2eebf734784eb1f07a3cec3fd1b5cfe32468567"
    assert state["gsdlc_00_c_status"]=="closed/PASS"
    assert state["gsdlc_00_c_program_status_at_close"]=="active/00-c"
    assert state["gsdlc_00_c_current_micro_sprint_at_close"]=="DEVPL-GSDLC-00-C"
    assert state["gsdlc_00_c_next_micro_sprint_at_close"]=="DEVPL-GSDLC-00-D"
    assert state["gsdlc_00_c_architecture_adrs_total"]==4
    assert state["gsdlc_00_c_state_domains_total"]==3
    assert state["gsdlc_runtime_implemented"] is False
    assert state["gsdlc_auth_runtime_enabled"] is False

def test_gsdlc_00_c_historical_sweep_scopes_future_without_rewriting_history():
    sweep=data("docs/audits/devpl_gsdlc_00_c_historical_contract_sweep.json")
    classes={x["classification"] for x in sweep["classifications"]}
    assert {"historical-freeze","current-active","successor-needed"}.issubset(classes)
    assert sweep["runtime_source_changed"] is False
    assert sweep["network_used"] is False
    assert sweep["external_api_used"] is False
    assert sweep["multiuser_auth_enabled"] is False
    assert sweep["uoc_route_count_frozen_as_future_max"] is False
