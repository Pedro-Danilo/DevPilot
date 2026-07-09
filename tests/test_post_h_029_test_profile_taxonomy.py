from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.schemas import SchemaValidator
from devpilot_core.testing import TestProfileRegistry as ProfileRegistry
from devpilot_core.testing import TestProfileTaxonomyRunner as ProfileTaxonomyRunner

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PROFILE_IDS = {
    "always-fast",
    "p0-critical",
    "security",
    "impact",
    "release",
    "release-candidate-local",
    "docs-historical",
    "full",
    "manual",
    "nightly-local",
}


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_profile_taxonomy_schema_and_runner_pass() -> None:
    schema = SchemaValidator(ROOT).validate(
        schema="TestProfileTaxonomy",
        instance=".devpilot/testing/test_profile_taxonomy.json",
    )
    assert schema.ok, schema.to_dict()

    result = ProfileTaxonomyRunner(ROOT).run()
    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-029-A"
    assert summary["test_profile_taxonomy_valid"] is True
    assert summary["profiles_total"] == 10
    assert summary["legacy_aliases_total"] == 3
    assert summary["unsafe_commands_total"] == 0
    assert summary["high_risk_without_approval_total"] == 0
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["tests_executed"] is False


def test_profile_taxonomy_declares_required_profiles_aliases_and_safety_flags() -> None:
    taxonomy = _read_json(".devpilot/testing/test_profile_taxonomy.json")
    profile_ids = {item["profile_id"] for item in taxonomy["profiles"]}
    assert REQUIRED_PROFILE_IDS <= profile_ids

    aliases = {item["legacy_profile_id"]: item["maps_to_profile_id"] for item in taxonomy["legacy_aliases"]}
    assert aliases == {"smoke": "always-fast", "unit": "always-fast", "all": "full"}
    assert taxonomy["policy"]["full_regression_preserved"] is True
    assert taxonomy["policy"]["unknown_impact_escalates"] is True
    assert taxonomy["policy"]["tests_run_approval_gated"] is True
    assert taxonomy["safety"]["tests_executed_from_taxonomy"] is False
    assert taxonomy["safety"]["network_used"] is False
    assert taxonomy["safety"]["external_api_used"] is False

    high_risk = {"p0-critical", "security", "release", "release-candidate-local", "full", "nightly-local"}
    for item in taxonomy["profiles"]:
        assert item["allow_shell"] is False
        assert item["network_allowed"] is False
        assert item["external_api_allowed"] is False
        assert item["mutations_allowed"] is False
        if item["profile_id"] in high_risk:
            assert item["requires_approval_for_execution"] is True


def test_tests_profiles_runtime_registry_preserves_legacy_and_new_profiles() -> None:
    registry = ProfileRegistry(ROOT)
    ids = {profile.profile_id for profile in registry.list()}
    assert {"smoke", "unit", "all"}.issubset(ids)
    assert REQUIRED_PROFILE_IDS <= ids

    profiles = _read_json(".devpilot/testing/test_profiles.json")
    assert profiles["created_by"] == "POST-H-029-A"
    assert profiles["safety"]["allow_shell"] is False
    assert profiles["safety"]["tests_run_approval_gated"] is True
    assert profiles["safety"]["tests_executed_from_json"] is False


def test_tests_taxonomy_cli_and_write_report() -> None:
    output_json = ROOT / "outputs/reports/test_profile_taxonomy_report.json"
    output_md = ROOT / "outputs/reports/test_profile_taxonomy_report.md"
    output_json.unlink(missing_ok=True)
    output_md.unlink(missing_ok=True)

    exit_code = cli.main(["tests", "taxonomy", "--json", "--write-report"])
    assert exit_code == 0
    assert output_json.is_file()
    assert output_md.is_file()
    report = json.loads(output_json.read_text(encoding="utf-8"))
    assert report["summary"]["decision"] == "PASS"
    assert report["summary"]["tests_executed"] is False


def test_post_h_029_a_governance_artifacts_are_synchronized() -> None:
    state = _read_json(".devpilot/project_state.json")
    catalog = _read_json("docs/schemas/schema_catalog.json")
    source_registry = _read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = _read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _read_json(".devpilot/testing/test_contract_registry_v2.json")
    readme = _read_text("README.md")
    runbook = _read_text("docs/05_operations/runbook.md")
    test_strategy = _read_text("docs/04_quality/test_strategy.md")
    changelog = _read_text("docs/release/CHANGELOG.md").lower()

    assert state["last_completed_sprint"] == "POST-H-028"
    assert state["next_sprint"] == "POST-H-029"
    assert state["current_micro_sprint"] == "POST-H-029-A"
    assert state["next_micro_sprint"] == "POST-H-029-B"
    assert state["current_repo"] == "repo_DevPilot_Local_279_POST_H_029_A.zip"
    assert state["post_h_029_test_profile_taxonomy_valid"] is True
    assert state["post_h_029_tests_executed_from_taxonomy"] is False
    assert state["post_h_029_full_regression_preserved"] is True

    assert any(item["schema_id"] == "SCHEMA-DEVPL-TEST-PROFILE-TAXONOMY-V1" for item in catalog["schemas"])
    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert {
        "POST-H-029-BACKLOG",
        "POST-H-029-DOC",
        "SCHEMA-DEVPL-TEST-PROFILE-TAXONOMY-V1",
        "POST-H-029-A-TEST-PROFILE-TAXONOMY",
        "POST-H-029-A-TEST-PROFILE-TAXONOMY-MODULE",
        "POST-H-029-A-TEST-PROFILE-TAXONOMY-REPORT",
        "POST-H-029-A-MANIFEST",
        "POST-H-029-A-TEST-PROFILE-TAXONOMY-TEST",
    } <= doc_ids
    assert any(item["contract_id"] == "post-h-029-test-profile-taxonomy" for item in tcr_v1["contracts"])
    assert any(item["contract_id"] == "post-h-029-test-profile-taxonomy" for item in tcr_v2["contracts"])
    assert "POST-H-029-A — Test profile taxonomy" in readme
    assert "POST-H-029-A — Test profile taxonomy" in runbook
    assert "Taxonomía de perfiles de prueba" in test_strategy
    assert "post-h-029-a" in changelog


def test_backlog_is_approved_and_top_level_doc_exists() -> None:
    backlog = _read_text("docs/backlogs/POST-H-029_testing_tiers_impact_regression_cost.md")
    top_level = _read_text("docs/POST-H-029_testing_tiers_impact_regression_cost.md")
    assert 'status: "approved"' in backlog
    assert 'implementation_status: "active/implemented-initial-post-h-029-a"' in backlog
    assert 'current_micro_sprint: "POST-H-029-A"' in backlog
    assert 'next_micro_sprint: "POST-H-029-B"' in backlog
    assert 'doc_id: "POST-H-029-DOC"' in top_level
