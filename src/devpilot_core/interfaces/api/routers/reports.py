from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["reports"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


@router.get("/api/v1/reports")
def list_reports(
    limit: int = Query(default=50, ge=1, le=200),
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    command: str | None = Query(default=None),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="reports.list",
            payload={"limit": limit, "severity": severity, "status": status, "command": command},
        )
    )


@router.get("/api/v1/reports/{report_id}")
def read_report(
    report_id: str,
    format: str = Query(default="json"),
    max_chars: int = Query(default=20000, ge=1, le=20000),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="reports.read",
            payload={"report_id": report_id, "format": format, "max_chars": max_chars},
        )
    )
