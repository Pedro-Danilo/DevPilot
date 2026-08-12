from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, Path as ApiPath
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from devpilot_core.application import ApplicationService
from devpilot_core.interfaces.api.dependencies import get_application_service
from devpilot_core.interfaces.api.models import dispatch_application_request

router=APIRouter(tags=['ai'])
class AiJobPlanBody(BaseModel):
    operation_id: str = Field(min_length=1,max_length=96)
    workspace_id: str = Field(default='devpilot-local',min_length=1,max_length=256)
    parameters: dict[str,Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=1,max_length=256)
    approval_id: str | None = Field(default=None,max_length=256)
class AiEvidenceBody(BaseModel): limit:int=Field(default=100,ge=1,le=250)
def _json(result: tuple[dict[str,Any],int])->JSONResponse:
    payload,status=result; return JSONResponse(status_code=200 if isinstance(payload,dict) else status,content=payload)
@router.get('/api/v1/ai/operations')
def operations(service:ApplicationService=Depends(get_application_service))->JSONResponse: return _json(dispatch_application_request(service,operation='ai.operations',payload={}))
@router.get('/api/v1/ai/status')
def status(service:ApplicationService=Depends(get_application_service))->JSONResponse: return _json(dispatch_application_request(service,operation='ai.status',payload={}))
@router.post('/api/v1/ai/jobs/plan')
def plan(body:AiJobPlanBody,service:ApplicationService=Depends(get_application_service))->JSONResponse: return _json(dispatch_application_request(service,operation='ai.jobs.plan',payload=body.model_dump()))
@router.post('/api/v1/ai/jobs/{job_id}/execute')
def execute(job_id:str=ApiPath(min_length=5,max_length=128),service:ApplicationService=Depends(get_application_service))->JSONResponse: return _json(dispatch_application_request(service,operation='ai.jobs.execute',payload={'job_id':job_id}))
@router.get('/api/v1/ai/jobs/{job_id}/result')
def result(job_id:str=ApiPath(min_length=5,max_length=128),service:ApplicationService=Depends(get_application_service))->JSONResponse: return _json(dispatch_application_request(service,operation='ai.jobs.result',payload={'job_id':job_id}))
@router.post('/api/v1/ai/evidence/package')
def evidence(body:AiEvidenceBody,service:ApplicationService=Depends(get_application_service))->JSONResponse: return _json(dispatch_application_request(service,operation='ai.evidence_package',payload=body.model_dump()))
