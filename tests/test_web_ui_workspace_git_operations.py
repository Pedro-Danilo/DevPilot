from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_uoc006_panel_exposes_progressive_governed_git_flow_and_no_go() -> None:
    panel = text("ui/web/src/components/WorkspaceGitOperationsPanel.ts")
    view = text("ui/web/src/pages/WorkspaceDocumentsView.ts")
    assert "WorkspaceGitOperationsPanel" in view
    for label in [
        "Operaciones Git gobernadas",
        "Planificar staging y commit",
        "Solicitar aprobación de staging",
        "Solicitar aprobación de commit",
        "Crear commit aprobado",
        "Crear branch local",
    ]:
        assert label in panel
    for forbidden_label in ["force push", "reset --hard", "rebase", "branch delete"]:
        assert forbidden_label.lower() in panel.lower()
    assert "implemented-initial" in panel.lower()
    assert "approval" in panel.lower()
    assert "workspaceGitHistory" in panel and "workspaceGitCompare" in panel
    assert "Actualizar status, history y compare" in panel


def test_uoc006_browser_never_constructs_free_git_command_or_path_argument() -> None:
    panel = text("ui/web/src/components/WorkspaceGitOperationsPanel.ts")
    client = text("ui/web/src/api/client.ts")
    # Browser uses typed API methods and opaque document ids; no subprocess/shell.
    assert "document_id" in panel or "documentId" in panel
    assert "subprocess" not in panel
    assert "child_process" not in panel
    assert "exec(" not in panel
    assert "child_process" not in panel
    assert "spawn(" not in panel
    assert "git " not in client.lower()
    assert "\'/workspace/git/" in client or "`/workspace/git/" in client


def test_uoc006_traceability_refresh_uses_exact_shared_neighbor_style() -> None:
    panel = text("ui/web/src/components/DocumentValidationPanel.ts")
    styles = text("ui/web/src/styles.css")
    assert "refreshButton.className = 'validation-action-button'" in panel
    assert "traceability-refresh-button" not in panel
    assert ".validation-action-button" in styles
    assert ".traceability-refresh-button" not in styles


def test_uoc006_responsive_panel_has_mobile_layout_contract() -> None:
    styles = text("ui/web/src/styles.css")
    assert ".uoc006-git-panel" in styles
    assert "@media" in styles
    assert ".uoc006-" in styles

def test_uoc006_commit_pass_survives_transient_document_reload() -> None:
    panel = text("ui/web/src/components/WorkspaceGitOperationsPanel.ts")
    view = text("ui/web/src/pages/WorkspaceDocumentsView.ts")
    assert "const transientCommitReload = Boolean(!document && currentDocument && commitExecution)" in panel
    assert "COMMIT PASS · estado preservado mientras se recarga el documento después del commit." in panel
    assert "if (before && document && before !== document.document_id) resetMutationState();" in panel
    assert "state.selected = undefined" in view
    assert "onCommitComplete" in view

