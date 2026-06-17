from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.release import ReleaseSbomBuilder, ReleaseSbomOptions

ROOT = Path(__file__).resolve().parents[1]


def test_release_sbom_builder_declares_runtime_dev_build_and_node_dependencies() -> None:
    result = ReleaseSbomBuilder(ROOT, options=ReleaseSbomOptions()).build()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    sbom = result.data["sbom"]
    assert summary["python_runtime_dependencies_total"] >= 1
    assert summary["python_dev_dependencies_total"] >= 1
    assert summary["python_build_dependencies_total"] >= 1
    assert summary["node_direct_dependencies_total"] >= 1
    assert summary["node_locked_components_total"] >= 1
    assert summary["cyclonedx_compatible"] is True
    assert sbom["cyclonedx"]["bomFormat"] == "CycloneDX"
    assert sbom["cyclonedx"]["specVersion"] == "1.5"
    assert sbom["security"]["network_used"] is False
    assert sbom["security"]["external_api_used"] is False
    assert sbom["security"]["vulnerability_scan_performed"] is False
    assert sbom["security"]["license_scan_performed"] is False


def test_release_sbom_mentions_declared_package_names() -> None:
    result = ReleaseSbomBuilder(ROOT, options=ReleaseSbomOptions()).build()
    names = {item["name"] for item in result.data["sbom"]["components"]}

    assert "jsonschema" in names
    assert "pytest" in names
    assert "setuptools" in names
    assert "typescript" in names
    assert "vite" in names


def test_release_sbom_cli_json_and_report_are_parseable() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "release", "sbom", "--json", "--write-report"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["command"] == "release sbom"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is True
    assert payload["data"]["sbom"]["release_version"] == "0.1.0"
    reports = payload["data"].get("reports")
    assert reports["json"] == "outputs/reports/release_sbom.json"
    assert reports["markdown"] == "outputs/reports/release_sbom.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()


def test_release_sbom_cli_accepts_explicit_version_override() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "release", "sbom", "--version", "0.1.1", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["data"]["summary"]["version"] == "0.1.1"
    assert payload["data"]["sbom"]["release_id"] == "DEVPL-0.1.1"
