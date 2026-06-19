from __future__ import annotations

import json
from pathlib import Path


def test_sprint_89_artifacts_exist_and_are_synced() -> None:
    root = Path.cwd()
    expected = [
        "src/devpilot_core/connectors/adapter.py",
        "docs/audits/func_sprint_89_mcp_mvp_audit.md",
        "docs/functional_sprint_89_manifest.json",
        "tests/test_connector_adapter.py",
    ]
    for rel in expected:
        assert (root / rel).exists(), rel

    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "FUNC-SPRINT-89" in readme
    assert "Último hito: `FUNC-SPRINT-96" in readme
    assert "Siguiente hito: `FUNC-SPRINT-97" in readme
    assert "connector call" in readme
    assert "--dry-run" in readme

    backlog = (root / "docs/devpilot_backlog_fase_H_capacidades_avanzadas.md").read_text(encoding="utf-8")
    assert 'last_completed_sprint: "FUNC-SPRINT-96"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-97"' in backlog
    assert "FUNC-SPRINT-89" in backlog
    assert "Estado de implementación Sprint 89" in backlog


def test_sprint_89_manifest_declares_mcp_boundaries() -> None:
    manifest = json.loads(Path("docs/functional_sprint_89_manifest.json").read_text(encoding="utf-8"))
    summary = manifest["summary"]
    assert manifest["sprint"] == "FUNC-SPRINT-89"
    assert summary["connector_adapter_added"] is True
    assert summary["connector_call_cli_added"] is True
    assert summary["read_only_connector_enabled"] is True
    assert summary["dry_run_required"] is True
    assert summary["policy_engine_required"] is True
    assert summary["trace_event_required"] is True
    assert summary["mcp_real_client_implemented"] is False
    assert summary["mcp_real_server_implemented"] is False
    assert summary["remote_execution_enabled"] is False
    assert summary["shell_enabled"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["dependencies_added"] is False


def test_sprint_89_docs_define_pass_block_and_security() -> None:
    audit = Path("docs/audits/func_sprint_89_mcp_mvp_audit.md").read_text(encoding="utf-8")
    card = Path("docs/06_miasi/connector_registry_card.md").read_text(encoding="utf-8")
    threat = Path("docs/03_security/mcp_connector_threat_model.md").read_text(encoding="utf-8")
    runbook = Path("docs/05_operations/runbook.md").read_text(encoding="utf-8")
    assert "Criterios PASS" in audit
    assert "Criterios BLOCK" in audit
    assert "PolicyEngine" in audit
    assert "connector.call.evaluated" in audit
    assert "Actualización FUNC-SPRINT-89" in card
    assert "Actualización FUNC-SPRINT-89" in threat
    assert "connector call" in runbook


def test_sprint_89_miasi_registry_declares_connector_call_policy() -> None:
    tools = json.loads(Path(".devpilot/miasi/tool_registry.json").read_text(encoding="utf-8"))["tools"]
    rules = json.loads(Path(".devpilot/miasi/policy_matrix.json").read_text(encoding="utf-8"))["rules"]
    assert any(tool["tool_id"] == "connector.call" for tool in tools)
    assert any(tool["tool_id"] == "connector.local_docs.list" for tool in tools)
    assert any(rule["rule_id"] == "CONNECTOR_CALL_READ_ONLY_ALLOW" for rule in rules)
    assert any(rule["rule_id"] == "CONNECTOR_CALL_EXECUTE_DENY" for rule in rules)


def test_sprint_89_changelog_and_functional_backlog_are_synced() -> None:
    changelog = Path("docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    functional = Path("docs/functional_backlog_after_precode.md").read_text(encoding="utf-8")
    assert "FUNC-SPRINT-89" in changelog
    assert "MCP MVP controlado" in changelog
    assert 'next_sprint: "FUNC-SPRINT-97"' in functional
    assert "Transición posterior a FUNC-SPRINT-89" in functional
    assert "Transición posterior a FUNC-SPRINT-90" in functional
