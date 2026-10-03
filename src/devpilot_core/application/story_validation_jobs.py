from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

from .governed_job_capability_registry import GovernedJobCapabilityRegistry
from .governed_job_operations import GovernedJobOperationalMetadataStore, GovernedJobOperationsApplicationService
from .governed_jobs import GovernedJobFramework, GovernedJobPolicyBlock, GovernedJobStore

CAPABILITY_REGISTRY = Path('.devpilot/quality/story_validation_job_capabilities.json')
PROFILE_REGISTRY = Path('.devpilot/quality/story_validation_job_profiles.json')
RUNTIME_ROOT = Path('outputs/runtime/gsdlc10b_story_validation')
CONTEXT_SCHEMA_ID = 'SCHEMA-DEVPL-GSDLC-10-B-STORY-VALIDATION-JOB-CONTEXT-V1'


def _sha(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=str(path.parent))
    temp = Path(name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


class StoryValidationJobApplicationService:
    """GSDLC-10-B story-bound governed validation job orchestration.

    The browser never supplies commands. An APPROVED StoryTestPlan is the immutable
    authority for test targets and changed paths. A small current-active registry
    chooses the typed adapter (test/build/lint). GovernedJobFramework remains the
    lifecycle store used by the existing Job Console/cancel/retry/orphan logic.
    """

    def __init__(
        self,
        root: Path,
        *,
        story_test_plan_loader: Callable[..., CommandResult],
        context_resolver=None,
    ) -> None:
        self.root = Path(root).resolve()
        self.story_test_plan_loader = story_test_plan_loader
        self.context_resolver = context_resolver
        self.registry = GovernedJobCapabilityRegistry(self.root, registry_path=CAPABILITY_REGISTRY)
        self.framework = GovernedJobFramework(self.root, registry=self.registry, store=GovernedJobStore(self.root))
        self.store = self.framework.store
        self.operations = GovernedJobOperationsApplicationService(self.root)
        self.metadata = GovernedJobOperationalMetadataStore(self.root)
        self.profiles = self._load_profiles()

    def create_for_plan(self, *, test_plan_id: str, test_plan_hash: str, actor: str, actor_role: str) -> CommandResult:
        command = 'story validation jobs create'
        if actor_role not in {'owner', 'developer'}:
            return self._block(command, 'GSDLC10B_JOB_ROLE_BLOCK', 'Story validation jobs require an authenticated owner/developer human role.')
        plan, failure = self._approved_test_plan(command, test_plan_id, test_plan_hash)
        if failure:
            return failure
        assert plan is not None
        workspace_id = str(plan.get('workspace_id') or '')
        story_execution_id = str(plan.get('story_execution_id') or '')
        changed_paths = sorted(set(str(x).replace('\\', '/') for x in plan.get('changed_paths', []) if str(x).strip()))
        tests = sorted(set(str(x) for x in list(plan.get('effective_required_tests') or plan.get('required_tests') or []) + list(plan.get('recommended_tests') or [])))
        if not workspace_id or not story_execution_id or not changed_paths:
            return self._block(command, 'GSDLC10B_PLAN_BINDING_BLOCK', 'Approved StoryTestPlan is missing workspace/story/changed-path binding.')
        if len(tests) > 200:
            return self._block(command, 'GSDLC10B_TEST_TARGET_BUDGET_BLOCK', 'StoryTestPlan exceeds the bounded 200-target validation budget.')
        if any(not self._safe_test_target(x) for x in tests):
            return self._block(command, 'GSDLC10B_TEST_TARGET_CONTRACT_BLOCK', 'StoryTestPlan contains a test target outside the typed repository test contract.')

        execution_root, execution_root_source, failure = self._execution_root(command, workspace_id)
        if failure:
            return failure
        assert execution_root is not None

        applicable = [profile for profile in self.profiles if self._applies(profile, changed_paths)]
        if not applicable:
            return self._block(command, 'GSDLC10B_NO_JOB_PROFILE_BLOCK', 'No typed validation profile applies to this StoryTestPlan.')
        if any(str(profile.get('job_kind')) == 'test' for profile in applicable) and not tests:
            return self._block(
                command,
                'GSDLC10B_EMPTY_TEST_TARGET_BLOCK',
                'The approved StoryTestPlan has no executable test targets; typed test jobs cannot be planned.',
            )

        jobs: list[dict[str, Any]] = []
        for profile in applicable:
            kind = str(profile['job_kind'])
            context_core = {
                'schema_id': CONTEXT_SCHEMA_ID,
                'job_kind': kind,
                'workspace_id': workspace_id,
                'story_execution_id': story_execution_id,
                'story_test_plan_id': test_plan_id,
                'story_test_plan_hash': test_plan_hash,
                'changed_paths': changed_paths,
                'test_targets': tests if kind == 'test' else [],
                'adapter': str(profile['adapter']),
                'limits': dict(profile.get('limits') or {}),
                'full_regression': False,
                'execution_root': str(execution_root),
                'execution_root_source': execution_root_source,
            }
            context_hash = _sha(context_core)
            context = {**context_core, 'context_hash': context_hash}
            binding = f'story-test-plan:{test_plan_id}:{test_plan_hash}'
            try:
                handle = self.framework.plan(
                    capability_id=str(profile['capability_id']),
                    workspace_id=workspace_id,
                    parameters={'story_test_plan_id': test_plan_id, 'story_test_plan_hash': test_plan_hash, 'job_kind': kind},
                    idempotency_key=f'gsdlc10b:{test_plan_hash}:{kind}',
                    dry_run=False,
                    timeout_seconds=int((profile.get('limits') or {}).get('timeout_seconds', 300)),
                    retry_limit=1,
                    approval_binding_id=binding,
                )
            except Exception as exc:
                return self._block(command, 'GSDLC10B_GOVERNED_JOB_PLAN_BLOCK', f'{type(exc).__name__}: {exc}')
            record = dict(handle.record)
            context_path = self._context_path(record['job_id'])
            if not context_path.exists():
                _atomic_json(context_path, context)
            else:
                existing = json.loads(context_path.read_text(encoding='utf-8'))
                if existing != context:
                    return self._block(command, 'GSDLC10B_CONTEXT_COLLISION_BLOCK', 'Idempotent job context differs from the immutable StoryTestPlan projection.')
            record['runtime_context_ref'] = str(context_path.relative_to(self.root)).replace('\\', '/')
            record['story_test_plan_id'] = test_plan_id
            record['story_test_plan_hash'] = test_plan_hash
            record['story_validation_kind'] = kind
            self.store.save(record)
            jobs.append(self._project(record))

        batch_id = f'story-validation-batch-{_sha({"test_plan_hash": test_plan_hash, "job_ids": sorted(x["job_id"] for x in jobs)})[:24]}'
        return self._pass(command, 'Typed validation jobs planned from APPROVED StoryTestPlan; no free-form command accepted.', {
            'batch_id': batch_id,
            'story_test_plan_id': test_plan_id,
            'story_test_plan_hash': test_plan_hash,
            'jobs': jobs,
            'summary': {'jobs_total': len(jobs), 'job_kinds': sorted(x['story_validation_kind'] for x in jobs), 'full_regression': False, 'arbitrary_shell': False},
        })

    def list_for_plan(self, *, test_plan_id: str) -> CommandResult:
        jobs = [self._project(record) for record in self.store.list() if str(record.get('story_test_plan_id') or '') == str(test_plan_id)]
        jobs.sort(key=lambda item: (item.get('created_at', ''), item.get('job_id', '')))
        return self._pass('story validation jobs list', 'Story validation jobs loaded.', {'story_test_plan_id': test_plan_id, 'jobs': jobs, 'summary': {'jobs_total': len(jobs)}})

    def start(self, *, job_id: str) -> CommandResult:
        command = 'story validation job start'
        try:
            record = self.store.load(job_id)
        except KeyError:
            return self._block(command, 'GSDLC10B_JOB_NOT_FOUND_BLOCK', 'Story validation job was not found.')
        if not str(record.get('capability_id', '')).startswith('story.validation.'):
            return self._block(command, 'GSDLC10B_JOB_CAPABILITY_BLOCK', 'Job is not a StoryValidationJob capability.')
        context, failure = self._context_for_record(command, record)
        if failure:
            return failure
        assert context is not None
        _, failure = self._approved_test_plan(command, str(context['story_test_plan_id']), str(context['story_test_plan_hash']))
        if failure:
            return self._block(command, 'GSDLC10B_STALE_TEST_PLAN_BLOCK', 'StoryValidationJob cannot start because its StoryTestPlan is no longer an exact APPROVED authority.')
        if bool(context.get('full_regression')):
            return self._block(command, 'GSDLC10B_FULL_REGRESSION_BLOCK', 'GSDLC-10-B cannot start a Full Regression job.')
        status = str(record.get('status'))
        queued = False
        try:
            if status in {'planned', 'approved'}:
                self.framework.queue(job_id)
                queued = True
            elif status == 'queued':
                # Start is idempotent for an already queued job. Never spawn a
                # second worker from a duplicate click/request. A genuinely
                # orphaned queued job is reconciled to ERROR by API startup and
                # can then use the governed retry lifecycle.
                meta = self.metadata.load(job_id)
                return self._pass(
                    command,
                    'StoryValidationJob is already queued; duplicate worker launch was suppressed.',
                    {
                        'job': self._project(record),
                        'worker': {
                            'pid': meta.get('worker_pid'),
                            'shell': False,
                            'argv_contract': 'fixed-gsdlc10b-worker',
                            'duplicate_launch_suppressed': True,
                        },
                    },
                )
            else:
                return self._block(command, 'GSDLC10B_JOB_STATE_BLOCK', f'StoryValidationJob cannot start from state {status}.')
            cmd = [sys.executable, '-m', 'devpilot_core.application.story_validation_job_worker', '--repo-root', str(self.root), '--job-id', job_id]
            env = os.environ.copy()
            source_root = self.root / 'src'
            if source_root.is_dir():
                existing = [item for item in str(env.get('PYTHONPATH') or '').split(os.pathsep) if item]
                source_text = str(source_root)
                env['PYTHONPATH'] = os.pathsep.join([source_text, *[item for item in existing if os.path.normcase(os.path.abspath(item)) != os.path.normcase(source_text)]])
            env['PYTHONUNBUFFERED'] = '1'
            proc = subprocess.Popen(
                cmd, cwd=str(self.root), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                shell=False, close_fds=(os.name != 'nt'),
            )
            meta = self.metadata.load(job_id)
            current_phase = str(meta.get('phase') or '').lower()
            meta.update({'worker_pid': proc.pid, 'worker_started_at': self.store.load(job_id).get('updated_at'), 'reconciled_orphan': False})
            if current_phase in {'', 'planned', 'approved', 'queued'}:
                meta.update({'phase': 'worker-starting', 'progress_percent': max(1, int(meta.get('progress_percent') or 0))})
            self.metadata.save(meta)
            self.operations.logs.append(job_id, level='INFO', phase='queue', message=f'GSDLC-10-B typed {record.get("story_validation_kind")} worker queued; shell=false; Full=false')

            # Bounded launch handshake: do not wait for the test itself, only ensure
            # that the child either advances the governed lifecycle or remains alive.
            # This closes the historical blind spot where an import/startup failure
            # could leave an apparently approved/queued job at 0% with no evidence.
            deadline = time.monotonic() + 1.0
            current = self.store.load(job_id)
            while time.monotonic() < deadline and str(current.get('status')) == 'queued':
                returncode = proc.poll()
                if returncode is not None:
                    current = self.framework.complete(
                        job_id, status='error',
                        error=f'Typed validation worker exited before lifecycle handoff (exit={returncode}).',
                    )
                    self.operations.logs.append(job_id, level='ERROR', phase='launcher', message=f'GSDLC-10-B worker launch failed before lifecycle handoff; exit={returncode}')
                    failed_meta = self.metadata.load(job_id)
                    failed_meta.update({'phase': 'launcher-error', 'progress_percent': int(failed_meta.get('progress_percent') or 1), 'worker_pid': proc.pid})
                    self.metadata.save(failed_meta)
                    return self._block(
                        command, 'GSDLC10B_WORKER_LAUNCH_BLOCK',
                        'Typed validation worker exited before taking lifecycle authority; inspect sanitized Job Console logs.',
                        metadata={'job_id': job_id, 'worker_exit_code': returncode, 'job_status': str(current.get('status'))},
                    )
                time.sleep(0.05)
                current = self.store.load(job_id)
            current = self.store.load(job_id)
            return self._pass(command, 'Typed StoryValidationJob launch accepted and lifecycle state is observable.', {'job': self._project(current), 'worker': {'pid': proc.pid, 'shell': False, 'argv_contract': 'fixed-gsdlc10b-worker', 'launch_handshake': True}})
        except Exception as exc:
            if queued:
                try:
                    current = self.store.load(job_id)
                    if str(current.get('status')) == 'queued':
                        self.framework.complete(job_id, status='error', error=f'Launcher error: {type(exc).__name__}')
                    self.operations.logs.append(job_id, level='ERROR', phase='launcher', message=f'GSDLC-10-B launcher error: {type(exc).__name__}')
                except Exception:
                    pass
            return self._block(command, 'GSDLC10B_JOB_START_BLOCK', f'{type(exc).__name__}: {exc}')

    def _approved_test_plan(self, command: str, test_plan_id: str, test_plan_hash: str) -> tuple[dict[str, Any] | None, CommandResult | None]:
        result = self.story_test_plan_loader(test_plan_id=test_plan_id)
        if not result.ok:
            return None, self._block(command, 'GSDLC10B_TEST_PLAN_DEPENDENCY_BLOCK', 'StoryTestPlan dependency could not be loaded.')
        plan = dict((result.data or {}).get('story_test_plan') or {})
        if str(plan.get('test_plan_hash') or '') != str(test_plan_hash or ''):
            return None, self._block(command, 'GSDLC10B_TEST_PLAN_HASH_BLOCK', 'StoryTestPlan hash is stale or mismatched.')
        if str(plan.get('status') or '') != 'APPROVED':
            return None, self._block(command, 'GSDLC10B_TEST_PLAN_STATUS_BLOCK', 'StoryValidationJobs require StoryTestPlan status APPROVED.')
        if bool((plan.get('full_regression_signal') or {}).get('execution_authorized')):
            return None, self._block(command, 'GSDLC10B_FULL_AUTHORITY_BLOCK', 'StoryTestPlan must not authorize Full Regression execution in GSDLC-10-B.')
        return plan, None


    def _execution_root(self, command: str, workspace_id: str) -> tuple[Path | None, str, CommandResult | None]:
        """Resolve the typed adapter cwd from server-side workspace authority.

        Browser payloads never provide a filesystem root. Production uses the same
        UiWorkspaceContext authority that binds StoryTestPlan/SourceChangePlan.
        Unit/self-validation without an external context remains platform-rooted.
        """
        if self.context_resolver is None:
            return self.root, 'platform-root', None
        try:
            context = self.context_resolver.resolve()
        except Exception as exc:
            return None, '', self._block(command, 'GSDLC10B_WORKSPACE_CONTEXT_BLOCK', f'Active workspace context could not be resolved: {type(exc).__name__}: {exc}')
        active_id = str(getattr(context, 'active_workspace_id', '') or '').strip()
        configured = bool(getattr(context, 'configured', False))
        valid = bool(getattr(context, 'valid', False))
        effective = getattr(context, 'effective_workspace_root', None)
        if not configured or not valid or not active_id or effective is None:
            return None, '', self._block(command, 'GSDLC10B_WORKSPACE_CONTEXT_BLOCK', 'Story validation requires a valid server-authoritative active project workspace.')
        if active_id != workspace_id:
            return None, '', self._block(command, 'GSDLC10B_WORKSPACE_ID_MISMATCH_BLOCK', f'StoryTestPlan workspace {workspace_id} does not match active workspace {active_id}.')
        root = Path(effective).resolve()
        if not root.is_dir():
            return None, '', self._block(command, 'GSDLC10B_EXECUTION_ROOT_MISSING_BLOCK', 'Active project workspace root does not exist.')
        return root, 'server-active-workspace', None

    def _context_for_record(self, command: str, record: dict[str, Any]) -> tuple[dict[str, Any] | None, CommandResult | None]:
        ref = str(record.get('runtime_context_ref') or '')
        if not ref or ref.startswith('/') or '..' in Path(ref).parts:
            return None, self._block(command, 'GSDLC10B_CONTEXT_REF_BLOCK', 'StoryValidationJob runtime context reference is invalid.')
        path = (self.root / ref).resolve()
        try:
            path.relative_to(self.root)
        except ValueError:
            return None, self._block(command, 'GSDLC10B_CONTEXT_ESCAPE_BLOCK', 'StoryValidationJob runtime context escaped repository root.')
        if not path.is_file():
            return None, self._block(command, 'GSDLC10B_CONTEXT_MISSING_BLOCK', 'StoryValidationJob immutable context is missing.')
        context = json.loads(path.read_text(encoding='utf-8'))
        expected = str(context.get('context_hash') or '')
        core = {k: v for k, v in context.items() if k != 'context_hash'}
        if expected != _sha(core):
            return None, self._block(command, 'GSDLC10B_CONTEXT_TAMPER_BLOCK', 'StoryValidationJob immutable context hash does not match.')
        if str(context.get('story_test_plan_hash')) != str(record.get('story_test_plan_hash')):
            return None, self._block(command, 'GSDLC10B_CONTEXT_PLAN_BINDING_BLOCK', 'Runtime context and governed job disagree on StoryTestPlan hash.')
        return context, None

    def _context_path(self, job_id: str) -> Path:
        return self.root / RUNTIME_ROOT / 'contexts' / f'{job_id}.json'

    def _load_profiles(self) -> list[dict[str, Any]]:
        payload = json.loads((self.root / PROFILE_REGISTRY).read_text(encoding='utf-8'))
        profiles = [dict(x) for x in payload.get('profiles', [])]
        if {str(x.get('job_kind')) for x in profiles} != {'test', 'build', 'lint'}:
            raise ValueError('GSDLC-10-B profile registry must declare exactly test/build/lint kinds.')
        return profiles

    @staticmethod
    def _applies(profile: dict[str, Any], changed_paths: list[str]) -> bool:
        trigger = dict(profile.get('trigger') or {})
        mode = str(trigger.get('mode') or '')
        if mode == 'always':
            return True
        if mode == 'path-prefix':
            prefixes = tuple(str(x) for x in trigger.get('prefixes', []))
            return any(path.startswith(prefixes) for path in changed_paths) if prefixes else False
        if mode == 'path-suffix':
            suffixes = tuple(str(x) for x in trigger.get('suffixes', []))
            return any(path.endswith(suffixes) for path in changed_paths) if suffixes else False
        return False

    @staticmethod
    def _safe_test_target(value: str) -> bool:
        text = str(value).replace('\\', '/')
        if not text.startswith('tests/') or not text.endswith('.py') and '.py::' not in text:
            return False
        if any(token in text for token in ('..', '\n', '\r', '\x00', ';', '|', '&', '$(', '`')):
            return False
        return True

    def _project(self, record: dict[str, Any]) -> dict[str, Any]:
        item = self.operations._snapshot(record)
        status = str(item.get('status') or '')
        timed_out = bool((item.get('result_summary') or {}).get('timed_out'))
        item['story_validation_status'] = 'TIMED_OUT' if timed_out else {'planned': 'PLANNED', 'approved': 'APPROVED', 'queued': 'QUEUED', 'running': 'RUNNING', 'pass': 'PASS', 'block': 'FAIL', 'error': 'ERROR', 'cancel-requested': 'CANCEL_REQUESTED', 'cancelled': 'CANCELLED'}.get(status, status.upper())
        return item

    @staticmethod
    def _pass(command: str, message: str, data: dict[str, Any]) -> CommandResult:
        return CommandResult(command, True, ExitCode.PASS, message, data={**data, 'network_used': False, 'external_api_used': False, 'full_regression_started': False}, findings=[Finding('GSDLC10B_PASS', message, Severity.INFO)])

    @staticmethod
    def _block(command: str, code: str, message: str) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={'network_used': False, 'external_api_used': False, 'full_regression_started': False}, findings=[Finding(code, message, Severity.BLOCK)])
