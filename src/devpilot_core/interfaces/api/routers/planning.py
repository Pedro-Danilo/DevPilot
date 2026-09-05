from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService
from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["planning"])




class BacklogProposalBody(BaseModel):
    mode: str = Field(pattern=r"^(MANUAL|DERIVED|AGENT)$")
    backlog: dict[str, Any]
    required_requirement_ids: list[str] = Field(default_factory=list, max_length=5000)
    roadmap_milestone_ids: list[str] = Field(default_factory=list, max_length=5000)
    known_adr_ids: list[str] = Field(default_factory=list, max_length=5000)
    known_risk_ids: list[str] = Field(default_factory=list, max_length=5000)
    known_test_intent_ids: list[str] = Field(default_factory=list, max_length=5000)
    source_label: str = Field(default="", max_length=500)


class SprintProposalBody(BaseModel):
    sprint_plan: dict[str, Any]
    backlog: dict[str, Any]
    dependencies: list[dict[str, Any]] = Field(default_factory=list, max_length=5000)
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


@router.get("/api/v1/planning/backlog")
def backlog_status(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    return _json(*dispatch_application_request(service, operation="planning.backlog.status", payload={"effective_roles": identity["roles"]}))


@router.post("/api/v1/planning/backlog/proposals")
def backlog_propose(request: Request, body: BacklogProposalBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    principal = identity["principal"]
    return _json(*dispatch_application_request(service, operation="planning.backlog.propose", payload={"mode":body.mode,"backlog":body.backlog,"required_requirement_ids":body.required_requirement_ids,"roadmap_milestone_ids":body.roadmap_milestone_ids,"known_adr_ids":body.known_adr_ids,"known_risk_ids":body.known_risk_ids,"known_test_intent_ids":body.known_test_intent_ids,"actor_id":principal.actor_id,"actor_role":identity["role"],"source_label":body.source_label}))


@router.post("/api/v1/planning/backlog/review")
def backlog_review(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    return _json(*dispatch_application_request(service, operation="planning.backlog.review", payload={"actor_id":identity["principal"].actor_id,"actor_role":identity["role"]}))


@router.post("/api/v1/planning/backlog/approve")
def backlog_approve(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    return _json(*dispatch_application_request(service, operation="planning.backlog.approve", payload={"actor_id":identity["principal"].actor_id,"actor_role":identity["role"]}))


@router.post("/api/v1/planning/backlog/freeze")
def backlog_freeze(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    return _json(*dispatch_application_request(service, operation="planning.backlog.freeze", payload={"actor_id":identity["principal"].actor_id,"actor_role":identity["role"]}))


@router.get("/api/v1/planning/sprint")
def sprint_status(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    return _json(*dispatch_application_request(service, operation="planning.sprint.status", payload={"effective_roles": identity["roles"]}))


@router.post("/api/v1/planning/sprint/proposals")
def sprint_propose(request: Request, body: SprintProposalBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    return _json(*dispatch_application_request(service, operation="planning.sprint.propose", payload={"sprint_plan":body.sprint_plan,"backlog":body.backlog,"dependencies":body.dependencies,"actor_id":identity["principal"].actor_id,"actor_role":identity["role"]}))


@router.post("/api/v1/planning/sprint/review")
def sprint_review(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    return _json(*dispatch_application_request(service, operation="planning.sprint.review", payload={"actor_id":identity["principal"].actor_id,"actor_role":identity["role"]}))


@router.post("/api/v1/planning/sprint/approve")
def sprint_approve(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    return _json(*dispatch_application_request(service, operation="planning.sprint.approve", payload={"actor_id":identity["principal"].actor_id,"actor_role":identity["role"]}))


@router.post("/api/v1/planning/sprint/freeze")
def sprint_freeze(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    return _json(*dispatch_application_request(service, operation="planning.sprint.freeze", payload={"actor_id":identity["principal"].actor_id,"actor_role":identity["role"]}))


@router.get("/api/v1/planning/closure")
def planning_closure(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _identity(request, service)
    if error: return error
    return _json(*dispatch_application_request(service, operation="planning.closure.status", payload={"effective_roles": identity["roles"]}))
