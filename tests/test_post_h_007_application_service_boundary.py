from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import ApplicationServiceBoundaryReportBuilder, ApplicationServiceBoundaryReportOptions

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_007_backlog_is_closed_before_post_h_008() -> None:
    backlog = _read("docs/backlogs/POST-H-006_cli_command_registry.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    changelog = _read("docs/release/CHANGELOG.md")
    state = _read_json(".devpilot/project_state.json")

    assert 'implementation_status: "closed"' in backlog
    assert "POST-H-006-E — Gate de no crecimiento monolítico" in backlog
    assert "Estado: `closed`" in backlog
    assert "Último hito: `POST-H-007" in readme
    assert "Siguiente hito: `POST-H-008" in readme
    assert "POST-H-008-A — Runtime state lifecycle" in readme
    assert "POST-H-007-A — Operación del inventario ApplicationService boundary" in runbook
    assert "post-h-007-a" in changelog
    assert state["last_completed_sprint"] == "POST-H-007"
    assert state["next_sprint"] == "POST-H-008"


def test_post_h_007_backlog_is_approved_and_a_is_documented() -> None:
    backlog = _read("docs/backlogs/POST-H-007_application_service_boundary.md")
    interface_doc = _read("docs/07_interfaces/application_service_boundary.md")
    architecture_doc = _read("docs/02_architecture/application_service_boundary_map.md")
    audit = _read("docs/audits/post_h_007_a_application_service_boundary_inventory_report.md")
    manifest = _read_json("docs/post_h_007_a_manifest.json")

    assert 'status: "approved"' in backlog
    assert 'implementation_status: "closed"' in backlog
    assert "POST-H-007-A — Inventario de operaciones y bypasses" in backlog
    assert "Estado: `implemented-initial`" in backlog
    assert "## 17. Cierre del backlog — POST-H-007" in backlog
    assert "ApplicationService boundary" in interface_doc
    assert "direct_core_bypass_total" in interface_doc
    assert "CLI/API/UI" in architecture_doc
    assert "POST-H-007-A" in audit
    assert manifest["id"] == "POST-H-007-A"
    assert manifest["status"] == "implemented-initial"
    assert manifest["parent_backlog"] == "POST-H-007"
    assert manifest["next_micro_sprint"] == "POST-H-007-B"
    assert manifest["remote_execution_enabled"] is False
    assert manifest["connector_write_enabled"] is False
    assert manifest["plugin_execution_enabled"] is False
    assert manifest["source_mutations_performed"] is False


def test_application_service_boundary_report_builder_is_read_only_and_finds_bypasses() -> None:
    result = ApplicationServiceBoundaryReportBuilder(ROOT).run()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    report = result.data["report"]
    assert summary["created_by"] == "POST-H-007-A"
    assert summary["operations_total"] >= 20
    assert summary["application_service_methods_total"] >= 20
    assert summary["domain_services_total"] >= 10
    assert summary["api_routes_total"] >= 10
    assert summary["api_bound_total"] == summary["api_routes_total"]
    assert summary["ui_bound_total"] > 0
    assert summary["cli_commands_total"] >= 130
    assert summary["direct_core_bypass_total"] > 0
    assert summary["high_or_critical_bypass_total"] > 0
    assert summary["critical_bypass_total"] > 0
    assert summary["read_only"] is True
    assert summary["runtime_behavior_changed"] is False
    assert summary["remote_execution_enabled"] is False
    assert summary["connector_write_enabled"] is False
    assert summary["plugin_execution_enabled"] is False
    assert report["safety"]["source_mutations_performed"] is False
    assert any(item["identifier"] == "plugin.dry-run" for item in report["bypasses"])
    assert any(item["operation_id"] == "workspace.status" for item in report["operations"])
    assert any(route["application_service_bound"] is True for route in report["interfaces"]["api"]["routes"])


def test_application_service_boundary_report_writes_expected_artifacts() -> None:
    result = ApplicationServiceBoundaryReportBuilder(ROOT, ApplicationServiceBoundaryReportOptions(write_report=True)).run()

    assert result.ok is True, result.to_dict()
    reports = result.data["reports"]
    assert reports["json"] == "outputs/reports/application_service_boundary_report.json"
    assert reports["markdown"] == "outputs/reports/application_service_boundary_report.md"
    payload = _read_json(reports["json"])
    markdown = _read(reports["markdown"])
    assert payload["summary"]["reports_written"] is True
    assert payload["summary"]["direct_core_bypass_total"] > 0
    assert "POST-H-007-A — ApplicationService boundary report" in markdown


def test_post_h_007_test_contracts_exist_in_v1_and_v2() -> None:
    v1 = _read_json(".devpilot/testing/test_contract_registry.json")
    v2 = _read_json(".devpilot/testing/test_contract_registry_v2.json")
    v1_contracts = {item["contract_id"]: item for item in v1["contracts"]}
    v2_contracts = {item["contract_id"]: item for item in v2["contracts"]}

    assert "post-h-007-application-service-boundary-inventory" in v1_contracts
    assert "post-h-007-application-service-boundary-inventory" in v2_contracts
    assert v1_contracts["post-h-007-application-service-boundary-inventory"]["owner"] == "POST-H-007-A"
    assert v2_contracts["post-h-007-application-service-boundary-inventory"]["capability"] == "ApplicationServiceBoundaryReport"
    assert v2_contracts["post-h-007-application-service-boundary-inventory"]["network_allowed"] is False
    assert v2_contracts["post-h-007-application-service-boundary-inventory"]["source_mutations_allowed"] is False
