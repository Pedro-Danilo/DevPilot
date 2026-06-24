from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.maturity import MaturityDashboardBuilder, MaturityDashboardGateOptions, MaturityDashboardQualityGate


@dataclass(frozen=True)
class MaturityReportPaths:
    """Root-relative paths generated for the maturity dashboard reports."""

    json: str
    markdown: str

    def to_dict(self) -> dict[str, str]:
        return {"json": self.json, "markdown": self.markdown}


class MaturityApplicationService:
    """Application boundary for POST-H-002 maturity dashboard operations.

    POST-H-002-D exposes the POST-H-002-C builder through ApplicationService
    without letting CLI/API clients import maturity core internals directly.
    Report persistence is explicit and writes only the dashboard JSON/Markdown
    artifacts under outputs/reports.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def dashboard(self, *, write_report: bool = False) -> CommandResult:
        """Build the local maturity dashboard and optionally persist reports."""

        build_result = MaturityDashboardBuilder(self.root).build()
        result = build_result.to_command_result()
        result = CommandResult(
            command="maturity dashboard",
            ok=result.ok,
            exit_code=result.exit_code,
            message=(
                "Maturity dashboard generated from POST-H evidence."
                if result.ok
                else "Maturity dashboard generation has blocking findings."
            ),
            data=dict(result.data or {}),
            findings=list(result.findings),
        )
        if write_report and result.ok:
            paths = self.write_dashboard_reports(result)
            data = dict(result.data or {})
            data["reports"] = paths.to_dict()
            data["reports_written"] = True
            result = CommandResult(
                command=result.command,
                ok=result.ok,
                exit_code=result.exit_code,
                message=result.message,
                data=data,
                findings=result.findings,
            )
        elif write_report and not result.ok:
            result = CommandResult(
                command=result.command,
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Maturity dashboard reports were not written because the dashboard has blocking findings.",
                data={**dict(result.data or {}), "reports_written": False},
                findings=[
                    *result.findings,
                    Finding(
                        id="MATURITY_DASHBOARD_REPORT_WRITE_BLOCKED",
                        message="Report persistence is blocked until the maturity dashboard validates successfully.",
                        severity=Severity.BLOCK,
                        metadata={"component": "MaturityApplicationService", "sprint": "POST-H-002-D"},
                    ),
                ],
            )
        return result


    def dashboard_gate(self, *, write_report: bool = False) -> CommandResult:
        """Run the POST-H-002-E maturity dashboard quality gate."""

        return MaturityDashboardQualityGate(
            self.root,
            options=MaturityDashboardGateOptions(write_report=write_report),
        ).run()

    def write_dashboard_reports(self, result: CommandResult) -> MaturityReportPaths:
        """Write canonical dashboard JSON/Markdown outputs under outputs/reports."""

        reports_dir = (self.root / "outputs" / "reports").resolve()
        try:
            reports_dir.relative_to(self.root)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise ValueError("Maturity dashboard reports must be written inside the workspace.") from exc
        reports_dir.mkdir(parents=True, exist_ok=True)
        json_path = reports_dir / "maturity_dashboard.json"
        markdown_path = reports_dir / "maturity_dashboard.md"
        data: dict[str, Any] = dict(result.data or {})
        dashboard_payload = data.get("dashboard")
        markdown_payload = str(data.get("markdown") or "")
        if not isinstance(dashboard_payload, dict):
            raise ValueError("Maturity dashboard JSON payload is not available for report writing.")
        json_path.write_text(json.dumps(dashboard_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(markdown_payload, encoding="utf-8")
        return MaturityReportPaths(
            json=_relative(json_path, self.root),
            markdown=_relative(markdown_path, self.root),
        )


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
