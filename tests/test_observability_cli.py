from __future__ import annotations

import json
from pathlib import Path

import pytest

from devpilot_core import cli
from devpilot_core.observability import MetricsCollector, TraceContext, TraceStore


def _payload(capsys: pytest.CaptureFixture[str]) -> dict:
    return json.loads(capsys.readouterr().out)


def test_trace_report_empty_workspace_is_json_parseable_and_writes_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["trace", "report", "--json", "--write-report"])
    payload = _payload(capsys)

    assert exit_code == 0
    assert payload["command"] == "trace report"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["traces_total"] == 0
    assert payload["data"]["reports"]["json"] == "outputs/reports/trace_report.json"
    assert (tmp_path / "outputs" / "reports" / "trace_report.json").is_file()
    assert (tmp_path / "outputs" / "reports" / "trace_report.md").is_file()
    assert any(finding["id"] == "TRACE_REPORT_EMPTY" for finding in payload["findings"])


def test_trace_report_and_inspect_return_tree_for_existing_trace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    smoke = TraceStore(tmp_path).record_smoke_trace(command="test trace smoke")
    trace_id = smoke["trace_context"]["trace_id"]

    report_exit = cli.main(["trace", "report", "--json", "--limit", "5"])
    report_payload = _payload(capsys)
    inspect_exit = cli.main(["trace", "inspect", trace_id, "--json"])
    inspect_payload = _payload(capsys)

    assert report_exit == 0
    assert inspect_exit == 0
    assert report_payload["data"]["summary"]["traces_total"] >= 1
    assert any(trace["trace_id"] == trace_id for trace in report_payload["data"]["traces"])
    assert inspect_payload["command"] == "trace inspect"
    assert inspect_payload["data"]["summary"]["found"] is True
    assert inspect_payload["data"]["summary"]["spans_total"] == 1
    assert inspect_payload["data"]["tree"][0]["span_type"] == "trace.smoke"


def test_trace_inspect_unknown_trace_is_controlled_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["trace", "inspect", "trace_missing", "--json"])
    payload = _payload(capsys)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["found"] is False
    assert payload["data"]["tree"] == []
    assert any(finding["id"] == "TRACE_NOT_FOUND" for finding in payload["findings"])


def test_metrics_summary_aggregates_local_metrics_and_writes_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    trace_context = TraceContext.start(command="test metrics")
    MetricsCollector(tmp_path).record_agent_operation(
        agent_id="agent.demo",
        operation="runs_total",
        status="PASS",
        ok=True,
        duration_ms=12,
        trace_context=trace_context,
    )

    exit_code = cli.main(["metrics", "summary", "--category", "agent", "--json", "--write-report"])
    payload = _payload(capsys)

    assert exit_code == 0
    assert payload["command"] == "metrics summary"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["metrics_total"] >= 2
    assert payload["data"]["summary"]["filter_category"] == "agent"
    assert payload["data"]["summary"]["recent_categories"]["agent"] >= 2
    assert payload["data"]["reports"]["json"] == "outputs/reports/metrics_summary.json"
    assert (tmp_path / "outputs" / "reports" / "metrics_summary.md").is_file()
