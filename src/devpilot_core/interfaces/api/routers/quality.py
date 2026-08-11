from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Path as ApiPath
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService
from devpilot_core.interfaces.api.dependencies import get_application_service
from devpilot_core.interfaces.api.models import dispatch_application_request

router = APIRouter(tags=["quality"])

class TestImpactBody(BaseModel):
    changed_paths: list[str] = Field(min_length=1, max_length=200)

class QualityJobPlanBody(BaseModel):
    operation_id: str = Field(min_length=1, max_length=96)
    workspace_id: str = Field(default="devpilot-local", min_length=1, max_length=256)
    parameters: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=1, max_length=256)
    approval_id: str | None = Field(default=None, max_length=256)
    full_regression_confirmation: str | None = Field(default=None, max_length=64)

class EvidencePackageBody(BaseModel):
    limit: int = Field(default=100, ge=1, le=500)

def _json(result: tuple[dict[str, Any], int]) -> JSONResponse:
    payload, status = result
    return JSONResponse(status_code=200 if isinstance(payload, dict) else status, content=payload)

@router.get("/api/v1/quality/operations")
def operations(service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(dispatch_application_request(service, operation="quality.operations", payload={}))

@router.get("/api/v1/quality/baseline")
def baseline(service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(dispatch_application_request(service, operation="quality.baseline", payload={}))

@router.post("/api/v1/quality/test-impact/plan")
def impact(body: TestImpactBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(dispatch_application_request(service, operation="quality.test_impact_plan", payload=body.model_dump()))

@router.post("/api/v1/quality/jobs/plan")
def plan(body: QualityJobPlanBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(dispatch_application_request(service, operation="quality.jobs.plan", payload=body.model_dump()))

@router.post("/api/v1/quality/jobs/{job_id}/execute")
def execute(job_id: str = ApiPath(min_length=5, max_length=128), service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(dispatch_application_request(service, operation="quality.jobs.execute", payload={"job_id": job_id}))

@router.post("/api/v1/quality/evidence/package")
def evidence(body: EvidencePackageBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(dispatch_application_request(service, operation="quality.evidence_package", payload=body.model_dump()))
