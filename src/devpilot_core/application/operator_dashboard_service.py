from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.portfolio import OperatorDashboardAggregator, OperatorDashboardAggregatorOptions


class OperatorDashboardApplicationService:
    """Application boundary for POST-H-015 local operator dashboard snapshots.

    POST-H-015-C exposes the POST-H-015-B aggregator through ApplicationService
    so API/UI clients do not import portfolio internals directly. Report
    persistence remains explicit through `write_report=True` and is limited to
    outputs/reports by the aggregator.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def dashboard(self, *, write_report: bool = False) -> CommandResult:
        return OperatorDashboardAggregator(
            self.root,
            OperatorDashboardAggregatorOptions(write_report=write_report),
        ).build()
