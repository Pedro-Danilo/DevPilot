from __future__ import annotations

import hashlib
import json
import os
import secrets
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .governed_job_capability_registry import GovernedJobCapabilityContract, GovernedJobCapabilityRegistry


JOB_SCHEMA_ID = 'SCHEMA-DEVPL-UI-GOVERNED-JOB-V2'
JOB_SCHEMA_VERSION = '2.0'
TERMINAL_STATUSES = {'cancelled', 'rolled-back', 'expired'}
COMPLETION_STATUSES = {'pass', 'pass-with-gaps', 'block', 'error'}
ALLOWED_STATUSES = {
    'planned', 'pending-approval', 'approved', 'queued', 'running', 'pass',
    'pass-with-gaps', 'block', 'error', 'cancel-requested', 'cancelled',
    'rollback-running', 'rolled-back', 'expired',
}
TRANSITIONS = {
    'planned': {'pending-approval', 'approved', 'queued', 'block', 'error', 'expired'},
    'pending-approval': {'approved', 'block', 'error', 'expired'},
    'approved': {'queued', 'block', 'error', 'expired'},
    'queued': {'running', 'cancel-requested', 'block', 'error', 'expired'},
    'running': {'pass', 'pass-with-gaps', 'block', 'error', 'cancel-requested', 'rollback-running'},
    'pass': {'rollback-running'},
    'pass-with-gaps': {'rollback-running'},
    'block': {'rollback-running'},
    'error': {'rollback-running'},
    'cancel-requested': {'cancelled', 'error'},
    'rollback-running': {'rolled-back', 'error'},
    'cancelled': set(),
    'rolled-back': set(),
    'expired': set(),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _secret_hash(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


class GovernedJobError(RuntimeError):
    pass


class GovernedJobConflict(GovernedJobError):
    pass


class GovernedJobPolicyBlock(GovernedJobError):
    pass


@dataclass(frozen=True)
class GovernedJobHandle:
    record: dict[str, Any]
    cancel_token: str | None
    idempotent_replay: bool = False


class GovernedJobStore:
    """Atomic local JSON store for UOC-007 job state.

    UOC-007 intentionally supports one local process as the authoritative writer.
    Multi-process locking, orphan reconciliation and streaming logs are deferred to
    UOC-008; the file format and atomic replace behavior are designed for that
    evolution.
    """

    def __init__(self, root: Path, runtime_root: Path | str = 'outputs/runtime/governed_jobs') -> None:
        self.root = Path(root).resolve()
        runtime = Path(runtime_root)
        self.runtime_root = runtime if runtime.is_absolute() else self.root / runtime
        self.jobs_root = self.runtime_root / 'jobs'
        self.idempotency_path = self.runtime_root / 'idempotency_index.json'

    def _ensure(self) -> None:
        self.jobs_root.mkdir(parents=True, exist_ok=True)

    def _atomic_write_json(self, path: Path, payload: dict[str, Any]) -> None:
        self._ensure()
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=str(path.parent))
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False, sort_keys=True)
                handle.write('\n')
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, path)
        finally:
            if tmp.exists():
                tmp.unlink(missing_ok=True)

    def save(self, record: dict[str, Any]) -> None:
        job_id = str(record['job_id'])
        self._atomic_write_json(self.jobs_root / f'{job_id}.json', record)

    def load(self, job_id: str) -> dict[str, Any]:
        path = self.jobs_root / f'{job_id}.json'
        if not path.exists():
            raise KeyError(f'Unknown governed job: {job_id}')
        return json.loads(path.read_text(encoding='utf-8'))

    def list(self) -> list[dict[str, Any]]:
        if not self.jobs_root.exists():
            return []
        return [json.loads(path.read_text(encoding='utf-8')) for path in sorted(self.jobs_root.glob('job_*.json'))]

    def _idempotency_index(self) -> dict[str, str]:
        if not self.idempotency_path.exists():
            return {}
        payload = json.loads(self.idempotency_path.read_text(encoding='utf-8'))
        return {str(k): str(v) for k, v in payload.get('keys', {}).items()}

    def lookup_idempotency(self, idempotency_key_hash: str) -> str | None:
        return self._idempotency_index().get(idempotency_key_hash)

    def bind_idempotency(self, idempotency_key_hash: str, job_id: str) -> None:
        index = self._idempotency_index()
        current = index.get(idempotency_key_hash)
        if current and current != job_id:
            raise GovernedJobConflict('Idempotency key is already bound to another job.')
        index[idempotency_key_hash] = job_id
        self._atomic_write_json(
            self.idempotency_path,
            {'schema_id': 'devpilot.uoc007.governed_job_idempotency_index.v1', 'keys': dict(sorted(index.items()))},
        )


