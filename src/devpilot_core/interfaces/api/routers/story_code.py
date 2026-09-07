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
