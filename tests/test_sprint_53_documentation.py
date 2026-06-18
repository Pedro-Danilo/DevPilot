from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_53_readme_runbook_backlog_and_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_D_ia_local_gobernada.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "Último hito: `FUNC-SPRINT-87" in readme
    assert "Siguiente hito: `FUNC-SPRINT-88" in readme
    assert "## FUNC-SPRINT-53 — CodeReviewAgent y PatchReviewAgent gobernados" in readme
    assert "python -m devpilot_core agent run code-review" in runbook
    assert "python -m devpilot_core agent run patch-review" in runbook
    assert "## FUNC-SPRINT-53 — CodeReviewAgent y PatchReviewAgent gobernados" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-56"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-55"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-56"' in backlog
    assert "## Estado de implementación Sprint 53" in backlog
    assert 'next_sprint: "FUNC-SPRINT-88"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-53" in functional_backlog
    assert "## Actualización FUNC-SPRINT-53 — Pruebas de CodeReviewAgent y PatchReviewAgent gobernados" in test_strategy


def test_sprint_53_miasi_prompts_and_eval_docs_are_synchronized() -> None:
    agents = {item["agent_id"]: item for item in _json(".devpilot/miasi/agent_registry.json")["agents"]}
    tools = {item["tool_id"]: item for item in _json(".devpilot/miasi/tool_registry.json")["tools"]}
    policies = {item["rule_id"]: item for item in _json(".devpilot/miasi/policy_matrix.json")["rules"]}
    code_prompt = _json("docs/prompts/code.review.agent.v1.json")
    patch_prompt = _json("docs/prompts/patch.review.agent.v1.json")
    fixture = _json("evals/fixtures/documentation_eval_cases.json")
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")
    policy_card = _read("docs/06_miasi/policy_card.md")
    eval_card = _read("docs/06_miasi/eval_card.md")
    agent_card = _read("docs/06_miasi/agent_card.md")

    assert agents["code.review"]["status"] == "implemented-initial"
    assert agents["patch.review"]["status"] == "implemented-initial"
    assert "agent.code_review.run" in agents["code.review"]["allowed_tools"]
    assert "agent.patch_review.run" in agents["patch.review"]["allowed_tools"]
    assert "agent.model.generate" in agents["code.review"]["allowed_tools"]
    assert "agent.model.generate" in agents["patch.review"]["allowed_tools"]
    assert tools["agent.code_review.run"]["status"] == "implemented-initial"
    assert tools["agent.patch_review.run"]["status"] == "implemented-initial"
    assert "CODE_REVIEW_AGENT_GOVERNED_ALLOW" in tools["agent.code_review.run"]["policy_rule_ids"]
    assert "PATCH_REVIEW_AGENT_GOVERNED_ALLOW" in tools["agent.patch_review.run"]["policy_rule_ids"]
    assert policies["CODE_REVIEW_AGENT_GOVERNED_ALLOW"]["default_effect"] == "allow"
    assert policies["PATCH_REVIEW_AGENT_GOVERNED_ALLOW"]["default_effect"] == "allow"
    assert "NoMutations" in policies["CODE_REVIEW_AGENT_GOVERNED_ALLOW"]["gate"]
    assert "NoPatchApply" in policies["PATCH_REVIEW_AGENT_GOVERNED_ALLOW"]["gate"]
    assert code_prompt["id"] == "code.review.agent"
    assert patch_prompt["id"] == "patch.review.agent"
    assert code_prompt["metadata"]["sprint"] == "FUNC-SPRINT-53"
    assert patch_prompt["metadata"]["sprint"] == "FUNC-SPRINT-53"
    assert any(case["component"] == "agent.code_review_model_aware" for case in fixture["cases"])
    assert any(case["component"] == "agent.patch_review_model_aware" for case in fixture["cases"])
    assert any(case["component"] == "agent.code_review" for case in fixture["cases"])
    assert any(case["component"] == "agent.patch_review" for case in fixture["cases"])
    assert "FUNC-SPRINT-53" in tool_card
    assert "FUNC-SPRINT-53" in tool_registry_doc
    assert "FUNC-SPRINT-53" in policy_card
    assert "FUNC-SPRINT-53" in eval_card
    assert "FUNC-SPRINT-53" in agent_card


def test_sprint_53_manifest_audit_and_files_exist() -> None:
    manifest = _json("docs/functional_sprint_53_manifest.json")
    audit = _read("docs/audits/func_sprint_53_review_agents_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-53"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert "src/devpilot_core/agents/code_review_agent.py" in manifest["created_files"]
    assert "src/devpilot_core/agents/patch_review_agent.py" in manifest["created_files"]
    assert "docs/prompts/code.review.agent.v1.json" in manifest["created_files"]
    assert "docs/prompts/patch.review.agent.v1.json" in manifest["created_files"]
    assert "tests/test_review_agents.py" in manifest["tests"]
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-54")
    assert "## Criterios PASS" in audit
    assert "## Criterios BLOCK" in audit
