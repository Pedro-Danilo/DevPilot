from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationRequest, ApplicationResponse, ApplicationService
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity


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
    result = CommandResult(
        command="api request",
        ok=False,
        exit_code=ExitCode.BLOCK if severity == Severity.BLOCK else ExitCode.FAIL,
        message=message,
        data={"summary": {"operation": operation, "status_hint": status_hint, "preliminary": True}},
        findings=[Finding(id=finding_id, message=message, severity=severity, metadata={"operation": operation})],
    )
    response = ApplicationResponse.from_command_result(result, operation=operation)
    return response.to_dict(), status_hint


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
        return error_response(
            operation=operation,
            message="Request operation does not match the endpoint contract.",
            finding_id="API_OPERATION_MISMATCH_BLOCK",
            severity=Severity.BLOCK,
            status_hint=403,
        )
    app_request = request.as_application_request(operation=operation, payload=payload) if request else ApplicationRequest(operation=operation, payload=payload or {}, client="api-local", dry_run=True)
    app_response = service.handle(app_request)
    if app_response.ok:
        return app_response.to_dict(), 200
    if app_response.exit_code == int(ExitCode.BLOCK):
        return app_response.to_dict(), 403
    if app_response.exit_code == int(ExitCode.ERROR):
        return app_response.to_dict(), 500
    return app_response.to_dict(), 400
