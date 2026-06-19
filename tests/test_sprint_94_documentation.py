from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_94_engineering_artifacts_exist() -> None:
    expected = [
        "src/devpilot_core/workspace/registry.py",
        "src/devpilot_core/portfolio/__init__.py",
        "src/devpilot_core/portfolio/status.py",
        ".devpilot/workspaces/workspace_registry.json",
        "docs/schemas/multiworkspace_registry.schema.json",
        "evals/fixtures/multiworkspace_isolation_eval_cases.json",
        "docs/audits/func_sprint_94_multiworkspace_audit.md",
        "docs/functional_sprint_94_manifest.json",
        "tests/test_multiworkspace.py",
        "tests/test_sprint_94_documentation.py",
    ]
    for path in expected:
        assert (ROOT / path).exists(), path


def test_sprint_94_readme_runbook_and_backlog_are_synchronized() -> None:
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    backlog = read("docs/devpilot_backlog_fase_H_capacidades_avanzadas.md")

    assert "Último hito: `FUNC-SPRINT-97" in readme
    assert "Siguiente hito: `FUNC-SPRINT-98" in readme
    assert "FUNC-SPRINT-94 — Multiworkspace Manager y portfolio local" in readme
    assert "FUNC-SPRINT-94 — Operación Multiworkspace Manager y portfolio local" in runbook
    assert 'source_repo: "repo_DevPilot_Local_126.zip"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-97"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-98"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-98"' in backlog
    assert "Estado de implementación Sprint 94" in backlog


def test_sprint_94_manifest_and_audit_are_consistent() -> None:
    manifest = json.loads(read("docs/functional_sprint_94_manifest.json"))
    audit = read("docs/audits/func_sprint_94_multiworkspace_audit.md")

    assert manifest["sprint_id"] == "FUNC-SPRINT-94"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["implemented_initial"] is True
    assert manifest["next_sprint"] == "FUNC-SPRINT-95"
    assert "workspace registry-validate --json" in audit
    assert "implemented-initial" in audit
    assert "No habilita SaaS" in audit


def test_sprint_94_multiworkspace_registry_and_schema_contracts() -> None:
    registry = json.loads(read(".devpilot/workspaces/workspace_registry.json"))
    schema = json.loads(read("docs/schemas/multiworkspace_registry.schema.json"))
    catalog = json.loads(read("docs/schemas/schema_catalog.json"))

    assert registry["created_by"] == "FUNC-SPRINT-94"
    assert registry["defaults"]["deny_unregistered_workspaces"] is True
    assert registry["defaults"]["cross_workspace_state_reads"] is False
    assert registry["defaults"]["secret_sharing_allowed"] is False
    assert registry["security"]["secrets_read"] is False
    assert all(workspace["state_path"] == ".devpilot/devpilot.db" for workspace in registry["workspaces"])
    assert all(workspace["secret_policy"] == "reference-only" for workspace in registry["workspaces"])
    assert schema["x-devpilot-schema-id"] == "SCHEMA-DEVPL-MULTIWORKSPACE-REGISTRY-V1"
    assert "SCHEMA-DEVPL-MULTIWORKSPACE-REGISTRY-V1" in {item["schema_id"] for item in catalog["schemas"]}


def test_sprint_94_miasi_policy_and_tool_bindings_exist() -> None:
    tools = json.loads(read(".devpilot/miasi/tool_registry.json"))["tools"]
    policies = json.loads(read(".devpilot/miasi/policy_matrix.json"))["rules"]
    agents = json.loads(read(".devpilot/miasi/agent_registry.json"))["agents"]

    tool_ids = {tool["tool_id"] for tool in tools}
    policy_ids = {policy["rule_id"] for policy in policies}
    for tool_id in ["workspace.registry.validate", "workspace.registry.register", "workspace.registry.select", "portfolio.status"]:
        assert tool_id in tool_ids
    for policy_id in ["MULTIWORKSPACE_REGISTRY_VALIDATE_ALLOW", "MULTIWORKSPACE_REGISTER_LOCAL_ALLOW", "MULTIWORKSPACE_SELECT_LOCAL_ALLOW", "PORTFOLIO_STATUS_READ_ONLY_ALLOW", "MULTIWORKSPACE_ISOLATION_REQUIRED"]:
        assert policy_id in policy_ids
    operations = next(agent for agent in agents if agent["agent_id"] == "operations.agent")
    assert operations["status"] == "implemented-initial"
    assert "portfolio.status" in operations["allowed_tools"]


def test_sprint_94_release_changelog_mentions_range() -> None:
    changelog = read("docs/release/CHANGELOG.md")

    assert "Range: `FUNC-SPRINT-74` → `FUNC-SPRINT-97`" in changelog
    assert "FUNC-SPRINT-94 — Multiworkspace Manager y portfolio local" in changelog
