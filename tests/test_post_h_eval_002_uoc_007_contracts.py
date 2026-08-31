from __future__ import annotations

import inspect
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def j(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding='utf-8'))


def t(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_uoc007_manifest_baseline_state_backlog_and_next_gate_are_synchronized() -> None:
    manifest = j('docs/post_h_eval_002_uoc_007_manifest.json')
    state = j('.devpilot/project_state.json')
    backlog = t('docs/backlogs/POST-H-EVAL-002_ui_operational_console_evolution.md')
    assert manifest['base_commit'] == 'de811e2a0e368ca7f571067a074d14c233fda3d6'
    assert manifest['authoritative_input_repo'] == 'repo_DevPilot_Local_334_POST_H_EVAL_002_UOC_006.zip'
    assert manifest['authoritative_input_repo_sha256'] == 'b5b4ae70682a7da57de585b58e4b764f96a2d148b150f9d0c5deae2ac63b0b3a'
    assert state['uoc_007_status'] == manifest['status']
    assert state['uoc_007_closed'] is manifest['closed']
    assert state['uoc_008_authorized'] is manifest['next']['uoc_008_authorized']
    if manifest['closed']:
        assert manifest['status'] == 'closed/PASS'
        assert manifest['decision'] == 'PASS'
        assert manifest['preliminary'] is False
        assert manifest['next']['uoc_008_authorized'] is True
        assert manifest['authoritative_output_repo'] == 'repo_DevPilot_Local_335_POST_H_EVAL_002_UOC_007.zip'
        current_number = int(state['current_repo'].split('repo_DevPilot_Local_', 1)[1].split('_', 1)[0])
        assert current_number >= 335
        assert 'UOC-007' in backlog
    else:
        assert manifest['status'] == 'implemented-initial/pending-authoritative-windows-closure'
        assert manifest['decision'] == 'PENDING'
        assert manifest['preliminary'] is True
        assert manifest['next']['uoc_008_authorized'] is False
        assert state['current_repo'] == 'repo_DevPilot_Local_334_POST_H_EVAL_002_UOC_006.zip'
        assert 'current_sprint: "UOC-007"' in backlog
        assert 'uoc_008_authorized: false' in backlog


def test_uoc006_authoritative_closure_metadata_is_reconciled_before_uoc007() -> None:
    prior = j('docs/post_h_eval_002_uoc_006_manifest.json')
    state = j('.devpilot/project_state.json')
    registry = j('.devpilot/interfaces/ui_capability_registry.json')
    assert prior['status'] == 'closed/PASS'
    assert prior['closed'] is True
    assert prior['preliminary'] is False
    assert prior['verification']['targeted_python']['windows_authoritative'].startswith('PASS')
    assert prior['verification']['vite_build'].startswith('PASS')
    assert prior['verification']['windows_git_staging_portability'].startswith('PASS')
    assert state['uoc_006_preliminary'] is False
    assert registry['summary']['uoc_006_preliminary'] is False


def test_uoc007_registry_flags_and_no_go_gates_are_explicit() -> None:
    registry = j('.devpilot/interfaces/governed_job_capability_registry.json')
    flags = j('.devpilot/interfaces/ui_operational_console_flags.json')
    ui = j('.devpilot/interfaces/ui_capability_registry.json')
    manifest = j('docs/post_h_eval_002_uoc_007_manifest.json')
    historical_total = manifest['registry']['governed_capabilities_total']
    assert historical_total == 193
    assert registry['summary']['capabilities_total'] >= historical_total
    assert registry['summary']['source_ui_capabilities_total'] == registry['summary']['capabilities_total']
    assert registry['summary']['coverage_exact'] is True
    assert manifest['registry']['execution_enabled_total'] == 0
    assert manifest['registry']['adapter_bound_total'] == 0
    # Later UOC sprints may enable a typed subset; UOC-007's historical no-execution fact remains in its manifest.
    assert registry['safety']['arbitrary_shell_allowed'] is False
    job_flag = next(item for item in flags['feature_flags'] if item['flag_id'] == 'uoc.jobs.framework')
    assert job_flag['enabled'] is True and job_flag['enabled_by'] == 'UOC-007'
    assert flags['safety']['governed_job_runtime_execution_from_ui_enabled'] is False
    assert ui['summary']['uoc_007_new_ui_routes_total'] == 0
    for source in (registry['safety'], flags['safety'], ui['safety']):
        assert source['remote_execution_enabled'] is False
        assert source['connector_write_enabled'] is False
        assert source['plugin_execution_enabled'] is False
        assert source['external_api_required'] is False
    assert registry['safety']['arbitrary_shell_allowed'] is False


def test_uoc007_job_framework_exposes_typed_lifecycle_not_arbitrary_shell() -> None:
    import devpilot_core.application.governed_jobs as jobs

    source = inspect.getsource(jobs)
    assert 'subprocess' not in source
    assert 'shell=True' not in source
    assert 'os.system' not in source
    assert 'eval(' not in source
    assert jobs.ALLOWED_STATUSES == {
        'planned', 'pending-approval', 'approved', 'queued', 'running', 'pass',
        'pass-with-gaps', 'block', 'error', 'cancel-requested', 'cancelled',
        'rollback-running', 'rolled-back', 'expired',
    }


def test_uoc007_schemas_docs_and_test_contract_are_registered() -> None:
    catalog = j('docs/schemas/schema_catalog.json')
    ids = {item['schema_id'] for item in catalog['schemas']}
    expected = {
        'SCHEMA-DEVPL-UI-GOVERNED-JOB-V2',
        'SCHEMA-DEVPL-GOVERNED-JOB-REQUEST-V1',
        'SCHEMA-DEVPL-GOVERNED-JOB-RESULT-V1',
        'SCHEMA-DEVPL-GOVERNED-JOB-CAPABILITY-REGISTRY-V1',
    }
    assert expected <= ids
    docs = {item['doc_id'] for item in j('.devpilot/docs_governance/source_registry.json')['documents']}
    assert {
        'DEVPL-UOC-007-GOVERNED-JOB-FRAMEWORK',
        'DEVPL-UOC-007-CAPABILITY-JOB-FRAMEWORK-REPORT',
        'UOC-007-MANIFEST',
        'UOC-007-GOVERNED-JOB-CAPABILITY-REGISTRY-V1',
    } <= docs
    for rel in ['.devpilot/testing/test_contract_registry.json', '.devpilot/testing/test_contract_registry_v2.json']:
        assert any(item['contract_id'] == 'post-h-eval-002-uoc-007-governed-job-framework' for item in j(rel)['contracts'])


def test_uoc007_does_not_claim_a_jobs_ui_route_in_its_immutable_manifest() -> None:
    manifest = j('docs/post_h_eval_002_uoc_007_manifest.json')
    assert manifest['scope']['new_ui_route'] is False
    assert manifest['verification']['browser_acceptance_required'] is False
    assert manifest['verification']['reason_browser_not_required'].startswith('No visible UI route')
