from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from devpilot_core.application import (
    GovernedJobCapabilityRegistry,
    GovernedJobConflict,
    GovernedJobFramework,
    GovernedJobPolicyBlock,
    GovernedJobStore,
)

ROOT = Path(__file__).resolve().parents[1]


def _canonical_framework(tmp_path: Path) -> GovernedJobFramework:
    return GovernedJobFramework(
        ROOT,
        registry=GovernedJobCapabilityRegistry(ROOT),
        store=GovernedJobStore(tmp_path),
    )


def _bound_registry(tmp_path: Path, *, supports_cancel: bool = True, supports_rollback: bool = True, approval: bool = False) -> GovernedJobCapabilityRegistry:
    registry = {
        'schema_version': '1.0',
        'schema_id': 'SCHEMA-DEVPL-GOVERNED-JOB-CAPABILITY-REGISTRY-V1',
        'registry_id': 'devpilot-governed-job-capability-registry',
        'created_by': 'UOC-007',
        'status': 'implemented-initial',
        'version': '1.0.0',
        'updated': '2026-08-10',
        'source_registry': '.devpilot/interfaces/ui_capability_registry.json',
        'capabilities': [{
            'capability_id': 'cli.test.echo',
            'cli_command_id': 'test.echo',
            'cli_command': 'python -m devpilot_core test echo',
            'application_service': 'test.echo',
            'risk_class': 'sensitive' if approval else 'read-only',
            'parity_status': 'CLI-BRIDGE-REGISTERED',
            'policy_binding': {
                'source': '.devpilot/miasi/policy_matrix.json',
                'required': approval,
                'default_decision': 'plan-only' if approval else 'allow-read-only',
                'approval_required': approval,
            },
            'budgets': {'timeout_seconds': 30, 'retry_limit': 1, 'heartbeat_interval_seconds': 5},
            'contracts': {
                'request_envelope_schema_id': 'SCHEMA-DEVPL-GOVERNED-JOB-REQUEST-V1',
                'result_envelope_schema_id': 'SCHEMA-DEVPL-GOVERNED-JOB-RESULT-V1',
                'command_result_schema_id': 'SCHEMA-DEVPL-COMMAND-RESULT-V1',
                'typed_parameters_schema_id': 'SCHEMA-TEST-ECHO-INPUT-V1',
            },
            'controls': {
                'dry_run_required': approval,
                'approval_required': approval,
                'supports_cancel': supports_cancel,
                'supports_rollback': supports_rollback,
                'idempotency_required': True,
                'correlation_required': True,
            },
            'evidence_mapping': {
                'command_result_required': True,
                'trace_required': True,
                'report_required': False,
                'evidence_reference_required': True,
                'commit_reference_required': False,
                'token_or_secret_allowed': False,
            },
            'runtime': {
                'registered': True,
                'planning_enabled': True,
                'execution_enabled': True,
                'adapter_bound': True,
                'adapter_id': 'typed.test.echo',
                'mode': 'typed-adapter',
            },
        }],
        'summary': {},
        'safety': {
            'local_first': True,
            'arbitrary_shell_allowed': False,
            'remote_execution_enabled': False,
            'connector_write_enabled': False,
            'plugin_execution_enabled': False,
            'external_api_required': False,
            'runtime_execution_from_ui_enabled': False,
        },
    }
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps(registry), encoding='utf-8')
    return GovernedJobCapabilityRegistry(tmp_path, path)


def test_uoc007_plan_is_idempotent_and_persists_only_hashes_not_raw_inputs(tmp_path: Path) -> None:
    framework = _canonical_framework(tmp_path)
    first = framework.plan(
        capability_id='cli.workspace.status',
        workspace_id='inventory-sales-local',
        parameters={'secret_like': 'DO-NOT-PERSIST-THIS', 'mode': 'status'},
        idempotency_key='idem-uoc007-001',
    )
    second = framework.plan(
        capability_id='cli.workspace.status',
        workspace_id='inventory-sales-local',
        parameters={'secret_like': 'DO-NOT-PERSIST-THIS', 'mode': 'status'},
        idempotency_key='idem-uoc007-001',
    )
    assert second.idempotent_replay is True
    assert second.record['job_id'] == first.record['job_id']
    persisted = json.loads((tmp_path / 'outputs/runtime/governed_jobs/jobs' / f"{first.record['job_id']}.json").read_text(encoding='utf-8'))
    serialized = json.dumps(persisted)
    assert 'DO-NOT-PERSIST-THIS' not in serialized
    assert 'idem-uoc007-001' not in serialized
    assert persisted['parameter_keys'] == ['mode', 'secret_like']
    assert len(persisted['idempotency_key_hash']) == 64
    assert first.record['correlation_id'].startswith('corr_')


