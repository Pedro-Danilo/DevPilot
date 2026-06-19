from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_90_artifacts_exist_and_are_synced() -> None:
    for rel in [
        "src/devpilot_core/multiagent/__init__.py",
        "src/devpilot_core/multiagent/coordinator.py",
        "src/devpilot_core/multiagent/handoff.py",
        "tests/test_multiagent_coordinator.py",
        "docs/audits/func_sprint_90_multiagent_coordinator_audit.md",
        "docs/functional_sprint_90_manifest.json",
    ]:
        assert (ROOT / rel).exists(), rel

    readme = _read("README.md")
    backlog = _read("docs/devpilot_backlog_fase_H_capacidades_avanzadas.md")
    runbook = _read("docs/05_operations/runbook.md")
    assert "Último hito: `FUNC-SPRINT-92" in readme
    assert "Siguiente hito: `FUNC-SPRINT-93" in readme
    assert "multiagent run --workflow repo-review --dry-run" in readme
    assert 'last_completed_sprint: "FUNC-SPRINT-92"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-93"' in backlog
    assert "Estado de implementación Sprint 90" in backlog
    assert "FUNC-SPRINT-90" in runbook
    assert "multiagent run" in runbook


def test_sprint_90_manifest_declares_boundaries() -> None:
    manifest = json.loads((ROOT / "docs/functional_sprint_90_manifest.json").read_text(encoding="utf-8"))
    summary = manifest["summary"]
    assert manifest["sprint"] == "FUNC-SPRINT-90"
    assert summary["multiagent_coordinator_added"] is True
    assert summary["handoff_model_added"] is True
    assert summary["multiagent_run_cli_added"] is True
    assert summary["dry_run_required"] is True
    assert summary["policy_engine_required"] is True
    assert summary["handoff_trace_required"] is True
    assert summary["implemented_agents_only"] is True
    assert summary["open_autonomy_enabled"] is False
    assert summary["mutations_performed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["shell_used"] is False
    assert summary["dependencies_added"] is False
    assert manifest["next_sprint"] == "FUNC-SPRINT-91"


def test_sprint_90_miasi_registry_declares_coordinator_and_handoff_policy() -> None:
    agents = json.loads((ROOT / ".devpilot/miasi/agent_registry.json").read_text(encoding="utf-8"))["agents"]
    tools = json.loads((ROOT / ".devpilot/miasi/tool_registry.json").read_text(encoding="utf-8"))["tools"]
    rules = json.loads((ROOT / ".devpilot/miasi/policy_matrix.json").read_text(encoding="utf-8"))["rules"]

    coordinator = next(agent for agent in agents if agent["agent_id"] == "multiagent.coordinator")
    assert coordinator["status"] == "implemented-initial"
    assert coordinator["max_autonomy"] == "A3"
    assert "MULTIAGENT_COORDINATOR_DRY_RUN_ALLOW" in coordinator["policy_rule_ids"]
    assert any(tool["tool_id"] == "multiagent.coordinator.run" for tool in tools)
    assert any(tool["tool_id"] == "multiagent.handoff" for tool in tools)
    assert any(rule["rule_id"] == "MULTIAGENT_HANDOFF_TRACE_REQUIRED" for rule in rules)
    assert any(rule["rule_id"] == "MULTIAGENT_EXECUTE_DENY" for rule in rules)


def test_sprint_90_audit_defines_pass_block_and_risks() -> None:
    audit = _read("docs/audits/func_sprint_90_multiagent_coordinator_audit.md")
    assert "Criterios PASS" in audit
    assert "Criterios BLOCK" in audit
    assert "Riesgos" in audit
    assert "HandoffRecord" in audit
    assert "multiagent.handoff.evaluated" in audit
    assert "implemented-initial" in audit


def test_sprint_90_changelog_and_functional_backlog_are_synced() -> None:
    changelog = _read("docs/release/CHANGELOG.md")
    functional = _read("docs/functional_backlog_after_precode.md")
    assert "FUNC-SPRINT-90" in changelog
    assert "MultiAgentCoordinator" in changelog
    assert 'next_sprint: "FUNC-SPRINT-93"' in functional
    assert "Transición posterior a FUNC-SPRINT-90" in functional
