from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_sprint_79_packaging_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog_g = _read("docs/devpilot_backlog_fase_G_productizacion_release.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")

    for path in [
        "src/devpilot_core/release/package_builder.py",
        "docs/05_operations/packaging.md",
        "docs/audits/func_sprint_79_packaging_audit.md",
        "docs/functional_sprint_79_manifest.json",
        "tests/test_package_builder.py",
        "tests/test_sprint_79_documentation.py",
    ]:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-93" in readme
    assert "Siguiente hito: `FUNC-SPRINT-94" in readme
    assert "FUNC-SPRINT-79 — Packaging Python y ZIP limpio reproducible" in readme
    assert "FUNC-SPRINT-79 — Operación de Packaging" in runbook
    assert 'source_repo: "repo_DevPilot_Local_106.zip"' in backlog_g
    assert 'last_completed_sprint: "FUNC-SPRINT-84"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-85"' in backlog_g
    assert 'phase_g_status: "closed"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-94"' in functional_backlog


def test_sprint_79_docs_define_package_boundaries() -> None:
    packaging = _read("docs/05_operations/packaging.md")
    audit = _read("docs/audits/func_sprint_79_packaging_audit.md")
    release_manifest = _read("docs/05_operations/release_manifest.md")

    for text in [packaging, audit, release_manifest]:
        assert "PKG-CLEAN-ZIP" in text
        assert "PKG-WHEEL" in text
        assert "PKG-SDIST" in text
        assert "no publica" in text or "no publicar" in text or "publish" in text
        assert "no despliega" in text or "deploy" in text

    for marker in ["outputs/", ".pytest_cache/", "__pycache__/", ".venv/", ".git/", "node_modules/", ".devpilot/devpilot.db"]:
        assert marker in packaging


def test_sprint_79_manifest_declares_packaging_scope() -> None:
    manifest = _json("docs/functional_sprint_79_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-79"
    assert manifest["status"] == "implemented"
    assert manifest["phase"] == "FASE-G-PRODUCTIZACION-RELEASE"
    assert manifest["summary"]["fg_level"] == "FG-L4"
    assert manifest["summary"]["package_build_cli_added"] is True
    assert manifest["summary"]["repo_zip_supported"] is True
    assert manifest["summary"]["python_sdist_supported"] is True
    assert manifest["summary"]["python_wheel_supported"] is True
    assert manifest["summary"]["dry_run_default"] is True
    assert manifest["summary"]["network_used"] is False
    assert manifest["summary"]["external_api_used"] is False
    assert manifest["summary"]["publishes_artifacts"] is False
    assert manifest["summary"]["deploys_artifacts"] is False
    assert manifest["summary"]["dependencies_added"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-80")
