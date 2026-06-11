from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_27_readme_runbook_backlog_and_phase_a_closure_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_A_baseline_industrial_minima.md")
    checklist = _read("docs/checklists/checklist_phase_a_exit.md")
    closure = _read("docs/audits/phase_a_baseline_industrial_minima_closure_report.md")

    assert "FUNC-SPRINT-27 — Architecture/code drift" in readme
    assert "FUNC-SPRINT-27 — Architecture/code drift" in runbook
    assert "Estado de implementación Sprint 27" in backlog
    assert "phase_a_status: \"closed\"" in backlog
    assert "next_phase: \"FASE-B-SEGURIDAD-OPERACIONAL\"" in backlog
    assert "FUNC-SPRINT-27" in checklist
    assert "Baseline Industrial Mínima" in closure


def test_sprint_27_manifest_declares_drift_files_and_no_adr_needed() -> None:
    payload = json.loads((ROOT / "docs/functional_sprint_27_manifest.json").read_text(encoding="utf-8"))

    assert payload["sprint"] == "FUNC-SPRINT-27"
    assert payload["status"] == "implemented"
    assert payload["phase_a_closure"] == "closed"
    assert payload["architectural_decision"]["required"] is False
    assert "src/devpilot_core/traceability/architecture_drift.py" in payload["created_files"]
    assert "docs/checklists/checklist_phase_a_exit.md" in payload["created_files"]
    assert "tests/test_architecture_drift.py" in payload["created_files"]
    assert payload["next_sprint"].startswith("FASE-B")


def test_sprint_27_audit_documents_controls_and_limits() -> None:
    audit = _read("docs/audits/func_sprint_27_architecture_drift_audit.md")

    for required in ["Propósito", "Funcionamiento técnico", "Criterios PASS", "Criterios BLOCK", "Riesgos"]:
        assert required in audit
    assert "implemented-initial" in audit
    assert "no reemplaza análisis arquitectónico manual" in audit
    assert "ARCHITECTURE_DRIFT_CODE_MODULE_UNDOCUMENTED" in audit


def test_phase_a_exit_checklist_documents_pass_block_and_future_limits() -> None:
    checklist = _read("docs/checklists/checklist_phase_a_exit.md")

    assert "Schema Validator" in checklist
    assert "Traceability Engine" in checklist
    assert "architecture-drift" in checklist
    assert "No se habilitaron acciones destructivas" in checklist
    assert "BLOCK" in checklist
