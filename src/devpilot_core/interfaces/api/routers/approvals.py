from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["approvals"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


class ApprovalRequestBody(BaseModel):
    tool_id: str = Field(default="tests.run")
    action: str = Field(default="execute")
    subject: str = Field(default="pytest")
    actor: str = Field(default="ui-local")
    reason: str = Field(default="Requested from DevPilot Approval Center.")
    scope: str | None = None
    expires_at: str | None = None
    ttl_minutes: int = Field(default=60, ge=1, le=1440)


class ApprovalDecisionBody(BaseModel):
    actor: str = Field(default="ui-local")
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
def request_approval(body: ApprovalRequestBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="approvals.request", payload=body.model_dump()))


@router.post("/api/v1/approvals/{approval_id}/approve")
def approve_approval(approval_id: str, body: ApprovalDecisionBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    payload = body.model_dump()
    payload["approval_id"] = approval_id
    return _json(*dispatch_application_request(service, operation="approvals.approve", payload=payload))


@router.post("/api/v1/approvals/{approval_id}/deny")
def deny_approval(approval_id: str, body: ApprovalDecisionBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    payload = body.model_dump()
    payload["approval_id"] = approval_id
    return _json(*dispatch_application_request(service, operation="approvals.deny", payload=payload))
