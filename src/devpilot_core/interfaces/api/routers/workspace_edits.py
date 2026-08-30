from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import ApiApplicationRequest, dispatch_application_request
from ..response_mapping import command_result_to_api_response

router = APIRouter(tags=["workspace-edits"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


def _session_actor(request: Request, supplied: str | None) -> tuple[str | None, JSONResponse | None]:
    principal=getattr(request.state,"authenticated_principal",None)
    if principal is None:
        return None,_json({"operation":"workspace.approval","ok":False,"exit_code":4,"message":"Authenticated human session required.","data":{},"findings":[{"id":"AUTH_HUMAN_SESSION_REQUIRED_BLOCK","severity":"block","message":"Workspace approval/mutation requires authenticated session."}]},401)
    if supplied and supplied.strip() and supplied.strip()!=principal.actor_id:
        return None,_json({"operation":"workspace.approval","ok":False,"exit_code":4,"message":"Caller actor cannot override authenticated principal.","data":{},"findings":[{"id":"APPROVAL_ACTOR_SPOOF_BLOCK","severity":"block","message":"Caller actor does not match authenticated principal."}]},403)
    return principal.actor_id,None


class ApplyApprovalRequestBody(BaseModel):
    plan_hash: str
    actor: str | None = Field(default=None, min_length=1, max_length=128)
    reason: str = Field(min_length=3, max_length=1000)
    ttl_minutes: int = Field(default=15, ge=1, le=30)


class ApplyRequestBody(BaseModel):
    plan_hash: str
    approval_id: str = Field(min_length=1, max_length=128)
    actor: str | None = Field(default=None, min_length=1, max_length=128)


class RollbackApprovalRequestBody(BaseModel):
    actor: str | None = Field(default=None, min_length=1, max_length=128)
    reason: str = Field(min_length=3, max_length=1000)
    ttl_minutes: int = Field(default=15, ge=1, le=30)


class RollbackRequestBody(BaseModel):
    approval_id: str = Field(min_length=1, max_length=128)
    actor: str | None = Field(default=None, min_length=1, max_length=128)


class DraftSaveBody(BaseModel):
    content: str = Field(max_length=1048576)
    expected_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_revision_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    event: str = Field(default="SAVE", pattern=r"^(SAVE|AUTOSAVE)$")


class DraftDiscardBody(BaseModel):
    expected_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_revision_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class DraftRecoverBody(BaseModel):
    revision_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_revision_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class ArtifactImportPreviewBody(BaseModel):
    source_type: str = Field(pattern=r"^(PASTE|UPLOAD|IMPORT)$")
    destination_path: str = Field(min_length=1, max_length=1024)
    source_label: str | None = Field(default=None, max_length=512)
    source_reference: str | None = Field(default=None, max_length=2048)
    original_filename: str | None = Field(default=None, max_length=128)
    declared_mime: str | None = Field(default=None, max_length=128)
    text_content: str | None = Field(default=None, max_length=1048576)
    content_base64: str | None = Field(default=None, max_length=1500000)


class ArtifactImportPersistBody(ArtifactImportPreviewBody):
    expected_preview_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ArtifactReviewFreezeBody(BaseModel):
    execution_id: str = Field(pattern=r"^uedit_[0-9a-f]{32}$")


class AgentAssistPlanBody(BaseModel):
    operation: str = Field(pattern=r"^(generate_draft|rewrite_selection|critique|improve|transform_imported_source)$")
    mode: str = Field(default="mock", pattern=r"^(mock|fake-local)$")
    instruction: str = Field(default="", max_length=4000)
    current_content: str = Field(max_length=1048576)
    expected_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_revision_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    selection_start: int | None = Field(default=None, ge=0)
    selection_end: int | None = Field(default=None, ge=1)
    import_id: str | None = Field(default=None, max_length=128)
    step_id: str | None = Field(default=None, max_length=128)


class AgentAssistRunBody(BaseModel):
    plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class AgentAssistDecisionBody(BaseModel):
    proposal_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision: str = Field(pattern=r"^(ACCEPT|REJECT|MODIFY)$")
    modified_content: str | None = Field(default=None, max_length=1048576)


def _draft_session_identity(request: Request) -> tuple[tuple[str, str, str] | None, JSONResponse | None]:
    principal = getattr(request.state, "authenticated_principal", None)
    if principal is None:
        return None, _json({"operation":"workspace.artifact_drafts","ok":False,"exit_code":4,"message":"Authenticated human session required.","data":{},"findings":[{"id":"AUTH_HUMAN_SESSION_REQUIRED_BLOCK","severity":"block","message":"Artifact draft authoring requires authenticated human session."}]}, 401)
    role = next((str(value) for value in principal.roles if str(value).strip()), "")
    if not role:
        return None, _json({"operation":"workspace.artifact_drafts","ok":False,"exit_code":4,"message":"Authenticated principal has no canonical role.","data":{},"findings":[{"id":"RBAC_ROLE_REQUIRED_BLOCK","severity":"block","message":"Artifact draft authoring requires a canonical server-side role."}]}, 403)
    return (principal.actor_id, role, principal.actor_id), None


def _draft_json(result, operation: str) -> JSONResponse:
    payload, status = command_result_to_api_response(result, operation=operation)
    return _json(payload, status)


@router.post("/api/v1/workspace/edit-plans/plan")
def workspace_edit_plan(
    request: ApiApplicationRequest,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.edits.plan", request=request))


@router.get("/api/v1/workspace/edit-plans/{plan_id}")
def workspace_edit_plan_status(
    plan_id: str,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.edits.status", payload={"plan_id": plan_id}))


@router.post("/api/v1/workspace/edit-plans/{plan_id}/recheck")
def workspace_edit_plan_recheck(
    plan_id: str,
    request: ApiApplicationRequest,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    payload = dict(request.payload or {})
    payload["plan_id"] = plan_id
    forwarded = ApiApplicationRequest(operation=request.operation, payload=payload, client=request.client, dry_run=request.dry_run)
    return _json(*dispatch_application_request(service, operation="workspace.edits.recheck", request=forwarded))


@router.post("/api/v1/workspace/edit-plans/{plan_id}/approval-request")
def workspace_edit_apply_approval_request(
    request: Request,
    plan_id: str,
    body: ApplyApprovalRequestBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    actor,error=_session_actor(request,body.actor)
    if error:return error
    payload=body.model_dump();payload["actor"]=actor
    return _json(*dispatch_application_request(service, operation="workspace.edits.approval_request", payload={"plan_id": plan_id, **payload}))


@router.post("/api/v1/workspace/edit-plans/{plan_id}/apply")
def workspace_edit_apply(
    request: Request,
    plan_id: str,
    body: ApplyRequestBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    actor,error=_session_actor(request,body.actor)
    if error:return error
    payload=body.model_dump();payload["actor"]=actor
    return _json(*dispatch_application_request(service, operation="workspace.edits.apply", payload={"plan_id": plan_id, **payload}))


@router.get("/api/v1/workspace/edit-executions/{execution_id}")
def workspace_edit_execution_status(
    execution_id: str,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.edits.execution_status", payload={"execution_id": execution_id}))


@router.post("/api/v1/workspace/edit-executions/{execution_id}/rollback-approval-request")
def workspace_edit_rollback_approval_request(
    request: Request,
    execution_id: str,
    body: RollbackApprovalRequestBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    actor,error=_session_actor(request,body.actor)
    if error:return error
    payload=body.model_dump();payload["actor"]=actor
    return _json(*dispatch_application_request(service, operation="workspace.edits.rollback_approval_request", payload={"execution_id": execution_id, **payload}))


@router.post("/api/v1/workspace/edit-executions/{execution_id}/rollback")
def workspace_edit_rollback(
    request: Request,
    execution_id: str,
    body: RollbackRequestBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    actor,error=_session_actor(request,body.actor)
    if error:return error
    payload=body.model_dump();payload["actor"]=actor
    return _json(*dispatch_application_request(service, operation="workspace.edits.rollback", payload={"execution_id": execution_id, **payload}))

@router.get("/api/v1/workspace/artifact-drafts/{document_id}")
def artifact_draft_get(
    request: Request,
    document_id: str,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    return _draft_json(service.artifact_draft_get(document_id=document_id), "workspace.artifact_drafts.get")


@router.get("/api/v1/workspace/artifact-drafts/{document_id}/history")
def artifact_draft_history(
    request: Request,
    document_id: str,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    return _draft_json(service.artifact_draft_history(document_id=document_id), "workspace.artifact_drafts.history")


@router.post("/api/v1/workspace/artifact-drafts/{document_id}/save")
def artifact_draft_save(
    request: Request,
    document_id: str,
    body: DraftSaveBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    assert identity is not None
    actor, actor_role, session_principal = identity
    result = service.artifact_draft_save(document_id=document_id, content=body.content, expected_source_sha256=body.expected_source_sha256, expected_revision_sha256=body.expected_revision_sha256, actor=actor, actor_role=actor_role, session_principal=session_principal, event=body.event)
    return _draft_json(result, "workspace.artifact_drafts.save")


@router.post("/api/v1/workspace/artifact-drafts/{document_id}/discard")
def artifact_draft_discard(
    request: Request,
    document_id: str,
    body: DraftDiscardBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    assert identity is not None
    actor, actor_role, session_principal = identity
    result = service.artifact_draft_discard(document_id=document_id, expected_source_sha256=body.expected_source_sha256, expected_revision_sha256=body.expected_revision_sha256, actor=actor, actor_role=actor_role, session_principal=session_principal)
    return _draft_json(result, "workspace.artifact_drafts.discard")


@router.post("/api/v1/workspace/artifact-drafts/{document_id}/recover")
def artifact_draft_recover(
    request: Request,
    document_id: str,
    body: DraftRecoverBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    assert identity is not None
    actor, actor_role, session_principal = identity
    result = service.artifact_draft_recover(document_id=document_id, revision_sha256=body.revision_sha256, expected_source_sha256=body.expected_source_sha256, expected_revision_sha256=body.expected_revision_sha256, actor=actor, actor_role=actor_role, session_principal=session_principal)
    return _draft_json(result, "workspace.artifact_drafts.recover")

@router.post("/api/v1/workspace/artifact-imports/preview")
def artifact_import_preview(
    request: Request,
    body: ArtifactImportPreviewBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    assert identity is not None
    actor, actor_role, session_principal = identity
    result = service.artifact_import_preview(actor=actor, actor_role=actor_role, session_principal=session_principal, **body.model_dump())
    return _draft_json(result, "workspace.artifact_imports.preview")


@router.post("/api/v1/workspace/artifact-imports/persist")
def artifact_import_persist(
    request: Request,
    body: ArtifactImportPersistBody,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    assert identity is not None
    actor, actor_role, session_principal = identity
    result = service.artifact_import_persist(actor=actor, actor_role=actor_role, session_principal=session_principal, **body.model_dump())
    return _draft_json(result, "workspace.artifact_imports.persist")


@router.get("/api/v1/workspace/artifact-imports/recent")
def artifact_import_recent(
    request: Request,
    limit: int = 20,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    result = service.artifact_import_recent(limit=limit)
    return _draft_json(result, "workspace.artifact_imports.recent")



@router.post("/api/v1/workspace/artifact-assist/documents/{document_id}/plan")
def artifact_assist_plan(request: Request, document_id: str, body: AgentAssistPlanBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    assert identity is not None
    actor, actor_role, principal = identity
    payload = body.model_dump()
    return _draft_json(service.artifact_assist_plan(document_id=document_id, actor=actor, actor_role=actor_role, session_principal=principal, **payload), "workspace.artifact_assist.plan")


@router.post("/api/v1/workspace/artifact-assist/plans/{plan_id}/run")
def artifact_assist_run(request: Request, plan_id: str, body: AgentAssistRunBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    return _draft_json(service.artifact_assist_run(plan_id=plan_id, plan_sha256=body.plan_sha256), "workspace.artifact_assist.run")


@router.post("/api/v1/workspace/artifact-assist/proposals/{proposal_id}/decision")
def artifact_assist_decision(request: Request, proposal_id: str, body: AgentAssistDecisionBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    assert identity is not None
    actor, actor_role, principal = identity
    return _draft_json(service.artifact_assist_decide(proposal_id=proposal_id, proposal_sha256=body.proposal_sha256, decision=body.decision, modified_content=body.modified_content, actor=actor, actor_role=actor_role, session_principal=principal), "workspace.artifact_assist.decision")


@router.get("/api/v1/workspace/artifact-assist/proposals/{proposal_id}")
def artifact_assist_get(request: Request, proposal_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    return _draft_json(service.artifact_assist_get(proposal_id=proposal_id), "workspace.artifact_assist.get")


@router.post("/api/v1/workspace/artifact-reviews/imports/{import_id}/start")
def artifact_review_start_import(request: Request, import_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    assert identity is not None
    actor, actor_role, principal = identity
    return _draft_json(service.artifact_review_start_import(import_id=import_id, actor=actor, actor_role=actor_role, session_principal=principal), "workspace.artifact_reviews.start_import")


@router.post("/api/v1/workspace/artifact-reviews/documents/{document_id}/start")
def artifact_review_start_document(request: Request, document_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    assert identity is not None
    actor, actor_role, principal = identity
    return _draft_json(service.artifact_review_start_document(document_id=document_id, actor=actor, actor_role=actor_role, session_principal=principal), "workspace.artifact_reviews.start_document")


@router.get("/api/v1/workspace/artifact-reviews/{review_id}")
def artifact_review_status(request: Request, review_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    return _draft_json(service.artifact_review_status(review_id=review_id), "workspace.artifact_reviews.status")


@router.post("/api/v1/workspace/artifact-reviews/{review_id}/freeze")
def artifact_review_freeze(request: Request, review_id: str, body: ArtifactReviewFreezeBody, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    assert identity is not None
    actor, actor_role, principal = identity
    return _draft_json(service.artifact_review_freeze(review_id=review_id, execution_id=body.execution_id, actor=actor, actor_role=actor_role, session_principal=principal), "workspace.artifact_reviews.freeze")


@router.post("/api/v1/workspace/artifact-reviews/{review_id}/reconcile")
def artifact_review_reconcile(request: Request, review_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    identity, error = _draft_session_identity(request)
    if error: return error
    assert identity is not None
    actor, actor_role, principal = identity
    return _draft_json(service.artifact_review_reconcile(review_id=review_id, actor=actor, actor_role=actor_role, session_principal=principal), "workspace.artifact_reviews.reconcile")
