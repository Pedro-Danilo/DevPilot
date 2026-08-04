from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult, Finding, Severity
from devpilot_core.observability import AgentOpsGateOptions, AgentOpsQualityGate, OTelDryRunExporter, OTelExportOptions, TraceQueryService

from .ui_workspace_context import UiWorkspaceContextResolver


class ObservabilityApplicationService:
    """Application-facing AgentOps/observability facade with explicit UI scope."""

    def __init__(self, root: Path, *, context_resolver: UiWorkspaceContextResolver | None = None) -> None:
        self.root = root.resolve()
        self.context_resolver = context_resolver or UiWorkspaceContextResolver(self.root)

    def trace_report(self, *, limit: int = 20, include_events: bool = True, include_metrics: bool = True, scope: str = "active") -> CommandResult:
        selected_root, selected_scope, findings = self._root_for_scope(scope)
        result = TraceQueryService(selected_root).report(limit=limit, include_events=include_events, include_metrics=include_metrics)
        return self._decorate(result, selected_root=selected_root, selected_scope=selected_scope, findings=findings)

    def trace_inspect(self, trace_id: str, *, limit: int = 100, scope: str = "active") -> CommandResult:
        selected_root, selected_scope, findings = self._root_for_scope(scope)
        result = TraceQueryService(selected_root).inspect(trace_id, limit=limit)
        return self._decorate(result, selected_root=selected_root, selected_scope=selected_scope, findings=findings)

    def metrics_summary(self, *, category: str | None = None, limit: int = 50, scope: str = "active") -> CommandResult:
        selected_root, selected_scope, findings = self._root_for_scope(scope)
        result = TraceQueryService(selected_root).metrics_summary(category=category, limit=limit)
        return self._decorate(result, selected_root=selected_root, selected_scope=selected_scope, findings=findings)

    def telemetry_export_dry_run(self, *, trace_id: str | None = None, limit: int = 20, include_metrics: bool = True) -> CommandResult:
        return OTelDryRunExporter(self.root).export(OTelExportOptions(trace_id=trace_id, limit=limit, include_metrics=include_metrics, dry_run=True))

    def agentops_status(self, *, limit: int = 100, strict_runtime_signals: bool = False) -> CommandResult:
        return AgentOpsQualityGate(self.root).status(AgentOpsGateOptions(limit=limit, strict_runtime_signals=strict_runtime_signals))

    def _root_for_scope(self, scope: str) -> tuple[Path, str, list[Finding]]:
        normalized = str(scope or "active").strip().lower()
        context = self.context_resolver.resolve()
        findings = list(context.findings)
        if normalized == "platform":
            return self.root, "platform", findings
        if normalized in {"active", "workspace"} and context.valid and context.active_workspace_root:
            return context.active_workspace_root, "workspace", findings
        if normalized == "workspace":
            findings.append(
                Finding(
                    "OBSERVABILITY_WORKSPACE_SCOPE_UNAVAILABLE",
                    "Workspace observability scope was requested but no valid active workspace is configured; platform scope was used.",
                    Severity.WARNING,
                )
            )
        return self.root, "platform", findings

    def _decorate(self, result: CommandResult, *, selected_root: Path, selected_scope: str, findings: list[Finding]) -> CommandResult:
        data = dict(result.data)
        summary = data.get("summary")
        summary = dict(summary) if isinstance(summary, dict) else {}
        summary.update(
            {
                "ui_scope": selected_scope,
                "ui_scope_root": str(selected_root).replace("\\", "/"),
                "workspace_context": self.context_resolver.resolve().summary(),
            }
        )
        data["summary"] = summary
        return CommandResult(
            command=result.command,
            ok=result.ok,
            exit_code=result.exit_code,
            message=result.message,
            data=data,
            findings=findings + list(result.findings),
        )
