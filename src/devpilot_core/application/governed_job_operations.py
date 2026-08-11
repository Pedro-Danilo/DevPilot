from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

from .governed_jobs import GovernedJobConflict, GovernedJobFramework, GovernedJobPolicyBlock, GovernedJobStore

_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"\bct_[A-Za-z0-9_\-]{12,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-]+", re.I),
]
ACTIVE_STATUSES = {"queued", "running", "cancel-requested", "rollback-running"}
TERMINAL_STATUSES = {"pass", "pass-with-gaps", "block", "error", "cancelled", "rolled-back", "expired"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_ts(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def sanitize_job_log_message(message: str) -> str:
    value = str(message).replace("\x00", "")[:8192]
    for pattern in _SECRET_PATTERNS:
        value = pattern.sub("<redacted>", value)
    return value


class GovernedJobLogStore:
    """Bounded append-only local log stream for one governed job."""

    def __init__(self, root: Path, *, max_bytes_per_job: int = 524_288) -> None:
        self.root = Path(root).resolve()
        self.logs_root = self.root / "outputs/runtime/governed_jobs/logs"
        self.max_bytes_per_job = int(max_bytes_per_job)

    def _path(self, job_id: str) -> Path:
        if not re.fullmatch(r"job_[a-f0-9]{32}", str(job_id)):
            raise KeyError("Invalid governed job id.")
        return self.logs_root / f"{job_id}.jsonl"

    def append(self, job_id: str, *, level: str, message: str, phase: str = "runtime") -> int:
        path = self._path(job_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": _utc_now(),
            "level": str(level).upper()[:16],
            "phase": str(phase)[:80],
            "message": sanitize_job_log_message(message),
        }
        raw = (json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        current = path.stat().st_size if path.exists() else 0
        if current + len(raw) > self.max_bytes_per_job:
            marker = (json.dumps({
                "timestamp": _utc_now(), "level": "WARN", "phase": "log-limit",
                "message": "Job log size limit reached; additional log entries were suppressed.",
            }, sort_keys=True) + "\n").encode("utf-8")
            if current < self.max_bytes_per_job:
                with path.open("ab") as handle:
                    handle.write(marker[: max(0, self.max_bytes_per_job - current)])
            return current
        with path.open("ab") as handle:
            handle.write(raw)
        return current + len(raw)

    def read(self, job_id: str, *, cursor: int = 0, limit: int = 100) -> dict[str, Any]:
        path = self._path(job_id)
        if not path.exists():
            return {"entries": [], "cursor": 0, "next_cursor": 0, "truncated": False}
        raw = path.read_bytes()
        start = max(0, min(int(cursor), len(raw)))
        entries: list[dict[str, Any]] = []
        consumed = start
        for line in raw[start:].splitlines(keepends=True):
            if len(entries) >= max(1, min(int(limit), 500)):
                break
            consumed += len(line)
            try:
                payload = json.loads(line.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                payload = {"timestamp": _utc_now(), "level": "WARN", "phase": "decode", "message": "Sanitized log entry could not be decoded."}
            entries.append(payload)
        return {"entries": entries, "cursor": start, "next_cursor": consumed, "truncated": consumed < len(raw)}


class GovernedJobOperationalMetadataStore:
    """Separate UOC-008 operational metadata so the frozen UOC-007 job schema remains immutable."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.meta_root = self.root / "outputs/runtime/governed_jobs/operational"

    def _path(self, job_id: str) -> Path:
        if not re.fullmatch(r"job_[a-f0-9]{32}", str(job_id)):
            raise KeyError("Invalid governed job id.")
        return self.meta_root / f"{job_id}.json"

    def load(self, job_id: str) -> dict[str, Any]:
        path = self._path(job_id)
        if not path.exists():
            return {
                "schema_id": "devpilot.uoc008.job_operational_metadata.v1",
                "job_id": job_id,
                "phase": "planned",
                "progress_percent": 0,
                "worker_pid": None,
                "worker_started_at": None,
                "retry_of_job_id": None,
                "retry_job_ids": [],
                "reconciled_orphan": False,
                "updated_at": _utc_now(),
            }
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, payload: dict[str, Any]) -> None:
        path = self._path(str(payload["job_id"]))
        path.parent.mkdir(parents=True, exist_ok=True)
        data = dict(payload)
        data["updated_at"] = _utc_now()
        fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(data, handle, indent=2, sort_keys=True, ensure_ascii=False)
                handle.write("\n")
                handle.flush(); os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)


class GovernedJobRuntimeLock:
    """Cross-process lock for UOC-008 operational mutations using atomic mkdir."""

    def __init__(self, root: Path, *, stale_seconds: int = 60) -> None:
        self.lock_path = Path(root).resolve() / "outputs/runtime/governed_jobs/.uoc008-operation.lock"
        self.stale_seconds = max(15, int(stale_seconds))

    @contextmanager
    def hold(self, *, timeout_seconds: float = 3.0):
        deadline = time.monotonic() + max(0.1, float(timeout_seconds))
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                self.lock_path.mkdir()
                (self.lock_path / "owner.json").write_text(json.dumps({"pid": os.getpid(), "acquired_at": _utc_now()}, sort_keys=True), encoding="utf-8")
                break
            except FileExistsError:
                try:
                    age = time.time() - self.lock_path.stat().st_mtime
                    if age > self.stale_seconds:
                        for child in self.lock_path.iterdir():
                            child.unlink(missing_ok=True)
                        self.lock_path.rmdir()
                        continue
                except OSError:
                    pass
                if time.monotonic() >= deadline:
                    raise GovernedJobConflict("Governed-job operational lock is busy.")
                time.sleep(0.05)
        try:
            yield
        finally:
            try:
                for child in self.lock_path.iterdir():
                    child.unlink(missing_ok=True)
                self.lock_path.rmdir()
            except OSError:
                pass


class ControlledProcessTree:
    """Terminate one recorded worker tree using fixed argv; never accepts shell text."""

    @staticmethod
    def terminate(pid: int, *, timeout_seconds: int = 10) -> dict[str, Any]:
        pid = int(pid)
        if pid <= 1 or pid == os.getpid():
            raise GovernedJobPolicyBlock("Refusing unsafe process-tree termination target.")
        if os.name == "nt":
            completed = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], shell=False, capture_output=True, text=True, timeout=timeout_seconds, check=False)
            return {"pid": pid, "exit_code": completed.returncode, "terminated": completed.returncode == 0, "platform": "windows"}
        try:
            os.killpg(os.getpgid(pid), 15)
            return {"pid": pid, "exit_code": 0, "terminated": True, "platform": "posix"}
        except (ProcessLookupError, PermissionError) as exc:
            return {"pid": pid, "exit_code": 1, "terminated": False, "platform": "posix", "error": type(exc).__name__}


class GovernedJobOperationsApplicationService:
    """UOC-008 operator boundary for list/detail/log/cancel/retry/reconciliation."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.store = GovernedJobStore(self.root)
        self.framework = GovernedJobFramework(self.root, store=self.store)
        self.logs = GovernedJobLogStore(self.root)
        self.metadata = GovernedJobOperationalMetadataStore(self.root)
        self.runtime_lock = GovernedJobRuntimeLock(self.root)

    def list_jobs(self, *, workspace_id: str | None = None, capability_id: str | None = None, status: str | None = None, limit: int = 50, offset: int = 0) -> CommandResult:
        jobs = [self._snapshot(item) for item in self.store.list()]
        if workspace_id: jobs = [item for item in jobs if item["workspace_id"] == workspace_id]
        if capability_id: jobs = [item for item in jobs if item["capability_id"] == capability_id]
        if status: jobs = [item for item in jobs if item["status"] == status]
        jobs.sort(key=lambda item: (str(item.get("updated_at", "")), str(item["job_id"])), reverse=True)
        total = len(jobs); offset = max(0, int(offset)); limit = max(1, min(int(limit), 200))
        return self._pass("jobs list", "Governed jobs listed.", {"jobs": jobs[offset:offset+limit], "total": total, "limit": limit, "offset": offset})

    def inspect(self, *, job_id: str) -> CommandResult:
        try: record = self.store.load(job_id)
        except KeyError:
            return self._block("jobs inspect", "Governed job was not found.", "GOVERNED_JOB_NOT_FOUND")
        return self._pass("jobs inspect", "Governed job inspected.", {"job": self._snapshot(record)})

    def read_logs(self, *, job_id: str, cursor: int = 0, limit: int = 100) -> CommandResult:
        try: self.store.load(job_id)
        except KeyError: return self._block("jobs logs", "Governed job was not found.", "GOVERNED_JOB_NOT_FOUND")
        return self._pass("jobs logs", "Sanitized governed-job logs read.", {"job_id": job_id, **self.logs.read(job_id, cursor=cursor, limit=limit)})

    def request_cancel(self, *, job_id: str, actor: str, reason: str) -> CommandResult:
        try: record = self.store.load(job_id)
        except KeyError: return self._block("jobs cancel", "Governed job was not found.", "GOVERNED_JOB_NOT_FOUND")
        if not record.get("supports_cancel"):
            return self._block("jobs cancel", "Capability does not support cancellation.", "GOVERNED_JOB_CANCEL_UNSUPPORTED")
        if record["status"] not in {"queued", "running"}:
            return self._block("jobs cancel", f"Cancellation is not valid from state {record['status']}.", "GOVERNED_JOB_CANCEL_STATE_BLOCK")
        try:
            with self.runtime_lock.hold():
                updated = self.framework._transition_record(record, "cancel-requested")
                meta = self.metadata.load(job_id); pid = meta.get("worker_pid"); process_result = None
                if isinstance(pid, int) and pid > 1:
                    process_result = ControlledProcessTree.terminate(pid)
                    if process_result.get("terminated"):
                        updated = self.framework.mark_cancelled(job_id)
                self.logs.append(job_id, level="WARN", phase="cancel", message=f"Cancellation requested by {actor}: {reason}")
        except GovernedJobConflict as exc:
            return self._block("jobs cancel", str(exc), "GOVERNED_JOB_CANCEL_TRANSITION_BLOCK")
        return self._pass("jobs cancel", "Cancellation request recorded.", {"job": self._snapshot(updated), "process_tree": process_result})

    def retry(self, *, job_id: str, actor: str, reason: str) -> CommandResult:
        try: record = self.store.load(job_id)
        except KeyError: return self._block("jobs retry", "Governed job was not found.", "GOVERNED_JOB_NOT_FOUND")
        if record["status"] not in TERMINAL_STATUSES:
            return self._block("jobs retry", "Only terminal jobs may be retried.", "GOVERNED_JOB_RETRY_STATE_BLOCK")
        if int(record.get("retry_count", 0)) >= int(record.get("retry_limit", 0)):
            return self._block("jobs retry", "Retry budget is exhausted.", "GOVERNED_JOB_RETRY_BUDGET_BLOCK")
        with self.runtime_lock.hold():
            retry_record = dict(record)
            retry_record["job_id"] = f"job_{os.urandom(16).hex()}"
            retry_record["status"] = "approved" if record.get("approval_binding_id") else "planned"
            retry_record["retry_count"] = int(record.get("retry_count", 0)) + 1
            retry_record["heartbeat_sequence"] = 0
            retry_record["last_heartbeat_at"] = None
            retry_record["created_at"] = _utc_now(); retry_record["updated_at"] = retry_record["created_at"]
            retry_record["errors"] = []; retry_record["result_summary"] = {}
            # Retry is a new job and intentionally receives a fresh opaque idempotency hash.
            retry_record["idempotency_key_hash"] = os.urandom(32).hex()
            self.store.save(retry_record)
            meta = self.metadata.load(retry_record["job_id"]); meta["retry_of_job_id"] = job_id; self.metadata.save(meta)
            origin_meta = self.metadata.load(job_id); origin_meta["retry_job_ids"] = sorted(set(origin_meta.get("retry_job_ids", []) + [retry_record["job_id"]])); self.metadata.save(origin_meta)
            self.logs.append(retry_record["job_id"], level="INFO", phase="retry", message=f"Governed retry created by {actor}: {reason}")
        return self._pass("jobs retry", "Governed retry job created without automatic execution.", {"job": self._snapshot(retry_record), "retry_of_job_id": job_id})

    def record_progress(self, *, job_id: str, phase: str, progress_percent: int, worker_pid: int | None = None, message: str | None = None) -> CommandResult:
        """Record trusted worker progress/heartbeat without exposing a browser mutation route."""
        try:
            record = self.store.load(job_id)
        except KeyError:
            return self._block("jobs progress", "Governed job was not found.", "GOVERNED_JOB_NOT_FOUND")
        if record.get("status") not in {"running", "cancel-requested", "rollback-running"}:
            return self._block("jobs progress", f"Progress heartbeat is invalid from state {record.get('status')}.", "GOVERNED_JOB_PROGRESS_STATE_BLOCK")
        pct = max(0, min(int(progress_percent), 100))
        with self.runtime_lock.hold():
            updated = self.framework.heartbeat(job_id)
            meta = self.metadata.load(job_id)
            meta["phase"] = str(phase)[:80] or str(record.get("status"))
            meta["progress_percent"] = pct
            if worker_pid is not None:
                pid = int(worker_pid)
                if pid <= 1:
                    return self._block("jobs progress", "Unsafe worker PID was rejected.", "GOVERNED_JOB_WORKER_PID_BLOCK")
                meta["worker_pid"] = pid
                meta["worker_started_at"] = meta.get("worker_started_at") or _utc_now()
            self.metadata.save(meta)
            if message:
                self.logs.append(job_id, level="INFO", phase=meta["phase"], message=message)
        return self._pass("jobs progress", "Governed-job progress heartbeat recorded.", {"job": self._snapshot(updated)})

    def reconcile_orphans(self, *, stale_after_seconds: int = 120) -> CommandResult:
        reconciled: list[str] = []
        now = time.time()
        for record in self.store.list():
            if record.get("status") not in ACTIVE_STATUSES: continue
            heartbeat = _parse_ts(record.get("last_heartbeat_at")) or _parse_ts(record.get("updated_at")) or now
            if now - heartbeat < max(30, int(stale_after_seconds)): continue
            job_id = str(record["job_id"])
            try:
                with self.runtime_lock.hold():
                    target = "cancelled" if record.get("status") == "cancel-requested" else "error"
                    updated = self.framework._transition_record(record, target)
                if target == "error":
                    updated.setdefault("errors", []).append("UOC-008 orphan reconciliation: no fresh worker heartbeat after restart.")
                    self.store.save(updated)
                meta = self.metadata.load(job_id); meta["reconciled_orphan"] = True; meta["phase"] = "reconciled"; self.metadata.save(meta)
                self.logs.append(job_id, level="WARN", phase="reconcile", message="Orphan/stale job reconciled after runtime restart.")
                reconciled.append(job_id)
            except GovernedJobConflict:
                continue
        return self._pass("jobs reconcile", "Governed-job orphan reconciliation completed.", {"reconciled_job_ids": reconciled, "reconciled_total": len(reconciled)})

    def _snapshot(self, record: dict[str, Any]) -> dict[str, Any]:
        item = dict(record); meta = self.metadata.load(str(record["job_id"])); now = time.time()
        created = _parse_ts(record.get("created_at")); updated = _parse_ts(record.get("updated_at")); heartbeat = _parse_ts(record.get("last_heartbeat_at"))
        item["operational"] = {
            "phase": meta.get("phase", record.get("status")), "progress_percent": int(meta.get("progress_percent", 0)),
            "duration_seconds": max(0, int((updated or now) - (created or updated or now))),
            "heartbeat_age_seconds": None if heartbeat is None else max(0, int(now - heartbeat)),
            "stale": bool(record.get("status") in ACTIVE_STATUSES and heartbeat is not None and now - heartbeat > max(30, int(record.get("heartbeat_interval_seconds", 10)) * 3)),
            "worker_pid_present": isinstance(meta.get("worker_pid"), int), "retry_of_job_id": meta.get("retry_of_job_id"),
            "retry_job_ids": list(meta.get("retry_job_ids", [])), "reconciled_orphan": bool(meta.get("reconciled_orphan")),
        }
        # Raw hashes are internal integrity fields and are not needed by the browser console.
        item.pop("cancel_token_hash", None); item.pop("idempotency_key_hash", None); item.pop("request_fingerprint", None)
        return item

    @staticmethod
    def _pass(command: str, message: str, data: dict[str, Any]) -> CommandResult:
        return CommandResult(command=command, ok=True, exit_code=ExitCode.PASS, message=message, data=data)

    @staticmethod
    def _block(command: str, message: str, finding_id: str) -> CommandResult:
        return CommandResult(command=command, ok=False, exit_code=ExitCode.BLOCK, message=message, findings=[Finding(finding_id, message, Severity.BLOCK)])
