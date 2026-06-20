from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_29_readme_runbook_and_phase_b_backlog_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    phase_b = _read("docs/devpilot_backlog_fase_B_seguridad_operacional.md")

    assert "CLI de aprobación local — FUNC-SPRINT-29" in readme
    assert "FUNC-SPRINT-29 — CLI de aprobación" in runbook
    assert "Estado de implementación Sprint 29" in phase_b
    assert "FUNC-SPRINT-30 — Binding de aprobaciones" in readme
    assert "FUNC-SPRINT-30 — Binding de aprobaciones" in runbook


def test_sprint_29_manifest_declares_cli_and_no_adr_needed() -> None:
    payload = json.loads((ROOT / "docs/functional_sprint_29_manifest.json").read_text(encoding="utf-8"))

    assert payload["sprint"] == "FUNC-SPRINT-29"
    assert payload["status"] == "implemented"
    assert payload["architectural_decision"]["required"] is False
    assert "src/devpilot_core/approval/service.py" in payload["created_files"]
    assert "src/devpilot_core/cli.py" in payload["modified_files"]
    assert payload["next_sprint"].startswith("FUNC-SPRINT-30")


def test_sprint_29_audit_documents_limits_and_pass_block() -> None:
    audit = _read("docs/audits/func_sprint_29_approval_cli_audit.md")

    for required in ["Propósito", "Funcionamiento técnico", "Criterios PASS", "Criterios BLOCK", "Riesgos", "Veredicto"]:
        assert required in audit
    assert "implemented-initial" in audit
    assert "no autoriza todavía ejecución" in audit
    assert "PolicyEngine" in audit


def test_sprint_29_does_not_claim_policy_binding_or_tool_execution() -> None:
    phase_b = _read("docs/devpilot_backlog_fase_B_seguridad_operacional.md")
    audit = _read("docs/audits/func_sprint_29_approval_cli_audit.md")

    assert "`approval_id` ya se conecta con `PolicyEngine`" in phase_b
    assert "no se ejecutan tests, patches, refactors, deploys ni Git write" in phase_b
    assert "no autoriza todavía ejecución de herramientas críticas" in audit
