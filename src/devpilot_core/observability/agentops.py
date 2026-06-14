from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding
from devpilot_core.observability.events import EventRecord
from devpilot_core.observability.metrics import MetricsCollector
from devpilot_core.observability.trace_store import TraceStore
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
