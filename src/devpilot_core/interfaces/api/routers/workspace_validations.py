from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import ApiApplicationRequest, dispatch_application_request

router = APIRouter(tags=["workspace-validations"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


def _job_json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    """Use HTTP 200 for a completed validation job, even when its gate is BLOCK.

    Transport/auth/path failures retain their HTTP status. Validation findings
    remain authoritative in DevPilotApplicationResponse.ok/exit_code/status so
    the UI can render them instead of converting a governed result into a
    network error.
    """
    data = payload.get("data") if isinstance(payload, dict) else None
    job = data.get("job") if isinstance(data, dict) else None
    return JSONResponse(content=payload, status_code=200 if isinstance(job, dict) else status_code)


@router.post("/api/v1/workspace/validations/plan")
def workspace_validations_plan(
    request: ApiApplicationRequest,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.validations.plan", request=request))


@router.post("/api/v1/workspace/validations/execute")
def workspace_validations_execute(
    request: ApiApplicationRequest,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _job_json(*dispatch_application_request(service, operation="workspace.validations.execute", request=request))


@router.get("/api/v1/workspace/validations/{job_id}")
def workspace_validations_status(
    job_id: str,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _job_json(*dispatch_application_request(service, operation="workspace.validations.status", payload={"job_id": job_id}))


@router.get("/api/v1/workspace/traceability")
def workspace_traceability(
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.traceability"))
