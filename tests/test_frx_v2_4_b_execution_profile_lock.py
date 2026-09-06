from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from devpilot_core.application.quality_operations import QualityOperationsApplicationService
from devpilot_core.testing.full_regression_execution_profile import (
    FullRegressionExecutionProfileRegistry,
    FullRegressionPreflight,
    TopologyCompatibilityGuard,
)

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = '.devpilot/testing/frx_v2_3_c_collection.json'
POSITIVE = '.devpilot/testing/fixtures/frx_v2_4_b_v2_3_current_profile_positive.json'
NEGATIVE = '.devpilot/testing/fixtures/frx_v2_4_b_08e_count50_topology_regression.json'


def test_profile_registry_schema_hash_and_unique_current_pass():
    result = FullRegressionExecutionProfileRegistry(ROOT).validate()
    assert result.ok, result.to_dict()
    summary = result.data['summary']
    assert summary['profiles_total'] == 1
    assert summary['current_active_total'] == 1
    assert summary['current_profile_id'] == 'frx-v2.4-current'
    assert summary['profile_hashes_valid'] is True
    assert summary['current_pointer_parity'] is True
    assert summary['consumer_contract_locked'] is True
    assert summary['budget_reserved'] is False


def test_current_profile_reproduces_v2_3_consolidated_policy():
    profile = FullRegressionExecutionProfileRegistry(ROOT).require('current')
    assert profile.planner == 'deterministic-lpt-sequential'
    assert profile.target_shard_seconds == 900.0
    assert profile.max_nodeids == 200
    assert profile.nodeid_transport == 'manifest'
    assert profile.default_workers == 1
    assert profile.parallel_opt_in_ceiling == 2
    assert profile.parallel_opt_in_default is False
    assert profile.unknown_policy == 'serial'
    assert profile.unclassified_isolation_policy == 'serial'
    assert profile.completion_first is True
    assert profile.exact_accounting is True
    assert profile.full_regression_runs_allowed == 1
    assert profile.second_full_allowed is False
    assert profile.resume_same_session is True
    assert profile.composite_recovery_after_functional_fail is True
    assert profile.source_guard_policy == 'git-semantic-v1'


def test_positive_v2_3_current_topology_fixture_passes_before_budget():
    result = TopologyCompatibilityGuard(ROOT).check_fixture(POSITIVE)
    assert result.ok, result.to_dict()
    assert result.data['summary']['compatible'] is True
    assert result.data['summary']['mismatches_total'] == 0
    assert result.data['summary']['budget_reserved'] is False


def test_08e_count50_topology_regression_blocks_before_budget_reservation():
    result = TopologyCompatibilityGuard(ROOT).check_fixture(NEGATIVE)
    assert not result.ok
    summary = result.data['summary']
    assert summary['compatible'] is False
    assert summary['budget_reserved'] is False
    assert summary['full_regression_runs'] == 0
    assert summary['mismatches']['max_nodeids'] == {'expected': 200, 'proposed': 50}
    assert summary['mismatches']['nodeid_transport'] == {'expected': 'manifest', 'proposed': 'command-line'}
    assert 'shard_strategy' in summary['mismatches']


def test_low_level_max_nodeids_override_is_blocked_by_default():
    profile = FullRegressionExecutionProfileRegistry(ROOT).require('current')
    proposed = profile.topology()
    proposed['max_nodeids'] = 50
    result = TopologyCompatibilityGuard(ROOT).check(proposed)
    assert not result.ok
    assert result.data['summary']['mismatches_total'] == 1
    assert result.data['summary']['waiver_used'] is False


def test_low_level_override_requires_explicit_owner_waiver_scope():
    profile = FullRegressionExecutionProfileRegistry(ROOT).require('current')
    proposed = profile.topology()
    proposed['max_nodeids'] = 150
    denied = TopologyCompatibilityGuard(ROOT).check(proposed, waiver={'status': 'owner-approved', 'waiver_id': 'W-1', 'allowed_overrides': []})
    assert not denied.ok
    accepted = TopologyCompatibilityGuard(ROOT).check(proposed, waiver={'status': 'owner-approved', 'waiver_id': 'W-2', 'allowed_overrides': ['max_nodeids']})
    assert accepted.ok
    assert accepted.data['summary']['waiver_used'] is True


def test_preflight_positive_is_machine_readable_and_does_not_reserve_full():
    result = FullRegressionPreflight(ROOT).run(collection=COLLECTION, full_budget_state=0)
    assert result.ok, result.to_dict()
    summary = result.data['summary']
    report = result.data['report']
    assert summary['collection_total'] == 2883
    assert summary['collection_sealed'] is True
    assert summary['projected_shards_total'] > 0
    assert summary['effective_workers'] == 1
    assert summary['budget_reserved'] is False
    assert summary['full_regression_runs'] == 0
    assert report['status'] == 'PASS'
    assert report['registries']['isolation_schema_pass'] is True
    assert report['registries']['isolation_collection_missing_total'] == 0
    assert report['registries']['duration_schema_pass'] is True
    assert report['registries']['duration_rejections_total'] == 0
    assert report['registries']['duration_unknown_cold_start_total'] == 79
    assert report['eta']['projected_full_eta_seconds'] > 0
    assert report['safety']['tests_executed'] is False


