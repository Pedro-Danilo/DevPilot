from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_95_engineering_artifacts_exist() -> None:
    expected = [
        "src/devpilot_core/identity/__init__.py",
        "src/devpilot_core/identity/models.py",
        "src/devpilot_core/identity/rbac.py",
        ".devpilot/identity/identity_registry.json",
        "docs/schemas/identity_registry.schema.json",
        "evals/fixtures/identity_rbac_eval_cases.json",
        "docs/audits/func_sprint_95_rbac_audit.md",
        "docs/functional_sprint_95_manifest.json",
        "tests/test_identity_rbac.py",
        "tests/test_sprint_95_documentation.py",
    ]
    for path in expected:
        assert (ROOT / path).exists(), path


def test_sprint_95_readme_runbook_and_backlog_are_synchronized() -> None:
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    backlog = read("docs/devpilot_backlog_fase_H_capacidades_avanzadas.md")

    assert "FUNC-SPRINT-95 — RBAC local y modelo de identidad" in readme
    assert "FUNC-SPRINT-95 — Operación RBAC local y modelo de identidad" in runbook
    assert "Estado de implementación Sprint 95" in backlog


def test_sprint_95_manifest_and_audit_are_consistent() -> None:
    manifest = json.loads(read("docs/functional_sprint_95_manifest.json"))
    audit = read("docs/audits/func_sprint_95_rbac_audit.md")

    assert manifest["sprint_id"] == "FUNC-SPRINT-95"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["implemented_initial"] is True
    assert manifest["summary"]["remote_auth_enabled"] is False
    assert manifest["summary"]["credentials_stored"] is False
    assert manifest["next_sprint"] == "FUNC-SPRINT-96"
    assert "identity current --json" in audit
    assert "implemented-initial" in audit
    assert "sin autenticación remota" in audit


def test_sprint_95_identity_registry_and_schema_contracts() -> None:
    registry = json.loads(read(".devpilot/identity/identity_registry.json"))
    schema = json.loads(read("docs/schemas/identity_registry.schema.json"))
    catalog = json.loads(read("docs/schemas/schema_catalog.json"))

    role_ids = {role["role_id"] for role in registry["roles"]}
    assert registry["created_by"] == "FUNC-SPRINT-95"
    assert registry["defaults"]["auth_remote_enabled"] is False
    assert registry["defaults"]["credentials_stored"] is False
    assert registry["defaults"]["rbac_enforced_for_sensitive_actions"] is True
    assert {"owner", "architect", "developer", "reviewer", "operator", "agent-supervisor"}.issubset(role_ids)
    assert all(actor["credentials_stored"] is False for actor in registry["actors"])
    assert all(actor["remote_auth_enabled"] is False for actor in registry["actors"])
    assert schema["x-devpilot-schema-id"] == "SCHEMA-DEVPL-IDENTITY-REGISTRY-V1"
    assert "SCHEMA-DEVPL-IDENTITY-REGISTRY-V1" in {item["schema_id"] for item in catalog["schemas"]}


def test_sprint_95_miasi_policy_and_tool_bindings_exist() -> None:
    tools = json.loads(read(".devpilot/miasi/tool_registry.json"))["tools"]
    policies = json.loads(read(".devpilot/miasi/policy_matrix.json"))["rules"]
    agents = json.loads(read(".devpilot/miasi/agent_registry.json"))["agents"]

    tool_ids = {tool["tool_id"] for tool in tools}
    policy_ids = {policy["rule_id"] for policy in policies}
    for tool_id in ["identity.current", "identity.roles", "identity.rbac.check"]:
        assert tool_id in tool_ids
    for policy_id in ["IDENTITY_READ_LOCAL_ALLOW", "RBAC_CHECK_SENSITIVE_ACTION_ALLOW", "APPROVAL_ACTOR_BINDING_REQUIRED", "REMOTE_AUTH_DENY"]:
        assert policy_id in policy_ids
    security = next(agent for agent in agents if agent["agent_id"] == "security.agent")
    assert "identity.rbac.check" in security["allowed_tools"]
    assert "RBAC_CHECK_SENSITIVE_ACTION_ALLOW" in security["policy_rule_ids"]


def test_sprint_95_release_changelog_mentions_range() -> None:
    changelog = read("docs/release/CHANGELOG.md")

    assert "FUNC-SPRINT-95 — RBAC local y modelo de identidad" in changelog
