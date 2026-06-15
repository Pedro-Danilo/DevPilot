from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import ApiApplicationRequest, dispatch_application_request

router = APIRouter(tags=["dry-run-actions"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


@router.post("/api/v1/review/code")
def review_code(request: ApiApplicationRequest | None = None, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="review.code", request=request or ApiApplicationRequest(operation="review.code", payload={"target": "."})))


@router.post("/api/v1/refactor/plan")
def refactor_plan(request: ApiApplicationRequest | None = None, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="refactor.plan", request=request or ApiApplicationRequest(operation="refactor.plan", payload={"target": ".", "goal": ""})))
