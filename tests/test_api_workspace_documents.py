from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from devpilot_core.interfaces.api import create_app
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, API_TOKEN_HEADER

TEST_TOKEN = "uoc-001-test-token"
ROOT = Path(__file__).resolve().parents[1]


def _workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    platform = tmp_path / "platform"
    workspace = tmp_path / "workspaces" / "inventory-sales-local"
    platform.mkdir(parents=True)
    workspace.mkdir(parents=True)
    (workspace / "product_vision.md").write_text("# Product vision\n", encoding="utf-8")
    (workspace / "requirements_specification.json").write_text(json.dumps({"id": "REQ-001"}), encoding="utf-8")
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(workspace))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(workspace))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)
    return platform, workspace


def _client(platform: Path, authenticated: bool = True) -> TestClient:
    client = TestClient(create_app(ROOT, api_token=TEST_TOKEN))
    if authenticated:
        client.headers.update({API_TOKEN_HEADER: TEST_TOKEN})
    return client


def test_workspace_document_api_list_read_metadata_and_zero_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    platform, workspace = _workspace(tmp_path, monkeypatch)
    before = {path.relative_to(workspace).as_posix(): path.read_bytes() for path in workspace.rglob("*") if path.is_file()}
    client = _client(platform)

    listed = client.get("/api/v1/workspace/documents?limit=100&query=vision")
    assert listed.status_code == 200, listed.text
    payload = listed.json()
    assert payload["operation"] == "workspace.documents.list"
    document = next(item for item in payload["data"]["nodes"] if item["kind"] == "document")
    assert document["document_id"].startswith("doc_")

    read = client.get(f"/api/v1/workspace/documents/{document['document_id']}")
    metadata = client.get(f"/api/v1/workspace/documents/{document['document_id']}/metadata")
    assert read.status_code == 200
    assert metadata.status_code == 200
    assert read.json()["data"]["document"]["content"].startswith("# Product")
    assert metadata.json()["data"]["document"]["sha256"] == read.json()["data"]["document"]["sha256"]
    after = {path.relative_to(workspace).as_posix(): path.read_bytes() for path in workspace.rglob("*") if path.is_file()}
    assert after == before


def test_workspace_document_api_requires_token_and_explicit_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    platform, _ = _workspace(tmp_path, monkeypatch)
    unauthorized = _client(platform, authenticated=False).get("/api/v1/workspace/documents")
    assert unauthorized.status_code == 401

    monkeypatch.delenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", raising=False)
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)
    blocked = _client(platform).get("/api/v1/workspace/documents")
    assert blocked.status_code == 403
    assert blocked.json()["findings"][-1]["id"] == "WORKSPACE_DOCUMENT_CONTEXT_REQUIRED_BLOCK"


def test_workspace_document_api_rejects_path_like_or_unknown_ids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    platform, _ = _workspace(tmp_path, monkeypatch)
    client = _client(platform)
    invalid = client.get("/api/v1/workspace/documents/..%2F.env")
    unknown = client.get("/api/v1/workspace/documents/doc_AAAAAAAAAAAAAAAAAAAAAAAA")
    assert invalid.status_code in {400, 403}
    assert unknown.status_code == 400
    assert "not found" in unknown.json()["message"].lower()


def test_uoc_001_api_routes_have_explicit_policy_bindings() -> None:
    expected = {
        ("GET", "/api/v1/workspace/documents"),
        ("GET", "/api/v1/workspace/documents/{document_id}"),
        ("GET", "/api/v1/workspace/documents/{document_id}/metadata"),
    }
    assert expected <= set(API_ROUTE_POLICIES)
