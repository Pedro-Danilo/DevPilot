from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_41_manifest_and_audit_exist() -> None:
    manifest = json.loads(_read("docs/functional_sprint_41_manifest.json"))
    audit = _read("docs/audits/func_sprint_41_patch_sandbox_changeset_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-41"
    assert manifest["status"] == "implemented"
    assert "src/devpilot_core/sandbox/patch_sandbox.py" in manifest["created_files"]
    assert "src/devpilot_core/changes/models.py" in manifest["created_files"]
    assert "tests/test_patch_sandbox.py" in manifest["tests"]
    assert manifest["architectural_decision"]["required"] is False
    assert "PatchSandbox" in audit
    assert "ChangeSet" in audit
    assert "outputs/sandbox" in audit


def test_sprint_41_readme_runbook_backlog_and_test_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_C_ingenieria_repositorio.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")
    gitignore = _read(".gitignore")

    assert "Último hito: `FUNC-SPRINT-91" in readme
    assert "Siguiente hito: `FUNC-SPRINT-92" in readme
    assert "## FUNC-SPRINT-41 — PatchSandbox y ChangeSet model" in runbook
    assert "python -m devpilot_core patch sandbox --patch-file safe.patch --json --write-report" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-45"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-44"' in backlog
    assert "Estado de implementación Sprint 41" in backlog
    assert "Actualización FUNC-SPRINT-41 — Pruebas de PatchSandbox y ChangeSet" in test_strategy
    assert "outputs/sandbox/" in gitignore


def test_sprint_41_miasi_patch_sandbox_tool_declared() -> None:
    registry = json.loads(_read(".devpilot/miasi/tool_registry.json"))
    agent_registry = json.loads(_read(".devpilot/miasi/agent_registry.json"))
    policy_matrix = json.loads(_read(".devpilot/miasi/policy_matrix.json"))
    tool_ids = {tool["tool_id"] for tool in registry["tools"]}
    rule_ids = {rule["rule_id"] for rule in policy_matrix["rules"]}
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")

    assert "patch.sandbox" in tool_ids
    assert "PATCH_SANDBOX_RUNTIME_ALLOW" in rule_ids
    patch_agent = next(agent for agent in agent_registry["agents"] if agent["agent_id"] == "patch.review")
    assert "patch.sandbox" in patch_agent["allowed_tools"]
    assert "Tool Card — PatchSandbox y ChangeSet" in tool_card
    assert "Estado operacional PatchSandbox" in tool_registry_doc


def test_sprint_41_functional_backlog_points_to_sprint_42_without_overclaiming() -> None:
    functional_backlog = _read("docs/functional_backlog_after_precode.md")

    assert 'next_sprint: "FUNC-SPRINT-92"' in functional_backlog
    assert "Transición posterior a FUNC-SPRINT-41" in functional_backlog
    assert "no aplica patches al workspace productivo" in functional_backlog
    assert "rollback ejecutable sigue fuera de alcance" in functional_backlog
    assert "Git write sigue bloqueado" in functional_backlog
