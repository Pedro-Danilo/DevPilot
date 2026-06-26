from __future__ import annotations

from pathlib import Path

from devpilot_core.application import (
    APPLICATION_CLI_BOUNDARY_INTEGRATION_REPORT_ID,
    POST_H_007_E_CREATED_BY,
    CliApplicationBoundaryIntegrationReportBuilder,
    application_cli_boundary_integration_report,
)
from devpilot_core.cli_models import ExitCode, Severity
from devpilot_core.cli_registry import DeclarativeCliRegistryBuilder
from devpilot_core.quality import QualityGate, QualityGateOptions

ROOT = Path(__file__).resolve().parents[1]


def _commands_by_id() -> dict[str, dict]:
    registry = DeclarativeCliRegistryBuilder(ROOT).build_registry().to_dict()
    return {
        command["command_id"]: command
        for group in registry["groups"]
        for command in group["commands"]
    }


def test_post_h_007_e_report_links_cli_registry_to_application_operations() -> None:
    report = application_cli_boundary_integration_report(ROOT)

    assert report["report_id"] == APPLICATION_CLI_BOUNDARY_INTEGRATION_REPORT_ID
    assert report["created_by"] == POST_H_007_E_CREATED_BY
    assert report["status"] == "implemented-initial"
    assert report["summary"]["commands_total"] >= 120
    assert report["summary"]["registered_commands_total"] >= 20
    assert report["summary"]["registered_commands_with_operation_mapping_total"] >= 3
    assert report["summary"]["api_ui_operations_without_contract_total"] == 0
    assert report["summary"]["blocking_findings_total"] == 0
    assert report["summary"]["quality_gate_hardening_bound"] is True
    assert report["summary"]["runtime_router_enabled"] is False
    assert report["safety"]["dynamic_handler_loading_enabled"] is False

    links = {item["command_id"]: item for item in report["command_operation_links"]}
    assert links["workspace.status"]["operation_id"] == "workspace.status"
    assert links["workspace.status"]["maps_to_catalog"] is True
    assert links["validate"]["operation_id"] == "validation.gateway"
    assert links["standards.status"]["operation_id"] == "standards.status"


def test_post_h_007_e_registered_commands_can_carry_operation_id_metadata() -> None:
    commands = _commands_by_id()

    assert commands["workspace.status"]["metadata"]["application_operation_id"] == "workspace.status"
    assert commands["workspace.status"]["metadata"]["application_operation_mapping_status"] == "mapped-initial"
    assert commands["validate"]["metadata"]["application_operation_id"] == "validation.gateway"
    assert commands["standards.status"]["metadata"]["application_operation_id"] == "standards.status"
    assert commands["workspace.list"]["metadata"]["application_operation_mapping_warning"] is True


def test_post_h_007_e_command_result_uses_warnings_without_blocking() -> None:
    result = CliApplicationBoundaryIntegrationReportBuilder(ROOT).run()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["blocking_findings_total"] == 0
    assert result.data["summary"]["warnings_total"] >= 1
    assert any(finding.severity == Severity.WARNING for finding in result.findings)


def test_post_h_007_e_hardening_quality_gate_contains_subgate_and_stays_pass() -> None:
    result = QualityGate(ROOT, options=QualityGateOptions(profile="hardening")).run()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    subgates = {item["id"]: item for item in result.data["subgates"]}
    assert "application-cli-boundary-integration" in subgates
    assert subgates["application-cli-boundary-integration"]["ok"] is True
