from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["project-entry"])


class ProjectEntryPlanningBody(BaseModel):
    intake: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = Field(default=3.0, ge=0.1, le=15.0)


class ProjectEntryRevalidateBody(ProjectEntryPlanningBody):
    expected_plan_hash: str = Field(min_length=64, max_length=64)
    expected_preimage_hash: str = Field(min_length=64, max_length=64)


def _json(payload: dict[str, Any], status: int) -> JSONResponse:
    return JSONResponse(payload, status_code=status)


@router.post("/api/v1/project-entry/environment-discovery")
def project_entry_environment_discovery(
    body: ProjectEntryPlanningBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="project_entry.environment_discovery",
            payload={"intake": body.intake, "timeout_seconds": body.timeout_seconds},
        )
    )


@router.post("/api/v1/project-entry/bootstrap-plan")
def project_entry_bootstrap_plan(
    body: ProjectEntryPlanningBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="project_entry.bootstrap_plan",
            payload={"intake": body.intake, "timeout_seconds": body.timeout_seconds},
        )
    )


@router.post("/api/v1/project-entry/dry-run")
def project_entry_dry_run(body: ProjectEntryPlanningBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="project_entry.dry_run", payload={"intake": body.intake, "timeout_seconds": body.timeout_seconds}))


@router.post("/api/v1/project-entry/revalidate")
def project_entry_revalidate(body: ProjectEntryRevalidateBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="project_entry.revalidate", payload={"intake": body.intake, "expected_plan_hash": body.expected_plan_hash, "expected_preimage_hash": body.expected_preimage_hash, "timeout_seconds": body.timeout_seconds}))
