from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import ApiApplicationRequest, dispatch_application_request

router = APIRouter(tags=["workspace-edits"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


class ApplyApprovalRequestBody(BaseModel):
    plan_hash: str
    actor: str = Field(default="local-owner", min_length=1, max_length=128)
    reason: str = Field(min_length=3, max_length=1000)
    ttl_minutes: int = Field(default=15, ge=1, le=30)


class ApplyRequestBody(BaseModel):
    plan_hash: str
    approval_id: str = Field(min_length=1, max_length=128)
    actor: str = Field(default="local-owner", min_length=1, max_length=128)


class RollbackApprovalRequestBody(BaseModel):
    actor: str = Field(default="local-owner", min_length=1, max_length=128)
    reason: str = Field(min_length=3, max_length=1000)
    ttl_minutes: int = Field(default=15, ge=1, le=30)


class RollbackRequestBody(BaseModel):
    approval_id: str = Field(min_length=1, max_length=128)
    actor: str = Field(default="local-owner", min_length=1, max_length=128)


@router.post("/api/v1/workspace/edit-plans/plan")
def workspace_edit_plan(
    request: ApiApplicationRequest,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.edits.plan", request=request))


@router.get("/api/v1/workspace/edit-plans/{plan_id}")
def workspace_edit_plan_status(
    plan_id: str,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.edits.status", payload={"plan_id": plan_id}))


@router.post("/api/v1/workspace/edit-plans/{plan_id}/recheck")
def workspace_edit_plan_recheck(
    plan_id: str,
    request: ApiApplicationRequest,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    payload = dict(request.payload or {})
    payload["plan_id"] = plan_id
    forwarded = ApiApplicationRequest(operation=request.operation, payload=payload, client=request.client, dry_run=request.dry_run)
    return _json(*dispatch_application_request(service, operation="workspace.edits.recheck", request=forwarded))


@router.post("/api/v1/workspace/edit-plans/{plan_id}/approval-request")
def workspace_edit_apply_approval_request(
    plan_id: str,
    body: ApplyApprovalRequestBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.edits.approval_request", payload={"plan_id": plan_id, **body.model_dump()}))


@router.post("/api/v1/workspace/edit-plans/{plan_id}/apply")
def workspace_edit_apply(
    plan_id: str,
    body: ApplyRequestBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.edits.apply", payload={"plan_id": plan_id, **body.model_dump()}))


@router.get("/api/v1/workspace/edit-executions/{execution_id}")
def workspace_edit_execution_status(
    execution_id: str,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.edits.execution_status", payload={"execution_id": execution_id}))


@router.post("/api/v1/workspace/edit-executions/{execution_id}/rollback-approval-request")
def workspace_edit_rollback_approval_request(
    execution_id: str,
    body: RollbackApprovalRequestBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.edits.rollback_approval_request", payload={"execution_id": execution_id, **body.model_dump()}))


@router.post("/api/v1/workspace/edit-executions/{execution_id}/rollback")
def workspace_edit_rollback(
    execution_id: str,
    body: RollbackRequestBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.edits.rollback", payload={"execution_id": execution_id, **body.model_dump()}))
