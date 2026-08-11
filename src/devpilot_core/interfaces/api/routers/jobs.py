from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService
from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["jobs"])


class JobControlBody(BaseModel):
    actor: str = Field(default="local-owner", min_length=1, max_length=128)
    reason: str = Field(default="Operator request", min_length=3, max_length=1000)


def _json(result: tuple[dict, int]) -> JSONResponse:
    payload, status = result
    # Governed BLOCK states are product results, not transport failures.
    return JSONResponse(content=payload, status_code=200 if isinstance(payload, dict) else status)


@router.get("/api/v1/jobs")
def list_jobs(
    workspace_id: str | None = Query(default=None, max_length=256),
    capability_id: str | None = Query(default=None, max_length=256),
    status: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(dispatch_application_request(service, operation="jobs.list", payload={"workspace_id": workspace_id, "capability_id": capability_id, "status": status, "limit": limit, "offset": offset}))


@router.get("/api/v1/jobs/{job_id}")
def inspect_job(job_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(dispatch_application_request(service, operation="jobs.inspect", payload={"job_id": job_id}))


@router.get("/api/v1/jobs/{job_id}/logs")
def job_logs(job_id: str, cursor: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=500), service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(dispatch_application_request(service, operation="jobs.logs", payload={"job_id": job_id, "cursor": cursor, "limit": limit}))


@router.post("/api/v1/jobs/{job_id}/cancel")
def cancel_job(job_id: str, body: JobControlBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(dispatch_application_request(service, operation="jobs.cancel", payload={"job_id": job_id, **body.model_dump()}))


@router.post("/api/v1/jobs/{job_id}/retry")
def retry_job(job_id: str, body: JobControlBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(dispatch_application_request(service, operation="jobs.retry", payload={"job_id": job_id, **body.model_dump()}))
