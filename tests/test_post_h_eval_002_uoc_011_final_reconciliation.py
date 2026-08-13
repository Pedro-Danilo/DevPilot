from collections import Counter
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def j(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
HIST='4ce3c2f851bc572a7b014b5e7aed423f15e3e30c'; REPO339='repo_DevPilot_Local_339_POST_H_EVAL_002_UOC_011.zip'; REPO340='repo_DevPilot_Local_340_POST_H_EVAL_002_UI_OPERATIONAL_CONSOLE_FINAL_CLOSURE.zip'
def test_uoc011_historical_closure_is_recorded_and_not_overclaimed():
 m=j('docs/post_h_eval_002_uoc_011_manifest.json'); assert m['status']=='closed/PASS' and m['closure_commit']==HIST and m['historical_closure_commit']==HIST; assert m['preliminary'] is True and m['final_full_regression_required'] is True; assert m['browser_matrix_runtime_required'] is True and m['browser_matrix_contract_only_sufficient'] is False
def test_capability_parity_summary_is_derived_from_193_entries():
 r=j('.devpilot/interfaces/ui_capability_registry.json'); actual=Counter(str(x['parity_status']) for x in r['capabilities']); assert len(r['capabilities'])==193; assert r['summary']['parity_status_counts']==dict(sorted(actual.items())); assert r['summary']['current_ui_native_or_read_only_total']==actual['UI-NATIVE']+actual['UI-READ-ONLY']; assert r['summary']['uoc_011_authorized'] is True
def test_browser_matrix_requires_real_browser_runtime_for_all_108_cases():
 m=j('.devpilot/interfaces/uoc011_browser_state_matrix.json'); assert len(m['routes'])==9 and len(m['required_states'])==12 and m['summary']['cases_total']==108; assert m['summary']['runtime_execution_required'] is True and m['summary']['runtime_cases_required']==108 and m['summary']['contract_only_is_sufficient'] is False
 for route in m['routes']:
  assert set(route['states'])==set(m['required_states'])
  for item in route['states'].values(): assert item['runtime_required'] is True and item['evidence']=='browser-runtime-controlled-fixture'
def test_all_operational_pages_expose_controlled_runtime_fixture_hook():
 pages={'ui.dashboard':'Dashboard.ts','ui.workspace-documents':'WorkspaceDocumentsView.ts','ui.reports':'ReportsView.ts','ui.traces':'TracesView.ts','ui.approvals':'ApprovalCenterView.ts','ui.jobs':'JobsView.ts','ui.quality':'QualityOperationsView.ts','ui.ai':'AiOperationsView.ts','ui.settings':'SettingsView.ts'}
 for route,file in pages.items():
  src=(ROOT/'ui/web/src/pages'/file).read_text(encoding='utf-8'); assert 'renderUoc011BrowserStateFixture' in src and route in src
 helper=(ROOT/'ui/web/src/testing/Uoc011BrowserStateFixture.ts').read_text(encoding='utf-8'); assert 'Presentation-only local browser fixture' in helper and 'renderUiStateNotice' in helper; assert 'import.meta.env.DEV' in helper and 'VITE_UOC011_BROWSER_MATRIX' in helper
def test_final_reconciliation_lifecycle_is_candidate_or_closed_without_regressing_pilot():
 s=j('.devpilot/project_state.json'); assert s['current_micro_sprint']=='POST-H-EVAL-002-02-B' and s['next_micro_sprint']=='POST-H-EVAL-002-02-C'; status=s['ui_operational_console_final_reconciliation_status']; assert status in {'implemented-initial/pending-authoritative-windows-final-closure','closed/PASS'}
 if status.startswith('implemented-initial'): assert s['current_repo']==REPO339 and s['ui_operational_console_final_reconciliation_source_commit'] is None
 else: assert s['current_repo']==REPO340 and s['ui_operational_console_program_status']=='CLOSED/PASS' and s['ui_operational_console_final_reconciliation_source_commit']; assert s['ui_operational_console_final_browser_runtime_matrix_status']=='PASS/108-of-108'; assert s['ui_operational_console_final_full_regression_status']=='PASS'; assert s['ui_operational_console_program_administrative_closure'] is True
def test_no_stale_uoc011_pending_windows_closure_after_program_finalization():
 s=j('.devpilot/project_state.json')
 if s['ui_operational_console_final_reconciliation_status']!='closed/PASS': return
 for rel in ['README.md','docs/backlogs/POST-H-EVAL-002_ui_operational_console_evolution.md']:
  text=(ROOT/rel).read_text(encoding='utf-8').lower(); assert 'uoc-011 implementation candidate: operational hardening materialized from repo338; authoritative closure pending windows evidence' not in text
 m=j('docs/post_h_eval_002_uoc_011_manifest.json'); assert m['program_administrative_closure'] is True and m['final_reconciliation_status']=='closed/PASS'; assert m['final_browser_runtime_matrix_status']=='PASS' and m['final_browser_runtime_matrix_cases_passed']==108; assert m['final_full_regression_status']=='PASS' and m['full_regression_claimed_pass'] is True
