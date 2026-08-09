from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import ApiApplicationRequest, dispatch_application_request

router = APIRouter(tags=["workspace-edits"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


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
