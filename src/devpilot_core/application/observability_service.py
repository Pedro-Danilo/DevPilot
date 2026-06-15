from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.observability import AgentOpsGateOptions, AgentOpsQualityGate, OTelDryRunExporter, OTelExportOptions, TraceQueryService


class ObservabilityApplicationService:
    """Application-facing AgentOps/observability facade."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def trace_report(self, *, limit: int = 20, include_events: bool = True, include_metrics: bool = True) -> CommandResult:
        return TraceQueryService(self.root).report(limit=limit, include_events=include_events, include_metrics=include_metrics)

    def trace_inspect(self, trace_id: str, *, limit: int = 100) -> CommandResult:
        return TraceQueryService(self.root).inspect(trace_id, limit=limit)

    def metrics_summary(self, *, category: str | None = None, limit: int = 50) -> CommandResult:
        return TraceQueryService(self.root).metrics_summary(category=category, limit=limit)

    def telemetry_export_dry_run(self, *, trace_id: str | None = None, limit: int = 20, include_metrics: bool = True) -> CommandResult:
        return OTelDryRunExporter(self.root).export(OTelExportOptions(trace_id=trace_id, limit=limit, include_metrics=include_metrics, dry_run=True))

    def agentops_status(self, *, limit: int = 100, strict_runtime_signals: bool = False) -> CommandResult:
        return AgentOpsQualityGate(self.root).status(AgentOpsGateOptions(limit=limit, strict_runtime_signals=strict_runtime_signals))
