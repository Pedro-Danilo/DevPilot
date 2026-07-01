from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.remote.readiness import RemoteReadinessOptions
from devpilot_core.remote.reports import RemoteReadinessReportOptions, RemoteReadinessReporter

_BLOCKING_SEVERITIES = {Severity.FAIL, Severity.BLOCK, Severity.ERROR}


@dataclass(frozen=True)
class RemoteReadinessQualityGateOptions(RemoteReadinessOptions):
    """Paths used by the POST-H-021-D remote-disabled quality gate."""

    remote_enterprise_fixture_path: str = "evals/fixtures/remote_enterprise_eval_cases.json"


class RemoteReadinessQualityGate:
    """Validate remote-runner disabled invariants as a hardening quality subgate.

    POST-H-021-D composes the existing read-only readiness checker, criteria
    schema validation and remote/enterprise eval fixture signal. It does not
    execute remote work, configure transport, read credentials, contact services
    or write reports.
    """

    def __init__(self, root: Path, *, options: RemoteReadinessQualityGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or RemoteReadinessQualityGateOptions()

    def run(self) -> CommandResult:
        readiness_result = RemoteReadinessReporter(
            self.root,
            options=RemoteReadinessReportOptions(
                criteria_path=self.options.criteria_path,
                criteria_schema_path=self.options.criteria_schema_path,
                registry_path=self.options.registry_path,
                registry_schema_path=self.options.registry_schema_path,
            ),
        ).build(write_report=False)
        eval_signal, eval_findings = self._remote_enterprise_eval_signal()

        findings: list[Finding] = []
        if not readiness_result.ok:
            findings.extend(readiness_result.findings)
        findings.extend(eval_findings)

        readiness_summary = _summary(readiness_result)
        report = readiness_result.data.get("report", {}) if isinstance(readiness_result.data, dict) else {}
        required_before_enablement = report.get("required_before_enablement", []) if isinstance(report, dict) else []
        safety = report.get("safety", {}) if isinstance(report, dict) else {}

        summary = {
            "created_by": "POST-H-021-D",
            "status": "implemented-initial",
            "preliminary": True,
            "quality_gate_subgate": "remote-readiness-design-only",
            "readiness_report_ok": readiness_result.ok,
            "readiness_level": readiness_summary.get("readiness_level"),
            "decision_status": readiness_summary.get("decision_status"),
            "schema_valid": readiness_summary.get("schema_valid") is True,
            "runner_registry_valid": readiness_summary.get("runner_registry_valid") is True,
            "requires_future_adr": readiness_summary.get("requires_future_adr") is True,
            "future_adr_required": report.get("future_adr_required") is True if isinstance(report, dict) else False,
            "required_before_enablement_total": len(required_before_enablement) if isinstance(required_before_enablement, list) else 0,
            "remote_enterprise_eval_signal_present": eval_signal["ok"],
            "remote_enterprise_suite_id": eval_signal.get("suite_id"),
            "remote_enterprise_cases_total": eval_signal.get("cases_total"),
            "remote_execution_allowed": bool(readiness_summary.get("remote_execution_allowed", False)),
            "remote_runner_enabled": bool(readiness_summary.get("remote_runner_enabled", False)),
            "execution_allowed": bool(readiness_summary.get("execution_allowed", False)),
            "remote_execution_used": bool(readiness_summary.get("remote_execution_used", False)),
            "network_used": bool(readiness_summary.get("network_used", False)) or bool(eval_signal.get("network_used", False)),
            "external_api_used": bool(readiness_summary.get("external_api_used", False)) or bool(eval_signal.get("external_api_used", False)),
            "credentials_required": bool(readiness_summary.get("credentials_required", False)),
            "secrets_read": bool(readiness_summary.get("secrets_read", False)),
            "mutations_performed": bool(readiness_summary.get("mutations_performed", False)),
            "source_mutations_performed": bool(readiness_summary.get("source_mutations_performed", False)),
            "connector_write_enabled": bool(safety.get("connector_write_enabled", False)) if isinstance(safety, dict) else False,
            "plugin_execution_enabled": bool(safety.get("plugin_execution_enabled", False)) if isinstance(safety, dict) else False,
            "reports_written": bool(readiness_summary.get("reports_written", False)),
        }

        findings.extend(self._invariant_findings(summary))
        blocking = _blocking(findings)
        summary["blocking_findings_total"] = len(blocking)
        ok = not blocking
        return CommandResult(
            command="quality remote-readiness-design-only",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Remote readiness design-only quality gate passed." if ok else "Remote readiness design-only quality gate blocked.",
            data={
                "summary": summary,
                "readiness": readiness_result.data,
                "remote_enterprise_eval_signal": eval_signal,
                "notes": [
                    "POST-H-021-D integrates remote disabled invariants into quality-gate hardening/industrial profiles.",
                    "The subgate is design-only evidence and does not authorize remote runner enablement.",
                    "Future remote execution remains blocked pending a future ADR and the POST-H-022/POST-H-023 design prerequisites.",
                ],
            },
            findings=findings
            or [
                Finding(
                    "REMOTE_READINESS_QUALITY_GATE_PASS",
                    "Remote readiness design-only quality gate confirms remote runner remains disabled.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _remote_enterprise_eval_signal(self) -> tuple[dict[str, Any], list[Finding]]:
        path = self._resolve(self.options.remote_enterprise_fixture_path)
        summary: dict[str, Any] = {
            "ok": False,
            "fixture_path": self.options.remote_enterprise_fixture_path,
            "fixture_exists": path.exists(),
            "suite_id": None,
            "cases_total": 0,
            "required_case_ids_present": [],
            "network_used": False,
            "external_api_used": False,
            "llm_judge_used": False,
        }
        findings: list[Finding] = []
        if not path.exists():
            findings.append(Finding("REMOTE_ENTERPRISE_EVAL_FIXTURE_MISSING", "Remote/enterprise eval fixture is missing.", Severity.BLOCK, path=self.options.remote_enterprise_fixture_path))
            return summary, findings
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("REMOTE_ENTERPRISE_EVAL_FIXTURE_INVALID_JSON", "Remote/enterprise eval fixture is not valid JSON.", Severity.ERROR, path=self.options.remote_enterprise_fixture_path, metadata={"error": str(exc)}))
            return summary, findings

        cases = payload.get("cases") if isinstance(payload, dict) else None
        case_ids = {str(item.get("id")) for item in cases if isinstance(item, dict)} if isinstance(cases, list) else set()
        required_case_ids = {
            "remote-enterprise-clean-disabled-pass",
            "remote-runner-execution-block",
            "remote-cloud-control-plane-block",
            "enterprise-report-mutation-or-policy-bypass-block",
        }
        summary.update(
            {
                "suite_id": payload.get("suite_id") if isinstance(payload, dict) else None,
                "cases_total": len(cases) if isinstance(cases, list) else 0,
                "required_case_ids_present": sorted(required_case_ids.intersection(case_ids)),
                "network_used": payload.get("network_used") is True if isinstance(payload, dict) else False,
                "external_api_used": payload.get("external_api_used") is True if isinstance(payload, dict) else False,
                "llm_judge_used": payload.get("llm_judge_used") is True if isinstance(payload, dict) else False,
            }
        )
        if summary["suite_id"] != "remote-enterprise":
            findings.append(Finding("REMOTE_ENTERPRISE_EVAL_SUITE_UNEXPECTED", "Remote/enterprise eval fixture suite_id is not remote-enterprise.", Severity.FAIL, path=self.options.remote_enterprise_fixture_path, metadata={"suite_id": summary["suite_id"]}))
        if not isinstance(cases, list) or len(cases) < 4:
            findings.append(Finding("REMOTE_ENTERPRISE_EVAL_CASES_INSUFFICIENT", "Remote/enterprise eval fixture must include at least four safety cases.", Severity.BLOCK, path=self.options.remote_enterprise_fixture_path, metadata={"cases_total": summary["cases_total"]}))
        missing = sorted(required_case_ids - case_ids)
        if missing:
            findings.append(Finding("REMOTE_ENTERPRISE_EVAL_CASES_MISSING", "Remote/enterprise eval fixture is missing required safety cases.", Severity.BLOCK, path=self.options.remote_enterprise_fixture_path, metadata={"missing_case_ids": missing}))
        for flag in ("network_used", "external_api_used", "llm_judge_used"):
            if summary[flag] is True:
                findings.append(Finding("REMOTE_ENTERPRISE_EVAL_UNSAFE_FLAG", "Remote/enterprise eval signal must remain local, deterministic and non-LLM-judged.", Severity.BLOCK, path=self.options.remote_enterprise_fixture_path, metadata={"flag": flag}))
        summary["ok"] = not _blocking(findings)
        return summary, findings

    def _invariant_findings(self, summary: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        if summary["quality_gate_subgate"] != "remote-readiness-design-only":
            findings.append(Finding("REMOTE_READINESS_SUBGATE_ID_DRIFT", "Remote quality gate subgate id drifted from the POST-H-021-D contract.", Severity.BLOCK))
        if summary["readiness_level"] != "remote-design-only" or summary["decision_status"] != "design-only":
            findings.append(Finding("REMOTE_READINESS_DESIGN_ONLY_BLOCKED", "Remote readiness quality gate requires design-only readiness.", Severity.BLOCK, metadata={"readiness_level": summary["readiness_level"], "decision_status": summary["decision_status"]}))
        if summary["schema_valid"] is not True or summary["runner_registry_valid"] is not True:
            findings.append(Finding("REMOTE_READINESS_SCHEMA_OR_REGISTRY_BLOCKED", "Remote readiness quality gate requires schema-valid criteria/report and disabled runner registry.", Severity.BLOCK))
        if summary["requires_future_adr"] is not True or summary["future_adr_required"] is not True:
            findings.append(Finding("REMOTE_READINESS_FUTURE_ADR_REQUIRED", "Remote runner enablement must remain blocked by future ADR requirement.", Severity.BLOCK))
        if summary["remote_enterprise_eval_signal_present"] is not True:
            findings.append(Finding("REMOTE_READINESS_EVAL_SIGNAL_MISSING", "Remote/enterprise eval safety signal is required.", Severity.BLOCK, metadata={"suite_id": summary.get("remote_enterprise_suite_id")}))
        for flag in (
            "remote_execution_allowed",
            "remote_runner_enabled",
            "execution_allowed",
            "remote_execution_used",
            "network_used",
            "external_api_used",
            "credentials_required",
            "secrets_read",
            "mutations_performed",
            "source_mutations_performed",
            "connector_write_enabled",
            "plugin_execution_enabled",
            "reports_written",
        ):
            if summary.get(flag) is True:
                findings.append(Finding("REMOTE_READINESS_UNSAFE_FLAG_BLOCKED", "Remote readiness quality gate blocks unsafe flags.", Severity.BLOCK, metadata={"flag": flag}))
        return findings

    def _resolve(self, value: str | Path) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.root / path


def _summary(result: CommandResult) -> dict[str, Any]:
    if isinstance(result.data, dict) and isinstance(result.data.get("summary"), dict):
        return dict(result.data["summary"])
    return {}


def _blocking(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity in _BLOCKING_SEVERITIES]


def _exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS
