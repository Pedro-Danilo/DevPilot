from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_d05_project_status_next_story_routes_to_story_code() -> None:
    service = (ROOT / "src/devpilot_core/application/guided_sdlc_service.py").read_text(encoding="utf-8")
    view = (ROOT / "ui/web/src/pages/ProjectStatusView.ts").read_text(encoding="utf-8")
    assert '"navigation_target": "ui.story-code-workbench"' in service
    assert "Continuar con siguiente story READY" in view
    assert "navigationPathFromServerTarget(cycleTarget)" in view
    assert "La selección/activación se realiza en Story Code Workbench" in view


def test_d05_story_code_exposes_recommended_story_without_forcing_order() -> None:
    activation = (ROOT / "src/devpilot_core/application/story_activation_service.py").read_text(encoding="utf-8")
    view = (ROOT / "ui/web/src/pages/StoryCodeWorkbenchView.ts").read_text(encoding="utf-8")
    assert '"recommended_story_id": candidates[0]["story_id"] if available and candidates else None' in activation
    assert "recommendedStoryId" in view
    assert "RECOMENDADA" in view
    assert "siguiente en Sprint" in view
    assert "Preparar contexto recomendado" in view
    assert "Preparar contexto (alternativa)" in view
    # READY alternatives remain legitimate Owner choices; current StoryExecution still prevents parallel activation.
    assert "prepare.disabled=!canAuthor||Boolean(current&&String(current.status)!=='DONE')" in view
