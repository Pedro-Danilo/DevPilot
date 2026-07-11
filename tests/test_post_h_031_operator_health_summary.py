from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.application import ApplicationRequest, ApplicationResponse, ApplicationService
from devpilot_core.cli_models import ExitCode
from devpilot_core.evidence_graph import OperatorHealthOptions, OperatorHealthSummaryBuilder
from devpilot_core.interfaces.api import ApiRouteContractRegistryValidator, create_app
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "test-token-operator-health"


def _health_from_result(result):
    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    health = result.data["health"]
    assert health["schema_id"] == "SCHEMA-DEVPL-OPERATOR-HEALTH-SUMMARY-V1"
    return health


def test_operator_health_summary_builds_schema_valid_read_only_view() -> None:
    result = OperatorHealthSummaryBuilder(ROOT).build()
    health = _health_from_result(result)

    validation = SchemaValidator(ROOT).validate_payload(
        schema="OperatorHealthSummary",
        payload=health,
        instance_label="in-memory-operator-health-summary",
    )

    assert validation.ok is True, validation.to_dict()
    assert health["created_by"] == "POST-H-031-B"
    assert health["overall_status"] in {"green", "yellow"}
    assert health["decision"] == "PASS"
    assert health["safety"]["read_only"] is True
    assert health["safety"]["commands_executed"] is False
    assert health["safety"]["network_used"] is False
    assert health["safety"]["external_api_used"] is False
    assert health["safety"]["source_mutations_performed"] is False
    assert health["safety"]["devpilot_db_read"] is False
    assert {section["section_id"] for section in health["sections"]} >= {
        "global_state",
        "evidence_graph",
        "documentation_governance",
        "test_contracts",
        "production_ready_local",
        "claims_no_go",
        "runtime_state",
        "observability",
        "operator_dashboard",
        "application_boundary",
    }


def test_operator_health_summary_derives_claims_and_no_go_safely() -> None:
    health = _health_from_result(OperatorHealthSummaryBuilder(ROOT).build())

    assert "production-ready-local" in health["claims"]["allowed"]
    assert "enterprise-ready" in health["claims"]["prohibited"]
    assert "remote-ready" in health["claims"]["prohibited"]
    assert "compliance-certified" in health["claims"]["prohibited"]
    assert "saas-ready" in health["claims"]["prohibited"]
    assert health["claims"]["forbidden_available_total"] == 0
    assert health["no_go_gates"]["violations_total"] == 0
    assert all(gate["safe"] is True for gate in health["no_go_gates"]["gates"])


def test_operator_health_summary_keeps_runtime_gaps_actionable_without_blocking() -> None:
    health = _health_from_result(OperatorHealthSummaryBuilder(ROOT).build())

    assert health["evidence_quality"]["missing_expected_total"] >= 1
    assert health["evidence_quality"]["blocking_gaps_total"] == 0
    assert health["top_actions"]
    assert all(action["dry_run"] is True for action in health["top_actions"])
    assert all("--write-report" in action["command"] for action in health["top_actions"])
    assert not any("--execute" in action["command"] for action in health["top_actions"])


def test_application_service_exposes_operator_health_summary() -> None:
    service = ApplicationService(ROOT)
    direct = service.operator_health_summary()
    health = _health_from_result(direct)

    response = service.handle(
        ApplicationRequest(
            operation="operator.health",
            payload={"write_report": False},
            client="api-local",
            dry_run=True,
        )
    )

    assert isinstance(response, ApplicationResponse)
    assert response.operation == "operator.health"
    assert response.ok is True, response.to_dict()
    assert response.exit_code == int(ExitCode.PASS)
    assert response.data["health"]["schema_id"] == health["schema_id"]
    assert response.data["summary"]["read_only"] is True


def test_operator_health_cli_json_and_report_output(tmp_path: Path) -> None:
    output_json = tmp_path / "operator_health_summary.json"
    output_markdown = tmp_path / "operator_health_summary.md"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "evidence",
            "health",
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
    assert payload["command"] == "evidence health"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is True
    assert output_json.exists()
    assert output_markdown.exists()
    stored = json.loads(output_json.read_text(encoding="utf-8"))
    assert stored["schema_id"] == "SCHEMA-DEVPL-OPERATOR-HEALTH-SUMMARY-V1"
    assert "Operator Health Summary" in output_markdown.read_text(encoding="utf-8")


def test_operator_health_api_route_is_protected_and_application_service_bound() -> None:
    client = TestClient(create_app(ROOT, api_token=TOKEN))
    missing_token = client.get("/api/v1/operator/health", headers={"Origin": "http://127.0.0.1:5173"})
    assert missing_token.status_code == 401

    response = client.get(
        "/api/v1/operator/health",
        headers={"X-DevPilot-Token": TOKEN, "Origin": "http://127.0.0.1:5173"},
    )
    assert response.status_code == 200, response.text
    assert response.headers.get("X-DevPilot-Policy") == "allowed"
    payload = response.json()
    assert payload["contract"] == "DevPilotApplicationResponse"
    assert payload["operation"] == "operator.health"
    assert payload["ok"] is True
    assert payload["data"]["health"]["schema_id"] == "SCHEMA-DEVPL-OPERATOR-HEALTH-SUMMARY-V1"
    assert payload["data"]["summary"]["read_only"] is True


def test_operator_health_contracts_and_route_registry_are_synchronized() -> None:
    route_result = ApiRouteContractRegistryValidator(ROOT).validate()
    assert route_result.ok, route_result.to_dict()
    route_summary = route_result.data["summary"]
    assert route_summary["routes_total"] == 37
    assert route_summary["fastapi_route_keys_total"] == 37
    assert route_summary["canonical_router_route_keys_total"] == 37
    assert route_summary["application_service_routes_total"] == 33

    route_registry = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    routes = {route["route_id"]: route for route in route_registry["routes"]}
    assert routes["api.operator.health"]["operation"] == "operator.health"
    assert routes["api.operator.health"]["application_service_required"] is True
    assert routes["api.operator.health"]["policy_check_required"] is True
    assert routes["api.operator.health"]["auth_required"] is True
    assert routes["api.operator.health"]["mutations_allowed"] is False
    assert routes["api.operator.health"]["external_api_allowed"] is False

    schema_catalog = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    assert any(schema["schema_id"] == "SCHEMA-DEVPL-OPERATOR-HEALTH-SUMMARY-V1" for schema in schema_catalog["schemas"])

    tcr_v2 = json.loads((ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8"))
    contracts = {contract["contract_id"]: contract for contract in tcr_v2["contracts"]}
    assert contracts["post-h-031-operator-health-summary"]["domain"] == "operations.observability"
    assert contracts["post-h-031-operator-health-application-api"]["domain"] == "application.service"
