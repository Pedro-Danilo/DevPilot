from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService
from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["release"])


class ReleasePackagePlanBody(BaseModel):
    dry_run: bool = True


class ReleasePackageExecuteBody(BaseModel):
    plan_id: str = Field(min_length=1, max_length=160)
    plan_hash: str = Field(min_length=64, max_length=64)


class ReleaseLifecycleExecuteBody(BaseModel):
    plan_id: str = Field(min_length=1, max_length=180)
    plan_hash: str = Field(min_length=64, max_length=64)


class ReleaseMetadataPrepareBody(BaseModel):
    mode: str = Field(default="MANUAL", min_length=1, max_length=32)
    version: str = Field(min_length=1, max_length=80)
    manual_notes: str = Field(default="", max_length=20000)
    agent_proposal: str = Field(default="", max_length=20000)


class ReleaseMetadataApprovalBody(BaseModel):
    plan_id: str = Field(min_length=1, max_length=200)
    plan_hash: str = Field(min_length=64, max_length=64)
    reason: str = Field(default="Reviewed release metadata and exact TagPlan.", min_length=1, max_length=1000)
    ttl_minutes: int = Field(default=30, ge=5, le=120)


class ReleaseMetadataTagExecuteBody(BaseModel):
    plan_id: str = Field(min_length=1, max_length=200)
    plan_hash: str = Field(min_length=64, max_length=64)
    approval_id: str = Field(min_length=1, max_length=200)


class ReleaseClosureFinalizeBody(BaseModel):
    graph_hash: str = Field(min_length=64, max_length=64)


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


def _identity(request: Request, service: ApplicationService, *, operation: str):
    principal = getattr(request.state, "authenticated_principal", None)
    session = getattr(request.state, "authenticated_session_context", None)
    if principal is None or session is None:
        return None, _json(
            {
                "operation": operation,
                "ok": False,
                "exit_code": 4,
                "message": "Authenticated human session is required.",
                "data": {},
                "findings": [{"id": "AUTH_HUMAN_SESSION_REQUIRED_BLOCK", "severity": "block", "message": "Release workbench requires server-authenticated human context."}],
            },
            401,
        )
    roles = list(service.rbac.canonical_roles(principal))
    if not roles:
        return None, _json(
            {
                "operation": operation,
                "ok": False,
                "exit_code": 4,
                "message": "Authenticated principal has no canonical role.",
                "data": {},
                "findings": [{"id": "RBAC_ROLE_REQUIRED_BLOCK", "severity": "block", "message": "Release workbench requires a canonical role."}],
            },
            403,
        )
    return {"principal": principal, "roles": roles, "scopes": list(principal.workspace_scopes)}, None


def _identity_payload(identity: dict[str, Any]) -> dict[str, Any]:
    return {"actor": identity["principal"].actor_id, "actor_roles": identity["roles"], "workspace_scopes": identity["scopes"]}


