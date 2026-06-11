from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase_a_and_phase_b_backlogs_are_approved_and_reconciled() -> None:
    phase_a = _read("docs/devpilot_backlog_fase_A_baseline_industrial_minima.md")
    phase_b = _read("docs/devpilot_backlog_fase_B_seguridad_operacional.md")

    assert 'status: "approved"' in phase_a
    assert 'source_repo: "repo_DevPilot_Local_33.zip"' in phase_a
    assert 'phase_a_status: "closed"' in phase_a
    assert 'next_phase: "FASE-B-SEGURIDAD-OPERACIONAL"' in phase_a

    assert 'status: "approved"' in phase_b
    assert 'source_repo: "repo_DevPilot_Local_39.zip"' in phase_b
    assert 'baseline_dependency: "Fase A cerrada y aprobada mediante FUNC-SPRINT-27"' in phase_b
    assert 'first_open_sprint: "FUNC-SPRINT-35"' in phase_b
    assert 'phase_b_status: "closed"' in phase_b


def test_sprint_28_readme_runbook_and_backlog_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    phase_b = _read("docs/devpilot_backlog_fase_B_seguridad_operacional.md")

    assert "Modelo de aprobación humana y persistencia operacional — FUNC-SPRINT-28" in readme
    assert "FUNC-SPRINT-28 — Modelo de aprobación humana" in runbook
    assert "Estado de implementación Sprint 28" in phase_b
    assert "CLI de aprobación local — FUNC-SPRINT-29" in readme
    assert "FUNC-SPRINT-29 — CLI de aprobación" in runbook
    assert "Estado de implementación Sprint 28" in phase_b
    assert "Estado de implementación Sprint 29" in phase_b


def test_sprint_28_manifest_declares_approval_domain_and_no_adr_needed() -> None:
    payload = json.loads((ROOT / "docs/functional_sprint_28_manifest.json").read_text(encoding="utf-8"))

    assert payload["sprint"] == "FUNC-SPRINT-28"
    assert payload["status"] == "implemented"
    assert payload["architectural_decision"]["required"] is False
    assert "src/devpilot_core/approval/models.py" in payload["created_files"]
    assert "src/devpilot_core/approval/store.py" in payload["created_files"]
    assert "src/devpilot_core/store/local_store.py" in payload["modified_files"]
    assert payload["next_sprint"].startswith("FUNC-SPRINT-29")


def test_sprint_28_audit_documents_pass_block_and_limits() -> None:
    audit = _read("docs/audits/func_sprint_28_approval_domain_audit.md")

    for required in ["Propósito", "Funcionamiento técnico", "Criterios PASS", "Criterios BLOCK", "Riesgos"]:
        assert required in audit
    assert "implemented-initial" in audit
    assert "no autoriza todavía acciones críticas" in audit
    assert "PolicyEngine" in audit
