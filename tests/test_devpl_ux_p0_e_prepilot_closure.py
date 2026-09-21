from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def j(rel: str): return json.loads((ROOT/rel).read_text(encoding="utf-8"))

def test_e_rebind_is_repo435_to_repo436():
    ps=j('.devpilot/project_state.json')
    assert ps['current_micro_sprint'] in {'DEVPL-UX-P0-E','DEVPL-GSDLC-13-A'}
    assert ps['current_repo'] in {'repo_DevPilot_Local_435_DEVPL_UX_P0_D_CROSS_SURFACE_OPERATIONAL_PATTERNS_WINDOWS_VALIDATED_CANDIDATE.zip','repo_DevPilot_Local_436_DEVPL_UX_P0_E_PRE_PILOT_PRODUCTIZATION_RC_WINDOWS_VALIDATED_CANDIDATE.zip','repo_DevPilot_Local_437_DEVPL_GSDLC_13_A_TRANSITION_REBIND_AUTHORITY_HYGIENE_WINDOWS_VALIDATED_CANDIDATE.zip'}
    assert ps['ux_p0_successor_repo']=='repo_DevPilot_Local_436_DEVPL_UX_P0_E_PRE_PILOT_PRODUCTIZATION_RC_WINDOWS_VALIDATED_CANDIDATE.zip'
    assert ps['ux_p0_d_status']=='CLOSED/PASS/WINDOWS-VALIDATED'

def test_e_full_budget_is_unconsumed_and_single_use():
    ps=j('.devpilot/project_state.json')
    assert ps['ux_p0_e_full_regression_runs'] in {0,1}
    assert ps['ux_p0_e_second_full_regression_runs']==0
    if ps['ux_p0_e_status']=='CLOSED/PASS/WINDOWS-VALIDATED':
        assert ps['ux_p0_e_full_regression_runs']==1
        assert str(ps['ux_p0_full_regression_budget']).startswith('1/1')
    else:
        assert ps['ux_p0_e_full_regression_runs']==0
        assert str(ps['ux_p0_full_regression_budget']).startswith('0/1')
    plan=j('docs/audits/DEVPL_UX_P0_E_FULL_REGRESSION_EXECUTION_PLAN.json')
    assert plan['logical_full_allowed']==1 and plan['second_full_allowed'] is False
    assert plan['functional_fail_policy']=='PRESERVE/NO-RERUN/COMPOSITE-RECOVERY'

def test_e_authority_metadata_is_aligned():
    ps=j('.devpilot/project_state.json'); sr=j('.devpilot/docs_governance/source_registry.json'); pkg=j('ui/web/package.json')
    assert sr['current_repo']==ps['current_repo']
    assert sr['current_micro_sprint']==ps['current_micro_sprint']
    assert pkg['devpilot']['currentSprint'] in {'DEVPL-UX-P0-E','DEVPL-GSDLC-13-A'}
    assert pkg['devpilot']['uxP0DStatus']=='closed/PASS/WINDOWS-VALIDATED'

def test_current_frx_profile_is_locked():
    fr=j('.devpilot/testing/full_regression_execution_profile_current.json')
    assert fr['status']=='current-active'
    assert fr['current_profile_id']=='frx-v2.4-current'
    assert fr['current_profile_sha256']=='2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219'
    isolation=j('.devpilot/testing/test_isolation_registry.json')
    assert isolation['collection_sha256']=='9a77ad63fbf5fb96088e5777a2da8afb53e30fa44c016b01f93363d1b090d0ab'
    assert len(isolation['entries'])==3225
    by_nodeid={entry['nodeid']:entry for entry in isolation['entries']}
    for nodeid in [
      'tests/test_devpl_ux_p0_e_prepilot_closure.py::test_e_rebind_is_repo435_to_repo436',
      'tests/test_devpl_ux_p0_e_prepilot_closure.py::test_e_full_budget_is_unconsumed_and_single_use',
      'tests/test_devpl_ux_p0_e_prepilot_closure.py::test_e_authority_metadata_is_aligned',
      'tests/test_devpl_ux_p0_e_prepilot_closure.py::test_current_frx_profile_is_locked',
      'tests/test_devpl_ux_p0_e_prepilot_closure.py::test_e_required_closure_artifacts_exist',
      'tests/test_devpl_ux_p0_e_prepilot_closure.py::test_e_performance_closure_uses_repo435_parity_not_stale_uoc011_threshold_widening',
    ]:
      assert nodeid in by_nodeid
      if by_nodeid[nodeid]['state']=='UNCLASSIFIED':
        assert by_nodeid[nodeid]['parallel_safe'] is False

def test_e_required_closure_artifacts_exist():
    for rel in [
      'DEVPL_UX_P0_D_FINAL_CLOSURE_ADJUDICATION_v1_0_0.md',
      '05_PROMPT_DEVPL_UX_P0_E_v1_0_1_APPROVED_REBOUND_REPO435.md',
      'SPRINT_DEVPL_UX_P0_E_v1_0_0_APPROVED_REBOUND_REPO435.md',
      'DEVPL_UX_P0_PRE_PILOT_PRODUCTIZATION_BACKLOG_v1_0_3_APPROVED_REBOUND_REPO435.md',
      'docs/audits/DEVPL_UX_P0_E_BROWSER_USABILITY_PLAN_v1_0_0.md',
      'docs/audits/DEVPL_UX_P0_E_PERFORMANCE_BUDGET.json',
      'docs/audits/DEVPL_UX_P0_E_CONTRACT_RECONCILIATION_SWEEP.json',
      'docs/audits/DEVPL_UX_P0_E_CLEAN_INSTALL_PLAN.json',
    ]:
      assert (ROOT/rel).is_file(), rel

def test_e_performance_closure_uses_repo435_parity_not_stale_uoc011_threshold_widening():
    budget=j('docs/audits/DEVPL_UX_P0_E_PERFORMANCE_BUDGET.json')
    hist=budget['historical_uoc011_source_smoke']
    assert hist['baseline_repo435_status']=='BLOCK/INHERITED-PRE-EXISTING'
    assert hist['baseline_source_ui_bytes']==939755
    assert hist['baseline_largest_source_bytes']==94240
    assert hist['ux_p0_e_changes_ui_web_src'] is False
    assert 'exceeds exact repo435 baseline' in hist['closure_policy']
    sweep=j('docs/audits/DEVPL_UX_P0_E_CONTRACT_RECONCILIATION_SWEEP.json')
    assert sweep['historical_performance_contract']['threshold_widening_performed'] is False
    assert sweep['historical_performance_contract']['e_ui_source_mutation_allowed'] is False
    pkg=j('ui/web/package.json')['devpilot']
    assert pkg['currentUiSourceBaselineBytes']==939755
    assert pkg['currentUiSingleSourceBaselineBytes']==94240
    assert pkg['currentUiSourceBudgetPolicy']=='absolute-budget-or-successor-baseline-no-regression'
    smoke=(ROOT/'ui/web/scripts/uoc011-performance-smoke.mjs').read_text(encoding='utf-8')
    assert 'v2-successor-aware' in smoke and 'threshold_widening:false' in smoke

