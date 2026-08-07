from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_uoc_002_ui_exposes_full_text_git_diff_and_links_without_shell() -> None:
    page = _read("ui/web/src/pages/WorkspaceDocumentsView.ts")
    panel = _read("ui/web/src/components/DocumentInspectionPanel.ts")
    client = _read("ui/web/src/api/client.ts")
    styles = _read("ui/web/src/styles.css")
    combined = "\n".join([page, panel, client])
    for required in ["searchWorkspaceDocuments", "workspaceDocumentHistory", "workspaceDocumentDiff", "workspaceDocumentLinks", "Frontmatter parseado", "Historial Git", "Diff read-only", "Relaciones documentales"]:
        assert required in combined
    for forbidden in ["child_process", "exec(", "spawn(", "node:fs", "innerHTML"]:
        assert forbidden not in combined
    assert "Índice incremental en memoria" in page
    assert "document-diff-viewer" in styles
    assert "@media (max-width: 560px)" in styles
