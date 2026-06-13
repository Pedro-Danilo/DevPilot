from __future__ import annotations

import sqlite3
from pathlib import Path

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling import ModelAdapterRouter
from devpilot_core.observability import MetricRecord, MetricsCollector, TraceContext
from devpilot_core.store import LocalStore, SCHEMA_VERSION


def test_metric_record_serializes_and_redacts_sensitive_payload() -> None:
    metric = MetricRecord(
        name="devpilot.command.completed_total",
        value=1,
        unit="count",
        category="command",
        operation="completed_total",
        status="PASS",
        ok=True,
        metadata={"prompt": "do not store", "api_key": "sk-secret", "safe": "ok"},
    )

    payload = metric.to_dict()

    assert payload["name"] == "devpilot.command.completed_total"
    assert payload["value"] == 1.0
    assert payload["metadata"]["safe"] == "ok"
    assert "do not store" not in str(payload)
    assert "sk-secret" not in str(payload)


def test_metrics_collector_persists_command_metrics_without_preinitialized_db(tmp_path: Path) -> None:
    result = CommandResult(
        command="validate all",
        ok=True,
        exit_code=ExitCode.PASS,
        message="Validation passed.",
        data={"summary": {"validations_passed": 2}},
        findings=[],
    )
    collector = MetricsCollector(tmp_path)

    metric_ids = collector.record_command_result(result, subject="docs", duration_ms=25.0)
    metrics = collector.list_metrics(category="command")
    summary = collector.summary()
    status = LocalStore(tmp_path).status()

    assert len(metric_ids) == 2
    assert status.data["summary"]["schema_version"] == SCHEMA_VERSION
    assert {metric["name"] for metric in metrics} >= {"devpilot.command.completed_total", "devpilot.command.completed.duration_ms"}
    assert summary["initialized"] is True
    assert summary["statuses"]["PASS"] == 1
    assert summary["operations_total"] == 1
    assert summary["categories"]["command"] >= 2


def test_metrics_collector_summarizes_agent_tool_and_model_metrics(tmp_path: Path) -> None:
    collector = MetricsCollector(tmp_path)
    context = TraceContext.start(command="agent run", trace_id="trace_metrics", run_id="run_metrics")
    model_result = CommandResult(
        command="model generate",
        ok=True,
        exit_code=ExitCode.PASS,
        message="Mock model completed.",
        data={"summary": {"provider": "mock", "model": "mock-deterministic-v1", "task": "generate", "tokens_estimated": 8, "cost_estimate_usd": 0.0, "external_api_used": False}},
        findings=[Finding(id="MODEL_ADAPTER_PASS", message="ok", severity=Severity.INFO)],
    )

    collector.record_agent_operation(agent_id="documentation.audit", operation="run_total", status="PASS", ok=True, duration_ms=10, trace_context=context)
    collector.record_tool_operation(tool_id="trace.append", operation="call_total", status="PASS", ok=True, trace_context=context)
    collector.record_model_result(model_result, provider="mock", model="mock-deterministic-v1", task="generate", trace_context=context)

    summary = collector.summary()
    metrics = collector.list_metrics(limit=20)

    assert summary["categories"]["agent"] == 2
    assert summary["categories"]["tool"] == 1
    assert summary["categories"]["model"] == 3
    assert summary["providers"]["mock"] == 3
    assert summary["estimated_cost_total_usd"] == 0.0
    assert summary["tokens_estimated_total"] == 8
    assert all(metric["trace_id"] == "trace_metrics" for metric in metrics if metric["category"] in {"agent", "tool", "model"})


def test_model_adapter_mock_records_model_metrics_best_effort(tmp_path: Path) -> None:
    result = ModelAdapterRouter(tmp_path).generate(prompt="hello", provider="mock")
    summary = MetricsCollector(tmp_path).summary()
    model_metrics = MetricsCollector(tmp_path).list_metrics(category="model")

    assert result.ok is True
    assert summary["providers"].get("mock", 0) >= 3
    assert summary["estimated_cost_total_usd"] == 0.0
    assert any(metric["name"] == "devpilot.model.calls_total" for metric in model_metrics)
    assert "hello" not in str(model_metrics)


def test_local_store_migrates_legacy_metrics_table(tmp_path: Path) -> None:
    db_path = tmp_path / ".devpilot" / "devpilot.db"
    db_path.parent.mkdir(parents=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
            CREATE TABLE metrics (
                metric_id TEXT PRIMARY KEY,
                trace_id TEXT,
                run_id TEXT,
                name TEXT NOT NULL,
                value REAL NOT NULL DEFAULT 0.0,
                unit TEXT,
                timestamp TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}'
            );
            """
        )

    collector = MetricsCollector(tmp_path)
    collector.record_count(category="command", operation="completed_total", status="PASS", ok=True, command="legacy")
    metrics = collector.list_metrics(category="command")
    summary = collector.summary()

    assert metrics[0]["category"] == "command"
    assert metrics[0]["operation"] == "completed_total"
    assert summary["statuses"]["PASS"] == 1
