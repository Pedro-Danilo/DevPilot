from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_39_manifest_and_audit_exist() -> None:
    manifest = json.loads(_read("docs/functional_sprint_39_manifest.json"))
    audit = _read("docs/audits/func_sprint_39_repo_quality_gate_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-39"
    assert manifest["status"] == "implemented"
    assert "src/devpilot_core/review/rule_packs.py" in manifest["created_files"]
    assert "src/devpilot_core/repo/quality_gate.py" in manifest["created_files"]
    assert "tests/test_repo_quality_gate.py" in manifest["tests"]
    assert manifest["architectural_decision"]["required"] is False
    assert "Repo Quality Gate dry-run" in audit
    assert "no modifica archivos" in audit
    assert "no usa red" in audit


def test_sprint_39_readme_runbook_backlog_and_test_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_C_ingenieria_repositorio.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "Último hito: `FUNC-SPRINT-75" in readme
    assert "Siguiente hito: `FUNC-SPRINT-76" in readme
    assert "## FUNC-SPRINT-39 — Review Rule Packs y Repo Quality Gate dry-run" in runbook
    assert "python -m devpilot_core repo quality-gate --json --write-report" in runbook
    assert 'phase_c_status: "completed"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-45"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-44"' in backlog
    assert "Estado de implementación Sprint 39" in backlog
    assert "Actualización FUNC-SPRINT-39 — Pruebas de Repo Quality Gate dry-run" in test_strategy


def test_sprint_39_miasi_quality_gate_tool_declared() -> None:
    registry = json.loads(_read(".devpilot/miasi/tool_registry.json"))
    agent_registry = json.loads(_read(".devpilot/miasi/agent_registry.json"))
    policy_matrix = json.loads(_read(".devpilot/miasi/policy_matrix.json"))
    tool_ids = {tool["tool_id"] for tool in registry["tools"]}
    rule_ids = {rule["rule_id"] for rule in policy_matrix["rules"]}
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")

    assert "repo.quality_gate" in tool_ids
    assert "REPO_QUALITY_GATE_DRY_RUN_ALLOW" in rule_ids
    repo_agent = next(agent for agent in agent_registry["agents"] if agent["agent_id"] == "repo.analysis")
    assert "repo.quality_gate" in repo_agent["allowed_tools"]
    assert "Tool Card — Repo Quality Gate dry-run" in tool_card
    assert "Estado operacional Repo Quality Gate" in tool_registry_doc


def test_sprint_39_functional_backlog_points_to_sprint_40_without_overclaiming() -> None:
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    assert 'next_sprint: "FUNC-SPRINT-76"' in functional_backlog
    assert "Transición posterior a FUNC-SPRINT-39" in functional_backlog
    assert "no aplica patches" in functional_backlog
    assert "no ejecuta Git write" in functional_backlog
    assert "no modifica archivos" in functional_backlog
    assert "no usa LLM, red ni APIs externas" in functional_backlog
