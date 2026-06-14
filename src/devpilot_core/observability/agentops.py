from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.observability.events import EventRecord
from devpilot_core.observability.metrics import MetricsCollector
from devpilot_core.observability.trace_store import TraceStore
from devpilot_core.store import DEFAULT_DB_PATH, LocalStore
from devpilot_core.observability.tracing import SpanRecord, SpanStatus, TraceContext, sanitize_span_payload, utc_now_iso


def status_from_ok(ok: bool, *, blocked: bool = False, errored: bool = False) -> SpanStatus:
    """Map DevPilot booleans/guards to the internal span status contract."""

    if errored:
        return SpanStatus.ERROR
    if blocked:
        return SpanStatus.BLOCK
    return SpanStatus.OK if ok else SpanStatus.FAIL


def status_from_command_result(result: CommandResult) -> SpanStatus:
    """Map a CommandResult to a SpanStatus without importing CLI internals elsewhere."""

    if result.ok:
        return SpanStatus.OK
    if int(result.exit_code) == int(ExitCode.BLOCK):
        return SpanStatus.BLOCK
    if int(result.exit_code) == int(ExitCode.ERROR):
        return SpanStatus.ERROR
    return SpanStatus.FAIL


class AgentOpsInstrumentor:
    """Best-effort local instrumentation for agentic DevPilot operations.

    FUNC-SPRINT-60 connects the contracts introduced in Sprints 57-59 to the
    actual agent/model/policy/approval runtime surface. Instrumentation is
    intentionally local-first, synchronous and best-effort: it can persist spans,
    events and metrics, but it must never change the functional result of a
    command, agent, tool, policy decision or model call.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.trace_store = TraceStore(self.root)
        self.metrics = MetricsCollector(self.root)

    def start_trace(
        self,
        *,
        command: str,
        agent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceContext:
        """Create a trace context for one local DevPilot operation."""

        return TraceContext.start(
            command=command,
            agent_run_id=agent_id,
            metadata={"component": "AgentOpsInstrumentor", **(metadata or {})},
        )

    def record_agent_run(
        self,
        *,
        context: TraceContext,
        agent_id: str,
        agent_name: str | None,
        ok: bool,
        dry_run: bool,
        tool_calls_total: int = 0,
        model_calls_total: int = 0,
        findings: list[Finding] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """Persist an agent_run span/event/metric."""

        try:
            status = status_from_ok(ok, blocked=_has_blocking_findings(findings or []))
            span = context.child_span(
                name=f"agent:{agent_id}",
                span_type="agent.run",
                status=status,
                severity="info" if ok else "warning",
                subject=agent_id,
                payload={
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "dry_run": dry_run,
                    "tool_calls_total": tool_calls_total,
                    "model_calls_total": model_calls_total,
                    "payload_redacted": True,
                },
                metadata={"instrumentation_sprint": "FUNC-SPRINT-60", **(metadata or {})},
                findings=findings or [],
            ).finish(status=status)
            span_id = self.trace_store.record_span(span)
            self.trace_store.record_event(
                EventRecord(
                    event_type="agent.run.completed",
                    command="agent run",
                    status=_status_text(status),
                    ok=ok,
                    exit_code=0 if ok else 1,
                    subject=agent_id,
                    summary={
                        "agent_id": agent_id,
                        "tool_calls_total": tool_calls_total,
                        "model_calls_total": model_calls_total,
                    },
                    metadata={"payload_redacted": True},
                ),
                trace_context=context,
                span=span,
            )
            self.metrics.record_agent_operation(
                agent_id=agent_id,
                operation="run_total",
                status=_status_text(status),
                ok=ok,
                trace_context=context,
                span_id=span_id,
                metadata={"agent_name": agent_name, "dry_run": dry_run, "payload_redacted": True},
            )
            return span_id
        except Exception:
            return None

    def record_tool_call(
        self,
        *,
        context: TraceContext,
        tool_id: str,
        action: str,
        allowed: bool,
        dry_run: bool,
        policy_exit_code: int | None = None,
        subject: str | None = None,
        parent_span_id: str | None = None,
        findings: list[Finding] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """Persist a tool_call span/event/metric."""

        try:
            blocked = not allowed or _has_blocking_findings(findings or [])
            status = status_from_ok(allowed, blocked=blocked)
            span = context.child_span(
                name=f"tool:{tool_id}",
                span_type="tool.call",
                parent_span_id=parent_span_id,
                status=status,
                severity="info" if allowed else "warning",
                subject=subject,
                payload={
                    "tool_id": tool_id,
                    "action": action,
                    "allowed": allowed,
                    "dry_run": dry_run,
                    "policy_exit_code": policy_exit_code,
                    "payload_redacted": True,
                },
                metadata={"instrumentation_sprint": "FUNC-SPRINT-60", **(metadata or {})},
                findings=findings or [],
            ).finish(status=status)
            span_id = self.trace_store.record_span(span)
            self.trace_store.record_event(
                EventRecord(
                    event_type="agent.tool_call.completed",
                    command="agent run",
                    status=_status_text(status),
                    ok=allowed,
                    exit_code=policy_exit_code,
                    subject=subject,
                    summary={"tool_id": tool_id, "action": action, "allowed": allowed, "dry_run": dry_run},
                    metadata={"payload_redacted": True},
                ),
                trace_context=context,
                span=span,
            )
            self.metrics.record_tool_operation(
                tool_id=tool_id,
                operation="call_total",
                status=_status_text(status),
                ok=allowed,
                trace_context=context,
                span_id=span_id,
                metadata={"action": action, "subject": subject, "dry_run": dry_run, "payload_redacted": True},
            )
            return span_id
        except Exception:
            return None

    def record_policy_result(
        self,
        *,
        result: CommandResult,
        action: str,
        subject: str | None = None,
        trace_context: TraceContext | None = None,
        parent_span_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """Persist a policy_check span/event/metric."""

        try:
            context = trace_context or self.start_trace(command="policy check", metadata={"component": "PolicyEngine"})
            status = status_from_command_result(result)
            summary = dict((result.data or {}).get("summary") or {}) if isinstance(result.data, dict) else {}
            span = context.child_span(
                name=f"policy:{action}",
                span_type="policy.check",
                parent_span_id=parent_span_id,
                status=status,
                severity="info" if result.ok else "warning",
                subject=subject,
                payload={
                    "action": action,
                    "allowed": result.ok,
                    "summary": summary,
                    "payload_redacted": True,
                },
                metadata={"instrumentation_sprint": "FUNC-SPRINT-60", **(metadata or {})},
                findings=result.findings,
            ).finish(status=status)
            span_id = self.trace_store.record_span(span)
            self.trace_store.record_event(
                EventRecord(
                    event_type="policy.check.completed",
                    command="policy check",
                    status=_status_text(status),
                    ok=result.ok,
                    exit_code=int(result.exit_code),
                    subject=subject,
                    summary={"action": action, **summary},
                    metadata={"payload_redacted": True},
                ),
                trace_context=context,
                span=span,
            )
            self.metrics.record_count(
                category="policy",
                operation="check_total",
                status=_status_text(status),
                ok=result.ok,
                command="policy check",
                trace_context=context,
                span_id=span_id,
                metadata={"action": action, "subject": subject, "payload_redacted": True},
            )
            return span_id
        except Exception:
            return None

    def record_approval_result(
        self,
        *,
        result: CommandResult,
        operation: str,
        approval_id: str | None = None,
        subject: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """Persist an approval workflow span/event/metric."""

        try:
            context = self.start_trace(command=result.command or f"approval {operation}", metadata={"component": "ApprovalService"})
            status = status_from_command_result(result)
            approval_payload = _approval_summary(result, approval_id=approval_id, subject=subject)
            span = context.child_span(
                name=f"approval:{operation}",
                span_type="approval.workflow",
                status=status,
                severity="info" if result.ok else "warning",
                subject=approval_payload.get("approval_id") or subject,
                payload={**approval_payload, "operation": operation, "payload_redacted": True},
                metadata={"instrumentation_sprint": "FUNC-SPRINT-60", **(metadata or {})},
                findings=result.findings,
            ).finish(status=status)
            span_id = self.trace_store.record_span(span)
            self.trace_store.record_event(
                EventRecord(
                    event_type="approval.workflow.completed",
                    command=result.command,
                    status=_status_text(status),
                    ok=result.ok,
                    exit_code=int(result.exit_code),
                    subject=approval_payload.get("approval_id") or subject,
                    summary={**approval_payload, "operation": operation},
                    metadata={"payload_redacted": True},
                ),
                trace_context=context,
                span=span,
            )
            self.metrics.record_count(
                category="approval",
                operation=f"{operation}_total",
                status=_status_text(status),
                ok=result.ok,
                command=result.command,
                trace_context=context,
                span_id=span_id,
                metadata={**approval_payload, "payload_redacted": True},
            )
            return span_id
        except Exception:
            return None

    def record_model_result(
        self,
        *,
        result: CommandResult,
        provider: str | None = None,
        model: str | None = None,
        task: str | None = None,
        trace_context: TraceContext | None = None,
        parent_span_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """Persist a model_call span/event and reuse MetricsCollector model metrics."""

        try:
            summary = dict((result.data or {}).get("summary") or {}) if isinstance(result.data, dict) else {}
            provider_id = provider or str(summary.get("provider") or "unknown")
            model_id = model or (str(summary.get("model")) if summary.get("model") else None)
            task_id = task or str(summary.get("task") or result.command.replace("model ", "") or "unknown")
            context = trace_context or self.start_trace(command=result.command or f"model {task_id}", metadata={"component": "ModelAdapterRouter"})
            status = status_from_command_result(result)
            span = context.child_span(
                name=f"model:{provider_id}:{task_id}",
                span_type="model.call",
                parent_span_id=parent_span_id,
                status=status,
                severity="info" if result.ok else "warning",
                subject=provider_id,
                payload={
                    "provider": provider_id,
                    "model": model_id,
                    "task": task_id,
                    "tokens_estimated": summary.get("tokens_estimated"),
                    "cost_estimate_usd": summary.get("cost_estimate_usd"),
                    "external_api_used": bool(summary.get("external_api_used", False)),
                    "payload_redacted": True,
                },
                metadata={"instrumentation_sprint": "FUNC-SPRINT-60", **(metadata or {})},
                findings=result.findings,
            ).finish(status=status)
            span_id = self.trace_store.record_span(span)
            self.trace_store.record_event(
                EventRecord(
                    event_type="model.call.completed",
                    command=result.command,
                    status=_status_text(status),
                    ok=result.ok,
                    exit_code=int(result.exit_code),
                    subject=provider_id,
                    summary={
                        "provider": provider_id,
                        "model": model_id,
                        "task": task_id,
                        "external_api_used": bool(summary.get("external_api_used", False)),
                        "payload_redacted": True,
                    },
                    metadata={"payload_redacted": True},
                ),
                trace_context=context,
                span=span,
            )
            self.metrics.record_model_result(
                result,
                provider=provider_id,
                model=model_id,
                task=task_id,
                trace_context=context,
                metadata={"span_id": span_id, "payload_redacted": True, **(metadata or {})},
            )
            return span_id
        except Exception:
            return None


def safe_record_agent_result(root: Path, *, context: TraceContext, result: Any) -> dict[str, Any]:
    """Record an AgentRunResult plus child spans without changing the caller result."""

    instrumentor = AgentOpsInstrumentor(root)
    try:
        agent_span_id = instrumentor.record_agent_run(
            context=context,
            agent_id=str(result.agent_id),
            agent_name=str(result.agent_name),
            ok=bool(result.ok),
            dry_run=bool(result.dry_run),
            tool_calls_total=len(result.tool_calls),
            model_calls_total=len(result.model_calls),
            findings=list(result.findings),
            metadata={"component": "AgentRuntime"},
        )
        tool_span_ids: list[str] = []
        policy_span_ids: list[str] = []
        model_span_ids: list[str] = []
        for call in result.tool_calls:
            tool_span_id = instrumentor.record_tool_call(
                context=context,
                parent_span_id=agent_span_id,
                tool_id=str(call.tool_id),
                action=str(call.action),
                allowed=bool(call.allowed),
                dry_run=bool(call.dry_run),
                policy_exit_code=int(call.policy_exit_code),
                subject=call.subject,
                findings=list(call.findings),
                metadata={"tool_call_id": getattr(call, "tool_call_id", None), **dict(call.metadata or {})},
            )
            if tool_span_id:
                tool_span_ids.append(tool_span_id)
            policy_result = CommandResult(
                command="policy check",
                ok=bool(call.allowed),
                exit_code=ExitCode.PASS if call.allowed else ExitCode.BLOCK,
                message="Policy projection generated from AgentToolCall.",
                data={"summary": dict((call.metadata or {}).get("policy_summary") or {})},
                findings=list(call.findings),
            )
            policy_span_id = instrumentor.record_policy_result(
                result=policy_result,
                action=str(call.action),
                subject=call.subject,
                trace_context=context,
                parent_span_id=tool_span_id or agent_span_id,
                metadata={"source": "AgentRuntime.tool_call_projection", "tool_id": str(call.tool_id), "payload_redacted": True},
            )
            if policy_span_id:
                policy_span_ids.append(policy_span_id)
        for call in result.model_calls:
            model_result = CommandResult(
                command=f"model {call.task}",
                ok=bool(call.ok),
                exit_code=ExitCode.PASS if call.ok else ExitCode.BLOCK,
                message="Model projection generated from AgentModelCall.",
                data={
                    "summary": {
                        "provider": call.provider,
                        "model": call.model,
                        "task": call.task,
                        "tokens_estimated": call.tokens_estimated,
                        "cost_estimate_usd": call.cost_estimate_usd,
                        "external_api_used": call.external_api_used,
                        "payload_redacted": True,
                    }
                },
                findings=[],
            )
            model_span_id = instrumentor.record_model_result(
                result=model_result,
                provider=call.provider,
                model=call.model,
                task=call.task,
                trace_context=context,
                parent_span_id=agent_span_id,
                metadata={"source": "AgentRuntime.model_call_projection", "payload_redacted": True},
            )
            if model_span_id:
                model_span_ids.append(model_span_id)
        return {
            "enabled": True,
            "trace_id": context.trace_id,
            "run_id": context.run_id,
            "agent_run_id": context.agent_run_id,
            "agent_span_id": agent_span_id,
            "tool_span_ids": tool_span_ids,
            "policy_span_ids": policy_span_ids,
            "model_span_ids": model_span_ids,
            "payload_redacted": True,
            "best_effort": True,
        }
    except Exception:
        return {"enabled": True, "best_effort": True, "recorded": False, "payload_redacted": True}


def _has_blocking_findings(findings: list[Finding]) -> bool:
    return any(str(getattr(finding.severity, "value", finding.severity)).lower() in {"block", "error"} for finding in findings)


def _status_text(status: SpanStatus) -> str:
    return {
        SpanStatus.OK: "PASS",
        SpanStatus.BLOCK: "BLOCK",
        SpanStatus.ERROR: "ERROR",
        SpanStatus.FAIL: "FAIL",
        SpanStatus.CANCELLED: "CANCELLED",
        SpanStatus.STARTED: "STARTED",
    }[status]


def _approval_summary(result: CommandResult, *, approval_id: str | None, subject: str | None) -> dict[str, Any]:
    data = result.data if isinstance(result.data, dict) else {}
    approval = data.get("approval") if isinstance(data, dict) else None
    approval = approval if isinstance(approval, dict) else {}
    return sanitize_span_payload(
        {
            "approval_id": approval.get("approval_id") or approval_id,
            "status": approval.get("status") or (data.get("summary") or {}).get("status") if isinstance(data.get("summary"), dict) else None,
            "tool_id": approval.get("tool_id"),
            "action": approval.get("action"),
            "subject": approval.get("subject") or subject,
        }
    )



@dataclass(frozen=True)
class AgentOpsGateOptions:
    """Options for the local AgentOps quality gate.

    FUNC-SPRINT-63 keeps the gate bounded and non-invasive. The status command
    reads local evidence only; it does not execute agents, does not call models,
    does not contact network services and does not require a UI.
    """

    limit: int = 100
    strict_runtime_signals: bool = False


class AgentOpsQualityGate:
    """Local quality gate for DevPilot AgentOps readiness.

    The gate consolidates the signals implemented during Fase E: TraceContext,
    TraceStore, MetricsCollector, AgentOps instrumentation, trace/metrics CLI,
    OTel dry-run export contracts and MIASI observability declarations. It is
    intentionally read-only over the repository and SQLite evidence store.
    Optional report writing remains a CLI concern handled by ReportEngine.
    """

    REQUIRED_DOCUMENTS: tuple[str, ...] = (
        "README.md",
        "docs/05_operations/runbook.md",
        "docs/05_operations/observability_plan.md",
        "docs/06_miasi/observability_card.md",
        "docs/06_miasi/tool_card.md",
        "docs/06_miasi/policy_matrix.md",
        "docs/devpilot_backlog_fase_E_agentops_observabilidad.md",
        "docs/audits/phase_e_agentops_closure_report.md",
        "docs/functional_sprint_63_manifest.json",
    )
    REQUIRED_TOOL_IDS: tuple[str, ...] = (
        "agentops.status",
        "telemetry.export",
    )
    REQUIRED_POLICY_RULE_IDS: tuple[str, ...] = (
        "AGENTOPS_STATUS_ALLOW",
        "OTEL_EXPORT_DRY_RUN_ALLOW",
        "OTEL_REMOTE_EXPORT_BLOCK",
    )
    REQUIRED_RUNTIME_CATEGORIES: tuple[str, ...] = (
        "agent",
        "command",
        "model",
        "policy",
        "tool",
    )
    REQUIRED_SPAN_TYPES: tuple[str, ...] = (
        "agent.run",
        "model.call",
        "policy.check",
        "tool.call",
    )

    def __init__(self, root: Path, *, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.root = root.resolve()
        self.db_path = db_path
        self.store = LocalStore(self.root, db_path=db_path)
        self.trace_store = TraceStore(self.root, db_path=db_path)
        self.metrics = MetricsCollector(self.root, db_path=db_path)

    def status(self, options: AgentOpsGateOptions | None = None) -> CommandResult:
        """Evaluate local AgentOps evidence and return PASS/BLOCK findings."""

        opts = options or AgentOpsGateOptions()
        limit = _agentops_safe_limit(opts.limit)
        store_result = self.store.status()
        store_data = store_result.data or {}
        store_summary = store_data.get("summary") if isinstance(store_data, dict) else {}
        store_counts = store_data.get("counts") if isinstance(store_data, dict) else {}
        store_summary = store_summary if isinstance(store_summary, dict) else {}
        store_counts = store_counts if isinstance(store_counts, dict) else {}

        spans = self.trace_store.list_spans(limit=limit)
        events = self.trace_store.list_events(limit=limit)
        recent_metrics = self.metrics.list_metrics(limit=min(limit * 2, 500))
        metric_summary = self.metrics.summary()

        span_type_counts = Counter(str(span.get("span_type") or "unknown") for span in spans)
        span_status_counts = Counter(str(span.get("status") or "unknown") for span in spans)
        event_type_counts = Counter(str(event.get("event_type") or "unknown") for event in events)
        metric_category_counts = Counter(str(metric.get("category") or "unknown") for metric in recent_metrics)
        metric_status_counts = Counter(str(metric.get("status") or "UNKNOWN") for metric in recent_metrics if metric.get("unit") == "count")
        trace_ids = sorted({str(span.get("trace_id")) for span in spans if span.get("trace_id")})

        document_status = {path: (self.root / path).is_file() for path in self.REQUIRED_DOCUMENTS}
        registry_status = self._registry_status()
        runtime_status = {
            "store_initialized": bool(store_summary.get("initialized")),
            "spans_present": bool(spans),
            "events_present": bool(events),
            "metrics_present": int(metric_summary.get("metrics_total") or 0) > 0,
            "required_metric_categories_present": all(
                category in (metric_summary.get("categories") or {}) or category in metric_category_counts
                for category in self.REQUIRED_RUNTIME_CATEGORIES
            ),
            "required_span_types_present": all(span_type in span_type_counts for span_type in self.REQUIRED_SPAN_TYPES),
            "network_used": False,
            "external_api_used": False,
            "ui_required": False,
            "remote_telemetry_enabled": False,
        }

        findings: list[Finding] = []
        for path, exists in document_status.items():
            if not exists:
                findings.append(
                    Finding(
                        id="AGENTOPS_REQUIRED_DOCUMENT_MISSING",
                        message=f"Required AgentOps/Phase E document is missing: {path}.",
                        severity=Severity.BLOCK,
                        path=path,
                    )
                )
        for tool_id, exists in registry_status["tools"].items():
            if not exists:
                findings.append(
                    Finding(
                        id="AGENTOPS_MIASI_TOOL_MISSING",
                        message=f"MIASI Tool Registry does not declare required tool '{tool_id}'.",
                        severity=Severity.BLOCK,
                        path=".devpilot/miasi/tool_registry.json",
                    )
                )
        for rule_id, exists in registry_status["policy_rules"].items():
            if not exists:
                findings.append(
                    Finding(
                        id="AGENTOPS_MIASI_POLICY_RULE_MISSING",
                        message=f"MIASI Policy Matrix does not declare required rule '{rule_id}'.",
                        severity=Severity.BLOCK,
                        path=".devpilot/miasi/policy_matrix.json",
                    )
                )

        if not runtime_status["store_initialized"]:
            findings.append(
                Finding(
                    id="AGENTOPS_STORE_NOT_INITIALIZED",
                    message="Local SQLite store is not initialized. Run `python -m devpilot_core state init --json`.",
                    severity=Severity.WARNING,
                    path=".devpilot/devpilot.db",
                )
            )
        if not runtime_status["spans_present"]:
            findings.append(
                Finding(
                    id="AGENTOPS_SPANS_EMPTY",
                    message="No spans were found. Run an instrumented agent/model/policy command before operational closure evidence.",
                    severity=Severity.BLOCK if opts.strict_runtime_signals else Severity.WARNING,
                    path=".devpilot/devpilot.db",
                )
            )
        if not runtime_status["metrics_present"]:
            findings.append(
                Finding(
                    id="AGENTOPS_METRICS_EMPTY",
                    message="No metrics were found. Run instrumented commands before operational closure evidence.",
                    severity=Severity.BLOCK if opts.strict_runtime_signals else Severity.WARNING,
                    path=".devpilot/devpilot.db",
                )
            )
        missing_span_types = [span_type for span_type in self.REQUIRED_SPAN_TYPES if span_type not in span_type_counts]
        if missing_span_types:
            findings.append(
                Finding(
                    id="AGENTOPS_RECOMMENDED_SPAN_TYPES_INCOMPLETE",
                    message="Recommended AgentOps span types are not all present in the recent sample: " + ", ".join(missing_span_types),
                    severity=Severity.BLOCK if opts.strict_runtime_signals else Severity.WARNING,
                    path=".devpilot/devpilot.db",
                )
            )
        metric_categories = set(metric_summary.get("categories") or {}) | set(metric_category_counts)
        missing_categories = [category for category in self.REQUIRED_RUNTIME_CATEGORIES if category not in metric_categories]
        if missing_categories:
            findings.append(
                Finding(
                    id="AGENTOPS_RECOMMENDED_METRIC_CATEGORIES_INCOMPLETE",
                    message="Recommended AgentOps metric categories are not all present: " + ", ".join(missing_categories),
                    severity=Severity.BLOCK if opts.strict_runtime_signals else Severity.WARNING,
                    path=".devpilot/devpilot.db",
                )
            )

        blocked = any(finding.severity == Severity.BLOCK for finding in findings)
        warning = any(finding.severity == Severity.WARNING for finding in findings)
        phase_e_closure_ready = not blocked and document_status.get("docs/audits/phase_e_agentops_closure_report.md", False)
        operational_status = "BLOCK" if blocked else "WARN" if warning else "PASS"
        data = {
            "summary": {
                "operational_status": operational_status,
                "phase": "FASE-E-AGENTOPS-OBSERVABILIDAD",
                "phase_e_closure_ready": phase_e_closure_ready,
                "next_phase": "FASE-F-PRODUCTO-VISUAL",
                "next_sprint": "FUNC-SPRINT-64",
                "store_initialized": runtime_status["store_initialized"],
                "traces_observed_total": len(trace_ids),
                "spans_scanned": len(spans),
                "events_scanned": len(events),
                "metrics_scanned": len(recent_metrics),
                "metrics_total": int(metric_summary.get("metrics_total") or 0),
                "warnings_total": sum(1 for finding in findings if finding.severity == Severity.WARNING),
                "blocking_findings_total": sum(1 for finding in findings if finding.severity == Severity.BLOCK),
                "network_used": False,
                "external_api_used": False,
                "ui_required": False,
                "remote_telemetry_enabled": False,
                "preliminary": True,
            },
            "store": store_data,
            "runtime_signals": {
                **runtime_status,
                "span_types": dict(sorted(span_type_counts.items())),
                "span_statuses": dict(sorted(span_status_counts.items())),
                "event_types": dict(sorted(event_type_counts.items())),
                "metric_categories_recent": dict(sorted(metric_category_counts.items())),
                "metric_statuses_recent": dict(sorted(metric_status_counts.items())),
                "metric_summary": metric_summary,
                "missing_recommended_span_types": missing_span_types,
                "missing_recommended_metric_categories": missing_categories,
                "sample_trace_ids": trace_ids[:10],
            },
            "control_plane": {
                "required_documents": document_status,
                "miasi_tools": registry_status["tools"],
                "miasi_policy_rules": registry_status["policy_rules"],
            },
            "capabilities": {
                "trace_context": "implemented",
                "trace_store": "implemented",
                "metrics_collector": "implemented",
                "agentops_instrumentation": "implemented-initial",
                "trace_metrics_cli": "implemented-initial",
                "otel_dry_run_exporter": "implemented-initial",
                "agentops_quality_gate": "implemented-initial",
                "dashboard_ui": "not_implemented_phase_f",
                "remote_telemetry": "blocked_by_default",
            },
            "recommendations": [
                "Mantener `agentops status` como gate de entrada para Fase F/UI.",
                "Visualizar estas señales desde ApplicationService/API sin duplicar lógica en UI.",
                "Mantener OpenTelemetry remoto como opt-in explícito, nunca por defecto.",
            ],
        }
        return CommandResult(
            command="agentops status",
            ok=not blocked,
            exit_code=ExitCode.PASS if not blocked else ExitCode.BLOCK,
            message="AgentOps quality gate passed." if not blocked else "AgentOps quality gate blocked.",
            data=data,
            findings=findings,
        )

    def _registry_status(self) -> dict[str, dict[str, bool]]:
        tools_payload = _read_json(self.root / ".devpilot" / "miasi" / "tool_registry.json")
        policy_payload = _read_json(self.root / ".devpilot" / "miasi" / "policy_matrix.json")
        tool_ids = {
            str(item.get("tool_id"))
            for item in tools_payload.get("tools", [])
            if isinstance(item, dict) and item.get("tool_id")
        }
        rule_ids = {
            str(item.get("rule_id"))
            for item in policy_payload.get("rules", [])
            if isinstance(item, dict) and item.get("rule_id")
        }
        return {
            "tools": {tool_id: tool_id in tool_ids for tool_id in self.REQUIRED_TOOL_IDS},
            "policy_rules": {rule_id: rule_id in rule_ids for rule_id in self.REQUIRED_POLICY_RULE_IDS},
        }


def _agentops_safe_limit(limit: int) -> int:
    try:
        parsed = int(limit)
    except (TypeError, ValueError):
        parsed = 100
    return max(10, min(parsed, 500))


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}
