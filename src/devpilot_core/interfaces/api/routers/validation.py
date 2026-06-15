from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import ApiApplicationRequest, dispatch_application_request

router = APIRouter(tags=["validation"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


@router.post("/api/v1/validation/frontmatter")
def validation_frontmatter(request: ApiApplicationRequest, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="validation.frontmatter", request=request))


@router.post("/api/v1/validation/artifact")
def validation_artifact(request: ApiApplicationRequest, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="validation.artifact", request=request))


@router.post("/api/v1/validation/readiness")
def validation_readiness(request: ApiApplicationRequest | None = None, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="validation.readiness", request=request or ApiApplicationRequest(operation="validation.readiness")))
