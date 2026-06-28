from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from devpilot_core.application import ApplicationResponse
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

from ..security import API_ROUTE_POLICIES, api_security_posture_summary

router = APIRouter(tags=["security"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


@router.get("/api/v1/security/posture")
def security_posture(request: Request) -> JSONResponse:
    """Return a redacted local API/UI security posture diagnostic.

    POST-H-014-D keeps this endpoint protected by the same token and PolicyEngine
    middleware as other non-public routes. It never returns the raw API token or
    secret values, and it does not start services, touch the network or mutate
    files.
    """

    summary = api_security_posture_summary(
        root=request.app.state.devpilot_root,
        config=request.app.state.api_security,
        routes_total=len([path for path in request.app.openapi().get("paths", {}) if str(path).startswith("/api/v1/")]),
        policy_bound_routes_total=len(API_ROUTE_POLICIES),
    )
    result = CommandResult(
        command="api security posture",
        ok=True,
        exit_code=ExitCode.PASS,
        message="Local API/UI security posture is protected, local-first and redacted.",
        data={"summary": summary},
        findings=[
            Finding(
                id="API_UI_SECURITY_POSTURE_READY",
                message="Security posture diagnostic is protected by token, restricted CORS and policy binding.",
                severity=Severity.INFO,
                metadata={"created_by": "POST-H-014-D", "token_redacted": True},
            )
        ],
    )
    return _json(ApplicationResponse.from_command_result(result, operation="api.security.posture").to_dict(), 200)
