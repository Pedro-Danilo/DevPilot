from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["workspace-git"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


class GitCommitPlanBody(BaseModel):
    document_ids: list[str] = Field(min_length=1, max_length=20)
    commit_message: str = Field(min_length=3, max_length=500)
    author_name: str = Field(min_length=1, max_length=128)
    author_email: str = Field(min_length=3, max_length=254)


class GitStageApprovalBody(BaseModel):
    plan_hash: str = Field(min_length=64, max_length=64)
    actor: str = Field(default="local-owner", min_length=1, max_length=128)
    reason: str = Field(min_length=3, max_length=1000)
    ttl_minutes: int = Field(default=15, ge=1, le=30)


class GitStageBody(BaseModel):
    plan_hash: str = Field(min_length=64, max_length=64)
    approval_id: str = Field(min_length=1, max_length=128)
    actor: str = Field(default="local-owner", min_length=1, max_length=128)


class GitCommitApprovalBody(BaseModel):
    actor: str = Field(default="local-owner", min_length=1, max_length=128)
    reason: str = Field(min_length=3, max_length=1000)
    ttl_minutes: int = Field(default=15, ge=1, le=30)


class GitCommitBody(BaseModel):
    approval_id: str = Field(min_length=1, max_length=128)
    actor: str = Field(default="local-owner", min_length=1, max_length=128)


class GitBranchPlanBody(BaseModel):
    branch_name: str = Field(min_length=3, max_length=120)


class GitBranchApprovalBody(BaseModel):
    plan_hash: str = Field(min_length=64, max_length=64)
    actor: str = Field(default="local-owner", min_length=1, max_length=128)
    reason: str = Field(min_length=3, max_length=1000)
    ttl_minutes: int = Field(default=15, ge=1, le=30)


class GitBranchCreateBody(BaseModel):
    plan_hash: str = Field(min_length=64, max_length=64)
    approval_id: str = Field(min_length=1, max_length=128)
    actor: str = Field(default="local-owner", min_length=1, max_length=128)


@router.get("/api/v1/workspace/git/status")
def workspace_git_status(service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.git.status", payload={}))


@router.get("/api/v1/workspace/git/history")
def workspace_git_history(limit: int = Query(default=20, ge=1, le=50), service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.git.history", payload={"limit": limit}))


@router.get("/api/v1/workspace/git/compare")
def workspace_git_compare(base_ref: str = Query(default="HEAD"), head_ref: str = Query(default="HEAD"), service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.git.compare", payload={"base_ref": base_ref, "head_ref": head_ref}))


@router.post("/api/v1/workspace/git/plans")
def workspace_git_plan(body: GitCommitPlanBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.git.plan", payload=body.model_dump()))


@router.get("/api/v1/workspace/git/plans/{plan_id}")
def workspace_git_plan_status(plan_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.git.plan_status", payload={"plan_id": plan_id}))


@router.post("/api/v1/workspace/git/plans/{plan_id}/stage-approval-request")
def workspace_git_stage_approval(plan_id: str, body: GitStageApprovalBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.git.stage_approval_request", payload={"plan_id": plan_id, **body.model_dump()}))


@router.post("/api/v1/workspace/git/plans/{plan_id}/stage")
def workspace_git_stage(plan_id: str, body: GitStageBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.git.stage", payload={"plan_id": plan_id, **body.model_dump()}))


@router.get("/api/v1/workspace/git/executions/{execution_id}")
def workspace_git_execution(execution_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.git.execution_status", payload={"execution_id": execution_id}))


@router.post("/api/v1/workspace/git/stage-executions/{execution_id}/commit-approval-request")
def workspace_git_commit_approval(execution_id: str, body: GitCommitApprovalBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.git.commit_approval_request", payload={"stage_execution_id": execution_id, **body.model_dump()}))


@router.post("/api/v1/workspace/git/stage-executions/{execution_id}/commit")
def workspace_git_commit(execution_id: str, body: GitCommitBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.git.commit", payload={"stage_execution_id": execution_id, **body.model_dump()}))


@router.post("/api/v1/workspace/git/branches/plan")
def workspace_git_branch_plan(body: GitBranchPlanBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.git.branch_plan", payload=body.model_dump()))


@router.post("/api/v1/workspace/git/branches/{plan_id}/approval-request")
def workspace_git_branch_approval(plan_id: str, body: GitBranchApprovalBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.git.branch_approval_request", payload={"plan_id": plan_id, **body.model_dump()}))


@router.post("/api/v1/workspace/git/branches/{plan_id}/create")
def workspace_git_branch_create(plan_id: str, body: GitBranchCreateBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.git.branch_create", payload={"plan_id": plan_id, **body.model_dump()}))
