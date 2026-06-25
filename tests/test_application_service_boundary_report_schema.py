from __future__ import annotations

from pathlib import Path

from devpilot_core.application import ApplicationServiceBoundaryReportBuilder
from devpilot_core.schemas import SchemaRegistry, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ID = "SCHEMA-DEVPL-APPLICATION-SERVICE-BOUNDARY-REPORT-V1"


def test_application_service_boundary_report_schema_is_registered() -> None:
    result = SchemaRegistry(ROOT).list()

    assert result.ok is True, result.to_dict()
    schema_ids = {item["schema_id"] for item in result.data["schemas"]}
    assert SCHEMA_ID in schema_ids


def test_application_service_boundary_report_validates_against_schema() -> None:
    report = ApplicationServiceBoundaryReportBuilder(ROOT).build_report()
    result = SchemaValidator(ROOT).validate_payload(schema=SCHEMA_ID, payload=report, instance_label="memory:application-service-boundary-report")

    assert result.ok is True, result.to_dict()
    assert result.data["summary"]["valid"] is True
    assert result.data["summary"]["errors_total"] == 0
    assert report["summary"]["direct_core_bypass_total"] > 0
