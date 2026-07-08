from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.release import PackageBuildBuilder, PackageBuildOptions, WindowsInstallSmokeOptions, WindowsInstallSmokeRunner
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _clean_runtime() -> None:
    for rel in ("dist", "outputs/reports", "outputs/release"):
        path = ROOT / rel
        if path.exists():
            shutil.rmtree(path)


def _build_all_artifacts() -> None:
    result = PackageBuildBuilder(ROOT, options=PackageBuildOptions(version="0.1.0", kind="all", execute=True)).build()
    assert result.ok, result.to_dict()


def test_windows_install_smoke_editable_passes_and_writes_schema_valid_report() -> None:
    _clean_runtime()

    result = WindowsInstallSmokeRunner(
        ROOT,
        WindowsInstallSmokeOptions(mode="editable", version="0.1.0", write_report=True),
    ).run()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["decision"] == "PASS"
    assert result.data["summary"]["guide_has_editable_flow"] is True
    assert result.data["summary"]["guide_has_wheel_flow"] is True
    assert result.data["summary"]["guide_has_zip_flow"] is True
    assert result.data["summary"]["network_used"] is False
    assert result.data["summary"]["admin_required"] is False
    assert result.data["reports"] == {
        "json": "outputs/reports/windows_install_smoke_report.json",
        "markdown": "outputs/reports/windows_install_smoke_report.md",
    }

    validation = SchemaValidator(ROOT).validate(
        schema="WindowsInstallSmokeReport",
        instance=Path("outputs/reports/windows_install_smoke_report.json"),
    )
    assert validation.ok is True, validation.to_dict()


def test_windows_install_smoke_wheel_passes_with_local_artifact() -> None:
    _clean_runtime()
    _build_all_artifacts()

    result = WindowsInstallSmokeRunner(
        ROOT,
        WindowsInstallSmokeOptions(
            mode="wheel",
            version="0.1.0",
            artifact="dist\\devpilot_local-0.1.0-py3-none-any.whl",
            output_json="outputs\\reports\\windows_install_smoke_report.json",
            output_markdown="outputs\\reports\\windows_install_smoke_report.md",
            write_report=True,
        ),
    ).run()

    assert result.ok, result.to_dict()
    assert result.data["summary"]["artifact_required"] is True
    assert result.data["summary"]["artifact_exists"] is True
    assert result.data["report"]["artifact"]["provided"] == "dist/devpilot_local-0.1.0-py3-none-any.whl"
    assert result.data["reports"]["json"] == "outputs/reports/windows_install_smoke_report.json"


def test_windows_install_smoke_zip_passes_with_local_source_zip() -> None:
    _clean_runtime()
    _build_all_artifacts()

    result = WindowsInstallSmokeRunner(
        ROOT,
        WindowsInstallSmokeOptions(
            mode="zip",
            version="0.1.0",
            artifact="dist/release/devpilot-local-0.1.0-source.zip",
        ),
    ).run()

    assert result.ok, result.to_dict()
    assert result.data["report"]["artifact"]["kind"] == "zip"
    assert result.data["report"]["artifact"]["exists"] is True
    assert result.data["summary"]["source_mutations"] is False


def test_windows_install_smoke_blocks_missing_required_wheel() -> None:
    _clean_runtime()

    result = WindowsInstallSmokeRunner(
        ROOT,
        WindowsInstallSmokeOptions(mode="wheel", version="0.1.0", artifact="dist/missing.whl"),
    ).run()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["artifact_required"] is True
    assert result.data["summary"]["artifact_exists"] is False
    assert any(finding.id == "WINDOWS_INSTALL_ARTIFACT_MISSING" for finding in result.findings)


def test_windows_install_smoke_blocks_artifact_outside_workspace() -> None:
    result = WindowsInstallSmokeRunner(
        ROOT,
        WindowsInstallSmokeOptions(mode="wheel", artifact="../outside.whl"),
    ).run()

    assert result.ok is False
    assert any(finding.id == "WINDOWS_INSTALL_ARTIFACT_OUTSIDE_WORKSPACE" for finding in result.findings)


def test_windows_install_smoke_cli_json(monkeypatch, capsys) -> None:
    _clean_runtime()
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["install", "windows-smoke", "--mode", "editable", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "install windows-smoke"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["decision"] == "PASS"
    assert payload["data"]["reports"]["json"] == "outputs/reports/windows_install_smoke_report.json"


def test_windows_install_smoke_docs_and_registries_are_synchronized() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    install_guide = (ROOT / "docs/05_operations/install_guide.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-027_packaging_reproducible_local_installation.md").read_text(encoding="utf-8")
    project_state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    schema_catalog = (ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")

    assert "POST-H-027-D — Windows install guide and smoke" in readme
    assert "POST-H-027-D — Windows install guide and smoke" in runbook
    assert "python -m devpilot_core install windows-smoke --mode editable --json --write-report" in install_guide
    assert "127.0.0.1" in install_guide
    assert "npm --prefix ui/web test" in install_guide
    assert "Upgrade/rollback dry-run" in backlog
    assert project_state["current_micro_sprint"] == "POST-H-027-D"
    assert project_state["next_micro_sprint"] == "POST-H-027-E"
    assert project_state["post_h_027_windows_install_smoke_available"] is True
    assert "SCHEMA-DEVPL-WINDOWS-INSTALL-SMOKE-REPORT-V1" in schema_catalog
    assert "post-h-027-windows-install-smoke" in tcr_v2
