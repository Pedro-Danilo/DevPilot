from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.application import ApplicationRequest, ApplicationResponse, ApplicationService
from devpilot_core.cli_models import ExitCode
from devpilot_core.interfaces.api import ApiRouteContractRegistryValidator, create_app

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "test-token-post-h-016-d"
REGISTRY_PATH = ROOT / ".devpilot/workspaces/workspace_registry.json"


def _client() -> TestClient:
    return TestClient(create_app(ROOT, api_token=TOKEN))


def _headers() -> dict[str, str]:
    return {"X-DevPilot-Token": TOKEN, "Origin": "http://127.0.0.1:5173"}


def test_post_h_016_d_application_service_exposes_portfolio_status_read_only() -> None:
    response = ApplicationService(ROOT).handle(
        ApplicationRequest(
            operation="portfolio.status",
            payload={},
            client="api-local",
            dry_run=True,
        )
    )

    assert isinstance(response, ApplicationResponse)
    assert response.operation == "portfolio.status"
    assert response.ok is True, response.to_dict()
    assert response.exit_code == int(ExitCode.PASS)
    summary = response.data["summary"]
    assert summary["portfolio_status_read_only"] is True
    assert summary["registered_workspaces_only"] is True
    assert summary["state_files_read"] is False
    assert summary["secrets_read"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["cross_workspace_writes"] is False
    assert response.to_dict()["contract"] == "DevPilotApplicationResponse"


def test_post_h_016_d_portfolio_status_api_is_protected_and_does_not_change_active_workspace() -> None:
    client = _client()
    before_text = REGISTRY_PATH.read_text(encoding="utf-8")
    before = json.loads(before_text)

    missing_token = client.get("/api/v1/portfolio/status", headers={"Origin": "http://127.0.0.1:5173"})
    assert missing_token.status_code == 401

    response = client.get("/api/v1/portfolio/status", headers=_headers())
    after_text = REGISTRY_PATH.read_text(encoding="utf-8")
    after = json.loads(after_text)

    assert response.status_code == 200, response.text
    assert response.headers.get("X-DevPilot-Policy") == "allowed"
    assert after_text == before_text
    assert after.get("active_workspace_id") == before.get("active_workspace_id")
    payload = response.json()
    assert payload["contract"] == "DevPilotApplicationResponse"
    assert payload["operation"] == "portfolio.status"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["portfolio_status_read_only"] is True
    assert payload["data"]["summary"]["cross_workspace_writes"] is False


def test_post_h_016_d_portfolio_api_has_no_workspace_selection_mutation_surface() -> None:
    client = _client()
    before_text = REGISTRY_PATH.read_text(encoding="utf-8")

    response = client.post("/api/v1/portfolio/status", headers=_headers(), json={"workspace_id": "devpilot-local"})

    assert response.status_code == 403
    assert REGISTRY_PATH.read_text(encoding="utf-8") == before_text
    payload = response.json()
    assert payload["operation"] == "api.policy"
    assert payload["findings"][0]["id"] == "API_POLICY_BINDING_MISSING_BLOCK"


def test_post_h_016_d_route_registry_docs_and_tcr_are_synchronized() -> None:
    result = ApiRouteContractRegistryValidator(ROOT).validate()
    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["routes_total"] == 35
    assert summary["fastapi_route_keys_total"] == 35
    assert summary["canonical_router_route_keys_total"] == 35
    assert summary["application_service_routes_total"] == 31

    route_registry = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    routes = {route["route_id"]: route for route in route_registry["routes"]}
    route = routes["api.portfolio.status"]
    assert route["operation"] == "portfolio.status"
    assert route["application_service_required"] is True
    assert route["policy_check_required"] is True
    assert route["auth_required"] is True
    assert route["dry_run_only"] is True
    assert route["mutations_allowed"] is False
    assert route["external_api_allowed"] is False
    assert route["remote_execution_allowed"] is False
    assert route["connector_write_allowed"] is False
    assert route["plugin_execution_allowed"] is False

    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")
    assert "post-h-016-cli-api-integration-secure" in tcr_v1
    assert "post-h-016-cli-api-integration-secure" in tcr_v2

    backlog = (ROOT / "docs/backlogs/POST-H-016_workspace_portfolio_hardening.md").read_text(encoding="utf-8")
    post_doc = (ROOT / "docs/POST-H-016_workspace_portfolio_hardening.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    assert 'current_micro_sprint: "POST-H-016-D"' in backlog
    assert 'next_micro_sprint: "POST-H-016-E"' in backlog
    assert "POST-H-016-D — CLI/API integration segura" in post_doc
    assert "POST-H-016-E — Quality gate y runbook" in post_doc
    assert len(post_doc.splitlines()) >= 300
    assert "GET /api/v1/portfolio/status" in runbook
