from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from devpilot_core.application.governed_jobs import GovernedJobStore
from devpilot_core.interfaces.api.app import create_app

REPO = Path(__file__).resolve().parents[1]
TOKEN = "uoc008-test-token"


def _headers() -> dict[str, str]: return {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture()
def runtime_root() -> Path:
    root = REPO / "outputs/runtime/governed_jobs"
    backup = REPO / "outputs/runtime/governed_jobs_uoc008_test_backup"
    if backup.exists(): shutil.rmtree(backup)
    if root.exists(): shutil.move(str(root), str(backup))
    try:
        yield REPO
    finally:
        if root.exists(): shutil.rmtree(root)
        if backup.exists(): shutil.move(str(backup), str(root))


def _seed(root: Path) -> str:
    job_id = "job_" + "b" * 32
    GovernedJobStore(root).save({
        "schema_version": "2.0", "schema_id": "SCHEMA-DEVPL-UI-GOVERNED-JOB-V2", "job_id": job_id,
        "capability_id": "cli.workspace.status", "workspace_id": "ws", "status": "error", "risk_class": "read-only", "dry_run": True,
        "timeout_seconds": 60, "retry_limit": 1, "retry_count": 0, "heartbeat_interval_seconds": 5, "heartbeat_sequence": 1,
        "created_at": "2026-08-11T00:00:00Z", "updated_at": "2026-08-11T00:00:00Z", "last_heartbeat_at": None,
        "approval_binding_id": None, "supports_cancel": True, "supports_rollback": False, "cancel_token_hash": "1"*64,
        "idempotency_key_hash": "2"*64, "correlation_id": "corr_api", "request_fingerprint": "3"*64, "parameter_keys": [],
        "artifact_refs": [], "evidence_refs": [], "runtime_adapter_id": None, "errors": ["fixture"], "result_summary": {},
    })
    return job_id


def test_uoc008_jobs_routes_require_token_and_support_list_detail_logs_retry(runtime_root: Path) -> None:
    job_id = _seed(runtime_root); client = TestClient(create_app(root=runtime_root, api_token=TOKEN))
    assert client.get("/api/v1/jobs").status_code == 401
    listed = client.get("/api/v1/jobs", headers=_headers()); assert listed.status_code == 200 and listed.json()["ok"] is True
    detail = client.get(f"/api/v1/jobs/{job_id}", headers=_headers()); assert detail.status_code == 200 and detail.json()["data"]["job"]["job_id"] == job_id
    logs = client.get(f"/api/v1/jobs/{job_id}/logs", headers=_headers()); assert logs.status_code == 200
    retry = client.post(f"/api/v1/jobs/{job_id}/retry", headers=_headers(), json={"actor":"owner","reason":"api retry"}); assert retry.status_code == 200 and retry.json()["ok"] is True


def test_uoc008_jobs_unknown_id_is_product_block_not_transport_crash(runtime_root: Path) -> None:
    client = TestClient(create_app(root=runtime_root, api_token=TOKEN))
    response = client.get("/api/v1/jobs/job_" + "f"*32, headers=_headers())
    assert response.status_code == 200
    assert response.json()["exit_code"] == 2
