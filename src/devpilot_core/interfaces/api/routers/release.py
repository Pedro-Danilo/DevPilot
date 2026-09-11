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
