from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from devpilot_core.application import ApplicationResponse
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

POST_H_014_B_CREATED_BY = "POST-H-014-B"
APPLICATION_RESPONSE_CONTRACT = "DevPilotApplicationResponse"


@dataclass(frozen=True)
class ApiResponseMapping:
    """HTTP mapping for DevPilot local API responses.

    POST-H-014-B makes this mapping explicit so FastAPI routes, security
    middleware and exception handlers do not re-implement status-code semantics.
    It is local-first, deterministic and does not call network/external APIs.
    """

    pass_status: int = 200
    fail_status: int = 400
    block_status: int = 403
    error_status: int = 500
    validation_status: int = 422
    unauthorized_status: int = 401
    not_found_status: int = 404


DEFAULT_API_RESPONSE_MAPPING = ApiResponseMapping()


def http_status_for_exit_code(exit_code: int | ExitCode, *, mapping: ApiResponseMapping = DEFAULT_API_RESPONSE_MAPPING) -> int:
    """Map DevPilot `ExitCode` values to stable HTTP status codes."""

    value = int(exit_code)
    if value == int(ExitCode.PASS):
        return mapping.pass_status
    if value == int(ExitCode.BLOCK):
        return mapping.block_status
    if value == int(ExitCode.ERROR):
        return mapping.error_status
    return mapping.fail_status


def command_result_to_api_response(
    result: CommandResult,
    *,
    operation: str | None = None,
    mapping: ApiResponseMapping = DEFAULT_API_RESPONSE_MAPPING,
) -> tuple[dict[str, Any], int]:
    """Convert a `CommandResult` to `(ApplicationResponse payload, HTTP status)`.

    The payload preserves the existing `ApplicationResponse` envelope while the
    HTTP status is derived from the DevPilot exit code. BLOCK is never reported
    as HTTP 200; technical ERROR is never collapsed into FAIL.
    """

    response = ApplicationResponse.from_command_result(result, operation=operation)
    return response.to_dict(), http_status_for_exit_code(result.exit_code, mapping=mapping)


def sanitized_exception_summary(exc: BaseException) -> dict[str, Any]:
    """Return safe diagnostic metadata without stack traces or raw exception text."""

    return {
        "exception_type": exc.__class__.__name__,
        "stack_trace_redacted": True,
        "raw_exception_message_redacted": True,
        "preliminary": True,
        "created_by": POST_H_014_B_CREATED_BY,
    }


def api_error_response(
    *,
    operation: str,
    message: str,
    finding_id: str,
    severity: Severity = Severity.FAIL,
    status_hint: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], int]:
    """Build a normalized API error response using `ApplicationResponse`."""

    exit_code = ExitCode.BLOCK if severity == Severity.BLOCK else ExitCode.ERROR if severity == Severity.ERROR else ExitCode.FAIL
    resolved_status = status_hint if status_hint is not None else http_status_for_exit_code(exit_code)
    result = CommandResult(
        command="api response mapping",
        ok=False,
        exit_code=exit_code,
        message=message,
        data={
            "summary": {
                "operation": operation,
                "status_hint": resolved_status,
                "preliminary": True,
                "created_by": POST_H_014_B_CREATED_BY,
                **(metadata or {}),
            }
        },
        findings=[Finding(id=finding_id, message=message, severity=severity, metadata={"operation": operation})],
    )
    response = ApplicationResponse.from_command_result(result, operation=operation)
    return response.to_dict(), resolved_status


def operation_mismatch_response(*, expected_operation: str) -> tuple[dict[str, Any], int]:
    return api_error_response(
        operation=expected_operation,
        message="Request operation does not match the endpoint contract.",
        finding_id="API_OPERATION_MISMATCH_BLOCK",
        severity=Severity.BLOCK,
        status_hint=DEFAULT_API_RESPONSE_MAPPING.block_status,
    )


def validation_error_response(*, operation: str = "api.request.validation", errors_total: int = 0) -> tuple[dict[str, Any], int]:
    return api_error_response(
        operation=operation,
        message="HTTP request validation failed for the local API contract.",
        finding_id="API_REQUEST_VALIDATION_FAIL",
        severity=Severity.FAIL,
        status_hint=DEFAULT_API_RESPONSE_MAPPING.validation_status,
        metadata={"validation_errors_total": errors_total, "request_body_redacted": True},
    )


def http_exception_response(*, operation: str, status_code: int, detail: str | None = None) -> tuple[dict[str, Any], int]:
    severity = Severity.BLOCK if status_code in {401, 403} else Severity.FAIL
    finding_id = "API_HTTP_EXCEPTION_BLOCK" if severity == Severity.BLOCK else "API_HTTP_EXCEPTION_FAIL"
    safe_message = detail if detail and status_code < 500 else "HTTP error returned by local API."
    return api_error_response(
        operation=operation,
        message=safe_message,
        finding_id=finding_id,
        severity=severity,
        status_hint=status_code,
        metadata={"http_status": status_code, "detail_redacted": status_code >= 500},
    )


def unhandled_exception_response(*, operation: str, exc: BaseException) -> tuple[dict[str, Any], int]:
    return api_error_response(
        operation=operation,
        message="Unexpected local API error. Technical details were redacted.",
        finding_id="API_UNHANDLED_EXCEPTION_ERROR",
        severity=Severity.ERROR,
        status_hint=DEFAULT_API_RESPONSE_MAPPING.error_status,
        metadata=sanitized_exception_summary(exc),
    )


def response_mapping_summary() -> dict[str, Any]:
    mapping = DEFAULT_API_RESPONSE_MAPPING
    return {
        "created_by": POST_H_014_B_CREATED_BY,
        "contract": APPLICATION_RESPONSE_CONTRACT,
        "pass_status": mapping.pass_status,
        "fail_status": mapping.fail_status,
        "block_status": mapping.block_status,
        "error_status": mapping.error_status,
        "validation_status": mapping.validation_status,
        "unauthorized_status": mapping.unauthorized_status,
        "not_found_status": mapping.not_found_status,
        "stack_traces_redacted": True,
        "raw_exception_messages_redacted": True,
        "network_used": False,
        "external_api_used": False,
        "preliminary": True,
    }
