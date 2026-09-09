from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..response_mapping import command_result_to_api_response

router = APIRouter(tags=["story-code-workbench"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


def _principal(request: Request, *, authoring: bool = False):
    principal = getattr(request.state, "authenticated_principal", None)
    if principal is None:
        return None, _json({"operation":"story.code","ok":False,"exit_code":4,"message":"Authenticated human session required.","data":{},"findings":[{"id":"AUTH_HUMAN_SESSION_REQUIRED_BLOCK","severity":"block","message":"Code Workbench requires authenticated human session."}]}, 401)
    roles = tuple(str(x) for x in principal.roles if str(x).strip())
    if authoring and not ({"owner", "developer"} & set(roles)):
        return None, _json({"operation":"story.code","ok":False,"exit_code":4,"message":"Code authoring role is not authorized.","data":{"allowed_roles":["owner","developer"]},"findings":[{"id":"GSDLC09B_ROLE_BLOCK","severity":"block","message":"SourceDraftBuffer authoring requires owner or developer role."}]}, 403)
    role = "owner" if "owner" in roles else ("developer" if "developer" in roles else (roles[0] if roles else ""))
    return (principal.actor_id, role), None


def _result(result, operation: str) -> JSONResponse:
    payload, status = command_result_to_api_response(result, operation=operation)
    if not result.ok and result.exit_code.value == 2 and any("CONFLICT" in f.id for f in result.findings):
        status = 409
    return _json(payload, status)


class SourceDraftSaveBody(BaseModel):
    operation: str = Field(pattern=r"^(CREATE|EDIT|RENAME)$")
    content: str = Field(max_length=262144)
    target_path: str = Field(min_length=1, max_length=1024)
    source_id: str | None = Field(default=None, max_length=128)
    expected_source_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    expected_revision_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class SourceDraftDiscardBody(BaseModel):
    expected_revision_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class SourceChangePlanBody(BaseModel):
    draft_ids: list[str] = Field(min_length=1, max_length=32)


class SourceChangeHashBody(BaseModel):
    plan_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class SourceChangeApprovalBody(SourceChangeHashBody):
    reason: str = Field(min_length=1, max_length=500)
    ttl_minutes: int = Field(default=15, ge=1, le=30)


class SourceChangeApplyBody(SourceChangeHashBody):
    approval_id: str = Field(min_length=1, max_length=160)


class StoryTestPlanCreateBody(SourceChangeHashBody):
    pass


class StoryTestPlanDecisionBody(BaseModel):
    test_plan_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision: str = Field(pattern=r"^(APPROVE|REJECT|WAIVE)$")
    reason: str | None = Field(default=None, max_length=500)
    waived_test_ids: list[str] = Field(default_factory=list, max_length=100)
    ttl_minutes: int = Field(default=60, ge=1, le=1440)


class SourceChangeRollbackApprovalBody(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
    ttl_minutes: int = Field(default=15, ge=1, le=30)


class SourceChangeRollbackBody(BaseModel):
    approval_id: str = Field(min_length=1, max_length=160)


class StoryAgentProposalBody(BaseModel):
    agent_type: str = Field(pattern=r"^(coding|test)$")
    mode: str = Field(default="mock", pattern=r"^(mock|fake-local)$")
    instruction: str = Field(min_length=1, max_length=2000)
    source_id: str | None = Field(default=None, max_length=128)


class StoryAgentProposalDecisionBody(BaseModel):
    proposal_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision: str = Field(pattern=r"^(ACCEPT|REJECT)$")


@router.get("/api/v1/story/code/status")
def story_code_status(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    _, error = _principal(request)
    if error: return error
    return _result(service.story_code_status(), "story.code.status")


@router.get("/api/v1/story/code/sources")
def story_code_sources(request: Request, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    _, error = _principal(request)
    if error: return error
    return _result(service.story_code_sources(), "story.code.sources")


@router.get("/api/v1/story/code/sources/{source_id}")
def story_code_source(request: Request, source_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    _, error = _principal(request)
    if error: return error
    return _result(service.story_code_source_read(source_id=source_id), "story.code.source.read")


@router.post("/api/v1/story/code/drafts")
def story_code_draft_save(request: Request, body: SourceDraftSaveBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _principal(request, authoring=True)
    if error: return error
    actor, role = identity
    return _result(service.story_code_draft_save(actor=actor, actor_role=role, **body.model_dump()), "story.code.draft.save")


@router.get("/api/v1/story/code/drafts/{draft_id}")
def story_code_draft_get(request: Request, draft_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    _, error = _principal(request)
    if error: return error
    return _result(service.story_code_draft_get(draft_id=draft_id), "story.code.draft.get")


@router.post("/api/v1/story/code/drafts/{draft_id}/recheck")
def story_code_draft_recheck(request: Request, draft_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    _, error = _principal(request, authoring=True)
    if error: return error
    return _result(service.story_code_draft_recheck(draft_id=draft_id), "story.code.draft.recheck")


@router.post("/api/v1/story/code/drafts/{draft_id}/discard")
def story_code_draft_discard(request: Request, draft_id: str, body: SourceDraftDiscardBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _principal(request, authoring=True)
    if error: return error
    _, role = identity
    return _result(service.story_code_draft_discard(draft_id=draft_id, expected_revision_sha256=body.expected_revision_sha256, actor_role=role), "story.code.draft.discard")


@router.post("/api/v1/story/code/change-plans")
def story_source_change_plan_create(request: Request, body: SourceChangePlanBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _principal(request, authoring=True)
    if error: return error
    actor, role = identity
    return _result(service.story_source_change_plan_create(draft_ids=body.draft_ids, actor=actor, actor_role=role), "story.source-change.plan")


@router.get("/api/v1/story/code/change-plans/{plan_id}")
def story_source_change_plan_get(request: Request, plan_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    _, error = _principal(request)
    if error: return error
    return _result(service.story_source_change_plan_get(plan_id=plan_id), "story.source-change.plan.get")


@router.post("/api/v1/story/code/change-plans/{plan_id}/recheck")
def story_source_change_plan_recheck(request: Request, plan_id: str, body: SourceChangeHashBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    _, error = _principal(request, authoring=True)
    if error: return error
    return _result(service.story_source_change_plan_recheck(plan_id=plan_id, plan_hash=body.plan_hash), "story.source-change.recheck")


@router.post("/api/v1/story/code/change-plans/{plan_id}/dry-run")
def story_source_change_dry_run(request: Request, plan_id: str, body: SourceChangeHashBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _principal(request, authoring=True)
    if error: return error
    actor, role = identity
    return _result(service.story_source_change_dry_run(plan_id=plan_id, plan_hash=body.plan_hash, actor=actor, actor_role=role), "story.source-change.dry-run")


@router.post("/api/v1/story/code/change-plans/{plan_id}/approval-request")
def story_source_change_approval_request(request: Request, plan_id: str, body: SourceChangeApprovalBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _principal(request, authoring=True)
    if error: return error
    actor, role = identity
    if role != "owner": return _json({"operation":"story.source-change.approval-request","ok":False,"exit_code":2,"message":"Owner role required.","data":{},"findings":[{"id":"GSDLC09C_WRONG_APPROVER_ROLE_BLOCK","severity":"block","message":"Only owner may request source apply approval."}]},403)
    return _result(service.story_source_change_apply_approval_request(plan_id=plan_id, plan_hash=body.plan_hash, actor=actor, actor_role=role, reason=body.reason, ttl_minutes=body.ttl_minutes), "story.source-change.approval-request")


@router.post("/api/v1/story/code/change-plans/{plan_id}/apply")
def story_source_change_apply(request: Request, plan_id: str, body: SourceChangeApplyBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _principal(request, authoring=True)
    if error: return error
    actor, role = identity
    if role != "owner": return _json({"operation":"story.source-change.apply","ok":False,"exit_code":2,"message":"Owner role required.","data":{},"findings":[{"id":"GSDLC09C_WRONG_ROLE_BLOCK","severity":"block","message":"Atomic source apply requires owner role."}]},403)
    return _result(service.story_source_change_apply(plan_id=plan_id, plan_hash=body.plan_hash, approval_id=body.approval_id, actor=actor, actor_role=role), "story.source-change.apply")


@router.post("/api/v1/story/code/change-plans/{plan_id}/test-plan")
def story_test_plan_create(request: Request, plan_id: str, body: StoryTestPlanCreateBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _principal(request, authoring=True)
    if error: return error
    actor, role = identity
    return _result(service.story_test_plan_create(source_plan_id=plan_id, source_plan_hash=body.plan_hash, actor=actor, actor_role=role), "story.test-plan.create")


@router.get("/api/v1/story/code/test-plans/{test_plan_id}")
def story_test_plan_get(request: Request, test_plan_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    _, error = _principal(request)
    if error: return error
    return _result(service.story_test_plan_get(test_plan_id=test_plan_id), "story.test-plan.get")


@router.post("/api/v1/story/code/test-plans/{test_plan_id}/decision")
def story_test_plan_decide(request: Request, test_plan_id: str, body: StoryTestPlanDecisionBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _principal(request, authoring=True)
    if error: return error
    actor, role = identity
    result = service.story_test_plan_decide(
        test_plan_id=test_plan_id,
        test_plan_hash=body.test_plan_hash,
        decision=body.decision,
        actor=actor,
        actor_role=role,
        reason=body.reason,
        waived_test_ids=body.waived_test_ids,
        ttl_minutes=body.ttl_minutes,
        authority_source="human-session",
    )
    if not result.ok and any(f.id in {"GSDLC10A_APPROVAL_ROLE_BLOCK", "GSDLC10A_WAIVER_ROLE_BLOCK"} for f in result.findings):
        payload, _ = command_result_to_api_response(result, operation="story.test-plan.decision")
        return _json(payload, 403)
    return _result(result, "story.test-plan.decision")


@router.get("/api/v1/story/code/change-executions/{execution_id}")
def story_source_change_execution_get(request: Request, execution_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    _, error = _principal(request)
    if error: return error
    return _result(service.story_source_change_execution_get(execution_id=execution_id), "story.source-change.execution.get")


@router.post("/api/v1/story/code/change-executions/{execution_id}/rollback-approval-request")
def story_source_change_rollback_approval_request(request: Request, execution_id: str, body: SourceChangeRollbackApprovalBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _principal(request, authoring=True)
    if error: return error
    actor, role = identity
    if role != "owner": return _json({"operation":"story.source-change.rollback-approval-request","ok":False,"exit_code":2,"message":"Owner role required.","data":{},"findings":[{"id":"GSDLC09C_ROLLBACK_WRONG_ROLE_BLOCK","severity":"block","message":"Only owner may request rollback approval."}]},403)
    return _result(service.story_source_change_rollback_approval_request(execution_id=execution_id, actor=actor, actor_role=role, reason=body.reason, ttl_minutes=body.ttl_minutes), "story.source-change.rollback-approval-request")


@router.post("/api/v1/story/code/change-executions/{execution_id}/rollback")
def story_source_change_rollback(request: Request, execution_id: str, body: SourceChangeRollbackBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _principal(request, authoring=True)
    if error: return error
    actor, role = identity
    if role != "owner": return _json({"operation":"story.source-change.rollback","ok":False,"exit_code":2,"message":"Owner role required.","data":{},"findings":[{"id":"GSDLC09C_ROLLBACK_WRONG_ROLE_BLOCK","severity":"block","message":"Manual source rollback requires owner role."}]},403)
    return _result(service.story_source_change_rollback(execution_id=execution_id, approval_id=body.approval_id, actor=actor, actor_role=role), "story.source-change.rollback")


@router.get("/api/v1/story/code/change-executions/{execution_id}/apply-manifest")
def story_source_change_apply_manifest(request: Request, execution_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    _, error = _principal(request)
    if error: return error
    return _result(service.story_source_change_apply_manifest(execution_id=execution_id), "story.source-change.apply-manifest")


@router.get("/api/v1/story/code/change-executions/{execution_id}/rollback-evidence")
def story_source_change_rollback_evidence(request: Request, execution_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    _, error = _principal(request)
    if error: return error
    return _result(service.story_source_change_rollback_evidence(execution_id=execution_id), "story.source-change.rollback-evidence")


@router.post("/api/v1/story/code/agent-assist/proposals")
def story_agent_proposal_create(request: Request, body: StoryAgentProposalBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _principal(request, authoring=True)
    if error: return error
    actor, role = identity
    return _result(service.story_agent_proposal_create(actor=actor, actor_role=role, **body.model_dump()), "story.agent-assist.proposal.create")


@router.get("/api/v1/story/code/agent-assist/proposals/{proposal_id}")
def story_agent_proposal_get(request: Request, proposal_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    _, error = _principal(request)
    if error: return error
    return _result(service.story_agent_proposal_get(proposal_id=proposal_id), "story.agent-assist.proposal.get")


@router.post("/api/v1/story/code/agent-assist/proposals/{proposal_id}/decision")
def story_agent_proposal_decide(request: Request, proposal_id: str, body: StoryAgentProposalDecisionBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _principal(request, authoring=True)
    if error: return error
    actor, role = identity
    return _result(service.story_agent_proposal_decide(proposal_id=proposal_id, proposal_sha256=body.proposal_sha256, decision=body.decision, actor=actor, actor_role=role), "story.agent-assist.proposal.decision")
