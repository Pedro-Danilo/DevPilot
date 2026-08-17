from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request
from ..response_mapping import command_result_to_api_response

router = APIRouter(tags=["approvals"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


class ApprovalRequestBody(BaseModel):
    tool_id: str = Field(default="tests.run")
    action: str = Field(default="execute")
    subject: str = Field(default="pytest")
    actor: str | None = Field(default=None)
    reason: str = Field(default="Requested from DevPilot Approval Center.")
    scope: str | None = None
    expires_at: str | None = None
    ttl_minutes: int = Field(default=60, ge=1, le=1440)


class ApprovalDecisionBody(BaseModel):
    actor: str | None = Field(default=None, description="Deprecated compatibility hint; authenticated session actor is authoritative.")
    reason: str = Field(default="Decision from DevPilot Approval Center.")


@router.get("/api/v1/approvals")
def list_approvals(
    status: str | None = Query(default=None),
    tool_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="approvals.list", payload={"status": status, "tool_id": tool_id, "action": action, "limit": limit}))


@router.get("/api/v1/approvals/{approval_id}")
def show_approval(approval_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="approvals.show", payload={"approval_id": approval_id}))


@router.post("/api/v1/approvals/request")
def request_approval(request: Request, body: ApprovalRequestBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    principal=getattr(request.state,"authenticated_principal",None)
    session=getattr(request.state,"authenticated_session_context",None)
    if principal is None or session is None:
        return _json({"operation":"approvals.request","ok":False,"exit_code":4,"message":"Authenticated human session is required.","data":{},"findings":[{"id":"AUTH_HUMAN_SESSION_REQUIRED_BLOCK","severity":"block","message":"Approval request requires authenticated human session."}]},401)
    result=service.approvals_request_authenticated(
        principal=principal, session=session,
        tool_id=body.tool_id, action=body.action, subject=body.subject,
        caller_actor=body.actor, reason=body.reason, scope=body.scope,
        expires_at=body.expires_at, ttl_minutes=body.ttl_minutes,
        workspace_id=None,
    )
    return _json(*command_result_to_api_response(result,operation="approvals.request"))


def _authenticated_decision(request: Request, service: ApplicationService, *, approval_id: str, decision: str, body: ApprovalDecisionBody) -> JSONResponse:
    principal=getattr(request.state,"authenticated_principal",None)
    session=getattr(request.state,"authenticated_session_context",None)
    if principal is None or session is None:
        return _json({"operation":f"approvals.{decision}","ok":False,"exit_code":4,"message":"Authenticated human session is required.","data":{},"findings":[{"id":"AUTH_HUMAN_SESSION_REQUIRED_BLOCK","severity":"block","message":"Approval decision requires authenticated human session."}]},401)
    result=service.approvals_decide_authenticated(
        approval_id=approval_id,
        decision="approved" if decision=="approve" else "denied",
        principal=principal,
        session=session,
        caller_actor=body.actor,
        reason=body.reason,
    )
    return _json(*command_result_to_api_response(result,operation=f"approvals.{decision}"))


@router.post("/api/v1/approvals/{approval_id}/approve")
def approve_approval(request: Request, approval_id: str, body: ApprovalDecisionBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _authenticated_decision(request,service,approval_id=approval_id,decision="approve",body=body)


@router.post("/api/v1/approvals/{approval_id}/deny")
def deny_approval(request: Request, approval_id: str, body: ApprovalDecisionBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _authenticated_decision(request,service,approval_id=approval_id,decision="deny",body=body)
