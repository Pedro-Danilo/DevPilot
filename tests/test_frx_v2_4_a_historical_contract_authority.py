from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.docs_governance.validator import DocumentationGovernanceValidator
from devpilot_core.testing.duration_registry import NodeDurationRegistry
from devpilot_core.testing.historical_contract_authority import HistoricalContractAuthorityGate
from devpilot_core.testing.isolation_registry import TestIsolationRegistry
from devpilot_core.testing.safe_parallel_full import SafeParallelFullPlanner

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / '.devpilot/testing/historical_contract_authority_registry.json'
FIXTURE_PATH = ROOT / '.devpilot/testing/fixtures/frx_v2_3_e_policy_pre_execution_fixture.json'
CURRENT_POLICY_PATH = ROOT / '.devpilot/testing/frx_v2_3_e_policy.json'


def _registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))


def test_authority_registry_schema_and_six_scopes_pass():
    result = HistoricalContractAuthorityGate(ROOT).run()
    assert result.ok, result.to_dict()
    summary = result.data['summary']
    assert summary['authority_contracts_total'] == 7
    assert summary['authority_scope_deterministic'] is True
    assert all(summary['authority_scope_counts'][name] >= 1 for name in ('historical-freeze','current-active','successor-needed','deprecated-after-proof','derived','runtime-ephemeral'))


def test_historical_test_to_current_mutable_is_blocked(tmp_path: Path):
    root = tmp_path / 'repo'; root.mkdir()
    (root/'tests').mkdir(); (root/'.devpilot/testing/fixtures').mkdir(parents=True)
    (root/'tests/historical.py').write_text("PATH='.devpilot/testing/current.json'\n",encoding='utf-8')
    (root/'.devpilot/testing/fixtures/snapshot.json').write_text('{}\n',encoding='utf-8')
    record={'contract_id':'x','authority_scope':'historical-freeze','owner':'o','rationale':'r','test_files':['tests/historical.py'],'snapshot_path':'.devpilot/testing/fixtures/snapshot.json','mutable_current_paths':['.devpilot/testing/current.json']}
    assert HistoricalContractAuthorityGate.validate_contract_record(record) == []
    text=(root/'tests/historical.py').read_text()
    assert record['mutable_current_paths'][0] in text and record['snapshot_path'] not in text


def test_historical_contract_missing_snapshot_is_blocked():
    record={'contract_id':'x','authority_scope':'historical-freeze','owner':'o','rationale':'r','test_files':[],'mutable_current_paths':['current.json']}
    assert 'missing-snapshot:x' in HistoricalContractAuthorityGate.validate_contract_record(record)


def test_invalid_isolation_entry_fails_complete_schema_validation():
    registry = TestIsolationRegistry(ROOT)
    payload = registry.load()
    broken = copy.deepcopy(payload)
    broken['entries'][0]['unexpected_frx_v2_4_a_field'] = True
    result = registry.validate_schema(broken)
    assert result.ok is False
    assert any(f.id == 'SCHEMA_VALIDATION_ERROR' for f in result.findings)


def test_ambiguous_pending_current_lifecycle_is_detectable():
    sweep=json.loads((ROOT/'docs/audits/DEVPL_GSDLC_08_E_CONTRACT_RECONCILIATION_SWEEP.json').read_text(encoding='utf-8'))
    assert sweep['final_reconciliation_required_at_detection'] is True
    assert sweep['final_reconciliation_pending_now'] is False
    broken=copy.deepcopy(sweep); broken.pop('final_reconciliation_pending_now')
    assert 'final_reconciliation_required_at_detection' in broken and 'final_reconciliation_pending_now' not in broken


def test_successor_needed_progression_is_explicit_positive():
    record={'contract_id':'x','authority_scope':'successor-needed','owner':'o','rationale':'r','test_files':[],'successor_contract_id':'FRX-v2.4-B'}
    assert HistoricalContractAuthorityGate.validate_contract_record(record) == []
    record.pop('successor_contract_id')
    assert 'missing-successor-contract-id:x' in HistoricalContractAuthorityGate.validate_contract_record(record)


def test_frx_v2_3_e_fixture_is_immutable_semantic_pre_execution_authority():
    fixture=json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))
    current=json.loads(CURRENT_POLICY_PATH.read_text(encoding='utf-8'))
    assert fixture['historical_fixture']['immutable'] is True
    assert fixture['historical_fixture']['kind']=='reconstructed-pre-execution-snapshot'
    assert fixture['full_regression_runs_consumed']==0 and current['full_regression_runs_consumed']==1
    source=(ROOT/'tests/test_frx_v2_3_e_safe_parallel_full.py').read_text(encoding='utf-8').replace('\\','/')
    assert '.devpilot/testing/fixtures/frx_v2_3_e_policy_pre_execution_fixture.json' in source
    assert ".devpilot/testing/frx_v2_3_e_policy.json" not in source


def test_frx_v2_3_e_planner_accepts_historical_fixture_without_mutation():
    before=FIXTURE_PATH.read_bytes()
    collection=json.loads((ROOT/'.devpilot/testing/frx_v2_3_c_collection.json').read_text(encoding='utf-8'))
    nodes=[row['nodeid'] for row in collection['nodes']]
    plan=SafeParallelFullPlanner(ROOT,policy_path=Path('.devpilot/testing/fixtures/frx_v2_3_e_policy_pre_execution_fixture.json')).build(nodes,environment_fingerprint='windows-pytest-devpilot-gsdlc07e-v1')
    assert plan['status']=='PASS' and plan['full_regression_runs_planned']==1
    assert FIXTURE_PATH.read_bytes()==before


def test_isolation_registry_complete_schema_and_semantics_pass():
    registry=TestIsolationRegistry(ROOT)
    schema=registry.validate_schema(); semantics=registry.validate_semantics(registry.load())
    assert schema.ok, schema.to_dict()
    assert semantics['ok'], semantics
    assert semantics['entries_total'] > 0


def test_duration_registry_complete_schema_pass_and_has_no_rejected_telemetry():
    registry=NodeDurationRegistry(ROOT)
    schema=registry.validate_schema(); status=registry.status()
    assert schema.ok, schema.to_dict()
    assert status['rejections_total']==0


def test_documentation_governance_integrates_authority_gate():
    result=DocumentationGovernanceValidator(ROOT).run()
    assert result.ok, result.to_dict()
    summary=result.data['summary']
    assert summary['historical_contract_authority_passed'] is True
    assert summary['historical_current_leakage_total']==0
    assert summary['frx_registry_schema_errors_total']==0


def test_08e_all_46_historical_failures_have_authority_classification():
    audit=json.loads((ROOT/'docs/audits/FRX_V2_4_A_HISTORICAL_FAIL_AUTHORITY_AUDIT.json').read_text(encoding='utf-8'))
    classes=audit['classification']
    assert classes['total']==46
    assert classes['current-active']==21 and classes['successor-needed']==13 and classes['derived']==7 and classes['historical-freeze']==5
    assert classes['unclassified']==0
