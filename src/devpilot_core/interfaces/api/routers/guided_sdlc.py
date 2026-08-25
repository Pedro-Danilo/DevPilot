from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["guided-sdlc"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


@router.get("/api/v1/guided-sdlc/status")
def guided_sdlc_project_status(
    workspace_id: str | None = Query(default=None, max_length=128),
    expected_state_fingerprint: str | None = Query(default=None, min_length=64, max_length=64),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    """Return sanitized, actor-neutral Project Status and NextAction.

    This endpoint is local/protected and read-only. It delegates all domain
    semantics to ApplicationService -> GuidedSDLCService; no route logic reads
    filesystem/Git or recomputes ProjectStatus.
    """

    observed_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return _json(
        *dispatch_application_request(
            service,
            operation="guided_sdlc.project_status",
            payload={
                "workspace_id": workspace_id,
                "expected_state_fingerprint": expected_state_fingerprint,
                "observed_at_utc": observed_at_utc,
            },
        )
    )


@router.get("/api/v1/guided-sdlc/step-actions")
def guided_sdlc_step_actions(
    request: Request,
    workspace_id: str | None = Query(default=None, max_length=128),
    expected_state_fingerprint: str | None = Query(default=None, min_length=64, max_length=64),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    """Return actor-aware StepActionCards without granting target capabilities."""

    principal = getattr(request.state, "authenticated_principal", None)
    session = getattr(request.state, "authenticated_session_context", None)
    if principal is None or session is None:
        return _json(
            {
                "operation": "guided_sdlc.step_actions",
                "ok": False,
                "exit_code": 4,
                "message": "Authenticated human session is required for Step Action Advisor.",
                "data": {},
                "findings": [{"id": "AUTH_HUMAN_SESSION_REQUIRED_BLOCK", "severity": "block", "message": "Step Action Advisor requires server-authenticated human context."}],
            },
            401,
        )
    effective_roles = list(service.rbac.canonical_roles(principal))
    observed_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return _json(
        *dispatch_application_request(
            service,
            operation="guided_sdlc.step_actions",
            payload={
                "workspace_id": workspace_id,
                "expected_state_fingerprint": expected_state_fingerprint,
                "observed_at_utc": observed_at_utc,
                "effective_roles": effective_roles,
                "workspace_scopes": list(principal.workspace_scopes),
            },
        )
    )
