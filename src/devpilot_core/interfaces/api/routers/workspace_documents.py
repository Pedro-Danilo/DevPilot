from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from devpilot_core.application import ApplicationService

from ..dependencies import get_application_service
from ..models import dispatch_application_request

router = APIRouter(tags=["workspace-documents"])


def _json(payload: dict[str, Any], status_code: int) -> JSONResponse:
    return JSONResponse(content=payload, status_code=status_code)


@router.get("/api/v1/workspace/documents")
def list_workspace_documents(
    limit: int = Query(default=50, ge=1, le=250),
    offset: int = Query(default=0, ge=0, le=100000),
    query: str | None = Query(default=None, max_length=200),
    extension: str | None = Query(default=None, max_length=16),
    category: str | None = Query(default=None, max_length=64),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="workspace.documents.list",
            payload={"limit": limit, "offset": offset, "query": query, "extension": extension, "category": category},
        )
    )


@router.get("/api/v1/workspace/documents/search")
def search_workspace_documents(
    query: str = Query(min_length=2, max_length=200),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=100000),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.documents.search", payload={"query": query, "limit": limit, "offset": offset}))


@router.get("/api/v1/workspace/documents/{document_id}/metadata")
def workspace_document_metadata(document_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.documents.metadata", payload={"document_id": document_id}))


@router.get("/api/v1/workspace/documents/{document_id}/history")
def workspace_document_history(
    document_id: str,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0, le=1000),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.documents.history", payload={"document_id": document_id, "limit": limit, "offset": offset}))


@router.get("/api/v1/workspace/documents/{document_id}/diff")
def workspace_document_diff(
    document_id: str,
    base_ref: str = Query(default="HEAD", min_length=4, max_length=40),
    max_bytes: int = Query(default=262144, ge=1, le=1048576),
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.documents.diff", payload={"document_id": document_id, "base_ref": base_ref, "max_bytes": max_bytes}))


@router.get("/api/v1/workspace/documents/{document_id}/links")
def workspace_document_links(document_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.documents.links", payload={"document_id": document_id}))


@router.get("/api/v1/workspace/documents/{document_id}")
def read_workspace_document(document_id: str, service: ApplicationService = Depends(get_application_service)) -> JSONResponse:
    return _json(*dispatch_application_request(service, operation="workspace.documents.read", payload={"document_id": document_id}))
