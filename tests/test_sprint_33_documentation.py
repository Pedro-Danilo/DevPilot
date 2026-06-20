from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_33_manifest_and_audit_exist_and_are_synchronized() -> None:
    manifest = json.loads(_read("docs/functional_sprint_33_manifest.json"))
    audit = _read("docs/audits/func_sprint_33_security_hardening_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-33"
    assert manifest["status"] == "implemented"
    assert "src/devpilot_core/policy/prompt_guard.py" in manifest["created_files"]
    assert "src/devpilot_core/policy/tool_injection_guard.py" in manifest["created_files"]
    assert "tests/test_prompt_injection_guard.py" in manifest["tests"]
    assert "tests/test_secret_guard_hardening.py" in manifest["tests"]
    assert "FUNC-SPRINT-33" in audit
    assert "SecretGuard" in audit
    assert "PromptInjectionGuard" in audit
    assert "ToolInjectionGuard" in audit
    assert "implemented-initial" in audit


def test_sprint_33_readme_runbook_and_backlog_point_to_sprint_34() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_B_seguridad_operacional.md")

    assert "Último hito: `FUNC-SPRINT-99" in readme
    assert "Siguiente hito: `POST-H-001" in readme
    assert "FUNC-SPRINT-33" in runbook
    assert "PromptInjectionGuard" in runbook
    assert "ToolInjectionGuard" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-35"' in backlog
    assert "`FUNC-SPRINT-33` queda implementado" in backlog


def test_sprint_33_security_docs_are_synchronized() -> None:
    threat_model = _read("docs/03_security/security_threat_model.md")
    policy_card = _read("docs/06_miasi/policy_card.md")
    tool_card = _read("docs/06_miasi/tool_card.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")

    assert "FUNC-SPRINT-33" in threat_model
    assert "PromptInjectionGuard" in policy_card
    assert "ToolInjectionGuard" in tool_card
    assert "Security hardening inicial" in functional_backlog
    assert "FUNC-SPRINT-35" in functional_backlog or "Fase C" in functional_backlog


def test_sprint_33_no_new_dependency_or_adr_required() -> None:
    manifest = json.loads(_read("docs/functional_sprint_33_manifest.json"))
    pyproject = _read("pyproject.toml")

    assert manifest["architectural_decision"]["required"] is False
    assert manifest["architectural_decision"]["adr"] is None
    assert "No usa LLM judge" in _read("docs/05_operations/runbook.md")
    assert "promptfoo" not in pyproject.lower()
