from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_sprint_82_installation_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog_g = _read("docs/devpilot_backlog_fase_G_productizacion_release.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")

    for path in [
        "src/devpilot_core/release/installation.py",
        "docs/05_operations/install_guide.md",
        "docs/02_architecture/adrs/ADR-0015-installation-strategy.md",
        "docs/audits/func_sprint_82_installation_audit.md",
        "docs/functional_sprint_82_manifest.json",
        "tests/test_installation_plan.py",
        "tests/test_sprint_82_documentation.py",
    ]:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-84" in readme
    assert "Siguiente hito: `FUNC-SPRINT-85" in readme
    assert "FUNC-SPRINT-83 — Backup, restore y upgrade local" in readme
    assert "FUNC-SPRINT-82 — Operación de instalación local" in runbook
    assert 'source_repo: "repo_DevPilot_Local_106.zip"' in backlog_g
    assert 'last_completed_sprint: "FUNC-SPRINT-84"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-85"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-85"' in functional_backlog


def test_sprint_82_docs_define_installation_boundaries() -> None:
    install_guide = _read("docs/05_operations/install_guide.md")
    adr = _read("docs/02_architecture/adrs/ADR-0015-installation-strategy.md")
    audit = _read("docs/audits/func_sprint_82_installation_audit.md")
    release_manifest = _read("docs/05_operations/release_manifest.md")
    artifacts_matrix = _read("docs/05_operations/release_artifacts_matrix.md")
    changelog = _read("docs/release/CHANGELOG.md")

    for text in [install_guide, adr, audit, release_manifest, artifacts_matrix, changelog]:
        assert "FUNC-SPRINT-82" in text

    for marker in [
        "install plan",
        "editable",
        "wheel",
        "ZIP",
        "desktop-bridge",
        "no auto-update",
        "no requiere privilegios elevados",
        "no instala servicios",
    ]:
        assert marker in install_guide

    assert "INSTALL-PLAN" in release_manifest
    assert "INSTALL-PLAN" in artifacts_matrix
    assert "FUNC-SPRINT-82` — `docs/functional_sprint_82_manifest.json`" in changelog


def test_sprint_82_manifest_declares_installation_scope() -> None:
    manifest = _json("docs/functional_sprint_82_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-82"
    assert manifest["status"] == "implemented"
    assert manifest["phase"] == "FASE-G-PRODUCTIZACION-RELEASE"
    assert manifest["summary"]["fg_level"] == "FG-L7"
    assert manifest["summary"]["install_plan_cli_added"] is True
    assert manifest["summary"]["install_guide_added"] is True
    assert manifest["summary"]["installation_strategy_adr_added"] is True
    assert manifest["summary"]["dry_run_default"] is True
    assert manifest["summary"]["execute_supported"] is False
    assert manifest["summary"]["auto_update_enabled"] is False
    assert manifest["summary"]["persistent_services_installed"] is False
    assert manifest["summary"]["admin_privileges_required"] is False
    assert manifest["summary"]["network_required"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-83")
