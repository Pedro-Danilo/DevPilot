from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from devpilot_core.application import ApplicationService
from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["release"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


def _identity(request: Request, service: ApplicationService):
    principal = getattr(request.state, "authenticated_principal", None)
    session = getattr(request.state, "authenticated_session_context", None)
    if principal is None or session is None:
        return None, _json(
            {
                "operation": "release.readiness",
                "ok": False,
                "exit_code": 4,
                "message": "Authenticated human session is required.",
                "data": {},
                "findings": [
                    {
                        "id": "AUTH_HUMAN_SESSION_REQUIRED_BLOCK",
                        "severity": "block",
                        "message": "Release Readiness requires server-authenticated human context.",
                    }
                ],
            },
            401,
        )
    roles = list(service.rbac.canonical_roles(principal))
    if not roles:
        return None, _json(
            {
                "operation": "release.readiness",
                "ok": False,
                "exit_code": 4,
                "message": "Authenticated principal has no canonical role.",
                "data": {},
                "findings": [
                    {
                        "id": "RBAC_ROLE_REQUIRED_BLOCK",
                        "severity": "block",
                        "message": "Release Readiness requires a canonical role.",
                    }
                ],
            },
            403,
        )
    return {
        "principal": principal,
        "roles": roles,
        "scopes": list(principal.workspace_scopes),
    }, None


@router.get("/api/v1/release/readiness")
def release_readiness(
    request: Request,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    identity, error = _identity(request, service)
    if error:
        return error
    return _json(
        *dispatch_application_request(
            service,
            operation="release.readiness",
            payload={
                "actor": identity["principal"].actor_id,
                "actor_roles": identity["roles"],
                "workspace_scopes": identity["scopes"],
            },
        )
    )
