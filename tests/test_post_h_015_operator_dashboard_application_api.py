from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.application import ApplicationRequest, ApplicationResponse, ApplicationService
from devpilot_core.cli_models import ExitCode
from devpilot_core.interfaces.api import ApiRouteContractRegistryValidator, create_app
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "test-token-operator-dashboard"


def _client() -> TestClient:
    return TestClient(create_app(ROOT, api_token=TOKEN))


def _headers() -> dict[str, str]:
    return {"X-DevPilot-Token": TOKEN, "Origin": "http://127.0.0.1:5173"}


def test_post_h_015_c_application_service_exposes_operator_dashboard_snapshot() -> None:
    service = ApplicationService(ROOT)
    response = service.handle(
        ApplicationRequest(
            operation="operator.dashboard",
            payload={"write_report": False},
            client="api-local",
            dry_run=True,
        )
    )

    assert isinstance(response, ApplicationResponse)
    assert response.operation == "operator.dashboard"
    assert response.ok is True, response.to_dict()
    assert response.exit_code == int(ExitCode.PASS)
    snapshot = response.data["snapshot"]
    summary = response.data["summary"]
    assert snapshot["schema_id"] == "SCHEMA-DEVPL-OPERATOR-DASHBOARD-SNAPSHOT-V1"
    assert snapshot["created_by"] == "POST-H-015-B"
    assert summary["read_only"] is True
    assert summary["dry_run"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert response.to_dict()["contract"] == "DevPilotApplicationResponse"


def test_post_h_015_c_operator_dashboard_api_route_is_protected_and_application_service_bound() -> None:
    client = _client()
    missing_token = client.get("/api/v1/operator/dashboard", headers={"Origin": "http://127.0.0.1:5173"})
    assert missing_token.status_code == 401

    response = client.get("/api/v1/operator/dashboard", headers=_headers())
    assert response.status_code == 200, response.text
    assert response.headers.get("X-DevPilot-Policy") == "allowed"
    payload = response.json()
    assert payload["contract"] == "DevPilotApplicationResponse"
    assert payload["operation"] == "operator.dashboard"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is False
    assert payload["data"]["summary"]["read_only"] is True
    assert payload["data"]["summary"]["network_used"] is False
    assert payload["data"]["snapshot"]["sections"]["roadmap"]["source_refs"]


def test_post_h_015_c_operator_dashboard_api_route_can_write_report_only_when_requested() -> None:
    response = _client().get("/api/v1/operator/dashboard?write_report=true", headers=_headers())

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is True
    assert payload["data"]["reports"] == {
        "json": "outputs/reports/operator_dashboard_snapshot.json",
        "markdown": "outputs/reports/operator_dashboard_snapshot.md",
    }
    validation = SchemaValidator(ROOT).validate(
        schema="OperatorDashboardSnapshot",
        instance="outputs/reports/operator_dashboard_snapshot.json",
    )
    assert validation.ok, validation.to_dict()


def test_post_h_015_c_route_registry_tcr_and_docs_are_synchronized() -> None:
    result = ApiRouteContractRegistryValidator(ROOT).validate()
    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["routes_total"] == 35
    assert summary["fastapi_route_keys_total"] == 35
    assert summary["canonical_router_route_keys_total"] == 35
    assert summary["application_service_routes_total"] == 31

    route_registry = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    routes = {route["route_id"]: route for route in route_registry["routes"]}
    route = routes["api.operator.dashboard"]
    assert route["operation"] == "operator.dashboard"
    assert route["application_service_required"] is True
    assert route["policy_check_required"] is True
    assert route["auth_required"] is True
    assert route["dry_run_only"] is True
    assert route["mutations_allowed"] is False
    assert route["external_api_allowed"] is False
    assert route["remote_execution_allowed"] is False
    assert route["connector_write_allowed"] is False
    assert route["plugin_execution_allowed"] is False

    tcr_v2 = json.loads((ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8"))
    contracts = {contract["contract_id"]: contract for contract in tcr_v2["contracts"]}
    assert contracts["post-h-015-operator-dashboard-schema-config"]["domain"] == "product.ui"
    assert contracts["post-h-015-operator-dashboard-aggregator"]["domain"] == "product.ui"
    assert contracts["post-h-015-operator-dashboard-application-service-api"]["domain"] == "application.service"

    backlog = (ROOT / "docs/backlogs/POST-H-015_local_operator_dashboard.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/local_operator_dashboard_runbook.md").read_text(encoding="utf-8")
    assert 'current_micro_sprint: "POST-H-015-E"' in backlog
    assert 'next_micro_sprint: "POST-H-016-A"' in backlog
    assert "POST-H-015-C — ApplicationService/API integration" in backlog
    assert "POST-H-015-C — ApplicationService/API integration" in runbook
    assert "POST-H-015-D — UI operator dashboard" in backlog
    assert "POST-H-015-D — UI operator dashboard" in runbook
    assert "POST-H-015-E — Quality gate y runbook operacional" in backlog
    assert "POST-H-015-E — Quality gate y runbook operacional" in runbook
