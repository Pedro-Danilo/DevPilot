from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from devpilot_core.interfaces.api import create_app
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, API_TOKEN_HEADER

from uoc003_fixtures import create_uoc003_workspace, source_snapshot

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "uoc-003-test-token"


def _client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, authenticated: bool = True) -> tuple[TestClient, Path]:
    workspace = create_uoc003_workspace(tmp_path / "inventory-sales-local")
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(workspace))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(workspace))
    client = TestClient(create_app(ROOT, api_token=TOKEN))
    if authenticated:
        client.headers.update({API_TOKEN_HEADER: TOKEN})
    return client, workspace


def test_uoc003_api_plan_execute_status_and_traceability(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client, workspace = _client(tmp_path, monkeypatch)
    before = source_snapshot(workspace)
    planned = client.post("/api/v1/workspace/validations/plan", json={"operation": "workspace.validations.plan", "payload": {"scopes": ["frontmatter", "links", "checklist_pre_code", "traceability"], "strict": True}, "dry_run": True})
    assert planned.status_code == 200, planned.text
    plan = planned.json()["data"]["plan"]
    executed = client.post("/api/v1/workspace/validations/execute", json={"operation": "workspace.validations.execute", "payload": {"plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"], "plan": plan}, "dry_run": False})
    assert executed.status_code == 200, executed.text
    assert executed.json()["data"]["summary"]["steps_total"] == 4
    job_id = executed.json()["data"]["job"]["job_id"]
    status = client.get(f"/api/v1/workspace/validations/{job_id}")
    traceability = client.get("/api/v1/workspace/traceability")
    assert status.status_code == 200
    assert traceability.status_code == 200
    assert traceability.json()["data"]["traceability"]["matrix"][0]["navigation"]["document_id"].startswith("doc_")
    assert source_snapshot(workspace) == before


def test_uoc003_completed_block_job_is_http_200_with_application_block(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = _client(tmp_path, monkeypatch)
    planned = client.post("/api/v1/workspace/validations/plan", json={"payload": {"scopes": ["readiness_strict"]}}).json()["data"]["plan"]
    response = client.post("/api/v1/workspace/validations/execute", json={"payload": {"plan_id": planned["plan_id"], "plan_hash": planned["plan_hash"], "plan": planned}, "dry_run": False})
    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert response.json()["data"]["job"]["status"] == "block"
    assert response.json()["findings"]


def test_uoc003_api_requires_token_and_rejects_operation_switch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    unauthorized, _ = _client(tmp_path, monkeypatch, authenticated=False)
    assert unauthorized.post("/api/v1/workspace/validations/plan", json={"payload": {}}).status_code == 401
    client, _ = _client(tmp_path / "second", monkeypatch)
    mismatch = client.post("/api/v1/workspace/validations/plan", json={"operation": "workspace.validations.execute", "payload": {}})
    assert mismatch.status_code in {400, 403}


def test_uoc003_routes_have_explicit_policy_bindings() -> None:
    expected = {
        ("POST", "/api/v1/workspace/validations/plan"),
        ("POST", "/api/v1/workspace/validations/execute"),
        ("GET", "/api/v1/workspace/validations/{job_id}"),
        ("GET", "/api/v1/workspace/traceability"),
    }
    assert expected <= set(API_ROUTE_POLICIES)
