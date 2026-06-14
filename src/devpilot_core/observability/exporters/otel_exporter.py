from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core import __version__
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.observability.metrics import MetricsCollector
from devpilot_core.observability.trace_store import TraceStore
from devpilot_core.policy import PolicyEngine, PolicyRequest, redact_sensitive_data
from devpilot_core.store import DEFAULT_DB_PATH


@dataclass(frozen=True)
class OTelExportOptions:
    """Options for the local OpenTelemetry-compatible dry-run exporter.

    FUNC-SPRINT-62 deliberately implements a dependency-free mapper, not a real
    OTLP client. The generated payload is useful for review, tests and future
    integration work, but it is never sent to a collector by this module.
    """

    format: str = "otlp"
    dry_run: bool = True
    trace_id: str | None = None
    limit: int = 20
    include_metrics: bool = True
    endpoint: str | None = None


class OTelDryRunExporter:
    """Map DevPilot local AgentOps records into an OTel-like JSON payload.

    The exporter is local-first and policy-first: export is allowed only as a
    dry-run projection. Any attempt to disable dry-run or configure a remote
    endpoint returns a controlled BLOCK result instead of using outbound I/O.
    """

    def __init__(self, root: Path, *, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.root = root.resolve()
        self.trace_store = TraceStore(self.root, db_path=db_path)
        self.metrics = MetricsCollector(self.root, db_path=db_path)

    def export(self, options: OTelExportOptions | None = None) -> CommandResult:
        """Return a local dry-run OTLP-like payload as a CommandResult."""

        options = options or OTelExportOptions()
        normalized_format = _normalize_format(options.format)
        safe_limit = _safe_limit(options.limit)
        policy_result = self._evaluate_policy(options=options, normalized_format=normalized_format, safe_limit=safe_limit)
        if not policy_result.ok:
            return self._blocked_result(policy_result, options=options, normalized_format=normalized_format, safe_limit=safe_limit)

        spans = self.trace_store.list_spans(trace_id=options.trace_id, limit=safe_limit)
        events = self.trace_store.list_events(trace_id=options.trace_id, limit=safe_limit)
        metrics = self.metrics.list_metrics(limit=safe_limit * 5) if options.include_metrics else []
        if options.trace_id:
            metrics = [metric for metric in metrics if metric.get("trace_id") == options.trace_id]
        payload = build_otel_like_payload(
            spans=spans,
            events=events,
            metrics=metrics,
            service_name="devpilot-local",
            service_version=__version__,
        )
        sanitized_payload = redact_sensitive_data(payload)
        summary = {
            "format": normalized_format,
            "dry_run": True,
            "trace_id": options.trace_id,
            "spans_exported": len(spans),
            "events_exported": len(events),
            "metrics_exported": len(metrics),
            "resource_spans_total": len(sanitized_payload.get("resourceSpans", [])),
            "resource_metrics_total": len(sanitized_payload.get("resourceMetrics", [])),
            "endpoint_configured": bool(options.endpoint),
            "network_used": False,
            "external_api_used": False,
            "remote_telemetry_enabled": False,
            "collector_required": False,
            "payload_redacted": True,
            "preliminary": True,
        }
        findings: list[Finding] = []
        if not spans and not metrics:
            findings.append(
                Finding(
                    id="OTEL_EXPORT_EMPTY",
                    message="No local spans or metrics were available for the dry-run OTel payload.",
                    severity=Severity.INFO,
                    path=".devpilot/devpilot.db",
                )
            )
        return CommandResult(
            command="telemetry export",
            ok=True,
            exit_code=ExitCode.PASS,
            message="OpenTelemetry dry-run payload generated locally.",
            data={
                "summary": summary,
                "mapping": otel_mapping_documentation(),
                "payload_kind": "otlp-json-dry-run",
                "payload": sanitized_payload,
                "policy_summary": (policy_result.data or {}).get("summary", {}),
                "preliminary": True,
                "network_used": False,
                "external_api_used": False,
                "ui_required": False,
            },
            findings=findings,
        )

    def _evaluate_policy(self, *, options: OTelExportOptions, normalized_format: str, safe_limit: int) -> CommandResult:
        endpoint_requested = bool(options.endpoint)
        unsafe_remote_attempt = (not options.dry_run) or endpoint_requested
        action = "network-call" if unsafe_remote_attempt else "telemetry-export-dry-run"
        return PolicyEngine(self.root).evaluate(
            PolicyRequest(
                action=action,
                external_api=unsafe_remote_attempt,
                provider="opentelemetry",
                estimated_cost_usd=0.0,
                dry_run=True,
                tool_id="telemetry.export",
                subject=options.endpoint or "observability:otel-dry-run",
                metadata={
                    "component": "OTelDryRunExporter",
                    "format": normalized_format,
                    "requested_dry_run": options.dry_run,
                    "trace_id": options.trace_id,
                    "limit": safe_limit,
                    "endpoint_configured": endpoint_requested,
                    "remote_telemetry_enabled": False,
                    "payload_redacted": True,
                },
            )
        )

    def _blocked_result(
        self,
        policy_result: CommandResult,
        *,
        options: OTelExportOptions,
        normalized_format: str,
        safe_limit: int,
    ) -> CommandResult:
        findings = list(policy_result.findings)
        findings.append(
            Finding(
                id="OTEL_REMOTE_EXPORT_BLOCKED",
                message="Remote OpenTelemetry export is disabled in FUNC-SPRINT-62; only local dry-run payload generation is allowed.",
                severity=Severity.BLOCK,
                metadata={"dry_run": options.dry_run, "endpoint_configured": bool(options.endpoint)},
            )
        )
        return CommandResult(
            command="telemetry export",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="OpenTelemetry export blocked by policy; remote telemetry remains disabled.",
            data={
                "summary": {
                    "format": normalized_format,
                    "dry_run": options.dry_run,
                    "trace_id": options.trace_id,
                    "limit": safe_limit,
                    "endpoint_configured": bool(options.endpoint),
                    "network_used": False,
                    "external_api_used": False,
                    "remote_telemetry_enabled": False,
                    "payload_redacted": True,
                    "preliminary": True,
                },
                "policy_result": redact_sensitive_data(policy_result.to_dict()),
            },
            findings=findings,
        )


def build_otel_like_payload(
    *,
    spans: list[dict[str, Any]],
    events: list[dict[str, Any]],
    metrics: list[dict[str, Any]],
    service_name: str,
    service_version: str,
) -> dict[str, Any]:
    """Build a dependency-free OTLP JSON-compatible shape.

    It intentionally uses OTLP-inspired field names (`resourceSpans`,
    `scopeSpans`, `traceId`, `spanId`, `parentSpanId`, `attributes`,
    `resourceMetrics`) while keeping the payload reviewable as plain JSON.
    """

    resource_attributes = [
        _attribute("service.name", service_name),
        _attribute("service.version", service_version),
        _attribute("telemetry.sdk.name", "devpilot-local-dry-run"),
        _attribute("telemetry.sdk.language", "python"),
        _attribute("devpilot.exporter.mode", "dry-run"),
    ]
    event_groups = _events_by_span(events)
    otel_spans = [_map_span(span, event_groups.get(str(span.get("span_id")), [])) for span in spans]
    metric_rows = [_map_metric(metric) for metric in metrics]
    payload: dict[str, Any] = {
        "resourceSpans": [
            {
                "resource": {"attributes": resource_attributes},
                "scopeSpans": [
                    {
                        "scope": {"name": "devpilot_core.observability", "version": service_version},
                        "spans": otel_spans,
                    }
                ],
            }
        ],
        "resourceMetrics": [
            {
                "resource": {"attributes": resource_attributes},
                "scopeMetrics": [
                    {
                        "scope": {"name": "devpilot_core.observability", "version": service_version},
                        "metrics": metric_rows,
                    }
                ],
            }
        ],
        "devpilot": {
            "format": "otlp-json-dry-run",
            "source": "SQLite TraceStore/MetricsCollector",
            "payload_redacted": True,
            "network_used": False,
            "external_api_used": False,
            "generated_at": _utc_now_iso(),
        },
    }
    return payload


def otel_mapping_documentation() -> dict[str, str]:
    """Return the documented DevPilot -> OTel-like field mapping."""

    return {
        "trace_id": "span.traceId, generated from a stable digest of the DevPilot trace_id",
        "span_id": "span.spanId, generated from a stable digest of the DevPilot span_id",
        "parent_span_id": "span.parentSpanId when present",
        "span.name": "span.name",
        "span_type": "attribute devpilot.span_type",
        "status": "span.status.code and attribute devpilot.status",
        "subject": "attribute devpilot.subject",
        "provider/model/task": "attributes gen_ai.system, gen_ai.request.model, gen_ai.operation.name when available",
        "tool_id": "attribute gen_ai.tool.name when available",
        "metrics": "resourceMetrics.scopeMetrics.metrics as gauge-like dry-run values",
        "events": "span.events with redacted attributes",
    }


def _map_span(span: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    metadata = _as_dict(span.get("metadata"))
    payload = _as_dict(span.get("payload"))
    attributes = [
        _attribute("devpilot.trace_id", span.get("trace_id")),
        _attribute("devpilot.span_id", span.get("span_id")),
        _attribute("devpilot.span_type", span.get("span_type")),
        _attribute("devpilot.status", span.get("status")),
        _attribute("devpilot.severity", span.get("severity")),
        _attribute("devpilot.subject", span.get("subject")),
        _attribute("devpilot.run_id", span.get("run_id")),
    ]
    tool_id = metadata.get("tool_id") or payload.get("tool_id")
    provider = metadata.get("provider") or payload.get("provider")
    if not provider and span.get("span_type") == "model.call":
        provider = span.get("subject")
    model = metadata.get("model") or payload.get("model")
    task = metadata.get("task") or payload.get("task")
    if provider:
        attributes.append(_attribute("gen_ai.system", provider))
    if model:
        attributes.append(_attribute("gen_ai.request.model", model))
    if task:
        attributes.append(_attribute("gen_ai.operation.name", task))
    if tool_id:
        attributes.append(_attribute("gen_ai.tool.name", tool_id))
    mapped_events = [_map_event(event) for event in events]
    return {
        "traceId": _otel_trace_id(span.get("trace_id")),
        "spanId": _otel_span_id(span.get("span_id")),
        "parentSpanId": _otel_span_id(span.get("parent_span_id")) if span.get("parent_span_id") else None,
        "name": str(span.get("name") or span.get("span_type") or "devpilot.span"),
        "kind": 1,
        "startTimeUnixNano": _iso_to_unix_nano(span.get("started_at")),
        "endTimeUnixNano": _iso_to_unix_nano(span.get("ended_at") or span.get("started_at")),
        "attributes": [attr for attr in attributes if attr is not None],
        "events": mapped_events,
        "status": _map_status(span.get("status")),
    }


def _map_event(event: dict[str, Any]) -> dict[str, Any]:
    attributes = [
        _attribute("devpilot.event_id", event.get("event_id")),
        _attribute("devpilot.event_type", event.get("event_type")),
        _attribute("devpilot.command", event.get("command")),
        _attribute("devpilot.status", event.get("status")),
        _attribute("devpilot.subject", event.get("subject")),
    ]
    metadata = _as_dict(event.get("metadata"))
    for key in sorted(metadata):
        if key in {"prompt", "completion", "stdout", "stderr", "secret", "token"}:
            continue
        value = metadata[key]
        if isinstance(value, (str, int, float, bool)) or value is None:
            attributes.append(_attribute(f"devpilot.event.metadata.{key}", value))
    return {
        "name": str(event.get("event_type") or "devpilot.event"),
        "timeUnixNano": _iso_to_unix_nano(event.get("timestamp")),
        "attributes": [attr for attr in attributes if attr is not None],
    }


def _map_metric(metric: dict[str, Any]) -> dict[str, Any]:
    attributes = [
        _attribute("devpilot.metric_id", metric.get("metric_id")),
        _attribute("devpilot.category", metric.get("category")),
        _attribute("devpilot.operation", metric.get("operation")),
        _attribute("devpilot.status", metric.get("status")),
        _attribute("devpilot.command", metric.get("command")),
        _attribute("devpilot.trace_id", metric.get("trace_id")),
        _attribute("gen_ai.system", metric.get("provider")),
        _attribute("gen_ai.request.model", metric.get("model")),
        _attribute("gen_ai.operation.name", metric.get("task")),
    ]
    return {
        "name": str(metric.get("name") or "devpilot.metric"),
        "unit": str(metric.get("unit") or "1"),
        "gauge": {
            "dataPoints": [
                {
                    "timeUnixNano": _iso_to_unix_nano(metric.get("timestamp")),
                    "asDouble": float(metric.get("value") or 0.0),
                    "attributes": [attr for attr in attributes if attr is not None],
                }
            ]
        },
    }


def _events_by_span(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        span_id = event.get("span_id")
        if span_id:
            groups.setdefault(str(span_id), []).append(event)
    return groups


def _attribute(key: str, value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, bool):
        encoded = {"boolValue": value}
    elif isinstance(value, int):
        encoded = {"intValue": value}
    elif isinstance(value, float):
        encoded = {"doubleValue": value}
    else:
        encoded = {"stringValue": str(value)}
    return {"key": key, "value": encoded}


def _map_status(value: Any) -> dict[str, Any]:
    status = str(value or "unknown").lower()
    if status in {"ok", "pass", "passed"}:
        return {"code": 1, "message": status}
    if status in {"error", "fail", "failed", "block", "blocked"}:
        return {"code": 2, "message": status}
    return {"code": 0, "message": status}


def _otel_trace_id(value: Any) -> str:
    return _stable_hex(value, 32)


def _otel_span_id(value: Any) -> str:
    return _stable_hex(value, 16)


def _stable_hex(value: Any, length: int) -> str:
    raw = str(value or "missing").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:length]


def _iso_to_unix_nano(value: Any) -> str:
    if not value:
        return "0"
    try:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return str(int(dt.timestamp() * 1_000_000_000))
    except Exception:
        return "0"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_limit(value: int, *, cap: int = 100) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = 20
    return max(1, min(parsed, cap))


def _normalize_format(value: str) -> str:
    normalized = str(value or "otlp").strip().lower()
    if normalized not in {"otlp", "otlp-json"}:
        return "otlp"
    return normalized


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
