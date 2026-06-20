from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_97_engineering_artifacts_exist() -> None:
    expected = [
        "src/devpilot_core/compliance/__init__.py",
        "src/devpilot_core/compliance/registry.py",
        "src/devpilot_core/compliance/runner.py",
        ".devpilot/compliance/packs.json",
        "docs/schemas/compliance_pack.schema.json",
        "evals/fixtures/compliance_pack_integrity_eval_cases.json",
        "tests/test_compliance_packs.py",
        "tests/test_sprint_97_documentation.py",
        "docs/audits/func_sprint_97_compliance_packs_audit.md",
        "docs/functional_sprint_97_manifest.json",
    ]
    for path in expected:
        assert (ROOT / path).exists(), path


def test_sprint_97_readme_runbook_and_backlog_are_synchronized() -> None:
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    backlog = read("docs/devpilot_backlog_fase_H_capacidades_avanzadas.md")
    functional = read("docs/functional_backlog_after_precode.md")

    assert "FUNC-SPRINT-97 — Compliance packs y policy packs" in readme
    assert "FUNC-SPRINT-97 — Operación de compliance packs y policy packs" in runbook
    assert "compliance run --pack baseline" in runbook
    assert 'version: "1.11.0"' in backlog
    assert "Estado de implementación Sprint 97" in backlog


def test_sprint_97_manifest_and_audit_are_consistent() -> None:
    manifest = json.loads(read("docs/functional_sprint_97_manifest.json"))
    audit = read("docs/audits/func_sprint_97_compliance_packs_audit.md")

    assert manifest["sprint_id"] == "FUNC-SPRINT-97"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["implemented_initial"] is True
    assert manifest["summary"]["declarative_only"] is True
    assert manifest["summary"]["policy_engine_used"] is True
    assert manifest["summary"]["policy_engine_replaced"] is False
    assert manifest["summary"]["network_used"] is False
    assert manifest["summary"]["external_api_used"] is False
    assert manifest["next_sprint"] == "FUNC-SPRINT-98"
    assert "compliance list --json" in audit
    assert "compliance run --pack baseline" in audit
    assert "implemented-initial" in audit


def test_sprint_97_registry_schema_and_fixture_are_registered() -> None:
    schema = json.loads(read("docs/schemas/compliance_pack.schema.json"))
    catalog = json.loads(read("docs/schemas/schema_catalog.json"))
    fixture = json.loads(read("evals/fixtures/compliance_pack_integrity_eval_cases.json"))
    registry = json.loads(read(".devpilot/compliance/packs.json"))

    assert schema["x-devpilot-schema-id"] == "SCHEMA-DEVPL-COMPLIANCE-PACK-V1"
    assert "SCHEMA-DEVPL-COMPLIANCE-PACK-V1" in {item["schema_id"] for item in catalog["schemas"]}
    assert fixture["suite_id"] == "compliance-pack-integrity"
    assert len(fixture["cases"]) >= 4
    assert registry["security"]["policy_engine_required"] is True
    assert registry["security"]["arbitrary_command_execution_allowed"] is False
    assert registry["packs"][0]["pack_id"] == "baseline"


def test_sprint_97_miasi_policy_and_tool_bindings_exist() -> None:
    tools = json.loads(read(".devpilot/miasi/tool_registry.json"))["tools"]
    policies = json.loads(read(".devpilot/miasi/policy_matrix.json"))["rules"]
    agents = json.loads(read(".devpilot/miasi/agent_registry.json"))["agents"]

    tool_ids = {tool["tool_id"] for tool in tools}
    policy_ids = {policy["rule_id"] for policy in policies}
    assert {"compliance.list", "compliance.run"}.issubset(tool_ids)
    assert {
        "COMPLIANCE_PACK_READ_ALLOW",
        "COMPLIANCE_PACK_RUN_DECLARATIVE_ALLOW",
        "COMPLIANCE_PACK_POLICY_ENGINE_REQUIRED",
        "COMPLIANCE_PACK_UNDECLARED_ACTION_DENY",
    }.issubset(policy_ids)
    security = next(agent for agent in agents if agent["agent_id"] == "security.agent")
    assert "compliance.run" in security["allowed_tools"]
    assert "COMPLIANCE_PACK_POLICY_ENGINE_REQUIRED" in security["policy_rule_ids"]
    assert "docs/audits/func_sprint_97_compliance_packs_audit.md" in security["required_artifacts"]


def test_sprint_97_release_changelog_mentions_range() -> None:
    changelog = read("docs/release/CHANGELOG.md")

    assert "FUNC-SPRINT-97" in changelog
    assert "Compliance packs y policy packs" in changelog
