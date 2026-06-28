from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.interfaces.api import create_app
from devpilot_core.interfaces.api.models import ApiApplicationRequest, dispatch_application_request
from devpilot_core.interfaces.api.response_mapping import (
    command_result_to_api_response,
    http_status_for_exit_code,
    response_mapping_summary,
    unhandled_exception_response,
    validation_error_response,
)
from devpilot_core.interfaces.api.security import API_TOKEN_HEADER

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "post-h-014-b-token"


class _FakeService:
    def __init__(self, result: CommandResult | None = None, exc: Exception | None = None) -> None:
        self.result = result
        self.exc = exc

    def handle(self, request):  # type: ignore[no-untyped-def]
        if self.exc is not None:
            raise self.exc
        assert self.result is not None
        return self.result


def _client() -> TestClient:
    client = TestClient(create_app(ROOT, api_token=TOKEN))
    client.headers.update({API_TOKEN_HEADER: TOKEN})
    return client


def test_post_h_014_b_exit_code_to_http_status_map_is_explicit() -> None:
    assert http_status_for_exit_code(ExitCode.PASS) == 200
    assert http_status_for_exit_code(ExitCode.FAIL) == 400
    assert http_status_for_exit_code(ExitCode.BLOCK) == 403
    assert http_status_for_exit_code(ExitCode.ERROR) == 500


def test_post_h_014_b_command_result_mapping_preserves_application_response_contract() -> None:
    result = CommandResult(
        command="probe fail",
        ok=False,
        exit_code=ExitCode.FAIL,
        message="Validation failed.",
        data={"summary": {"probe": True}},
        findings=[Finding("PROBE_FAIL", "Probe failed.", Severity.FAIL)],
    )

    payload, status = command_result_to_api_response(result, operation="probe.operation")

    assert status == 400
    assert payload["contract"] == "DevPilotApplicationResponse"
    assert payload["operation"] == "probe.operation"
    assert payload["ok"] is False
    assert payload["exit_code"] == 1
    assert payload["findings"][0]["severity"] == "fail"


def test_post_h_014_b_dispatch_never_reports_block_as_http_success() -> None:
    result = CommandResult(
        command="probe block",
        ok=False,
        exit_code=ExitCode.BLOCK,
        message="Blocked by policy.",
        findings=[Finding("POLICY_BLOCK", "Blocked by policy.", Severity.BLOCK)],
    )

    payload, status = dispatch_application_request(_FakeService(result), operation="probe.block")  # type: ignore[arg-type]

    assert status == 403
    assert payload["contract"] == "DevPilotApplicationResponse"
    assert payload["ok"] is False
    assert payload["exit_code"] == 2


def test_post_h_014_b_dispatch_redacts_technical_exceptions() -> None:
    secret_stack = "Traceback most recent call with sk-proj-secret and filesystem internals"

    payload, status = dispatch_application_request(_FakeService(exc=RuntimeError(secret_stack)), operation="probe.error")  # type: ignore[arg-type]
    rendered = str(payload)

    assert status == 500
    assert payload["contract"] == "DevPilotApplicationResponse"
    assert payload["ok"] is False
    assert payload["exit_code"] == 3
    assert "Unexpected local API error" in payload["message"]
    assert "Traceback" not in rendered
    assert "sk-proj-secret" not in rendered
    assert payload["data"]["summary"]["exception_type"] == "RuntimeError"
    assert payload["data"]["summary"]["stack_trace_redacted"] is True


def test_post_h_014_b_fastapi_validation_errors_are_application_response() -> None:
    response = _client().post("/api/v1/actions/dry-run", json={"strict": "not-a-bool"})
    payload = response.json()

    assert response.status_code == 422
    assert payload["contract"] == "DevPilotApplicationResponse"
    assert payload["ok"] is False
    assert payload["operation"] == "api.request.validation"
    assert payload["data"]["summary"]["request_body_redacted"] is True
    assert "not-a-bool" not in response.text


def test_post_h_014_b_operation_mismatch_uses_block_status_not_success() -> None:
    request = ApiApplicationRequest(operation="other.operation", payload={})

    payload, status = dispatch_application_request(_FakeService(), operation="expected.operation", request=request)  # type: ignore[arg-type]

    assert status == 403
    assert payload["contract"] == "DevPilotApplicationResponse"
    assert payload["findings"][0]["id"] == "API_OPERATION_MISMATCH_BLOCK"


def test_post_h_014_b_health_is_backward_compatible_and_has_application_envelope() -> None:
    response = TestClient(create_app(ROOT, api_token=TOKEN)).get("/api/v1/health")
    payload = response.json()

    assert response.status_code == 200
    assert payload["contract"] == "DevPilotApplicationResponse"
    assert payload["operation"] == "api.health"
    assert payload["ok"] is True
    assert payload["token_required"] is True  # backward-compatible top-level field
    assert payload["data"]["summary"]["post_h_014_b_response_mapping"] is True


def test_post_h_014_b_response_mapping_summary_declares_no_external_surface() -> None:
    summary = response_mapping_summary()

    assert summary["created_by"] == "POST-H-014-B"
    assert summary["contract"] == "DevPilotApplicationResponse"
    assert summary["block_status"] == 403
    assert summary["error_status"] == 500
    assert summary["stack_traces_redacted"] is True
    assert summary["external_api_used"] is False
