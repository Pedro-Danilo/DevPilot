from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application.agentic_precode_acceptance import AgenticPrecodeAcceptanceEvaluator
from devpilot_core.application.settings_service import SettingsApplicationService
from devpilot_core.testing import full_regression as frx
from devpilot_core.testing.full_regression_telemetry import FullRegressionTelemetryExporter

ROOT = Path(__file__).resolve().parents[1]


def _result():
    # Keep runtime-ephemeral outputs from prior tests from influencing this one.
    for path in (ROOT / 'outputs/runtime/gsdlc_07_d_agent_execution.json',):
        if path.exists():
            path.unlink()
    return AgenticPrecodeAcceptanceEvaluator(ROOT).evaluate()


def test_07_e_assisted_journey_is_five_of_five_and_manual_route_preserved() -> None:
    result = _result(); assert result.ok, result.to_dict()
    summary = result.data['summary']
    assert summary['assisted_steps_total'] == summary['assisted_steps_expected'] == 5
    assert summary['journey'] == 'Product Vision -> PRE_CODE_READY'
    assert summary['manual_route_preserved'] is True


def test_07_e_human_decision_rates_are_accept_modify_reject() -> None:
    summary = _result().data['summary']
    assert summary['human_decision_rates_percent'] == {'ACCEPT': 60.0, 'MODIFY': 20.0, 'REJECT': 20.0}


def test_07_e_trace_provenance_model_route_tokens_and_cost_are_visible() -> None:
    traces = _result().data['traces']
    assert all(t['sources'] and len(t['sources'][0]['sha256']) == 64 for t in traces)
    assert all(t['agent_role'] and t['runtime_agent'] and t['provider'] and t['model'] and t['access_route'] for t in traces)
    assert all(t['tokens_total'] > 0 and t['cost_known'] is True and t['estimated_cost_usd'] == 0.0 for t in traces)


def test_07_e_agent_never_auto_approves_or_writes_source() -> None:
    traces = _result().data['traces']
    assert all(t['auto_approval'] is False for t in traces)
    assert all(t['source_write'] is False for t in traces)
    assert all(t['tool_authority_granted'] is False for t in traces)


def test_07_e_forbidden_filesystem_delete_is_contained() -> None:
    result = _result(); assert result.ok
    assert result.data['summary']['forbidden_tool_containment'] is True
    decision = result.data['forbidden_tool_receipt']['data']['tool_execution_decision']
    assert decision['executable'] is False and decision['tool_executed'] is False
    assert decision['model_route_granted_permission'] is False


def test_07_e_cost_hard_stop_is_demonstrated() -> None:
    result = _result(); assert result.ok
    assert result.data['summary']['hard_stop_demonstrated'] is True
    assert result.data['hard_stop_receipt']['ok'] is False


def test_07_e_handoff_requires_human_checkpoint_and_no_scope_inheritance() -> None:
    result = _result(); assert result.ok
    assert result.data['summary']['bounded_handoff'] is True
    transfer = result.data['handoff_receipt']['data']['transfer']
    assert transfer['human_checkpoint'] is True and transfer['scope_inherited'] is False


def test_07_e_mock_local_required_external_fake_optional_and_no_network() -> None:
    summary = _result().data['summary']
    assert summary['mock_pass'] is True and summary['fake_local_pass'] is True
    assert summary['optional_external_fake'] == 'PASS/HERMETIC-NO-NETWORK'
    assert summary['external_api_used'] is False and summary['network_used'] is False


def test_07_e_v2_2_handoff_prepared_and_v2_3_remains_disabled() -> None:
    summary = _result().data['summary']
    assert summary['v2_2_next'] is True
    assert summary['v2_3_prepared_not_enabled'] is True
    assert summary['parallel_workers'] == 0


def test_07_e_settings_projection_is_read_only_sealed_evidence() -> None:
    result = SettingsApplicationService(ROOT).agent_eval_trace_settings()
    assert result.ok, result.to_dict()
    summary = result.data['summary']
    assert summary['read_only'] is True
    assert summary['external_api_used'] is False and summary['network_used'] is False
    assert summary['model_route_grants_tool_permission'] is False


def test_07_e_full_regression_fingerprint_excludes_sqlite_runtime_sidecars(tmp_path: Path) -> None:
    root = tmp_path / 'repo'; root.mkdir(); (root / 'a.txt').write_text('stable', encoding='utf-8')
    auth = root / '.devpilot/auth'; auth.mkdir(parents=True)
    db = auth / 'auth.db'; db.write_text('runtime', encoding='utf-8')
    before = frx._fingerprint(frx._source_descriptor(root))
    for suffix in ('-wal', '-shm', '-journal', '.wal', '.shm', '.journal'):
        Path(str(db) + suffix).write_text('ephemeral-change', encoding='utf-8')
        assert frx._fingerprint(frx._source_descriptor(root)) == before


def test_07_e_telemetry_exporter_preserves_node_duration_and_parallel_default(tmp_path: Path) -> None:
    root = tmp_path / 'repo'; session = root / 'outputs/testing/full_regression/S1'; receipts = session / 'receipts'; runtime = session / 'runtime'
    receipts.mkdir(parents=True); runtime.mkdir(parents=True)
    outcome = runtime / 'shard-001-attempt-001.outcomes.jsonl'
    outcome.write_text(json.dumps({'nodeid':'tests/test_x.py::test_a','when':'call','outcome':'PASS','duration_seconds':0.125})+'\n', encoding='utf-8')
    receipt = {
        'outcomes': {'tests/test_x.py::test_a':'PASS'},
        'duration_seconds': 0.2,
        'outcome_log_path': str(outcome.relative_to(root)).replace('\\','/'),
    }
    (receipts / 'shard-001-attempt-001.json').write_text(json.dumps(receipt), encoding='utf-8')
    result = FullRegressionTelemetryExporter(root).export('S1')
    assert result.ok, result.to_dict()
    telemetry = result.data['telemetry']
    assert telemetry['samples'][0]['duration_seconds'] == 0.125
    assert telemetry['samples'][0]['v2_3_isolation']['parallel_safe'] is False
    assert telemetry['v2_3']['workers'] == 0

def test_07_e_agent_evals_route_is_server_rbac_registered_and_human_session_only() -> None:
    catalog = json.loads((ROOT / '.devpilot/identity/server_rbac_policy_catalog.json').read_text(encoding='utf-8'))
    matches = [item for item in catalog['route_policies'] if item['method'] == 'GET' and item['path'] == '/api/v1/settings/agent-evals']
    assert len(matches) == 1
    policy = matches[0]
    assert policy['operation'] == 'settings.agent_evals'
    assert policy['human_session_required'] is True
    assert policy['legacy_token_allowed'] is False
    assert policy['deny_by_default'] is True
    assert 'owner' in policy['allowed_roles']


def test_07_e_protected_api_policy_registry_has_server_rbac_coverage() -> None:
    from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES
    catalog = json.loads((ROOT / '.devpilot/identity/server_rbac_policy_catalog.json').read_text(encoding='utf-8'))
    registered = {(item['method'].upper(), item['path']) for item in catalog['route_policies']}
    missing = sorted(set(API_ROUTE_POLICIES) - registered)
    assert missing == []

