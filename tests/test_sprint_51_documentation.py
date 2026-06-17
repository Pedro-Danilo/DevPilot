from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_51_readme_runbook_backlog_and_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_D_ia_local_gobernada.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "Último hito: `FUNC-SPRINT-74" in readme
    assert "Siguiente hito: `FUNC-SPRINT-75" in readme
    assert "## FUNC-SPRINT-51 — AgentRuntime v2 model-aware en modo monoagente" in readme
    assert "python -m devpilot_core agent run documentation-audit --target docs/01_requirements --provider mock --json" in runbook
    assert "python -m devpilot_core eval run --json" in runbook
    assert "## FUNC-SPRINT-51 — AgentRuntime v2 model-aware en modo monoagente" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-56"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-55"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-56"' in backlog
    assert "## Estado de implementación Sprint 51" in backlog
    assert 'next_sprint: "FUNC-SPRINT-75"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-51" in functional_backlog
    assert "## Actualización FUNC-SPRINT-51 — Pruebas de AgentRuntime v2 model-aware" in test_strategy


def test_sprint_51_miasi_agent_tool_policy_and_eval_docs_are_synchronized() -> None:
    agents = {item["agent_id"]: item for item in _json(".devpilot/miasi/agent_registry.json")["agents"]}
    tools = {item["tool_id"]: item for item in _json(".devpilot/miasi/tool_registry.json")["tools"]}
    policies = {item["rule_id"]: item for item in _json(".devpilot/miasi/policy_matrix.json")["rules"]}
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")
    policy_card = _read("docs/06_miasi/policy_card.md")
    eval_card = _read("docs/06_miasi/eval_card.md")
    agent_card = _read("docs/06_miasi/agent_card.md")

    assert tools["agent.model.generate"]["status"] == "implemented-initial"
    assert "AGENT_MODEL_CALL_GOVERNED_ALLOW" in tools["agent.model.generate"]["policy_rule_ids"]
    assert policies["AGENT_MODEL_CALL_GOVERNED_ALLOW"]["default_effect"] == "allow"
    assert "AgentRuntimeV2" in policies["AGENT_MODEL_CALL_GOVERNED_ALLOW"]["gate"]
    assert "NoHandoffs" in policies["AGENT_MODEL_CALL_GOVERNED_ALLOW"]["gate"]
    assert "NoRawPrompts" in policies["AGENT_MODEL_CALL_GOVERNED_ALLOW"]["gate"]
    assert "agent.model.generate" in agents["precode.audit"]["allowed_tools"]
    assert "agent.model.generate" in agents["precode.documentation"]["allowed_tools"]
    assert "FUNC-SPRINT-51" in tool_card
    assert "FUNC-SPRINT-51" in tool_registry_doc
    assert "FUNC-SPRINT-51" in policy_card
    assert "FUNC-SPRINT-51" in eval_card
    assert "FUNC-SPRINT-51" in agent_card


def test_sprint_51_manifest_audit_and_eval_fixture_are_synchronized() -> None:
    manifest = _json("docs/functional_sprint_51_manifest.json")
    audit = _read("docs/audits/func_sprint_51_agent_runtime_v2_audit.md")
    fixture = _json("evals/fixtures/documentation_eval_cases.json")

    assert manifest["sprint"] == "FUNC-SPRINT-51"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert "src/devpilot_core/agents/base.py" in manifest["created_files"]
    assert "src/devpilot_core/agents/runtime.py" in manifest["modified_files"]
    assert "tests/test_agent_runtime_v2.py" in manifest["tests"]
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-52")
    assert any(case["component"] == "agent.documentation_audit_model_aware" for case in fixture["cases"])
    assert "## Criterios PASS" in audit
    assert "## Criterios BLOCK" in audit
