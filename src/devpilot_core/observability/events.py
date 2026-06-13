from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult
from devpilot_core.observability.tracing import SpanRecord, TraceContext

DEFAULT_EVENTS_PATH = "outputs/traces/events.jsonl"

from devpilot_core.policy import REDACTED, SecretGuard, redact_sensitive_data as _policy_redact_sensitive_data, redact_string as _policy_redact_string


def utc_now_iso() -> str:
    """Return a second-resolution UTC timestamp for deterministic event shape."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class EventRecord:
    """Serializable JSONL event emitted by DevPilot local observability.

    This is the initial FUNC-SPRINT-07 event contract. It is intentionally
    compact: enough to reconstruct what command/gate ran, whether it passed,
    what findings were produced and which safe metadata accompanied the event.
    The payload is redacted before persistence so synthetic secrets do not leak
    into `outputs/traces/events.jsonl`.
    """

    event_type: str
    command: str
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: str = field(default_factory=utc_now_iso)
    level: str = "info"
    status: str | None = None
    ok: bool | None = None
    exit_code: int | None = None
    message: str | None = None
    subject: str | None = None
    trace_id: str | None = None
    run_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)
    findings: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable event dictionary without empty fields."""

        payload: dict[str, Any] = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "level": self.level,
            "command": self.command,
        }
        optional_values = {
            "status": self.status,
            "ok": self.ok,
            "exit_code": self.exit_code,
            "message": self.message,
            "subject": self.subject,
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "summary": self.summary,
            "findings": self.findings,
            "metadata": self.metadata,
        }
        for key, value in optional_values.items():
            if value not in (None, {}, []):
                payload[key] = value
        return payload


@dataclass(frozen=True)
class EventWriteResult:
    """Path information returned after appending an event."""

    path: str
    event_id: str
    event_type: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "event_id": self.event_id, "event_type": self.event_type}


