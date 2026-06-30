from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import (
    APPLICATION_OPERATION_CATALOG_ID,
    APPLICATION_OPERATION_CATALOG_SCHEMA_ID,
    POST_H_007_B_CREATED_BY,
    ApplicationCapabilityRegistry,
    ApplicationOperationCatalogBuilder,
    ApplicationOperationCatalogOptions,
)
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_application_operation_catalog_builder_covers_required_domains_and_contracts() -> None:
    catalog = ApplicationOperationCatalogBuilder(ROOT).build_catalog().to_dict()

    assert catalog["catalog_id"] == APPLICATION_OPERATION_CATALOG_ID
    assert catalog["schema_id"] == APPLICATION_OPERATION_CATALOG_SCHEMA_ID
    assert catalog["created_by"] == POST_H_007_B_CREATED_BY
    assert catalog["status"] == "implemented-initial"
    assert catalog["required_initial_domains_missing"] == []
    assert catalog["summary"]["required_initial_domains_covered_total"] == len(catalog["required_initial_domains"])
    assert catalog["summary"]["required_initial_domains_covered_total"] >= 10
    assert "portfolio" in catalog["required_initial_domains"]
    assert catalog["summary"]["operations_total"] >= 30
    assert catalog["summary"]["direct_core_bypass_total"] > 0
    assert catalog["summary"]["operations_without_test_contracts_total"] == 0
    assert catalog["safety"]["read_only"] is True
    assert catalog["safety"]["runtime_behavior_changed"] is False
    assert catalog["safety"]["remote_execution_enabled"] is False
    assert catalog["safety"]["connector_write_enabled"] is False
    assert catalog["safety"]["plugin_execution_enabled"] is False

    operations = {operation["operation_id"]: operation for operation in catalog["operations"]}
    for operation_id in [
        "workspace.status",
        "validation.readiness",
        "reports.list",
        "approvals.list",
        "settings.workspace",
        "repo.inventory",
        "review.code",
        "refactor.plan",
        "model.providers",
        "observability.trace_report",
        "portfolio.status",
    ]:
        assert operation_id in operations
        op = operations[operation_id]
        assert op["request_contract"] == "ApplicationRequest"
        assert op["response_contract"] == "ApplicationResponse"
        assert isinstance(op["cli_commands"], list)
        assert isinstance(op["api_routes"], list)
        assert isinstance(op["ui_surfaces"], list)
        assert op["risk_level"] in {"low", "medium", "high", "critical"}
        assert isinstance(op["writes_files"], bool)
        assert isinstance(op["policy_required"], bool)
        assert op["test_coverage"]["covered"] is True
        assert op["test_contract_ids"]


def test_application_operation_catalog_validates_against_schema_and_writes_reports() -> None:
    result = ApplicationOperationCatalogBuilder(
        ROOT,
        ApplicationOperationCatalogOptions(write_report=True),
    ).run()

    assert result.ok is True, result.to_dict()
    reports = result.data["reports"]
    json_path = ROOT / reports["json"]
    markdown_path = ROOT / reports["markdown"]
    assert json_path.exists()
    assert markdown_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    validation = SchemaValidator(ROOT).validate_payload(
        schema="ApplicationOperationCatalog",
        payload=payload,
        instance_label="memory:application-operation-catalog",
    )
    assert validation.ok is True, validation.to_dict()
    assert validation.data["summary"]["valid"] is True
    assert validation.data["summary"]["errors_total"] == 0


def test_application_capability_registry_lookup_is_read_only_catalog_facade() -> None:
    registry = ApplicationCapabilityRegistry(ROOT)

    operation = registry.get("workspace.status")
    assert operation is not None
    assert operation["operation_id"] == "workspace.status"
    assert operation["domain"] == "workspace"
    assert "workspace.status" in registry.list_operation_ids()
    assert registry.get("missing.operation") is None
