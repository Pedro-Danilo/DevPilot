from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from devpilot_core.release import (
    BackupCreateBuilder,
    BackupCreateOptions,
    BackupListBuilder,
    BackupListOptions,
    BackupRestoreBuilder,
    BackupRestoreOptions,
    UpgradeCheckBuilder,
    UpgradeCheckOptions,
)

ROOT = Path(__file__).resolve().parents[1]


def _minimal_workspace(root: Path) -> None:
    (root / "docs/05_operations").mkdir(parents=True)
    (root / "docs/05_operations/install_guide.md").write_text("# install\n", encoding="utf-8")
    (root / "docs/05_operations/release_verification.md").write_text("# release verify\n", encoding="utf-8")
    (root / "docs/05_operations/backup_restore_upgrade.md").write_text("# backup\n", encoding="utf-8")
    (root / "pyproject.toml").write_text('[project]\nname = "devpilot-local"\nversion = "0.1.0"\n', encoding="utf-8")
    (root / ".devpilot/miasi").mkdir(parents=True)
    (root / ".devpilot/execution").mkdir(parents=True)
    (root / ".devpilot/testing").mkdir(parents=True)
    (root / ".devpilot/project.yaml").write_text("project_id: devpilot\n", encoding="utf-8")
    (root / ".devpilot/policy.yaml").write_text("mode: local\n", encoding="utf-8")
    (root / ".devpilot/providers.yaml").write_text("api_key: sk-test-secret-token-123456\n", encoding="utf-8")
    (root / ".devpilot/providers.yaml.example").write_text("providers: []\n", encoding="utf-8")
    (root / ".devpilot/devpilot.db").write_bytes(b"sqlite-placeholder")
    (root / ".devpilot/miasi/agent_registry.json").write_text("{}\n", encoding="utf-8")
    (root / ".devpilot/miasi/tool_registry.json").write_text("{}\n", encoding="utf-8")
    (root / ".devpilot/miasi/policy_matrix.json").write_text("{}\n", encoding="utf-8")
    (root / ".devpilot/execution/command_allowlist.json").write_text("[]\n", encoding="utf-8")
    (root / ".devpilot/testing/test_profiles.json").write_text("{}\n", encoding="utf-8")


def test_backup_create_dry_run_is_safe(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)

    result = BackupCreateBuilder(tmp_path, options=BackupCreateOptions(dry_run=True, execute=False)).build()

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["dry_run"] is True
    assert summary["backup_created"] is False
    assert summary["outputs_excluded_by_default"] is True
    assert summary["venv_excluded_by_default"] is True
    assert summary["git_dir_excluded_by_default"] is True
    assert summary["redactions_total"] >= 1
    assert not (tmp_path / ".devpilot/backups").exists()


def test_backup_create_execute_writes_zip_and_redacts_secrets(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)

    result = BackupCreateBuilder(tmp_path, options=BackupCreateOptions(dry_run=False, execute=True)).build()

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["backup_created"] is True
    zip_path = tmp_path / summary["backup_zip"]
    manifest_path = tmp_path / summary["backup_manifest"]
    assert zip_path.exists()
    assert manifest_path.exists()
    assert summary["redactions_total"] >= 1
    assert ".git" not in zip_path.read_bytes().decode("latin1", errors="ignore")


def test_backup_list_and_restore_dry_run(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    created = BackupCreateBuilder(tmp_path, options=BackupCreateOptions(dry_run=False, execute=True)).build()
    backup_id = created.data["summary"]["backup_id"]

    listed = BackupListBuilder(tmp_path, options=BackupListOptions(limit=10)).build()
    assert listed.ok is True
    assert listed.data["summary"]["backups_total"] == 1
    assert listed.data["backups"][0]["backup_id"] == backup_id

    restored = BackupRestoreBuilder(
        tmp_path,
        options=BackupRestoreOptions(backup_id=backup_id, dry_run=True, execute=False),
    ).build()
    assert restored.ok is True
    assert restored.data["summary"]["dry_run"] is True
    assert restored.data["summary"]["restore_performed"] is False
    assert restored.data["summary"]["restore_overwrites_require_confirmation"] is True


def test_backup_restore_execute_requires_confirmation(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    created = BackupCreateBuilder(tmp_path, options=BackupCreateOptions(dry_run=False, execute=True)).build()
    backup_id = created.data["summary"]["backup_id"]

    blocked = BackupRestoreBuilder(
        tmp_path,
        options=BackupRestoreOptions(backup_id=backup_id, dry_run=False, execute=True, confirm_restore=False),
    ).build()

    assert blocked.ok is False
    assert blocked.exit_code.value == 2
    assert any(finding.id == "BACKUP_RESTORE_CONFIRMATION_REQUIRED" for finding in blocked.findings)


def test_upgrade_check_generates_plan(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    BackupCreateBuilder(tmp_path, options=BackupCreateOptions(dry_run=False, execute=True)).build()

    result = UpgradeCheckBuilder(tmp_path, options=UpgradeCheckOptions()).build()

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["dry_run_default"] is True
    assert summary["mutations_performed"] is False
    assert summary["network_used"] is False
    assert summary["latest_backup_manifest"] is not None
    assert any("backup create" in step["command"] for step in result.data["upgrade_plan"]["steps"])


def test_backup_and_upgrade_cli_json_dry_run() -> None:
    backup = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "backup", "create", "--dry-run", "--json", "--write-report"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert backup.returncode == 0, backup.stderr + backup.stdout
    backup_payload = json.loads(backup.stdout)
    assert backup_payload["ok"] is True
    assert backup_payload["data"]["summary"]["dry_run"] is True
    assert backup_payload["data"]["summary"]["reports_written"] is True

    upgrade = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "upgrade", "check", "--json", "--write-report"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert upgrade.returncode == 0, upgrade.stderr + upgrade.stdout
    upgrade_payload = json.loads(upgrade.stdout)
    assert upgrade_payload["ok"] is True
    assert upgrade_payload["data"]["summary"]["dry_run_default"] is True
    assert upgrade_payload["data"]["summary"]["reports_written"] is True
