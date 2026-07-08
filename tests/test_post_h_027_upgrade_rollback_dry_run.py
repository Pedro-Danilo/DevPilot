from __future__ import annotations

import json
import zipfile
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.release import BackupCreateBuilder, BackupCreateOptions, PackagingLocalReadyGate, UpgradeRollbackDryRunOptions, UpgradeRollbackDryRunRunner
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _minimal_workspace(root: Path, *, checksums_verified: bool = True) -> None:
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
    (root / ".devpilot/providers.yaml").write_text("providers: []\n", encoding="utf-8")
    (root / ".devpilot/providers.yaml.example").write_text("providers: []\n", encoding="utf-8")
    (root / ".devpilot/devpilot.db").write_bytes(b"sqlite-placeholder")
    (root / ".devpilot/miasi/agent_registry.json").write_text("{}\n", encoding="utf-8")
    (root / ".devpilot/miasi/tool_registry.json").write_text("{}\n", encoding="utf-8")
    (root / ".devpilot/miasi/policy_matrix.json").write_text("{}\n", encoding="utf-8")
    (root / ".devpilot/execution/command_allowlist.json").write_text("[]\n", encoding="utf-8")
    (root / ".devpilot/testing/test_profiles.json").write_text("{}\n", encoding="utf-8")
    _write_artifact_manifest(root, checksums_verified=checksums_verified)


