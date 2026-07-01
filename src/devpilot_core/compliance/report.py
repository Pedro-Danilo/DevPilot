from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.compliance.evidence import ComplianceEvidenceCollector, ComplianceEvidenceCollectorOptions
from devpilot_core.schemas import SchemaValidator

DEFAULT_COMPLIANCE_MAPPING_REPORT_JSON = "outputs/reports/compliance_mapping_report.json"
DEFAULT_COMPLIANCE_MAPPING_REPORT_MD = "outputs/reports/compliance_mapping_report.md"
DEFAULT_COMPLIANCE_MAPPING_REPORT_SCHEMA = "ComplianceMappingReport"
_BLOCKING_SEVERITIES = {Severity.FAIL, Severity.BLOCK, Severity.ERROR}


@dataclass(frozen=True)
class ComplianceMappingReportOptions:
    """Options for POST-H-020-C compliance mapping report generation."""

    control_mappings_path: str = ".devpilot/compliance/control_mappings.json"
    evidence_mappings_path: str = ".devpilot/compliance/evidence_mappings.json"
    output_json: str = DEFAULT_COMPLIANCE_MAPPING_REPORT_JSON
    output_markdown: str = DEFAULT_COMPLIANCE_MAPPING_REPORT_MD


class ComplianceMappingReporter:
    """Generate local non-certifying compliance mapping reports.

    The reporter composes the semantic validator and metadata-only evidence
    collector. It writes reports only when requested. Defaults stay under
    outputs/reports, while explicit absolute output paths are accepted for
    test harnesses and controlled integrations. It never executes mapped
    source commands or exports evidence outside the generated report.
    """

    def __init__(self, root: Path, options: ComplianceMappingReportOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ComplianceMappingReportOptions()

    def build(self, *, write_report: bool = False) -> CommandResult:
        collection = ComplianceEvidenceCollector(
            self.root,
            ComplianceEvidenceCollectorOptions(
                control_mappings_path=self.options.control_mappings_path,
                evidence_mappings_path=self.options.evidence_mappings_path,
            ),
        ).collect()
        summary = collection.data.get("summary", {}) if isinstance(collection.data, dict) else {}
        findings = list(collection.findings)
        report = self._report(summary, findings)
        schema_result = SchemaValidator(self.root).validate_payload(
            schema=DEFAULT_COMPLIANCE_MAPPING_REPORT_SCHEMA,
            payload=report,
            instance_label=self.options.output_json,
        )
        if not schema_result.ok:
            findings.extend(schema_result.findings)
        blocking = [finding for finding in findings if finding.severity in _BLOCKING_SEVERITIES]

        reports: dict[str, str] = {}
        if write_report:
            try:
                reports = self.write(report)
            except ValueError as exc:
                findings.append(Finding("COMPLIANCE_MAPPING_REPORT_OUTPUT_BLOCKED", "Compliance report output path is invalid.", Severity.BLOCK, metadata={"error": str(exc)}))
                blocking = [finding for finding in findings if finding.severity in _BLOCKING_SEVERITIES]

        result_summary = dict(summary)
        result_summary.update(
            {
                "schema_valid": schema_result.ok,
                "reports_written": bool(write_report),
                "output_json": reports.get("json"),
                "output_markdown": reports.get("markdown"),
                "blocking_findings_total": len(blocking),
            }
        )
        ok = schema_result.ok and not blocking
        return CommandResult(
            command="compliance mapping report",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Compliance mapping report generated locally." if ok else "Compliance mapping report found blocking gaps.",
            data={
                "summary": result_summary,
                "report": report,
                "evidence": collection.data.get("evidence", []) if isinstance(collection.data, dict) else [],
                "reports": reports,
                "notes": [
                    "POST-H-020-C reports are local engineering evidence aids only.",
                    "No source_command values were executed and no evidence was sent outside the workspace.",
                    "This is not certification, legal advice or an external audit result.",
                ],
            },
            findings=findings
            or [
                Finding(
                    "COMPLIANCE_MAPPING_REPORT_PASS",
                    "Compliance mapping report generated locally without certification or legal advice claims.",
                    Severity.INFO,
                    metadata=result_summary,
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

    def _report(self, summary: dict[str, Any], findings: list[Finding]) -> dict[str, Any]:
        blocking = [finding for finding in findings if finding.severity in _BLOCKING_SEVERITIES]
        return {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-COMPLIANCE-MAPPING-REPORT-V1",
            "created_by": "POST-H-020-A",
            "report_id": "devpilot-compliance-mapping-report",
            "generated_at_utc": _now_utc(),
            "pack_id": str(summary.get("pack_id") or "unknown"),
            "ok": not blocking,
            "certification_claimed": False,
            "legal_advice_claimed": False,
            "controls_total": int(summary.get("controls_total", 0) or 0),
            "controls_mapped": int(summary.get("controls_mapped", 0) or 0),
            "controls_with_evidence": int(summary.get("controls_with_evidence", 0) or 0),
            "controls_missing_evidence": int(summary.get("controls_missing_evidence", 0) or 0),
            "blocking_findings_total": len(blocking),
            "disclaimer_present": True,
            "domain_coverage": summary.get("domain_coverage", {}),
            "findings": [finding.to_dict() for finding in findings],
            "safety": {
                "local_first": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
            },
        }

    def _markdown(self, report: dict[str, Any]) -> str:
        rows = [
            ("pack_id", report.get("pack_id")),
            ("ok", report.get("ok")),
            ("controls_total", report.get("controls_total")),
            ("controls_mapped", report.get("controls_mapped")),
            ("controls_with_evidence", report.get("controls_with_evidence")),
            ("controls_missing_evidence", report.get("controls_missing_evidence")),
            ("blocking_findings_total", report.get("blocking_findings_total")),
            ("certification_claimed", report.get("certification_claimed")),
            ("legal_advice_claimed", report.get("legal_advice_claimed")),
        ]
        lines = [
            "---",
            'doc_id: "POST-H-020-C-COMPLIANCE-MAPPING-REPORT-RUNTIME"',
            'status: "generated"',
            'owner: "Ordóñez"',
            'created_by: "POST-H-020-C"',
            "---",
            "",
            "# Compliance mapping report",
            "",
            "Reporte local de mapeo de compliance. Es evidencia de ingeniería, no certificación, asesoría legal ni auditoría externa.",
            "",
            "| Metric | Value |",
            "|---|---:|",
        ]
        for key, value in rows:
            lines.append(f"| `{key}` | `{value}` |")
        lines.extend(["", "## Domain coverage", ""])
        for domain, count in sorted((report.get("domain_coverage") or {}).items()):
            lines.append(f"- `{domain}`: `{count}`")
        lines.extend(["", "## Findings", ""])
        if report.get("findings"):
            for finding in report["findings"]:
                lines.append(f"- `{finding.get('severity')}` `{finding.get('id')}`: {finding.get('message')}")
        else:
            lines.append("- Sin findings.")
        lines.extend(["", "## Limits", "", "No se ejecutaron comandos declarados, no se usó red/API externa y no se enviaron evidencias a terceros.", ""])
        return "\n".join(lines)

    def _resolve_output(self, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = self.root / path
        resolved = path.resolve()
        if resolved.exists() and resolved.is_dir():
            raise ValueError(f"output path points to a directory: {resolved}")
        return resolved


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
        return str(path).replace("\\", "/")
