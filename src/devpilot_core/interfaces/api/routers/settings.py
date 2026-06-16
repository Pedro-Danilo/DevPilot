from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["settings"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


class ProviderPlanBody(BaseModel):
    provider_id: str = Field(default="mock")
    changes: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(default="ui-local")
    reason: str = Field(default="Settings UI plan-only provider change")


@router.get("/api/v1/settings/workspace")
def settings_workspace(service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="settings.workspace", payload={}))


@router.get("/api/v1/settings/providers")
def settings_providers(prefer_example: bool = Query(default=False), service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="settings.providers", payload={"prefer_example": prefer_example}))


@router.get("/api/v1/settings/policy")
def settings_policy(service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="settings.policy", payload={}))


@router.post("/api/v1/settings/providers/plan")
def settings_provider_plan(body: ProviderPlanBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="settings.providers.plan", payload=body.model_dump()))
