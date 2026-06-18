from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase_h_backlog_is_approved_after_phase_g_closure() -> None:
    backlog_h = _read("docs/devpilot_backlog_fase_H_capacidades_avanzadas.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    functional = _read("docs/functional_backlog_after_precode.md")

    assert 'status: "approved"' in backlog_h
    assert 'version: "1.1.0"' in backlog_h
    assert 'source_repo: "repo_DevPilot_Local_108.zip"' in backlog_h
    assert 'phase_h_status: "in_progress"' in backlog_h
    assert 'next_sprint: "FUNC-SPRINT-86"' in backlog_h
    assert "## 3.1 Decisión de aprobación" in backlog_h
    assert "FUNC-SPRINT-85" in readme
    assert "Fase H" in runbook
    assert "aprobación de fase h" in functional.lower()


def test_phase_h_approval_artifacts_exist() -> None:
    for path in [
        "docs/audits/phase_g_sprints_74_84_implementation_report.md",
        "docs/audits/phase_h_backlog_approval_audit.md",
    ]:
        assert (ROOT / path).exists(), path


def test_phase_h_backlog_preserves_safety_boundaries() -> None:
    backlog_h = _read("docs/devpilot_backlog_fase_H_capacidades_avanzadas.md")
    lowered = backlog_h.lower()
    for marker in [
        "policyengine",
        "miasi",
        "approval",
        "rag no puede responder sin evidencia",
        "mcp/conectores",
        "deny-by-default",
        "remote runners",
        "experimental",
    ]:
        assert marker in lowered
