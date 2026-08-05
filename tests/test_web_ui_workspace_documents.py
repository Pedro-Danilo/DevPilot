from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_workspace_documents_route_and_components_are_registered() -> None:
    main = _read("ui/web/src/main.ts")
    page = _read("ui/web/src/pages/WorkspaceDocumentsView.ts")
    tree = _read("ui/web/src/components/DocumentTree.ts")
    viewer = _read("ui/web/src/components/DocumentViewer.ts")
    client = _read("ui/web/src/api/client.ts")
    registry = _json(".devpilot/interfaces/ui_route_contract_registry.json")

    route = next(item for item in registry["routes"] if item["route_id"] == "ui.workspace-documents")
    assert route["path"] == "/workspace/documents"
    assert route["shows_mutation_controls"] is False
    assert route["remote_execution_allowed"] is False
    assert "api.workspace.documents.list" in route["allowed_api_routes"]
    assert "api.workspace.documents.read" in route["allowed_api_routes"]
    assert "api.workspace.documents.metadata" in route["allowed_api_routes"]
    assert "renderWorkspaceDocumentsView" in main
    assert "ui.workspace-documents" in page
    assert "identificadores opacos" in page
    assert "role', 'treeitem'" in tree
    assert "textContent" in viewer
    assert "innerHTML" not in viewer
    assert "/workspace/documents" in client


def test_workspace_documents_ui_has_required_states_and_responsive_contract() -> None:
    page = _read("ui/web/src/pages/WorkspaceDocumentsView.ts")
    styles = _read("ui/web/src/styles.css")
    package = _json("ui/web/package.json")
    index = _read("ui/web/index.html")

    for state in ["loading", "empty", "error", "block"]:
        assert f"'{state}'" in page
    assert "@media (max-width: 900px)" in styles
    assert "@media (max-width: 560px)" in styles
    assert "workspace-documents-layout" in styles
    assert package["devpilot"]["workspaceDocuments"] is True
    assert package["devpilot"]["workspaceDocumentsReadOnly"] is True
    assert package["devpilot"]["workspaceDocumentsOpaqueIds"] is True
    assert package["devpilot"]["workspaceDocumentsSymlinkFollowing"] is False
    assert "Content-Security-Policy" in index
    assert "object-src 'none'" in index


def test_document_viewer_never_executes_html_or_reads_filesystem() -> None:
    sources = "\n".join(
        _read(path)
        for path in [
            "ui/web/src/pages/WorkspaceDocumentsView.ts",
            "ui/web/src/components/DocumentTree.ts",
            "ui/web/src/components/DocumentViewer.ts",
            "ui/web/src/api/client.ts",
        ]
    )
    for forbidden in ["node:fs", "fs.readFile", "writeFile", "child_process", "devpilot_core", ".env"]:
        assert forbidden not in sources
    viewer = _read("ui/web/src/components/DocumentViewer.ts")
    assert "paragraph.textContent = rawLine" in viewer
    assert "pre.textContent" in viewer
