from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core.application.governed_job_operations import GovernedJobLogStore
from devpilot_core.application.story_validation_jobs import StoryValidationJobApplicationService
from devpilot_core.cli_models import CommandResult, ExitCode

ROOT = Path(__file__).resolve().parents[1]


def _root(tmp_path: Path) -> Path:
    for rel in [
        '.devpilot/quality/story_validation_job_capabilities.json',
        '.devpilot/quality/story_validation_job_profiles.json',
    ]:
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dst)
    return tmp_path


def _plan(*, status: str = 'APPROVED', hash_value: str = 'a' * 64, paths: list[str] | None = None) -> dict:
    return {
        'test_plan_id': 'story-test-plan-' + '1' * 24,
        'test_plan_hash': hash_value,
        'status': status,
        'workspace_id': 'workspace-10b',
        'story_execution_id': 'story-execution-10b',
        'changed_paths': paths or ['src/devpilot_core/application/quality_operations.py', 'ui/web/src/pages/JobsView.ts'],
        'required_tests': ['tests/test_quality_operations_service.py'],
        'effective_required_tests': ['tests/test_quality_operations_service.py'],
        'recommended_tests': ['tests/test_governed_job_operations.py'],
        'full_regression_signal': {'execution_authorized': False, 'informational_only': True},
    }


def _loader(plan: dict):
    def load(*, test_plan_id: str):
        if test_plan_id != plan['test_plan_id']:
            return CommandResult('load', False, ExitCode.BLOCK, 'missing')
        return CommandResult('load', True, ExitCode.PASS, 'ok', data={'story_test_plan': dict(plan)})
    return load


def test_approved_plan_derives_typed_test_build_lint_jobs_without_shell(tmp_path: Path):
    root = _root(tmp_path); plan = _plan()
    service = StoryValidationJobApplicationService(root, story_test_plan_loader=_loader(plan))
    result = service.create_for_plan(test_plan_id=plan['test_plan_id'], test_plan_hash=plan['test_plan_hash'], actor='owner-1', actor_role='owner')
    assert result.ok
    jobs = result.data['jobs']
    assert {job['story_validation_kind'] for job in jobs} == {'test', 'build', 'lint'}
    assert all(job['approval_binding_id'].startswith('story-test-plan:') for job in jobs)
    assert result.data['summary']['full_regression'] is False
    assert result.data['summary']['arbitrary_shell'] is False
    for job in jobs:
        assert job['retry_limit'] == 1
        assert job['supports_cancel'] is True
        assert job['runtime_context_ref'].startswith('outputs/runtime/gsdlc10b_story_validation/contexts/')


def test_stale_or_unapproved_story_test_plan_is_fail_closed(tmp_path: Path):
    root = _root(tmp_path); plan = _plan(status='DRAFT')
    service = StoryValidationJobApplicationService(root, story_test_plan_loader=_loader(plan))
    blocked = service.create_for_plan(test_plan_id=plan['test_plan_id'], test_plan_hash=plan['test_plan_hash'], actor='owner-1', actor_role='owner')
    assert not blocked.ok
    assert blocked.findings[0].id == 'GSDLC10B_TEST_PLAN_STATUS_BLOCK'
    plan['status'] = 'APPROVED'
    blocked_hash = service.create_for_plan(test_plan_id=plan['test_plan_id'], test_plan_hash='b' * 64, actor='owner-1', actor_role='owner')
    assert not blocked_hash.ok
    assert blocked_hash.findings[0].id == 'GSDLC10B_TEST_PLAN_HASH_BLOCK'


