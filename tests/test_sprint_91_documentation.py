from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_91_artifacts_exist_and_are_synced() -> None:
    for rel in [
        ".devpilot/workflows/sdlc_review.json",
        "docs/schemas/multiagent_workflow.schema.json",
        "src/devpilot_core/multiagent/workflow.py",
        "evals/fixtures/multiagent_workflow_sdlc_review_cases.json",
        "tests/test_multiagent_workflow.py",
        "docs/audits/func_sprint_91_multiagent_workflows_audit.md",
        "docs/functional_sprint_91_manifest.json",
    ]:
        assert (ROOT / rel).exists(), rel

    readme = _read("README.md")
    backlog = _read("docs/devpilot_backlog_fase_H_capacidades_avanzadas.md")
    runbook = _read("docs/05_operations/runbook.md")
    assert "Último hito: `FUNC-SPRINT-91" in readme
    assert "Siguiente hito: `FUNC-SPRINT-92" in readme
    assert "multiagent workflow run --workflow sdlc_review --dry-run" in readme
    assert 'last_completed_sprint: "FUNC-SPRINT-91"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-92"' in backlog
    assert "Estado de implementación Sprint 91" in backlog
    assert "FUNC-SPRINT-91" in runbook
    assert "multiagent workflow run" in runbook


def test_sprint_91_manifest_declares_boundaries() -> None:
    manifest = json.loads((ROOT / "docs/functional_sprint_91_manifest.json").read_text(encoding="utf-8"))
    summary = manifest["summary"]
    assert manifest["sprint"] == "FUNC-SPRINT-91"
    assert summary["workflow_definition_added"] is True
    assert summary["workflow_runner_added"] is True
    assert summary["workflow_schema_added"] is True
    assert summary["dry_run_required"] is True
    assert summary["report_only"] is True
    assert summary["workflow_report_consolidated"] is True
    assert summary["open_autonomy_enabled"] is False
    assert summary["mutations_performed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["shell_used"] is False
    assert summary["dependencies_added"] is False
    assert manifest["next_sprint"] == "FUNC-SPRINT-92"


def test_sprint_91_miasi_registry_declares_workflow_tool_and_policy() -> None:
    agents = json.loads((ROOT / ".devpilot/miasi/agent_registry.json").read_text(encoding="utf-8"))["agents"]
    tools = json.loads((ROOT / ".devpilot/miasi/tool_registry.json").read_text(encoding="utf-8"))["tools"]
    rules = json.loads((ROOT / ".devpilot/miasi/policy_matrix.json").read_text(encoding="utf-8"))["rules"]

    coordinator = next(agent for agent in agents if agent["agent_id"] == "multiagent.coordinator")
    assert "multiagent.workflow.run" in coordinator["allowed_tools"]
    assert "MULTIAGENT_WORKFLOW_DRY_RUN_ALLOW" in coordinator["policy_rule_ids"]
    assert any(tool["tool_id"] == "multiagent.workflow.run" for tool in tools)
    assert any(rule["rule_id"] == "MULTIAGENT_WORKFLOW_DRY_RUN_ALLOW" for rule in rules)
    assert any(rule["rule_id"] == "MULTIAGENT_WORKFLOW_EXECUTE_DENY" for rule in rules)


def test_sprint_91_audit_defines_pass_block_and_risks() -> None:
    audit = _read("docs/audits/func_sprint_91_multiagent_workflows_audit.md")
    assert "Criterios PASS" in audit
    assert "Criterios BLOCK" in audit
    assert "Riesgos" in audit
    assert "sdlc-review" in audit
    assert "MultiAgentWorkflowRunner" in audit
    assert "implemented-initial" in audit


def test_sprint_91_changelog_and_functional_backlog_are_synced() -> None:
    changelog = _read("docs/release/CHANGELOG.md")
    functional = _read("docs/functional_backlog_after_precode.md")
    assert "FUNC-SPRINT-91" in changelog
    assert "Workflows multiagente SDLC" in changelog
    assert 'next_sprint: "FUNC-SPRINT-92"' in functional
    assert "Transición posterior a FUNC-SPRINT-91" in functional
