from __future__ import annotations

import json
from pathlib import Path


def test_sprint_86_artifacts_exist_and_are_synced() -> None:
    root = Path.cwd()
    expected = [
        "src/devpilot_core/agents/session.py",
        "docs/06_miasi/agent_session_card.md",
        "docs/audits/func_sprint_86_agent_session_audit.md",
        "docs/functional_sprint_86_manifest.json",
        "tests/test_agent_session.py",
    ]
    for rel in expected:
        assert (root / rel).exists(), rel

    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "Último hito: `FUNC-SPRINT-97" in readme
    assert "Siguiente hito: `FUNC-SPRINT-98" in readme
    assert "agent session inspect" in readme
    assert "semantic_memory_enabled" in readme

    backlog = (root / "docs/devpilot_backlog_fase_H_capacidades_avanzadas.md").read_text(encoding="utf-8")
    assert 'last_completed_sprint: "FUNC-SPRINT-97"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-98"' in backlog
    assert "Estado de implementación Sprint 86" in backlog


def test_sprint_86_manifest_declares_safety_boundaries() -> None:
    manifest = json.loads(Path("docs/functional_sprint_86_manifest.json").read_text(encoding="utf-8"))
    summary = manifest["summary"]
    assert manifest["sprint"] == "FUNC-SPRINT-86"
    assert summary["agent_session_model_added"] is True
    assert summary["agent_session_inspect_cli_added"] is True
    assert summary["semantic_memory_enabled"] is False
    assert summary["rag_enabled"] is False
    assert summary["multiagent_runtime_added"] is False
    assert summary["network_used"] is False
    assert summary["dependencies_added"] is False


def test_sprint_86_docs_define_pass_block_and_retention() -> None:
    card = Path("docs/06_miasi/agent_session_card.md").read_text(encoding="utf-8")
    audit = Path("docs/audits/func_sprint_86_agent_session_audit.md").read_text(encoding="utf-8")
    runbook = Path("docs/05_operations/runbook.md").read_text(encoding="utf-8")
    assert "Criterios PASS" in card
    assert "Criterios BLOCK" in card
    assert "retention" in card.lower() or "retención" in card.lower()
    assert "No se guardan prompts" in card
    assert "AgentSessionStore" in audit
    assert "agent session inspect" in runbook


def test_sprint_86_miasi_registry_declares_session_tool_and_policy() -> None:
    tools = json.loads(Path(".devpilot/miasi/tool_registry.json").read_text(encoding="utf-8"))["tools"]
    rules = json.loads(Path(".devpilot/miasi/policy_matrix.json").read_text(encoding="utf-8"))["rules"]
    assert any(tool["tool_id"] == "agent.session.inspect" for tool in tools)
    assert any(rule["rule_id"] == "AGENT_SESSION_INSPECT_ALLOW" for rule in rules)
    assert any(rule["rule_id"] == "AGENT_SESSION_STATE_ALLOW" for rule in rules)


def test_sprint_86_changelog_and_functional_backlog_are_synced() -> None:
    changelog = Path("docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    functional = Path("docs/functional_backlog_after_precode.md").read_text(encoding="utf-8")
    assert "FUNC-SPRINT-86" in changelog
    assert "Agent session state y memoria operativa controlada" in changelog
    assert 'next_sprint: "FUNC-SPRINT-98"' in functional
    assert "Transición posterior a FUNC-SPRINT-86" in functional
