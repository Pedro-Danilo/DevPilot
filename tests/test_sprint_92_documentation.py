from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_sprint_92_artifacts_exist_and_are_synchronized() -> None:
    expected_paths = [
        "evals/fixtures/advanced_agentic_eval_cases.json",
        "evals/fixtures/red_team_agentic_eval_cases.json",
        "src/devpilot_core/evals/safety.py",
        "tests/test_advanced_evals.py",
        "docs/audits/func_sprint_92_advanced_evals_audit.md",
        "docs/functional_sprint_92_manifest.json",
    ]
    for path in expected_paths:
        assert (ROOT / path).exists(), path

    readme = _read("README.md")
    backlog = _read("docs/devpilot_backlog_fase_H_capacidades_avanzadas.md")
    runbook = _read("docs/05_operations/runbook.md")
    functional = _read("docs/functional_backlog_after_precode.md")

    assert "Último hito: `FUNC-SPRINT-98" in readme
    assert "Siguiente hito: `FUNC-SPRINT-99" in readme
    assert 'last_completed_sprint: "FUNC-SPRINT-98"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-99"' in backlog
    assert "FUNC-SPRINT-92 — Operación Evaluación avanzada" in runbook
    assert 'next_sprint: "FUNC-SPRINT-99"' in functional
    assert "Transición posterior a FUNC-SPRINT-92" in functional


def test_sprint_92_manifest_declares_boundaries() -> None:
    manifest = _json("docs/functional_sprint_92_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-92"
    assert manifest["status"] == "implemented"
    assert manifest["next_sprint"] == "FUNC-SPRINT-93"
    summary = manifest["summary"]
    assert summary["advanced_agentic_suite_added"] is True
    assert summary["red_team_suite_added"] is True
    assert summary["quality_gate_consumes_advanced_evals"] is True
    assert summary["secret_leakage_cases_synthetic_only"] is True
    assert summary["llm_judge_used"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert "python -m devpilot_core eval run --suite red-team --json" in manifest["commands"]


def test_sprint_92_fixtures_cover_adversarial_categories() -> None:
    advanced = _json("evals/fixtures/advanced_agentic_eval_cases.json")
    red_team = _json("evals/fixtures/red_team_agentic_eval_cases.json")

    assert advanced["suite_id"] == "advanced-agentic"
    assert red_team["suite_id"] == "red-team"
    components = {case["component"] for case in advanced["cases"] + red_team["cases"]}
    assert {
        "safety.prompt_injection",
        "safety.secret_leakage",
        "safety.tool_misuse",
        "safety.rag_groundedness",
        "safety.connector_misuse",
        "safety.multiagent_workflow",
    }.issubset(components)
    assert any(case["expected"]["ok"] is False for case in advanced["cases"])
    assert any(case["expected"]["ok"] is False for case in red_team["cases"])


def test_sprint_92_miasi_declares_tool_and_policies() -> None:
    tool_registry = _json(".devpilot/miasi/tool_registry.json")
    policy_matrix = _json(".devpilot/miasi/policy_matrix.json")
    agent_registry = _json(".devpilot/miasi/agent_registry.json")

    tools = {tool["tool_id"]: tool for tool in tool_registry["tools"]}
    assert tools["eval.safety.run"]["status"] == "implemented-initial"
    assert tools["eval.safety.run"]["side_effect"] == "report"
    rules = {rule["rule_id"]: rule for rule in policy_matrix["rules"]}
    assert rules["EVAL_SAFETY_SCORING_ALLOW"]["default_effect"] == "allow"
    assert rules["RED_TEAM_FIXTURE_SYNTHETIC_ONLY"]["default_effect"] == "block"
    agents = {agent["agent_id"]: agent for agent in agent_registry["agents"]}
    assert "eval.safety.run" in agents["security.agent"]["allowed_tools"]
    assert "eval.safety.run" in agents["multiagent.coordinator"]["allowed_tools"]


def test_sprint_92_audit_and_changelog_are_synced() -> None:
    audit = _read("docs/audits/func_sprint_92_advanced_evals_audit.md")
    changelog = _read("docs/release/CHANGELOG.md")
    miasi_docs = "\n".join(
        _read(path)
        for path in [
            "docs/06_miasi/agent_card.md",
            "docs/06_miasi/tool_card.md",
            "docs/06_miasi/policy_card.md",
            "docs/06_miasi/agent_registry.md",
            "docs/06_miasi/tool_registry.md",
            "docs/06_miasi/policy_matrix.md",
        ]
    )

    assert "Criterios PASS" in audit
    assert "Criterios BLOCK" in audit
    assert "secreto real" in audit.lower()
    assert "Range: `FUNC-SPRINT-74` → `FUNC-SPRINT-98`" in changelog
    assert "docs/functional_sprint_92_manifest.json" in changelog
    assert "eval.safety.run" in miasi_docs
    assert "EVAL_SAFETY_SCORING_ALLOW" in miasi_docs
