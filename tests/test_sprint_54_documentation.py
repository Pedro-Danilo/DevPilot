from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_54_readme_runbook_backlog_and_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_D_ia_local_gobernada.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "Último hito: `FUNC-SPRINT-65" in readme
    assert "Siguiente hito: `FUNC-SPRINT-66" in readme
    assert "## FUNC-SPRINT-54 — SafeRefactorAgent y TestPlannerAgent gobernados" in readme
    assert "python -m devpilot_core agent run safe-refactor" in runbook
    assert "python -m devpilot_core agent run test-planner" in runbook
    assert "## FUNC-SPRINT-54 — SafeRefactorAgent y TestPlannerAgent gobernados" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-56"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-55"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-56"' in backlog
    assert "## Estado de implementación Sprint 54" in backlog
    assert 'next_sprint: "FUNC-SPRINT-66"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-54" in functional_backlog
    assert "## Actualización FUNC-SPRINT-54 — Pruebas de SafeRefactorAgent y TestPlannerAgent gobernados" in test_strategy


def test_sprint_54_miasi_prompts_and_eval_docs_are_synchronized() -> None:
    agents = {item["agent_id"]: item for item in _json(".devpilot/miasi/agent_registry.json")["agents"]}
    tools = {item["tool_id"]: item for item in _json(".devpilot/miasi/tool_registry.json")["tools"]}
    policies = {item["rule_id"]: item for item in _json(".devpilot/miasi/policy_matrix.json")["rules"]}
    safe_prompt = _json("docs/prompts/safe.refactor.agent.v1.json")
    test_prompt = _json("docs/prompts/test.planner.agent.v1.json")
    fixture = _json("evals/fixtures/documentation_eval_cases.json")
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")
    policy_card = _read("docs/06_miasi/policy_card.md")
    eval_card = _read("docs/06_miasi/eval_card.md")
    agent_card = _read("docs/06_miasi/agent_card.md")

    assert agents["safe.refactor"]["status"] == "implemented-initial"
    assert agents["testplanner.agent"]["status"] == "implemented-initial"
    assert "agent.safe_refactor.run" in agents["safe.refactor"]["allowed_tools"]
    assert "agent.test_planner.run" in agents["testplanner.agent"]["allowed_tools"]
    assert "agent.model.generate" in agents["safe.refactor"]["allowed_tools"]
    assert "agent.model.generate" in agents["testplanner.agent"]["allowed_tools"]
    assert tools["agent.safe_refactor.run"]["status"] == "implemented-initial"
    assert tools["agent.test_planner.run"]["status"] == "implemented-initial"
    assert tools["traceability.coverage"]["status"] == "implemented"
    assert "SAFE_REFACTOR_AGENT_GOVERNED_ALLOW" in tools["agent.safe_refactor.run"]["policy_rule_ids"]
    assert "TEST_PLANNER_AGENT_GOVERNED_ALLOW" in tools["agent.test_planner.run"]["policy_rule_ids"]
    assert policies["SAFE_REFACTOR_AGENT_GOVERNED_ALLOW"]["default_effect"] == "allow"
    assert policies["TEST_PLANNER_AGENT_GOVERNED_ALLOW"]["default_effect"] == "allow"
    assert "NoWorkspaceMutation" in policies["SAFE_REFACTOR_AGENT_GOVERNED_ALLOW"]["gate"]
    assert "NoArbitraryCommands" in policies["TEST_PLANNER_AGENT_GOVERNED_ALLOW"]["gate"]
    assert safe_prompt["id"] == "safe.refactor.agent"
    assert test_prompt["id"] == "test.planner.agent"
    assert safe_prompt["metadata"]["sprint"] == "FUNC-SPRINT-54"
    assert test_prompt["metadata"]["sprint"] == "FUNC-SPRINT-54"
    assert any(case["component"] == "agent.safe_refactor_model_aware" for case in fixture["cases"])
    assert any(case["component"] == "agent.test_planner_model_aware" for case in fixture["cases"])
    assert any(case["component"] == "agent.test_planner" for case in fixture["cases"])
    assert "FUNC-SPRINT-54" in tool_card
    assert "FUNC-SPRINT-54" in tool_registry_doc
    assert "FUNC-SPRINT-54" in policy_card
    assert "FUNC-SPRINT-54" in eval_card
    assert "FUNC-SPRINT-54" in agent_card


def test_sprint_54_manifest_audit_and_files_exist() -> None:
    manifest = _json("docs/functional_sprint_54_manifest.json")
    audit = _read("docs/audits/func_sprint_54_refactor_testplanner_agents_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-54"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert "src/devpilot_core/agents/safe_refactor_agent.py" in manifest["created_files"]
    assert "src/devpilot_core/agents/test_planner_agent.py" in manifest["created_files"]
    assert "docs/prompts/safe.refactor.agent.v1.json" in manifest["created_files"]
    assert "docs/prompts/test.planner.agent.v1.json" in manifest["created_files"]
    assert "tests/test_refactor_testplanner_agents.py" in manifest["tests"]
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-55")
    assert "## Criterios PASS" in audit
    assert "## Criterios BLOCK" in audit
