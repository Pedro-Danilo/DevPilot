from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

from .threat_model import EnterpriseThreatModelValidationOptions, EnterpriseThreatModelValidator

_BLOCKING_SEVERITIES = {Severity.FAIL, Severity.BLOCK, Severity.ERROR}


@dataclass(frozen=True)
class EnterpriseThreatModelReportOptions(EnterpriseThreatModelValidationOptions):
    """Options for the POST-H-022-D read-only enterprise threat report."""

    output_json_path: str = "outputs/reports/enterprise_threat_model_report.json"
    output_markdown_path: str = "outputs/reports/enterprise_threat_model_report.md"


class EnterpriseThreatModelReporter:
    """Build a schema-backed enterprise threat-model report in read-only mode."""

    def __init__(self, root: Path, options: EnterpriseThreatModelReportOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or EnterpriseThreatModelReportOptions()

    def build(self, *, write_report: bool = False) -> CommandResult:
        validation = EnterpriseThreatModelValidator(
            self.root,
            EnterpriseThreatModelValidationOptions(
                threat_model_path=self.options.threat_model_path,
                control_matrix_path=self.options.control_matrix_path,
            ),
        ).validate()
        summary = dict((validation.data or {}).get("summary") or {})
        blocking = [finding for finding in validation.findings if finding.severity in _BLOCKING_SEVERITIES]
        report = self._report(summary, validation.findings)
        reports: dict[str, str] = {}
        if write_report:
            reports = self._write_report(report)
        if write_report:
            summary["reports_written"] = True
        else:
            summary["reports_written"] = False
        summary["blocking_findings_total"] = len(blocking)
        report["summary"] = summary
        report["blocking_findings_total"] = len(blocking)
        ok = validation.ok and not blocking
        return CommandResult(
            command="enterprise threat-model report",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Enterprise threat model report built in read-only mode." if ok else "Enterprise threat model report detected blockers.",
            data={
                "summary": summary,
                "report": report,
                "reports": reports,
                "source_paths": {
                    "threat_model": self.options.threat_model_path,
                    "control_matrix": self.options.control_matrix_path,
                },
            },
            findings=validation.findings
            or [
                Finding(
                    "ENTERPRISE_THREAT_MODEL_REPORT_PASS",
                    "Enterprise threat model report confirms design-only state with no enterprise runtime enablement.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _report(self, summary: dict[str, Any], findings: list[Finding]) -> dict[str, Any]:
        blocking = [finding for finding in findings if finding.severity in _BLOCKING_SEVERITIES]
        return {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-ENTERPRISE-THREAT-MODEL-REPORT-V1",
            "report_id": "devpilot-enterprise-threat-model-report",
            "created_by": "POST-H-022-D",
            "status": "implemented-initial",
            "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "ok": len(blocking) == 0,
            "decision_status": "design-only",
            "enterprise_deployment_enabled": False,
            "remote_execution_enabled": False,
            "secure_transport_implemented": False,
            "compliance_certification_claim": False,
            "enterprise_ready_claimed": False,
            "blocking_findings_total": len(blocking),
            "summary": summary,
            "required_before_enterprise": [
                "enterprise identity lifecycle",
                "enterprise RBAC and negative authorization tests",
                "secure transport architecture and implementation",
                "secrets management and rotation model",
                "tenant/workspace isolation",
                "retention and audit evidence policy",
                "future ADR approving any enterprise runtime enablement",
            ],
            "no_go_gates": {
                "enterprise_deployment_enabled": False,
                "remote_execution_enabled": False,
                "secure_transport_implemented": False,
                "compliance_certification_claim": False,
                "enterprise_ready_claimed": False,
                "network_dependency_introduced": False,
                "secrets_introduced": False,
                "source_mutations_performed": False,
            },
            "findings": [finding.to_dict() for finding in findings],
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "enterprise_deployment_enabled": False,
                "remote_execution_enabled": False,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "secrets_read": False,
                "compliance_certification_claim": False,
            },
            "notes": [
                "Enterprise report != enterprise readiness.",
                "POST-H-022-D is a design-only validator/report; it does not authorize enterprise deployment.",
                "Required-not-implemented controls remain blockers until future implementation and ADR approval.",
            ],
        }

    def _write_report(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self._resolve(self.options.output_json_path)
        markdown_path = self._resolve(self.options.output_markdown_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(_markdown(report), encoding="utf-8")
        return {"json": self.options.output_json_path, "markdown": self.options.output_markdown_path}

    def _resolve(self, value: str | Path) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.root / path


def _markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    lines = [
        "# Enterprise Threat Model Report",
        "",
        f"- created_by: `{report.get('created_by')}`",
        f"- decision_status: `{report.get('decision_status')}`",
        f"- ok: `{report.get('ok')}`",
        f"- enterprise_deployment_enabled: `{report.get('enterprise_deployment_enabled')}`",
        f"- remote_execution_enabled: `{report.get('remote_execution_enabled')}`",
        f"- enterprise_ready_claimed: `{report.get('enterprise_ready_claimed')}`",
        f"- required_not_implemented_total: `{summary.get('required_not_implemented_total')}`",
        f"- blocking_findings_total: `{report.get('blocking_findings_total')}`",
        "",
        "Enterprise report != enterprise readiness. This report is design-only and read-only.",
        "",
    ]
    return "\n".join(lines)


def _exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS
