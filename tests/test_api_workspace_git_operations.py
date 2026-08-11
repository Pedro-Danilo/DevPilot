from __future__ import annotations

from fastapi.testclient import TestClient

from devpilot_core.interfaces.api.app import create_app

from uoc006_fixtures import find_approval_id, uoc006_env

TOKEN = "uoc006-test-token"
HEADERS = {"X-DevPilot-Token": TOKEN}


def _document_id(client: TestClient) -> str:
    response = client.get("/api/v1/workspace/documents?limit=100", headers=HEADERS)
    assert response.status_code == 200
    return next(str(node["document_id"]) for node in response.json()["data"]["nodes"] if node.get("relative_path") == "docs/review.md")


def _approve(client: TestClient, payload: dict) -> str:
    approval_id = find_approval_id(payload)
    assert approval_id
    response = client.post(f"/api/v1/approvals/{approval_id}/approve", headers=HEADERS, json={"actor": "owner", "reason": "Approved UOC-006 fixture"})
    assert response.status_code == 200
    assert response.json()["ok"] is True
    return approval_id


def test_uoc006_api_end_to_end_stage_and_commit(uoc006_env):
    client = TestClient(create_app(uoc006_env["platform"], api_token=TOKEN))
    assert client.get("/api/v1/workspace/git/status", headers=HEADERS).status_code == 200
    document_id = _document_id(client)
    plan_response = client.post("/api/v1/workspace/git/plans", headers=HEADERS, json={
        "document_ids": [document_id],
        "commit_message": "docs: API governed review",
        "author_name": "DevPilot Owner",
        "author_email": "devpilot-owner@local.invalid",
    })
    assert plan_response.status_code == 200
    plan = plan_response.json()["data"]["plan"]
    missing = client.post(f"/api/v1/workspace/git/plans/{plan['plan_id']}/stage", headers=HEADERS, json={"plan_hash": plan["plan_hash"], "approval_id": "APPROVAL-MISSING", "actor": "owner"})
    assert missing.status_code in {403, 409, 422}
    assert missing.json()["ok"] is False
    request = client.post(f"/api/v1/workspace/git/plans/{plan['plan_id']}/stage-approval-request", headers=HEADERS, json={"plan_hash": plan["plan_hash"], "actor": "owner", "reason": "Stage reviewed API fixture", "ttl_minutes": 15})
    assert request.status_code == 200
    stage_approval = _approve(client, request.json()["data"])
    staged_response = client.post(f"/api/v1/workspace/git/plans/{plan['plan_id']}/stage", headers=HEADERS, json={"plan_hash": plan["plan_hash"], "approval_id": stage_approval, "actor": "owner"})
    assert staged_response.status_code == 200
    stage = staged_response.json()["data"]["stage_execution"]
    commit_request = client.post(f"/api/v1/workspace/git/stage-executions/{stage['stage_execution_id']}/commit-approval-request", headers=HEADERS, json={"actor": "owner", "reason": "Commit reviewed API fixture", "ttl_minutes": 15})
    assert commit_request.status_code == 200
    commit_approval = _approve(client, commit_request.json()["data"])
    committed = client.post(f"/api/v1/workspace/git/stage-executions/{stage['stage_execution_id']}/commit", headers=HEADERS, json={"approval_id": commit_approval, "actor": "owner"})
    assert committed.status_code == 200
    execution = committed.json()["data"]["execution"]
    assert execution["status"] == "committed"
    assert execution["committed_paths"] == ["docs/review.md"]
    assert execution["push_performed"] is False


def test_uoc006_api_branch_control_and_security(uoc006_env):
    from uoc006_fixtures import git
    git(uoc006_env["workspace"], "restore", "docs/review.md")
    client = TestClient(create_app(uoc006_env["platform"], api_token=TOKEN))
    assert client.get("/api/v1/workspace/git/status", headers={"X-DevPilot-Token": "invalid"}).status_code in {401, 403}
    invalid = client.post("/api/v1/workspace/git/branches/plan", headers=HEADERS, json={"branch_name": "unsafe-branch"})
    assert invalid.status_code in {403, 409, 422}
    response = client.post("/api/v1/workspace/git/branches/plan", headers=HEADERS, json={"branch_name": "feat/uoc006-api"})
    assert response.status_code == 200
    plan = response.json()["data"]["plan"]
    request = client.post(f"/api/v1/workspace/git/branches/{plan['plan_id']}/approval-request", headers=HEADERS, json={"plan_hash": plan["plan_hash"], "actor": "owner", "reason": "Create safe local branch", "ttl_minutes": 15})
    approval_id = _approve(client, request.json()["data"])
    created = client.post(f"/api/v1/workspace/git/branches/{plan['plan_id']}/create", headers=HEADERS, json={"plan_hash": plan["plan_hash"], "approval_id": approval_id, "actor": "owner"})
    assert created.status_code == 200
    assert created.json()["ok"] is True
    assert created.json()["data"]["summary"]["checkout_performed"] is False
    assert created.json()["data"]["summary"]["push_performed"] is False
