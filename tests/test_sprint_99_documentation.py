from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_99_engineering_artifacts_exist() -> None:
    expected = [
        "src/devpilot_core/industrial/__init__.py",
        "src/devpilot_core/industrial/readiness.py",
        "docs/schemas/industrial_readiness.schema.json",
        "tests/test_industrial_readiness.py",
        "tests/test_sprint_99_documentation.py",
        "docs/audits/phase_h_advanced_capabilities_closure.md",
        "docs/backlogs/post_phase_h_ideas.md",
        "docs/functional_sprint_99_manifest.json",
    ]
    for path in expected:
        assert (ROOT / path).exists(), path


def test_sprint_99_readme_runbook_and_backlogs_are_synchronized() -> None:
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    backlog = read("docs/devpilot_backlog_fase_H_capacidades_avanzadas.md")
    functional = read("docs/functional_backlog_after_precode.md")

    assert "Último hito: `FUNC-SPRINT-99" in readme
    assert "Siguiente hito: `POST-H-001" in readme
    assert "FUNC-SPRINT-99 — Industrial readiness gate y cierre Fase H" in readme
    assert "FUNC-SPRINT-99 — Operación de Industrial Readiness Gate" in runbook
    assert "industrial-readiness check" in runbook
    assert "quality-gate run --profile industrial" in runbook
    assert 'version: "1.11.0"' in backlog
    assert 'source_repo: "repo_DevPilot_Local_128.zip"' in backlog
    assert 'phase_h_status: "closed_implemented_initial"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-99"' in backlog
    assert 'next_sprint: "POST-H-001"' in backlog
    assert 'first_open_sprint: "POST-H-001"' in backlog
    assert 'next_sprint: "POST-H-001"' in functional
    assert "Estado de implementación Sprint 99 y cierre Fase H" in backlog


def test_sprint_99_manifest_closure_and_post_h_backlog_are_consistent() -> None:
    manifest = json.loads(read("docs/functional_sprint_99_manifest.json"))
    closure = read("docs/audits/phase_h_advanced_capabilities_closure.md")
    post_h = read("docs/backlogs/post_phase_h_ideas.md")

    assert manifest["sprint_id"] == "FUNC-SPRINT-99"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["phase_h_closed"] is True
    assert manifest["summary"]["industrial_readiness_gate"] is True
    assert manifest["summary"]["maturity_classification"] is True
    assert manifest["summary"]["overclaim_blocked"] is True
    assert manifest["summary"]["remote_runner_enabled"] is False
    assert manifest["next_sprint"] == "POST-H-001"
    assert "production-ready" in closure
    assert "implemented-initial" in closure
    assert "experimental" in closure
    assert "POST-H-001" in post_h
    assert "Industrial hardening" in post_h


def test_sprint_99_schema_catalog_and_miasi_are_registered() -> None:
    schema = json.loads(read("docs/schemas/industrial_readiness.schema.json"))
    catalog = json.loads(read("docs/schemas/schema_catalog.json"))
    tools = json.loads(read(".devpilot/miasi/tool_registry.json"))["tools"]
    policies = json.loads(read(".devpilot/miasi/policy_matrix.json"))["rules"]
    agents = json.loads(read(".devpilot/miasi/agent_registry.json"))["agents"]

    assert schema["x-devpilot-schema-id"] == "SCHEMA-DEVPL-INDUSTRIAL-READINESS-V1"
    assert "SCHEMA-DEVPL-INDUSTRIAL-READINESS-V1" in {item["schema_id"] for item in catalog["schemas"]}
    assert "industrial.readiness.check" in {tool["tool_id"] for tool in tools}
    assert {
        "INDUSTRIAL_READINESS_LOCAL_ALLOW",
        "INDUSTRIAL_READINESS_OVERCLAIM_DENY",
        "INDUSTRIAL_READINESS_PHASE_H_CLOSURE_REQUIRED",
    }.issubset({rule["rule_id"] for rule in policies})
    operations = next(agent for agent in agents if agent["agent_id"] == "operations.agent")
    assert "industrial.readiness.check" in operations["allowed_tools"]
    assert "docs/audits/phase_h_advanced_capabilities_closure.md" in operations["required_artifacts"]


def test_sprint_99_changelog_mentions_phase_h_closure() -> None:
    changelog = read("docs/release/CHANGELOG.md")

    assert "Range: `FUNC-SPRINT-74` → `FUNC-SPRINT-99`" in changelog
    assert "FUNC-SPRINT-99" in changelog
    assert "Industrial readiness gate y cierre Fase H" in changelog
    assert "docs/functional_sprint_99_manifest.json" in changelog
