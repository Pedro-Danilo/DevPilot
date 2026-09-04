from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService
from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["planning"])


class RoadmapProposalBody(BaseModel):
    mode: str = Field(pattern=r"^(MANUAL|IMPORT|AGENT)$")
    roadmap: dict[str, Any]
    required_requirement_ids: list[str] = Field(default_factory=list, max_length=5000)
    required_risk_ids: list[str] = Field(default_factory=list, max_length=5000)
    source_label: str = Field(default="", max_length=500)


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


def _identity(request: Request, service: ApplicationService):
    principal = getattr(request.state, "authenticated_principal", None)
    session = getattr(request.state, "authenticated_session_context", None)
    if principal is None or session is None:
        return None, _json({"operation":"planning.roadmap","ok":False,"exit_code":4,"message":"Authenticated human session is required.","data":{},"findings":[{"id":"AUTH_HUMAN_SESSION_REQUIRED_BLOCK","severity":"block","message":"Roadmap Workbench requires server-authenticated human context."}]}, 401)
    roles = list(service.rbac.canonical_roles(principal))
    role = roles[0] if roles else ""
    if not role:
        return None, _json({"operation":"planning.roadmap","ok":False,"exit_code":4,"message":"Authenticated principal has no canonical role.","data":{},"findings":[{"id":"RBAC_ROLE_REQUIRED_BLOCK","severity":"block","message":"Roadmap Workbench requires a canonical role."}]}, 403)
    return {"principal": principal, "roles": roles, "role": role, "scopes": list(principal.workspace_scopes)}, None


@router.get("/api/v1/planning/roadmap")
def roadmap_status(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    return _json(*dispatch_application_request(service, operation="planning.roadmap.status", payload={"effective_roles": identity["roles"]}))


@router.post("/api/v1/planning/roadmap/proposals")
def roadmap_propose(request: Request, body: RoadmapProposalBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    principal = identity["principal"]
    return _json(*dispatch_application_request(service, operation="planning.roadmap.propose", payload={"mode":body.mode,"roadmap":body.roadmap,"required_requirement_ids":body.required_requirement_ids,"required_risk_ids":body.required_risk_ids,"source_label":body.source_label,"actor_id":principal.actor_id,"actor_role":identity["role"]}))


@router.post("/api/v1/planning/roadmap/review")
def roadmap_review(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    principal = identity["principal"]
    return _json(*dispatch_application_request(service, operation="planning.roadmap.review", payload={"actor_id":principal.actor_id,"actor_role":identity["role"]}))


@router.post("/api/v1/planning/roadmap/approve")
def roadmap_approve(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    principal = identity["principal"]
    return _json(*dispatch_application_request(service, operation="planning.roadmap.approve", payload={"actor_id":principal.actor_id,"actor_role":identity["role"]}))


@router.post("/api/v1/planning/roadmap/freeze")
def roadmap_freeze(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    principal = identity["principal"]
    return _json(*dispatch_application_request(service, operation="planning.roadmap.freeze", payload={"actor_id":principal.actor_id,"actor_role":identity["role"]}))
