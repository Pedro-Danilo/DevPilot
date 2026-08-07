from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from devpilot_core.application.workspace_document_inspection_service import WorkspaceDocumentInspectionApplicationService
from devpilot_core.application.workspace_documents_service import WorkspaceDocumentsApplicationService
from devpilot_core.repo.git_adapter import GitAdapter


def _run(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _configure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str = "inventory-sales-local") -> tuple[Path, Path, WorkspaceDocumentInspectionApplicationService]:
    platform = tmp_path / "platform"
    workspace = tmp_path / "workspaces" / name
    platform.mkdir(parents=True)
    workspace.mkdir(parents=True)
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(workspace))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(workspace))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)
    documents = WorkspaceDocumentsApplicationService(platform)
    return platform, workspace, WorkspaceDocumentInspectionApplicationService(documents, platform)


def _document_id(service: WorkspaceDocumentInspectionApplicationService, name: str) -> str:
    listed = service.documents.list_documents(limit=250)
    return next(item["document_id"] for item in listed.data["nodes"] if item.get("name") == name)


def _init_repo(workspace: Path) -> None:
    _run(workspace, "init")
    _run(workspace, "config", "user.name", "DevPilot Test")
    _run(workspace, "config", "user.email", "devpilot@example.test")


def test_metadata_history_diff_links_and_frontmatter_are_read_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, workspace, service = _configure(tmp_path, monkeypatch)
    docs = workspace / "docs"
    docs.mkdir()
    target = docs / "product_vision.md"
    target.write_text("---\ntitle: Vision Pilot\ndoc_id: PILOT-VISION\nstatus: draft\n---\n# Vision\n\nSee [Architecture](architecture.md).\n", encoding="utf-8")
    (docs / "architecture.md").write_text("# Architecture\n\nBack to [Vision](product_vision.md).\n", encoding="utf-8")
    _init_repo(workspace)
    _run(workspace, "add", ".")
    _run(workspace, "commit", "-m", "Initial documents")
    target.write_text(target.read_text(encoding="utf-8") + "\nSQLite local.\n", encoding="utf-8")
    before = target.read_bytes()

    document_id = _document_id(service, "product_vision.md")
    metadata = service.metadata(document_id)
    history = service.history(document_id)
    diff = service.diff(document_id)
    links = service.links(document_id)

    assert metadata.ok and history.ok and diff.ok and links.ok
    assert metadata.data["document"]["frontmatter"]["fields"]["title"] == "Vision Pilot"
    assert metadata.data["document"]["git"]["status"]["unstaged"] is True
    assert metadata.data["document"]["git"]["last_commit"]["subject"] == "Initial documents"
    assert history.data["commits"][0]["author_name"] == "DevPilot Test"
    assert "+SQLite local." in diff.data["diff"]
    assert links.data["outgoing"][0]["resolved"] is True
    assert links.data["incoming"][0]["source_relative_path"] == "docs/architecture.md"
    assert target.read_bytes() == before
    assert metadata.data["safety"]["mutations_performed"] is False


def test_incremental_search_invalidates_by_hash_and_is_scoped_per_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    platform, workspace, service = _configure(tmp_path, monkeypatch)
    doc = workspace / "requirements.md"
    doc.write_text("Inventory requires SQLite persistence.", encoding="utf-8")

    first = service.search(query="SQLite")
    second = service.search(query="SQLite")
    assert first.ok and first.data["summary"]["cache_reindexed"] == 1
    assert second.data["summary"]["cache_reused"] == 1

    stat = doc.stat()
    doc.write_text("Inventory requires PostgreSQL locally.", encoding="utf-8")
    doc.touch()
    assert doc.stat().st_mtime_ns >= stat.st_mtime_ns
    third = service.search(query="PostgreSQL")
    assert third.data["summary"]["cache_reindexed"] == 1
    assert third.data["results"][0]["relative_path"] == "requirements.md"

    other = tmp_path / "workspaces" / "other-workspace"
    other.mkdir()
    (other / "secret.md").write_text("PostgreSQL secret workspace", encoding="utf-8")
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(other))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(other))
    other_service = WorkspaceDocumentInspectionApplicationService(WorkspaceDocumentsApplicationService(platform), platform)
    other_result = other_service.search(query="PostgreSQL")
    assert {item["relative_path"] for item in other_result.data["results"]} == {"secret.md"}
    assert all(item["relative_path"] != "requirements.md" for item in other_result.data["results"])


def test_git_adapter_handles_clean_dirty_untracked_renamed_deleted_and_detached(tmp_path: Path) -> None:
    workspace = tmp_path / "repo"
    workspace.mkdir()
    _init_repo(workspace)
    tracked = workspace / "doc.md"
    tracked.write_text("one\n", encoding="utf-8")
    _run(workspace, "add", "doc.md")
    _run(workspace, "commit", "-m", "add doc")
    adapter = GitAdapter(workspace)

    assert adapter.file_status("doc.md").data["status"]["clean"] is True
    tracked.write_text("one\ntwo\n", encoding="utf-8")
    assert adapter.file_status("doc.md").data["status"]["unstaged"] is True
    _run(workspace, "add", "doc.md")
    assert adapter.file_status("doc.md").data["status"]["staged"] is True
    _run(workspace, "commit", "-m", "update doc")

    (workspace / "new.md").write_text("new", encoding="utf-8")
    assert adapter.file_status("new.md").data["status"]["untracked"] is True
    _run(workspace, "mv", "doc.md", "renamed.md")
    assert adapter.file_status("renamed.md").data["status"]["renamed"] is True
    _run(workspace, "reset", "HEAD", "--", "renamed.md", "doc.md")
    if (workspace / "renamed.md").exists():
        (workspace / "renamed.md").unlink()
    tracked.write_text("restored", encoding="utf-8")
    _run(workspace, "add", "doc.md")
    _run(workspace, "commit", "-m", "restore doc")
    tracked.unlink()
    assert adapter.file_status("doc.md").data["status"]["deleted"] is True

    commit = _run(workspace, "rev-parse", "HEAD")
    _run(workspace, "checkout", "--detach", commit)
    history = adapter.file_history("doc.md", limit=10)
    assert history.ok is True
    assert history.data["summary"]["is_git_repo"] is True


def test_large_diff_is_truncated_with_explicit_finding(tmp_path: Path) -> None:
    workspace = tmp_path / "repo"
    workspace.mkdir()
    _init_repo(workspace)
    path = workspace / "large.md"
    path.write_text("base\n", encoding="utf-8")
    _run(workspace, "add", "large.md")
    _run(workspace, "commit", "-m", "base")
    path.write_text("base\n" + ("changed line\n" * 5000), encoding="utf-8")
    result = GitAdapter(workspace).file_diff("large.md", max_bytes=2048)
    assert result.ok is True
    assert result.data["summary"]["truncated"] is True
    assert any(finding.id == "GIT_FILE_DIFF_TRUNCATED" for finding in result.findings)


def test_empty_git_history_is_pass_with_empty_collection(tmp_path: Path) -> None:
    workspace = tmp_path / "repo"
    workspace.mkdir()
    _init_repo(workspace)
    (workspace / "doc.md").write_text("draft", encoding="utf-8")
    result = GitAdapter(workspace).file_history("doc.md")
    assert result.ok is True
    assert result.data["commits"] == []
