from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.testing.isolation_evidence import (
    FunctionIsolationAuditor,
    IsolationContractCatalog,
    RuntimeSafePromotion,
)
from devpilot_core.testing.isolation_registry import IsolationState, TestIsolationRegistry

ROOT = Path(__file__).resolve().parents[1]


def test_br_contract_catalog_never_authorizes_by_contract_alone() -> None:
    payload = IsolationContractCatalog.payload()
    assert payload['contracts']
    assert all(item['parallel_safe_by_contract_alone'] is False for item in payload['contracts'])
    assert payload['workers_general_suite'] == 0
    assert payload['full_runs'] == 0


def test_br_function_auditor_accepts_tmp_path_fixture() -> None:
    audit = FunctionIsolationAuditor(ROOT).audit(
        'tests/test_agentops_instrumentation.py::test_agent_runtime_persists_correlated_agentops_spans_and_metrics',
        requested_contract='TMP_PATH_PROCESS_ISOLATED_V1',
    )
    assert audit.eligible is True
    assert audit.contract_id == 'TMP_PATH_PROCESS_ISOLATED_V1'


def test_br_function_auditor_rejects_real_localhost_resource() -> None:
    audit = FunctionIsolationAuditor(ROOT).audit(
        'tests/test_ollama_adapter.py::test_ollama_fake_server_generate_classify_embed_pass',
        requested_contract='LOCAL_CLONE_PER_WORKER_V1',
    )
    assert audit.eligible is False
    assert 'fixed-localhost-port-or-server-lifecycle' in audit.blockers


def test_br_successor_registry_adds_new_nodes_as_unclassified(tmp_path: Path) -> None:
    root = tmp_path
    (root / '.devpilot/testing').mkdir(parents=True)
    (root / 'tests').mkdir()
    (root / 'tests/test_x.py').write_text('def test_x():\n    assert True\n\n', encoding='utf-8')
    (root / '.devpilot/testing/node_duration_registry.json').write_text(json.dumps({'environments': {}}), encoding='utf-8')
    base = {
        'schema_id': 'devpilot.testing.test_isolation_registry.v1', 'version': '1.0.0', 'status': 'implemented-initial',
        'updated': 'x', 'source_commit': 'abcdef1', 'collection_sha256': '0'*64, 'registry_sha256': '1'*64,
        'policy': {'default_state':'UNCLASSIFIED','default_parallel_safe':False,'explicit_review_required':True,'static_suggestions_authorize_parallel':False,'duration_or_name_authorize_parallel':False,'workers':0,'full_runs':0},
        'resource_classes': ['r']*11, 'entries': [],
    }
    promotion = RuntimeSafePromotion(root)
    successor = promotion.successor_registry(base, ['tests/test_x.py::test_x'], source_commit='abcdef2')
    assert len(successor['entries']) == 1
    assert successor['entries'][0]['state'] == IsolationState.UNCLASSIFIED.value
    assert successor['entries'][0]['parallel_safe'] is False


def test_br_evidence_promotion_requires_contract_probe_pass() -> None:
    base = json.loads((ROOT / '.devpilot/testing/test_isolation_registry.json').read_text(encoding='utf-8'))
    nodeid = next(x['nodeid'] for x in base['entries'] if x['state'] == 'UNCLASSIFIED' and x['parallel_safe'] is False)
    candidate = {'candidates': [{'candidate_id': 'BR-CAND-0001', 'nodeid': nodeid, 'contract_id': 'TMP_PATH_PROCESS_ISOLATED_V1'}]}
    promotion = RuntimeSafePromotion(ROOT)
    no_probe, report = promotion.apply_evidence(base, candidate_manifest=candidate, contract_probe_report={'contracts': []}, reviewer='test-reviewer', reviewed_at='2026-09-02T00:00:00Z')
    entry = next(x for x in no_probe['entries'] if x['nodeid'] == nodeid)
    assert entry['parallel_safe'] is False
    assert report['decisions'][0]['decision'] in {'UNCLASSIFIED', 'SERIAL_REQUIRED'}


