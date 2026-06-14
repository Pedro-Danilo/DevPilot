from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.observability.metrics import MetricsCollector
from devpilot_core.observability.trace_store import TraceStore
from devpilot_core.policy import redact_sensitive_data
from devpilot_core.store import DEFAULT_DB_PATH


@dataclass(frozen=True)
class TraceReportOptions:
    """Query options for local trace reports.

    FUNC-SPRINT-61 keeps trace reporting dependency-free and bounded. The CLI
    can ask for recent traces without requiring a UI, an exporter or external
    telemetry infrastructure. Limits are capped to avoid overly large reports.
    """

    limit: int = 20
    include_events: bool = True
    include_metrics: bool = True


class TraceQueryService:
    """Read-only query facade for TraceStore and MetricsCollector.

    The service is intentionally separate from CLI parsing. It transforms local
    SQLite projections into bounded CommandResult payloads that are safe to emit
    as JSON and safe to persist with ReportEngine. It never writes spans,
    metrics or events by itself; optional report writing remains a CLI concern.
    """

    def __init__(self, root: Path, *, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.root = root.resolve()
        self.trace_store = TraceStore(self.root, db_path=db_path)
        self.metrics = MetricsCollector(self.root, db_path=db_path)

    def report(self, *, limit: int = 20, include_events: bool = True, include_metrics: bool = True) -> CommandResult:
        """Return a bounded report of recent traces.

        If the local SQLite database is empty or absent, the command still
        passes with an explicit informational finding. This matches the Fase E
        rule that observability inspection must be operationally safe in a new
        workspace.
        """

        options = TraceReportOptions(limit=_safe_limit(limit), include_events=include_events, include_metrics=include_metrics)
        span_rows = self.trace_store.list_spans(limit=options.limit * 25)
        event_rows = self.trace_store.list_events(limit=options.limit * 25) if options.include_events else []
        metric_rows = self.metrics.list_metrics(limit=options.limit * 25) if options.include_metrics else []
        traces = _build_trace_summaries(span_rows, event_rows, metric_rows, limit=options.limit)
        summary = _trace_report_summary(traces, span_rows, event_rows, metric_rows, options=options)
        findings: list[Finding] = []
        if not traces:
            findings.append(
                Finding(
                    id="TRACE_REPORT_EMPTY",
                    message="No local traces were found. Run an instrumented command such as agent run or model generate first.",
                    severity=Severity.INFO,
                    path=".devpilot/devpilot.db",
                )
            )
        return CommandResult(
            command="trace report",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local trace report generated." if traces else "No local traces found; empty trace report generated.",
            data=_redact_observability_data(
                {
                    "summary": summary,
                    "traces": traces,
                    "options": {
                        "limit": options.limit,
                        "include_events": options.include_events,
                        "include_metrics": options.include_metrics,
                    },
                    "preliminary": True,
                    "network_used": False,
                    "external_api_used": False,
                    "ui_required": False,
                }
            ),
            findings=findings,
        )

    def inspect(self, trace_id: str, *, limit: int = 100) -> CommandResult:
        """Return a tree-oriented inspection of one trace id.

        A missing trace_id is handled as PASS with a warning finding. The command
        is diagnostic, not a quality gate, so absence of a trace is not a crash
        and does not produce ERROR/BLOCK.
        """

        safe_limit = _safe_limit(limit, cap=500)
        trace_id = str(trace_id or "").strip()
        spans = self.trace_store.list_spans(trace_id=trace_id, limit=safe_limit)
        events = self.trace_store.list_events(trace_id=trace_id, limit=safe_limit)
        metrics = [metric for metric in self.metrics.list_metrics(limit=safe_limit * 2) if metric.get("trace_id") == trace_id]
        tree = _build_span_tree(spans)
        summary = {
            "trace_id": trace_id,
            "found": bool(spans or events or metrics),
            "spans_total": len(spans),
            "root_spans_total": len(tree),
            "events_total": len(events),
            "metrics_total": len(metrics),
            "statuses": dict(Counter(str(span.get("status") or "unknown") for span in spans)),
            "span_types": dict(Counter(str(span.get("span_type") or "unknown") for span in spans)),
            "limit": safe_limit,
        }
        findings: list[Finding] = []
        if not summary["found"]:
            findings.append(
                Finding(
                    id="TRACE_NOT_FOUND",
                    message=f"Trace id '{trace_id}' was not found in the local TraceStore.",
                    severity=Severity.WARNING,
                    path=".devpilot/devpilot.db",
                )
            )
        return CommandResult(
            command="trace inspect",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Trace inspection generated." if summary["found"] else "Trace id not found; empty inspection generated.",
            data=_redact_observability_data(
                {
                    "summary": summary,
                    "trace_id": trace_id,
                    "tree": tree,
                    "spans": spans,
                    "events": events,
                    "metrics": metrics,
                    "preliminary": True,
                    "network_used": False,
                    "external_api_used": False,
                    "ui_required": False,
                }
            ),
            findings=findings,
        )

    def metrics_summary(self, *, category: str | None = None, limit: int = 50) -> CommandResult:
        """Return aggregate local metrics and a bounded recent sample."""

        safe_limit = _safe_limit(limit, cap=500)
        summary = self.metrics.summary()
        recent = self.metrics.list_metrics(category=category, limit=safe_limit)
        category_counts = Counter(str(metric.get("category") or "unknown") for metric in recent)
        operation_counts = Counter(str(metric.get("operation") or metric.get("name") or "unknown") for metric in recent)
        status_counts = Counter(str(metric.get("status") or "UNKNOWN") for metric in recent if metric.get("unit") == "count")
        provider_counts = Counter(str(metric.get("provider")) for metric in recent if metric.get("provider"))
        payload_summary = {
            **summary,
            "recent_metrics_total": len(recent),
            "recent_categories": dict(sorted(category_counts.items())),
            "recent_operations": dict(sorted(operation_counts.items())),
            "recent_statuses": dict(sorted(status_counts.items())),
            "recent_providers": dict(sorted(provider_counts.items())),
            "filter_category": category,
            "limit": safe_limit,
        }
        findings: list[Finding] = []
        if int(summary.get("metrics_total") or 0) == 0:
            findings.append(
                Finding(
                    id="METRICS_SUMMARY_EMPTY",
                    message="No local metrics were found. Run an instrumented command first.",
                    severity=Severity.INFO,
                    path=".devpilot/devpilot.db",
                )
            )
        return CommandResult(
            command="metrics summary",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local metrics summary generated." if summary.get("metrics_total") else "No local metrics found; empty metrics summary generated.",
            data=_redact_observability_data(
                {
                    "summary": payload_summary,
                    "metrics": recent,
                    "preliminary": True,
                    "network_used": False,
                    "external_api_used": False,
                    "ui_required": False,
                }
            ),
            findings=findings,
        )


def _safe_limit(limit: int, *, cap: int = 100) -> int:
    try:
        parsed = int(limit)
    except (TypeError, ValueError):
        parsed = 20
    return max(1, min(parsed, cap))


def _build_trace_summaries(
    spans: list[dict[str, Any]],
    events: list[dict[str, Any]],
    metrics: list[dict[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    by_trace: dict[str, dict[str, Any]] = {}
    for span in spans:
        trace_id = span.get("trace_id")
        if not trace_id:
            continue
        trace = by_trace.setdefault(str(trace_id), _empty_trace_summary(str(trace_id)))
        trace["spans_total"] += 1
        trace["span_types"][str(span.get("span_type") or "unknown")] += 1
        trace["statuses"][str(span.get("status") or "unknown")] += 1
        trace["duration_ms_total"] += int(span.get("duration_ms") or 0)
        _touch_trace_time(trace, span.get("started_at"), span.get("ended_at"))
        if len(trace["sample_spans"]) < 5:
            trace["sample_spans"].append(_span_summary(span))
    for event in events:
        trace_id = event.get("trace_id")
        if not trace_id:
            continue
        trace = by_trace.setdefault(str(trace_id), _empty_trace_summary(str(trace_id)))
        trace["events_total"] += 1
        trace["event_types"][str(event.get("event_type") or "unknown")] += 1
        _touch_trace_time(trace, event.get("timestamp"), event.get("timestamp"))
    for metric in metrics:
        trace_id = metric.get("trace_id")
        if not trace_id:
            continue
        trace = by_trace.setdefault(str(trace_id), _empty_trace_summary(str(trace_id)))
        trace["metrics_total"] += 1
        trace["metric_categories"][str(metric.get("category") or "unknown")] += 1
        _touch_trace_time(trace, metric.get("timestamp"), metric.get("timestamp"))
    traces: list[dict[str, Any]] = []
    for trace in by_trace.values():
        normalized = dict(trace)
        for key in ("span_types", "statuses", "event_types", "metric_categories"):
            normalized[key] = dict(sorted(normalized[key].items()))
        traces.append(normalized)
    traces.sort(key=lambda item: str(item.get("last_seen_at") or item.get("started_at") or ""), reverse=True)
    return traces[:limit]


def _empty_trace_summary(trace_id: str) -> dict[str, Any]:
    return {
        "trace_id": trace_id,
        "started_at": None,
        "last_seen_at": None,
        "spans_total": 0,
        "events_total": 0,
        "metrics_total": 0,
        "duration_ms_total": 0,
        "span_types": Counter(),
        "statuses": Counter(),
        "event_types": Counter(),
        "metric_categories": Counter(),
        "sample_spans": [],
    }


def _touch_trace_time(trace: dict[str, Any], started_at: Any, ended_at: Any) -> None:
    if started_at and (trace.get("started_at") is None or str(started_at) < str(trace["started_at"])):
        trace["started_at"] = str(started_at)
    candidate_end = ended_at or started_at
    if candidate_end and (trace.get("last_seen_at") is None or str(candidate_end) > str(trace["last_seen_at"])):
        trace["last_seen_at"] = str(candidate_end)


def _span_summary(span: dict[str, Any]) -> dict[str, Any]:
    return {
        "span_id": span.get("span_id"),
        "parent_span_id": span.get("parent_span_id"),
        "name": span.get("name"),
        "span_type": span.get("span_type"),
        "status": span.get("status"),
        "subject": span.get("subject"),
        "duration_ms": span.get("duration_ms"),
    }


def _trace_report_summary(
    traces: list[dict[str, Any]],
    spans: list[dict[str, Any]],
    events: list[dict[str, Any]],
    metrics: list[dict[str, Any]],
    *,
    options: TraceReportOptions,
) -> dict[str, Any]:
    return {
        "traces_total": len(traces),
        "spans_scanned": len(spans),
        "events_scanned": len(events),
        "metrics_scanned": len(metrics),
        "limit": options.limit,
        "include_events": options.include_events,
        "include_metrics": options.include_metrics,
        "statuses": dict(Counter(status for trace in traces for status, total in trace["statuses"].items() for _ in range(int(total)))),
        "span_types": dict(Counter(span_type for trace in traces for span_type, total in trace["span_types"].items() for _ in range(int(total)))),
    }


def _build_span_tree(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    children: dict[str | None, list[str]] = defaultdict(list)
    for span in spans:
        span_id = str(span.get("span_id"))
        parent_span_id = span.get("parent_span_id")
        by_id[span_id] = {**_span_summary(span), "children": []}
        children[parent_span_id].append(span_id)
    root_ids = [span_id for span_id, span in by_id.items() if not span.get("parent_span_id") or span.get("parent_span_id") not in by_id]
    if not root_ids:
        root_ids = list(by_id)

    def attach(span_id: str, seen: set[str]) -> dict[str, Any]:
        node = dict(by_id[span_id])
        if span_id in seen:
            node["cycle_detected"] = True
            node["children"] = []
            return node
        next_seen = {span_id, *seen}
        node["children"] = [attach(child_id, next_seen) for child_id in children.get(span_id, []) if child_id in by_id]
        return node

    return [attach(span_id, set()) for span_id in root_ids if span_id in by_id]


_ALLOWED_TOKEN_ESTIMATE_KEYS = {
    "tokens_estimated",
    "tokens_estimated_total",
    "estimated_tokens",
    "estimated_token_count_total",
}


def _redact_observability_data(payload: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive data while preserving safe aggregate token counts.

    DevPilot's general SecretGuard treats any key containing `token` as
    sensitive. That is correct for credentials, but AgentOps also has numeric
    estimated-token counters that are not secrets. Sprint 61 preserves those
    aggregate numbers while still redacting strings and credential-like keys.
    """

    redacted = redact_sensitive_data(payload)
    return _restore_safe_token_estimates(original=payload, redacted=redacted)


def _restore_safe_token_estimates(original: Any, redacted: Any) -> Any:
    if isinstance(original, dict) and isinstance(redacted, dict):
        restored = dict(redacted)
        for key, original_value in original.items():
            if key in _ALLOWED_TOKEN_ESTIMATE_KEYS and isinstance(original_value, (int, float)):
                restored[key] = original_value
            elif key in restored:
                restored[key] = _restore_safe_token_estimates(original_value, restored[key])
        return restored
    if isinstance(original, list) and isinstance(redacted, list):
        return [_restore_safe_token_estimates(o, r) for o, r in zip(original, redacted)]
    return redacted
