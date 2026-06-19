from __future__ import annotations

import json
from pathlib import Path


def test_sprint_88_artifacts_exist_and_are_synced() -> None:
    root = Path.cwd()
    expected = [
        "src/devpilot_core/connectors/__init__.py",
        "src/devpilot_core/connectors/registry.py",
        ".devpilot/connectors/connector_registry.json",
        "docs/schemas/connector_registry.schema.json",
        "docs/03_security/mcp_connector_threat_model.md",
        "docs/06_miasi/connector_registry_card.md",
        "docs/audits/func_sprint_88_connector_registry_audit.md",
        "docs/functional_sprint_88_manifest.json",
        "tests/test_connector_registry.py",
    ]
    for rel in expected:
        assert (root / rel).exists(), rel

    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "Último hito: `FUNC-SPRINT-98" in readme
    assert "Siguiente hito: `FUNC-SPRINT-99" in readme
    assert "connector validate" in readme

    backlog = (root / "docs/devpilot_backlog_fase_H_capacidades_avanzadas.md").read_text(encoding="utf-8")
    assert 'last_completed_sprint: "FUNC-SPRINT-98"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-99"' in backlog
    assert "Estado de implementación Sprint 88" in backlog


def test_sprint_88_manifest_declares_mcp_boundaries() -> None:
    manifest = json.loads(Path("docs/functional_sprint_88_manifest.json").read_text(encoding="utf-8"))
    summary = manifest["summary"]
    assert manifest["sprint"] == "FUNC-SPRINT-88"
    assert summary["connector_schema_added"] is True
    assert summary["connector_registry_added"] is True
    assert summary["connector_validate_cli_added"] is True
    assert summary["deny_by_default"] is True
    assert summary["policy_rule_ids_required"] is True
    assert summary["mcp_enabled_by_default"] is False
    assert summary["mcp_client_implemented"] is False
    assert summary["mcp_server_implemented"] is False
    assert summary["connector_execution_enabled"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["dependencies_added"] is False


def test_sprint_88_docs_define_threat_model_and_miasi_policy() -> None:
    threat = Path("docs/03_security/mcp_connector_threat_model.md").read_text(encoding="utf-8")
    card = Path("docs/06_miasi/connector_registry_card.md").read_text(encoding="utf-8")
    runbook = Path("docs/05_operations/runbook.md").read_text(encoding="utf-8")
    assert "Amenazas" in threat
    assert "Controles" in threat
    assert "Criterios de bloqueo" in threat
    assert "tool poisoning" in threat.lower()
    assert "deny-by-default" in threat
    assert "CONNECTOR_REGISTRY_VALIDATE_ALLOW" in card
    assert "connector validate" in runbook


def test_sprint_88_miasi_registry_declares_connector_tools_and_policy() -> None:
    tools = json.loads(Path(".devpilot/miasi/tool_registry.json").read_text(encoding="utf-8"))["tools"]
    rules = json.loads(Path(".devpilot/miasi/policy_matrix.json").read_text(encoding="utf-8"))["rules"]
    assert any(tool["tool_id"] == "connector.validate" for tool in tools)
    assert any(tool["tool_id"] == "connector.discover" for tool in tools)
    for rule_id in ["CONNECTOR_REGISTRY_VALIDATE_ALLOW", "CONNECTOR_DISCOVERY_DENY_BY_DEFAULT", "MCP_EXECUTION_DENY", "CONNECTOR_EXTERNAL_API_DENY"]:
        assert any(rule["rule_id"] == rule_id for rule in rules)


def test_sprint_88_changelog_and_functional_backlog_are_synced() -> None:
    changelog = Path("docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    functional = Path("docs/functional_backlog_after_precode.md").read_text(encoding="utf-8")
    assert "FUNC-SPRINT-88" in changelog
    assert "Connector Registry" in changelog
    assert 'next_sprint: "FUNC-SPRINT-99"' in functional
    assert "Transición posterior a FUNC-SPRINT-88" in functional
