from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode
from devpilot_core.observability.tracing import TraceContext, utc_now_iso, sanitize_span_payload
from devpilot_core.store import DEFAULT_DB_PATH, LocalStore


@dataclass(frozen=True)
class MetricRecord:
    """Serializable local metric for DevPilot AgentOps observability.

    FUNC-SPRINT-59 keeps metrics intentionally simple, local-first and
    dependency-free. A metric is a bounded numeric observation plus safe labels;
    it must not contain raw prompts, completions, diffs, stdout/stderr, tokens or
    secrets in metadata. Aggregation and persistence are best-effort so metrics
    cannot alter the functional result of commands, agents, tools or models.
    """

    name: str
    value: float
    unit: str = "count"
    category: str = "command"
    metric_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    operation: str | None = None
    command: str | None = None
    status: str | None = None
    ok: bool | None = None
    severity: str = "info"
    provider: str | None = None
    model: str | None = None
    task: str | None = None
    trace_id: str | None = None
    run_id: str | None = None
    span_id: str | None = None
    timestamp: str = field(default_factory=utc_now_iso)
    estimated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a redacted JSON-serializable metric payload."""

        payload: dict[str, Any] = {
            "metric_id": self.metric_id,
            "name": self.name,
            "value": float(self.value),
            "unit": self.unit,
            "category": self.category,
            "severity": self.severity,
            "timestamp": self.timestamp,
            "estimated": self.estimated,
        }
        optional = {
            "operation": self.operation,
            "command": self.command,
            "status": self.status,
            "ok": self.ok,
            "provider": self.provider,
            "model": self.model,
            "task": self.task,
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "span_id": self.span_id,
            "metadata": sanitize_metric_metadata(self.metadata),
        }
        for key, value in optional.items():
            if value not in (None, {}, []):
                payload[key] = value
        return payload


def sanitize_metric_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Redact metric metadata using the span redaction policy."""

    if not metadata:
        return {}
    sanitized = sanitize_span_payload(metadata)
    return sanitized if isinstance(sanitized, dict) else {"value": sanitized}


