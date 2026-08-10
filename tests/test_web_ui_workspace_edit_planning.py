from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(rel): return (ROOT/rel).read_text(encoding='utf-8')

def test_uoc004_ui_preserves_manual_session_draft_immutable_plan_diff_preview_and_patch_evidence():
    ui=read('ui/web/src/components/DocumentEditPlanner.ts')
    assert 'sessionStorage.setItem' in ui and 'localStorage.setItem' not in ui and 'globalThis.localStorage' not in ui
    assert 'Guardar draft de sesión' in ui and 'Generar plan inmutable' in ui
    assert 'Diff completo' in ui and 'Preview seguro' in ui and 'Exportar .patch (no ejecutado)' in ui
    assert 'patch.apply genérico' in ui and 'auto-save' in ui.lower() and 'filesystem' in ui.lower()

def test_uoc004_ui_is_integrated_and_traceability_refresh_s3_uses_same_shared_button_class():
    view=read('ui/web/src/pages/WorkspaceDocumentsView.ts'); validation=read('ui/web/src/components/DocumentValidationPanel.ts'); css=read('ui/web/src/styles.css')
    assert 'createDocumentEditPlanner' in view and 'editPlanner' in view
    assert "planButton.className = 'validation-action-button'" in validation
    assert "executeButton.className = 'validation-action-button'" in validation
    assert "refreshButton.className = 'validation-action-button traceability-refresh-button'" in validation
    assert '.validation-action-button' in css
    assert '.traceability-refresh-button:not(:disabled)' not in css

def test_uoc004_css_supports_keyboard_responsive_and_bounded_diff():
    css=read('ui/web/src/styles.css')
    assert '.uoc004-editor:focus-visible' in css and 'max-height:32rem' in css and '@media (max-width:720px)' in css

def test_uoc004_patch_export_has_persistent_explicit_non_execution_feedback_before_download():
    ui=read('ui/web/src/components/DocumentEditPlanner.ts'); css=read('ui/web/src/styles.css')
    assert "Descarga solicitada · evidencia NO EJECUTADA." in ui
    assert "data-uoc004-export-feedback" in ui or "uoc004ExportFeedback" in ui
    assert "requested-not-executed" in ui and "requestAnimationFrame" in ui and "anchor.click()" in ui
    assert ui.index("exportFeedback = 'Descarga solicitada") < ui.index("anchor.click()")
    assert "no aplicó, no guardó, no stageó y no escribió" in ui
    assert ".uoc004-export-feedback" in css and ".uoc004-export-feedback:focus-visible" in css
