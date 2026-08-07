from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.application import ApplicationRequest, ApplicationResponse, ApplicationService
from devpilot_core.cli_models import ExitCode
from devpilot_core.evidence_graph import GapActionMapBuilder, GapActionOptions
from devpilot_core.interfaces.api import ApiRouteContractRegistryValidator, create_app
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "test-token-operator-gaps"


def _map_from_result(result):
    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    gap_map = result.data["gap_action_map"]
    assert gap_map["schema_id"] == "SCHEMA-DEVPL-GAP-ACTION-MAP-V1"
    return gap_map


def test_gap_action_map_builds_schema_valid_read_only_mapping() -> None:
    result = GapActionMapBuilder(ROOT).build()
    gap_map = _map_from_result(result)

    validation = SchemaValidator(ROOT).validate_payload(
        schema="GapActionMap",
        payload=gap_map,
        instance_label="in-memory-gap-action-map",
    )

    assert validation.ok is True, validation.to_dict()
    assert gap_map["created_by"] == "POST-H-031-C"
    assert gap_map["summary"]["decision"] == "PASS"
    assert gap_map["summary"]["gaps_total"] >= 1
    assert gap_map["summary"]["mapped_gaps_total"] == gap_map["summary"]["gaps_total"]
    assert gap_map["summary"]["unmapped_gaps_total"] == 0
    assert gap_map["summary"]["required_rule_categories_present_total"] == gap_map["summary"]["required_rule_categories_total"]
    assert gap_map["safety"]["read_only"] is True
    assert gap_map["safety"]["commands_executed"] is False
    assert gap_map["safety"]["network_used"] is False
    assert gap_map["safety"]["external_api_used"] is False
    assert gap_map["safety"]["source_mutations_performed"] is False
    assert gap_map["safety"]["devpilot_db_read"] is False


def test_gap_action_map_maps_runtime_gaps_to_safe_verifiable_actions() -> None:
    gap_map = _map_from_result(GapActionMapBuilder(ROOT).build())

    actions = gap_map["actions"]
    assert actions
    assert all(action["dry_run"] is True for action in actions)
    assert all(action["safe"] is True for action in actions)
    assert all(action["verification"] for action in actions)
    assert all(action["closure_criterion"] for action in actions)
    assert all(action["risk_if_ignored"] for action in actions)
    assert not any("--execute" in action["command"] for action in actions)
    assert not any("pip install" in action["command"] for action in actions)
    assert any(action["category"] in {"observability", "production-readiness", "operator-dashboard"} for action in actions)


def test_gap_action_map_blocks_missing_required_rule_category(tmp_path: Path) -> None:
    rules = tmp_path / "gap_action_rules.json"
    rules.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "required_rule_categories": ["missing_required_evidence"],
                "rules": [],
                "safety": {"forbidden_command_fragments": ["--execute"]},
            }
        ),
        encoding="utf-8",
    )

    result = GapActionMapBuilder(ROOT, GapActionOptions(rules_path=rules)).build()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["decision"] == "BLOCK"
    assert any(finding.id == "GAP_ACTION_REQUIRED_RULE_CATEGORY_MISSING" for finding in result.findings)


def test_application_service_exposes_gap_action_map() -> None:
    service = ApplicationService(ROOT)
    direct = service.gap_action_map()
    gap_map = _map_from_result(direct)

    response = service.handle(
        ApplicationRequest(
            operation="operator.gaps",
            payload={"write_report": False},
            client="api-local",
            dry_run=True,
        )
    )

    assert isinstance(response, ApplicationResponse)
    assert response.operation == "operator.gaps"
    assert response.ok is True, response.to_dict()
    assert response.exit_code == int(ExitCode.PASS)
    assert response.data["gap_action_map"]["schema_id"] == gap_map["schema_id"]
    assert response.data["summary"]["commands_executed"] is False


def test_gap_action_map_cli_json_and_report_output(tmp_path: Path) -> None:
    output_json = tmp_path / "gap_action_map.json"
    output_markdown = tmp_path / "gap_action_map.md"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "evidence",
            "gaps",
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
    assert payload["command"] == "evidence gaps"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is True
    assert output_json.exists()
    assert output_markdown.exists()
    stored = json.loads(output_json.read_text(encoding="utf-8"))
    assert stored["schema_id"] == "SCHEMA-DEVPL-GAP-ACTION-MAP-V1"
    assert "Gap Action Map" in output_markdown.read_text(encoding="utf-8")


def test_gap_action_map_api_route_is_protected_and_application_service_bound() -> None:
    client = TestClient(create_app(ROOT, api_token=TOKEN))
    missing_token = client.get("/api/v1/operator/gaps", headers={"Origin": "http://127.0.0.1:5173"})
    assert missing_token.status_code == 401

    response = client.get(
        "/api/v1/operator/gaps",
        headers={"X-DevPilot-Token": TOKEN, "Origin": "http://127.0.0.1:5173"},
    )
    assert response.status_code == 200, response.text
    assert response.headers.get("X-DevPilot-Policy") == "allowed"
    payload = response.json()
    assert payload["contract"] == "DevPilotApplicationResponse"
    assert payload["operation"] == "operator.gaps"
    assert payload["ok"] is True
    assert payload["data"]["gap_action_map"]["schema_id"] == "SCHEMA-DEVPL-GAP-ACTION-MAP-V1"
    assert payload["data"]["summary"]["read_only"] is True


def test_gap_action_contracts_and_route_registry_are_synchronized() -> None:
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
    assert routes["api.operator.gaps"]["operation"] == "operator.gaps"
    assert routes["api.operator.gaps"]["application_service_required"] is True
    assert routes["api.operator.gaps"]["policy_check_required"] is True
    assert routes["api.operator.gaps"]["auth_required"] is True
    assert routes["api.operator.gaps"]["mutations_allowed"] is False
    assert routes["api.operator.gaps"]["external_api_allowed"] is False

    schema_catalog = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    assert any(schema["schema_id"] == "SCHEMA-DEVPL-GAP-ACTION-MAP-V1" for schema in schema_catalog["schemas"])

    tcr_v2 = json.loads((ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8"))
    contracts = {contract["contract_id"]: contract for contract in tcr_v2["contracts"]}
    assert contracts["post-h-031-gap-action-map"]["domain"] == "operations.observability"
    assert contracts["post-h-031-gap-action-application-api"]["domain"] == "application.service"
