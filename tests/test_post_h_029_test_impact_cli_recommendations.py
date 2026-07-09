from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.testing import TestImpactAnalyzerV2, TestImpactV2Options

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_post_h_029_c_policy_change_produces_normalized_recommendation_report() -> None:
    result = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("src/devpilot_core/policy/engine.py",))).analyze()

    assert result.ok, result.to_dict()
    report = result.data["recommendation_report"]
    summary = report["summary"]
    assert report["schema_id"] == "SCHEMA-DEVPL-TEST-IMPACT-RECOMMENDATION-REPORT-V1"
    assert summary["created_by"] == "POST-H-029-C"
    assert summary["tests_executed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert "p0-critical" in report["recommended_profiles"]
    assert "security" in report["recommended_profiles"]
    assert report["matched_rules"]
    assert any(rule["rule_id"] == "policy-security" for rule in report["matched_rules"])
    assert report["recommended_tests"]
    assert report["recommended_commands"]
    assert summary["full_regression_required"] is True
    assert summary["waiver_required_if_full_regression_skipped"] is True
    assert report["execution_plan"]["tests_executed"] is False


def test_post_h_029_c_release_change_recommends_release_profiles() -> None:
    result = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("src/devpilot_core/release_candidate/report.py",))).analyze()

    assert result.ok, result.to_dict()
    report = result.data["recommendation_report"]
    assert "release" in report["recommended_profiles"]
    assert "release-candidate-local" in report["recommended_profiles"]
    assert any(rule["rule_id"] == "release-packaging-rc" for rule in report["matched_rules"])
    assert report["summary"]["tests_executed"] is False
    assert report["summary"]["full_regression_required"] is True


def test_post_h_029_c_unmapped_path_requires_review_not_no_tests() -> None:
    result = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("sandbox/unknown/new_file.txt",))).analyze()

    assert result.ok, result.to_dict()
    report = result.data["recommendation_report"]
    assert report["summary"]["unmatched_paths_total"] == 1
    assert report["summary"]["manual_review_required"] is True
    assert report["summary"]["decision"] == "REVIEW_REQUIRED"
    assert report["recommendation_groups"]["manual_review"]["required"] is True
    assert "p0-critical" in report["recommended_profiles"]
    assert report["summary"]["tests_executed"] is False


def test_post_h_029_c_changed_paths_file_and_write_report_validate_schema(tmp_path: Path) -> None:
    changed = tmp_path / "changed_paths.txt"
    changed.write_text("src/devpilot_core/testing/impact_v2.py\n", encoding="utf-8")
    output_json = ROOT / "outputs/reports/test_impact_recommendation_report.json"
    output_md = ROOT / "outputs/reports/test_impact_recommendation_report.md"
    output_json.unlink(missing_ok=True)
    output_md.unlink(missing_ok=True)

    exit_code = cli.main(["test-impact", "analyze-v2", "--changed-paths-file", str(changed), "--json", "--write-report"])

    assert exit_code == 0
    assert output_json.is_file()
    assert output_md.is_file()
    report = json.loads(output_json.read_text(encoding="utf-8"))
    assert report["summary"]["reports_written"] is True
    assert report["summary"]["tests_executed"] is False
    assert cli.main(["schema", "validate", "--schema-id", "TestImpactRecommendationReport", "--instance", "outputs/reports/test_impact_recommendation_report.json", "--json"]) == 0


def test_post_h_029_c_recommended_commands_are_safe() -> None:
    result = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("src/devpilot_core/testing/impact_v2.py",))).analyze()

    assert result.ok, result.to_dict()
    report = result.data["recommendation_report"]
    assert report["summary"]["unsafe_commands_total"] == 0
    for command in report["recommended_commands"]:
        lowered = command.lower()
        assert "&&" not in lowered
        assert "||" not in lowered
        assert ";" not in lowered
        assert not lowered.startswith("curl ")
        assert not lowered.startswith("wget ")


def test_post_h_029_c_governance_artifacts_are_synchronized() -> None:
    state = _read_json(".devpilot/project_state.json")
    catalog = _read_json("docs/schemas/schema_catalog.json")
    source_registry = _read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = _read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _read_json(".devpilot/testing/test_contract_registry_v2.json")
    readme = _read_text("README.md")
    runbook = _read_text("docs/05_operations/runbook.md")
    test_strategy = _read_text("docs/04_quality/test_strategy.md")
    tcr_design = _read_text("docs/04_quality/test_contract_registry_2_design.md")
    changelog = _read_text("docs/release/CHANGELOG.md").lower()
    backlog = _read_text("docs/backlogs/POST-H-029_testing_tiers_impact_regression_cost.md")

    assert state["current_micro_sprint"] == "POST-H-029-C"
    assert state["next_micro_sprint"] == "POST-H-029-D"
    assert state["current_repo"] == "repo_DevPilot_Local_281_POST_H_029_C.zip"
    assert state["post_h_029_test_impact_recommendation_report_schema_registered"] is True
    assert state["post_h_029_test_impact_cli_recommendations_available"] is True
    assert state["post_h_029_test_impact_cli_recommendations_tests_executed"] is False
    assert state["post_h_029_test_impact_cli_recommendations_unsafe_commands_total"] == 0
    assert state["post_h_029_test_impact_cli_recommendations_write_report_available"] is True

    assert any(item["schema_id"] == "SCHEMA-DEVPL-TEST-IMPACT-RECOMMENDATION-REPORT-V1" for item in catalog["schemas"])
    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert {
        "SCHEMA-DEVPL-TEST-IMPACT-RECOMMENDATION-REPORT-V1",
        "POST-H-029-C-RECOMMENDATIONS-MODULE",
        "POST-H-029-C-RECOMMENDATIONS-REPORT",
        "POST-H-029-C-MANIFEST",
        "POST-H-029-C-RECOMMENDATIONS-TEST",
    } <= doc_ids
    assert any(item["contract_id"] == "post-h-029-test-impact-cli-recommendations" for item in tcr_v1["contracts"])
    v2_contract = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-029-test-impact-cli-recommendations")
    assert v2_contract["classification_status"] == "explicit"
    assert v2_contract["subgate_id"] == "test-impact-recommendations"
    assert "SCHEMA-DEVPL-TEST-IMPACT-RECOMMENDATION-REPORT-V1" in v2_contract["schema_ids"]
    assert "POST-H-029-C — Test impact CLI recommendations" in readme
    assert "POST-H-029-C — Test impact CLI recommendations" in runbook
    assert "TestImpactRecommendationReport" in test_strategy
    assert "TestImpactRecommendationReport" in tcr_design
    assert "post-h-029-c" in changelog
    assert 'current_micro_sprint: "POST-H-029-C"' in backlog