def test_uoc007_idempotency_conflict_is_blocked(tmp_path: Path) -> None:
    framework = _canonical_framework(tmp_path)
    framework.plan(capability_id='cli.workspace.status', workspace_id='ws', parameters={'a': 1}, idempotency_key='same-key')
    with pytest.raises(GovernedJobConflict):
        framework.plan(capability_id='cli.workspace.status', workspace_id='ws', parameters={'a': 2}, idempotency_key='same-key')


def test_uoc007_canonical_registry_cannot_start_runtime_execution(tmp_path: Path) -> None:
    framework = _canonical_framework(tmp_path)
    handle = framework.plan(capability_id='cli.workspace.status', workspace_id='ws', parameters={}, idempotency_key='runtime-block')
    framework.queue(handle.record['job_id'])
    with pytest.raises(GovernedJobPolicyBlock):
        framework.start(handle.record['job_id'])


def test_uoc007_typed_bound_adapter_executes_without_shell_and_heartbeats(tmp_path: Path) -> None:
    registry = _bound_registry(tmp_path)
    framework = GovernedJobFramework(tmp_path, registry=registry, store=GovernedJobStore(tmp_path))
    handle = framework.plan(capability_id='cli.test.echo', workspace_id='ws', parameters={'value': 7}, idempotency_key='echo-1')
    assert handle.cancel_token is not None
    completed = framework.execute_with(
        handle.record['job_id'],
        parameters={'value': 7},
        executor=lambda payload: {'ok': True, 'exit_code': 0, 'data': {'echo': payload['value']}},
    )
    assert completed['status'] == 'pass'
    assert completed['heartbeat_sequence'] >= 1
    assert completed['result_summary']['data']['echo'] == 7


def test_uoc007_cancel_token_is_hash_only_and_wrong_token_is_rejected(tmp_path: Path) -> None:
    registry = _bound_registry(tmp_path)
    framework = GovernedJobFramework(tmp_path, registry=registry, store=GovernedJobStore(tmp_path))
    handle = framework.plan(capability_id='cli.test.echo', workspace_id='ws', parameters={}, idempotency_key='cancel-1')
    framework.queue(handle.record['job_id'])
    framework.start(handle.record['job_id'])
    with pytest.raises(GovernedJobPolicyBlock):
        framework.request_cancel(handle.record['job_id'], cancel_token='ct_wrong')
    requested = framework.request_cancel(handle.record['job_id'], cancel_token=str(handle.cancel_token))
    assert requested['status'] == 'cancel-requested'
    cancelled = framework.mark_cancelled(handle.record['job_id'])
    assert cancelled['status'] == 'cancelled'
    raw = (tmp_path / 'outputs/runtime/governed_jobs/jobs' / f"{handle.record['job_id']}.json").read_text(encoding='utf-8')
    assert str(handle.cancel_token) not in raw


def test_uoc007_approval_and_rollback_lifecycle(tmp_path: Path) -> None:
    registry = _bound_registry(tmp_path, approval=True)
    framework = GovernedJobFramework(tmp_path, registry=registry, store=GovernedJobStore(tmp_path))
    handle = framework.plan(capability_id='cli.test.echo', workspace_id='ws', parameters={'value': 1}, idempotency_key='approve-1')
    assert handle.record['status'] == 'pending-approval'
    with pytest.raises(GovernedJobPolicyBlock):
        framework.queue(handle.record['job_id'])
    approved = framework.approve(handle.record['job_id'], approval_binding_id='approval_test_001')
    assert approved['status'] == 'approved'
    framework.queue(handle.record['job_id'])
    framework.start(handle.record['job_id'])
    framework.complete(handle.record['job_id'], status='pass', evidence_refs=['evidence:test'])
    rollback = framework.begin_rollback(handle.record['job_id'])
    assert rollback['status'] == 'rollback-running'
    done = framework.mark_rolled_back(handle.record['job_id'], evidence_refs=['evidence:rollback'])
    assert done['status'] == 'rolled-back'
    assert done['evidence_refs'] == ['evidence:rollback', 'evidence:test']


def test_uoc007_job_v2_schema_accepts_real_planned_record(tmp_path: Path) -> None:
    framework = _canonical_framework(tmp_path)
    handle = framework.plan(capability_id='cli.workspace.status', workspace_id='ws', parameters={}, idempotency_key='schema-1')
    schema = json.loads((ROOT / 'docs/schemas/ui_governed_job_v2.schema.json').read_text(encoding='utf-8'))
    Draft202012Validator(schema).validate(handle.record)
