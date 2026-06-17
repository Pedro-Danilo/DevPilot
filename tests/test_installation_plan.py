from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from devpilot_core.release import InstallPlanBuilder, InstallPlanOptions

ROOT = Path(__file__).resolve().parents[1]


def test_install_plan_all_mode_is_dry_run_and_safe() -> None:
    result = InstallPlanBuilder(ROOT, options=InstallPlanOptions(mode="all", version="0.1.0")).build()

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["mode"] == "all"
    assert summary["dry_run_default"] is True
    assert summary["execute_supported"] is False
    assert summary["network_required"] is False
    assert summary["admin_privileges_required"] is False
    assert summary["auto_update_enabled"] is False
    assert summary["persistent_services_installed"] is False
    assert summary["desktop_bridge_documented"] is True

    plan = result.data["install_plan"]
    modes = {item["mode"] for item in plan["decision_matrix"]}
    assert {"editable", "wheel", "zip", "desktop-bridge"}.issubset(modes)


def test_install_plan_wheel_mode_uses_local_artifact_path() -> None:
    result = InstallPlanBuilder(ROOT, options=InstallPlanOptions(mode="wheel", version="0.1.0")).build()

    assert result.ok is True
    artifact = result.data["summary"]
    assert artifact["artifact_mode"] is True
    assert artifact["artifact_expected"] is True
    assert result.data["install_plan"]["artifact"]["path"] == "dist/devpilot_local-0.1.0-py3-none-any.whl"


def test_install_plan_rejects_invalid_semver() -> None:
    result = InstallPlanBuilder(ROOT, options=InstallPlanOptions(mode="all", version="version-one")).build()

    assert result.ok is False
    assert result.exit_code.value == 3
    assert result.findings[0].id == "INSTALL_VERSION_INVALID"


def test_install_plan_rejects_artifact_outside_workspace() -> None:
    result = InstallPlanBuilder(
        ROOT,
        options=InstallPlanOptions(mode="wheel", version="0.1.0", artifact="../outside.whl"),
    ).build()

    assert result.ok is False
    assert result.findings[0].id == "INSTALL_ARTIFACT_OUTSIDE_WORKSPACE"


def test_install_plan_rejects_artifact_kind_mismatch() -> None:
    result = InstallPlanBuilder(
        ROOT,
        options=InstallPlanOptions(mode="wheel", version="0.1.0", artifact="dist/release/devpilot-local-0.1.0-source.zip"),
    ).build()

    assert result.ok is False
    assert result.findings[0].id == "INSTALL_ARTIFACT_KIND_MISMATCH"


def test_install_plan_cli_json_and_write_report() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "install",
            "plan",
            "--mode",
            "all",
            "--version",
            "0.1.0",
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
    assert payload["ok"] is True
    assert payload["data"]["summary"]["reports_written"] is True
    assert (ROOT / "outputs/reports/install_plan.json").exists()
    assert (ROOT / "outputs/reports/install_plan.md").exists()
