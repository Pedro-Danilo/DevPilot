from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.remote.readiness import RemoteReadinessChecker, RemoteReadinessOptions

DEFAULT_REMOTE_READINESS_REPORT_JSON = "outputs/reports/remote_readiness_report.json"
DEFAULT_REMOTE_READINESS_REPORT_MD = "outputs/reports/remote_readiness_report.md"


@dataclass(frozen=True)
class RemoteReadinessReportOptions(RemoteReadinessOptions):
    """Options for POST-H-021-C read-only readiness report generation."""

    output_json: str = DEFAULT_REMOTE_READINESS_REPORT_JSON
    output_markdown: str = DEFAULT_REMOTE_READINESS_REPORT_MD


class RemoteReadinessReporter:
    """Generate and optionally persist remote readiness report evidence.

    Report writing is explicit and constrained to the configured output paths.
    The default paths are under outputs/reports, which remain runtime evidence
    and must not be shipped in clean repository ZIPs.
    """

    def __init__(self, root: Path, *, options: RemoteReadinessReportOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or RemoteReadinessReportOptions()

    def build(self, *, write_report: bool = False) -> CommandResult:
        check = RemoteReadinessChecker(self.root, options=self.options).check()
        findings = list(check.findings)
        reports: dict[str, str] = {}
        if write_report and check.data.get("report"):
            try:
                reports = self.write(check.data["report"])
            except ValueError as exc:
                findings.append(Finding("REMOTE_READINESS_REPORT_OUTPUT_BLOCKED", "Remote readiness report output path is invalid.", Severity.BLOCK, metadata={"error": str(exc)}))

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        summary = dict(check.data.get("summary", {}))
        summary.update(
            {
                "reports_written": bool(reports),
                "output_json": reports.get("json"),
                "output_markdown": reports.get("markdown"),
                "blocking_findings_total": len(blocking),
            }
        )
        report = dict(check.data.get("report", {}))
        if report:
            report["summary"] = summary
            report["blocking_findings_total"] = len(blocking)
            report["ok"] = not blocking
        ok = check.ok and not blocking
        return CommandResult(
            "remote runner readiness",
            ok,
            ExitCode.PASS if ok else _exit_code(blocking),
            "Remote readiness report generated locally." if ok else "Remote readiness report blocked.",
            data={
                "summary": summary,
                "report": report,
                "reports": reports,
                "criteria": check.data.get("criteria", {}),
                "runner_status": check.data.get("runner_status", {}),
            },
            findings=findings
            or [
                Finding(
                    "REMOTE_READINESS_REPORT_PASS",
                    "Remote readiness report generated locally without remote execution.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def write(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self._resolve_output(self.options.output_json)
        markdown_path = self._resolve_output(self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(self._markdown(report), encoding="utf-8")
        return {"json": _rel(self.root, json_path), "markdown": _rel(self.root, markdown_path)}

    def _markdown(self, report: dict[str, Any]) -> str:
        summary = report.get("summary", {})
        rows = [
            ("readiness_level", report.get("readiness_level")),
            ("ok", report.get("ok")),
            ("decision_status", report.get("decision_status")),
            ("future_adr_required", report.get("future_adr_required")),
            ("remote_runner_enabled", report.get("remote_runner_enabled")),
            ("remote_execution_used", report.get("remote_execution_used")),
            ("network_used", report.get("network_used")),
            ("external_api_used", report.get("external_api_used")),
            ("credentials_required", report.get("credentials_required")),
            ("secrets_read", report.get("secrets_read")),
            ("blocking_findings_total", report.get("blocking_findings_total")),
        ]
        lines = [
            "---",
            'doc_id: "POST-H-021-C-REMOTE-READINESS-REPORT-RUNTIME"',
            'status: "generated"',
            'owner: "Ordóñez"',
            'created_by: "POST-H-021-C"',
            "---",
            "",
            "# Remote readiness report",
            "",
            "Reporte local read-only. No autoriza ejecución remota, transporte, credenciales, red ni shell.",
            "",
            "| Metric | Value |",
            "|---|---:|",
        ]
        for key, value in rows:
            lines.append(f"| `{key}` | `{value}` |")
        lines.extend(["", "## Required before enablement", ""])
        for item in report.get("required_before_enablement", []):
            lines.append(f"- `{item}`")
        lines.extend(["", "## Safety", ""])
        for key, value in sorted((report.get("safety") or {}).items()):
            lines.append(f"- `{key}`: `{value}`")
        lines.extend(["", "## Summary", "", f"- schema_valid: `{summary.get('schema_valid')}`", ""])
        return "\n".join(lines)

    def _resolve_output(self, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = self.root / path
        resolved = path.resolve()
        if resolved.exists() and resolved.is_dir():
            raise ValueError(f"output path points to a directory: {resolved}")
        return resolved


def _exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)
