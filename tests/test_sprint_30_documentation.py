from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_30_readme_runbook_and_phase_b_backlog_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    phase_b = _read("docs/devpilot_backlog_fase_B_seguridad_operacional.md")

    assert "FUNC-SPRINT-30 — Binding de aprobaciones" in readme
    assert "FUNC-SPRINT-30 — Binding de aprobaciones" in runbook
    assert "Estado de implementación Sprint 30" in phase_b
    assert 'source_repo: "repo_DevPilot_Local_36.zip"' in phase_b
    assert 'first_open_sprint: "FUNC-SPRINT-32"' in phase_b
    assert "FUNC-SPRINT-31 — SafeSubprocessRunner" in readme
    assert "FUNC-SPRINT-31 — SafeSubprocessRunner" in runbook
    assert "FUNC-SPRINT-32 — tests.run" in readme


def test_sprint_30_manifest_declares_binding_and_no_adr_needed() -> None:
    payload = json.loads((ROOT / "docs/functional_sprint_30_manifest.json").read_text(encoding="utf-8"))

    assert payload["sprint"] == "FUNC-SPRINT-30"
    assert payload["status"] == "implemented"
    assert payload["architectural_decision"]["required"] is False
    assert "src/devpilot_core/approval/policy.py" in payload["created_files"]
    assert "src/devpilot_core/policy/engine.py" in payload["modified_files"]
    assert payload["next_sprint"].startswith("FUNC-SPRINT-31")


def test_sprint_30_audit_documents_limits_and_policy_binding() -> None:
    audit = _read("docs/audits/func_sprint_30_approval_policy_binding_audit.md")

    for required in ["Propósito", "Funcionamiento técnico", "Criterios PASS", "Criterios BLOCK", "Riesgos", "Veredicto"]:
        assert required in audit
    assert "implemented-initial" in audit
    assert "no ejecuta herramientas" in audit or "No ejecuta herramientas" in audit
    assert "ApprovalPolicyChecker" in audit
    assert "bypass global" in audit


def test_sprint_30_miasi_policy_matrix_references_approval_policy_checker() -> None:
    matrix = json.loads((ROOT / ".devpilot/miasi/policy_matrix.json").read_text(encoding="utf-8"))
    rules = {rule["rule_id"]: rule for rule in matrix["rules"]}

    assert "ApprovalPolicyChecker" in rules["AGENT_CRITICAL_TOOL_DENY"]["gate"]
    assert "ApprovalPolicyChecker" in rules["PATCH_APPLY_DENY"]["gate"]
    assert "ApprovalPolicyChecker" in _read("docs/06_miasi/policy_matrix.md")
