from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService
from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["recovery"])


class RecoveryPendingWorkBody(BaseModel):
    work_id: str = Field(min_length=1, max_length=256, pattern=r"^[A-Za-z0-9_.:-]+$")
    kind: str = Field(default="work", min_length=1, max_length=64)
    status: str = Field(default="PENDING", min_length=1, max_length=64)
    sensitive: bool = False
    safe_to_resume: bool = False
    approval_id: str | None = Field(default=None, max_length=256)
    approval_actor: str | None = Field(default=None, max_length=256)
    approval_expires_at: str | None = Field(default=None, max_length=64)
    bound_git_head: str | None = Field(default=None, max_length=64)


class RecoveryCheckpointBody(BaseModel):
    draft_refs: list[str] = Field(default_factory=list, max_length=100)
    pending_work: list[RecoveryPendingWorkBody] = Field(default_factory=list, max_length=100)
    evidence_refs: list[str] = Field(default_factory=list, max_length=100)
    recovery_reason: str = Field(default="manual-checkpoint", min_length=3, max_length=256)


class LockAcquireBody(BaseModel):
    action_id: str = Field(min_length=1, max_length=256, pattern=r"^[A-Za-z0-9_.:-]+$")
    sensitive: bool = True
    ttl_seconds: int = Field(default=300, ge=30, le=3600)


class LockActionBody(BaseModel):
    action_id: str = Field(min_length=1, max_length=256, pattern=r"^[A-Za-z0-9_.:-]+$")


class LockRecoverBody(LockActionBody):
    confirmation: str = Field(pattern=r"^RECOVER_STALE_LOCK$")


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


def _identity(request: Request, service: ApplicationService, *, operation: str):
    principal = getattr(request.state, "authenticated_principal", None)
    session = getattr(request.state, "authenticated_session_context", None)
    if principal is None or session is None:
        return None, _json({"operation":operation,"ok":False,"exit_code":4,"message":"Authenticated human session is required.","data":{},"findings":[{"id":"AUTH_HUMAN_SESSION_REQUIRED_BLOCK","severity":"block","message":"Recovery operations require server-authenticated human context."}]}, 401)
    roles = list(service.rbac.canonical_roles(principal))
    return {
        "actor": principal.actor_id,
        "roles": roles,
        "workspace_scopes": list(principal.workspace_scopes),
        "session_created_at": session.created_at,
        "rotation_counter": session.rotation_counter,
    }, None


@router.get("/api/v1/recovery")
def recovery_status(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="recovery.status")
    if error: return error
    return _json(*dispatch_application_request(service, operation="recovery.status", payload=identity))


@router.post("/api/v1/recovery/checkpoint")
def recovery_checkpoint(request: Request, body: RecoveryCheckpointBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="recovery.checkpoint")
    if error: return error
    return _json(*dispatch_application_request(service, operation="recovery.checkpoint", payload={**identity, "draft_refs":body.draft_refs, "pending_work":[item.model_dump() for item in body.pending_work], "evidence_refs":body.evidence_refs, "recovery_reason":body.recovery_reason}))


@router.post("/api/v1/recovery/locks/acquire")
def recovery_lock_acquire(request: Request, body: LockAcquireBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="recovery.lock.acquire")
    if error: return error
    return _json(*dispatch_application_request(service, operation="recovery.lock.acquire", payload={**identity, "action_id":body.action_id, "sensitive":body.sensitive, "ttl_seconds":body.ttl_seconds}))


@router.post("/api/v1/recovery/locks/release")
def recovery_lock_release(request: Request, body: LockActionBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="recovery.lock.release")
    if error: return error
    return _json(*dispatch_application_request(service, operation="recovery.lock.release", payload={**identity, "action_id":body.action_id}))


@router.post("/api/v1/recovery/locks/recover")
def recovery_lock_recover(request: Request, body: LockRecoverBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="recovery.lock.recover")
    if error: return error
    return _json(*dispatch_application_request(service, operation="recovery.lock.recover", payload={**identity, "action_id":body.action_id, "confirmation":body.confirmation}))
