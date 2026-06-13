from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from devpilot_core.cli_models import Finding
from devpilot_core.policy import REDACTED, redact_sensitive_data, redact_string

IdFactory = Callable[[], str]
Clock = Callable[[], str]

_SPAN_PAYLOAD_REDACT_KEYS = {
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "id_token",
    "auth_token",
    "authorization",
    "bearer",
    "client_secret",
    "connection_string",
    "database_url",
    "password",
    "passwd",
    "private_key",
    "pwd",
    "secret",
    "token",
}

# These keys are not necessarily secrets, but they often contain large or sensitive
# payloads. FUNC-SPRINT-57 deliberately stores observability metadata, not raw
# prompts, completions, patches or process output.
_RAW_PAYLOAD_REDACT_KEYS = {
    "completion",
    "completion_text",
    "content",
    "diff",
    "full_diff",
    "input_text",
    "output",
    "output_text",
    "patch",
    "patch_text",
    "prompt",
    "prompt_text",
    "raw_completion",
    "raw_diff",
    "raw_input",
    "raw_output",
    "stderr",
    "stdout",
}

_ALLOWED_LARGE_TEXT_KEYS = {
    "command",
    "event_type",
    "id",
    "message",
    "model",
    "name",
    "provider",
    "reason",
    "span_type",
    "status",
    "subject",
    "title",
}

_MAX_SAFE_STRING_LENGTH = 500


def utc_now_iso() -> str:
    """Return a UTC ISO-8601 timestamp suitable for trace/span records."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class SpanStatus(str, Enum):
    """Lifecycle/status values for DevPilot v2 spans.

    These values are intentionally small and independent from OpenTelemetry.
    A future exporter may map them to OTel status codes, but the internal
    contract remains local-first and dependency-free.
    """

    STARTED = "started"
    OK = "ok"
    FAIL = "fail"
    BLOCK = "block"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class TraceContext:
    """Correlation context for one DevPilot command/run.

    FUNC-SPRINT-57 introduces this as an internal, serializable contract only.
    Persistence, querying and CLI inspection are intentionally left to later
    Fase E sprints. The context carries identifiers that future command,
    agent, tool, policy and model spans can share.
    """

    trace_id: str = field(default_factory=lambda: new_trace_id())
    run_id: str = field(default_factory=lambda: new_run_id())
    command: str | None = None
    root_span_id: str | None = None
    agent_run_id: str | None = None
    started_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def start(
        cls,
        *,
        command: str | None = None,
        trace_id: str | None = None,
        run_id: str | None = None,
        root_span_id: str | None = None,
        agent_run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        id_factory: IdFactory | None = None,
        clock: Clock = utc_now_iso,
    ) -> "TraceContext":
        """Create a trace context with injectable ids/clock for tests."""

        return cls(
            trace_id=trace_id or new_trace_id(id_factory),
            run_id=run_id or new_run_id(id_factory),
            command=command,
            root_span_id=root_span_id,
            agent_run_id=agent_run_id,
            started_at=clock(),
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a redacted JSON-serializable trace context."""

        payload: dict[str, Any] = {
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "started_at": self.started_at,
        }
        optional = {
            "command": self.command,
            "root_span_id": self.root_span_id,
            "agent_run_id": self.agent_run_id,
            "metadata": sanitize_span_payload(self.metadata),
        }
        for key, value in optional.items():
            if value not in (None, {}, []):
                payload[key] = value
        return payload

    def child_span(
        self,
        *,
        name: str,
        span_type: str,
        parent_span_id: str | None = None,
        span_id: str | None = None,
        status: SpanStatus | str = SpanStatus.STARTED,
        severity: str = "info",
        subject: str | None = None,
        payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        findings: list[Finding | dict[str, Any]] | None = None,
        started_at: str | None = None,
        id_factory: IdFactory | None = None,
        clock: Clock = utc_now_iso,
    ) -> "SpanRecord":
        """Create a child span linked to this context."""

        return SpanRecord(
            trace_id=self.trace_id,
            run_id=self.run_id,
            span_id=span_id or new_span_id(id_factory),
            parent_span_id=parent_span_id or self.root_span_id,
            name=name,
            span_type=span_type,
            status=_normalize_status(status),
            severity=severity,
            subject=subject,
            payload=payload or {},
            metadata={"command": self.command, **(metadata or {})} if self.command else (metadata or {}),
            findings=findings or [],
            started_at=started_at or clock(),
        )