class GovernedJobFramework:
    """Typed, no-shell governed job lifecycle for UOC-007.

    The framework creates and persists job state but does not discover commands,
    construct shell text or bypass policy/approval. Runtime execution requires an
    explicitly bound typed adapter in the capability registry and an executor
    callable supplied by trusted application code.
    """

    def __init__(
        self,
        root: Path,
        *,
        registry: GovernedJobCapabilityRegistry | None = None,
        store: GovernedJobStore | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.registry = registry or GovernedJobCapabilityRegistry(self.root)
        self.store = store or GovernedJobStore(self.root)

    def plan(
        self,
        *,
        capability_id: str,
        workspace_id: str,
        parameters: dict[str, Any] | None,
        idempotency_key: str,
        dry_run: bool = True,
        correlation_id: str | None = None,
        timeout_seconds: int | None = None,
        retry_limit: int | None = None,
        approval_binding_id: str | None = None,
        artifact_refs: list[str] | None = None,
        evidence_refs: list[str] | None = None,
    ) -> GovernedJobHandle:
        contract = self.registry.require(capability_id)
        if contract.risk_class == 'forbidden' or not contract.planning_enabled:
            raise GovernedJobPolicyBlock(f'Capability is not eligible for governed-job planning: {capability_id}')
        if not idempotency_key or len(idempotency_key) > 256:
            raise ValueError('idempotency_key must contain 1..256 characters')
        if not workspace_id or len(workspace_id) > 256:
            raise ValueError('workspace_id must contain 1..256 characters')
        parameters = dict(parameters or {})
        effective_timeout = int(timeout_seconds or contract.budgets['timeout_seconds'])
        effective_retry = int(retry_limit if retry_limit is not None else contract.budgets['retry_limit'])
        if effective_timeout < 1 or effective_timeout > int(contract.budgets['timeout_seconds']):
            raise GovernedJobPolicyBlock('Requested timeout exceeds the registered capability budget.')
        if effective_retry < 0 or effective_retry > int(contract.budgets['retry_limit']):
            raise GovernedJobPolicyBlock('Requested retry limit exceeds the registered capability budget.')
        if contract.controls.get('dry_run_required') and not dry_run and not approval_binding_id:
            raise GovernedJobPolicyBlock('Non-dry-run planning requires an approval binding for this capability.')
        if contract.risk_class == 'sensitive' and not dry_run and not approval_binding_id:
            raise GovernedJobPolicyBlock('Sensitive capability requires approval for non-dry-run planning.')

        request_fingerprint = _canonical_hash({
            'capability_id': capability_id,
            'workspace_id': workspace_id,
            'parameters': parameters,
            'dry_run': bool(dry_run),
        })
        idempotency_key_hash = _secret_hash(idempotency_key)
        existing_id = self.store.lookup_idempotency(idempotency_key_hash)
        if existing_id:
            existing = self.store.load(existing_id)
            if existing.get('request_fingerprint') != request_fingerprint:
                raise GovernedJobConflict('Idempotency key was reused with a different governed-job request.')
            return GovernedJobHandle(record=existing, cancel_token=None, idempotent_replay=True)

        now = _utc_now()
        job_id = f'job_{uuid.uuid4().hex}'
        correlation = correlation_id or f'corr_{uuid.uuid4().hex}'
        if not str(correlation).startswith('corr_'):
            raise ValueError('correlation_id must start with corr_')
        cancel_token = f'ct_{secrets.token_urlsafe(32)}' if contract.supports_cancel else None
        status = 'pending-approval' if contract.requires_approval and not approval_binding_id else 'planned'
        if contract.requires_approval and approval_binding_id:
            status = 'approved'
        record = {
            'schema_version': JOB_SCHEMA_VERSION,
            'schema_id': JOB_SCHEMA_ID,
            'job_id': job_id,
            'capability_id': capability_id,
            'workspace_id': workspace_id,
            'status': status,
            'risk_class': contract.risk_class,
            'dry_run': bool(dry_run),
            'timeout_seconds': effective_timeout,
            'retry_limit': effective_retry,
            'retry_count': 0,
            'heartbeat_interval_seconds': int(contract.budgets['heartbeat_interval_seconds']),
            'heartbeat_sequence': 0,
            'created_at': now,
            'updated_at': now,
            'last_heartbeat_at': None,
            'approval_binding_id': approval_binding_id,
            'supports_cancel': contract.supports_cancel,
            'supports_rollback': contract.supports_rollback,
            'cancel_token_hash': _secret_hash(cancel_token) if cancel_token else None,
            'idempotency_key_hash': idempotency_key_hash,
            'correlation_id': correlation,
            'request_fingerprint': request_fingerprint,
            'parameter_keys': sorted(str(key) for key in parameters.keys()),
            'artifact_refs': sorted(set(artifact_refs or [])),
            'evidence_refs': sorted(set(evidence_refs or [])),
            'runtime_adapter_id': contract.runtime.get('adapter_id'),
            'errors': [],
            'result_summary': {},
        }
        self.store.save(record)
        self.store.bind_idempotency(idempotency_key_hash, job_id)
        return GovernedJobHandle(record=record, cancel_token=cancel_token)

    def approve(self, job_id: str, *, approval_binding_id: str) -> dict[str, Any]:
        if not approval_binding_id:
            raise ValueError('approval_binding_id is required')
        record = self.store.load(job_id)
        record['approval_binding_id'] = approval_binding_id
        return self._transition_record(record, 'approved')

    def queue(self, job_id: str) -> dict[str, Any]:
        record = self.store.load(job_id)
        contract = self.registry.require(str(record['capability_id']))
        if contract.requires_approval and not record.get('approval_binding_id'):
            raise GovernedJobPolicyBlock('Approval-bound capability cannot be queued without approval.')
        return self._transition_record(record, 'queued')

    def start(self, job_id: str) -> dict[str, Any]:
        record = self.store.load(job_id)
        contract = self.registry.require(str(record['capability_id']))
        if not contract.execution_enabled or not contract.adapter_bound:
            raise GovernedJobPolicyBlock('Runtime adapter is not enabled/bound for this capability.')
        return self._transition_record(record, 'running', heartbeat=True)

    def heartbeat(self, job_id: str, *, artifact_refs: list[str] | None = None, evidence_refs: list[str] | None = None) -> dict[str, Any]:
        record = self.store.load(job_id)
        if record['status'] not in {'running', 'cancel-requested', 'rollback-running'}:
            raise GovernedJobConflict(f'Heartbeat is invalid from state {record["status"]}.')
        record['heartbeat_sequence'] = int(record.get('heartbeat_sequence', 0)) + 1
        record['last_heartbeat_at'] = _utc_now()
        record['updated_at'] = record['last_heartbeat_at']
        record['artifact_refs'] = sorted(set(record.get('artifact_refs', []) + list(artifact_refs or [])))
        record['evidence_refs'] = sorted(set(record.get('evidence_refs', []) + list(evidence_refs or [])))
        self.store.save(record)
        return record

    def request_cancel(self, job_id: str, *, cancel_token: str) -> dict[str, Any]:
        record = self.store.load(job_id)
        if not record.get('supports_cancel'):
            raise GovernedJobPolicyBlock('Capability does not support cancellation.')
        expected = record.get('cancel_token_hash')
        if not expected or not secrets.compare_digest(str(expected), _secret_hash(cancel_token)):
            raise GovernedJobPolicyBlock('Cancel token is invalid.')
        return self._transition_record(record, 'cancel-requested')

    def mark_cancelled(self, job_id: str) -> dict[str, Any]:
        return self._transition(job_id, 'cancelled')

    def complete(
        self,
        job_id: str,
        *,
        status: str,
        result_summary: dict[str, Any] | None = None,
        artifact_refs: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        if status not in COMPLETION_STATUSES:
            raise ValueError(f'Unsupported completion status: {status}')
        record = self.store.load(job_id)
        record['result_summary'] = dict(result_summary or {})
        record['artifact_refs'] = sorted(set(record.get('artifact_refs', []) + list(artifact_refs or [])))
        record['evidence_refs'] = sorted(set(record.get('evidence_refs', []) + list(evidence_refs or [])))
        if error:
            record.setdefault('errors', []).append(str(error))
        return self._transition_record(record, status)

    def begin_rollback(self, job_id: str) -> dict[str, Any]:
        record = self.store.load(job_id)
        if not record.get('supports_rollback'):
            raise GovernedJobPolicyBlock('Capability does not support rollback.')
        return self._transition_record(record, 'rollback-running', heartbeat=True)

    def mark_rolled_back(self, job_id: str, *, evidence_refs: list[str] | None = None) -> dict[str, Any]:
        record = self.store.load(job_id)
        record['evidence_refs'] = sorted(set(record.get('evidence_refs', []) + list(evidence_refs or [])))
        return self._transition_record(record, 'rolled-back')

    def expire(self, job_id: str) -> dict[str, Any]:
        return self._transition(job_id, 'expired')

    def execute_with(
        self,
        job_id: str,
        *,
        parameters: dict[str, Any],
        executor: Callable[[dict[str, Any]], Any],
    ) -> dict[str, Any]:
        """Execute through a trusted typed callable; arbitrary shell text is never accepted."""
        record = self.store.load(job_id)
        contract = self.registry.require(str(record['capability_id']))
        if not contract.execution_enabled or not contract.adapter_bound:
            raise GovernedJobPolicyBlock('Capability has no enabled typed runtime adapter.')
        fingerprint = _canonical_hash({
            'capability_id': record['capability_id'],
            'workspace_id': record['workspace_id'],
            'parameters': dict(parameters),
            'dry_run': bool(record['dry_run']),
        })
        if not secrets.compare_digest(str(record['request_fingerprint']), fingerprint):
            raise GovernedJobConflict('Execution parameters do not match the immutable planned request.')
        if record['status'] == 'planned':
            record = self.queue(job_id)
        record = self.start(job_id)
        try:
            result = executor(dict(parameters))
        except Exception as exc:  # noqa: BLE001 - converted to governed error state
            return self.complete(job_id, status='error', error=f'{type(exc).__name__}: {exc}')
        if hasattr(result, 'to_dict'):
            payload = result.to_dict()
        elif isinstance(result, dict):
            payload = dict(result)
        else:
            payload = {'value': result}
        ok = bool(payload.get('ok', True))
        exit_code = int(payload.get('exit_code', 0 if ok else 1))
        status = 'pass' if ok and exit_code == 0 else ('block' if exit_code == 2 else 'error' if exit_code == 3 else 'block')
        return self.complete(job_id, status=status, result_summary=payload)

    def _transition(self, job_id: str, target: str) -> dict[str, Any]:
        return self._transition_record(self.store.load(job_id), target)

    def _transition_record(self, record: dict[str, Any], target: str, *, heartbeat: bool = False) -> dict[str, Any]:
        current = str(record['status'])
        if target not in ALLOWED_STATUSES:
            raise ValueError(f'Unknown governed job state: {target}')
        if target == current:
            return record
        if target not in TRANSITIONS.get(current, set()):
            raise GovernedJobConflict(f'Invalid governed job transition: {current} -> {target}')
        record['status'] = target
        now = _utc_now()
        record['updated_at'] = now
        if heartbeat:
            record['heartbeat_sequence'] = int(record.get('heartbeat_sequence', 0)) + 1
            record['last_heartbeat_at'] = now
        self.store.save(record)
        return record
