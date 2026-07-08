from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.release import PackageBuildBuilder, PackageBuildOptions, SourceZipPolicyOptions, SourceZipReleasePolicyValidator
from devpilot_core.schemas.validator import SchemaValidator
from devpilot_core.testing import TestContractRegistryV2Validator
from devpilot_core.testing.impact_v2 import TestImpactAnalyzerV2, TestImpactV2Options

ROOT = Path(__file__).resolve().parents[1]


def _clean_dist_and_reports() -> None:
    shutil.rmtree(ROOT / "dist", ignore_errors=True)
    shutil.rmtree(ROOT / "outputs" / "release", ignore_errors=True)
    for path in [ROOT / "outputs" / "reports" / "package_build.json", ROOT / "outputs" / "reports" / "package_build.md"]:
        if path.exists():
            path.unlink()


def test_source_zip_release_policy_passes_without_network_or_mutations() -> None:
    result = SourceZipReleasePolicyValidator(ROOT).run()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["decision"] == "PASS"
    assert summary["clean_source_zip_policy_passed"] is True
    assert summary["no_runtime_artifacts_in_packages"] is True
    assert summary["no_secrets_in_packages"] is True
    assert summary["package_build_dry_run_default"] is True
    assert summary["execute_required_to_write"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["source_mutations"] is False
    safety = result.data["report"]["safety"]
    assert safety["artifact_extracted"] is False
    assert safety["subprocess_executed"] is False
    assert safety["publish_performed"] is False
    assert safety["deploy_performed"] is False
    assert any(finding.id == "SOURCE_ZIP_RELEASE_POLICY_PASS" for finding in result.findings)


def test_source_zip_release_policy_json_and_report_validate_against_schemas() -> None:
    policy_validation = SchemaValidator(ROOT).validate(
        schema="SourceZipReleasePolicy",
        instance=ROOT / ".devpilot/release/source_zip_release_policy.json",
    )
    assert policy_validation.ok, policy_validation.to_dict()

    output_json = ROOT / "outputs/test_fixtures/post_h_027_a/source_zip_release_report.json"
    output_markdown = ROOT / "outputs/test_fixtures/post_h_027_a/source_zip_release_report.md"
    result = SourceZipReleasePolicyValidator(
        ROOT,
        SourceZipPolicyOptions(
            output_json=str(output_json),
            output_markdown=str(output_markdown),
            write_report=True,
        ),
    ).run()
    assert result.ok, result.to_dict()
    assert output_json.exists()
    assert output_markdown.exists()
    report = json.loads(output_json.read_text(encoding="utf-8"))
    report_validation = SchemaValidator(ROOT).validate_payload(
        schema="SourceZipReleaseReport",
        payload=report,
        instance_label="memory:source-zip-release-report",
    )
    assert report_validation.ok, report_validation.to_dict()
    assert report["decision"] == "PASS"
    assert report["safety"]["reports_written"] is True


def test_source_zip_release_policy_blocks_bad_candidate_zip(tmp_path: Path) -> None:
    policy = json.loads((ROOT / ".devpilot/release/source_zip_release_policy.json").read_text(encoding="utf-8"))
    candidate = tmp_path / "bad-source.zip"
    with zipfile.ZipFile(candidate, "w") as archive:
        for required in policy["required_includes"]:
            archive.writestr(required, "placeholder\n")
        archive.writestr("outputs/traces/events.jsonl", "{}\n")
        archive.writestr("ui/web/node_modules/pkg/index.js", "bad")
        archive.writestr("src/devpilot_core/leaky.py", "TOKEN = 'ghp_abcdefghijklmnopqrstuv'\n")

    result = SourceZipReleasePolicyValidator(ROOT, SourceZipPolicyOptions(artifact=str(candidate))).run()

    assert not result.ok
    assert result.exit_code == ExitCode.BLOCK
    report = result.data["report"]
    assert report["decision"] == "BLOCK"
    artifact = report["artifact_result"]
    assert artifact["artifact_checked"] is True
    assert artifact["forbidden_present_total"] >= 2
    assert artifact["secret_findings_total"] >= 1
    finding_ids = {finding.id for finding in result.findings}
    assert "SOURCE_ZIP_ARTIFACT_FORBIDDEN_ENTRIES_BLOCK" in finding_ids
    assert "SOURCE_ZIP_ARTIFACT_SECRET_CONTENT_BLOCK" in finding_ids


def test_package_build_repo_zip_uses_policy_and_artifact_passes_policy() -> None:
    _clean_dist_and_reports()
    build = PackageBuildBuilder(ROOT, options=PackageBuildOptions(version="0.1.0", kind="repo-zip", execute=True)).build()

    assert build.ok, build.to_dict()
    package = build.data["package_build"]
    assert package["source_zip_release_policy"]["policy_loaded"] is True
    assert package["source_zip_release_policy"]["policy_id"] == "devpilot-source-zip-release-policy-v1"
    artifact = ROOT / "dist/release/devpilot-local-0.1.0-source.zip"
    assert artifact.exists()

    policy_result = SourceZipReleasePolicyValidator(ROOT, SourceZipPolicyOptions(artifact=str(artifact))).run()
    assert policy_result.ok, policy_result.to_dict()
    assert policy_result.data["summary"]["artifact_checked"] is True
    assert policy_result.data["report"]["artifact_result"]["forbidden_present_total"] == 0
    assert policy_result.data["report"]["artifact_result"]["required_missing_total"] == 0


def test_source_zip_release_policy_cli_json_is_available(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["package", "source-zip-policy", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "package source-zip-policy"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["decision"] == "PASS"
    assert payload["data"]["summary"]["network_used"] is False


def test_source_zip_release_policy_registered_in_tcr_v2_and_impact_analyzer() -> None:
    release = TestContractRegistryV2Validator(ROOT).profile("release")
    assert release.ok, release.to_dict()
    assert "post-h-027-source-zip-policy" in {item["contract_id"] for item in release.data["contracts"]}

    impact = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("src/devpilot_core/release/source_zip_policy.py",))).analyze()
    assert impact.ok, impact.to_dict()
    assert "release" in impact.data["summary"]["recommended_profiles"]
    assert any("package source-zip-policy" in command for command in impact.data["recommended_commands"])


def test_post_h_027_a_documentation_is_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-027_packaging_reproducible_local_installation.md").read_text(encoding="utf-8")
    top_level = (ROOT / "docs/POST-H-027_packaging_reproducible_local_installation.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "docs/post_h_027_a_manifest.json").read_text(encoding="utf-8"))

    assert 'status: "approved"' in backlog
    assert 'implementation_status: "active/artifact-manifest-checksums-implemented-initial"' in backlog
    assert 'current_micro_sprint: "POST-H-027-C"' in backlog
    assert "POST-H-027-A — Source ZIP release policy hardening" in backlog
    assert "POST-H-027-A — Source ZIP release policy hardening" in top_level
    assert "package source-zip-policy" in readme
    assert "package source-zip-policy" in runbook
    assert "post-h-027-a" in changelog
    assert manifest["micro_sprint"] == "POST-H-027-A"
    assert manifest["status"] == "implemented-initial"
    assert manifest["tests_execute_from_json"] is False
