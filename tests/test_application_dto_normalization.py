from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import (
    APPLICATION_DTO_NORMALIZATION_REPORT_ID,
    POST_H_007_C_CREATED_BY,
    PRIORITY_OPERATION_IDS,
    ApplicationRequest,
    ApplicationResponse,
    ApplicationService,
    application_dto_normalization_report,
    normalize_priority_application_request,
    priority_dto_operation_ids,
)
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _priority_payloads() -> dict[str, dict[str, object]]:
    probe = ROOT / "outputs" / "reports" / "post_h_007_c_dto_probe.json"
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text(
        json.dumps(
            {
                "summary": {"probe": True, "created_by": "POST-H-007-C"},
                "report_paths": ["outputs/reports/post_h_007_c_dto_probe.json"],
                "metadata": {"critical": True},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "workspace.status": {},
        "validation.docs": {},
        "validation.contracts": {},
        "reports.list": {"limit": 5},
        "reports.read": {"report_id": "post_h_007_c_dto_probe", "format": "json"},
        "approvals.list": {"limit": 5},
        "settings.status": {},
        "repo.inventory": {},
        "review.code": {"target": "src/devpilot_core/application/dtos.py"},
        "refactor.plan": {"target": "src/devpilot_core/application/dtos.py", "goal": "Verify DTO boundary normalization", "include_code_review": False},
        "observability.traces": {"limit": 1, "include_events": False, "include_metrics": False},
    }


def test_post_h_007_c_priority_dto_operation_report_matches_backlog() -> None:
    report = application_dto_normalization_report()

    assert report["report_id"] == APPLICATION_DTO_NORMALIZATION_REPORT_ID
    assert report["created_by"] == POST_H_007_C_CREATED_BY
    assert report["status"] == "implemented-initial"
    assert tuple(priority_dto_operation_ids()) == PRIORITY_OPERATION_IDS
    assert [operation["operation_id"] for operation in report["operations"]] == list(PRIORITY_OPERATION_IDS)
    assert report["summary"]["operations_required_total"] == 11
    assert report["summary"]["operations_covered_total"] == 11
    assert report["summary"]["preserves_findings"] is True
    assert report["summary"]["preserves_exit_code"] is True
    assert report["summary"]["preserves_data"] is True
    assert report["summary"]["remote_execution_enabled"] is False
    assert report["summary"]["connector_write_enabled"] is False
    assert report["summary"]["plugin_execution_enabled"] is False
    assert report["summary"]["public_cli_commands_added"] is False


def test_post_h_007_c_priority_operations_return_schema_valid_application_response() -> None:
    service = ApplicationService(ROOT)
    validator = SchemaValidator(ROOT)
    payloads = _priority_payloads()

    try:
        for operation_id in PRIORITY_OPERATION_IDS:
            request = ApplicationRequest(operation=operation_id, payload=payloads[operation_id], client="post-h-007-c-test", dry_run=True)
            response = service.handle(request)
            response_payload = response.to_dict()
            validation = validator.validate_payload(schema="ApplicationResponse", payload=response_payload, instance_label=f"memory:{operation_id}")

            assert isinstance(response, ApplicationResponse)
            assert response.operation == operation_id
            assert response.exit_code in {int(ExitCode.PASS), int(ExitCode.FAIL), int(ExitCode.BLOCK), int(ExitCode.ERROR)}
            assert response_payload["contract"] == "DevPilotApplicationResponse"
            assert response_payload["schema_version"] == "1.0"
            assert isinstance(response_payload["data"], dict)
            assert isinstance(response_payload["findings"], list)
            assert validation.ok is True, validation.to_dict()
            assert validation.data["summary"]["valid"] is True
    finally:
        probe = ROOT / "outputs" / "reports" / "post_h_007_c_dto_probe.json"
        if probe.exists():
            probe.unlink()


def test_post_h_007_c_default_payload_normalization_keeps_user_values() -> None:
    request = ApplicationRequest(operation="observability.traces", payload={"limit": 3, "include_metrics": False}, client="api-local", dry_run=True)

    normalized = normalize_priority_application_request(request)

    assert normalized.operation == "observability.traces"
    assert normalized.client == "api-local"
    assert normalized.dry_run is True
    assert normalized.payload["limit"] == 3
    assert normalized.payload["include_metrics"] is False
    assert normalized.payload["include_events"] is True


def test_application_response_preserves_command_result_exit_findings_and_metadata() -> None:
    result = CommandResult(
        command="post-h-007-c preservation probe",
        ok=False,
        exit_code=ExitCode.BLOCK,
        message="Synthetic preservation probe blocked.",
        data={
            "summary": {"report_paths_total": 1, "metadata_critical": True},
            "report_paths": ["outputs/reports/post_h_007_c_probe.json"],
            "metadata": {"critical": True, "dry_run": True},
        },
        findings=[
            Finding(
                id="POST_H_007_C_PRESERVATION_PROBE",
                message="Synthetic finding metadata must survive ApplicationResponse conversion.",
                severity=Severity.BLOCK,
                metadata={"critical": True, "report_path": "outputs/reports/post_h_007_c_probe.json"},
            )
        ],
    )

    response = ApplicationResponse.from_command_result(result, operation="post_h_007_c.probe")
    payload = response.to_dict()

    assert payload["operation"] == "post_h_007_c.probe"
    assert payload["ok"] is False
    assert payload["exit_code"] == int(ExitCode.BLOCK)
    assert payload["data"]["report_paths"] == ["outputs/reports/post_h_007_c_probe.json"]
    assert payload["data"]["metadata"]["critical"] is True
    assert payload["findings"][0]["id"] == "POST_H_007_C_PRESERVATION_PROBE"
    assert payload["findings"][0]["metadata"]["critical"] is True
    assert payload["findings"][0]["metadata"]["report_path"] == "outputs/reports/post_h_007_c_probe.json"
