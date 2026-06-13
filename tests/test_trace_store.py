from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from devpilot_core.observability import EventLogger, EventRecord, SpanStatus, TraceContext, TraceStore
from devpilot_core.store import LocalStore, SCHEMA_VERSION


def _events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_trace_store_persists_and_reads_span_and_event(tmp_path: Path) -> None:
    store = TraceStore(tmp_path)
    context = TraceContext.start(
        command="agent run smoke",
        trace_id="trace_58",
        run_id="run_58",
        root_span_id="span_root",
        clock=lambda: "2026-06-13T00:00:00Z",
    )
    span = context.child_span(
        name="Smoke child",
        span_type="trace.smoke",
        span_id="span_child",
        payload={"stage": "persist"},
        started_at="2026-06-13T00:00:01Z",
    ).finish(status=SpanStatus.OK, ended_at="2026-06-13T00:00:03Z")
    event = EventRecord(event_type="trace.smoke.completed", command="agent run smoke", status="PASS", ok=True, exit_code=0)

    span_id = store.record_span(span)
    event_id = store.record_event(event, trace_context=context, span=span)
    spans = store.list_spans(trace_id="trace_58")
    events = store.list_events(trace_id="trace_58")

    assert span_id == "span_child"
    assert event_id
    assert spans[0]["trace_id"] == "trace_58"
    assert spans[0]["span_id"] == "span_child"
    assert spans[0]["parent_span_id"] == "span_root"
    assert spans[0]["duration_ms"] == 2000
    assert spans[0]["payload"] == {"stage": "persist"}
    assert events[0]["trace_id"] == "trace_58"
    assert events[0]["span_id"] == "span_child"
    assert events[0]["run_id"] == "run_58"


def test_event_logger_v2_keeps_jsonl_compatibility_and_adds_trace_ids(tmp_path: Path) -> None:
    context = TraceContext.start(command="validate all", trace_id="trace_jsonl", run_id="run_jsonl", clock=lambda: "2026-06-13T00:00:00Z")
    logger = EventLogger(tmp_path)

    logger.emit(EventRecord(event_type="command.started", command="validate all"), trace_context=context)
    payload = _events(tmp_path / "outputs" / "traces" / "events.jsonl")[0]

    assert payload["event_type"] == "command.started"
    assert payload["trace_id"] == "trace_jsonl"
    assert payload["run_id"] == "run_jsonl"


def test_local_store_migrates_existing_events_table_with_trace_columns(tmp_path: Path) -> None:
    db_path = tmp_path / ".devpilot" / "devpilot.db"
    db_path.parent.mkdir(parents=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
            CREATE TABLE events (
                event_id TEXT PRIMARY KEY,
                run_id TEXT,
                event_type TEXT NOT NULL,
                command TEXT NOT NULL,
                status TEXT,
                ok INTEGER CHECK (ok IN (0, 1)),
                exit_code INTEGER,
                timestamp TEXT NOT NULL,
                subject TEXT,
                summary_json TEXT NOT NULL DEFAULT '{}',
                metadata_json TEXT NOT NULL DEFAULT '{}'
            );
            """
        )

    store = LocalStore(tmp_path)
    store.record_event(event_type="trace.migrated", command="migration", trace_id="trace_migrated", ok=True, exit_code=0)
    status = store.status()
    events = store.list_events(trace_id="trace_migrated")

    assert status.data["summary"]["schema_version"] == SCHEMA_VERSION
    assert {"spans", "metrics"}.issubset(set(status.data["tables"]))
    assert events[0]["trace_id"] == "trace_migrated"


def test_trace_store_smoke_helper_creates_correlated_records(tmp_path: Path) -> None:
    store = TraceStore(tmp_path)

    result = store.record_smoke_trace(command="trace smoke")
    trace_id = result["trace_context"]["trace_id"]

    assert store.list_spans(trace_id=trace_id)[0]["trace_id"] == trace_id
    assert store.list_events(trace_id=trace_id)[0]["trace_id"] == trace_id
