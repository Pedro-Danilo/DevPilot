from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core.application.governed_job_operations import GovernedJobLogStore, GovernedJobOperationsApplicationService
from devpilot_core.application.governed_jobs import GovernedJobStore

REPO = Path(__file__).resolve().parents[1]


def _root(tmp_path: Path) -> Path:
    target = tmp_path / "repo"
    (target / ".devpilot/interfaces").mkdir(parents=True)
    shutil.copy2(REPO / ".devpilot/interfaces/governed_job_capability_registry.json", target / ".devpilot/interfaces/governed_job_capability_registry.json")
    return target


def _job(root: Path, *, status: str = "running", retry_count: int = 0, retry_limit: int = 1) -> dict:
    record = {
        "schema_version": "2.0", "schema_id": "SCHEMA-DEVPL-UI-GOVERNED-JOB-V2", "job_id": "job_" + "a" * 32,
        "capability_id": "cli.workspace.status", "workspace_id": "ws", "status": status, "risk_class": "read-only",
        "dry_run": True, "timeout_seconds": 60, "retry_limit": retry_limit, "retry_count": retry_count,
        "heartbeat_interval_seconds": 5, "heartbeat_sequence": 1, "created_at": "2026-08-11T00:00:00Z", "updated_at": "2026-08-11T00:00:00Z",
        "last_heartbeat_at": "2026-08-11T00:00:00Z", "approval_binding_id": None, "supports_cancel": True, "supports_rollback": False,
        "cancel_token_hash": "1" * 64, "idempotency_key_hash": "2" * 64, "correlation_id": "corr_test", "request_fingerprint": "3" * 64,
        "parameter_keys": [], "artifact_refs": [], "evidence_refs": [], "runtime_adapter_id": None, "errors": [], "result_summary": {},
    }
    GovernedJobStore(root).save(record)
    return record


def test_uoc008_list_detail_hide_internal_hashes_and_report_stale(tmp_path: Path) -> None:
    root = _root(tmp_path); _job(root)
    service = GovernedJobOperationsApplicationService(root)
    listed = service.list_jobs()
    assert listed.ok
    job = listed.data["jobs"][0]
    assert "cancel_token_hash" not in job and "idempotency_key_hash" not in job and "request_fingerprint" not in job
    assert job["operational"]["stale"] is True
    assert service.inspect(job_id=job["job_id"]).ok


def test_uoc008_log_redaction_and_bounded_page(tmp_path: Path) -> None:
    root = _root(tmp_path); record = _job(root, status="planned")
    logs = GovernedJobLogStore(root, max_bytes_per_job=4096)
    logs.append(record["job_id"], level="INFO", phase="test", message="token=supersecret Bearer abc.def ct_abcdefghijklmnop")
    page = logs.read(record["job_id"], cursor=0, limit=10)
    assert len(page["entries"]) == 1
    message = page["entries"][0]["message"]
    assert "supersecret" not in message and "abc.def" not in message and "ct_abcdefghijklmnop" not in message
    assert "<redacted>" in message


def test_uoc008_retry_is_governed_and_never_auto_executes(tmp_path: Path) -> None:
    root = _root(tmp_path); record = _job(root, status="error", retry_limit=1)
    service = GovernedJobOperationsApplicationService(root)
    result = service.retry(job_id=record["job_id"], actor="local-owner", reason="retry test")
    assert result.ok
    retry = result.data["job"]
    assert retry["job_id"] != record["job_id"]
    assert retry["status"] in {"planned", "approved"}
    assert retry["retry_count"] == 1
    assert retry["operational"]["retry_of_job_id"] == record["job_id"]


def test_uoc008_cancel_blocks_invalid_state(tmp_path: Path) -> None:
    root = _root(tmp_path); record = _job(root, status="pass")
    result = GovernedJobOperationsApplicationService(root).request_cancel(job_id=record["job_id"], actor="owner", reason="no")
    assert not result.ok and result.exit_code.value == 2


def test_uoc008_reconcile_stale_running_job_to_error(tmp_path: Path) -> None:
    root = _root(tmp_path); record = _job(root, status="running")
    service = GovernedJobOperationsApplicationService(root)
    result = service.reconcile_orphans(stale_after_seconds=30)
    assert result.ok and record["job_id"] in result.data["reconciled_job_ids"]
    assert GovernedJobStore(root).load(record["job_id"])["status"] == "error"


def test_uoc008_progress_records_heartbeat_phase_and_worker_presence(tmp_path: Path) -> None:
    root = _root(tmp_path); record = _job(root, status="running")
    service = GovernedJobOperationsApplicationService(root)
    result = service.record_progress(job_id=record["job_id"], phase="validate", progress_percent=42, worker_pid=4321, message="phase progress token=secretvalue")
    assert result.ok
    job = result.data["job"]
    assert job["heartbeat_sequence"] == 2
    assert job["operational"]["phase"] == "validate"
    assert job["operational"]["progress_percent"] == 42
    assert job["operational"]["worker_pid_present"] is True
    logs = service.read_logs(job_id=record["job_id"])
    assert "secretvalue" not in logs.data["entries"][0]["message"]


def test_uoc008_runtime_lock_is_not_left_after_mutation(tmp_path: Path) -> None:
    root = _root(tmp_path); record = _job(root, status="error", retry_limit=1)
    service = GovernedJobOperationsApplicationService(root)
    assert service.retry(job_id=record["job_id"], actor="owner", reason="lock test").ok
    assert not (root / "outputs/runtime/governed_jobs/.uoc008-operation.lock").exists()
