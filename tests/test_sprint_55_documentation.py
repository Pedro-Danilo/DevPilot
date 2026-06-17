from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_55_readme_runbook_backlogs_and_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_D_ia_local_gobernada.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "Último hito: `FUNC-SPRINT-75" in readme
    assert "Siguiente hito: `FUNC-SPRINT-76" in readme
    assert "## FUNC-SPRINT-55 — Requirements/Architecture/Security agents y cierre Fase D" in readme
    assert "python -m devpilot_core agent run requirements" in runbook
    assert "python -m devpilot_core agent run architecture" in runbook
    assert "python -m devpilot_core agent run security" in runbook
    assert "## FUNC-SPRINT-55 — Requirements/Architecture/Security agents y cierre Fase D" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-56"' in backlog
    assert 'phase_d_status: "closed"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-55"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-56"' in backlog
    assert "## Estado de implementación Sprint 55" in backlog
    assert 'next_sprint: "FUNC-SPRINT-76"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-55" in functional_backlog
    assert "## Actualización FUNC-SPRINT-55 — Pruebas de agentes SDLC y cierre Fase D" in test_strategy


def test_sprint_55_miasi_prompts_and_eval_docs_are_synchronized() -> None:
    agents = {item["agent_id"]: item for item in _json(".devpilot/miasi/agent_registry.json")["agents"]}
    tools = {item["tool_id"]: item for item in _json(".devpilot/miasi/tool_registry.json")["tools"]}
    policies = {item["rule_id"]: item for item in _json(".devpilot/miasi/policy_matrix.json")["rules"]}
    req_prompt = _json("docs/prompts/requirements.agent.v1.json")
    arch_prompt = _json("docs/prompts/architecture.agent.v1.json")
    sec_prompt = _json("docs/prompts/security.agent.v1.json")
    fixture = _json("evals/fixtures/documentation_eval_cases.json")
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")
    policy_card = _read("docs/06_miasi/policy_card.md")
    eval_card = _read("docs/06_miasi/eval_card.md")
    agent_card = _read("docs/06_miasi/agent_card.md")

    for agent_id in ["requirements.agent", "architecture.agent", "security.agent"]:
        assert agents[agent_id]["status"] == "implemented-initial"
        assert "agent.model.generate" in agents[agent_id]["allowed_tools"]
        assert agents[agent_id]["approval_required"] is False

    assert tools["agent.requirements.run"]["status"] == "implemented-initial"
    assert tools["agent.architecture.run"]["status"] == "implemented-initial"
    assert tools["agent.security.run"]["status"] == "implemented-initial"
    assert policies["REQUIREMENTS_AGENT_GOVERNED_ALLOW"]["default_effect"] == "allow"
    assert policies["ARCHITECTURE_AGENT_GOVERNED_ALLOW"]["default_effect"] == "allow"
    assert policies["SECURITY_AGENT_GOVERNED_ALLOW"]["default_effect"] == "allow"
    assert req_prompt["id"] == "requirements.agent"
    assert arch_prompt["id"] == "architecture.agent"
    assert sec_prompt["id"] == "security.agent"
    assert req_prompt["metadata"]["sprint"] == "FUNC-SPRINT-55"
    assert arch_prompt["metadata"]["sprint"] == "FUNC-SPRINT-55"
    assert sec_prompt["metadata"]["sprint"] == "FUNC-SPRINT-55"
    assert any(case["component"] == "agent.requirements_model_aware" for case in fixture["cases"])
    assert any(case["component"] == "agent.architecture_model_aware" for case in fixture["cases"])
    assert any(case["component"] == "agent.security_model_aware" for case in fixture["cases"])
    assert any(case["component"] == "agent.security" for case in fixture["cases"])
    assert "FUNC-SPRINT-55" in tool_card
    assert "FUNC-SPRINT-55" in tool_registry_doc
    assert "FUNC-SPRINT-55" in policy_card
    assert "FUNC-SPRINT-55" in eval_card
    assert "FUNC-SPRINT-55" in agent_card


def test_sprint_55_manifest_phase_manifest_audit_and_files_exist() -> None:
    manifest = _json("docs/functional_sprint_55_manifest.json")
    phase_manifest = _json("docs/phase_d_manifest.json")
    audit = _read("docs/audits/phase_d_local_ai_governance_closure_report.md")

    assert manifest["sprint"] == "FUNC-SPRINT-55"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert "src/devpilot_core/agents/requirements_agent.py" in manifest["created_files"]
    assert "src/devpilot_core/agents/architecture_agent.py" in manifest["created_files"]
    assert "src/devpilot_core/agents/security_agent.py" in manifest["created_files"]
    assert "docs/audits/phase_d_local_ai_governance_closure_report.md" in manifest["created_files"]
    assert "tests/test_sdlc_agents.py" in manifest["tests"]
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-56")
    assert phase_manifest["phase"] == "FASE-D-IA-LOCAL-GOBERNADA"
    assert phase_manifest["status"] == "closed"
    assert phase_manifest["last_completed_sprint"] == "FUNC-SPRINT-55"
    assert "## Criterios PASS" in audit
    assert "## Criterios BLOCK" in audit
    assert "## Brechas pendientes" in audit