def test_plan_is_idempotent_and_retry_keeps_exact_context_identity(tmp_path: Path):
    root = _root(tmp_path); plan = _plan(paths=['src/devpilot_core/application/quality_operations.py'])
    service = StoryValidationJobApplicationService(root, story_test_plan_loader=_loader(plan))
    first = service.create_for_plan(test_plan_id=plan['test_plan_id'], test_plan_hash=plan['test_plan_hash'], actor='owner', actor_role='owner')
    second = service.create_for_plan(test_plan_id=plan['test_plan_id'], test_plan_hash=plan['test_plan_hash'], actor='owner', actor_role='owner')
    assert first.ok and second.ok
    assert [x['job_id'] for x in first.data['jobs']] == [x['job_id'] for x in second.data['jobs']]
    job = next(x for x in first.data['jobs'] if x['story_validation_kind'] == 'test')
    original = service.store.load(job['job_id'])
    service.framework.queue(job['job_id']); service.framework.start(job['job_id']); service.framework.complete(job['job_id'], status='block', result_summary={'failed': 1})
    retry = service.operations.retry(job_id=job['job_id'], actor='owner', reason='bounded retry')
    assert retry.ok
    retried = retry.data['job']
    assert retried['job_id'] != job['job_id']
    assert retried['retry_count'] == 1
    assert retried['runtime_context_ref'] == original['runtime_context_ref']
    assert retried['story_test_plan_hash'] == plan['test_plan_hash']
    assert retry.data['retry_of_job_id'] == job['job_id']


def test_log_store_redacts_secrets_and_is_bounded(tmp_path: Path):
    logs = GovernedJobLogStore(tmp_path, max_bytes_per_job=1024)
    job_id = 'job_' + 'a' * 32
    logs.append(job_id, level='INFO', phase='test', message='token=super-secret Bearer abc.def password=hunter2')
    payload = logs.read(job_id, cursor=0, limit=10)
    text = json.dumps(payload)
    assert 'super-secret' not in text and 'abc.def' not in text and 'hunter2' not in text
    assert '<redacted>' in text


def test_no_command_string_or_full_regression_contract_exposed(tmp_path: Path):
    root = _root(tmp_path); plan = _plan(paths=['src/devpilot_core/application/quality_operations.py'])
    service = StoryValidationJobApplicationService(root, story_test_plan_loader=_loader(plan))
    result = service.create_for_plan(test_plan_id=plan['test_plan_id'], test_plan_hash=plan['test_plan_hash'], actor='owner', actor_role='owner')
    assert result.ok
    for job in result.data['jobs']:
        record = service.store.load(job['job_id'])
        assert 'command' not in record['parameter_keys']
        context = json.loads((root / record['runtime_context_ref']).read_text())
        assert context['full_regression'] is False
        assert 'command' not in context


def test_orphan_reconciliation_never_promotes_to_pass(tmp_path: Path):
    root = _root(tmp_path); plan = _plan(paths=['src/devpilot_core/application/quality_operations.py'])
    service = StoryValidationJobApplicationService(root, story_test_plan_loader=_loader(plan))
    created = service.create_for_plan(test_plan_id=plan['test_plan_id'], test_plan_hash=plan['test_plan_hash'], actor='owner', actor_role='owner')
    job = next(x for x in created.data['jobs'] if x['story_validation_kind'] == 'test')
    service.framework.queue(job['job_id']); service.framework.start(job['job_id'])
    record = service.store.load(job['job_id']); record['last_heartbeat_at'] = '2000-01-01T00:00:00Z'; record['updated_at'] = '2000-01-01T00:00:00Z'; service.store.save(record)
    reconciled = service.operations.reconcile_orphans(stale_after_seconds=30)
    assert reconciled.ok and job['job_id'] in reconciled.data['reconciled_job_ids']
    final = service.store.load(job['job_id'])
    assert final['status'] == 'error'
    assert final['status'] != 'pass'


def test_ui_contract_exposes_typed_job_planning_job_console_and_no_free_form_command():
    story = (ROOT / 'ui/web/src/pages/StoryCodeWorkbenchView.ts').read_text(encoding='utf-8')
    jobs = (ROOT / 'ui/web/src/pages/JobsView.ts').read_text(encoding='utf-8')
    assert 'Planificar jobs tipados' in story
    assert 'createStoryValidationJobs' in story
    assert 'Abrir Job Console' in story
    assert 'FULL REGRESSION=0 EN 10-B' in story
    assert 'Iniciar validación tipada' in jobs
    assert 'startStoryValidationJob' in jobs
    assert 'refreshSelected(client, state.selected.job_id)' in jobs
    assert 'state.logs = await client.jobLogs(jobId, 0, 200)' in jobs
    assert 'free-form' not in story.lower() or 'no' in story.lower()


