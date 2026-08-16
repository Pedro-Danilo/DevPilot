from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def j(rel): return json.loads((ROOT/rel).read_text(encoding="utf-8-sig"))
def t(rel): return (ROOT/rel).read_text(encoding="utf-8-sig")
def test_00_e_closes_backlog_and_authorizes_only_01():
    s=j(".devpilot/project_state.json"); c=j(".devpilot/gsdlc/g00e_closure_contract.json")
    assert s["gsdlc_00_status"]=="closed/PASS"
    assert s["gsdlc_00_d_status"]=="closed/PASS"
    assert s["gsdlc_00_e_status"]=="closed/PASS"
    assert s["gsdlc_next_backlog_authorized"]=="DEVPL-GSDLC-01"
    assert s["gsdlc_01_authorized"] is True
    assert s["post_h_eval_002_execution_status"]=="paused-before-02-b"
    assert s["post_h_eval_002_02_b_executed"] is False
    assert c["next"]["backlog_authorized"]=="DEVPL-GSDLC-01"
def test_00_e_current_repo_is_successor_and_repo341_remains_parent():
    s=j(".devpilot/project_state.json"); c=j(".devpilot/gsdlc/g00e_closure_contract.json")
    name=s["current_repo"]
    assert re.fullmatch(r"repo_DevPilot_Local_\d+_DEVPL_GSDLC_00_PROGRAM_ACTIVATION_REBASELINE\.zip",name)
    assert s["gsdlc_current_canonical_repo"]==name
    assert c["baseline_artifact_name"]==name
    assert c["parent_repo341"]["immutable"] is True
    assert c["parent_repo341"]["git_commit"]=="cff43e8d992ff6139bd13bb1809ce4d497ae0952"
def test_00_e_release_freshness_criteria_tracks_successor_repo():
    s=j(".devpilot/project_state.json"); q=j(".devpilot/release/local_release_candidate_criteria.json")
    item=next(x for x in q["evidence"] if x["evidence_id"]=="project-state-current-repo")
    assert item["expected_fields"]["current_repo"]==s["current_repo"]
    assert item["expected_fields"]["current_micro_sprint"]=="POST-H-EVAL-002-02-B"
def test_00_e_no_go_and_runtime_remain_closed():
    s=j(".devpilot/project_state.json"); c=j(".devpilot/gsdlc/g00e_closure_contract.json")
    assert s["gsdlc_runtime_implemented"] is False
    assert s["gsdlc_auth_runtime_enabled"] is False
    assert s["gsdlc_provider_runtime_enabled"] is False
    assert s["gsdlc_filesystem_write_enabled"] is False
    safe=c["safety"]
    for k in ["runtime_guided_sdlc_implemented","multiuser_auth_enabled","generic_filesystem_write_enabled","external_api_enabled","remote_execution_enabled","connector_write_enabled","plugin_execution_enabled","arbitrary_shell_enabled"]:
        assert safe[k] is False
def test_00_e_full_regression_policy_is_required_once():
    d=j("docs/audits/devpl_gsdlc_00_e_full_regression_decision.json")
    assert d["decision"]=="REQUIRED"
    assert d["execution_policy"]["run_once_before_seal_commit"] is True
    assert d["execution_policy"]["rerun_after_seal"] is False
    assert d["source_test_impact"]["p0_selected"]==61
    assert d["source_test_impact"]["recommended_tests"]==218
    r=d["execution_result"]
    assert r["status"]=="PASS"
    assert r["validation_mode"]=="composite-full-regression-selective-retest"
    assert r["corrective_commit"]=="066c0ebce54e902b46e494ae111960e472dba21c"
    assert r["selective_retest"]["passed"]==47
    assert r["full_pytest_repeated"] is False
def test_00_e_historical_sweep_final_has_zero_unclassified():
    d=j("docs/audits/devpl_gsdlc_00_e_historical_contract_sweep_final.json")
    assert d["matches_total"]==d["classified_total"]==546
    assert d["unclassified_total"]==0
    assert d["tests_rewritten_only_to_pass"] is False
    assert d["no_go_flags_weakened"] is False
    r=d["preseal_residual_reconciliation"]
    assert r["residual_failures_total"]==5
    assert r["corrective_commit"]=="066c0ebce54e902b46e494ae111960e472dba21c"
    assert r["selective_retest_passed"]==47
    assert r["status"]=="reconciled-before-baseline"
def test_00_e_docs_and_registry_are_synchronized():
    r=j(".devpilot/docs_governance/source_registry.json")
    # gsdlc_last_registered_micro_sprint is a mutable registry pointer.
    # Freeze the 00-E historical close in the project-state snapshot instead.
    assert r["project_state_snapshot"]["gsdlc_current_micro_sprint"]=="DEVPL-GSDLC-00-E"
    assert r["gsdlc_last_registered_micro_sprint"].startswith("DEVPL-GSDLC-")
    assert r["gsdlc_program_status"]=="active/post-00-closed/01-authorized"
    assert 'backlog_status: "closed/PASS"' in t("docs/backlogs/DEVPL-GSDLC-00_program_activation_rebaseline_and_pilot_pause.md")
    assert "DEVPL-GSDLC-01" in t("docs/00_product/DEVPL_GSDLC_product_evolution_roadmap.md")
