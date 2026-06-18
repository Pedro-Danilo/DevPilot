from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_sprint_75_quality_gate_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog_g = _read("docs/devpilot_backlog_fase_G_productizacion_release.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")

    for path in [
        "src/devpilot_core/quality/__init__.py",
        "src/devpilot_core/quality/gate.py",
        "tests/test_quality_gate.py",
        "tests/test_sprint_75_documentation.py",
        "docs/audits/func_sprint_75_quality_gate_audit.md",
        "docs/functional_sprint_75_manifest.json",
    ]:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-85" in readme
    assert "Siguiente hito: `FUNC-SPRINT-86" in readme
    assert "FUNC-SPRINT-75 — Quality Gate local unificado" in readme
    assert "FUNC-SPRINT-75 — Operación del Quality Gate local unificado" in runbook
    assert 'source_repo: "repo_DevPilot_Local_106.zip"' in backlog_g
    assert 'last_completed_sprint: "FUNC-SPRINT-84"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-85"' in backlog_g
    assert 'phase_g_status: "closed"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-86"' in functional_backlog


def test_sprint_75_audit_documents_quality_gate_boundaries() -> None:
    audit = _read("docs/audits/func_sprint_75_quality_gate_audit.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")

    for text in [audit, readme, runbook]:
        assert "quality-gate run" in text
        assert "readiness" in text
        assert "standards" in text
        assert "MIASI" in text
        assert "app contract" in text or "ApplicationService" in text
        assert "--write-report" in text

    assert "pytest es opcional" in audit
    assert "no publica" in audit
    assert "primera versión operacional" in audit


def test_sprint_75_manifest_declares_initial_quality_gate_scope() -> None:
    manifest = _json("docs/functional_sprint_75_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-75"
    assert manifest["status"] == "implemented"
    assert manifest["phase"] == "FASE-G-PRODUCTIZACION-RELEASE"
    assert manifest["summary"]["fg_level"] == "FG-L1"
    assert manifest["summary"]["quality_gate_cli_added"] is True
    assert manifest["summary"]["default_profile"] == "fast"
    assert manifest["summary"]["pytest_optional"] is True
    assert manifest["summary"]["external_publication_out_of_scope"] is True
    assert manifest["summary"]["dependencies_added"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-76")
