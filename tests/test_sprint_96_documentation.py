from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_96_engineering_artifacts_exist() -> None:
    expected = [
        "src/devpilot_core/auditpack/__init__.py",
        "src/devpilot_core/auditpack/builder.py",
        "docs/schemas/audit_pack_manifest.schema.json",
        "evals/fixtures/audit_pack_integrity_eval_cases.json",
        "tests/test_audit_pack.py",
        "tests/test_sprint_96_documentation.py",
        "docs/05_operations/audit_pack_runbook.md",
        "docs/audits/func_sprint_96_audit_pack_audit.md",
        "docs/functional_sprint_96_manifest.json",
    ]
    for path in expected:
        assert (ROOT / path).exists(), path


def test_sprint_96_readme_runbook_and_backlog_are_synchronized() -> None:
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    audit_pack_runbook = read("docs/05_operations/audit_pack_runbook.md")
    backlog = read("docs/devpilot_backlog_fase_H_capacidades_avanzadas.md")
    functional = read("docs/functional_backlog_after_precode.md")

    assert "Último hito: `FUNC-SPRINT-97" in readme
    assert "Siguiente hito: `FUNC-SPRINT-98" in readme
    assert "FUNC-SPRINT-96 — Colaboración local y audit packs" in readme
    assert "FUNC-SPRINT-96 — Operación de audit packs locales" in runbook
    assert "audit-pack build --json" in audit_pack_runbook
    assert 'source_repo: "repo_DevPilot_Local_126.zip"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-97"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-98"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-98"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-98"' in functional
    assert "Estado de implementación Sprint 96" in backlog


def test_sprint_96_manifest_and_audit_are_consistent() -> None:
    manifest = json.loads(read("docs/functional_sprint_96_manifest.json"))
    audit = read("docs/audits/func_sprint_96_audit_pack_audit.md")

    assert manifest["sprint_id"] == "FUNC-SPRINT-96"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["implemented_initial"] is True
    assert manifest["summary"]["secrets_exported"] is False
    assert manifest["summary"]["runtime_db_exported"] is False
    assert manifest["next_sprint"] == "FUNC-SPRINT-97"
    assert "audit-pack build --json" in audit
    assert "audit-pack verify" in audit
    assert "implemented-initial" in audit


def test_sprint_96_schema_catalog_and_fixture_are_registered() -> None:
    schema = json.loads(read("docs/schemas/audit_pack_manifest.schema.json"))
    catalog = json.loads(read("docs/schemas/schema_catalog.json"))
    fixture = json.loads(read("evals/fixtures/audit_pack_integrity_eval_cases.json"))

    assert schema["x-devpilot-schema-id"] == "SCHEMA-DEVPL-AUDIT-PACK-MANIFEST-V1"
    assert "SCHEMA-DEVPL-AUDIT-PACK-MANIFEST-V1" in {item["schema_id"] for item in catalog["schemas"]}
    assert fixture["suite_id"] == "audit-pack-integrity"
    assert len(fixture["cases"]) >= 4


def test_sprint_96_miasi_policy_and_tool_bindings_exist() -> None:
    tools = json.loads(read(".devpilot/miasi/tool_registry.json"))["tools"]
    policies = json.loads(read(".devpilot/miasi/policy_matrix.json"))["rules"]
    agents = json.loads(read(".devpilot/miasi/agent_registry.json"))["agents"]

    tool_ids = {tool["tool_id"] for tool in tools}
    policy_ids = {policy["rule_id"] for policy in policies}
    assert {"auditpack.build", "auditpack.verify"}.issubset(tool_ids)
    assert {"AUDIT_PACK_BUILD_LOCAL_ALLOW", "AUDIT_PACK_VERIFY_LOCAL_ALLOW", "AUDIT_PACK_SECRET_EXPORT_DENY", "AUDIT_PACK_INTEGRITY_REQUIRED"}.issubset(policy_ids)
    security = next(agent for agent in agents if agent["agent_id"] == "security.agent")
    assert "auditpack.build" in security["allowed_tools"]
    assert "AUDIT_PACK_INTEGRITY_REQUIRED" in security["policy_rule_ids"]


def test_sprint_96_release_changelog_mentions_range() -> None:
    changelog = read("docs/release/CHANGELOG.md")

    assert "Range: `FUNC-SPRINT-74` → `FUNC-SPRINT-97`" in changelog
    assert "FUNC-SPRINT-96 — Colaboración local y audit packs" in changelog
