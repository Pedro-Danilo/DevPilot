from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _json(relative_path: str):
    return json.loads(_read(relative_path))


def test_sprint_48_readme_runbook_backlog_and_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_D_ia_local_gobernada.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "Último hito: `FUNC-SPRINT-73" in readme
    assert "Siguiente hito: `FUNC-SPRINT-74" in readme
    assert "## FUNC-SPRINT-48 — Model governance: health, capability matrix y budget ledger" in readme
    assert "python -m devpilot_core model health --json" in runbook
    assert "python -m devpilot_core model capabilities --json" in runbook
    assert "python -m devpilot_core model budget status --json" in runbook
    assert "## FUNC-SPRINT-48 — Model governance: health, capability matrix y budget ledger" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-56"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-55"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-56"' in backlog
    assert "## Estado de implementación Sprint 48" in backlog
    assert 'next_sprint: "FUNC-SPRINT-74"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-48" in functional_backlog
    assert "## Actualización FUNC-SPRINT-48 — Pruebas de Model Governance" in test_strategy


def test_sprint_48_miasi_and_model_governance_docs_are_synchronized() -> None:
    tools = {item["tool_id"]: item for item in _json(".devpilot/miasi/tool_registry.json")["tools"]}
    policies = {item["rule_id"]: item for item in _json(".devpilot/miasi/policy_matrix.json")["rules"]}
    tool_card = _read("docs/06_miasi/tool_card.md")
    policy_card = _read("docs/06_miasi/policy_card.md")

    assert tools["model.capabilities.read"]["status"] == "implemented-initial"
    assert tools["model.budget.status"]["status"] == "implemented-initial"
    assert "MODEL_CAPABILITIES_READ_ALLOW" in tools["model.capabilities.read"]["policy_rule_ids"]
    assert "MODEL_BUDGET_LEDGER_ALLOW" in tools["model.budget.status"]["policy_rule_ids"]
    assert policies["MODEL_CAPABILITIES_READ_ALLOW"]["default_effect"] == "allow"
    assert policies["MODEL_BUDGET_LEDGER_ALLOW"]["default_effect"] == "allow"
    assert "FUNC-SPRINT-48" in tool_card
    assert "NoRawPrompts" in policies["MODEL_BUDGET_LEDGER_ALLOW"]["gate"]
    assert "FUNC-SPRINT-48" in policy_card


def test_sprint_48_manifest_and_audit_exist() -> None:
    manifest = _json("docs/functional_sprint_48_manifest.json")
    audit = _read("docs/audits/func_sprint_48_model_governance_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-48"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert "src/devpilot_core/modeling/health.py" in manifest["created_files"]
    assert "src/devpilot_core/modeling/capabilities.py" in manifest["created_files"]
    assert "src/devpilot_core/modeling/budget.py" in manifest["created_files"]
    assert "tests/test_model_governance.py" in manifest["tests"]
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-49")
    assert "## Criterios PASS" in audit
    assert "## Criterios BLOCK" in audit
