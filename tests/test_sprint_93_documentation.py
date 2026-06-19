from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_93_engineering_artifacts_exist() -> None:
    expected = [
        "src/devpilot_core/plugins/__init__.py",
        "src/devpilot_core/plugins/registry.py",
        ".devpilot/plugins/plugin_registry.json",
        "docs/schemas/plugin_manifest.schema.json",
        "evals/fixtures/plugin_ecosystem_eval_cases.json",
        "docs/audits/func_sprint_93_plugin_ecosystem_audit.md",
        "docs/functional_sprint_93_manifest.json",
        "tests/test_plugin_registry.py",
        "tests/test_sprint_93_documentation.py",
    ]
    for path in expected:
        assert (ROOT / path).exists(), path


def test_sprint_93_readme_runbook_and_backlog_are_synchronized() -> None:
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    backlog = read("docs/devpilot_backlog_fase_H_capacidades_avanzadas.md")

    assert "Último hito: `FUNC-SPRINT-93" in readme
    assert "Siguiente hito: `FUNC-SPRINT-94" in readme
    assert "FUNC-SPRINT-93 — Plugin y connector ecosystem controlado" in readme
    assert "FUNC-SPRINT-93 — Operación Plugin y connector ecosystem controlado" in runbook
    assert 'source_repo: "repo_DevPilot_Local_121.zip"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-93"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-94"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-94"' in backlog
    assert "FUNC-SPRINT-93" in backlog
    assert "FUNC-SPRINT-94" in backlog


def test_sprint_93_manifest_and_audit_are_consistent() -> None:
    manifest = json.loads(read("docs/functional_sprint_93_manifest.json"))
    audit = read("docs/audits/func_sprint_93_plugin_ecosystem_audit.md")

    assert manifest["sprint_id"] == "FUNC-SPRINT-93"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["implemented_initial"] is True
    assert manifest["next_sprint"] == "FUNC-SPRINT-94"
    assert "plugin validate --json" in audit
    assert "Plugin loading ejecutable queda deshabilitado" in audit
    assert "implemented-initial" in audit


def test_sprint_93_plugin_registry_and_schema_contracts() -> None:
    registry = json.loads(read(".devpilot/plugins/plugin_registry.json"))
    schema = json.loads(read("docs/schemas/plugin_manifest.schema.json"))
    catalog = json.loads(read("docs/schemas/schema_catalog.json"))

    assert registry["created_by"] == "FUNC-SPRINT-93"
    assert registry["defaults"]["plugin_default_effect"] == "deny"
    assert registry["defaults"]["executable_loading_default"] is False
    assert registry["security"]["plugin_code_loaded"] is False
    assert registry["security"]["arbitrary_code_execution_performed"] is False
    assert all(plugin["execution_enabled"] is False for plugin in registry["plugins"])
    assert all(plugin["observability_required"] is True for plugin in registry["plugins"])
    assert all(plugin["eval_required"] is True for plugin in registry["plugins"])
    assert schema["x-devpilot-schema-id"] == "SCHEMA-DEVPL-PLUGIN-MANIFEST-V1"
    assert "SCHEMA-DEVPL-PLUGIN-MANIFEST-V1" in {item["schema_id"] for item in catalog["schemas"]}


def test_sprint_93_miasi_policy_and_tool_bindings_exist() -> None:
    tools = json.loads(read(".devpilot/miasi/tool_registry.json"))["tools"]
    policies = json.loads(read(".devpilot/miasi/policy_matrix.json"))["rules"]
    agents = json.loads(read(".devpilot/miasi/agent_registry.json"))["agents"]

    tool_ids = {tool["tool_id"] for tool in tools}
    policy_ids = {policy["rule_id"] for policy in policies}
    assert "plugin.registry.validate" in tool_ids
    assert "plugin.loader.dry_run" in tool_ids
    for policy_id in ["PLUGIN_METADATA_READ_ALLOW", "PLUGIN_DRY_RUN_ONLY_ALLOW", "PLUGIN_CONNECTOR_BINDING_ALLOW", "PLUGIN_EXECUTE_DENY"]:
        assert policy_id in policy_ids
    coordinator = next(agent for agent in agents if agent["agent_id"] == "multiagent.coordinator")
    assert "plugin.registry.validate" in coordinator["allowed_tools"]
    assert "plugin.loader.dry_run" in coordinator["allowed_tools"]


def test_sprint_93_release_changelog_mentions_range() -> None:
    changelog = read("docs/release/CHANGELOG.md")

    assert "Range: `FUNC-SPRINT-74` → `FUNC-SPRINT-93`" in changelog
    assert "FUNC-SPRINT-93 — Plugin y connector ecosystem controlado" in changelog
