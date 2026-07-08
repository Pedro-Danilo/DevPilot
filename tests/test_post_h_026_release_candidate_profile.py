from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.release_candidate import ReleaseCandidateVerificationProfile, ReleaseCandidateVerificationProfileOptions
from devpilot_core.testing import TestContractRegistryV2Validator, TestImpactAnalyzerV2, TestImpactV2Options

ROOT = Path(__file__).resolve().parents[1]


def test_release_candidate_profile_registry_is_local_only_and_approval_gated() -> None:
    profiles = json.loads((ROOT / ".devpilot/testing/test_profiles.json").read_text(encoding="utf-8"))
    profile = next(item for item in profiles["profiles"] if item["profile_id"] == "release-candidate-local")

    assert profile["network_allowed"] is False
    assert profile["external_api_allowed"] is False
    assert profile["requires_approval_for_pytest"] is True
    assert profile["allow_arbitrary_pytest_args"] is False
    assert profile["allow_shell"] is False
    assert set(profile["taxonomy"]) == {"always", "impacted", "release-candidate", "full"}
    assert "release-candidate evidence-freshness" in profile["commands"]
    assert "release-candidate ui-api-smoke" in profile["commands"]
    assert "release-candidate install-smoke" in profile["commands"]
    assert "industrial-readiness production-ready-local-final" in profile["commands"]
    assert "tests/test_post_h_026_release_candidate_profile.py" in profile["pytest_targets"]


def test_release_candidate_profile_inspector_is_plan_only_and_can_write_report(tmp_path: Path) -> None:
    result = ReleaseCandidateVerificationProfile(
        ROOT,
        ReleaseCandidateVerificationProfileOptions(
            output_json="outputs/reports/test_rc_profile.json",
            output_markdown="outputs/reports/test_rc_profile.md",
            write_report=True,
        ),
    ).inspect()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["profile_id"] == "release-candidate-local"
    assert summary["execution_mode"] == "plan-only"
    assert summary["tests_executed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["tcr_v2_contracts_selected_total"] >= 1
    assert result.data["report"]["decision"] == "PASS"
    assert (ROOT / "outputs/reports/test_rc_profile.json").is_file()
    assert (ROOT / "outputs/reports/test_rc_profile.md").is_file()


def test_release_candidate_profile_blocks_incomplete_fixture(tmp_path: Path) -> None:
    testing = ROOT / "outputs/test_fixtures/post_h_026_b/.devpilot/testing"
    testing.mkdir(parents=True, exist_ok=True)
    (testing / "test_profiles.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "profiles": [
                    {
                        "profile_id": "release-candidate-local",
                        "description": "unsafe fixture",
                        "commands": ["project-state validate"],
                        "pytest_targets": [],
                        "taxonomy": ["always"],
                        "network_allowed": True,
                        "external_api_allowed": False,
                        "requires_approval_for_pytest": False,
                        "allow_arbitrary_pytest_args": True,
                        "allow_shell": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    # Reuse the real TCR v2 so this test isolates profile semantic failures.
    result = ReleaseCandidateVerificationProfile(
        ROOT,
        ReleaseCandidateVerificationProfileOptions(test_profiles_path="outputs/test_fixtures/post_h_026_b/.devpilot/testing/test_profiles.json"),
    ).inspect()

    assert not result.ok
    finding_ids = {finding.id for finding in result.findings}
    assert "RC_PROFILE_REQUIRED_COMMANDS_MISSING" in finding_ids
    assert "RC_PROFILE_NETWORK_NOT_ALLOWED" in finding_ids
    assert "RC_PROFILE_PYTEST_APPROVAL_REQUIRED" in finding_ids
    assert "RC_PROFILE_ARBITRARY_EXECUTION_BLOCKED" in finding_ids


def test_release_candidate_profile_cli_command_is_available(capsys) -> None:
    exit_code = cli.main(["release-candidate", "profile", "--profile", "release-candidate-local", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "release-candidate profile"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["tests_executed"] is False
    assert payload["data"]["summary"]["network_used"] is False


def test_tcr_v2_selects_release_candidate_local_profile() -> None:
    result = TestContractRegistryV2Validator(ROOT).profile("release-candidate-local")

    assert result.ok, result.to_dict()
    assert result.data["summary"]["profile"] == "release-candidate-local"
    assert result.data["summary"]["contracts_selected"] >= 1
    assert "post-h-026-release-candidate-profile" in {item["contract_id"] for item in result.data["contracts"]}


def test_impact_v2_release_candidate_changes_recommend_rc_profile() -> None:
    result = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("src/devpilot_core/release_candidate/verification_profile.py",))).analyze()

    assert result.ok, result.to_dict()
    assert "release-candidate-local" in result.data["summary"]["recommended_profiles"]
    assert any("release-candidate profile" in command for command in result.data["recommended_commands"])
    assert result.data["summary"]["tests_executed"] is False


def test_post_h_026_b_documentation_is_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-026_local_release_candidate_operator_verification.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "docs/post_h_026_b_manifest.json").read_text(encoding="utf-8"))

    assert "POST-H-026-B — Release candidate verification profile" in backlog
    assert "release-candidate profile" in readme
    assert "release-candidate profile" in runbook
    assert "post-h-026-b" in changelog
    assert manifest["micro_sprint"] == "POST-H-026-B"
    assert manifest["tests_execute_from_json"] is False
