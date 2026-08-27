from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request
from ..response_mapping import command_result_to_api_response

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


class ProviderEnablementBody(BaseModel):
    provider_id: str
    access_route_id: str
    workspace_id: str = Field(default="devpilot-local")
    credential_reference: dict[str, Any] = Field(default_factory=dict)
    gate_report: dict[str, Any] = Field(default_factory=dict)
    notices_acknowledged: list[str] = Field(default_factory=list)
    budget_limit_usd: float = Field(default=0.0, ge=0.0)
    approval_id: str | None = None
    requested_mode: str = Field(default="fake")
    reason: str = Field(default="External provider enablement request")
    connectivity_mode: str = Field(default="fake")
    simulation_case: str = Field(default="success")


class ProviderDisableBody(BaseModel):
    provider_id: str
    reason: str = Field(default="Disable external provider")


def _session(request: Request):
    return getattr(request.state, "authenticated_principal", None), getattr(request.state, "authenticated_session_context", None)


@router.get("/api/v1/settings/providers/enablement")
def settings_provider_enablement_status(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    principal, session = _session(request)
    if principal is None or session is None:
        return _json({"operation":"settings.providers.enablement.status","ok":False,"exit_code":4,"message":"Authenticated human session is required.","data":{},"findings":[{"id":"AUTH_HUMAN_SESSION_REQUIRED_BLOCK","severity":"block","message":"Provider enablement status requires authenticated human session."}]},401)
    result=service.settings_provider_enablement_status()
    return _json(*command_result_to_api_response(result,operation="settings.providers.enablement.status"))


@router.post("/api/v1/settings/providers/enablement/plan")
def settings_provider_enablement_plan(request: Request, body: ProviderEnablementBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    principal, session = _session(request)
    if principal is None or session is None:
        return _json({"operation":"settings.providers.enablement.plan","ok":False,"exit_code":4,"message":"Authenticated human session is required.","data":{},"findings":[{"id":"AUTH_HUMAN_SESSION_REQUIRED_BLOCK","severity":"block","message":"Provider enablement plan requires authenticated human session."}]},401)
    result=service.settings_provider_enablement_plan(payload=body.model_dump())
    return _json(*command_result_to_api_response(result,operation="settings.providers.enablement.plan"))


@router.post("/api/v1/settings/providers/connectivity-test")
def settings_provider_connectivity_test(request: Request, body: ProviderEnablementBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    principal, session = _session(request)
    if principal is None or session is None:
        return _json({"operation":"settings.providers.connectivity_test","ok":False,"exit_code":4,"message":"Authenticated human session is required.","data":{},"findings":[{"id":"AUTH_HUMAN_SESSION_REQUIRED_BLOCK","severity":"block","message":"Provider connectivity test requires authenticated human session."}]},401)
    result=service.settings_provider_connectivity_test_authenticated(payload=body.model_dump(),principal=principal,session=session)
    return _json(*command_result_to_api_response(result,operation="settings.providers.connectivity_test"))


@router.post("/api/v1/settings/providers/enablement")
def settings_provider_enablement_apply(request: Request, body: ProviderEnablementBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    principal, session = _session(request)
    if principal is None or session is None:
        return _json({"operation":"settings.providers.enablement.apply","ok":False,"exit_code":4,"message":"Authenticated human session is required.","data":{},"findings":[{"id":"AUTH_HUMAN_SESSION_REQUIRED_BLOCK","severity":"block","message":"Provider enablement apply requires authenticated human session."}]},401)
    result=service.settings_provider_enablement_apply_authenticated(payload=body.model_dump(),principal=principal,session=session)
    return _json(*command_result_to_api_response(result,operation="settings.providers.enablement.apply"))


def _disable_or_revoke(request: Request, body: ProviderDisableBody, service: ApplicationService, *, revoke: bool) -> JSONResponse:
    principal, session = _session(request)
    operation="settings.providers.enablement.revoke" if revoke else "settings.providers.enablement.disable"
    if principal is None or session is None:
        return _json({"operation":operation,"ok":False,"exit_code":4,"message":"Authenticated human session is required.","data":{},"findings":[{"id":"AUTH_HUMAN_SESSION_REQUIRED_BLOCK","severity":"block","message":"Provider disable/revoke requires authenticated human session."}]},401)
    result=service.settings_provider_enablement_disable_authenticated(provider_id=body.provider_id,reason=body.reason,principal=principal,session=session,revoke=revoke)
    return _json(*command_result_to_api_response(result,operation=operation))


@router.post("/api/v1/settings/providers/disable")
def settings_provider_disable(request: Request, body: ProviderDisableBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _disable_or_revoke(request,body,service,revoke=False)


@router.post("/api/v1/settings/providers/revoke")
def settings_provider_revoke(request: Request, body: ProviderDisableBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _disable_or_revoke(request,body,service,revoke=True)
