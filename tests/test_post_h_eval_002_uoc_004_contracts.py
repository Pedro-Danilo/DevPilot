from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
BASE='40ba9e77276d97e69952a8e54c68b8943fd3e51d'

def j(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def t(rel): return (ROOT/rel).read_text(encoding='utf-8')

def test_uoc004_manifest_tracks_open_and_closed_plan_only_lifecycle():
    m=j('docs/post_h_eval_002_uoc_004_manifest.json')
    assert m['base_commit']==BASE
    assert m['scope']['source_write_enabled'] is False and m['scope']['apply_enabled'] is False
    assert m['safety']['no_shell'] is True
    if m['closed']:
        assert m['status']=='closed/PASS'
        assert m['pass_block']['uoc_005_authorized'] is True
        assert m['authoritative_output_repo']=='repo_DevPilot_Local_332_POST_H_EVAL_002_UOC_004.zip'
    else:
        assert m['status']=='implemented-initial'
        assert m['pass_block']['uoc_005_authorized'] is False
        assert m['authoritative_output_repo'] is None
    assert m['capabilities']['immutable_edit_plan'] and m['capabilities']['document_sha_before_binding'] and m['capabilities']['full_unified_diff']
    assert m['capabilities']['explicit_patch_export_nonexecution_feedback'] is True

def test_uoc004_api_and_ui_registries_are_synchronized():
    api=j('.devpilot/interfaces/api_route_contract_registry.json'); ui=j('.devpilot/interfaces/ui_route_contract_registry.json'); flags=j('.devpilot/interfaces/ui_operational_console_flags.json')
    ids={x['route_id'] for x in api['routes']}
    expected={'api.workspace.edit-plans.plan','api.workspace.edit-plans.status','api.workspace.edit-plans.recheck'}; assert expected <= ids
    route=next(x for x in ui['routes'] if x['route_id']=='ui.workspace-documents'); assert expected <= set(route['allowed_api_routes']); assert 'ui/web/src/components/DocumentEditPlanner.ts' in route['source_files']
    flag=next(x for x in flags['feature_flags'] if x['flag_id']=='uoc.documents.edit_plan'); assert flag['enabled'] is True and flag['enabled_by']=='UOC-004'; assert flags['safety']['document_write_enabled'] is False

def test_uoc004_schema_and_test_contracts_are_registered():
    catalog=j('docs/schemas/schema_catalog.json'); assert any(x['schema_id']=='SCHEMA-DEVPL-WORKSPACE-EDIT-PLAN-V1' for x in catalog['schemas'])
    for rel in ['.devpilot/testing/test_contract_registry.json','.devpilot/testing/test_contract_registry_v2.json']:
        d=j(rel); assert any(x['contract_id']=='post-h-eval-002-uoc-004-governed-edit-planning' for x in d['contracts'])

def test_uoc003_residual_documentary_drift_is_reconciled():
    closure=t('docs/audits/uoc_003_closure_report.md'); backlog=t('docs/backlogs/POST-H-EVAL-002_ui_operational_console_evolution.md'); m=j('docs/post_h_eval_002_uoc_003_manifest.json')
    assert 'remains open' not in closure and 'UOC-004 remains unauthorized' not in closure
    assert 'uoc_003_browser_ux_corrective_status: "closed/PASS-v1.0.5"' in backlog
    assert m['pass_block']['closure_status']=='PASS' and m['pass_block']['uoc_004_authorized'] is True

def test_uoc004_openapi_has_typed_plan_status_recheck_paths():
    paths=j('docs/07_interfaces/openapi_v1.json')['paths']
    assert 'post' in paths['/api/v1/workspace/edit-plans/plan']
    assert 'get' in paths['/api/v1/workspace/edit-plans/{plan_id}']
    assert 'post' in paths['/api/v1/workspace/edit-plans/{plan_id}/recheck']

def test_uoc004_no_write_controls_are_visible_in_source():
    svc=t('src/devpilot_core/application/workspace_edit_plan_service.py'); ui=t('ui/web/src/components/DocumentEditPlanner.ts')
    assert 'never writes source documents' in svc and 'source_write_enabled' in svc and 'apply_available_in_uoc_004' in svc
    assert 'sessionStorage.setItem' in ui and 'Exportar .patch (no ejecutado)' in ui and 'NO-GO UOC-004' in ui
    assert 'localStorage.setItem' not in ui
