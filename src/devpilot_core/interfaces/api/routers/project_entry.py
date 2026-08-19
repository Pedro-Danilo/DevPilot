from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request
from ..response_mapping import command_result_to_api_response

router = APIRouter(tags=["project-entry"])


class ProjectEntryPlanningBody(BaseModel):
    intake: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = Field(default=3.0, ge=0.1, le=15.0)


class ProjectEntryRevalidateBody(ProjectEntryPlanningBody):
    expected_plan_hash: str = Field(min_length=64, max_length=64)
    expected_preimage_hash: str = Field(min_length=64, max_length=64)


class ProjectEntryExecutionApprovalBody(ProjectEntryRevalidateBody):
    reason: str = Field(default="Execute reviewed GSDLC-03-D bootstrap plan.")
    ttl_minutes: int = Field(default=30, ge=1, le=60)


class ProjectEntryExecuteBody(ProjectEntryRevalidateBody):
    approval_id: str = Field(min_length=1, max_length=128)
    dependency_mode: str = Field(default="defer-network")
    fault_stage: str | None = Field(default=None)


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


def _human_session(request: Request) -> tuple[Any | None, Any | None]:
    return (
        getattr(request.state, "authenticated_principal", None),
        getattr(request.state, "authenticated_session_context", None),
    )


@router.post("/api/v1/project-entry/execution-approval-request")
def project_entry_execution_approval_request(
    request: Request,
    body: ProjectEntryExecutionApprovalBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    principal, session = _human_session(request)
    if principal is None or session is None:
        return _json(
            {
                "operation": "project_entry.execution_approval_request",
                "ok": False,
                "exit_code": 4,
                "message": "Authenticated human session is required.",
                "data": {},
                "findings": [
                    {
                        "id": "AUTH_HUMAN_SESSION_REQUIRED_BLOCK",
                        "severity": "block",
                        "message": "Bootstrap approval request requires authenticated human session.",
                    }
                ],
            },
            401,
        )
    result = service.project_entry_request_execution_approval_authenticated(
        intake=body.intake,
        expected_plan_hash=body.expected_plan_hash,
        expected_preimage_hash=body.expected_preimage_hash,
        principal=principal,
        session=session,
        reason=body.reason,
        ttl_minutes=body.ttl_minutes,
        timeout_seconds=body.timeout_seconds,
    )
    return _json(*command_result_to_api_response(result, operation="project_entry.execution_approval_request"))


@router.post("/api/v1/project-entry/execute")
def project_entry_execute(
    request: Request,
    body: ProjectEntryExecuteBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    principal, session = _human_session(request)
    if principal is None or session is None:
        return _json(
            {
                "operation": "project_entry.execute",
                "ok": False,
                "exit_code": 4,
                "message": "Authenticated human session is required.",
                "data": {},
                "findings": [
                    {
                        "id": "AUTH_HUMAN_SESSION_REQUIRED_BLOCK",
                        "severity": "block",
                        "message": "Bootstrap execution requires authenticated human session.",
                    }
                ],
            },
            401,
        )
    result = service.project_entry_execute_authenticated(
        intake=body.intake,
        expected_plan_hash=body.expected_plan_hash,
        expected_preimage_hash=body.expected_preimage_hash,
        approval_id=body.approval_id,
        principal=principal,
        session=session,
        dependency_mode=body.dependency_mode,
        fault_stage=body.fault_stage,
        timeout_seconds=body.timeout_seconds,
    )
    return _json(*command_result_to_api_response(result, operation="project_entry.execute"))
