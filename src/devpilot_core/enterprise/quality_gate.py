from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

from .reports import EnterpriseThreatModelReportOptions, EnterpriseThreatModelReporter

_BLOCKING_SEVERITIES = {Severity.FAIL, Severity.BLOCK, Severity.ERROR}


@dataclass(frozen=True)
class EnterpriseThreatModelQualityGateOptions(EnterpriseThreatModelReportOptions):
    """Paths used by the POST-H-022-D enterprise design-only quality subgate."""


class EnterpriseThreatModelQualityGate:
    """Validate enterprise deployment design artifacts as a quality subgate.

    The subgate consumes the read-only report in memory. It does not write the
    report, does not enable enterprise deployment, and does not contact network
    services or read secrets.
    """

    def __init__(self, root: Path, options: EnterpriseThreatModelQualityGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or EnterpriseThreatModelQualityGateOptions()

    def run(self) -> CommandResult:
        report_result = EnterpriseThreatModelReporter(
            self.root,
            EnterpriseThreatModelReportOptions(
                threat_model_path=self.options.threat_model_path,
                control_matrix_path=self.options.control_matrix_path,
                output_json_path=self.options.output_json_path,
                output_markdown_path=self.options.output_markdown_path,
            ),
        ).build(write_report=False)
        report = report_result.data.get("report", {}) if isinstance(report_result.data, dict) else {}
        summary = dict(report_result.data.get("summary", {})) if isinstance(report_result.data, dict) else {}
        summary.update(
            {
                "created_by": "POST-H-022-D",
                "quality_gate_subgate": "enterprise-threat-model-design-only",
                "report_ok": report_result.ok,
                "report_schema_id": report.get("schema_id") if isinstance(report, dict) else None,
                "reports_written": False,
            }
        )

        findings: list[Finding] = list(report_result.findings)
        findings.extend(self._invariant_findings(summary))
        blocking = [finding for finding in findings if finding.severity in _BLOCKING_SEVERITIES]
        summary["blocking_findings_total"] = len(blocking)
        ok = not blocking
        return CommandResult(
            command="quality enterprise-threat-model-design-only",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Enterprise threat model design-only quality gate passed." if ok else "Enterprise threat model design-only quality gate blocked.",
            data={
                "summary": summary,
                "report": report,
                "notes": [
                    "POST-H-022-D integrates enterprise deployment threat model validation into hardening/industrial quality gates.",
                    "The subgate is design-only evidence and does not authorize enterprise deployment or enterprise readiness claims.",
                    "No report files are written by the quality gate; optional report writing is left to explicit caller flows.",
                ],
            },
            findings=findings
            or [
                Finding(
                    "ENTERPRISE_THREAT_MODEL_QUALITY_GATE_PASS",
                    "Enterprise deployment design-only quality gate passed with runtime enablement blocked.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _invariant_findings(self, summary: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        if summary.get("decision_status") != "design-only":
            findings.append(Finding("ENTERPRISE_GATE_DESIGN_ONLY_BLOCKED", "Enterprise quality gate requires design-only decision status.", Severity.BLOCK, metadata={"decision_status": summary.get("decision_status")}))
        if summary.get("required_not_implemented_total", 0) <= 0:
            findings.append(Finding("ENTERPRISE_GATE_BLOCKERS_REQUIRED", "Enterprise quality gate requires explicit required-not-implemented blockers.", Severity.BLOCK))
        if summary.get("enterprise_ready") is True or summary.get("enterprise_ready_claimed") is True:
            findings.append(Finding("ENTERPRISE_GATE_READY_CLAIM_BLOCKED", "Enterprise quality gate blocks enterprise-ready claims.", Severity.BLOCK))
        for flag in (
            "enterprise_deployment_enabled",
            "remote_execution_enabled",
            "secure_transport_implemented",
            "compliance_certification_claim",
            "network_used",
            "external_api_used",
            "mutations_performed",
            "source_mutations_performed",
            "secrets_read",
            "remote_execution_used",
            "reports_written",
        ):
            if summary.get(flag) is True:
                findings.append(Finding("ENTERPRISE_GATE_UNSAFE_FLAG_BLOCKED", "Enterprise quality gate blocks unsafe safety flags.", Severity.BLOCK, metadata={"flag": flag}))
        return findings


def _exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS
