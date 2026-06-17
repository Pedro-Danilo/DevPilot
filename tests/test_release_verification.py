from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.release import (
    ReleaseChecksumBuilder,
    ReleaseChecksumOptions,
    ReleaseSmokeTestBuilder,
    ReleaseSmokeTestOptions,
    ReleaseVerifyBuilder,
    ReleaseVerifyOptions,
)

ROOT = Path(__file__).resolve().parents[1]


def _make_source_zip(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for rel in [
            "pyproject.toml",
            "README.md",
            "src/devpilot_core/__init__.py",
            "src/devpilot_core/__main__.py",
        ]:
            archive.write(ROOT / rel, rel)
    return path


def test_release_checksum_builder_requires_real_local_artifact(tmp_path: Path) -> None:
    artifact = _make_source_zip(ROOT / "dist" / "release" / "test-devpilot-release.zip")

    result = ReleaseChecksumBuilder(ROOT, options=ReleaseChecksumOptions(artifact=str(artifact.relative_to(ROOT)))).build()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["artifact_exists"] is True
    assert summary["sha256_generated"] is True
    assert len(summary["sha256"]) == 64
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False


def test_release_checksum_blocks_missing_artifact() -> None:
    result = ReleaseChecksumBuilder(ROOT, options=ReleaseChecksumOptions(artifact="dist/release/missing.zip")).build()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.findings[0].id == "RELEASE_ARTIFACT_MISSING"


def test_release_smoke_test_checks_container_and_exit_codes() -> None:
    artifact = _make_source_zip(ROOT / "dist" / "release" / "test-devpilot-release.zip")

    result = ReleaseSmokeTestBuilder(ROOT, options=ReleaseSmokeTestOptions(artifact=str(artifact.relative_to(ROOT)))).build()

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["checks_total"] == 2
    assert summary["checks_failed"] == 0
    assert summary["container_check_passed"] is True
    assert summary["cli_version_check_passed"] is True
    assert summary["exit_codes_observed"] is True
    checks = result.data["smoke_test"]["checks"]
    assert {check["id"] for check in checks} == {"artifact-container", "cli-version"}
    assert all("exit_code" in check for check in checks)


def test_release_verify_builder_consolidates_checksum_and_smoke() -> None:
    artifact = _make_source_zip(ROOT / "dist" / "release" / "test-devpilot-release.zip")

    result = ReleaseVerifyBuilder(ROOT, options=ReleaseVerifyOptions(artifact=str(artifact.relative_to(ROOT)))).build()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["release_verified"] is True
    assert summary["sha256_generated"] is True
    assert summary["smoke_test_passed"] is True
    assert summary["subchecks_total"] == 2
    assert summary["subchecks_failed"] == 0
    assert summary["network_used"] is False
    verification = result.data["release_verification"]
    assert verification["subresults"]["checksum_ok"] is True
    assert verification["subresults"]["smoke_test_ok"] is True


def test_release_verify_cli_json_write_report_and_checksum_file_are_parseable() -> None:
    artifact = _make_source_zip(ROOT / "dist" / "release" / "test-devpilot-release.zip")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "release",
            "verify",
            "--artifact",
            str(artifact.relative_to(ROOT)),
            "--json",
            "--write-report",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["command"] == "release verify"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is True
    assert payload["data"]["summary"]["release_verified"] is True
    reports = payload["data"].get("reports")
    assert reports["json"] == "outputs/reports/release_verification.json"
    assert reports["markdown"] == "outputs/reports/release_verification.md"
    assert reports["sha256"] == "outputs/reports/checksums.sha256"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()
    checksum_text = (ROOT / reports["sha256"]).read_text(encoding="utf-8")
    assert str(artifact.relative_to(ROOT)).replace("\\", "/") in checksum_text
    assert len(checksum_text.split()[0]) == 64


def test_release_checksum_cli_supports_explicit_report() -> None:
    artifact = _make_source_zip(ROOT / "dist" / "release" / "test-devpilot-release.zip")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "release",
            "checksum",
            "--artifact",
            str(artifact.relative_to(ROOT)),
            "--json",
            "--write-report",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["command"] == "release checksum"
    assert payload["data"]["summary"]["sha256_generated"] is True
    assert payload["data"]["reports"]["sha256"] == "outputs/reports/checksums.sha256"


def test_release_smoke_test_cli_rejects_unsupported_artifact(tmp_path: Path) -> None:
    artifact = ROOT / "dist" / "release" / "unsupported.txt"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("not a release package", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "release",
            "smoke-test",
            "--artifact",
            str(artifact.relative_to(ROOT)),
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == int(ExitCode.FAIL)
    payload = json.loads(completed.stdout)
    assert payload["command"] == "release smoke-test"
    assert payload["ok"] is False
    assert payload["data"]["summary"]["checks_failed"] == 1
