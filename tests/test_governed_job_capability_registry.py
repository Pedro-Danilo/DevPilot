from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import GovernedJobCapabilityRegistry

ROOT = Path(__file__).resolve().parents[1]


def test_uoc007_governed_job_registry_covers_ui_capabilities_exactly() -> None:
    result = GovernedJobCapabilityRegistry(ROOT).validate()
    assert result.ok is True, result.to_dict()
    summary = result.data['summary']
    assert summary['capabilities_total'] == 193
    assert summary['ui_capabilities_total'] == 193
    assert summary['coverage_exact'] is True
    assert summary['planning_enabled_total'] == 188
    assert summary['execution_enabled_total'] == 0
    assert summary['adapter_bound_total'] == 0
    assert summary['forbidden_total'] == 5


def test_uoc007_registry_blocks_forbidden_runtime_and_untyped_execution() -> None:
    payload = json.loads((ROOT / '.devpilot/interfaces/governed_job_capability_registry.json').read_text(encoding='utf-8'))
    for capability in payload['capabilities']:
        runtime = capability['runtime']
        if capability['risk_class'] == 'forbidden':
            assert runtime['planning_enabled'] is False
            assert runtime['execution_enabled'] is False
        assert runtime['execution_enabled'] is False
        assert runtime['adapter_bound'] is False
        assert runtime['adapter_id'] is None
        assert capability['contracts']['typed_parameters_schema_id'] is None
        assert capability['policy_binding']['source'] == '.devpilot/miasi/policy_matrix.json'
        assert capability['controls']['idempotency_required'] is True
        assert capability['controls']['correlation_required'] is True


def test_uoc007_sensitive_capabilities_always_require_approval() -> None:
    payload = json.loads((ROOT / '.devpilot/interfaces/governed_job_capability_registry.json').read_text(encoding='utf-8'))
    sensitive = [item for item in payload['capabilities'] if item['risk_class'] == 'sensitive']
    assert sensitive
    assert all(item['controls']['approval_required'] for item in sensitive)
    assert all(item['policy_binding']['approval_required'] for item in sensitive)