def test_preflight_budget_state_one_blocks_second_full_without_reservation():
    result = FullRegressionPreflight(ROOT).run(collection=COLLECTION, full_budget_state=1)
    assert not result.ok
    assert result.data['report']['budget']['full_budget_available'] is False
    assert result.data['report']['budget']['budget_reserved'] is False
    assert any(f.id == 'FRX24B_BUDGET_ALREADY_CONSUMED_BLOCK' for f in result.findings)


def test_preflight_missing_collection_seal_blocks():
    payload = json.loads((ROOT / COLLECTION).read_text(encoding='utf-8'))
    payload.pop('collection_sha256', None)
    result = FullRegressionPreflight(ROOT).run(collection=payload, full_budget_state=0)
    assert not result.ok
    assert result.data['report']['collection']['sealed'] is False
    assert any(f.id == 'FRX24B_COLLECTION_SEAL_BLOCK' for f in result.findings)


def test_preflight_negative_topology_fixture_blocks_before_budget():
    result = FullRegressionPreflight(ROOT).run(collection=COLLECTION, full_budget_state=0, topology_fixture=NEGATIVE)
    assert not result.ok
    assert result.data['report']['budget']['budget_reserved'] is False
    assert result.data['report']['safety']['full_regression_runs'] == 0
    assert any(f.id == 'FRX24B_TOPOLOGY_DOWNGRADE_BLOCK' for f in result.findings)


def test_preflight_safe_parallel_opt_in_is_only_high_level_preview():
    result = FullRegressionPreflight(ROOT).run(collection=COLLECTION, full_budget_state=0, parallel_opt_in=True)
    assert result.ok, result.to_dict()
    report = result.data['report']
    assert report['topology']['parallel_opt_in'] is True
    assert report['topology']['effective_workers'] == 2
    assert report['topology']['parallel_opt_in_ceiling'] == 2
    assert report['safety']['tests_executed'] is False
    assert report['safety']['budget_reserved'] is False


def test_full_session_cli_plan_exposes_profile_id_not_legacy_shard_size():
    cp = subprocess.run([sys.executable, '-m', 'devpilot_core', 'tests', 'full-session', 'plan', '--help'], cwd=ROOT, text=True, capture_output=True, check=False)
    assert cp.returncode == 0, cp.stderr
    text = cp.stdout
    assert '--profile-id' in text
    assert '--full-budget-state' in text
    assert '--shard-size' not in text
    assert '--target-shard-seconds' not in text
    assert '--max-nodeids' not in text
    assert '--nodeid-transport' not in text


def test_full_regression_preflight_cli_has_no_low_level_topology_knobs():
    cp = subprocess.run([sys.executable, '-m', 'devpilot_core', 'tests', 'full-regression', 'preflight', '--help'], cwd=ROOT, text=True, capture_output=True, check=False)
    assert cp.returncode == 0, cp.stderr
    text = cp.stdout
    assert '--profile-id' in text
    assert '--parallel-opt-in' in text
    assert '--max-nodeids' not in text
    assert '--target-shard-seconds' not in text
    assert '--nodeid-transport' not in text
    assert '--workers' not in text


def test_full_regression_profile_cli_passes_and_reports_current_profile():
    cp = subprocess.run([sys.executable, '-m', 'devpilot_core', 'tests', 'full-regression', 'profile', '--json'], cwd=ROOT, text=True, capture_output=True, check=False)
    assert cp.returncode == 0, cp.stderr
    payload = json.loads(cp.stdout)
    assert payload['ok'] is True
    assert payload['data']['summary']['current_profile_id'] == 'frx-v2.4-current'
    assert payload['data']['summary']['budget_reserved'] is False


def test_uoc_legacy_direct_full_worker_is_blocked_before_job_creation():
    result = QualityOperationsApplicationService(ROOT).plan_job(
        operation_id='full-regression', workspace_id='devpilot-local', parameters={}, idempotency_key='frx24b-no-direct-full'
    )
    assert not result.ok
    assert result.exit_code.value == 2
    assert any(f.id == 'FRX24B_DIRECT_FULL_WORKER_BLOCK' for f in result.findings)


def test_quality_worker_has_explicit_full_regression_runtime_backstop():
    source = (ROOT / 'src/devpilot_core/application/quality_job_worker.py').read_text(encoding='utf-8')
    assert "elif kind=='tests-full':" in source
    assert 'FRX-v2.4-B blocks the legacy direct full-regression worker' in source
    assert "elif kind=='tests-focused':" in source


def test_profile_governed_full_session_path_is_bound_in_cli_source():
    source = (ROOT / 'src/devpilot_core/cli.py').read_text(encoding='utf-8')
    assert 'manager.plan_governed' in source
    assert 'manager.validate_governed_execution' in source
    assert 'FRX-v2.4 profile-locked shard plan after preflight' in source


def test_legacy_temporal_planner_cli_remains_preview_only_not_full_consumer():
    source = (ROOT / 'src/devpilot_core/cli.py').read_text(encoding='utf-8')
    assert 'Preview FRX-v2.2-C temporal shard plans without enabling scheduler execution' in source
    assert '"tests_executed":False' in source
    assert '"scheduler_enabled":False' in source