class EventLogger:
    """Append-only local JSONL event logger.

    The logger writes only under the DevPilot project root. Its default target
    is `outputs/traces/events.jsonl`. It is local-first, dependency-free and
    suitable for command/gate observability before the future SQLite/EventStore
    sprint exists.
    """

    def __init__(self, root: Path, *, events_path: str | Path = DEFAULT_EVENTS_PATH) -> None:
        self.root = root.resolve()
        self.events_path = self._resolve_events_path(events_path)

    def emit(
        self,
        event: EventRecord,
        *,
        trace_context: TraceContext | None = None,
        span: SpanRecord | None = None,
    ) -> EventWriteResult:
        """Append one redacted event as a single JSONL line.

        The optional trace/span arguments are the FUNC-SPRINT-58 v2 extension.
        Existing callers can still pass only EventRecord and get the historical
        JSONL behavior.
        """

        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        payload = event.to_dict()
        if trace_context is not None:
            payload.setdefault("trace_id", trace_context.trace_id)
            payload.setdefault("run_id", trace_context.run_id)
        if span is not None:
            payload.setdefault("trace_id", span.trace_id)
            if span.run_id:
                payload.setdefault("run_id", span.run_id)
            payload.setdefault("span_id", span.span_id)
            if span.parent_span_id:
                payload.setdefault("parent_span_id", span.parent_span_id)
        payload = redact_sensitive_data(payload)
        with self.events_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            file.write("\n")
        return EventWriteResult(
            path=_relative(self.events_path, self.root), event_id=str(payload["event_id"]), event_type=str(payload["event_type"])
        )

    def emit_started(
        self,
        command: str,
        *,
        argv: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        trace_context: TraceContext | None = None,
    ) -> EventWriteResult:
        """Emit a command.started event before command dispatch."""

        return self.emit(
            EventRecord(
                event_type="command.started",
                command=command,
                message="Command execution started.",
                metadata={"argv": argv or [], **(metadata or {})},
            ),
            trace_context=trace_context,
        )

    def emit_completed(
        self,
        command: str,
        *,
        exit_code: int,
        ok: bool,
        message: str = "Command execution completed.",
        metadata: dict[str, Any] | None = None,
        trace_context: TraceContext | None = None,
    ) -> EventWriteResult:
        """Emit a command.completed event after command dispatch."""

        return self.emit(
            EventRecord(
                event_type="command.completed",
                command=command,
                status="PASS" if ok else "FAIL",
                ok=ok,
                exit_code=exit_code,
                message=message,
                metadata=metadata or {},
            ),
            trace_context=trace_context,
        )

    def emit_error(
        self,
        command: str,
        *,
        error: Exception,
        exit_code: int,
        metadata: dict[str, Any] | None = None,
        trace_context: TraceContext | None = None,
    ) -> EventWriteResult:
        """Emit a command.error event for handled CLI exceptions."""

        return self.emit(
            EventRecord(
                event_type="command.error",
                command=command,
                level="error",
                status="ERROR",
                ok=False,
                exit_code=exit_code,
                message=str(error),
                metadata=metadata or {},
            ),
            trace_context=trace_context,
        )

    def emit_result(
        self,
        result: CommandResult,
        *,
        event_type: str = "gate.evaluated",
        subject: str | Path | None = None,
        trace_context: TraceContext | None = None,
        span: SpanRecord | None = None,
    ) -> EventWriteResult:
        """Emit a result-derived event for gates and validators."""

        return self.emit(
            event_from_command_result(result, event_type=event_type, subject=subject, trace_context=trace_context, span=span),
            trace_context=trace_context,
            span=span,
        )

    def _resolve_events_path(self, events_path: str | Path) -> Path:
        candidate = Path(events_path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("EventLogger only writes inside the DevPilot project root.") from exc
        return candidate


def event_from_command_result(
    result: CommandResult,
    *,
    event_type: str = "gate.evaluated",
    subject: str | Path | None = None,
    trace_context: TraceContext | None = None,
    span: SpanRecord | None = None,
) -> EventRecord:
    """Build a compact event from the common CLI `CommandResult`."""

    status = "PASS" if result.ok else _status_from_exit_code(int(result.exit_code))
    data = result.data or {}
    return EventRecord(
        event_type=event_type,
        command=result.command,
        status=status,
        ok=result.ok,
        exit_code=int(result.exit_code),
        message=result.message,
        subject=str(subject).replace("\\", "/") if subject is not None else None,
        trace_id=trace_context.trace_id if trace_context else (span.trace_id if span else None),
        run_id=trace_context.run_id if trace_context else (span.run_id if span else None),
        span_id=span.span_id if span else None,
        parent_span_id=span.parent_span_id if span else None,
        summary=summarize_command_data(data),
        findings=[finding.to_dict() for finding in result.findings],
        metadata={"findings_total": len(result.findings)},
    )


def summarize_command_data(data: dict[str, Any]) -> dict[str, Any]:
    """Return a bounded summary for event metadata, not full command payload."""

    if isinstance(data.get("summary"), dict):
        return dict(data["summary"])

    summary: dict[str, Any] = {}
    for key in ("strict", "ok", "path", "status", "has_frontmatter", "heading_count", "h1_count"):
        if key in data:
            summary[key] = data[key]
    if isinstance(data.get("checks"), list):
        summary["checks_total"] = len(data["checks"])
    if isinstance(data.get("artifacts"), list):
        summary["artifacts_total"] = len(data["artifacts"])
    if isinstance(data.get("standards"), list):
        summary["standards_total"] = len(data["standards"])
    if isinstance(data.get("reports"), dict):
        summary["reports"] = data["reports"]
    return summary


def redact_sensitive_data(value: Any) -> Any:
    """Recursively redact synthetic secrets using SecretGuard.

    Kept as a compatibility wrapper for FUNC-SPRINT-07 tests and callers.
    FUNC-SPRINT-09 centralizes the implementation in `devpilot_core.policy`.
    """

    return _policy_redact_sensitive_data(value)


def redact_sensitive_string(value: str) -> str:
    """Redact known token patterns in strings.

    Kept as a compatibility wrapper. New code should use SecretGuard directly.
    """

    return _policy_redact_string(value)


def _status_from_exit_code(exit_code: int) -> str:
    if exit_code == 2:
        return "BLOCK"
    if exit_code == 3:
        return "ERROR"
    return "FAIL"


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
