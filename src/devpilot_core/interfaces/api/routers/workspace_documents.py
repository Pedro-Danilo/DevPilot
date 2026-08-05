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
            payload={
                "limit": limit,
                "offset": offset,
                "query": query,
                "extension": extension,
                "category": category,
            },
        )
    )


@router.get("/api/v1/workspace/documents/{document_id}")
def read_workspace_document(
    document_id: str,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="workspace.documents.read",
            payload={"document_id": document_id},
        )
    )


@router.get("/api/v1/workspace/documents/{document_id}/metadata")
def workspace_document_metadata(
    document_id: str,
    service: ApplicationService = Depends(get_application_service),
) -> JSONResponse:
    return _json(
        *dispatch_application_request(
            service,
            operation="workspace.documents.metadata",
            payload={"document_id": document_id},
        )
    )
