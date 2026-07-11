from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.testing import ReleaseCandidateTestProfileOptions, ReleaseCandidateTestProfileRunner

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_post_h_029_d_release_candidate_profile_runner_passes_without_execution() -> None:
    result = ReleaseCandidateTestProfileRunner(ROOT).run()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["decision"] == "PASS"
    assert summary["profile_id"] == "release-candidate-local"
    assert summary["required_commands_total"] >= 15
    assert summary["missing_required_commands_total"] == 0
    assert summary["missing_pytest_targets_total"] == 0
    assert summary["unsafe_commands_total"] == 0
    assert summary["tests_run_profile_synced"] is True
    assert summary["taxonomy_profile_synced"] is True
    assert summary["full_regression_rules_total"] >= 1
    assert summary["tests_executed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False


def test_post_h_029_d_profile_contains_required_release_candidate_controls() -> None:
    profile = _read_json(".devpilot/testing/release_candidate_test_profile.json")
    required_commands = "\n".join(item["command"] for item in profile["required_commands"])
    pytest_targets = {item["path"] for item in profile["pytest_targets"]}

    for fragment in [
        "project-state validate",
        "docs-governance validate",
        "schema list",
        "test-contracts validate",
        "test-contracts validate-v2",
        "quality-gate run --profile hardening",
        "industrial-readiness production-ready-local-final",
        "api shell-gate",
        "api contract-drift",
        "api security-hardening",
        "api ui-route-enforcement",
        "release-candidate final",
        "package source-zip-policy",
        "release artifact-manifest",
        "release upgrade-rollback-dry-run",
    ]:
        assert fragment in required_commands
    assert "tests/test_post_h_029_release_candidate_test_profile.py" in pytest_targets
    assert "tests/test_post_h_026_release_candidate_profile.py" in pytest_targets
    assert "tests/test_post_h_025_production_ready_final_declaration.py" in pytest_targets
    assert profile["safety"]["tests_executed_from_profile"] is False
    assert profile["safety"]["allow_shell"] is False
    assert profile["full_regression_required_when"]


def test_post_h_029_d_cli_write_report_validates_schema(capsys) -> None:
    output_json = ROOT / "outputs/reports/release_candidate_test_profile_report.json"
    output_md = ROOT / "outputs/reports/release_candidate_test_profile_report.md"
    output_json.unlink(missing_ok=True)
    output_md.unlink(missing_ok=True)

    exit_code = cli.main(["tests", "release-candidate-profile", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "tests release-candidate-profile"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["tests_executed"] is False
    assert output_json.is_file()
    assert output_md.is_file()
    assert cli.main(["schema", "validate", "--schema-id", "ReleaseCandidateTestProfileReport", "--instance", "outputs/reports/release_candidate_test_profile_report.json", "--json"]) == 0
    capsys.readouterr()


def test_post_h_029_d_blocks_unsafe_fixture(tmp_path: Path) -> None:
    fixture_dir = ROOT / "outputs/test_fixtures/post_h_029_d"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    fixture = fixture_dir / "bad_release_candidate_test_profile.json"
    payload = _read_json(".devpilot/testing/release_candidate_test_profile.json")
    payload["required_commands"] = [{"id": "bad", "command": "python -m devpilot_core project-state validate --json && echo unsafe", "category": "bad", "required": True, "write_report": False, "read_only": True, "approval_required_for_execution": False}]
    payload["safety"]["allow_shell"] = True
    fixture.write_text(json.dumps(payload), encoding="utf-8")

    result = ReleaseCandidateTestProfileRunner(ROOT, ReleaseCandidateTestProfileOptions(profile_path=fixture)).run()

    assert not result.ok
    finding_ids = {finding.id for finding in result.findings}
    assert "RC_TEST_PROFILE_UNSAFE_FLAG" in finding_ids
    assert "RC_TEST_PROFILE_REQUIRED_COMMANDS_MISSING" in finding_ids
    assert "RC_TEST_PROFILE_UNSAFE_COMMANDS" in finding_ids


def test_post_h_029_d_governance_artifacts_are_synchronized() -> None:
    state = _read_json(".devpilot/project_state.json")
    catalog = _read_json("docs/schemas/schema_catalog.json")
    source_registry = _read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = _read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _read_json(".devpilot/testing/test_contract_registry_v2.json")
    tests_profiles = _read_json(".devpilot/testing/test_profiles.json")
    readme = _read_text("README.md")
    runbook = _read_text("docs/05_operations/runbook.md")
    test_strategy = _read_text("docs/04_quality/test_strategy.md")
    tcr_design = _read_text("docs/04_quality/test_contract_registry_2_design.md")
    changelog = _read_text("docs/release/CHANGELOG.md").lower()
    backlog = _read_text("docs/backlogs/POST-H-029_testing_tiers_impact_regression_cost.md")

    assert state.get("post_h_029_current_micro_sprint") in {"POST-H-029-D", "POST-H-029-E"}
    assert state.get("post_h_029_next_micro_sprint") in {"POST-H-029-E", "POST-H-030"}
    assert state["post_h_029_status"] == "closed/testing-tiers-ready"
    assert str(state["current_repo"]).startswith("repo_DevPilot_Local_")
    assert state["post_h_029_release_candidate_test_profile_schema_registered"] is True
    assert state["post_h_029_release_candidate_test_profile_available"] is True
    assert state["post_h_029_release_candidate_test_profile_tests_executed"] is False
    assert state["post_h_029_release_candidate_test_profile_full_regression_preserved"] is True
    assert any(item["schema_id"] == "SCHEMA-DEVPL-RELEASE-CANDIDATE-TEST-PROFILE-REPORT-V1" for item in catalog["schemas"])
    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert {
        "SCHEMA-DEVPL-RELEASE-CANDIDATE-TEST-PROFILE-REPORT-V1",
        "POST-H-029-D-RELEASE-CANDIDATE-TEST-PROFILE",
        "POST-H-029-D-RELEASE-CANDIDATE-PROFILE-MODULE",
        "POST-H-029-D-RELEASE-CANDIDATE-PROFILE-REPORT",
        "POST-H-029-D-MANIFEST",
        "POST-H-029-D-RELEASE-CANDIDATE-PROFILE-TEST",
    } <= doc_ids
    assert any(item["contract_id"] == "post-h-029-release-candidate-test-profile" for item in tcr_v1["contracts"])
    v2_contract = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-029-release-candidate-test-profile")
    assert v2_contract["classification_status"] == "explicit"
    assert v2_contract["subgate_id"] == "release-candidate-test-profile"
    assert "SCHEMA-DEVPL-RELEASE-CANDIDATE-TEST-PROFILE-REPORT-V1" in v2_contract["schema_ids"]
    tests_run_profile = next(item for item in tests_profiles["profiles"] if item["profile_id"] == "release-candidate-local")
    assert tests_run_profile["release_candidate_profile_path"] == ".devpilot/testing/release_candidate_test_profile.json"
    assert tests_run_profile["requires_approval_for_pytest"] is True
    assert "POST-H-029-D — Release candidate test profile" in readme
    assert "POST-H-029-D — Release candidate test profile" in runbook
    assert "ReleaseCandidateTestProfileReport" in test_strategy
    assert "ReleaseCandidateTestProfileReport" in tcr_design
    assert "post-h-029-d" in changelog
    assert 'current_micro_sprint: "POST-H-029-D"' in backlog or 'current_micro_sprint: "POST-H-029-E"' in backlog


def test_post_h_029_d_existing_post_h_026_profile_remains_compatible() -> None:
    exit_code = cli.main(["release-candidate", "profile", "--profile", "release-candidate-local", "--json"])
    assert exit_code == 0
