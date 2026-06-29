from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["portfolio"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


@router.get("/api/v1/portfolio/status")
def portfolio_status(service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    """Return registered-workspace portfolio status without changing active workspace."""

    return _json(
        *dispatch_application_request(
            service,
            operation="portfolio.status",
            payload={},
        )
    )
