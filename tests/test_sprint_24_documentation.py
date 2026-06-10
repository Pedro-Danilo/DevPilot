from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_24_readme_runbook_and_backlog_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_A_baseline_industrial_minima.md")

    assert "FUNC-SPRINT-24 — Artifact Profiles data-driven" in readme
    assert "FUNC-SPRINT-24 — Artifact Profiles data-driven" in runbook
    assert "Estado de implementación Sprint 24" in backlog
    assert "FUNC-SPRINT-25 — Traceability Model" in readme
    assert "first_open_sprint: \"FUNC-SPRINT-27\"" in backlog


def test_sprint_24_manifest_declares_gateway_and_no_adr_needed() -> None:
    payload = json.loads((ROOT / "docs/functional_sprint_24_manifest.json").read_text(encoding="utf-8"))

    assert payload["sprint"] == "FUNC-SPRINT-24"
    assert payload["status"] == "implemented"
    assert payload["architectural_decision"]["required"] is False
    assert "src/devpilot_core/validation/gateway.py" in payload["created_files"]
    assert "docs/validation/artifact_profiles.json" in payload["created_files"]
    assert payload["next_sprint"].startswith("FUNC-SPRINT-25")


def test_sprint_24_schema_catalog_registers_artifact_profiles_contract() -> None:
    catalog = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    contracts = {item["contract"] for item in catalog["schemas"]}

    assert "ArtifactProfiles" in contracts
    entry = next(item for item in catalog["schemas"] if item["contract"] == "ArtifactProfiles")
    assert entry["sprint"] == "FUNC-SPRINT-24"
    assert (ROOT / entry["path"]).exists()


def test_sprint_24_audit_documents_controls_and_limits() -> None:
    audit = _read("docs/audits/func_sprint_24_validation_gateway_audit.md")

    for required in ["Propósito", "Funcionamiento técnico", "Criterios PASS", "Criterios BLOCK", "Riesgos"]:
        assert required in audit
    assert "implemented-initial" in audit
    assert "fallback Python" in audit
    assert "no duplica reglas" in audit or "no duplicar reglas" in audit
