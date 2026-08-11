from __future__ import annotations
import json, shutil
from pathlib import Path
import pytest
from devpilot_core.application.quality_operations import QualityOperationsApplicationService, QualityOperationProfileRegistry

ROOT=Path(__file__).resolve().parents[1]

def test_uoc009_catalog_is_typed_no_shell_and_runtime_subset_bound() -> None:
    service=QualityOperationsApplicationService(ROOT); result=service.catalog(); assert result.ok
    assert result.data['summary']['arbitrary_shell'] is False and result.data['summary']['free_pytest_args'] is False
    assert result.data['summary']['runtime_enabled_total']==10
    assert len(result.data['operations'])==11

def test_uoc009_test_impact_accepts_repo_relative_and_blocks_absolute_or_traversal() -> None:
    s=QualityOperationsApplicationService(ROOT); assert s.test_impact_plan(changed_paths=['README.md']).ok
    assert not s.test_impact_plan(changed_paths=['../secret']).ok
    assert not s.test_impact_plan(changed_paths=['C:/secret']).ok

def test_uoc009_full_regression_requires_confirmation_and_approval_before_plan() -> None:
    s=QualityOperationsApplicationService(ROOT)
    r=s.plan_job(operation_id='full-regression',workspace_id='devpilot-local',parameters={},idempotency_key='uoc009-confirm-no',full_regression_confirmation='NO')
    assert not r.ok and r.exit_code.value==2
    r=s.plan_job(operation_id='full-regression',workspace_id='devpilot-local',parameters={'confirmation':'RUN FULL REGRESSION'},idempotency_key='uoc009-no-approval',full_regression_confirmation='RUN FULL REGRESSION')
    assert not r.ok and 'approval' in r.message.lower()

def test_uoc009_focused_tests_accept_registry_profile_only() -> None:
    s=QualityOperationsApplicationService(ROOT)
    r=s.plan_job(operation_id='focused-tests',workspace_id='devpilot-local',parameters={'tcr_profile':'not-a-profile'},idempotency_key='uoc009-invalid-profile',approval_id='missing')
    assert not r.ok and 'profile' in r.message.lower()

def test_uoc009_worker_source_has_fixed_subprocess_contract() -> None:
    source=(ROOT/'src/devpilot_core/application/quality_job_worker.py').read_text(encoding='utf-8')+(ROOT/'src/devpilot_core/application/quality_operations.py').read_text(encoding='utf-8')
    assert 'shell=False' in source
    assert 'shell=True' not in source and 'os.system' not in source and 'eval(' not in source and 'exec(' not in source
    assert "[sys.executable,'-m','pytest','-q',*files" in source


def test_uoc009_execute_uses_operational_metadata_store_contract(monkeypatch) -> None:
    from types import SimpleNamespace
    import devpilot_core.application.quality_operations as module
    service=QualityOperationsApplicationService(ROOT)
    job_id='job_'+'1'*32
    record={'job_id':job_id,'status':'planned','updated_at':'2026-08-11T00:00:00Z'}
    monkeypatch.setattr(service.jobs.store,'load',lambda _job_id: dict(record))
    monkeypatch.setattr(service.runtime,'load_plan',lambda _job_id: {'operation_id':'project-state'})
    monkeypatch.setattr(service.jobs,'queue',lambda _job_id: None)
    saved={}
    monkeypatch.setattr(service.meta,'load',lambda _job_id: {'schema_id':'devpilot.uoc008.job_operational_metadata.v1','job_id':job_id})
    monkeypatch.setattr(service.meta,'save',lambda payload: saved.update(payload))
    monkeypatch.setattr(module.subprocess,'Popen',lambda *args,**kwargs: SimpleNamespace(pid=4321))
    result=service.execute_job(job_id=job_id)
    assert result.ok is True
    assert result.data['worker']['pid']==4321 and result.data['worker']['shell'] is False
    assert saved['worker_pid']==4321 and saved['phase']=='worker-starting'


def test_uoc009_quality_profile_registry_is_lazy_for_non_platform_workspace(tmp_path: Path) -> None:
    registry=QualityOperationProfileRegistry(tmp_path)
    assert registry.path == tmp_path.resolve()/'.devpilot/quality/ui_quality_operation_profiles.json'
    assert registry._payload is None and registry._profiles is None

