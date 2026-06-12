from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_34_manifest_checklist_and_closure_report_exist() -> None:
    manifest = json.loads(_read("docs/functional_sprint_34_manifest.json"))
    checklist = _read("docs/checklists/checklist_phase_b_exit.md")
    closure = _read("docs/audits/phase_b_operational_security_closure_report.md")

    assert manifest["sprint"] == "FUNC-SPRINT-34"
    assert manifest["status"] == "implemented"
    assert "src/devpilot_core/security/readiness.py" in manifest["created_files"]
    assert "src/devpilot_core/security/simulation.py" in manifest["created_files"]
    assert "tests/test_security_readiness.py" in manifest["tests"]
    assert "FB-EXIT-007" in checklist
    assert "Security readiness" in closure
    assert "implemented-initial" in closure


def test_sprint_34_readme_runbook_and_backlog_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_B_seguridad_operacional.md")

    assert "Último hito: `FUNC-SPRINT-43" in readme
    assert "Siguiente hito: `FUNC-SPRINT-44" in readme
    assert "## FUNC-SPRINT-34 — Security readiness operacional" in runbook
    assert "security readiness" in runbook
    assert 'phase_b_status: "closed"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-35"' in backlog
    assert "Estado de cierre posterior a FUNC-SPRINT-34" in backlog


def test_sprint_34_functional_backlog_points_to_phase_c_without_overclaiming() -> None:
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    phase_b_checklist = _read("docs/checklists/checklist_phase_b_exit.md")

    assert "Transición posterior a FUNC-SPRINT-34" in functional_backlog
    assert "Fase C" in functional_backlog
    assert "sandbox real" in functional_backlog
    assert "no hay sandbox real" in phase_b_checklist
    assert "no hay patch apply" in phase_b_checklist


def test_sprint_34_no_new_dependency_or_adr_required() -> None:
    manifest = json.loads(_read("docs/functional_sprint_34_manifest.json"))
    pyproject = _read("pyproject.toml")

    assert manifest["architectural_decision"]["required"] is False
    assert manifest["architectural_decision"]["adr"] is None
    assert "pytest" in pyproject
    assert "promptfoo" not in pyproject.lower()
