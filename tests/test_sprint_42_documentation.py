from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_42_manifest_and_audit_exist() -> None:
    manifest = json.loads(_read("docs/functional_sprint_42_manifest.json"))
    audit = _read("docs/audits/func_sprint_42_rollback_manager_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-42"
    assert manifest["status"] == "implemented"
    assert "src/devpilot_core/changes/rollback.py" in manifest["created_files"]
    assert "tests/test_rollback_manager.py" in manifest["tests"]
    assert manifest["architectural_decision"]["required"] is False
    assert "RollbackManager" in audit
    assert "backup local" in audit
    assert "rollback execute" in audit


def test_sprint_42_readme_runbook_backlog_and_test_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_C_ingenieria_repositorio.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")
    gitignore = _read(".gitignore")

    assert "Último hito: `FUNC-SPRINT-87" in readme
    assert "Siguiente hito: `FUNC-SPRINT-88" in readme
    assert "## FUNC-SPRINT-42 — RollbackManager y backup local controlado" in runbook
    assert "python -m devpilot_core rollback list --json" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-45"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-44"' in backlog
    assert "Estado de implementación Sprint 42" in backlog
    assert 'next_sprint: "FUNC-SPRINT-88"' in functional_backlog
    assert "Transición posterior a FUNC-SPRINT-42" in functional_backlog
    assert "Actualización FUNC-SPRINT-42 — Pruebas de RollbackManager" in test_strategy
    assert ".devpilot/rollback/" in gitignore


def test_sprint_42_miasi_rollback_tools_declared() -> None:
    registry = json.loads(_read(".devpilot/miasi/tool_registry.json"))
    agent_registry = json.loads(_read(".devpilot/miasi/agent_registry.json"))
    policy_matrix = json.loads(_read(".devpilot/miasi/policy_matrix.json"))
    tool_ids = {tool["tool_id"] for tool in registry["tools"]}
    rule_ids = {rule["rule_id"] for rule in policy_matrix["rules"]}
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")

    assert {"rollback.plan", "rollback.list", "rollback.show", "rollback.execute"}.issubset(tool_ids)
    assert {"ROLLBACK_PLAN_RUNTIME_ALLOW", "ROLLBACK_READ_ALLOW", "ROLLBACK_EXECUTE_GATED_BLOCKED"}.issubset(rule_ids)
    patch_agent = next(agent for agent in agent_registry["agents"] if agent["agent_id"] == "patch.review")
    assert "rollback.plan" in patch_agent["allowed_tools"]
    assert "Tool Card — RollbackManager y backup local" in tool_card
    assert "Estado operacional RollbackManager" in tool_registry_doc


def test_sprint_42_does_not_ship_intermediate_patch_diffs() -> None:
    assert not (ROOT / "fix_sprint41_patch_sandbox_fallback.diff").exists()
    assert not (ROOT / "patch_sprint41_pytest_fix.diff").exists()
