from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.observability.events import EventRecord
from devpilot_core.observability.tracing import SpanRecord, SpanStatus, TraceContext
from devpilot_core.store import DEFAULT_DB_PATH, LocalStore


class TraceStore:
    """SQLite-backed trace/span/event projection store.

    FUNC-SPRINT-58 introduces this as a thin observability facade over
    LocalStore. JSONL remains the append-only evidence log; TraceStore provides
    structured, query-friendly persistence for spans and trace-correlated event
    projections. It does not implement metrics aggregation or CLI trace reports;
    those are planned for later Fase E sprints.
    """

    def __init__(self, root: Path, *, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.root = root.resolve()
        self.store = LocalStore(self.root, db_path=db_path)

    def initialize(self) -> None:
        """Ensure the underlying LocalStore schema exists."""

        self.store.initialize()

    def record_span(self, span: SpanRecord) -> str:
        """Persist one redacted span and return its span id."""

        return self.store.record_span(span)

    def record_event(
        self,
        event: EventRecord,
        *,
        trace_context: TraceContext | None = None,
        span: SpanRecord | None = None,
    ) -> str:
        """Persist one event projection with optional trace/span correlation."""

        payload = event.to_dict()
        context_trace_id = trace_context.trace_id if trace_context else None
        context_run_id = trace_context.run_id if trace_context else None
        return self.store.record_event(
            event_type=str(payload["event_type"]),
            command=str(payload["command"]),
            status=payload.get("status"),
            ok=payload.get("ok"),
            exit_code=payload.get("exit_code"),
            subject=payload.get("subject"),
            summary=payload.get("summary") if isinstance(payload.get("summary"), dict) else {},
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
            run_id=payload.get("run_id") or context_run_id,
            trace_id=payload.get("trace_id") or context_trace_id,
            span_id=payload.get("span_id") or (span.span_id if span else None),
            parent_span_id=payload.get("parent_span_id") or (span.parent_span_id if span else None),
        )

    def list_spans(self, *, trace_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """Return persisted spans, optionally scoped by trace id."""

        return self.store.list_spans(trace_id=trace_id, limit=limit)

    def list_events(self, *, trace_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """Return persisted event projections, optionally scoped by trace id."""

        return self.store.list_events(trace_id=trace_id, limit=limit)

    def record_smoke_trace(self, *, command: str = "trace smoke") -> dict[str, Any]:
        """Create a minimal local trace for migration/smoke testing.

        This helper is intentionally not exposed as public CLI yet. It gives
        tests and future commands a deterministic way to verify that spans and
        events can be persisted together without requiring agents, tools or
        model calls.
        """

        context = TraceContext.start(command=command)
        span = context.child_span(name="TraceStore smoke", span_type="trace.smoke", payload={"stage": "smoke"}).finish(
            status=SpanStatus.OK,
            payload={"result": "ok"},
        )
        event = EventRecord(
            event_type="trace.smoke.completed",
            command=command,
            status="PASS",
            ok=True,
            exit_code=0,
            summary={"spans_total": 1},
        )
        span_id = self.record_span(span)
        event_id = self.record_event(event, trace_context=context, span=span)
        return {"trace_context": context.to_dict(), "span_id": span_id, "event_id": event_id}
