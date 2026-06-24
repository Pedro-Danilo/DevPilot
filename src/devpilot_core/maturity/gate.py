from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator


@dataclass(frozen=True)
class MaturityDashboardGateOptions:
    """Options for the POST-H-002-E maturity dashboard quality gate.

    The gate is read-only by default. `write_report=True` delegates report
    persistence to the application boundary and writes only the canonical
    `outputs/reports/maturity_dashboard.{json,md}` files.
    """

    write_report: bool = False
    validate_report_file: bool = True


class MaturityDashboardQualityGate:
    """Quality gate for the POST-H-002 maturity dashboard.

    POST-H-002-E connects the evidence-backed maturity dashboard to the local
    quality-gate ecosystem without replacing existing gates. The gate verifies
    structural schema validity, safety no-go invariants, evidence completeness,
    roadmap alignment and optional output report integrity.
    """

    REQUIRED_NO_GO_CAPABILITIES = {
        "no-go-sec-001": "POST-H-021",
        "no-go-sec-002": "POST-H-018",
        "no-go-sec-003": "POST-H-019",
    }
    REQUIRED_ROADMAP_MILESTONES = {"POST-H-002", "POST-H-003", "POST-H-004", "POST-H-025"}
    SAFETY_FLAGS = {
        "remote_execution_enabled",
        "connector_write_enabled",
        "plugin_execution_enabled",
        "external_apis_enabled_by_default",
        "network_used",
        "mutations_performed",
    }

    def __init__(self, root: Path, *, options: MaturityDashboardGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or MaturityDashboardGateOptions()

    def run(self) -> CommandResult:
        # Local import avoids an import cycle: ApplicationService imports the
        # maturity service, and the maturity service exposes this gate.
        from devpilot_core.application import ApplicationService

        dashboard_result = ApplicationService(self.root).maturity_dashboard(write_report=self.options.write_report)
        findings = list(dashboard_result.findings)
        checks: dict[str, bool] = {
            "dashboard_command_ok": dashboard_result.ok,
            "schema_valid": False,
            "summary_thresholds_valid": False,
            "safety_no_go_flags_false": False,
            "no_go_capabilities_blocked": False,
            "source_evidence_present": False,
            "roadmap_alignment_present": False,
            "reports_valid": not self.options.write_report,
            "no_network_external_api_or_source_mutation": False,
        }

        data = dict(dashboard_result.data or {})
        dashboard = data.get("dashboard")
        if not dashboard_result.ok or not isinstance(dashboard, Mapping):
            findings.append(
                Finding(
                    id="MATURITY_DASHBOARD_GATE_BUILD_BLOCKED",
                    message="Maturity dashboard quality gate cannot proceed because dashboard generation failed.",
                    severity=Severity.BLOCK,
                    metadata={"write_report": self.options.write_report},
                )
            )
            return self._result(False, checks, findings, dashboard_result)

        schema_result = SchemaValidator(self.root).validate_payload(
            schema="MaturityDashboard",
            payload=dict(dashboard),
            instance_label="in-memory:maturity-dashboard-gate",
        )
        findings.extend(schema_result.findings)
        checks["schema_valid"] = schema_result.ok

        summary = dashboard.get("summary") if isinstance(dashboard.get("summary"), Mapping) else {}
        checks["summary_thresholds_valid"] = self._summary_thresholds_valid(summary)
        if not checks["summary_thresholds_valid"]:
            findings.append(
                Finding(
                    id="MATURITY_DASHBOARD_GATE_SUMMARY_BLOCK",
                    message="Maturity dashboard summary does not satisfy POST-H-002 closure thresholds.",
                    severity=Severity.BLOCK,
                    metadata={"summary": dict(summary)},
                )
            )

        safety = dashboard.get("safety") if isinstance(dashboard.get("safety"), Mapping) else {}
        unsafe_flags = {flag: safety.get(flag) for flag in self.SAFETY_FLAGS if safety.get(flag) is not False}
        checks["safety_no_go_flags_false"] = not unsafe_flags
        checks["no_network_external_api_or_source_mutation"] = not unsafe_flags and data.get("network_used") is False and data.get("external_api_used") is False and data.get("mutations_performed") is False
        if unsafe_flags:
            findings.append(
                Finding(
                    id="MATURITY_DASHBOARD_GATE_SAFETY_BLOCK",
                    message="Maturity dashboard safety flags must remain false.",
                    severity=Severity.BLOCK,
                    metadata={"unsafe_flags": unsafe_flags},
                )
            )

        capabilities = dashboard.get("capabilities") if isinstance(dashboard.get("capabilities"), list) else []
        checks["no_go_capabilities_blocked"] = self._no_go_capabilities_blocked(capabilities)
        if not checks["no_go_capabilities_blocked"]:
            findings.append(
                Finding(
                    id="MATURITY_DASHBOARD_GATE_NO_GO_BLOCK",
                    message="Required no-go capabilities are not blocked or not mapped to the expected roadmap milestones.",
                    severity=Severity.BLOCK,
                    metadata={"required_no_go_capabilities": self.REQUIRED_NO_GO_CAPABILITIES},
                )
            )

        checks["source_evidence_present"] = self._source_evidence_present(capabilities)
        if not checks["source_evidence_present"]:
            findings.append(
                Finding(
                    id="MATURITY_DASHBOARD_GATE_EVIDENCE_BLOCK",
                    message="Every maturity capability must include at least one source evidence path.",
                    severity=Severity.BLOCK,
                )
            )

        roadmap_alignment = dashboard.get("roadmap_alignment") if isinstance(dashboard.get("roadmap_alignment"), list) else []
        checks["roadmap_alignment_present"] = self._roadmap_alignment_present(roadmap_alignment)
        if not checks["roadmap_alignment_present"]:
            findings.append(
                Finding(
                    id="MATURITY_DASHBOARD_GATE_ROADMAP_BLOCK",
                    message="Maturity dashboard is missing required post-H roadmap alignment milestones.",
                    severity=Severity.BLOCK,
                    metadata={"required_milestones": sorted(self.REQUIRED_ROADMAP_MILESTONES)},
                )
            )

        if self.options.write_report and self.options.validate_report_file:
            checks["reports_valid"] = self._reports_valid(data, findings)

        blocking_findings = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        ok = all(checks.values()) and schema_result.ok and not blocking_findings
        if ok:
            findings.append(
                Finding(
                    id="MATURITY_DASHBOARD_GATE_PASS",
                    message="Maturity dashboard quality gate passed without enabling sensitive capabilities.",
                    severity=Severity.INFO,
                    metadata={"checks_total": len(checks), "summary": dict(summary)},
                )
            )
        return self._result(ok, checks, findings, dashboard_result)

    def _summary_thresholds_valid(self, summary: Mapping[str, Any]) -> bool:
        return (
            int(summary.get("capabilities_total", 0)) >= 28
            and int(summary.get("production_ready_local_total", 0)) >= 1
            and int(summary.get("blocked_total", 0)) >= 3
            and int(summary.get("critical_risks_total", 0)) >= 1
            and int(summary.get("blocking_gaps_total", 0)) >= 3
        )

    def _no_go_capabilities_blocked(self, capabilities: list[Any]) -> bool:
        by_id = {
            str(item.get("capability_id")): item
            for item in capabilities
            if isinstance(item, Mapping) and item.get("capability_id")
        }
        for capability_id, roadmap in self.REQUIRED_NO_GO_CAPABILITIES.items():
            item = by_id.get(capability_id)
            if not isinstance(item, Mapping):
                return False
            if item.get("status") != "blocked" or item.get("no_go_gate") is not True:
                return False
            if item.get("roadmap_dependency") != roadmap:
                return False
        return True

    def _source_evidence_present(self, capabilities: list[Any]) -> bool:
        for item in capabilities:
            if not isinstance(item, Mapping):
                return False
            evidence = item.get("source_evidence")
            if not isinstance(evidence, list) or not evidence or not all(str(value).strip() for value in evidence):
                return False
        return bool(capabilities)

    def _roadmap_alignment_present(self, roadmap_alignment: list[Any]) -> bool:
        milestones = {
            str(item.get("milestone"))
            for item in roadmap_alignment
            if isinstance(item, Mapping) and item.get("milestone")
        }
        return self.REQUIRED_ROADMAP_MILESTONES.issubset(milestones)

    def _reports_valid(self, data: Mapping[str, Any], findings: list[Finding]) -> bool:
        reports = data.get("reports") if isinstance(data.get("reports"), Mapping) else {}
        expected = {
            "json": "outputs/reports/maturity_dashboard.json",
            "markdown": "outputs/reports/maturity_dashboard.md",
        }
        if dict(reports) != expected:
            findings.append(
                Finding(
                    id="MATURITY_DASHBOARD_GATE_REPORT_PATH_BLOCK",
                    message="Maturity dashboard reports must use the canonical outputs/reports paths.",
                    severity=Severity.BLOCK,
                    metadata={"reports": dict(reports), "expected": expected},
                )
            )
            return False
        json_path = self.root / expected["json"]
        markdown_path = self.root / expected["markdown"]
        if not json_path.is_file() or not markdown_path.is_file():
            findings.append(
                Finding(
                    id="MATURITY_DASHBOARD_GATE_REPORT_MISSING",
                    message="Maturity dashboard report files are missing after --write-report.",
                    severity=Severity.BLOCK,
                    metadata={"json_exists": json_path.is_file(), "markdown_exists": markdown_path.is_file()},
                )
            )
            return False
        file_validation = SchemaValidator(self.root).validate(schema="MaturityDashboard", instance=expected["json"])
        findings.extend(file_validation.findings)
        if not file_validation.ok:
            findings.append(
                Finding(
                    id="MATURITY_DASHBOARD_GATE_REPORT_SCHEMA_BLOCK",
                    message="Persisted maturity dashboard JSON report does not conform to schema.",
                    severity=Severity.BLOCK,
                    path=expected["json"],
                )
            )
            return False
        return "# DevPilot Local — Maturity Dashboard" in markdown_path.read_text(encoding="utf-8")

    def _result(
        self,
        ok: bool,
        checks: Mapping[str, bool],
        findings: list[Finding],
        dashboard_result: CommandResult,
    ) -> CommandResult:
        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        data = dict(dashboard_result.data or {})
        summary = data.get("summary") if isinstance(data.get("summary"), Mapping) else {}
        return CommandResult(
            command="maturity dashboard gate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else self._exit_code(findings),
            message=(
                "Maturity dashboard quality gate passed."
                if ok
                else "Maturity dashboard quality gate failed or blocked."
            ),
            data={
                "summary": {
                    "checks_total": len(checks),
                    "checks_passed": sum(1 for value in checks.values() if value),
                    "blocking_findings_total": len(blocking),
                    "dashboard_summary": dict(summary),
                    "reports_written": bool(data.get("reports_written", False)),
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "source_mutations_performed": False,
                    "preliminary": True,
                },
                "checks": dict(checks),
                "reports": data.get("reports"),
                "no_go_capabilities": dict(self.REQUIRED_NO_GO_CAPABILITIES),
            },
            findings=findings,
        )

    def _exit_code(self, findings: list[Finding]) -> ExitCode:
        severities = {finding.severity for finding in findings}
        if Severity.ERROR in severities:
            return ExitCode.ERROR
        if Severity.BLOCK in severities:
            return ExitCode.BLOCK
        if Severity.FAIL in severities:
            return ExitCode.FAIL
        return ExitCode.PASS
