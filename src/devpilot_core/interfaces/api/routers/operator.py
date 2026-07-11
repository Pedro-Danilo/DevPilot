from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["operator"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


@router.get("/api/v1/operator/dashboard")
def operator_dashboard(
    write_report: bool = Query(default=False),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="operator.dashboard",
            payload={"write_report": write_report},
        )
    )


@router.get("/api/v1/operator/health")
def operator_health(
    write_report: bool = Query(default=False),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="operator.health",
            payload={"write_report": write_report},
        )
    )

@router.get("/api/v1/operator/gaps")
def operator_gaps(
    write_report: bool = Query(default=False),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="operator.gaps",
            payload={"write_report": write_report},
        )
    )

@router.get("/api/v1/operator/claims-no-go")
def operator_claims_no_go(
    write_report: bool = Query(default=False),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="operator.claims_no_go",
            payload={"write_report": write_report},
        )
    )

@router.get("/api/v1/operator/evidence-export")
def operator_evidence_export(
    redacted: bool = Query(default=True),
    dry_run: bool = Query(default=True),
    write_report: bool = Query(default=False),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="operator.evidence_export",
            payload={"redacted": redacted, "dry_run": dry_run or not write_report, "write_report": write_report},
        )
    )