class MetricsCollector:
    """Best-effort SQLite-backed local metrics collector.

    The collector is deliberately synchronous and minimal in Sprint 59. It gives
    DevPilot a stable API for recording command, agent, tool and model metrics
    before Sprint 60 instruments agent runtime internals. Failures are contained
    by CLI/router callers so metrics never become a functional dependency.
    """

    def __init__(self, root: Path, *, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.root = root.resolve()
        self.store = LocalStore(self.root, db_path=db_path)

    def record(self, metric: MetricRecord) -> str:
        """Persist one metric and return its metric_id."""

        return self.store.record_metric(metric)

    def record_count(
        self,
        *,
        category: str,
        operation: str,
        status: str | None = None,
        ok: bool | None = None,
        value: float = 1.0,
        unit: str = "count",
        command: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        task: str | None = None,
        trace_context: TraceContext | None = None,
        trace_id: str | None = None,
        run_id: str | None = None,
        span_id: str | None = None,
        estimated: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Record one count-style metric for a logical operation."""

        effective_trace_id = trace_id or (trace_context.trace_id if trace_context else None)
        effective_run_id = run_id or (trace_context.run_id if trace_context else None)
        metric = MetricRecord(
            name=f"devpilot.{category}.{operation}",
            value=float(value),
            unit=unit,
            category=category,
            operation=operation,
            command=command,
            status=status,
            ok=ok,
            provider=provider,
            model=model,
            task=task,
            trace_id=effective_trace_id,
            run_id=effective_run_id,
            span_id=span_id,
            estimated=estimated,
            metadata=metadata or {},
        )
        return self.record(metric)

    def record_duration(
        self,
        *,
        category: str,
        operation: str,
        duration_ms: float,
        status: str | None = None,
        ok: bool | None = None,
        command: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        task: str | None = None,
        trace_context: TraceContext | None = None,
        trace_id: str | None = None,
        run_id: str | None = None,
        span_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Record one duration metric in milliseconds."""

        effective_trace_id = trace_id or (trace_context.trace_id if trace_context else None)
        effective_run_id = run_id or (trace_context.run_id if trace_context else None)
        return self.record(
            MetricRecord(
                name=f"devpilot.{category}.{operation}.duration_ms",
                value=float(duration_ms),
                unit="ms",
                category=category,
                operation=operation,
                command=command,
                status=status,
                ok=ok,
                provider=provider,
                model=model,
                task=task,
                trace_id=effective_trace_id,
                run_id=effective_run_id,
                span_id=span_id,
                metadata=metadata or {},
            )
        )

    def record_command_result(
        self,
        result: CommandResult,
        *,
        subject: str | Path | None = None,
        trace_context: TraceContext | None = None,
        duration_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        """Record bounded metrics for one normalized command result."""

        status = _status_from_command_result(result)
        payload = {"subject": str(subject).replace("\\", "/") if subject is not None else None, **(metadata or {})}
        metric_ids = [
            self.record_count(
                category="command",
                operation="completed_total",
                command=result.command,
                status=status,
                ok=result.ok,
                trace_context=trace_context,
                metadata=payload,
            )
        ]
        if duration_ms is not None:
            metric_ids.append(
                self.record_duration(
                    category="command",
                    operation="completed",
                    duration_ms=duration_ms,
                    command=result.command,
                    status=status,
                    ok=result.ok,
                    trace_context=trace_context,
                    metadata=payload,
                )
            )
        return metric_ids

    def record_agent_operation(
        self,
        *,
        agent_id: str,
        operation: str,
        status: str,
        ok: bool,
        duration_ms: float | None = None,
        trace_context: TraceContext | None = None,
        span_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        """Record metrics for an agent-level operation without runtime coupling."""

        metadata_payload = {"agent_id": agent_id, **(metadata or {})}
        ids = [
            self.record_count(
                category="agent",
                operation=operation,
                status=status,
                ok=ok,
                trace_context=trace_context,
                span_id=span_id,
                metadata=metadata_payload,
            )
        ]
        if duration_ms is not None:
            ids.append(
                self.record_duration(
                    category="agent",
                    operation=operation,
                    duration_ms=duration_ms,
                    status=status,
                    ok=ok,
                    trace_context=trace_context,
                    span_id=span_id,
                    metadata=metadata_payload,
                )
            )
        return ids

    def record_tool_operation(
        self,
        *,
        tool_id: str,
        operation: str,
        status: str,
        ok: bool,
        duration_ms: float | None = None,
        trace_context: TraceContext | None = None,
        span_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        """Record metrics for a tool operation without executing the tool."""

        metadata_payload = {"tool_id": tool_id, **(metadata or {})}
        ids = [
            self.record_count(
                category="tool",
                operation=operation,
                status=status,
                ok=ok,
                trace_context=trace_context,
                span_id=span_id,
                metadata=metadata_payload,
            )
        ]
        if duration_ms is not None:
            ids.append(
                self.record_duration(
                    category="tool",
                    operation=operation,
                    duration_ms=duration_ms,
                    status=status,
                    ok=ok,
                    trace_context=trace_context,
                    span_id=span_id,
                    metadata=metadata_payload,
                )
            )
        return ids

    def record_model_result(
        self,
        result: CommandResult,
        *,
        provider: str | None = None,
        model: str | None = None,
        task: str | None = None,
        trace_context: TraceContext | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        """Record local model metrics from a sanitized CommandResult."""

        summary = (result.data or {}).get("summary") if isinstance(result.data, dict) else {}
        summary = summary if isinstance(summary, dict) else {}
        provider_id = provider or str(summary.get("provider") or "unknown")
        model_id = model or (str(summary.get("model")) if summary.get("model") else None)
        task_id = task or (str(summary.get("task")) if summary.get("task") else result.command.replace("model ", ""))
        status = _status_from_command_result(result)
        metadata_payload = {
            "source_command": result.command,
            "external_api_used": bool(summary.get("external_api_used", False)),
            "llm_required": bool(summary.get("llm_required", provider_id != "mock")),
            **(metadata or {}),
        }
        ids = [
            self.record_count(
                category="model",
                operation="calls_total",
                status=status,
                ok=result.ok,
                provider=provider_id,
                model=model_id,
                task=task_id,
                trace_context=trace_context,
                estimated=True,
                metadata=metadata_payload,
            )
        ]
        tokens = summary.get("tokens_estimated")
        if tokens is not None:
            ids.append(
                self.record(
                    MetricRecord(
                        name="devpilot.model.tokens_estimated",
                        value=float(tokens or 0),
                        unit="tokens",
                        category="model",
                        operation="tokens_estimated",
                        status=status,
                        ok=result.ok,
                        provider=provider_id,
                        model=model_id,
                        task=task_id,
                        trace_id=trace_context.trace_id if trace_context else None,
                        run_id=trace_context.run_id if trace_context else None,
                        estimated=True,
                        metadata=metadata_payload,
                    )
                )
            )
        if "cost_estimate_usd" in summary:
            ids.append(
                self.record(
                    MetricRecord(
                        name="devpilot.model.cost_estimate_usd",
                        value=float(summary.get("cost_estimate_usd") or 0.0),
                        unit="usd",
                        category="model",
                        operation="cost_estimate_usd",
                        status=status,
                        ok=result.ok,
                        provider=provider_id,
                        model=model_id,
                        task=task_id,
                        trace_id=trace_context.trace_id if trace_context else None,
                        run_id=trace_context.run_id if trace_context else None,
                        estimated=True,
                        metadata=metadata_payload,
                    )
                )
            )
        return ids

    def list_metrics(self, *, category: str | None = None, name: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent metric records."""

        return self.store.list_metrics(category=category, name=name, limit=limit)

    def summary(self) -> dict[str, Any]:
        """Return aggregate local metrics summary."""

        return self.store.metrics_summary()


def _status_from_command_result(result: CommandResult) -> str:
    if result.ok:
        return "PASS"
    if int(result.exit_code) == int(ExitCode.BLOCK):
        return "BLOCK"
    if int(result.exit_code) == int(ExitCode.ERROR):
        return "ERROR"
    return "FAIL"
