from __future__ import annotations

import json
from pathlib import Path

import pytest

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.observability import MetricsCollector, TraceContext, TraceStore
from devpilot_core.observability.exporters import OTelDryRunExporter, OTelExportOptions


def _payload(capsys: pytest.CaptureFixture[str]) -> dict:
    return json.loads(capsys.readouterr().out)


def test_telemetry_export_generates_local_otlp_like_payload_and_reports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    smoke = TraceStore(tmp_path).record_smoke_trace(command="otel smoke")
    trace_context = TraceContext.start(trace_id=smoke["trace_context"]["trace_id"], command="otel smoke")
    MetricsCollector(tmp_path).record_agent_operation(
        agent_id="agent.otel.demo",
        operation="run_total",
        status="PASS",
        ok=True,
        trace_context=trace_context,
    )

    exit_code = cli.main(["telemetry", "export", "--format", "otlp", "--dry-run", "--json", "--write-report"])
    payload = _payload(capsys)

    assert exit_code == 0
    assert payload["command"] == "telemetry export"
    assert payload["ok"] is True
    summary = payload["data"]["summary"]
    assert summary["dry_run"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["remote_telemetry_enabled"] is False
    assert summary["collector_required"] is False
    assert summary["spans_exported"] >= 1
    assert payload["data"]["payload_kind"] == "otlp-json-dry-run"
    assert payload["data"]["payload"]["resourceSpans"][0]["scopeSpans"][0]["spans"]
    assert payload["data"]["reports"]["json"] == "outputs/reports/telemetry_export_otel_dry_run.json"
    assert (tmp_path / "outputs" / "reports" / "telemetry_export_otel_dry_run.md").is_file()


def test_telemetry_export_blocks_remote_endpoint_without_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main([
        "telemetry",
        "export",
        "--format",
        "otlp",
        "--dry-run",
        "--endpoint",
        "https://collector.example/v1/traces",
        "--json",
    ])
    payload = _payload(capsys)

    assert exit_code == int(ExitCode.BLOCK)
    assert payload["ok"] is False
    assert payload["data"]["summary"]["network_used"] is False
    assert payload["data"]["summary"]["external_api_used"] is False
    assert payload["data"]["summary"]["remote_telemetry_enabled"] is False
    assert any(finding["id"] == "OTEL_REMOTE_EXPORT_BLOCKED" for finding in payload["findings"])


def test_otel_exporter_service_blocks_non_dry_run_mode(tmp_path: Path) -> None:
    result = OTelDryRunExporter(tmp_path).export(OTelExportOptions(dry_run=False))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["network_used"] is False
    assert result.data["summary"]["external_api_used"] is False


def test_telemetry_export_redacts_sensitive_payload_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    context = TraceContext.start(command="sensitive otel", trace_id="trace_sensitive_otel")
    span = context.child_span(
        name="model:mock:generate",
        span_type="model.call",
        subject="mock",
        payload={"api_key": "sk-secret-value", "prompt": "raw prompt should not be exported"},
        metadata={"token": "token-secret-value", "provider": "mock", "model": "mock-deterministic-v1"},
    ).finish()
    TraceStore(tmp_path).record_span(span)

    exit_code = cli.main(["telemetry", "export", "--trace-id", "trace_sensitive_otel", "--json"])
    payload = _payload(capsys)
    rendered = json.dumps(payload, ensure_ascii=False)

    assert exit_code == 0
    assert "sk-secret-value" not in rendered
    assert "raw prompt should not be exported" not in rendered
    assert "token-secret-value" not in rendered
    assert payload["data"]["summary"]["payload_redacted"] is True
