from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["traces"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


@router.get("/api/v1/traces")
def list_traces(
    limit: int = Query(default=20, ge=1, le=100),
    include_events: bool = Query(default=True),
    include_metrics: bool = Query(default=True),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="observability.trace_report",
            payload={"limit": limit, "include_events": include_events, "include_metrics": include_metrics},
        )
    )


@router.get("/api/v1/traces/{trace_id}")
def inspect_trace(
    trace_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="observability.trace_inspect",
            payload={"trace_id": trace_id, "limit": limit},
        )
    )


@router.get("/api/v1/metrics/summary")
def metrics_summary(
    category: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="observability.metrics_summary",
            payload={"category": category, "limit": limit},
        )
    )