def _write_artifact_manifest(root: Path, *, checksums_verified: bool) -> None:
    outputs = root / "outputs/release"
    outputs.mkdir(parents=True, exist_ok=True)
    checksums_file = outputs / "checksums.sha256"
    checksums_file.write_text("0" * 64 + "  dist/release/devpilot-local-0.1.0-source.zip\n", encoding="utf-8")
    manifest = {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-RELEASE-ARTIFACT-MANIFEST-V1",
        "manifest_id": "DEVPL-LOCAL-ARTIFACT-MANIFEST-0.1.0",
        "created_by": "POST-H-027-C",
        "status": "implemented-initial",
        "generated_at_utc": "2026-07-08T00:00:00Z",
        "release_version": "0.1.0",
        "scope": "local-package",
        "policy": {
            "policy_id": "local-artifact-manifest-policy-v1",
            "policy_path": ".devpilot/release/local_artifact_manifest_policy.json",
            "status": "implemented-initial",
            "required_artifacts_total": 1,
            "optional_artifacts_total": 0,
        },
        "artifacts": [
            {
                "artifact_id": "source-zip",
                "artifact_type": "source_zip",
                "path": "dist/release/devpilot-local-0.1.0-source.zip",
                "required": True,
                "classification": "distributable",
                "exists": True,
                "sha256": "0" * 64,
                "size_bytes": 1,
                "verification_status": "pass",
                "source": "test-fixture",
                "notes": [],
            }
        ],
        "checksums_file": "outputs/release/checksums.sha256",
        "checksums": {
            "algorithm": "sha256",
            "generated": True,
            "verified": checksums_verified,
            "entries_total": 1,
            "entries_sha256": "1" * 64,
            "mismatches": [],
        },
        "summary": {
            "decision": "PASS",
            "created_by": "POST-H-027-C",
            "preliminary": True,
            "release_version": "0.1.0",
            "scope": "local-package",
            "required_missing_total": 0,
            "checksum_mismatch_total": 0,
            "checksums_verified": checksums_verified,
            "network_used": False,
            "external_api_used": False,
            "publish_performed": False,
            "deploy_performed": False,
            "signing_performed": False,
            "source_mutations": False,
            "reports_written": True,
        },
        "safety": {
            "local_first": True,
            "network_used": False,
            "external_api_used": False,
            "publish_performed": False,
            "deploy_performed": False,
            "git_tagging_performed": False,
            "signing_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "source_mutations": False,
            "reports_written": True,
        },
        "limitations": ["fixture"],
        "preliminary": True,
    }
    (outputs / "release_artifact_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _create_backup(root: Path) -> str:
    result = BackupCreateBuilder(root, options=BackupCreateOptions(dry_run=False, execute=True)).build()
    assert result.ok, result.to_dict()
    return result.data["summary"]["backup_id"]


def test_upgrade_rollback_dry_run_passes_and_writes_schema_valid_report(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    backup_id = _create_backup(tmp_path)

    result = UpgradeRollbackDryRunRunner(
        tmp_path,
        UpgradeRollbackDryRunOptions(from_version="0.1.0", to_version="0.1.1", backup_id=backup_id, write_report=True),
    ).run()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["decision"] == "PASS"
    assert result.data["summary"]["backup_plan_available"] is True
    assert result.data["summary"]["checksums_verified"] is True
    assert result.data["summary"]["restore_dry_run_safe"] is True
    assert result.data["summary"]["restore_performed"] is False
    assert result.data["summary"]["auto_update_enabled"] is False
    assert result.data["reports"] == {
        "json": "outputs/reports/upgrade_rollback_dry_run_report.json",
        "markdown": "outputs/reports/upgrade_rollback_dry_run_report.md",
    }

    validation = SchemaValidator(ROOT).validate_payload(
        schema="UpgradeRollbackDryRunReport",
        payload=result.data["report"],
        instance_label="outputs/reports/upgrade_rollback_dry_run_report.json",
    )
    assert validation.ok is True, validation.to_dict()


def test_upgrade_rollback_dry_run_blocks_without_backup_plan(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)

    result = UpgradeRollbackDryRunRunner(tmp_path, UpgradeRollbackDryRunOptions(from_version="0.1.0", to_version="0.1.1")).run()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["backup_plan_available"] is False
    assert any(finding.id == "UPGRADE_ROLLBACK_BACKUP_PLAN_MISSING" for finding in result.findings)


def test_upgrade_rollback_dry_run_blocks_unverified_checksums(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path, checksums_verified=False)
    backup_id = _create_backup(tmp_path)

    result = UpgradeRollbackDryRunRunner(
        tmp_path,
        UpgradeRollbackDryRunOptions(from_version="0.1.0", to_version="0.1.1", backup_id=backup_id),
    ).run()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["checksums_verified"] is False
    assert any(finding.id == "UPGRADE_ROLLBACK_CHECKSUMS_NOT_VERIFIED" for finding in result.findings)


def test_upgrade_rollback_dry_run_blocks_unsafe_restore_entry(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    backup_id = _create_backup(tmp_path)
    zip_path = tmp_path / ".devpilot" / "backups" / f"{backup_id}.zip"
    manifest_path = tmp_path / ".devpilot" / "backups" / f"{backup_id}.manifest.json"

    with zipfile.ZipFile(zip_path, "a") as zf:
        zf.writestr("../escape.txt", "unsafe")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    import hashlib
    manifest["artifact"]["zip_sha256"] = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    result = UpgradeRollbackDryRunRunner(
        tmp_path,
        UpgradeRollbackDryRunOptions(from_version="0.1.0", to_version="0.1.1", backup_id=backup_id),
    ).run()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["restore_dry_run_safe"] is False
    assert result.data["summary"]["restore_blocked_entries_total"] == 1
    assert any(finding.id == "UPGRADE_ROLLBACK_RESTORE_DRY_RUN_UNSAFE" for finding in result.findings)


def test_upgrade_rollback_dry_run_cli_json(monkeypatch, capsys, tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    backup_id = _create_backup(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main([
        "release",
        "upgrade-rollback-dry-run",
        "--from-version",
        "0.1.0",
        "--to-version",
        "0.1.1",
        "--backup-id",
        backup_id,
        "--json",
        "--write-report",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "release upgrade-rollback-dry-run"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["decision"] == "PASS"
    assert payload["data"]["reports"]["json"] == "outputs/reports/upgrade_rollback_dry_run_report.json"


def test_packaging_local_ready_gate_uses_upgrade_rollback_dry_run(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    _create_backup(tmp_path)

    result = PackagingLocalReadyGate(tmp_path).run()

    assert result.ok is True, result.to_dict()
    assert result.data["summary"]["quality_gate_subgate"] == "packaging-local-ready"
    assert result.data["summary"]["packaging_local_ready"] is True
    assert result.data["summary"]["remote_execution_enabled"] is False


def test_post_h_027_e_documentation_and_registries_are_synchronized() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backup_runbook = (ROOT / "docs/05_operations/backup_restore_upgrade.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-027_packaging_reproducible_local_installation.md").read_text(encoding="utf-8")
    project_state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    schema_catalog = (ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")

    assert "POST-H-027-E — Upgrade/rollback dry-run" in readme
    assert "POST-H-027-E — Upgrade/rollback dry-run" in runbook
    assert "python -m devpilot_core release upgrade-rollback-dry-run --from-version 0.1.0 --to-version 0.1.1 --json --write-report" in backup_runbook
    assert "Estado: `closed / packaging-local-ready`" in backlog
    assert project_state["current_micro_sprint"] == "POST-H-027-E"
    assert project_state["post_h_027_upgrade_rollback_dry_run_available"] is True
    assert project_state["post_h_027_packaging_local_ready_quality_gate_enabled"] is True
    assert "SCHEMA-DEVPL-UPGRADE-ROLLBACK-DRY-RUN-REPORT-V1" in schema_catalog
    assert "post-h-027-upgrade-rollback-dry-run" in tcr_v2