def test_worker_timeout_terminates_process_tree_and_reports_timed_out(tmp_path: Path):
    import sys
    import time
    from devpilot_core.application.story_validation_job_worker import _stream_process

    logs = GovernedJobLogStore(tmp_path, max_bytes_per_job=4096)
    started = time.monotonic()
    rc, timed_out = _stream_process(
        tmp_path,
        'job_' + 'b' * 32,
        [sys.executable, '-c', 'import time; time.sleep(10)'],
        timeout_seconds=1,
        logs=logs,
    )
    elapsed = time.monotonic() - started
    assert timed_out is True
    assert rc != 0
    assert elapsed < 6


def test_worker_test_adapter_emits_junit_and_structured_result_refs(tmp_path: Path):
    from devpilot_core.application.story_validation_job_worker import run_job

    root = _root(tmp_path)
    sample = root / 'tests/test_gsdlc10b_sample.py'
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_text('def test_sample():\n    assert 2 + 2 == 4\n', encoding='utf-8')
    plan = _plan(paths=['src/devpilot_core/application/quality_operations.py'])
    plan['required_tests'] = ['tests/test_gsdlc10b_sample.py']
    plan['effective_required_tests'] = ['tests/test_gsdlc10b_sample.py']
    plan['recommended_tests'] = []
    service = StoryValidationJobApplicationService(root, story_test_plan_loader=_loader(plan))
    created = service.create_for_plan(
        test_plan_id=plan['test_plan_id'],
        test_plan_hash=plan['test_plan_hash'],
        actor='owner',
        actor_role='owner',
    )
    job = next(x for x in created.data['jobs'] if x['story_validation_kind'] == 'test')
    service.framework.queue(job['job_id'])
    rc = run_job(root, job['job_id'])
    assert rc == 0
    final = service.store.load(job['job_id'])
    assert final['status'] == 'pass'
    refs = list(final.get('artifact_refs') or [])
    junit_ref = next(x for x in refs if x.endswith('.xml'))
    result_ref = next(x for x in refs if x.endswith('.json'))
    assert (root / junit_ref).is_file()
    result = json.loads((root / result_ref).read_text(encoding='utf-8'))
    assert result['job_kind'] == 'test'
    assert result['summary']['tests'] == 1
    assert result['summary']['passed'] == 1
    assert result['summary']['failed'] == 0
    assert result['full_regression'] is False


def test_story_job_cancel_uses_process_tree_termination(tmp_path: Path, monkeypatch):
    from devpilot_core.application.governed_job_operations import ControlledProcessTree

    root = _root(tmp_path)
    plan = _plan(paths=['src/devpilot_core/application/quality_operations.py'])
    service = StoryValidationJobApplicationService(root, story_test_plan_loader=_loader(plan))
    created = service.create_for_plan(
        test_plan_id=plan['test_plan_id'],
        test_plan_hash=plan['test_plan_hash'],
        actor='owner',
        actor_role='owner',
    )
    job = next(x for x in created.data['jobs'] if x['story_validation_kind'] == 'test')
    service.framework.queue(job['job_id'])
    service.framework.start(job['job_id'])
    meta = service.metadata.load(job['job_id'])
    meta['worker_pid'] = 43210
    service.metadata.save(meta)
    called: list[int] = []

    def fake_terminate(pid: int):
        called.append(pid)
        return {'pid': pid, 'terminated': True, 'method': 'process-tree-test'}

    monkeypatch.setattr(ControlledProcessTree, 'terminate', staticmethod(fake_terminate))
    result = service.operations.request_cancel(job_id=job['job_id'], actor='owner', reason='cancel tree test')
    assert result.ok
    assert called == [43210]
    assert service.store.load(job['job_id'])['status'] == 'cancelled'
    assert result.data['process_tree']['terminated'] is True
