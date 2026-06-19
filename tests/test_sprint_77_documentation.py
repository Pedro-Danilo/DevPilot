from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_sprint_77_release_manifest_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog_g = _read("docs/devpilot_backlog_fase_G_productizacion_release.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")

    for path in [
        "src/devpilot_core/release/__init__.py",
        "src/devpilot_core/release/manifest.py",
        "docs/05_operations/release_manifest.md",
        "docs/audits/func_sprint_77_release_manifest_audit.md",
        "docs/functional_sprint_77_manifest.json",
        "tests/test_release_manifest.py",
        "tests/test_sprint_77_documentation.py",
    ]:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-91" in readme
    assert "Siguiente hito: `FUNC-SPRINT-92" in readme
    assert "FUNC-SPRINT-77 — Release metadata y Release Manifest" in readme
    assert "FUNC-SPRINT-77 — Operación de Release Manifest" in runbook
    assert 'source_repo: "repo_DevPilot_Local_106.zip"' in backlog_g
    assert 'last_completed_sprint: "FUNC-SPRINT-84"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-85"' in backlog_g
    assert 'phase_g_status: "closed"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-92"' in functional_backlog


def test_sprint_77_docs_define_release_manifest_boundaries() -> None:
    release_doc = _read("docs/05_operations/release_manifest.md")
    audit = _read("docs/audits/func_sprint_77_release_manifest_audit.md")

    for text in [release_doc, audit]:
        assert "release manifest --version 0.1.0 --json" in text
        assert "outputs/reports/release_manifest.json" in text
        assert "python -m pytest -q" in text
        assert "quality-gate run --profile ci" in text
        assert "no publica" in text
        assert "no despliega" in text
        assert "preliminar" in text or "primera versión" in text


def test_sprint_77_manifest_declares_release_scope() -> None:
    manifest = _json("docs/functional_sprint_77_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-77"
    assert manifest["status"] == "implemented"
    assert manifest["phase"] == "FASE-G-PRODUCTIZACION-RELEASE"
    assert manifest["summary"]["fg_level"] == "FG-L3"
    assert manifest["summary"]["release_manifest_cli_added"] is True
    assert manifest["summary"]["release_manifest_model_added"] is True
    assert manifest["summary"]["version_metadata_added"] is True
    assert manifest["summary"]["package_building_added"] is False
    assert manifest["summary"]["sbom_added"] is False
    assert manifest["summary"]["checksums_added"] is False
    assert manifest["summary"]["dependencies_added"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-78")
