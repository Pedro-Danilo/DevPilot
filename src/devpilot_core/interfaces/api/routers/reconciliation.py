from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService
from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["reconciliation"])


class ReconciliationMutationBody(BaseModel):
    execute: bool = False
    confirmation: str = Field(default="", max_length=128)


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


def _identity(request: Request, service: ApplicationService, *, operation: str):
    principal = getattr(request.state, "authenticated_principal", None)
    session = getattr(request.state, "authenticated_session_context", None)
    if principal is None or session is None:
        return None, _json({"operation":operation,"ok":False,"exit_code":4,"message":"Authenticated human session is required.","data":{},"findings":[{"id":"AUTH_HUMAN_SESSION_REQUIRED_BLOCK","severity":"block","message":"Reconciliation operations require server-authenticated human context."}]}, 401)
    roles = list(service.rbac.canonical_roles(principal))
    return {"actor": principal.actor_id, "roles": roles, "workspace_scopes": list(principal.workspace_scopes), "session_created_at": session.created_at, "rotation_counter": session.rotation_counter}, None


@router.get("/api/v1/reconciliation")
def reconciliation_status(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="reconciliation.status")
    if error: return error
    return _json(*dispatch_application_request(service, operation="reconciliation.status", payload=identity))


@router.post("/api/v1/reconciliation/baseline")
def reconciliation_baseline(request: Request, body: ReconciliationMutationBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="reconciliation.baseline")
    if error: return error
    return _json(*dispatch_application_request(service, operation="reconciliation.baseline", payload={**identity, "execute":body.execute, "confirmation":body.confirmation}))


@router.post("/api/v1/reconciliation/adopt")
def reconciliation_adopt(request: Request, body: ReconciliationMutationBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="reconciliation.adopt")
    if error: return error
    return _json(*dispatch_application_request(service, operation="reconciliation.adopt", payload={**identity, "execute":body.execute, "confirmation":body.confirmation}))
