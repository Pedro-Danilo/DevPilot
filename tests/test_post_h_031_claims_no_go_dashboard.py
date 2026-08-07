from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.application import ApplicationRequest, ApplicationResponse, ApplicationService
from devpilot_core.cli_models import ExitCode
from devpilot_core.evidence_graph import ClaimsDashboardOptions, ClaimsNoGoDashboardBuilder
from devpilot_core.interfaces.api import ApiRouteContractRegistryValidator, create_app
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "test-token-claims-no-go"


def _dashboard_from_result(result):
    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    dashboard = result.data["claims_no_go_dashboard"]
    assert dashboard["schema_id"] == "SCHEMA-DEVPL-CLAIMS-NO-GO-DASHBOARD-V1"
    return dashboard


def test_claims_no_go_dashboard_builds_schema_valid_read_only_view() -> None:
    result = ClaimsNoGoDashboardBuilder(ROOT).build()
    dashboard = _dashboard_from_result(result)

    validation = SchemaValidator(ROOT).validate_payload(
        schema="ClaimsNoGoDashboard",
        payload=dashboard,
        instance_label="in-memory-claims-no-go-dashboard",
    )

    assert validation.ok is True, validation.to_dict()
    assert dashboard["created_by"] == "POST-H-031-D"
    assert dashboard["summary"]["decision"] == "PASS"
    assert dashboard["summary"]["allowed_claims_total"] == 1
    assert dashboard["summary"]["conditioned_claims_total"] == 1
    assert dashboard["summary"]["prohibited_claims_total"] == 4
    assert dashboard["summary"]["no_go_violations_total"] == 0
    assert dashboard["summary"]["overclaim_violations_total"] == 0
    assert dashboard["safety"]["read_only"] is True
    assert dashboard["safety"]["claims_mutated"] is False
    assert dashboard["safety"]["no_go_gates_mutated"] is False
    assert dashboard["safety"]["overclaim_scan_llm_used"] is False
    assert dashboard["safety"]["network_used"] is False
    assert dashboard["safety"]["external_api_used"] is False
    assert dashboard["safety"]["devpilot_db_read"] is False


def test_claims_no_go_dashboard_blocks_forbidden_claims_and_preserves_bounded_claims() -> None:
    dashboard = _dashboard_from_result(ClaimsNoGoDashboardBuilder(ROOT).build())
    claims = {claim["claim_id"]: claim for claim in dashboard["claims"]}

    assert claims["production-ready-local"]["status"] == "allowed"
    assert claims["production-ready-local"]["allowed"] is True
    assert claims["production-ready-local"]["evidence_refs"]

    assert claims["audit-friendly"]["status"] == "conditioned"
    assert claims["audit-friendly"]["conditioned"] is True
    assert "not compliance certification" in claims["audit-friendly"]["scope"]

    for claim_id in ["enterprise-ready", "remote-ready", "compliance-certified", "saas-ready"]:
        assert claims[claim_id]["status"] == "prohibited"
        assert claims[claim_id]["allowed"] is False
        assert claims[claim_id]["prohibited"] is True
        assert claims[claim_id]["blocking_reasons"]


def test_claims_no_go_dashboard_lists_all_no_go_gates_with_reasons() -> None:
    dashboard = _dashboard_from_result(ClaimsNoGoDashboardBuilder(ROOT).build())
    gates = {gate["gate_id"]: gate for gate in dashboard["no_go_gates"]}

    expected = {
        "remote_execution_enabled",
        "connector_write_enabled",
        "plugin_execution_enabled",
        "external_apis_required",
        "compliance_certification_claim",
        "enterprise_ready_claim",
        "remote_ready_claim",
        "saas_ready_claim",
    }
    assert set(gates) == expected
    assert all(gate["status"] == "active_blocking" for gate in gates.values())
    assert all(gate["safe"] is True for gate in gates.values())
    assert all(gate["source_refs"] for gate in gates.values())
    assert gates["enterprise_ready_claim"]["blocks_claims"] == ["enterprise-ready"]


def test_claims_no_go_dashboard_integrates_production_claims_validator() -> None:
    dashboard = _dashboard_from_result(ClaimsNoGoDashboardBuilder(ROOT).build())

    scan = dashboard["overclaim_scan"]
    assert scan["status"] == "pass"
    assert scan["validator_command"] == "production-ready claims validate"
    assert scan["documents_scanned_total"] >= 3
    assert scan["violations_total"] == 0
    assert scan["llm_judge_used"] is False

    relation = dashboard["production_ready_relation"]
    assert relation["claims_validator_ok"] is True
    assert relation["production_ready_local_declared"] is True
    assert relation["final_declaration_audit_path"] == "docs/audits/devpilot_local_production_ready_declaration.md"


