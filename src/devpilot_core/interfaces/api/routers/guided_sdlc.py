from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["guided-sdlc"])


class PreCodeDraftBody(BaseModel):
    mode: str = Field(pattern=r"^(MANUAL|IMPORT)$")
    content: str = Field(min_length=1, max_length=1048576)


class PreCodeApprovalBody(BaseModel):
    reason: str = Field(default="Approve governed pre-code artifact apply.", min_length=3, max_length=1000)


class PreCodeFreezeBody(BaseModel):
    review_id: str = Field(pattern=r"^arev_[0-9a-f]{32}$")
    execution_id: str = Field(pattern=r"^uedit_[0-9a-f]{32}$")


def _pre_code_identity(request: Request, service: ApplicationService):
    principal = getattr(request.state, "authenticated_principal", None)
    session = getattr(request.state, "authenticated_session_context", None)
    if principal is None or session is None:
        return None, _json({"operation":"guided_sdlc.pre_code","ok":False,"exit_code":4,"message":"Authenticated human session is required.","data":{},"findings":[{"id":"AUTH_HUMAN_SESSION_REQUIRED_BLOCK","severity":"block","message":"Pre-code wizard requires server-authenticated human context."}]},401)
    roles = list(service.rbac.canonical_roles(principal))
    role = roles[0] if roles else ""
    if not role:
        return None, _json({"operation":"guided_sdlc.pre_code","ok":False,"exit_code":4,"message":"Authenticated principal has no canonical role.","data":{},"findings":[{"id":"RBAC_ROLE_REQUIRED_BLOCK","severity":"block","message":"Pre-code wizard requires a canonical role."}]},403)
    return {"principal":principal,"session":session,"roles":roles,"role":role,"scopes":list(principal.workspace_scopes)}, None


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


@router.get("/api/v1/guided-sdlc/pre-code")
def guided_pre_code_status(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _pre_code_identity(request, service)
    if error: return error
    assert identity is not None
    return _json(*dispatch_application_request(service, operation="guided_sdlc.pre_code.status", payload={"effective_roles":identity["roles"],"workspace_scopes":identity["scopes"]}))


@router.post("/api/v1/guided-sdlc/pre-code/stages/{stage_id}/draft")
def guided_pre_code_draft(request: Request, stage_id: str, body: PreCodeDraftBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _pre_code_identity(request, service)
    if error: return error
    assert identity is not None
    principal=identity["principal"]
    return _json(*dispatch_application_request(service, operation="guided_sdlc.pre_code.draft", payload={"stage_id":stage_id,"mode":body.mode,"content":body.content,"actor":principal.actor_id,"actor_role":identity["role"],"session_principal":principal.actor_id,"effective_roles":identity["roles"],"workspace_scopes":identity["scopes"]}))


@router.post("/api/v1/guided-sdlc/pre-code/stages/{stage_id}/review")
def guided_pre_code_review(request: Request, stage_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _pre_code_identity(request, service)
    if error: return error
    assert identity is not None
    principal=identity["principal"]
    return _json(*dispatch_application_request(service, operation="guided_sdlc.pre_code.review", payload={"stage_id":stage_id,"actor":principal.actor_id,"actor_role":identity["role"],"session_principal":principal.actor_id,"effective_roles":identity["roles"]}))


@router.post("/api/v1/guided-sdlc/pre-code/stages/{stage_id}/approval-request")
def guided_pre_code_approval_request(request: Request, stage_id: str, body: PreCodeApprovalBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _pre_code_identity(request, service)
    if error: return error
    assert identity is not None
    principal=identity["principal"]
    return _json(*dispatch_application_request(service, operation="guided_sdlc.pre_code.approval_request", payload={"stage_id":stage_id,"actor":principal.actor_id,"actor_role":identity["role"],"session_principal":principal.actor_id,"effective_roles":identity["roles"],"reason":body.reason}))


@router.post("/api/v1/guided-sdlc/pre-code/stages/{stage_id}/apply")
def guided_pre_code_apply(request: Request, stage_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _pre_code_identity(request, service)
    if error: return error
    assert identity is not None
    principal=identity["principal"]
    return _json(*dispatch_application_request(service, operation="guided_sdlc.pre_code.apply", payload={"stage_id":stage_id,"actor":principal.actor_id,"actor_role":identity["role"],"session_principal":principal.actor_id,"effective_roles":identity["roles"]}))


@router.post("/api/v1/guided-sdlc/pre-code/stages/{stage_id}/freeze")
def guided_pre_code_freeze(request: Request, stage_id: str, body: PreCodeFreezeBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _pre_code_identity(request, service)
    if error: return error
    assert identity is not None
    principal=identity["principal"]
    return _json(*dispatch_application_request(service, operation="guided_sdlc.pre_code.freeze", payload={"stage_id":stage_id,"review_id":body.review_id,"execution_id":body.execution_id,"actor":principal.actor_id,"actor_role":identity["role"],"session_principal":principal.actor_id,"effective_roles":identity["roles"],"workspace_scopes":identity["scopes"]}))


@router.get("/api/v1/guided-sdlc/pre-code/readiness")
def guided_pre_code_readiness(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _pre_code_identity(request, service)
    if error: return error
    assert identity is not None
    return _json(*dispatch_application_request(service, operation="guided_sdlc.pre_code.readiness", payload={"effective_roles":identity["roles"],"workspace_scopes":identity["scopes"]}))
