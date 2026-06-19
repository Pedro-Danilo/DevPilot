from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_98_engineering_artifacts_exist() -> None:
    expected = [
        "src/devpilot_core/enterprise/__init__.py",
        "src/devpilot_core/enterprise/report.py",
        "src/devpilot_core/remote/__init__.py",
        "src/devpilot_core/remote/runner.py",
        ".devpilot/remote/runner_registry.json",
        "docs/schemas/remote_runner.schema.json",
        "evals/fixtures/remote_enterprise_eval_cases.json",
        "tests/test_enterprise_reporting.py",
        "tests/test_sprint_98_documentation.py",
        "docs/02_architecture/adrs/ADR-0017-remote-runners-experimental.md",
        "docs/audits/func_sprint_98_enterprise_reporting_audit.md",
        "docs/functional_sprint_98_manifest.json",
    ]
    for path in expected:
        assert (ROOT / path).exists(), path


def test_sprint_98_readme_runbook_and_backlog_are_synchronized() -> None:
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    backlog = read("docs/devpilot_backlog_fase_H_capacidades_avanzadas.md")
    functional = read("docs/functional_backlog_after_precode.md")

    assert "Último hito: `FUNC-SPRINT-98" in readme
    assert "Siguiente hito: `FUNC-SPRINT-99" in readme
    assert "FUNC-SPRINT-98 — Remote runners experimentales y enterprise reporting" in readme
    assert "FUNC-SPRINT-98 — Operación de remote runners experimentales y enterprise reporting" in runbook
    assert "remote runner status" in runbook
    assert "enterprise report" in runbook
    assert 'version: "1.10.0"' in backlog
    assert 'source_repo: "repo_DevPilot_Local_127.zip"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-98"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-99"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-99"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-99"' in functional
    assert "Estado de implementación Sprint 98" in backlog


def test_sprint_98_manifest_audit_and_adr_are_consistent() -> None:
    manifest = json.loads(read("docs/functional_sprint_98_manifest.json"))
    audit = read("docs/audits/func_sprint_98_enterprise_reporting_audit.md")
    adr = read("docs/02_architecture/adrs/ADR-0017-remote-runners-experimental.md")

    assert manifest["sprint_id"] == "FUNC-SPRINT-98"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["implemented_initial"] is True
    assert manifest["summary"]["remote_runner_enabled"] is False
    assert manifest["summary"]["remote_execution_used"] is False
    assert manifest["summary"]["cloud_control_plane_enabled"] is False
    assert manifest["summary"]["adr_created"] is True
    assert manifest["next_sprint"] == "FUNC-SPRINT-99"
    assert "remote runner status" in audit
    assert "enterprise report" in audit
    assert "No se habilita ejecución remota" in adr


def test_sprint_98_registry_schema_fixture_and_catalog_are_registered() -> None:
    schema = json.loads(read("docs/schemas/remote_runner.schema.json"))
    catalog = json.loads(read("docs/schemas/schema_catalog.json"))
    fixture = json.loads(read("evals/fixtures/remote_enterprise_eval_cases.json"))
    registry = json.loads(read(".devpilot/remote/runner_registry.json"))

    assert schema["x-devpilot-schema-id"] == "SCHEMA-DEVPL-REMOTE-RUNNER-REGISTRY-V1"
    assert "SCHEMA-DEVPL-REMOTE-RUNNER-REGISTRY-V1" in {item["schema_id"] for item in catalog["schemas"]}
    assert fixture["suite_id"] == "remote-enterprise"
    assert len(fixture["cases"]) >= 4
    assert registry["security"]["remote_runner_enabled"] is False
    assert registry["security"]["execution_allowed"] is False
    assert registry["security"]["cloud_control_plane_enabled"] is False


def test_sprint_98_miasi_policy_and_tool_bindings_exist() -> None:
    tools = json.loads(read(".devpilot/miasi/tool_registry.json"))["tools"]
    policies = json.loads(read(".devpilot/miasi/policy_matrix.json"))["rules"]
    agents = json.loads(read(".devpilot/miasi/agent_registry.json"))["agents"]

    tool_ids = {tool["tool_id"] for tool in tools}
    policy_ids = {policy["rule_id"] for policy in policies}
    assert {"remote.runner.status", "enterprise.report"}.issubset(tool_ids)
    assert {
        "REMOTE_RUNNER_STATUS_ALLOW",
        "REMOTE_RUNNER_EXECUTE_DENY",
        "REMOTE_CLOUD_CONTROL_PLANE_DENY",
        "ENTERPRISE_REPORT_LOCAL_READ_ONLY_ALLOW",
    }.issubset(policy_ids)
    security = next(agent for agent in agents if agent["agent_id"] == "security.agent")
    assert "remote.runner.status" in security["allowed_tools"]
    assert "enterprise.report" in security["allowed_tools"]
    assert "REMOTE_RUNNER_EXECUTE_DENY" in security["policy_rule_ids"]
    assert "docs/audits/func_sprint_98_enterprise_reporting_audit.md" in security["required_artifacts"]


def test_sprint_98_release_changelog_mentions_range() -> None:
    changelog = read("docs/release/CHANGELOG.md")

    assert "Range: `FUNC-SPRINT-74` → `FUNC-SPRINT-98`" in changelog
    assert "FUNC-SPRINT-98" in changelog
    assert "Remote runners experimentales y enterprise reporting" in changelog
