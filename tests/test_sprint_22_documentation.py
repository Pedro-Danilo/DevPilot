from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_22_readme_runbook_and_backlog_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_A_baseline_industrial_minima.md")

    assert "FUNC-SPRINT-22 — Schema Validator" in readme
    assert "FUNC-SPRINT-22 — Schema Validator" in runbook
    assert "Estado de implementación Sprint 22" in backlog
    assert "FUNC-SPRINT-23 — Schemas MIASI" in readme
    assert "first_open_sprint: \"FUNC-SPRINT-26\"" in backlog


def test_sprint_22_manifest_declares_adr_dependency_and_files() -> None:
    payload = json.loads((ROOT / "docs/functional_sprint_22_manifest.json").read_text(encoding="utf-8"))

    assert payload["sprint"] == "FUNC-SPRINT-22"
    assert payload["status"] == "implemented"
    assert payload["architectural_decision"]["required"] is True
    assert payload["architectural_decision"]["adr"] == "docs/02_architecture/adrs/ADR-0010-schema-validation-dependency.md"
    assert "src/devpilot_core/schemas/validator.py" in payload["created_files"]
    assert "pyproject.toml" in payload["modified_files"]
    assert payload["next_sprint"].startswith("FUNC-SPRINT-23")


def test_sprint_22_audit_and_adr_document_required_controls() -> None:
    audit = _read("docs/audits/func_sprint_22_schema_validator_audit.md")
    adr = _read("docs/02_architecture/adrs/ADR-0010-schema-validation-dependency.md")

    for required in ["Propósito", "Funcionamiento técnico", "Criterios PASS", "Criterios BLOCK", "Riesgos"]:
        assert required in audit
    assert "jsonschema>=4.22,<5" in adr
    assert "no debe hacer llamadas de red" in adr
    assert "Accepted" in adr


def test_sprint_22_pyproject_declares_jsonschema_dependency() -> None:
    pyproject = _read("pyproject.toml")

    assert "jsonschema>=4.22,<5" in pyproject
