from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from devpilot_core.interfaces.api import create_app
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, API_TOKEN_HEADER

TOKEN = "uoc-002-test-token"
ROOT = Path(__file__).resolve().parents[1]


def _run(root: Path, *args: str) -> None:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr


def _client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, Path, str]:
    workspace = tmp_path / "inventory-sales-local"
    workspace.mkdir()
    document = workspace / "product_vision.md"
    document.write_text("---\ntitle: Pilot Vision\n---\n# Vision\n\nSQLite and [requirements](requirements.md).\n", encoding="utf-8")
    (workspace / "requirements.md").write_text("# Requirements\n\nInventory SQLite.\n", encoding="utf-8")
    _run(workspace, "init")
    _run(workspace, "config", "user.name", "API Test")
    _run(workspace, "config", "user.email", "api@example.test")
    _run(workspace, "add", ".")
    _run(workspace, "commit", "-m", "initial")
    document.write_text(document.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8")
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(workspace))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(workspace))
    app = create_app(ROOT, api_token=TOKEN)
    client = TestClient(app)
    client.headers.update({API_TOKEN_HEADER: TOKEN})
    listed = client.get("/api/v1/workspace/documents?limit=100").json()
    document_id = next(item["document_id"] for item in listed["data"]["nodes"] if item.get("name") == "product_vision.md")
    return client, workspace, document_id


def test_uoc_002_api_metadata_history_diff_search_and_links(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client, workspace, document_id = _client(tmp_path, monkeypatch)
    before = {p.relative_to(workspace).as_posix(): p.read_bytes() for p in workspace.rglob("*") if p.is_file() and ".git" not in p.parts}
    metadata = client.get(f"/api/v1/workspace/documents/{document_id}/metadata")
    history = client.get(f"/api/v1/workspace/documents/{document_id}/history")
    diff = client.get(f"/api/v1/workspace/documents/{document_id}/diff")
    search = client.get("/api/v1/workspace/documents/search?query=SQLite")
    links = client.get(f"/api/v1/workspace/documents/{document_id}/links")
    assert [r.status_code for r in [metadata, history, diff, search, links]] == [200, 200, 200, 200, 200]
    assert metadata.json()["data"]["document"]["frontmatter"]["fields"]["title"] == "Pilot Vision"
    assert history.json()["data"]["commits"][0]["author_name"] == "API Test"
    assert "+Changed." in diff.json()["data"]["diff"]
    assert search.json()["data"]["results"]
    assert links.json()["data"]["outgoing"][0]["resolved"] is True
    after = {p.relative_to(workspace).as_posix(): p.read_bytes() for p in workspace.rglob("*") if p.is_file() and ".git" not in p.parts}
    assert before == after


def test_uoc_002_api_blocks_free_git_refs_and_path_shaped_ids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client, _, document_id = _client(tmp_path, monkeypatch)
    unsafe_ref = client.get(f"/api/v1/workspace/documents/{document_id}/diff?base_ref=main%20--output=/tmp/x")
    traversal = client.get("/api/v1/workspace/documents/..%2Fsecret/history")
    assert unsafe_ref.status_code in {400, 403, 422}
    assert traversal.status_code in {400, 403, 404, 422}


def test_uoc_002_routes_have_explicit_policy_bindings() -> None:
    expected = {
        ("GET", "/api/v1/workspace/documents/{document_id}/history"),
        ("GET", "/api/v1/workspace/documents/{document_id}/diff"),
        ("GET", "/api/v1/workspace/documents/search"),
        ("GET", "/api/v1/workspace/documents/{document_id}/links"),
    }
    assert expected <= set(API_ROUTE_POLICIES)
