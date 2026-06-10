from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_25_readme_runbook_and_backlog_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_A_baseline_industrial_minima.md")

    assert "FUNC-SPRINT-25 — Traceability Model" in readme
    assert "FUNC-SPRINT-25 — Traceability Model" in runbook
    assert "Estado de implementación Sprint 25" in backlog
    assert "FUNC-SPRINT-26 — Traceability Engine" in readme
    assert "first_open_sprint: \"FUNC-SPRINT-27\"" in backlog


def test_sprint_25_manifest_declares_traceability_files_and_no_adr_needed() -> None:
    payload = json.loads((ROOT / "docs/functional_sprint_25_manifest.json").read_text(encoding="utf-8"))

    assert payload["sprint"] == "FUNC-SPRINT-25"
    assert payload["status"] == "implemented"
    assert payload["architectural_decision"]["required"] is False
    assert "src/devpilot_core/traceability/models.py" in payload["created_files"]
    assert "src/devpilot_core/traceability/extractors.py" in payload["created_files"]
    assert "tests/test_traceability_extractors.py" in payload["created_files"]
    assert payload["next_sprint"].startswith("FUNC-SPRINT-26")


def test_sprint_25_audit_documents_controls_and_limits() -> None:
    audit = _read("docs/audits/func_sprint_25_traceability_model_audit.md")

    for required in ["Propósito", "Funcionamiento técnico", "Criterios PASS", "Criterios BLOCK", "Riesgos"]:
        assert required in audit
    assert "implemented-initial" in audit
    assert "no infiere relaciones" in audit or "no inferir relaciones" in audit
    assert "TRACEABILITY_ENTITY_DUPLICATE" in audit


def test_sprint_25_no_new_dependency_or_adr_required() -> None:
    manifest = json.loads((ROOT / "docs/functional_sprint_25_manifest.json").read_text(encoding="utf-8"))
    pyproject = _read("pyproject.toml")

    assert manifest["architectural_decision"]["required"] is False
    assert "PyYAML" not in pyproject
    assert "network" not in manifest["architectural_decision"]["reason"].lower() or "external" in manifest["architectural_decision"]["reason"].lower()
