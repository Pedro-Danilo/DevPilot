from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_23_readme_runbook_and_backlog_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_A_baseline_industrial_minima.md")

    assert "FUNC-SPRINT-23 — Schemas MIASI" in readme
    assert "FUNC-SPRINT-23 — Schemas MIASI" in runbook
    assert "Estado de implementación Sprint 23" in backlog
    assert "FUNC-SPRINT-24 — Artifact Profiles" in readme
    assert "first_open_sprint: \"FUNC-SPRINT-26\"" in backlog


def test_sprint_23_manifest_declares_contract_schemas_and_no_adr_needed() -> None:
    payload = json.loads((ROOT / "docs/functional_sprint_23_manifest.json").read_text(encoding="utf-8"))

    assert payload["sprint"] == "FUNC-SPRINT-23"
    assert payload["status"] == "implemented"
    assert payload["architectural_decision"]["required"] is False
    assert "src/devpilot_core/schemas/builtins.py" in payload["created_files"]
    assert "docs/schemas/miasi_agent_registry.schema.json" in payload["created_files"]
    assert "docs/schemas/provider_config.schema.json" in payload["created_files"]
    assert payload["next_sprint"].startswith("FUNC-SPRINT-24")


def test_sprint_23_schema_catalog_registers_critical_contracts() -> None:
    catalog = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    contracts = {item["contract"] for item in catalog["schemas"]}

    expected = {
        "MiasiAgentRegistry",
        "MiasiToolRegistry",
        "MiasiPolicyMatrix",
        "WorkspaceProject",
        "ProviderConfig",
        "FunctionalSprintManifest",
    }
    assert expected.issubset(contracts)


def test_sprint_23_audit_documents_controls_and_limits() -> None:
    audit = _read("docs/audits/func_sprint_23_contract_schemas_audit.md")

    for required in ["Propósito", "Funcionamiento técnico", "Criterios PASS", "Criterios BLOCK", "Riesgos"]:
        assert required in audit
    assert "implemented-initial" in audit
    assert "no sustituyen validaciones semánticas" in audit or "no sustituye validaciones semánticas" in audit
    assert "PyYAML" in audit
