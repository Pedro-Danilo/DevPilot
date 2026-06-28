from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationRequest, ApplicationResponse, ApplicationService
from devpilot_core.cli_models import CommandResult, Severity

from .response_mapping import (
    api_error_response,
    command_result_to_api_response,
    http_status_for_exit_code,
    operation_mismatch_response,
    unhandled_exception_response,
)


class ApiApplicationRequest(BaseModel):
    """HTTP request envelope accepted by local API POST routes.

    The transport remains deliberately small. Route handlers pin the operation
    to the endpoint contract and do not allow a request body to switch to a
    different operation.
    """

    operation: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    client: str = "api-local"
    dry_run: bool = True

    def as_application_request(self, *, operation: str, payload: dict[str, Any] | None = None) -> ApplicationRequest:
        merged_payload = dict(payload or {})
        merged_payload.update(dict(self.payload or {}))
        return ApplicationRequest(operation=operation, payload=merged_payload, client=self.client, dry_run=self.dry_run)


def response_dict(response: ApplicationResponse) -> dict[str, Any]:
    return response.to_dict()


def error_response(*, operation: str, message: str, finding_id: str, severity: Severity = Severity.FAIL, status_hint: int = 400) -> tuple[dict[str, Any], int]:
    return api_error_response(
        operation=operation,
        message=message,
        finding_id=finding_id,
        severity=severity,
        status_hint=status_hint,
    )


def dispatch_application_request(
    service: ApplicationService,
    *,
    operation: str,
    request: ApiApplicationRequest | None = None,
    payload: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], int]:
    """Dispatch an API request through ApplicationService and map status code.

    No route handler calls validators/repo/review/model/observability internals
    directly. This is the central Sprint 67 safety boundary.
    """

    if request is not None and request.operation and request.operation != operation:
        return operation_mismatch_response(expected_operation=operation)
    app_request = request.as_application_request(operation=operation, payload=payload) if request else ApplicationRequest(operation=operation, payload=payload or {}, client="api-local", dry_run=True)
    try:
        app_response = service.handle(app_request)
    except Exception as exc:  # defensive transport boundary: never leak stack traces through HTTP payloads
        return unhandled_exception_response(operation=operation, exc=exc)
    if isinstance(app_response, CommandResult):
        return command_result_to_api_response(app_response, operation=operation)
    return app_response.to_dict(), http_status_for_exit_code(app_response.exit_code)
