from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.release import (
    PackageBuildBuilder,
    PackageBuildOptions,
    PythonArtifactInstallVerificationOptions,
    PythonArtifactInstallVerifier,
)
from devpilot_core.schemas.validator import SchemaValidator
from devpilot_core.testing import TestContractRegistryV2Validator
from devpilot_core.testing.impact_v2 import TestImpactAnalyzerV2, TestImpactV2Options

ROOT = Path(__file__).resolve().parents[1]


def _clean_runtime() -> None:
    shutil.rmtree(ROOT / "dist", ignore_errors=True)
    shutil.rmtree(ROOT / "outputs" / "release", ignore_errors=True)
    shutil.rmtree(ROOT / "outputs" / "tmp" / "python-artifact-install", ignore_errors=True)


def _build_python_artifacts() -> tuple[Path, Path]:
    build = PackageBuildBuilder(ROOT, options=PackageBuildOptions(version="0.1.0", kind="python", execute=True)).build()
    assert build.ok, build.to_dict()
    wheel = ROOT / "dist/devpilot_local-0.1.0-py3-none-any.whl"
    sdist = ROOT / "dist/devpilot-local-0.1.0.tar.gz"
    assert wheel.exists()
    assert sdist.exists()
    return wheel, sdist


@pytest.fixture(scope="module")
def wheel_install_result():
    _clean_runtime()
    wheel, _ = _build_python_artifacts()
    result = PythonArtifactInstallVerifier(
        ROOT,
        PythonArtifactInstallVerificationOptions(artifact=str(wheel.relative_to(ROOT)), timeout_seconds=120),
    ).run()
    assert result.ok, result.to_dict()
    return result


def test_wheel_install_verification_passes_without_source_path_dependency(wheel_install_result) -> None:
    result = wheel_install_result
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["decision"] == "PASS"
    assert summary["artifact_kind"] == "wheel"
    assert summary["artifact_installed"] is True
    assert summary["cli_version_passed"] is True
    assert summary["schema_list_passed"] is True
    assert summary["project_state_validate_passed"] is True
    assert summary["docs_governance_validate_passed"] is True
    assert summary["import_from_installed_site_packages"] is True
    assert summary["source_path_dependency_detected"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["source_mutations"] is False
    assert result.data["report"]["safety"]["pip_no_index"] is True
    assert result.data["report"]["temp_cleaned"] is True


def test_sdist_install_verification_uses_local_build_backend_bridge() -> None:
    _, sdist = _build_python_artifacts()
    verifier = PythonArtifactInstallVerifier(
        ROOT,
        PythonArtifactInstallVerificationOptions(artifact=str(sdist.relative_to(ROOT)), timeout_seconds=120),
    )

    cmd = verifier._pip_install_command(Path(".venv/bin/python"), sdist, "sdist")

    assert "--no-index" in cmd
    assert "--no-deps" in cmd
    assert "--no-build-isolation" in cmd
    assert str(sdist) in cmd

    bridge = {"paths": verifier._dependency_bridge_paths()}
    env = verifier._env_with_dependency_bridge({}, bridge)

    assert env.get("PYTHONPATH")
    assert str((ROOT / "src").resolve()) not in env["PYTHONPATH"]


def test_dependency_bridge_keeps_operator_venv_dependencies_without_source_tree(monkeypatch, tmp_path: Path) -> None:
    workspace = tmp_path / "repo"
    host_site = workspace / ".venv" / "Lib" / "site-packages"
    host_site.mkdir(parents=True)
    (host_site / "jsonschema").mkdir()
    (host_site / "jsonschema" / "__init__.py").write_text("", encoding="utf-8")

    workspace_src = workspace / "src"
    workspace_src.mkdir(parents=True)

    monkeypatch.setattr("devpilot_core.release.python_artifact_verify.site.getsitepackages", lambda: [str(host_site), str(workspace_src)])
    monkeypatch.setattr("devpilot_core.release.python_artifact_verify.site.getusersitepackages", lambda: str(tmp_path / "missing-user-site"))

    verifier = PythonArtifactInstallVerifier(workspace, PythonArtifactInstallVerificationOptions(artifact="dist/missing.whl"))

    assert verifier._dependency_bridge_paths() == [str(host_site.resolve())]


def test_python_artifact_install_report_validates_against_schema(wheel_install_result) -> None:
    report = wheel_install_result.data["report"]
    validation = SchemaValidator(ROOT).validate_payload(
        schema="PythonArtifactInstallVerification",
        payload=report,
        instance_label="memory:python-artifact-install-verification",
    )
    assert validation.ok, validation.to_dict()
    assert report["summary"]["reports_written"] is False


def test_python_artifact_verify_cli_json_is_available(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main([
        "release",
        "python-artifact-verify",
        "--artifact",
        "dist/does-not-exist.whl",
        "--json",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["command"] == "release python-artifact-verify"
    assert payload["ok"] is False
    assert payload["data"]["summary"]["decision"] == "BLOCK"


def test_python_artifact_verify_blocks_missing_or_unsupported_artifacts(tmp_path: Path) -> None:
    missing = PythonArtifactInstallVerifier(
        ROOT,
        PythonArtifactInstallVerificationOptions(artifact="dist/does-not-exist.whl"),
    ).run()
    assert not missing.ok
    assert missing.exit_code == ExitCode.BLOCK
    assert any(finding.id == "PYTHON_ARTIFACT_MISSING_BLOCK" for finding in missing.findings)

    unsupported = tmp_path / "artifact.zip"
    unsupported.write_text("not a python artifact", encoding="utf-8")
    outside = PythonArtifactInstallVerifier(ROOT, PythonArtifactInstallVerificationOptions(artifact=str(unsupported))).run()
    assert not outside.ok
    assert any(finding.id in {"PYTHON_ARTIFACT_OUTSIDE_WORKSPACE_BLOCK", "PYTHON_ARTIFACT_UNSUPPORTED_KIND_BLOCK"} for finding in outside.findings)


def test_post_h_027_b_contracts_and_impact_are_registered() -> None:
    release = TestContractRegistryV2Validator(ROOT).profile("release")
    assert release.ok, release.to_dict()
    assert "post-h-027-python-artifact-install-verification" in {item["contract_id"] for item in release.data["contracts"]}

    impact = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("src/devpilot_core/release/python_artifact_verify.py",))).analyze()
    assert impact.ok, impact.to_dict()
    assert "release" in impact.data["summary"]["recommended_profiles"]
    assert any("python-artifact-verify" in command for command in impact.data["recommended_commands"])


def test_post_h_027_b_documentation_is_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-027_packaging_reproducible_local_installation.md").read_text(encoding="utf-8")
    top_level = (ROOT / "docs/POST-H-027_packaging_reproducible_local_installation.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "docs/post_h_027_b_manifest.json").read_text(encoding="utf-8"))

    assert 'current_micro_sprint: "POST-H-027-E"' in backlog
    assert 'next_micro_sprint: "POST-H-028"' in backlog
    assert "POST-H-027-B — Wheel/sdist install verification" in backlog
    assert "POST-H-027-B — Wheel/sdist install verification" in top_level
    assert "python-artifact-verify" in readme
    assert "python-artifact-verify" in runbook
    assert "post-h-027-b" in changelog
    assert manifest["post_h_id"] == "POST-H-027"
    assert manifest["status"] == "implemented-initial"
    assert "tests/test_post_h_027_python_artifact_install_verification.py" in manifest["tests"]
