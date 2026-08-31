from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def data(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

def test_00_d_threat_model_has_complete_owned_successor_controls():
    threat = text("docs/03_security/security_threat_model.md")
    trace = data("docs/audits/devpl_gsdlc_00_d_security_control_traceability.json")
    assert trace["threats_total"] == 18
    assert trace["threats_traced"] == 18
    assert trace["coverage_percent"] == 100
    assert trace["critical_without_control"] == 0
    assert trace["critical_without_test_owner"] == 0
    assert len({x["threat_id"] for x in trace["entries"]}) == 18
    assert len({x["control_id"] for x in trace["entries"]}) == 18
    for i in range(1, 19):
        assert f"GSDLC-TM-{i:03d}" in threat
        assert f"GSDLC-CTRL-{i:03d}" in threat

def test_00_d_test_strategy_has_eleven_layers_and_deterministic_gate_separation():
    strategy = text("docs/04_quality/test_strategy.md")
    contract = data(".devpilot/gsdlc/security_test_reconciliation_contract.json")
    assert contract["testing"]["layers_total"] == 11
    assert len(contract["testing"]["layers"]) == 11
    assert contract["testing"]["provider_tests_do_not_decide_deterministic_gates"] is True
    for layer in range(1, 12):
        assert f"| L{layer} |" in strategy
    assert "full regression" in strategy.lower()
    assert "Browser acceptance" in strategy
    assert "restart/resume/reconciliation" in strategy.lower()

def test_00_d_historical_sweep_classifies_every_required_search_match():
    sweep = data("docs/audits/devpl_gsdlc_00_d_historical_contract_sweep.json")
    assert sweep["matches_total"] == 546
    assert sweep["classified_total"] == 546
    assert sweep["unclassified_total"] == 0
    assert sum(sweep["classification_counts"].values()) == 546
    assert sweep["classification_counts"]["historical-freeze"] == 322
    assert sweep["classification_counts"]["current-active"] == 202
    assert sweep["classification_counts"]["successor-needed"] == 22
    assert sweep["tests_rewritten_only_to_pass"] == 0
    assert sweep["no_go_flags_weakened"] is False
    allowed = {"historical-freeze", "current-active", "successor-needed", "deprecated-after-proof"}
    assert {x["classification"] for x in sweep["items"]} <= allowed

def test_00_d_migration_plan_scopes_known_false_regression_hotspots():
    plan = data("docs/audits/devpl_gsdlc_00_d_historical_contract_migration_plan.json")
    ids = {x["migration_id"] for x in plan["migration_items"]}
    assert ids == {f"GSDLC-HCM-{i:03d}" for i in range(1, 9)}
    assert plan["unclassified_total"] == 0
    assert plan["policy"]["no_history_rewrite"] is True
    assert plan["policy"]["no_test_change_only_to_make_pytest_pass"] is True
    assert plan["policy"]["global_false_not_flipped_for_future_capability"] is True

def test_00_d_prior_gsdlc_contracts_freeze_close_state_not_future_program_pointer():
    a = text("tests/test_devpl_gsdlc_00_a_program_activation.py")
    b = text("tests/test_devpl_gsdlc_00_b_product_requirements.py")
    c = text("tests/test_devpl_gsdlc_00_c_architecture_contracts.py")
    assert 'gsdlc_00_a_program_status_at_close' in a
    assert 'gsdlc_program_status"] in {"active/00-a", "active/00-b"}' not in a
    assert 'gsdlc_00_b_program_status_at_close' in b
    assert 'gsdlc_program_status"] in {"active/00-b", "active/00-c"}' not in b
    assert 'gsdlc_00_c_program_status_at_close' in c
    assert 'gsdlc_current_micro_sprint"]=="DEVPL-GSDLC-00-C"' not in c

def test_00_d_pilot_and_uoc_tests_use_scoped_checkpoint_not_global_progression():
    activation = text("tests/test_post_h_eval_002_activation_contract.py")
    closure = text("tests/test_post_h_eval_002_01_d_governance_closure_327.py")
    uoc8 = text("tests/test_post_h_eval_002_uoc_008_contracts.py")
    uoc11 = text("tests/test_post_h_eval_002_uoc_011_final_reconciliation.py")
    for source in (activation, closure, uoc8, uoc11):
        assert "post_h_eval_002_current_micro_sprint" in source
        assert "post_h_eval_002_next_micro_sprint" in source
    assert 'state["current_micro_sprint"] == CURRENT_MICRO' not in activation
    assert 'state["post_h_eval_002_current_micro_sprint"] == "POST-H-EVAL-002-02-B"' in uoc8
    assert "s['post_h_eval_002_current_micro_sprint']=='POST-H-EVAL-002-02-B'" in uoc11

def test_00_d_global_state_no_longer_has_pre_gsdlc_current_micro_allowlist():
    global_test = text("tests/test_project_global_state.py")
    assert 'assert state.get("post_h_eval_002_current_micro_sprint") == "POST-H-EVAL-002-02-B"' in global_test
    assert 'assert state.get("post_h_eval_002_next_micro_sprint") == "POST-H-EVAL-002-02-C"' in global_test
    # The old large allowlist was the false-regression pattern.
    assert 'assert state["current_micro_sprint"] in {"POST-H-033-D"' not in global_test
    assert 'assert state.get("current_micro_sprint") in {"POST-H-033-D"' not in global_test

def test_00_d_uoc_route_baseline_is_not_future_maximum():
    ctest = text("tests/test_devpl_gsdlc_00_c_architecture_contracts.py")
    assert 'ui["summary"]["ui_routes_total"] >= 9' in ctest
    assert 'ui["summary"]["ui_routes_mapped_total"] == ui["summary"]["ui_routes_total"]' in ctest
    # UOC historical browser matrix may still freeze 9 routes / 108 cases.
    uoc11 = text("tests/test_post_h_eval_002_uoc_011_contracts.py")
    assert "len(m['routes'])==9" in uoc11
    assert "cases_total']==108" in uoc11

def test_00_d_no_go_flags_remain_false_and_auth_is_not_enabled():
    state = data(".devpilot/project_state.json")
    contract = data(".devpilot/gsdlc/security_test_reconciliation_contract.json")
    assert state["gsdlc_00_c_status"] == "closed/PASS"
    assert state["gsdlc_00_c_implementation_commit"] == "3c2dbff91eaddbbb92af41bc7ac6b9aacb309ba0"
    assert state["gsdlc_00_c_adrs_owner_approved"] is False
    assert state["gsdlc_00_c_adrs_review_status"] == "reviewed/pending-owner-adjudication"
    assert state["gsdlc_00_d_program_status_at_close"] == "active/00-d"
    assert state["gsdlc_00_d_current_micro_sprint_at_close"] == "DEVPL-GSDLC-00-D"
    assert state["gsdlc_00_d_next_micro_sprint_at_close"] == "DEVPL-GSDLC-00-E"
    for key in (
        "multiuser_auth_enabled", "filesystem_write_allowed", "external_api_allowed",
        "remote_execution_enabled", "connector_write_enabled", "plugin_execution_enabled"
    ):
        assert state[key] is False, key
    security = contract["security"]
    assert security["auth_runtime_enabled"] is False
    assert security["multiuser_auth_enabled"] is False
    assert security["generic_filesystem_write_enabled"] is False
    assert security["external_api_allowed_by_default"] is False
    assert security["remote_execution_enabled"] is False
    assert security["connector_write_enabled"] is False
    assert security["plugin_arbitrary_execution_enabled"] is False
    assert security["arbitrary_shell_allowed"] is False

def test_00_d_c_adrs_remain_reviewed_pending_owner_and_runtime_stays_planned():
    for rel in (
        "docs/02_architecture/adrs/ADR-GSDLC-001-guided-sdlc-engine.md",
        "docs/02_architecture/adrs/ADR-GSDLC-002-state-separation.md",
        "docs/02_architecture/adrs/ADR-GSDLC-003-local-authenticated-operator-boundary.md",
        "docs/02_architecture/adrs/ADR-GSDLC-004-ui-complete-normal-journey.md",
    ):
        value = text(rel)
        assert 'status: "reviewed"' in value
        assert 'approval: "pending_owner_00_c_adjudication"' in value
        assert 'runtime_implemented: false' in value

def test_00_d_source_registry_and_tcr_register_successor_governance():
    registry = data(".devpilot/docs_governance/source_registry.json")
    ids = {x["doc_id"] for x in registry["documents"]}
    required = {
        "DEVPL-SEC-001","DEVPL-QUAL-001","DEVPL-GSDLC-00-D-SECURITY-TEST-RECONCILIATION",
        "DEVPL-GSDLC-00-D-HISTORICAL-CONTRACT-SWEEP",
        "DEVPL-GSDLC-00-D-HISTORICAL-CONTRACT-MIGRATION-PLAN",
        "DEVPL-GSDLC-00-D-SECURITY-CONTROL-TRACEABILITY",
        "DEVPL-GSDLC-00-D-TEST-IMPACT-BASELINE",
    }
    assert required <= ids
    assert registry["gsdlc_00_d_last_registered_micro_sprint_at_close"] == "DEVPL-GSDLC-00-D"
    assert registry["gsdlc_00_c_last_registered_micro_sprint_at_close"] == "DEVPL-GSDLC-00-C"
    v1 = data(".devpilot/testing/test_contract_registry.json")
    v2 = data(".devpilot/testing/test_contract_registry_v2.json")
    c1 = next(x for x in v1["contracts"] if x["contract_id"] == "devpl-gsdlc-00-d-security-test-reconciliation")
    c2 = next(x for x in v2["contracts"] if x["contract_id"] == "devpl-gsdlc-00-d-security-test-reconciliation")
    assert c1["network_allowed"] is False and c1["external_api_allowed"] is False
    assert c2["network_allowed"] is False and c2["external_api_allowed"] is False
    assert c2["required_for_security_gate"] is True
    assert c2["security_negative_required"] is True