def test_claims_no_go_dashboard_cli_json_and_report_output(tmp_path: Path) -> None:
    output_json = tmp_path / "claims_no_go_dashboard.json"
    output_markdown = tmp_path / "claims_no_go_dashboard.md"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "evidence",
            "claims-dashboard",
            "--json",
            "--write-report",
            "--output-json",
            str(output_json),
            "--output-markdown",
            str(output_markdown),
        ],
        cwd=ROOT,
        env={"PYTHONPATH": "src"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["command"] == "evidence claims-dashboard"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is True
    assert output_json.exists()
    assert output_markdown.exists()
    stored = json.loads(output_json.read_text(encoding="utf-8"))
    assert stored["schema_id"] == "SCHEMA-DEVPL-CLAIMS-NO-GO-DASHBOARD-V1"
    assert "Claims and No-Go Dashboard" in output_markdown.read_text(encoding="utf-8")


def test_claims_no_go_dashboard_application_service_and_api_route() -> None:
    service = ApplicationService(ROOT)
    direct = service.claims_no_go_dashboard()
    dashboard = _dashboard_from_result(direct)

    response = service.handle(
        ApplicationRequest(
            operation="operator.claims_no_go",
            payload={"write_report": False},
            client="api-local",
            dry_run=True,
        )
    )

    assert isinstance(response, ApplicationResponse)
    assert response.operation == "operator.claims_no_go"
    assert response.ok is True, response.to_dict()
    assert response.exit_code == int(ExitCode.PASS)
    assert response.data["claims_no_go_dashboard"]["schema_id"] == dashboard["schema_id"]
    assert response.data["summary"]["claims_mutated"] is False

    client = TestClient(create_app(ROOT, api_token=TOKEN))
    missing_token = client.get("/api/v1/operator/claims-no-go", headers={"Origin": "http://127.0.0.1:5173"})
    assert missing_token.status_code == 401
    api_response = client.get(
        "/api/v1/operator/claims-no-go",
        headers={"X-DevPilot-Token": TOKEN, "Origin": "http://127.0.0.1:5173"},
    )
    assert api_response.status_code == 200, api_response.text
    assert api_response.headers.get("X-DevPilot-Policy") == "allowed"
    payload = api_response.json()
    assert payload["contract"] == "DevPilotApplicationResponse"
    assert payload["operation"] == "operator.claims_no_go"
    assert payload["ok"] is True
    assert payload["data"]["claims_no_go_dashboard"]["schema_id"] == "SCHEMA-DEVPL-CLAIMS-NO-GO-DASHBOARD-V1"


def test_claims_no_go_contracts_and_route_registry_are_synchronized() -> None:
    route_result = ApiRouteContractRegistryValidator(ROOT).validate()
    assert route_result.ok, route_result.to_dict()
    route_summary = route_result.data["summary"]
    assert route_summary["routes_total"] == len(json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))["routes"])
    assert route_summary["routes_total"] >= 39
    registry = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    expected_total = len(registry["routes"])
    assert route_summary["fastapi_route_keys_total"] == expected_total
    assert route_summary["canonical_router_route_keys_total"] == expected_total
    assert route_summary["application_service_routes_total"] == sum(1 for route in registry["routes"] if route.get("application_service_required"))

    route_registry = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    routes = {route["route_id"]: route for route in route_registry["routes"]}
    assert routes["api.operator.claims_no_go"]["operation"] == "operator.claims_no_go"
    assert routes["api.operator.claims_no_go"]["application_service_required"] is True
    assert routes["api.operator.claims_no_go"]["policy_check_required"] is True
    assert routes["api.operator.claims_no_go"]["auth_required"] is True
    assert routes["api.operator.claims_no_go"]["mutations_allowed"] is False
    assert routes["api.operator.claims_no_go"]["external_api_allowed"] is False

    schema_catalog = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    assert any(schema["schema_id"] == "SCHEMA-DEVPL-CLAIMS-NO-GO-DASHBOARD-V1" for schema in schema_catalog["schemas"])

    tcr_v2 = json.loads((ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8"))
    contracts = {contract["contract_id"]: contract for contract in tcr_v2["contracts"]}
    assert contracts["post-h-031-claims-no-go-dashboard"]["domain"] == "operations.observability"
    assert contracts["post-h-031-claims-no-go-application-api"]["domain"] == "application.service"
