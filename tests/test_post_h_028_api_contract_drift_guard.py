from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode, Severity
from devpilot_core.interfaces.api.contract_drift import ApiContractDriftGuard, ApiContractDriftOptions
from devpilot_core.interfaces.api.contracts import collect_canonical_api_route_keys
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES
from devpilot_core.schemas import SchemaRegistry, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / ".devpilot" / "interfaces" / "api_route_contract_registry.json"
OPENAPI_PATH = ROOT / "docs" / "07_interfaces" / "openapi_v1.json"


def _registry_payload() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _openapi_payload() -> dict:
    return json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))


def _finding_ids(result) -> set[str]:
    return {finding.id for finding in result.findings}


def test_api_contract_drift_guard_passes_baseline_without_source_mutations() -> None:
    result = ApiContractDriftGuard(ROOT).run()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["api_contract_drift_guard_passed"] is True
    assert summary["blocking_findings_total"] == 0
    assert summary["report_schema_valid"] is True
    assert summary["runtime_routes_total"] == summary["registry_routes_total"]
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["source_mutations_performed"] is False
    assert result.data["report"]["safety"]["remote_execution_enabled"] is False
    assert result.data["report"]["safety"]["connector_write_enabled"] is False
    assert result.data["report"]["safety"]["plugin_execution_enabled"] is False


def test_api_contract_drift_guard_writes_schema_valid_report_under_explicit_output(tmp_path: Path) -> None:
    result = ApiContractDriftGuard(
        ROOT,
        ApiContractDriftOptions(
            write_report=True,
            output_json=tmp_path / "api_contract_drift_report.json",
            output_markdown=tmp_path / "api_contract_drift_report.md",
        ),
    ).run()

    assert result.ok is True
    assert (tmp_path / "api_contract_drift_report.json").is_file()
    assert (tmp_path / "api_contract_drift_report.md").is_file()
    payload = json.loads((tmp_path / "api_contract_drift_report.json").read_text(encoding="utf-8"))
    assert payload["summary"]["reports_written"] is True
    schema_result = SchemaValidator(ROOT).validate_payload(
        schema="ApiContractDriftReport",
        payload=payload,
        instance_label="pytest:api_contract_drift_report",
    )
    assert schema_result.ok is True


def test_api_contract_drift_guard_blocks_unregistered_runtime_route() -> None:
    runtime_keys = collect_canonical_api_route_keys() | {"GET /api/v1/drift/unregistered"}
    result = ApiContractDriftGuard(
        ROOT,
        ApiContractDriftOptions(runtime_route_keys_override=runtime_keys),
    ).run()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert "API_CONTRACT_DRIFT_UNREGISTERED_RUNTIME_ROUTE" in _finding_ids(result)
    assert "API_CONTRACT_DRIFT_RUNTIME_CANONICAL_MISMATCH" in _finding_ids(result)


def test_api_contract_drift_guard_blocks_protected_route_without_policy_binding() -> None:
    registry = _registry_payload()
    new_route = dict(registry["routes"][-1])
    new_route.update(
        {
            "route_id": "api.drift.protected",
            "method": "GET",
            "path": "/api/v1/drift/protected",
            "operation": "drift.protected",
            "public": False,
            "auth_required": True,
            "policy_check_required": True,
            "application_service_required": True,
            "response_contract": "ApplicationResponse",
        }
    )
    registry["routes"] = registry["routes"] + [new_route]
    runtime_keys = collect_canonical_api_route_keys() | {"GET /api/v1/drift/protected"}
    openapi = _openapi_payload()
    openapi.setdefault("paths", {})["/api/v1/drift/protected"] = {"get": {"summary": "Drift fixture"}}

    result = ApiContractDriftGuard(
        ROOT,
        ApiContractDriftOptions(
            registry_payload_override=registry,
            runtime_route_keys_override=runtime_keys,
            static_openapi_payload_override=openapi,
            policy_routes_override=dict(API_ROUTE_POLICIES),
        ),
    ).run()

    assert result.ok is False
    assert "API_CONTRACT_DRIFT_POLICY_BINDING_MISSING" in _finding_ids(result)


def test_api_contract_drift_guard_blocks_static_openapi_extra_path() -> None:
    openapi = _openapi_payload()
    openapi.setdefault("paths", {})["/api/v1/drift/openapi-extra"] = {"get": {"summary": "Extra"}}

    result = ApiContractDriftGuard(
        ROOT,
        ApiContractDriftOptions(static_openapi_payload_override=openapi),
    ).run()

    assert result.ok is False
    assert "API_CONTRACT_DRIFT_OPENAPI_EXTRA_PATH_BLOCK" in _finding_ids(result)


def test_api_contract_drift_guard_blocks_protected_route_without_auth_policy_metadata() -> None:
    registry = _registry_payload()
    protected = next(route for route in registry["routes"] if not route.get("public"))
    for route in registry["routes"]:
        if route.get("route_id") == protected["route_id"]:
            route["auth_required"] = False
            route["policy_check_required"] = False
            break

    result = ApiContractDriftGuard(ROOT, ApiContractDriftOptions(registry_payload_override=registry)).run()

    assert result.ok is False
    assert "API_CONTRACT_DRIFT_PROTECTED_ROUTE_AUTH_POLICY_BLOCK" in _finding_ids(result)


def test_api_contract_drift_schema_registered() -> None:
    result = SchemaRegistry(ROOT).list()
    matches = [schema for schema in result.data["schemas"] if schema["contract"] == "ApiContractDriftReport"]

    assert result.ok is True
    assert len(matches) == 1
    assert matches[0]["path"] == "docs/schemas/api_contract_drift_report.schema.json"


def test_api_contract_drift_findings_keep_no_error_on_baseline() -> None:
    result = ApiContractDriftGuard(ROOT).run()

    assert all(finding.severity != Severity.ERROR for finding in result.findings)
    assert all(finding.id != "API_CONTRACT_DRIFT_REPORT_SCHEMA_SCHEMA_REFERENCE_NOT_FOUND" for finding in result.findings)
