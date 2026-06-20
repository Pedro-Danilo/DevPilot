from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_37_manifest_and_audit_exist() -> None:
    manifest = json.loads(_read("docs/functional_sprint_37_manifest.json"))
    audit = _read("docs/audits/func_sprint_37_repo_analyzer_v2_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-37"
    assert manifest["status"] == "implemented"
    assert "src/devpilot_core/repo/analyzer.py" in manifest["created_files"]
    assert "tests/test_repo_analyzer.py" in manifest["tests"]
    assert manifest["architectural_decision"]["required"] is False
    assert "RepoAnalyzer v2" in audit
    assert "no ejecuta ni importa código analizado" in audit


def test_sprint_37_readme_runbook_backlog_and_test_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_C_ingenieria_repositorio.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "## FUNC-SPRINT-37 — RepoAnalyzer v2" in runbook
    assert "python -m devpilot_core repo analyze --json --write-report" in runbook
    assert 'phase_c_status: "completed"' in backlog
    assert "Estado de implementación Sprint 37" in backlog
    assert "Actualización FUNC-SPRINT-37 — Pruebas de RepoAnalyzer v2" in test_strategy


def test_sprint_37_miasi_repo_analyze_tool_declared() -> None:
    registry = json.loads(_read(".devpilot/miasi/tool_registry.json"))
    agent_registry = json.loads(_read(".devpilot/miasi/agent_registry.json"))
    tool_ids = {tool["tool_id"] for tool in registry["tools"]}
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")

    assert "repo.analyze" in tool_ids
    repo_agent = next(agent for agent in agent_registry["agents"] if agent["agent_id"] == "repo.analysis")
    assert "repo.analyze" in repo_agent["allowed_tools"]
    assert "Tool Card — RepoAnalyzer v2 read-only" in tool_card
    assert "Estado operacional RepoAnalyzer v2" in tool_registry_doc


def test_sprint_37_functional_backlog_points_to_sprint_38_without_overclaiming() -> None:
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    assert "Transición posterior a FUNC-SPRINT-37" in functional_backlog
    assert "no ejecuta código analizado" in functional_backlog
    assert "no habilita patch apply" in functional_backlog
