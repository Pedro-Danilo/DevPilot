from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_uoc003_web_ui_exposes_governed_validation_and_traceability() -> None:
    component = (ROOT / "ui/web/src/components/DocumentValidationPanel.ts").read_text(encoding="utf-8")
    view = (ROOT / "ui/web/src/pages/WorkspaceDocumentsView.ts").read_text(encoding="utf-8")
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    viewer = (ROOT / "ui/web/src/components/DocumentViewer.ts").read_text(encoding="utf-8")
    assert "Preparar validación estricta" in component
    assert "Ejecutar plan" in component
    assert "Findings por severidad" in component
    assert "Matriz requisito → historia → riesgo/control → prueba" in component
    assert "Bridges CLI residuales registrados" in component
    assert "cli.docs-governance.validate" in component
    assert "cli.industrial-readiness.check" in component
    assert "cli.workspace.readiness-preview" in component
    assert "jobs_synchronous_preliminary" not in component
    assert "createDocumentValidationPanel" in view
    assert "workspace/validations/plan" in client
    assert "workspace/validations/execute" in client
    assert "workspace/traceability" in client
    assert "data-source-line" in viewer
    assert "scrollIntoView" in viewer


def test_uoc003_ui_preserves_no_shell_and_no_free_form_validator_command() -> None:
    sources = "\n".join(path.read_text(encoding="utf-8") for path in [
        ROOT / "ui/web/src/components/DocumentValidationPanel.ts",
        ROOT / "ui/web/src/api/client.ts",
    ])
    forbidden = ["child_process", "subprocess", "powershell", "cmd.exe", "shell=true", "validator_command"]
    assert not any(marker in sources.lower() for marker in forbidden)

def _relative_luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    channels = [int(value[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    first = _relative_luminance(foreground)
    second = _relative_luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def test_uoc003_validation_surfaces_have_explicit_readable_contrast_and_focus() -> None:
    css = (ROOT / "ui/web/src/styles.css").read_text(encoding="utf-8")
    assert "--uoc003-surface-bg: #ffffff;" in css
    assert "--uoc003-surface-text: #182033;" in css
    assert "--uoc003-muted-text: #53627a;" in css
    assert "--uoc003-link: #155eef;" in css
    assert "background: var(--uoc003-surface-bg);" in css
    assert "color: var(--uoc003-surface-text);" in css
    assert ".document-validation-plan details > summary:focus-visible" in css
    assert ".button-link:focus-visible" in css
    assert "background: color-mix(in srgb, var(--panel-bg, #171c26) 94%, transparent);" not in css
    assert _contrast_ratio("#182033", "#ffffff") >= 7.0
    assert _contrast_ratio("#53627a", "#f8fafc") >= 4.5
    assert _contrast_ratio("#0d6532", "#f8fafc") >= 4.5
    assert _contrast_ratio("#725100", "#f8fafc") >= 4.5
    assert _contrast_ratio("#92211b", "#f8fafc") >= 4.5
    assert _contrast_ratio("#155eef", "#ffffff") >= 4.5



def test_uoc003_findings_navigation_is_bounded_feedback_driven_and_render_resilient() -> None:
    component = (ROOT / "ui/web/src/components/DocumentValidationPanel.ts").read_text(encoding="utf-8")
    view = (ROOT / "ui/web/src/pages/WorkspaceDocumentsView.ts").read_text(encoding="utf-8")
    viewer = (ROOT / "ui/web/src/components/DocumentViewer.ts").read_text(encoding="utf-8")
    css = (ROOT / "ui/web/src/styles.css").read_text(encoding="utf-8")

    assert "const pageSize = 25;" in component
    assert "Filtrar severidad" in component
    assert "Findings anteriores" in component
    assert "Findings siguientes" in component
    assert "navigationPending" in component
    assert "Documento abierto:" in component

    assert "document.createDocumentFragment()" in view
    assert "renderGuarded" in view
    assert "workspace-documents-render-boundary" in view
    assert "listRequestSequence" in view
    assert "documentRequestSequence" in view
    assert "La UI aisló un error de render sin perder el estado operativo" in view

    assert "findNavigationTarget" in viewer
    assert "Volver a findings" in viewer
    assert "Finding abierto:" in viewer
    assert "String(resource.category ?? 'documentation').toUpperCase()" in viewer

    assert ".validation-findings-toolbar" in css
    assert ".validation-findings-pagination" in css
    assert ".workspace-documents-render-boundary" in css
    assert ".document-navigation-back" in css


def test_uoc003_v104_navigation_dom_order_context_and_traceability_feedback() -> None:
    component = (ROOT / "ui/web/src/components/DocumentValidationPanel.ts").read_text(encoding="utf-8")
    view = (ROOT / "ui/web/src/pages/WorkspaceDocumentsView.ts").read_text(encoding="utf-8")
    viewer = (ROOT / "ui/web/src/components/DocumentViewer.ts").read_text(encoding="utf-8")
    css = (ROOT / "ui/web/src/styles.css").read_text(encoding="utf-8")

    assert "section.insertBefore(notice, content)" not in viewer
    assert "const navigationActive = Boolean(options.navigationOrigin);" in viewer
    assert viewer.index("section.append(notice);") < viewer.index("section.append(content);")
    assert "Fuente de trazabilidad abierta" in viewer
    assert "Volver a trazabilidad" in viewer
    assert "Volver a findings" in viewer
    assert "section.scrollIntoView" in viewer

    assert "navigationOrigin?: 'finding' | 'traceability'" in view
    assert "validationPanel.querySelector<HTMLElement>(selector)" in view
    assert "'.document-traceability'" in view
    assert "'.validation-findings'" in view

    assert "onNavigate(navigation, 'finding')" in component
    assert "onNavigate(navigation, 'traceability')" in component
    assert "Recargar trazabilidad" in component
    assert "La matriz se cargó automáticamente al ejecutar el plan" in component
    assert "navigationContext === 'traceability'" in component

    assert "max-height: 28rem;" in css
    assert "overflow-y: auto;" in css
    assert ".traceability-refresh-button:not(:disabled)" in css
