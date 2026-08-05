from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from devpilot_core.application import workspace_documents_service as workspace_documents_module
from devpilot_core.application.workspace_documents_service import (
    MAX_INLINE_BYTES,
    WorkspaceDocumentsApplicationService,
)


def _configure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    platform = tmp_path / "platform"
    workspace = tmp_path / "workspaces" / "inventory-sales-local"
    platform.mkdir(parents=True)
    workspace.mkdir(parents=True)
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(workspace))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(workspace))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)
    return platform, workspace


def test_document_index_and_read_are_bounded_read_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    platform, workspace = _configure(tmp_path, monkeypatch)
    (workspace / "docs" / "architecture").mkdir(parents=True)
    (workspace / "product_vision.md").write_text("# Vision\n\nSafe <script>alert(1)</script>\n", encoding="utf-8")
    (workspace / "docs" / "architecture" / "architecture_document.md").write_text("# Architecture\n", encoding="utf-8")
    (workspace / "requirements_specification.json").write_text(json.dumps({"requirements": ["REQ-001"]}), encoding="utf-8")
    before = {path.relative_to(workspace).as_posix(): path.read_bytes() for path in workspace.rglob("*") if path.is_file()}

    service = WorkspaceDocumentsApplicationService(platform)
    listed = service.list_documents(limit=100)

    assert listed.ok is True, listed.to_dict()
    assert listed.data["summary"]["documents_total"] == 3
    assert listed.data["summary"]["mutations_performed"] is False
    documents = [item for item in listed.data["nodes"] if item["kind"] == "document"]
    assert all(item["document_id"].startswith("doc_") for item in documents)
    assert all(str(workspace) not in json.dumps(item) for item in documents)

    vision = next(item for item in documents if item["name"] == "product_vision.md")
    read = service.read_document(vision["document_id"])
    metadata = service.document_metadata(vision["document_id"])

    assert read.ok is True
    assert read.data["document"]["content"].startswith("# Vision")
    assert read.data["document"]["relative_path"] == "product_vision.md"
    assert read.data["document"]["sha256"] == metadata.data["document"]["sha256"]
    assert read.data["safety"]["absolute_paths_accepted_from_browser"] is False
    after = {path.relative_to(workspace).as_posix(): path.read_bytes() for path in workspace.rglob("*") if path.is_file()}
    assert after == before


def test_document_index_excludes_sensitive_runtime_and_unsupported_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    platform, workspace = _configure(tmp_path, monkeypatch)
    for directory in [".git", ".venv", "node_modules", "outputs/reports", ".devpilot/private"]:
        (workspace / directory).mkdir(parents=True, exist_ok=True)
    (workspace / ".env").write_text("SECRET=value", encoding="utf-8")
    (workspace / "outputs" / "reports" / "report.json").write_text("{}", encoding="utf-8")
    (workspace / ".devpilot" / "private" / "secret.json").write_text("{}", encoding="utf-8")
    (workspace / ".devpilot" / "project.yaml").write_text("project:\n  id: demo\n", encoding="utf-8")
    (workspace / "image.png").write_bytes(b"PNG")
    (workspace / "notes.txt").write_text("safe", encoding="utf-8")
    (workspace / "alternate:stream.txt").write_text("blocked ADS-like name", encoding="utf-8")

    result = WorkspaceDocumentsApplicationService(platform).list_documents(limit=250)
    paths = {item["relative_path"] for item in result.data["nodes"] if item["kind"] == "document"}

    assert "notes.txt" in paths
    assert ".devpilot/project.yaml" in paths
    assert ".env" not in paths
    assert "outputs/reports/report.json" not in paths
    assert ".devpilot/private/secret.json" not in paths
    assert "image.png" not in paths
    assert "alternate:stream.txt" not in paths


def test_link_guard_excludes_link_like_entries_without_host_symlink_privilege(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    platform, workspace = _configure(tmp_path, monkeypatch)
    guarded_path = workspace / "outside-link.md"
    guarded_path.write_text("fixture content must never be indexed", encoding="utf-8")
    original_guard = workspace_documents_module._is_link_or_reparse

    def deterministic_link_guard(candidate: str | Path) -> bool:
        path = Path(candidate)
        if path == guarded_path:
            return True
        return original_guard(path)

    monkeypatch.setattr(
        workspace_documents_module,
        "_is_link_or_reparse",
        deterministic_link_guard,
    )

    result = WorkspaceDocumentsApplicationService(platform).list_documents(limit=250)
    paths = {item["relative_path"] for item in result.data["nodes"]}

    assert "outside-link.md" not in paths
    assert any(
        finding.id == "WORKSPACE_DOCUMENT_LINK_SKIPPED"
        for finding in result.findings
    )


def test_large_file_is_not_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    platform, workspace = _configure(tmp_path, monkeypatch)
    large = workspace / "large.md"
    large.write_bytes(b"x" * (MAX_INLINE_BYTES + 1))

    result = WorkspaceDocumentsApplicationService(platform).list_documents(limit=250)
    nodes = result.data["nodes"]
    large_node = next(item for item in nodes if item["relative_path"] == "large.md")

    assert large_node["readable"] is False
    blocked = WorkspaceDocumentsApplicationService(platform).read_document(
        large_node["document_id"]
    )
    assert blocked.exit_code.value == 2
    assert blocked.findings[-1].id == "WORKSPACE_DOCUMENT_SIZE_LIMIT_BLOCK"


def test_document_id_cannot_be_used_as_path_authority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    platform, workspace = _configure(tmp_path, monkeypatch)
    (workspace / "product_vision.md").write_text("# Vision", encoding="utf-8")
    service = WorkspaceDocumentsApplicationService(platform)

    for attacker_value in ["../.env", str(workspace / "product_vision.md"), "doc_../../.env", "file:///etc/passwd"]:
        result = service.read_document(attacker_value)
        assert result.ok is False
        assert result.exit_code.value in {1, 2}
        assert result.data["summary"]["mutations_performed"] is False


def test_filters_and_pagination_are_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    platform, workspace = _configure(tmp_path, monkeypatch)
    for name in ["product_vision.md", "mvp_scope.md", "requirements_specification.md", "security_threat_model.yaml", "notes.txt"]:
        (workspace / name).write_text(f"# {name}\n", encoding="utf-8")
    service = WorkspaceDocumentsApplicationService(platform)

    product = service.list_documents(limit=10, category="product")
    markdown_page = service.list_documents(limit=2, extension="md", offset=0)
    markdown_next = service.list_documents(limit=2, extension=".md", offset=2)

    product_names = {item["name"] for item in product.data["nodes"] if item["kind"] == "document"}
    assert {"product_vision.md", "mvp_scope.md"} <= product_names
    assert markdown_page.data["summary"]["matching_total"] == 3
    assert markdown_page.data["summary"]["next_offset"] == 2
    assert markdown_next.data["summary"]["returned_total"] == 1
