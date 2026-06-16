from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_38_manifest_and_audit_exist() -> None:
    manifest = json.loads(_read("docs/functional_sprint_38_manifest.json"))
    audit = _read("docs/audits/func_sprint_38_architecture_drift_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-38"
    assert manifest["status"] == "implemented"
    assert "src/devpilot_core/repo/architecture_drift.py" in manifest["created_files"]
    assert "tests/test_architecture_drift_repo.py" in manifest["tests"]
    assert manifest["architectural_decision"]["required"] is False
    assert "Architecture/code drift inicial" in audit
    assert "no ejecuta código analizado" in audit
    assert "no usa red, APIs externas ni modelos" in audit


def test_sprint_38_readme_runbook_backlog_and_test_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_C_ingenieria_repositorio.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "Último hito: `FUNC-SPRINT-69" in readme
    assert "Siguiente hito: `FUNC-SPRINT-70" in readme
    assert "## FUNC-SPRINT-38 — Architecture/code drift inicial" in runbook
    assert "python -m devpilot_core repo architecture-drift --json --write-report" in runbook
    assert 'phase_c_status: "completed"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-45"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-44"' in backlog
    assert "Estado de implementación Sprint 38" in backlog
    assert "Actualización FUNC-SPRINT-38 — Pruebas de Architecture/code drift" in test_strategy


def test_sprint_38_miasi_architecture_drift_tool_declared() -> None:
    registry = json.loads(_read(".devpilot/miasi/tool_registry.json"))
    agent_registry = json.loads(_read(".devpilot/miasi/agent_registry.json"))
    tool_ids = {tool["tool_id"] for tool in registry["tools"]}
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")

    assert "repo.architecture_drift" in tool_ids
    repo_agent = next(agent for agent in agent_registry["agents"] if agent["agent_id"] == "repo.analysis")
    assert "repo.architecture_drift" in repo_agent["allowed_tools"]
    assert "Tool Card — Architecture/code drift read-only" in tool_card
    assert "Estado operacional Architecture/code drift" in tool_registry_doc


def test_sprint_38_functional_backlog_points_to_sprint_39_without_overclaiming() -> None:
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    assert 'next_sprint: "FUNC-SPRINT-70"' in functional_backlog
    assert "Transición posterior a FUNC-SPRINT-38" in functional_backlog
    assert "no ejecuta código analizado" in functional_backlog
    assert "no modifica documentación" in functional_backlog
    assert "no habilita patch apply" in functional_backlog
