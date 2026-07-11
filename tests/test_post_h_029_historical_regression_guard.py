from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from devpilot_core import cli
from devpilot_core.quality import QualityGate, QualityGateOptions
from devpilot_core.testing import HistoricalRegressionGuardOptions, HistoricalRegressionGuardRunner

ROOT = Path(__file__).resolve().parents[1]


def _post_h_number(value: str) -> int:
    return int(str(value).split("POST-H-")[-1].split("-")[0])


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_post_h_029_e_micro_sprint_guard_passes_without_executing_tests() -> None:
    result = HistoricalRegressionGuardRunner(ROOT).run()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["decision"] == "PASS"
    assert summary["context"] == "micro-sprint"
    assert summary["regression_decision"] == "focal-expanded"
    assert summary["full_regression_required"] is False
    assert summary["components_passed_total"] == summary["components_total"]
    assert summary["tests_executed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False


def test_post_h_029_e_backlog_closure_without_decision_blocks() -> None:
    result = HistoricalRegressionGuardRunner(
        ROOT,
        HistoricalRegressionGuardOptions(context="backlog-closure"),
    ).run()

    assert not result.ok
    summary = result.data["summary"]
    assert summary["decision"] == "BLOCK"
    assert summary["full_regression_required"] is True
    assert summary["explicit_decision_required"] is True
    assert "HISTORICAL_REGRESSION_DECISION_REQUIRED" in {finding.id for finding in result.findings}


def test_post_h_029_e_sensitive_changed_path_requires_full_or_waiver() -> None:
    result = HistoricalRegressionGuardRunner(
        ROOT,
        HistoricalRegressionGuardOptions(
            context="micro-sprint",
            changed_paths=(".devpilot/project_state.json",),
            regression_decision="focal-expanded",
        ),
    ).run()

    assert not result.ok
    summary = result.data["summary"]
    assert summary["full_regression_required"] is True
    assert summary["blocking_findings_total"] >= 1
    assert "HISTORICAL_REGRESSION_FULL_REQUIRED" in {finding.id for finding in result.findings}


def test_post_h_029_e_waiver_requires_owner_reason_risk_tests_and_expiration() -> None:
    fixture_dir = ROOT / "outputs/test_fixtures/post_h_029_e"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    bad_waiver = fixture_dir / "bad_waiver.json"
    bad_waiver.write_text(json.dumps({"owner": "Ordóñez"}), encoding="utf-8")

    result = HistoricalRegressionGuardRunner(
        ROOT,
        HistoricalRegressionGuardOptions(
            context="backlog-closure",
            regression_decision="waiver",
            waiver_file=bad_waiver,
        ),
    ).run()

    assert not result.ok
    assert "HISTORICAL_REGRESSION_WAIVER_INVALID" in {finding.id for finding in result.findings}

    good_waiver = fixture_dir / "good_waiver.json"
    expires = (datetime.now(UTC) + timedelta(days=7)).isoformat().replace("+00:00", "Z")
    good_waiver.write_text(
        json.dumps(
            {
                "owner": "Ordóñez",
                "reason": "Full regression is deferred because focal RC evidence has already been captured for this local-only change.",
                "risk": "medium",
                "tests_executed": ["tests/test_post_h_029_historical_regression_guard.py"],
                "expires_at": expires,
            }
        ),
        encoding="utf-8",
    )
    ok_result = HistoricalRegressionGuardRunner(
        ROOT,
        HistoricalRegressionGuardOptions(
            context="backlog-closure",
            regression_decision="waiver",
            waiver_file=good_waiver,
        ),
    ).run()

    assert ok_result.ok, ok_result.to_dict()
    assert ok_result.data["summary"]["waiver_valid"] is True


def test_post_h_029_e_cli_write_report_validates_schema(capsys) -> None:
    output_json = ROOT / "outputs/reports/historical_regression_guard_report.json"
    output_md = ROOT / "outputs/reports/historical_regression_guard_report.md"
    output_json.unlink(missing_ok=True)
    output_md.unlink(missing_ok=True)

    exit_code = cli.main(["tests", "regression-guard", "--context", "micro-sprint", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "tests regression-guard"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["tests_executed"] is False
    assert output_json.is_file()
    assert output_md.is_file()
    assert cli.main(["schema", "validate", "--schema-id", "HistoricalRegressionGuardReport", "--instance", "outputs/reports/historical_regression_guard_report.json", "--json"]) == 0
    capsys.readouterr()


def test_post_h_029_e_quality_gate_and_governance_are_synchronized() -> None:
    gate = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))
    subgates = {subgate.id: subgate for subgate in gate._subgates()}
    assert "testing-tiers-ready" in subgates
    subgate_result = subgates["testing-tiers-ready"].runner()
    assert subgate_result.ok, subgate_result.to_dict()
    assert subgate_result.data["summary"]["context"] == "micro-sprint"

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

    assert state.get("post_h_029_current_micro_sprint") == "POST-H-029-E"
    assert _post_h_number(state["last_completed_sprint"]) >= 29
    assert state.get("post_h_029_next_micro_sprint") == "POST-H-030"
    assert state["post_h_029_status"] == "closed/testing-tiers-ready"
    assert str(state["current_repo"]).startswith("repo_DevPilot_Local_")
    assert state["post_h_029_status"] == "closed/testing-tiers-ready"
    assert state["post_h_029_historical_regression_guard_available"] is True
    assert state["post_h_029_testing_tiers_ready_quality_gate_enabled"] is True
    assert any(item["schema_id"] == "SCHEMA-DEVPL-HISTORICAL-REGRESSION-GUARD-REPORT-V1" for item in catalog["schemas"])
    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert {
        "SCHEMA-DEVPL-HISTORICAL-REGRESSION-GUARD-REPORT-V1",
        "POST-H-029-E-HISTORICAL-REGRESSION-GUARD-MODULE",
        "POST-H-029-E-HISTORICAL-REGRESSION-GUARD-REPORT",
        "POST-H-029-E-MANIFEST",
        "POST-H-029-E-HISTORICAL-REGRESSION-GUARD-TEST",
    } <= doc_ids
    assert any(item["contract_id"] == "post-h-029-historical-regression-guard" for item in tcr_v1["contracts"])
    v2_contract = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-029-historical-regression-guard")
    assert v2_contract["subgate_id"] == "testing-tiers-ready"
    assert "SCHEMA-DEVPL-HISTORICAL-REGRESSION-GUARD-REPORT-V1" in v2_contract["schema_ids"]
    assert "POST-H-029-E — Historical regression guard" in readme
    assert "POST-H-029-E — Historical regression guard" in runbook
    assert "HistoricalRegressionGuardReport" in test_strategy
    assert "HistoricalRegressionGuardReport" in tcr_design
    assert "post-h-029-e" in changelog
    assert 'implementation_status: "closed/testing-tiers-ready"' in backlog