@dataclass(frozen=True)
class SpanRecord:
    """Serializable record for one operation inside a trace.

    A span represents a bounded operation such as a command stage, agent run,
    tool call, policy decision or model call. It deliberately stores redacted
    metadata and summaries rather than raw prompts, completions, diffs or
    process output.
    """

    trace_id: str
    span_id: str
    name: str
    span_type: str
    run_id: str | None = None
    parent_span_id: str | None = None
    status: SpanStatus = SpanStatus.STARTED
    severity: str = "info"
    subject: str | None = None
    started_at: str = field(default_factory=utc_now_iso)
    ended_at: str | None = None
    duration_ms: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    findings: list[Finding | dict[str, Any]] = field(default_factory=list)

    def finish(
        self,
        *,
        status: SpanStatus | str = SpanStatus.OK,
        ended_at: str | None = None,
        duration_ms: int | None = None,
        severity: str | None = None,
        payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        findings: list[Finding | dict[str, Any]] | None = None,
        clock: Clock = utc_now_iso,
    ) -> "SpanRecord":
        """Return a completed copy of the span."""

        final_ended_at = ended_at or clock()
        final_duration = duration_ms if duration_ms is not None else _duration_ms(self.started_at, final_ended_at)
        return replace(
            self,
            status=_normalize_status(status),
            ended_at=final_ended_at,
            duration_ms=final_duration,
            severity=severity or self.severity,
            payload={**self.payload, **(payload or {})},
            metadata={**self.metadata, **(metadata or {})},
            findings=findings if findings is not None else self.findings,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a redacted JSON-serializable span dictionary."""

        payload: dict[str, Any] = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "name": self.name,
            "span_type": self.span_type,
            "status": self.status.value,
            "severity": self.severity,
            "started_at": self.started_at,
        }
        optional = {
            "run_id": self.run_id,
            "parent_span_id": self.parent_span_id,
            "subject": self.subject,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "payload": sanitize_span_payload(self.payload),
            "metadata": sanitize_span_payload(self.metadata),
            "findings": sanitize_span_payload([_finding_to_dict(item) for item in self.findings]),
        }
        for key, value in optional.items():
            if value not in (None, {}, []):
                payload[key] = value
        return payload


def new_trace_id(id_factory: IdFactory | None = None) -> str:
    """Generate a trace id with a stable DevPilot prefix."""

    return _new_prefixed_id("trace", id_factory)


def new_span_id(id_factory: IdFactory | None = None) -> str:
    """Generate a span id with a stable DevPilot prefix."""

    return _new_prefixed_id("span", id_factory)


def new_run_id(id_factory: IdFactory | None = None) -> str:
    """Generate a run id with a stable DevPilot prefix."""

    return _new_prefixed_id("run", id_factory)


def sanitize_span_payload(value: Any) -> Any:
    """Redact span payloads before serialization or future persistence.

    The function applies two layers:
    1. a span-specific denylist for raw prompts/completions/diffs/output;
    2. SecretGuard-compatible recursive redaction for token-like values.
    """

    sanitized = _sanitize_by_key_policy(value)
    return redact_sensitive_data(sanitized)


def _new_prefixed_id(prefix: str, id_factory: IdFactory | None = None) -> str:
    raw = id_factory() if id_factory else uuid.uuid4().hex
    raw = str(raw).strip()
    if raw.startswith(f"{prefix}_"):
        return raw
    return f"{prefix}_{raw}"


def _normalize_status(status: SpanStatus | str) -> SpanStatus:
    if isinstance(status, SpanStatus):
        return status
    return SpanStatus(str(status))


def _sanitize_by_key_policy(value: Any, *, key: str | None = None) -> Any:
    if key is not None:
        normalized_key = key.lower().replace("-", "_").strip()
        if normalized_key in _SPAN_PAYLOAD_REDACT_KEYS or normalized_key in _RAW_PAYLOAD_REDACT_KEYS:
            return REDACTED
    if isinstance(value, dict):
        return {item_key: _sanitize_by_key_policy(item_value, key=str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [_sanitize_by_key_policy(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_by_key_policy(item) for item in value]
    if isinstance(value, str):
        redacted = redact_string(value)
        if key not in _ALLOWED_LARGE_TEXT_KEYS and len(redacted) > _MAX_SAFE_STRING_LENGTH:
            return f"{redacted[:_MAX_SAFE_STRING_LENGTH]}...[TRUNCATED length={len(redacted)}]"
        return redacted
    return value


def _finding_to_dict(value: Finding | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, Finding):
        return value.to_dict()
    return dict(value)


def _duration_ms(started_at: str, ended_at: str) -> int | None:
    try:
        start = _parse_iso_z(started_at)
        end = _parse_iso_z(ended_at)
    except ValueError:
        return None
    return max(0, int((end - start).total_seconds() * 1000))


def _parse_iso_z(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)
