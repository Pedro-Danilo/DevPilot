from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_sprint_83_backup_upgrade_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog_g = _read("docs/devpilot_backlog_fase_G_productizacion_release.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")

    for path in [
        "src/devpilot_core/release/backup.py",
        "src/devpilot_core/release/upgrade.py",
        "docs/05_operations/backup_restore_upgrade.md",
        "docs/audits/func_sprint_83_backup_upgrade_audit.md",
        "docs/functional_sprint_83_manifest.json",
        "tests/test_backup_upgrade.py",
        "tests/test_sprint_83_documentation.py",
    ]:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-90" in readme
    assert "Siguiente hito: `FUNC-SPRINT-91" in readme
    assert "FUNC-SPRINT-83 — Backup, restore y upgrade local" in readme
    assert "FUNC-SPRINT-83 — Operación de backup" in runbook
    assert 'source_repo: "repo_DevPilot_Local_106.zip"' in backlog_g
    assert 'last_completed_sprint: "FUNC-SPRINT-84"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-85"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-91"' in functional_backlog


def test_sprint_83_docs_define_backup_restore_boundaries() -> None:
    backup_doc = _read("docs/05_operations/backup_restore_upgrade.md")
    audit = _read("docs/audits/func_sprint_83_backup_upgrade_audit.md")
    release_manifest = _read("docs/05_operations/release_manifest.md")
    artifacts_matrix = _read("docs/05_operations/release_artifacts_matrix.md")
    changelog = _read("docs/release/CHANGELOG.md")

    for text in [backup_doc, audit, release_manifest, artifacts_matrix, changelog]:
        assert "FUNC-SPRINT-83" in text

    for marker in [
        "backup create",
        "backup list",
        "backup restore",
        "upgrade check",
        "--confirm-restore",
        "SecretGuard",
        "PathGuard",
        "dry-run por defecto",
    ]:
        assert marker in backup_doc

    for marker in ["BACKUP-MANIFEST", "BACKUP-REPORT", "RESTORE-PLAN", "UPGRADE-CHECK"]:
        assert marker in release_manifest
        assert marker in artifacts_matrix

    assert "FUNC-SPRINT-83` — `docs/functional_sprint_83_manifest.json`" in changelog


def test_sprint_83_manifest_declares_backup_upgrade_scope() -> None:
    manifest = _json("docs/functional_sprint_83_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-83"
    assert manifest["status"] == "implemented"
    assert manifest["phase"] == "FASE-G-PRODUCTIZACION-RELEASE"
    assert manifest["summary"]["fg_level"] == "FG-L8"
    assert manifest["summary"]["backup_create_cli_added"] is True
    assert manifest["summary"]["backup_list_cli_added"] is True
    assert manifest["summary"]["backup_restore_cli_added"] is True
    assert manifest["summary"]["upgrade_check_cli_added"] is True
    assert manifest["summary"]["dry_run_default"] is True
    assert manifest["summary"]["restore_execute_requires_confirmation"] is True
    assert manifest["summary"]["path_guard_integrated"] is True
    assert manifest["summary"]["secret_guard_integrated"] is True
    assert manifest["summary"]["outputs_excluded_by_default"] is True
    assert manifest["summary"]["venv_excluded_by_default"] is True
    assert manifest["summary"]["git_dir_excluded_by_default"] is True
    assert manifest["summary"]["network_used"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-84")
