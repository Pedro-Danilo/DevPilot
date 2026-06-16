from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.interfaces.api import create_app
from devpilot_core.interfaces.api.security import API_TOKEN_HEADER, API_ROUTE_POLICIES

ROOT = Path(__file__).resolve().parents[1]
TEST_TOKEN = "devpilot-test-token"


def _client() -> TestClient:
    client = TestClient(create_app(ROOT, api_token=TEST_TOKEN))
    client.headers.update({API_TOKEN_HEADER: TEST_TOKEN})
    return client


def test_approval_center_can_request_list_show_approve_and_deny_controlled_records() -> None:
    client = _client()
    request = client.post(
        "/api/v1/approvals/request",
        json={"tool_id": "tests.run", "action": "execute", "subject": "pytest-sprint71", "actor": "tester", "reason": "sprint 71 test", "ttl_minutes": 30},
    )
    assert request.status_code == 200
    approval = request.json()["data"]["approval"]
    approval_id = approval["approval_id"]
    assert approval["status"] == "requested"

    listed = client.get("/api/v1/approvals?status=requested&limit=20")
    assert listed.status_code == 200
    assert any(item["approval_id"] == approval_id for item in listed.json()["data"]["approvals"])

    shown = client.get(f"/api/v1/approvals/{approval_id}")
    assert shown.status_code == 200
    assert shown.json()["data"]["approval"]["approval_id"] == approval_id

    approved = client.post(f"/api/v1/approvals/{approval_id}/approve", json={"actor": "tester", "reason": "approved for test"})
    assert approved.status_code == 200
    assert approved.json()["data"]["approval"]["status"] == "approved"

    second = client.post(
        "/api/v1/approvals/request",
        json={"tool_id": "tests.run", "action": "execute", "subject": "pytest-sprint71-deny", "actor": "tester", "reason": "sprint 71 deny", "ttl_minutes": 30},
    )
    second_id = second.json()["data"]["approval"]["approval_id"]
    denied = client.post(f"/api/v1/approvals/{second_id}/deny", json={"actor": "tester", "reason": "denied for test"})
    assert denied.status_code == 200
    assert denied.json()["data"]["approval"]["status"] == "denied"


def test_action_launcher_runs_only_safe_dry_run_actions() -> None:
    client = _client()

    readiness = client.post("/api/v1/actions/dry-run", json={"action_id": "readiness", "target": ".", "strict": True})
    code_review = client.post("/api/v1/actions/dry-run", json={"action_id": "code-review", "target": "docs/01_requirements/use_cases.md"})
    refactor_plan = client.post("/api/v1/actions/dry-run", json={"action_id": "refactor-plan", "target": "docs/01_requirements/use_cases.md", "goal": "improve docs"})

    assert readiness.status_code == 200
    assert readiness.json()["data"]["action_launcher"]["dry_run"] is True
    assert code_review.status_code == 200
    assert code_review.json()["data"]["action_launcher"]["operation"] == "review.code"
    assert refactor_plan.status_code == 200
    assert refactor_plan.json()["data"]["action_launcher"]["operation"] == "refactor.plan"


def test_action_launcher_blocks_critical_actions_even_when_dry_run() -> None:
    response = _client().post("/api/v1/actions/dry-run", json={"action_id": "patch-apply", "target": "."})
    payload = response.json()

    assert response.status_code == 403
    assert payload["ok"] is False
    assert payload["data"]["summary"]["critical"] is True
    assert any(finding["id"] == "UI_CRITICAL_ACTION_DISABLED_BLOCK" for finding in payload["findings"])


def test_policy_binding_covers_sprint71_routes() -> None:
    expected = {
        ("GET", "/api/v1/approvals"),
        ("GET", "/api/v1/approvals/{approval_id}"),
        ("POST", "/api/v1/approvals/request"),
        ("POST", "/api/v1/approvals/{approval_id}/approve"),
        ("POST", "/api/v1/approvals/{approval_id}/deny"),
        ("POST", "/api/v1/actions/dry-run"),
    }
    assert expected.issubset(set(API_ROUTE_POLICIES))


def test_openapi_includes_approval_and_dry_run_routes() -> None:
    openapi = _client().get("/api/v1/openapi.json").json()
    for path in ["/api/v1/approvals", "/api/v1/approvals/request", "/api/v1/actions/dry-run"]:
        assert path in openapi["paths"]