@router.get("/api/v1/release/readiness")
def release_readiness(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.readiness")
    if error:
        return error
    return _json(*dispatch_application_request(service, operation="release.readiness", payload=_identity_payload(identity)))


@router.get("/api/v1/release/package")
def release_package_status(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.package.status")
    if error:
        return error
    return _json(*dispatch_application_request(service, operation="release.package.status", payload=_identity_payload(identity)))


@router.post("/api/v1/release/package/plan")
def release_package_plan(request: Request, body: ReleasePackagePlanBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.package.plan")
    if error:
        return error
    return _json(*dispatch_application_request(service, operation="release.package.plan", payload=_identity_payload(identity)))


@router.post("/api/v1/release/package/execute")
def release_package_execute(request: Request, body: ReleasePackageExecuteBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.package.execute")
    if error:
        return error
    return _json(*dispatch_application_request(service, operation="release.package.execute", payload={**_identity_payload(identity), "plan_id": body.plan_id, "plan_hash": body.plan_hash}))

@router.get("/api/v1/release/lifecycle")
def release_lifecycle_status(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.lifecycle.status")
    if error: return error
    return _json(*dispatch_application_request(service, operation="release.lifecycle.status", payload=_identity_payload(identity)))


@router.post("/api/v1/release/lifecycle/install/plan")
def release_lifecycle_install_plan(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.lifecycle.install.plan")
    if error: return error
    return _json(*dispatch_application_request(service, operation="release.lifecycle.install.plan", payload=_identity_payload(identity)))


@router.post("/api/v1/release/lifecycle/install/execute")
def release_lifecycle_install_execute(request: Request, body: ReleaseLifecycleExecuteBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.lifecycle.install.execute")
    if error: return error
    return _json(*dispatch_application_request(service, operation="release.lifecycle.install.execute", payload={**_identity_payload(identity), "plan_id": body.plan_id, "plan_hash": body.plan_hash}))


@router.post("/api/v1/release/lifecycle/upgrade/plan")
def release_lifecycle_upgrade_plan(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.lifecycle.upgrade.plan")
    if error: return error
    return _json(*dispatch_application_request(service, operation="release.lifecycle.upgrade.plan", payload=_identity_payload(identity)))


@router.post("/api/v1/release/lifecycle/upgrade/execute")
def release_lifecycle_upgrade_execute(request: Request, body: ReleaseLifecycleExecuteBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.lifecycle.upgrade.execute")
    if error: return error
    return _json(*dispatch_application_request(service, operation="release.lifecycle.upgrade.execute", payload={**_identity_payload(identity), "plan_id": body.plan_id, "plan_hash": body.plan_hash}))


@router.post("/api/v1/release/lifecycle/rollback/plan")
def release_lifecycle_rollback_plan(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.lifecycle.rollback.plan")
    if error: return error
    return _json(*dispatch_application_request(service, operation="release.lifecycle.rollback.plan", payload=_identity_payload(identity)))


@router.post("/api/v1/release/lifecycle/rollback/execute")
def release_lifecycle_rollback_execute(request: Request, body: ReleaseLifecycleExecuteBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.lifecycle.rollback.execute")
    if error: return error
    return _json(*dispatch_application_request(service, operation="release.lifecycle.rollback.execute", payload={**_identity_payload(identity), "plan_id": body.plan_id, "plan_hash": body.plan_hash}))

@router.get("/api/v1/release/metadata")
def release_metadata_status(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.metadata.status")
    if error: return error
    return _json(*dispatch_application_request(service, operation="release.metadata.status", payload=_identity_payload(identity)))


@router.post("/api/v1/release/metadata/prepare")
def release_metadata_prepare(request: Request, body: ReleaseMetadataPrepareBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.metadata.prepare")
    if error: return error
    return _json(*dispatch_application_request(service, operation="release.metadata.prepare", payload={**_identity_payload(identity), "mode": body.mode, "version": body.version, "manual_notes": body.manual_notes, "agent_proposal": body.agent_proposal}))


@router.post("/api/v1/release/metadata/tag-plan")
def release_metadata_tag_plan(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.metadata.tag-plan")
    if error: return error
    return _json(*dispatch_application_request(service, operation="release.metadata.tag-plan", payload=_identity_payload(identity)))


@router.post("/api/v1/release/metadata/approve")
def release_metadata_approve(request: Request, body: ReleaseMetadataApprovalBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.metadata.approve")
    if error: return error
    return _json(*dispatch_application_request(service, operation="release.metadata.approve", payload={**_identity_payload(identity), "plan_id": body.plan_id, "plan_hash": body.plan_hash, "reason": body.reason, "ttl_minutes": body.ttl_minutes}))


@router.post("/api/v1/release/metadata/tag/execute")
def release_metadata_tag_execute(request: Request, body: ReleaseMetadataTagExecuteBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.metadata.tag.execute")
    if error: return error
    return _json(*dispatch_application_request(service, operation="release.metadata.tag.execute", payload={**_identity_payload(identity), "plan_id": body.plan_id, "plan_hash": body.plan_hash, "approval_id": body.approval_id}))

@router.get("/api/v1/release/closure")
def release_closure_status(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.closure.status")
    if error: return error
    return _json(*dispatch_application_request(service, operation="release.closure.status", payload=_identity_payload(identity)))


@router.post("/api/v1/release/closure/finalize")
def release_closure_finalize(request: Request, body: ReleaseClosureFinalizeBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service, operation="release.closure.finalize")
    if error: return error
    return _json(*dispatch_application_request(service, operation="release.closure.finalize", payload={**_identity_payload(identity), "graph_hash": body.graph_hash}))

