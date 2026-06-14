from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_52_readme_runbook_backlog_and_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_D_ia_local_gobernada.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "Último hito: `FUNC-SPRINT-61" in readme
    assert "Siguiente hito: `FUNC-SPRINT-62" in readme
    assert "## FUNC-SPRINT-52 — RepoAnalysisAgent gobernado" in readme
    assert "python -m devpilot_core agent run repo-analysis --target . --provider mock --json" in runbook
    assert "python -m devpilot_core eval run --json" in runbook
    assert "## FUNC-SPRINT-52 — RepoAnalysisAgent gobernado" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-56"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-55"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-56"' in backlog
    assert "## Estado de implementación Sprint 52" in backlog
    assert 'next_sprint: "FUNC-SPRINT-62"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-52" in functional_backlog
    assert "## Actualización FUNC-SPRINT-52 — Pruebas de RepoAnalysisAgent gobernado" in test_strategy


def test_sprint_52_miasi_prompt_and_eval_docs_are_synchronized() -> None:
    agents = {item["agent_id"]: item for item in _json(".devpilot/miasi/agent_registry.json")["agents"]}
    tools = {item["tool_id"]: item for item in _json(".devpilot/miasi/tool_registry.json")["tools"]}
    policies = {item["rule_id"]: item for item in _json(".devpilot/miasi/policy_matrix.json")["rules"]}
    prompt = _json("docs/prompts/repo.analysis.agent.v1.json")
    fixture = _json("evals/fixtures/documentation_eval_cases.json")
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")
    policy_card = _read("docs/06_miasi/policy_card.md")
    eval_card = _read("docs/06_miasi/eval_card.md")
    agent_card = _read("docs/06_miasi/agent_card.md")

    assert agents["repo.analysis"]["status"] == "implemented-initial"
    assert "agent.repo_analysis.run" in agents["repo.analysis"]["allowed_tools"]
    assert "agent.model.generate" in agents["repo.analysis"]["allowed_tools"]
    assert tools["agent.repo_analysis.run"]["status"] == "implemented-initial"
    assert "REPO_ANALYSIS_AGENT_GOVERNED_ALLOW" in tools["agent.repo_analysis.run"]["policy_rule_ids"]
    assert policies["REPO_ANALYSIS_AGENT_GOVERNED_ALLOW"]["default_effect"] == "allow"
    assert "RepoAnalysisAgent" in policies["REPO_ANALYSIS_AGENT_GOVERNED_ALLOW"]["gate"]
    assert "NoExternalAPI" in policies["REPO_ANALYSIS_AGENT_GOVERNED_ALLOW"]["gate"]
    assert "NoHandoffs" in policies["REPO_ANALYSIS_AGENT_GOVERNED_ALLOW"]["gate"]
    assert prompt["id"] == "repo.analysis.agent"
    assert prompt["version"] == "1.0.0"
    assert prompt["metadata"]["sprint"] == "FUNC-SPRINT-52"
    assert any(case["component"] == "agent.repo_analysis_model_aware" for case in fixture["cases"])
    assert "FUNC-SPRINT-52" in tool_card
    assert "FUNC-SPRINT-52" in tool_registry_doc
    assert "FUNC-SPRINT-52" in policy_card
    assert "FUNC-SPRINT-52" in eval_card
    assert "FUNC-SPRINT-52" in agent_card


def test_sprint_52_manifest_audit_and_files_exist() -> None:
    manifest = _json("docs/functional_sprint_52_manifest.json")
    audit = _read("docs/audits/func_sprint_52_repo_analysis_agent_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-52"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert "src/devpilot_core/agents/repo_analysis_agent.py" in manifest["created_files"]
    assert "docs/prompts/repo.analysis.agent.v1.json" in manifest["created_files"]
    assert "tests/test_repo_analysis_agent.py" in manifest["tests"]
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-53")
    assert "## Criterios PASS" in audit
    assert "## Criterios BLOCK" in audit
