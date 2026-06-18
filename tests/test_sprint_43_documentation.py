from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_43_manifest_and_audit_exist() -> None:
    manifest = json.loads(_read("docs/functional_sprint_43_manifest.json"))
    audit = _read("docs/audits/func_sprint_43_refactor_executor_sandbox_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-43"
    assert manifest["status"] == "implemented"
    assert "src/devpilot_core/refactor/executor.py" in manifest["created_files"]
    assert "tests/test_refactor_executor.py" in manifest["tests"]
    assert manifest["architectural_decision"]["required"] is False
    assert "RefactorExecutor" in audit
    assert "implemented-initial" in audit
    assert "refactor sandbox" in audit
    assert "tests.run" in audit


def test_sprint_43_readme_runbook_backlog_and_test_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_C_ingenieria_repositorio.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "Último hito: `FUNC-SPRINT-89" in readme
    assert "Siguiente hito: `FUNC-SPRINT-90" in readme
    assert "## FUNC-SPRINT-43 — RefactorExecutor controlado en sandbox" in runbook
    assert "python -m devpilot_core refactor sandbox" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-45"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-44"' in backlog
    assert "Estado de implementación Sprint 43" in backlog
    assert 'next_sprint: "FUNC-SPRINT-90"' in functional_backlog
    assert "Transición posterior a FUNC-SPRINT-43" in functional_backlog
    assert "Actualización FUNC-SPRINT-43 — Pruebas de RefactorExecutor" in test_strategy


def test_sprint_43_miasi_refactor_tool_declared() -> None:
    registry = json.loads(_read(".devpilot/miasi/tool_registry.json"))
    agent_registry = json.loads(_read(".devpilot/miasi/agent_registry.json"))
    policy_matrix = json.loads(_read(".devpilot/miasi/policy_matrix.json"))
    tool_ids = {tool["tool_id"] for tool in registry["tools"]}
    rule_ids = {rule["rule_id"] for rule in policy_matrix["rules"]}
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")

    assert "refactor.sandbox" in tool_ids
    refactor_tool = next(tool for tool in registry["tools"] if tool["tool_id"] == "refactor.sandbox")
    assert refactor_tool["requires_approval"] is True
    assert "REFACTOR_SANDBOX_EXECUTE_GATED" in rule_ids
    safe_refactor = next(agent for agent in agent_registry["agents"] if agent["agent_id"] == "safe.refactor")
    assert "refactor.sandbox" in safe_refactor["allowed_tools"]
    assert "Tool Card — RefactorExecutor controlado en sandbox" in tool_card
    assert "Estado operacional RefactorExecutor" in tool_registry_doc


def test_sprint_43_fixture_exists_and_no_intermediate_diff_artifacts() -> None:
    assert (ROOT / "tests/fixtures/refactor_executor_project/refactor_sample.py").exists()
    assert not (ROOT / "fix_sprint41_patch_sandbox_fallback.diff").exists()
    assert not (ROOT / "patch_sprint41_pytest_fix.diff").exists()
