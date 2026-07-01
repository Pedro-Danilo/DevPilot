from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.auditpack import AuditPackV2BuildOptions, AuditPackV2Builder
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

from .evidence import ComplianceEvidenceCollector, ComplianceEvidenceCollectorOptions
from .mapping import ComplianceMappingValidator, ComplianceMappingValidatorOptions
from .report import ComplianceMappingReporter, ComplianceMappingReportOptions

_BLOCKING_SEVERITIES = {Severity.FAIL, Severity.BLOCK, Severity.ERROR}


@dataclass(frozen=True)
class ComplianceMappingQualityGateOptions:
    """Paths used by the POST-H-020-D compliance mapping quality gate."""

    control_mappings_path: str = ".devpilot/compliance/control_mappings.json"
    evidence_mappings_path: str = ".devpilot/compliance/evidence_mappings.json"
    compliance_pack_integrity_fixture_path: str = "evals/fixtures/compliance_pack_integrity_eval_cases.json"


class ComplianceMappingQualityGate:
    """Validate compliance mapping safety as a hardening quality subgate.

    POST-H-020-D composes the semantic validator, metadata-only collector,
    local report generator, audit-pack dry-run manifest and compliance-pack
    eval fixture signal. It does not execute declared evidence commands, does
    not write reports, does not build audit-pack ZIPs, does not use network or
    external APIs, and does not claim certification or legal advice.
    """

    def __init__(self, root: Path, *, options: ComplianceMappingQualityGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ComplianceMappingQualityGateOptions()

    def run(self) -> CommandResult:
        validator_result = ComplianceMappingValidator(
            self.root,
            ComplianceMappingValidatorOptions(
                control_mappings_path=self.options.control_mappings_path,
                evidence_mappings_path=self.options.evidence_mappings_path,
            ),
        ).validate()
        collector_result = ComplianceEvidenceCollector(
            self.root,
            ComplianceEvidenceCollectorOptions(
                control_mappings_path=self.options.control_mappings_path,
                evidence_mappings_path=self.options.evidence_mappings_path,
            ),
        ).collect()
        reporter_result = ComplianceMappingReporter(
            self.root,
            ComplianceMappingReportOptions(
                control_mappings_path=self.options.control_mappings_path,
                evidence_mappings_path=self.options.evidence_mappings_path,
            ),
        ).build(write_report=False)
        audit_result = AuditPackV2Builder(self.root).build(AuditPackV2BuildOptions(dry_run=True, execute=False))
        eval_signal, eval_findings = self._compliance_pack_integrity_eval_signal()

        findings: list[Finding] = []
        for source, result in (
            ("validator", validator_result),
            ("collector", collector_result),
            ("reporter", reporter_result),
            ("audit-pack", audit_result),
        ):
            if not result.ok:
                findings.extend(_prefixed_findings(source, result.findings))
                findings.append(
                    Finding(
                        "COMPLIANCE_MAPPING_GATE_RESULT_BLOCK",
                        "Compliance mapping quality gate dependency did not pass.",
                        Severity.BLOCK,
                        metadata={"source": source, "command": result.command},
                    )
                )
        findings.extend(eval_findings)

        validator_summary = _summary(validator_result)
        collector_summary = _summary(collector_result)
        reporter_summary = _summary(reporter_result)
        audit_summary = _summary(audit_result)
        audit_manifest = audit_result.data.get("manifest", {}) if isinstance(audit_result.data, dict) else {}
        audit_compliance = audit_manifest.get("compliance_mapping", {}) if isinstance(audit_manifest, dict) else {}

        summary = {
            "created_by": "POST-H-020-D",
            "status": "implemented-initial",
            "preliminary": True,
            "quality_gate_subgate": "compliance-mapping-pack",
            "validator_ok": validator_result.ok,
            "collector_ok": collector_result.ok,
            "reporter_ok": reporter_result.ok,
            "audit_pack_dry_run_ok": audit_result.ok,
            "audit_pack_manifest_has_compliance_mapping": bool(audit_compliance),
            "audit_pack_compliance_certification_claimed": audit_compliance.get("certification_claimed"),
            "audit_pack_legal_advice_claimed": audit_compliance.get("legal_advice_claimed"),
            "eval_signal_present": eval_signal["ok"],
            "eval_suite_id": eval_signal.get("suite_id"),
            "eval_cases_total": eval_signal.get("cases_total"),
            "pack_id": validator_summary.get("pack_id") or collector_summary.get("pack_id") or reporter_summary.get("pack_id"),
            "controls_total": int(reporter_summary.get("controls_total", collector_summary.get("controls_total", 0)) or 0),
            "controls_mapped": int(reporter_summary.get("controls_mapped", collector_summary.get("controls_mapped", 0)) or 0),
            "controls_with_evidence": int(reporter_summary.get("controls_with_evidence", collector_summary.get("controls_with_evidence", 0)) or 0),
            "controls_missing_evidence": int(reporter_summary.get("controls_missing_evidence", collector_summary.get("controls_missing_evidence", 0)) or 0),
            "critical_controls_missing_evidence": int(collector_summary.get("critical_controls_missing_evidence", validator_summary.get("critical_controls_missing_evidence", 0)) or 0),
            "evidence_total": int(collector_summary.get("evidence_total", 0) or 0),
            "evidence_available_total": int(collector_summary.get("evidence_available_total", 0) or 0),
            "missing_source_paths_total": int(collector_summary.get("missing_source_paths_total", 0) or 0),
            "certification_claimed": bool(reporter_summary.get("certification_claimed") or validator_summary.get("certification_claimed")),
            "legal_advice_claimed": bool(reporter_summary.get("legal_advice_claimed") or validator_summary.get("legal_advice_claimed")),
            "disclaimer_present": reporter_summary.get("disclaimer_present") is True or validator_summary.get("disclaimer_present") is True,
            "schema_valid": reporter_summary.get("schema_valid") is True,
            "audit_pack_mutations_performed": bool(audit_summary.get("mutations_performed", False)),
            "source_command_values_executed": bool(collector_summary.get("commands_executed", False)),
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_used": False,
            "connector_write_used": False,
            "plugin_execution_used": False,
        }

        findings.extend(self._invariant_findings(summary))
        blocking = _blocking(findings)
        summary["blocking_findings_total"] = len(blocking)
        ok = not blocking
        return CommandResult(
            command="quality compliance-mapping-pack",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Compliance mapping quality gate passed." if ok else "Compliance mapping quality gate blocked.",
            data={
                "summary": summary,
                "validator": validator_result.data,
                "collector": collector_result.data,
                "reporter": reporter_result.data,
                "audit_pack_summary": audit_summary,
                "audit_pack_compliance_mapping": audit_compliance,
                "compliance_pack_integrity_eval_signal": eval_signal,
                "notes": [
                    "POST-H-020-D integrates compliance mapping with quality-gate and audit-pack dry-run evidence.",
                    "This gate is not certification, legal advice or external audit evidence.",
                    "source_command declarations were not executed and no reports or audit-pack ZIPs were written by this subgate.",
                ],
            },
            findings=findings
            or [
                Finding(
                    "COMPLIANCE_MAPPING_QUALITY_GATE_PASS",
                    "Compliance mapping quality gate passed with no certification/legal claims and audit-pack summary signal present.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _compliance_pack_integrity_eval_signal(self) -> tuple[dict[str, Any], list[Finding]]:
        path = self._resolve(self.options.compliance_pack_integrity_fixture_path)
        summary: dict[str, Any] = {
            "ok": False,
            "fixture_path": self.options.compliance_pack_integrity_fixture_path,
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
            findings.append(Finding("COMPLIANCE_PACK_EVAL_FIXTURE_MISSING", "Compliance-pack integrity eval fixture is missing.", Severity.BLOCK, path=self.options.compliance_pack_integrity_fixture_path))
            return summary, findings
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("COMPLIANCE_PACK_EVAL_FIXTURE_INVALID_JSON", "Compliance-pack integrity eval fixture is not valid JSON.", Severity.ERROR, path=self.options.compliance_pack_integrity_fixture_path, metadata={"error": str(exc)}))
            return summary, findings

        cases = payload.get("cases") if isinstance(payload, dict) else None
        case_ids = {str(item.get("id")) for item in cases if isinstance(item, dict)} if isinstance(cases, list) else set()
        required_case_ids = {
            "compliance-clean-baseline-pass",
            "compliance-missing-registry-schema-block",
            "compliance-undeclared-action-block",
            "compliance-policy-engine-bypass-block",
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
        if summary["suite_id"] != "compliance-pack-integrity":
            findings.append(Finding("COMPLIANCE_PACK_EVAL_SUITE_UNEXPECTED", "Compliance-pack eval fixture suite_id is not compliance-pack-integrity.", Severity.FAIL, path=self.options.compliance_pack_integrity_fixture_path, metadata={"suite_id": summary["suite_id"]}))
        if not isinstance(cases, list) or len(cases) < 4:
            findings.append(Finding("COMPLIANCE_PACK_EVAL_CASES_INSUFFICIENT", "Compliance-pack eval fixture must include at least four safety cases.", Severity.BLOCK, path=self.options.compliance_pack_integrity_fixture_path, metadata={"cases_total": summary["cases_total"]}))
        missing = sorted(required_case_ids - case_ids)
        if missing:
            findings.append(Finding("COMPLIANCE_PACK_EVAL_CASES_MISSING", "Compliance-pack eval fixture is missing required safety cases.", Severity.BLOCK, path=self.options.compliance_pack_integrity_fixture_path, metadata={"missing_case_ids": missing}))
        for flag in ("network_used", "external_api_used", "llm_judge_used"):
            if summary[flag] is True:
                findings.append(Finding("COMPLIANCE_PACK_EVAL_UNSAFE_FLAG", "Compliance-pack eval signal must remain local, deterministic and non-LLM-judged.", Severity.BLOCK, path=self.options.compliance_pack_integrity_fixture_path, metadata={"flag": flag}))
        summary["ok"] = not _blocking(findings)
        return summary, findings

    def _invariant_findings(self, summary: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        if summary["certification_claimed"] is True or summary["audit_pack_compliance_certification_claimed"] is True:
            findings.append(Finding("COMPLIANCE_MAPPING_CERTIFICATION_CLAIM_BLOCKED", "Compliance mapping quality gate blocks certification claims.", Severity.BLOCK))
        if summary["legal_advice_claimed"] is True or summary["audit_pack_legal_advice_claimed"] is True:
            findings.append(Finding("COMPLIANCE_MAPPING_LEGAL_ADVICE_CLAIM_BLOCKED", "Compliance mapping quality gate blocks legal advice claims.", Severity.BLOCK))
        if summary["disclaimer_present"] is not True:
            findings.append(Finding("COMPLIANCE_MAPPING_DISCLAIMER_MISSING", "Compliance mapping quality gate requires no-certification/no-legal-advice disclaimers.", Severity.BLOCK))
        if summary["schema_valid"] is not True:
            findings.append(Finding("COMPLIANCE_MAPPING_REPORT_SCHEMA_BLOCKED", "Compliance mapping report must be schema-valid.", Severity.BLOCK))
        if summary["audit_pack_manifest_has_compliance_mapping"] is not True:
            findings.append(Finding("COMPLIANCE_MAPPING_AUDIT_PACK_SUMMARY_MISSING", "Audit pack dry-run manifest must include a compliance mapping summary.", Severity.BLOCK))
        if summary["eval_signal_present"] is not True:
            findings.append(Finding("COMPLIANCE_MAPPING_EVAL_SIGNAL_MISSING", "Compliance-pack integrity eval signal is required.", Severity.BLOCK, metadata={"suite_id": summary.get("eval_suite_id")}))
        if summary["controls_total"] <= 0 or summary["controls_missing_evidence"] > 0 or summary["critical_controls_missing_evidence"] > 0:
            findings.append(Finding("COMPLIANCE_MAPPING_COVERAGE_BLOCKED", "Compliance mapping must cover controls without critical/missing evidence gaps.", Severity.BLOCK, metadata={"controls_total": summary["controls_total"], "controls_missing_evidence": summary["controls_missing_evidence"], "critical_controls_missing_evidence": summary["critical_controls_missing_evidence"]}))
        if summary["evidence_total"] <= 0 or summary["evidence_available_total"] != summary["evidence_total"] or summary["missing_source_paths_total"] > 0:
            findings.append(Finding("COMPLIANCE_MAPPING_EVIDENCE_AVAILABILITY_BLOCKED", "Compliance mapping evidence must be locally available or explicitly reported as a gap.", Severity.BLOCK, metadata={"evidence_total": summary["evidence_total"], "evidence_available_total": summary["evidence_available_total"], "missing_source_paths_total": summary["missing_source_paths_total"]}))
        for flag in (
            "source_command_values_executed",
            "network_used",
            "external_api_used",
            "mutations_performed",
            "source_mutations_performed",
            "remote_execution_used",
            "connector_write_used",
            "plugin_execution_used",
        ):
            if summary.get(flag) is True:
                findings.append(Finding("COMPLIANCE_MAPPING_UNSAFE_FLAG_BLOCKED", "Compliance mapping quality gate blocks unsafe safety flags.", Severity.BLOCK, metadata={"flag": flag}))
        return findings

    def _resolve(self, value: str | Path) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.root / path


def _summary(result: CommandResult) -> dict[str, Any]:
    if isinstance(result.data, dict) and isinstance(result.data.get("summary"), dict):
        return dict(result.data["summary"])
    return {}


def _prefixed_findings(prefix: str, findings: list[Finding]) -> list[Finding]:
    return [
        Finding(
            f"COMPLIANCE_MAPPING_GATE_{prefix.upper().replace('-', '_')}_{finding.id}",
            finding.message,
            finding.severity,
            path=finding.path,
            metadata={"source": prefix, **(finding.metadata or {})},
        )
        for finding in findings
    ]


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
