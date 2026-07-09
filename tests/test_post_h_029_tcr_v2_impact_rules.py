from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.testing import TestImpactAnalyzerV2, TestImpactRuleRegistryOptions, TestImpactRuleRegistryRunner, TestImpactV2Options

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_post_h_029_b_rule_registry_runner_passes_without_executing_tests() -> None:
    result = TestImpactRuleRegistryRunner(ROOT).validate()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["test_impact_rule_registry_valid"] is True
    assert summary["rules_total"] >= 12
    assert summary["unmapped_p0_p1_domains_total"] == 0
    assert summary["unsafe_commands_total"] == 0
    assert summary["unknown_impact_escalates"] is True
    assert summary["sensitive_unmatched_full_regression"] is True
    assert summary["tests_executed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False


def test_post_h_029_b_schema_and_cli_write_report() -> None:
    output_json = ROOT / "outputs/reports/test_impact_rule_registry_report.json"
    output_md = ROOT / "outputs/reports/test_impact_rule_registry_report.md"
    output_json.unlink(missing_ok=True)
    output_md.unlink(missing_ok=True)

    assert cli.main(["schema", "validate", "--schema-id", "TestImpactRuleRegistry", "--instance", ".devpilot/testing/test_impact_rules.json", "--json"]) == 0
    assert cli.main(["test-impact", "rules", "--json", "--write-report"]) == 0
    assert output_json.is_file()
    assert output_md.is_file()
    report = json.loads(output_json.read_text(encoding="utf-8"))
    assert report["summary"]["decision"] == "PASS"
    assert report["summary"]["tests_executed"] is False


def test_post_h_029_b_rules_cover_all_current_p0_p1_tcr_v2_domains() -> None:
    registry = _read_json(".devpilot/testing/test_impact_rules.json")
    tcr_v2 = _read_json(".devpilot/testing/test_contract_registry_v2.json")
    mapped_domains = {domain for rule in registry["rules"] for domain in rule["domains"]}
    p0_p1_domains = {contract["domain"] for contract in tcr_v2["contracts"] if contract["criticality"] in {"P0", "P1"}}

    assert p0_p1_domains <= mapped_domains
    assert registry["unmatched_path_policy"]["unknown_path_escalates"] is True
    assert registry["unmatched_path_policy"]["sensitive_path_default"] == "full-regression-required"
    assert all(rule["safety"]["tests_executed_from_rule"] is False for rule in registry["rules"])


def test_post_h_029_b_impact_analyzer_v2_uses_rule_registry_for_testing_changes() -> None:
    result = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("src/devpilot_core/testing/impact_rules.py",))).analyze()

    assert result.ok, result.to_dict()
    assert "p0-critical" in result.data["summary"]["recommended_profiles"]
    assert "impact" in result.data["summary"]["recommended_profiles"]
    assert any(item["rule_id"] == "testing-infra" for item in result.data["heuristic_recommendations"])
    assert any(finding.id == "TEST_IMPACT_V2_RULE_REGISTRY_APPLIED" for finding in result.findings)
    assert result.data["summary"]["tests_executed"] is False


def test_post_h_029_b_negative_policy_blocks_unsafe_unmatched_policy(tmp_path: Path) -> None:
    registry = _read_json(".devpilot/testing/test_impact_rules.json")
    registry["unmatched_path_policy"]["unknown_path_escalates"] = False
    registry["unmatched_path_policy"]["sensitive_path_default"] = "review-required"
    bad_registry = tmp_path / "bad_test_impact_rules.json"
    bad_registry.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    result = TestImpactRuleRegistryRunner(ROOT, TestImpactRuleRegistryOptions(registry_path=bad_registry)).validate()

    assert not result.ok
    assert result.data["summary"]["decision"] == "BLOCK"
    assert any(finding.id == "TEST_IMPACT_RULE_UNKNOWN_IMPACT_MUST_ESCALATE" for finding in result.findings)
    assert any(finding.id == "TEST_IMPACT_RULE_SENSITIVE_UNMATCHED_FULL_REQUIRED" for finding in result.findings)


def test_post_h_029_b_governance_artifacts_are_synchronized() -> None:
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

    assert state["current_micro_sprint"] == "POST-H-029-D"
    assert state["next_micro_sprint"] == "POST-H-029-E"
    assert state["current_repo"] == "repo_DevPilot_Local_282_POST_H_029_D.zip"
    assert state["post_h_029_test_impact_rule_registry_valid"] is True
    assert state["post_h_029_test_impact_rules_unmapped_p0_p1_domains_total"] == 0
    assert state["post_h_029_test_impact_rules_unsafe_commands_total"] == 0
    assert state["post_h_029_test_impact_analyzer_v2_uses_rule_registry"] is True

    assert any(item["schema_id"] == "SCHEMA-DEVPL-TEST-IMPACT-RULE-REGISTRY-V1" for item in catalog["schemas"])
    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert {
        "SCHEMA-DEVPL-TEST-IMPACT-RULE-REGISTRY-V1",
        "POST-H-029-B-TEST-IMPACT-RULES",
        "POST-H-029-B-IMPACT-RULES-MODULE",
        "POST-H-029-B-IMPACT-RULES-REPORT",
        "POST-H-029-B-MANIFEST",
        "POST-H-029-B-IMPACT-RULES-TEST",
    } <= doc_ids
    assert any(item["contract_id"] == "post-h-029-tcr-v2-impact-rules" for item in tcr_v1["contracts"])
    v2_contract = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-029-tcr-v2-impact-rules")
    assert v2_contract["classification_status"] == "explicit"
    assert v2_contract["subgate_id"] == "test-impact-rules"
    assert "SCHEMA-DEVPL-TEST-IMPACT-RULE-REGISTRY-V1" in v2_contract["schema_ids"]
    assert "POST-H-029-B — TCR v2 impact rules" in readme
    assert "POST-H-029-B — TCR v2 impact rules" in runbook
    assert "TestImpactRuleRegistry" in test_strategy
    assert "TestImpactRuleRegistry" in tcr_design
    assert "post-h-029-b" in changelog
    assert 'current_micro_sprint: "POST-H-029-D"' in backlog
