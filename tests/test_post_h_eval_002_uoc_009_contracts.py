from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def j(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
def test_uoc009_project_state_preserves_pilot_and_candidate_lifecycle() -> None:
    s=j('.devpilot/project_state.json'); assert s['uoc_009_authorized'] is True; assert s['current_micro_sprint']=='POST-H-EVAL-002-02-B'; assert s['next_micro_sprint']=='POST-H-EVAL-002-02-C'
    assert s['uoc_009_status'] in {'implemented-initial/pending-windows-browser-closure','closed/PASS'}
    if s['uoc_009_status'].startswith('implemented-initial'):
        assert s['current_repo']=='repo_DevPilot_Local_336_POST_H_EVAL_002_UOC_008.zip' and s['uoc_010_authorized'] is False
    else:
        assert s['uoc_009_authoritative_baseline']=='repo_DevPilot_Local_337_POST_H_EVAL_002_UOC_009.zip'; assert s['uoc_010_authorized'] is True

def test_uoc009_routes_and_typed_execution_subset_without_no_go_relaxation() -> None:
    ui=j('.devpilot/interfaces/ui_route_contract_registry.json'); api=j('.devpilot/interfaces/api_route_contract_registry.json'); jobs=j('.devpilot/interfaces/governed_job_capability_registry.json')
    route=next(x for x in ui['routes'] if x['route_id']=='ui.quality'); assert route['path']=='/quality'
    assert all(route[k] is False for k in ('remote_execution_allowed','connector_write_allowed','plugin_execution_allowed','external_api_allowed'))
    expected={'api.quality.operations','api.quality.baseline','api.quality.test-impact-plan','api.quality.jobs.plan','api.quality.jobs.execute','api.quality.evidence-package'}; assert expected <= set(route['allowed_api_routes']); assert expected <= {x['route_id'] for x in api['routes']}
    uoc009=[x for x in jobs['capabilities'] if x['runtime'].get('adapter_id')=='uoc009.quality.typed-worker']; assert len(uoc009)==10; assert all(x['runtime']['execution_enabled'] for x in uoc009); assert jobs['safety']['arbitrary_shell_allowed'] is False

def test_uoc009_manifest_freezes_repo336_and_does_not_preauthorize_uoc010() -> None:
    m=j('docs/post_h_eval_002_uoc_009_manifest.json'); assert m['baseline_repo']=='repo_DevPilot_Local_336_POST_H_EVAL_002_UOC_008.zip'; assert m['baseline_sha256']=='2a1e0e2501753431cc1ac8a685b4b597ac34ebf0e48dbec8d80715bb92c1a734'; assert m['full_regression_requires_approval'] is True and m['full_regression_requires_explicit_confirmation'] is True
    if m['status'].startswith('implemented-initial'): assert m['uoc_010_authorized'] is False and m['output_repo'] is None
    assert m['test_impact']['recommended_tests']==224 and m['test_impact']['unmatched_paths']==0

def test_uoc009_schemas_docs_and_registry_profiles_are_present() -> None:
    for p in ['docs/07_interfaces/quality_test_release_operations.md','docs/audits/uoc_009_quality_tests_release_operations_report.md','docs/post_h_eval_002_uoc_009_manifest.json','.devpilot/quality/ui_quality_operation_profiles.json','docs/schemas/quality_operation_profiles.schema.json','docs/schemas/quality_operation_parameters.schema.json','docs/schemas/quality_job_plan.schema.json','docs/schemas/quality_job_result.schema.json']: assert (ROOT/p).is_file()
    profiles=j('.devpilot/quality/ui_quality_operation_profiles.json'); assert profiles['safety']['arbitrary_shell'] is False; assert profiles['safety']['free_pytest_args'] is False; assert len(profiles['operations'])==11

def test_uoc008_stale_risk_was_reconciled_without_changing_closed_facts() -> None:
    m=j('docs/post_h_eval_002_uoc_008_manifest.json'); assert m['status']=='closed/PASS'; assert m['browser_acceptance']=='PASS'; assert m['output_repo']=='repo_DevPilot_Local_336_POST_H_EVAL_002_UOC_008.zip'; assert all('remain pending' not in x for x in m['risks'])


def test_uoc009_test_contract_registries_keep_runtime_artifacts_out_of_test_files() -> None:
    for rel in ('.devpilot/testing/test_contract_registry.json','.devpilot/testing/test_contract_registry_v2.json'):
        registry=j(rel)
        contract=next(x for x in registry['contracts'] if x['contract_id']=='post-h-eval-002-uoc-002-regression-recovery')
        assert '.devpilot/rag/docs_index.json' not in contract['test_files']
        assert '.devpilot/rag/docs_index.json' in contract['watched_paths']
        assert '.devpilot/rag/docs_index.json' in contract['validates']
        assert all(path.endswith('.py') for path in contract['test_files'])

