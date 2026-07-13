from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import application_cli_boundary_integration_report
from devpilot_core.cli_registry import CliNoGrowthGate
from devpilot_core.release_candidate import EvidenceFreshnessScanner, LocalReleaseCandidateReporter
from devpilot_core.quality import QualityGateOptions
from devpilot_core.testing import HistoricalRegressionGuardRunner, TestImpactRuleRegistryRunner

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_closure_application_boundary_has_no_stale_operation_metadata() -> None:
    report = application_cli_boundary_integration_report(ROOT)

    assert report["summary"]["stale_metadata_total"] == 0
    assert report["summary"]["blocking_findings_total"] == 0
    assert report["summary"]["api_ui_operations_without_contract_total"] == 0


def test_closure_release_candidate_evidence_is_current_and_passes() -> None:
    criteria = _read_json(".devpilot/release/local_release_candidate_criteria.json")
    state = _read_json(".devpilot/project_state.json")

    assert criteria["expected_current_repo"] == state["current_repo"]
    assert criteria["expected_current_micro_sprint"] == "POST-H-034-CLOSURE"
    assert EvidenceFreshnessScanner(ROOT).scan().ok
    assert LocalReleaseCandidateReporter(ROOT).run().ok


def test_closure_agentic_runtime_is_covered_and_regression_guard_passes() -> None:
    rules = _read_json(".devpilot/testing/test_impact_rules.json")
    mapped_domains = {domain for rule in rules["rules"] for domain in rule["domains"]}

    assert "agentic.runtime" in mapped_domains
    assert TestImpactRuleRegistryRunner(ROOT).validate().ok
    assert HistoricalRegressionGuardRunner(ROOT).run().ok


def test_closure_cli_allowlist_contains_only_current_legacy_exceptions() -> None:
    allowlist = _read_json(".devpilot/cli_registry/legacy_command_allowlist.json")
    result = CliNoGrowthGate(ROOT).run()

    assert "agentops.status" in allowlist["allowed_legacy_command_ids"]
    assert result.ok
    assert result.data["summary"]["stale_allowed_commands_total"] == 0
    assert set(result.data["gate"]["commands"]["legacy_command_ids"]) == set(allowlist["allowed_legacy_command_ids"])


def test_closure_state_and_backlog_are_administratively_closed() -> None:
    state = _read_json(".devpilot/project_state.json")
    backlog = (ROOT / "docs/backlogs/POST-H-034_sensitive_capabilities_adrs.md").read_text(encoding="utf-8")

    assert state["last_completed_sprint"] == "POST-H-034"
    assert state["current_micro_sprint"] == "POST-H-034-CLOSURE"
    assert state["post_h_034_closed"] is True
    assert state["next_backlog_planned"] is False
    assert 'implementation_status: "closed/full-regression-pass"' in backlog
    assert state["post_h_034_closure_status"] == "closed/full-regression-pass"
    assert state["post_h_034_closure_full_regression_passed"] is True
    assert state["post_h_034_closure_full_regression_tests_passed"] == 1911
    assert state["post_h_034_closure_full_regression_tests_failed"] == 0
    manifest = _read_json("docs/post_h_034_closure_manifest.json")
    assert manifest["decision"] == "PASS-full-regression"
    assert manifest["final_evidence"]["test_summary"] == {
        "passed": 1911, "failed": 0, "errors": 0, "skipped": 0, "collected_total": 1911
    }


def test_closure_visual_smoke_timeout_is_bounded_for_large_repositories() -> None:
    options = QualityGateOptions(profile="hardening")

    assert 120 <= options.visual_smoke_timeout_seconds <= 600
