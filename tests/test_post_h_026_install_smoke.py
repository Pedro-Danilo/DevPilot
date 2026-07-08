from __future__ import annotations

import json
import zipfile
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.release_candidate import LocalInstallSmokeOptions, LocalInstallSmokeRunner
from devpilot_core.schemas.validator import SchemaValidator
from devpilot_core.testing import TestContractRegistryV2Validator
from devpilot_core.testing.impact_v2 import TestImpactAnalyzerV2, TestImpactV2Options

ROOT = Path(__file__).resolve().parents[1]


def test_local_install_smoke_passes_without_installers_network_or_mutations() -> None:
    result = LocalInstallSmokeRunner(ROOT).run()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["decision"] == "PASS"
    assert summary["python_package_importable"] is True
    assert summary["editable_install_documented"] is True
    assert summary["operator_checklist_documented"] is True
    assert summary["frontend_smoke_documented"] is True
    assert summary["clean_package_policy_passed"] is True
    assert summary["commands_executed"] is False
    safety = result.data["report"]["safety"]
    assert safety["subprocess_executed"] is False
    assert safety["pip_executed"] is False
    assert safety["npm_executed"] is False
    assert safety["socket_opened"] is False
    assert safety["network_used"] is False
    assert safety["external_api_used"] is False
    assert safety["remote_execution_enabled"] is False
    assert safety["connector_write_enabled"] is False
    assert safety["plugin_execution_enabled"] is False
    assert any(finding.id == "LOCAL_INSTALL_SMOKE_PASS" for finding in result.findings)


def test_local_install_smoke_blocks_candidate_zip_with_runtime_artifacts(tmp_path: Path) -> None:
    candidate = tmp_path / "bad_candidate.zip"
    with zipfile.ZipFile(candidate, "w") as archive:
        archive.writestr("README.md", "ok")
        archive.writestr("outputs/traces/events.jsonl", "{}\n")
        archive.writestr("ui/web/node_modules/pkg/index.js", "bad")

    result = LocalInstallSmokeRunner(ROOT, LocalInstallSmokeOptions(candidate_zip=str(candidate))).run()

    assert not result.ok
    assert result.exit_code == ExitCode.BLOCK
    finding_ids = {finding.id for finding in result.findings}
    assert "LOCAL_INSTALL_CANDIDATE_ZIP_RUNTIME_ARTIFACTS_BLOCK" in finding_ids
    check = next(item for item in result.data["report"]["checks"] if item["check_id"] == "candidate-zip-hygiene")
    assert check["status"] == "block"
    assert check["metadata"]["violations_total"] == 2


def test_local_install_smoke_write_report_validates_schema() -> None:
    output_json = ROOT / "outputs/test_fixtures/post_h_026_d/local_install_smoke_report.json"
    output_markdown = ROOT / "outputs/test_fixtures/post_h_026_d/local_install_smoke_report.md"
    result = LocalInstallSmokeRunner(
        ROOT,
        LocalInstallSmokeOptions(
            output_json=str(output_json),
            output_markdown=str(output_markdown),
            write_report=True,
        ),
    ).run()

    assert result.ok, result.to_dict()
    assert output_json.exists()
    assert output_markdown.exists()
    report = json.loads(output_json.read_text(encoding="utf-8"))
    validation = SchemaValidator(ROOT).validate_payload(
        schema="LocalInstallSmokeReport",
        payload=report,
        instance_label="memory:local-install-smoke-report",
    )
    assert validation.ok, validation.to_dict()
    assert report["decision"] == "PASS"
    assert report["safety"]["reports_written"] is True


def test_local_install_smoke_cli_json(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["release-candidate", "install-smoke", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "release-candidate install-smoke"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["decision"] == "PASS"
    assert payload["data"]["summary"]["network_used"] is False


def test_local_install_smoke_registered_in_tcr_v2_and_impact_analyzer() -> None:
    profile = TestContractRegistryV2Validator(ROOT).profile("release-candidate-local")
    assert profile.ok, profile.to_dict()
    assert "post-h-026-install-smoke" in {item["contract_id"] for item in profile.data["contracts"]}

    impact = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("src/devpilot_core/release_candidate/install_smoke.py",))).analyze()
    assert impact.ok, impact.to_dict()
    assert "release-candidate-local" in impact.data["summary"]["recommended_profiles"]
    assert any("release-candidate install-smoke" in command for command in impact.data["recommended_commands"])


def test_post_h_026_d_documentation_is_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-026_local_release_candidate_operator_verification.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "docs/post_h_026_d_manifest.json").read_text(encoding="utf-8"))

    assert "POST-H-026-D — Local install and run verification" in backlog
    assert "release-candidate install-smoke" in readme
    assert "release-candidate install-smoke" in runbook
    assert "post-h-026-d" in changelog
    assert manifest["micro_sprint"] == "POST-H-026-D"
    assert manifest["tests_execute_from_json"] is False
