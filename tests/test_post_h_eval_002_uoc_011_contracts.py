from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def j(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))

def test_uoc011_candidate_lifecycle_preserves_pilot_and_repo338() -> None:
    s=j('.devpilot/project_state.json'); assert s['uoc_011_authorized'] is True; assert s['current_micro_sprint']=='POST-H-EVAL-002-02-B'; assert s['next_micro_sprint']=='POST-H-EVAL-002-02-C'; assert s['uoc_011_implementation_maturity']=='implemented-initial'; assert s['uoc_011_preliminary'] is True
    assert s['uoc_011_status'] in {'implemented-initial/pending-windows-closure','closed/PASS'}
    if s['uoc_011_status'].startswith('implemented-initial'):
        assert s['current_repo']=='repo_DevPilot_Local_338_POST_H_EVAL_002_UOC_010.zip'; assert s['uoc_011_local_release_declared'] is False
    else:
        assert s['uoc_011_authoritative_baseline']=='repo_DevPilot_Local_339_POST_H_EVAL_002_UOC_011.zip'; assert s['uoc_011_local_release_declared'] is True
        assert s['current_repo'].startswith('repo_DevPilot_Local_')

def test_uoc011_browser_matrix_is_9_by_12_and_routes_match() -> None:
    m=j('.devpilot/interfaces/uoc011_browser_state_matrix.json'); frozen=j('.devpilot/interfaces/ui_route_contract_registry_uoc011_at_close.json'); current=j('.devpilot/interfaces/ui_route_contract_registry.json'); expected=set(m['required_states']); assert len(m['routes'])==9 and len(expected)==12 and m['summary']['cases_total']==108
    assert {x['route_id'] for x in m['routes']}=={x['route_id'] for x in frozen['routes']}
    for route in frozen['routes']: assert all(route['state_contract'].get(state) is True for state in expected)
    assert {x['route_id'] for x in frozen['routes']} < {x['route_id'] for x in current['routes']}
    assert any(x['route_id']=='ui.project-status' for x in current['routes'])

def test_uoc011_profile_no_go_and_release_assets() -> None:
    p=j('.devpilot/interfaces/uoc011_operational_hardening_profile.json'); assert p['security']['max_request_body_bytes']==1048576; assert p['security']['token_session_ttl_seconds']==28800; assert p['browser']['route_state_cases_total']==108
    assert all(p['safety'][k] is False for k in ('arbitrary_shell_allowed','remote_execution_enabled','connector_write_enabled','plugin_execution_enabled','external_api_enabled'))
    for path in ['docs/03_security/uoc_011_operational_threat_model.md','docs/05_operations/uoc_011_release_operator_runbook.md','docs/release/uoc_011_release_notes.md','docs/audits/uoc_011_hardening_accessibility_performance_release_report.md','docs/post_h_eval_002_uoc_011_manifest.json']:
        assert (ROOT/path).is_file()

def test_uoc011_manifest_freezes_repo338_and_does_not_overclaim() -> None:
    m=j('docs/post_h_eval_002_uoc_011_manifest.json'); assert m['input_repo']=='repo_DevPilot_Local_338_POST_H_EVAL_002_UOC_010.zip'; assert m['input_repo_sha256']=='ee6756961d25a067e5be71e0c2b57fd16237ccf413f18c3684b89765d644b4fa'; assert m['preliminary'] is True; assert m['closure_commit']=='4ce3c2f851bc572a7b014b5e7aed423f15e3e30c'; assert m['browser_matrix_runtime_required'] is True; assert m['browser_matrix_contract_only_sufficient'] is False
    if str(m['status']).startswith('implemented-initial'):
        assert m['release_claim']=='pending-authoritative-windows-closure'
    else:
        assert m['status']=='closed/PASS'; assert m['release_claim']=='approved-local-release'
