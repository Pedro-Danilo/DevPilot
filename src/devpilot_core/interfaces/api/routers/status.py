from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["status"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


@router.get("/api/v1/workspace/status")
def workspace_status(service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.status"))


@router.get("/api/v1/application/contract")
def application_contract(service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="app.contract"))


@router.get("/api/v1/miasi/status")
def miasi_status(scope: str = Query(default="all"), service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="miasi.validate", payload={"scope": scope}))


@router.get("/api/v1/standards/status")
def standards_status(service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="standards.status"))


@router.get("/api/v1/model/providers")
def model_providers(service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="model.providers"))


@router.get("/api/v1/repo/inventory")
def repo_inventory(service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="repo.inventory"))


@router.get("/api/v1/observability/traces")
def traces(
    limit: int = Query(default=20, ge=1, le=100),
    include_events: bool = Query(default=True),
    include_metrics: bool = Query(default=True),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="observability.trace_report", payload={"limit": limit, "include_events": include_events, "include_metrics": include_metrics}))


@router.get("/api/v1/observability/metrics")
def metrics(
    category: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="observability.metrics_summary", payload={"category": category, "limit": limit}))


@router.get("/api/v1/history/runs")
def history_runs(limit: int = Query(default=10, ge=1, le=100), service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="history.runs", payload={"limit": limit}))
