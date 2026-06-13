from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_44_manifest_phase_manifest_and_closure_report_exist() -> None:
    manifest = json.loads(_read("docs/functional_sprint_44_manifest.json"))
    phase_manifest = json.loads(_read("docs/phase_c_manifest.json"))
    closure = _read("docs/audits/phase_c_repository_engineering_closure_report.md")

    assert manifest["sprint"] == "FUNC-SPRINT-44"
    assert manifest["status"] == "implemented"
    assert "src/devpilot_core/repo/engineering_gate.py" in manifest["created_files"]
    assert "tests/test_repo_engineering_gate.py" in manifest["tests"]
    assert manifest["architectural_decision"]["required"] is False
    assert phase_manifest["status"] == "completed"
    assert phase_manifest["closed_by"] == "FUNC-SPRINT-44"
    assert "Repository Engineering Quality Gate" in closure
    assert "implemented-initial" in closure
    assert "Fase D" in closure


def test_sprint_44_readme_runbook_backlog_and_test_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_C_ingenieria_repositorio.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "Último hito: `FUNC-SPRINT-56" in readme
    assert "Siguiente hito: `FUNC-SPRINT-57" in readme
    assert "## FUNC-SPRINT-44 — Cierre Fase C: repository engineering quality gate" in runbook
    assert "python -m devpilot_core repo engineering-gate --profile full --json --write-report" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-45"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-44"' in backlog
    assert 'phase_c_status: "completed"' in backlog
    assert "Estado de implementación Sprint 44" in backlog
    assert 'next_sprint: "FUNC-SPRINT-57"' in functional_backlog
    assert "Transición posterior a FUNC-SPRINT-44" in functional_backlog
    assert "Actualización FUNC-SPRINT-44 — Pruebas de Repository Engineering Gate" in test_strategy


def test_sprint_44_miasi_engineering_gate_declared() -> None:
    registry = json.loads(_read(".devpilot/miasi/tool_registry.json"))
    agent_registry = json.loads(_read(".devpilot/miasi/agent_registry.json"))
    policy_matrix = json.loads(_read(".devpilot/miasi/policy_matrix.json"))
    tool_ids = {tool["tool_id"] for tool in registry["tools"]}
    rule_ids = {rule["rule_id"] for rule in policy_matrix["rules"]}
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")

    assert "repo.engineering_gate" in tool_ids
    gate_tool = next(tool for tool in registry["tools"] if tool["tool_id"] == "repo.engineering_gate")
    assert gate_tool["requires_approval"] is False
    assert "ENGINEERING_GATE_READ_ONLY_ALLOW" in rule_ids
    repo_agent = next(agent for agent in agent_registry["agents"] if agent["agent_id"] == "repo.analysis")
    assert "repo.engineering_gate" in repo_agent["allowed_tools"]
    assert "Tool Card — RepoEngineeringGate cierre Fase C" in tool_card
    assert "Estado operacional RepoEngineeringGate" in tool_registry_doc
