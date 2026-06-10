from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.traceability import TraceabilityEngine
from devpilot_core.traceability.reports import build_traceability_markdown_summary

ROOT = Path(__file__).resolve().parents[1]


def test_traceability_engine_complete_fixture_has_full_coverage() -> None:
    fixture = ROOT / "tests/fixtures/traceability_engine/complete.md"

    result = TraceabilityEngine(ROOT).coverage(targets=[fixture])

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["requirements_total"] == 2
    assert summary["requirements_without_acceptance_criteria"] == 0
    assert summary["requirements_without_test_or_eval_evidence"] == 0
    assert summary["coverage_percentages"]["requirements_acceptance_criteria"] == 100.0
    assert summary["coverage_percentages"]["requirements_test_or_eval"] == 100.0


def test_traceability_engine_incomplete_fixture_reports_non_blocking_gaps() -> None:
    fixture = ROOT / "tests/fixtures/traceability_engine/incomplete.md"

    result = TraceabilityEngine(ROOT).validate(targets=[fixture])

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    finding_ids = {finding.id for finding in result.findings}
    assert "TRACEABILITY_REQUIREMENT_WITHOUT_ACCEPTANCE_CRITERIA" in finding_ids
    assert "TRACEABILITY_REQUIREMENT_WITHOUT_TEST_EVIDENCE" in finding_ids
    assert "TRACEABILITY_ACCEPTANCE_CRITERION_WITHOUT_REQUIREMENT" in finding_ids
    assert result.data["summary"]["blocking_findings_total"] == 0


def test_traceability_engine_real_docs_generates_coverage_metrics() -> None:
    result = TraceabilityEngine(ROOT).coverage()

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["requirements_total"] >= 1
    assert summary["requirements_with_acceptance_criteria"] >= 1
    assert summary["requirements_with_test_or_eval_evidence"] >= 1
    assert summary["links_total"] >= 1
    assert "coverage_percentages" in summary


def test_traceability_report_payload_is_reproducible() -> None:
    fixture = ROOT / "tests/fixtures/traceability_engine/complete.md"

    first = TraceabilityEngine(ROOT).report(targets=[fixture])
    second = TraceabilityEngine(ROOT).report(targets=[fixture])

    assert first.ok is True
    assert first.data["summary"] == second.data["summary"]
    assert first.data["coverage"] == second.data["coverage"]
    assert first.data["report"] == second.data["report"]


def test_traceability_report_summary_renderer_is_side_effect_free() -> None:
    fixture = ROOT / "tests/fixtures/traceability_engine/complete.md"
    result = TraceabilityEngine(ROOT).report(targets=[fixture])

    markdown = build_traceability_markdown_summary(result.data)

    assert "DevPilot Traceability Summary" in markdown
    assert "Requirements" in markdown
    assert "Gaps" in markdown


def test_traceability_validate_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["traceability", "validate", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "traceability validate"
    assert payload["ok"] is True
    assert "gaps_total" in payload["data"]["summary"]


def test_traceability_coverage_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["traceability", "coverage", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "traceability coverage"
    assert payload["data"]["summary"]["requirements_total"] >= 1


def test_traceability_report_cli_write_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    report_json = ROOT / "outputs/reports/traceability_report.json"
    report_md = ROOT / "outputs/reports/traceability_report.md"
    if report_json.exists():
        report_json.unlink()
    if report_md.exists():
        report_md.unlink()

    exit_code = cli.main(["traceability", "report", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "traceability report"
    assert payload["data"]["reports"] == {
        "json": "outputs/reports/traceability_report.json",
        "markdown": "outputs/reports/traceability_report.md",
    }
    assert report_json.exists()
    assert report_md.exists()
