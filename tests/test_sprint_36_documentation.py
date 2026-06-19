from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_36_manifest_and_audit_exist() -> None:
    manifest = json.loads(_read("docs/functional_sprint_36_manifest.json"))
    audit = _read("docs/audits/func_sprint_36_dependency_graph_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-36"
    assert manifest["status"] == "implemented"
    assert "src/devpilot_core/repo/dependency_graph.py" in manifest["created_files"]
    assert "src/devpilot_core/repo/models.py" in manifest["created_files"]
    assert "tests/test_dependency_graph.py" in manifest["tests"]
    assert manifest["architectural_decision"]["required"] is False
    assert "DependencyGraph e import graph Python" in audit
    assert "no ejecuta el código analizado" in audit


def test_sprint_36_readme_runbook_and_phase_c_backlog_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_C_ingenieria_repositorio.md")

    assert "Último hito: `FUNC-SPRINT-93" in readme
    assert "Siguiente hito: `FUNC-SPRINT-94" in readme
    assert "## FUNC-SPRINT-36 — DependencyGraph e import graph Python" in runbook
    assert "python -m devpilot_core repo dependency-graph --target src/devpilot_core --json --write-report" in runbook
    assert 'phase_c_status: "completed"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-45"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-44"' in backlog
    assert "Estado de implementación Sprint 36" in backlog


def test_sprint_36_miasi_dependency_graph_tool_declared() -> None:
    registry = json.loads(_read(".devpilot/miasi/tool_registry.json"))
    agent_registry = json.loads(_read(".devpilot/miasi/agent_registry.json"))
    tool_ids = {tool["tool_id"] for tool in registry["tools"]}
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")

    assert "repo.dependency_graph" in tool_ids
    repo_agent = next(agent for agent in agent_registry["agents"] if agent["agent_id"] == "repo.analysis")
    assert "repo.dependency_graph" in repo_agent["allowed_tools"]
    assert "Tool Card — DependencyGraph read-only" in tool_card
    assert "Estado operacional DependencyGraph" in tool_registry_doc


def test_sprint_36_functional_backlog_points_to_sprint_37_without_overclaiming() -> None:
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    assert 'next_sprint: "FUNC-SPRINT-94"' in functional_backlog
    assert "Transición posterior a FUNC-SPRINT-36" in functional_backlog
    assert "no ejecuta código analizado" in functional_backlog
    assert "no habilita patch apply" in functional_backlog