def test_br_evidence_promotion_sets_explicit_review_only_after_pass() -> None:
    base = json.loads((ROOT / '.devpilot/testing/test_isolation_registry.json').read_text(encoding='utf-8'))
    nodeid = next(x['nodeid'] for x in base['entries'] if x['state'] == 'UNCLASSIFIED' and x['parallel_safe'] is False)
    candidate = {'candidates': [{'candidate_id': 'BR-CAND-0001', 'nodeid': nodeid, 'contract_id': 'TMP_PATH_PROCESS_ISOLATED_V1'}]}
    probes = {'contracts': [{'contract_id': 'TMP_PATH_PROCESS_ISOLATED_V1', 'status': 'PASS', 'evidence_id': 'probe-1'}]}
    promotion = RuntimeSafePromotion(ROOT)
    promoted, report = promotion.apply_evidence(base, candidate_manifest=candidate, contract_probe_report=probes, reviewer='test-reviewer', reviewed_at='2026-09-02T00:00:00Z')
    entry = next(x for x in promoted['entries'] if x['nodeid'] == nodeid)
    assert entry['state'] == IsolationState.PROVEN_PARALLEL_SAFE.value
    assert entry['parallel_safe'] is True
    assert entry['review']['evidence_ids'] == ['br-structural-audit:BR-CAND-0001', 'probe-1']
    assert report['coverage']['proven_parallel_safe_total'] >= 1


def test_br_duration_or_name_never_authorizes_without_review() -> None:
    entry = TestIsolationRegistry.default_entry('tests/test_fast_safe_name.py::test_parallel_safe_fast', runtime_estimate={'known': True, 'seconds': 1000.0, 'confidence': 'high', 'source_environment': 'x', 'last_seen': 'x'})
    assert entry['parallel_safe'] is False
    assert entry['explicit_review_required'] is True


def test_br_candidate_manifest_is_runtime_representative_and_non_authoritative() -> None:
    manifest = json.loads((ROOT / '.devpilot/testing/frx_v2_3_br_candidate_manifest.json').read_text(encoding='utf-8'))
    assert manifest['candidates_total'] == len(manifest['candidates'])
    assert manifest['candidate_runtime_percent'] >= 70.0
    assert manifest['selection_policy']['candidate_is_not_parallel_authorization'] is True
    registry = json.loads((ROOT / '.devpilot/testing/test_isolation_registry.json').read_text(encoding='utf-8'))
    by_nodeid = {x['nodeid']: x for x in registry['entries']}
    assert all(by_nodeid[item['nodeid']]['state'] == 'PROVEN_PARALLEL_SAFE' and by_nodeid[item['nodeid']]['parallel_safe'] is True for item in manifest['candidates'] if item['nodeid'] in by_nodeid)


def test_br_all_checked_in_candidates_pass_current_structural_audit() -> None:
    manifest = json.loads((ROOT / '.devpilot/testing/frx_v2_3_br_candidate_manifest.json').read_text(encoding='utf-8'))
    auditor = FunctionIsolationAuditor(ROOT)
    audits = [auditor.audit(item['nodeid'], requested_contract=item['contract_id']) for item in manifest['candidates']]
    assert audits
    assert all(item.eligible for item in audits), [item.to_dict() for item in audits if not item.eligible]


def test_br_project_state_keeps_repo394_authority_until_windows_closure() -> None:
    state = json.loads((ROOT / '.devpilot/project_state.json').read_text(encoding='utf-8'))
    assert state['frx_v2_3_br_parent_repo'] == 'repo_DevPilot_Local_394_FRX_V2_3_C_CONFLICT_GRAPH_SHADOW_SCHEDULER_WINDOWS_VALIDATED_CANDIDATE.zip'
    assert state['frx_v2_3_br_status'] == 'CLOSED/PASS/WINDOWS-VALIDATED'
    assert state['current_repo'].startswith('repo_DevPilot_Local_396_')
    assert state['frx_v2_3_br_authorized'] is True
    assert state['frx_v2_3_d_authorized'] is True
    assert state['frx_v2_3_d_status'] == 'CLOSED/PASS/WINDOWS-VALIDATED'
    assert state['frx_v2_3_e_authorized'] is True
    assert state['frx_v2_3_br_full_regression_runs'] == 0
    assert state['frx_v2_3_br_general_suite_parallel_workers'] == 0
