from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

_DEFAULT_CONTROL_MAPPINGS = ".devpilot/compliance/control_mappings.json"
_DEFAULT_EVIDENCE_MAPPINGS = ".devpilot/compliance/evidence_mappings.json"
_REQUIRED_DOMAINS = frozenset({"security", "testing", "policy", "release", "observability", "agentic"})
_BLOCKING_SEVERITIES = {Severity.FAIL, Severity.BLOCK, Severity.ERROR}
_FORBIDDEN_SOURCE_TOKENS = {
    "curl ",
    "wget ",
    "http://",
    "https://",
    "pip install",
    "npm install",
    "subprocess",
    "powershell -c",
    "cmd /c",
    "git push",
    "deploy",
    "publish",
}


@dataclass(frozen=True)
class ComplianceMappingValidatorOptions:
    """Options for semantic validation of local compliance mappings."""

    control_mappings_path: str = _DEFAULT_CONTROL_MAPPINGS
    evidence_mappings_path: str = _DEFAULT_EVIDENCE_MAPPINGS
    required_domains: frozenset[str] = _REQUIRED_DOMAINS


class ComplianceMappingValidator:
    """Validate local compliance mappings without collecting evidence.

    POST-H-020-B validates registry semantics only. It does not execute
    source_command values, collect runtime evidence, generate reports, use the
    network, call external APIs or mutate files. Evidence collection and report
    generation remain POST-H-020-C scope.
    """

    def __init__(self, root: Path, options: ComplianceMappingValidatorOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ComplianceMappingValidatorOptions()

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        controls_payload = self._load_json(self.options.control_mappings_path, findings)
        evidence_payload = self._load_json(self.options.evidence_mappings_path, findings)
        if controls_payload is None or evidence_payload is None:
            return self._result(findings, {}, {})

        controls = controls_payload.get("controls", [])
        evidence_items = evidence_payload.get("evidence", [])
        if not isinstance(controls, list):
            findings.append(Finding("COMPLIANCE_CONTROLS_INVALID", "Control mappings must declare controls as a list.", Severity.BLOCK, path=self.options.control_mappings_path))
            controls = []
        if not isinstance(evidence_items, list):
            findings.append(Finding("COMPLIANCE_EVIDENCE_INVALID", "Evidence mappings must declare evidence as a list.", Severity.BLOCK, path=self.options.evidence_mappings_path))
            evidence_items = []

        self._validate_non_certifying_payload(controls_payload, self.options.control_mappings_path, findings)
        self._validate_non_certifying_payload(evidence_payload, self.options.evidence_mappings_path, findings)
        if controls_payload.get("pack_id") != evidence_payload.get("pack_id"):
            findings.append(Finding("COMPLIANCE_PACK_ID_MISMATCH", "Control and evidence mappings must use the same pack_id.", Severity.BLOCK, path=self.options.evidence_mappings_path, metadata={"control_pack_id": controls_payload.get("pack_id"), "evidence_pack_id": evidence_payload.get("pack_id")}))

        control_ids = [str(control.get("control_id", "")).strip() for control in controls if isinstance(control, dict)]
        evidence_ids = [str(evidence.get("evidence_id", "")).strip() for evidence in evidence_items if isinstance(evidence, dict)]
        self._validate_duplicates("COMPLIANCE_CONTROL_ID_DUPLICATE", "Duplicate compliance control_id detected.", control_ids, self.options.control_mappings_path, findings)
        self._validate_duplicates("COMPLIANCE_EVIDENCE_ID_DUPLICATE", "Duplicate compliance evidence_id detected.", evidence_ids, self.options.evidence_mappings_path, findings)

        known_control_ids = {control_id for control_id in control_ids if control_id}
        known_evidence_ids = {evidence_id for evidence_id in evidence_ids if evidence_id}
        evidence_by_control: dict[str, set[str]] = {control_id: set() for control_id in known_control_ids}
        for evidence in evidence_items:
            if not isinstance(evidence, dict):
                findings.append(Finding("COMPLIANCE_EVIDENCE_ENTRY_INVALID", "Evidence entry must be an object.", Severity.BLOCK, path=self.options.evidence_mappings_path))
                continue
            evidence_id = str(evidence.get("evidence_id", "")).strip()
            control_refs = evidence.get("control_ids", [])
            if not isinstance(control_refs, list) or not control_refs:
                findings.append(Finding("COMPLIANCE_EVIDENCE_CONTROL_IDS_MISSING", "Evidence entry must reference at least one control_id.", Severity.BLOCK, path=self.options.evidence_mappings_path, metadata={"evidence_id": evidence_id}))
                control_refs = []
            for control_id in control_refs:
                control_id = str(control_id).strip()
                if control_id not in known_control_ids:
                    findings.append(Finding("COMPLIANCE_EVIDENCE_UNKNOWN_CONTROL", "Evidence references an unknown control_id.", Severity.BLOCK, path=self.options.evidence_mappings_path, metadata={"evidence_id": evidence_id, "control_id": control_id}))
                else:
                    evidence_by_control.setdefault(control_id, set()).add(evidence_id)
            self._validate_evidence_source(evidence, findings)

        domain_counts: dict[str, int] = {}
        controls_with_evidence = 0
        controls_missing_evidence = 0
        critical_controls_missing_evidence = 0
        for control in controls:
            if not isinstance(control, dict):
                findings.append(Finding("COMPLIANCE_CONTROL_ENTRY_INVALID", "Control entry must be an object.", Severity.BLOCK, path=self.options.control_mappings_path))
                continue
            control_id = str(control.get("control_id", "")).strip()
            domain = str(control.get("domain", "")).strip()
            risk_level = str(control.get("risk_level", "")).strip()
            status = str(control.get("status", "")).strip()
            required_evidence = control.get("required_evidence", [])
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            if not isinstance(required_evidence, list) or not required_evidence:
                findings.append(Finding("COMPLIANCE_CONTROL_REQUIRED_EVIDENCE_MISSING", "Control must declare required_evidence or an explicit gap evidence mapping.", Severity.BLOCK, path=self.options.control_mappings_path, metadata={"control_id": control_id}))
                controls_missing_evidence += 1
                if risk_level == "critical":
                    critical_controls_missing_evidence += 1
                continue
            missing_required = sorted({str(item).strip() for item in required_evidence} - known_evidence_ids)
            if missing_required:
                severity = Severity.BLOCK if risk_level == "critical" else Severity.FAIL
                findings.append(Finding("COMPLIANCE_CONTROL_REQUIRED_EVIDENCE_UNMAPPED", "Control required_evidence has no evidence mapping.", severity, path=self.options.control_mappings_path, metadata={"control_id": control_id, "risk_level": risk_level, "missing_evidence": missing_required}))
                controls_missing_evidence += 1
                if risk_level == "critical":
                    critical_controls_missing_evidence += 1
            elif not evidence_by_control.get(control_id):
                findings.append(Finding("COMPLIANCE_CONTROL_WITHOUT_LINKED_EVIDENCE", "No evidence entry links back to this control_id.", Severity.BLOCK, path=self.options.evidence_mappings_path, metadata={"control_id": control_id}))
                controls_missing_evidence += 1
                if risk_level == "critical":
                    critical_controls_missing_evidence += 1
            else:
                controls_with_evidence += 1
            if status == "gap" and not str(control.get("gap_reason", "")).strip():
                findings.append(Finding("COMPLIANCE_GAP_REASON_MISSING", "Controls marked as gap must declare gap_reason.", Severity.BLOCK, path=self.options.control_mappings_path, metadata={"control_id": control_id}))

        missing_domains = sorted(self.options.required_domains - set(domain_counts))
        for domain in missing_domains:
            findings.append(Finding("COMPLIANCE_DOMAIN_COVERAGE_MISSING", "Compliance mapping lacks a required domain.", Severity.BLOCK, path=self.options.control_mappings_path, metadata={"domain": domain}))

        summary = {
            "control_mappings_path": self.options.control_mappings_path,
            "evidence_mappings_path": self.options.evidence_mappings_path,
            "pack_id": controls_payload.get("pack_id"),
            "controls_total": len(controls),
            "evidence_total": len(evidence_items),
            "controls_with_evidence": controls_with_evidence,
            "controls_missing_evidence": controls_missing_evidence,
            "critical_controls_missing_evidence": critical_controls_missing_evidence,
            "domain_coverage": dict(sorted(domain_counts.items())),
            "required_domains": sorted(self.options.required_domains),
            "missing_required_domains": missing_domains,
            "certification_claimed": bool(controls_payload.get("certification_claimed") or evidence_payload.get("certification_claimed")),
            "legal_advice_claimed": bool(controls_payload.get("legal_advice_claimed") or evidence_payload.get("legal_advice_claimed")),
            "disclaimer_present": _has_disclaimer(controls_payload) and _has_disclaimer(evidence_payload),
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "commands_executed": False,
            "preliminary": True,
        }
        return self._result(findings, summary, {"controls": controls_payload, "evidence": evidence_payload})

    def _result(self, findings: list[Finding], summary: dict[str, Any], mappings: dict[str, Any]) -> CommandResult:
        blocking = [finding for finding in findings if finding.severity in _BLOCKING_SEVERITIES]
        summary = dict(summary)
        summary.setdefault("network_used", False)
        summary.setdefault("external_api_used", False)
        summary.setdefault("mutations_performed", False)
        summary.setdefault("source_mutations_performed", False)
        summary.setdefault("commands_executed", False)
        summary["blocking_findings_total"] = len(blocking)
        ok = not blocking
        if ok and not findings:
            findings = [Finding("COMPLIANCE_MAPPING_VALIDATOR_PASS", "Compliance mapping semantic validation passed.", Severity.INFO, metadata={"controls_total": summary.get("controls_total", 0), "evidence_total": summary.get("evidence_total", 0)})]
        return CommandResult(
            command="compliance mapping validate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Compliance mapping semantic validation passed." if ok else "Compliance mapping semantic validation failed or blocked.",
            data={
                "summary": summary,
                "mappings": mappings,
                "notes": [
                    "POST-H-020-B validates mapping semantics only; evidence collection and report generation are POST-H-020-C scope.",
                    "The validator is local-first and does not execute source_command values.",
                ],
            },
            findings=findings,
        )

    def _load_json(self, path_value: str, findings: list[Finding]) -> dict[str, Any] | None:
        configured_path = Path(path_value)
        full_path = configured_path if configured_path.is_absolute() else self.root / configured_path
        if not configured_path.is_absolute():
            try:
                full_path.resolve().relative_to(self.root)
            except ValueError:
                findings.append(Finding("COMPLIANCE_MAPPING_PATH_BLOCKED", "Relative compliance mapping paths must stay inside the workspace root.", Severity.BLOCK, path=path_value))
                return None
        if not full_path.exists():
            findings.append(Finding("COMPLIANCE_MAPPING_FILE_MISSING", "Compliance mapping file does not exist.", Severity.BLOCK, path=path_value))
            return None
        try:
            payload = json.loads(full_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("COMPLIANCE_MAPPING_JSON_INVALID", "Compliance mapping file is not valid JSON.", Severity.ERROR, path=path_value, metadata={"error": str(exc)}))
            return None
        if not isinstance(payload, dict):
            findings.append(Finding("COMPLIANCE_MAPPING_JSON_INVALID", "Compliance mapping file must be a JSON object.", Severity.ERROR, path=path_value))
            return None
        return payload

    def _validate_non_certifying_payload(self, payload: dict[str, Any], path: str, findings: list[Finding]) -> None:
        if payload.get("certification_claimed") is not False:
            findings.append(Finding("COMPLIANCE_CERTIFICATION_CLAIM_BLOCKED", "Compliance mappings must not claim certification.", Severity.BLOCK, path=path))
        if payload.get("legal_advice_claimed") is not False:
            findings.append(Finding("COMPLIANCE_LEGAL_ADVICE_CLAIM_BLOCKED", "Compliance mappings must not claim legal advice.", Severity.BLOCK, path=path))
        if not _has_disclaimer(payload):
            findings.append(Finding("COMPLIANCE_DISCLAIMER_MISSING", "Compliance mappings must include a no-certification/no-legal-advice disclaimer.", Severity.BLOCK, path=path))
        safety = payload.get("safety", {})
        if isinstance(safety, dict) and (
            safety.get("network_used") is not False
            or safety.get("external_api_used") is not False
            or safety.get("mutations_performed") is not False
        ):
            findings.append(Finding("COMPLIANCE_SAFETY_FLAGS_BLOCKED", "Compliance mappings must remain local, no-network and non-mutating.", Severity.BLOCK, path=path, metadata={"safety": safety}))

    def _validate_duplicates(self, finding_id: str, message: str, values: list[str], path: str, findings: list[Finding]) -> None:
        duplicates = sorted({value for value in values if value and values.count(value) > 1})
        for value in duplicates:
            findings.append(Finding(finding_id, message, Severity.BLOCK, path=path, metadata={"id": value}))

    def _validate_evidence_source(self, evidence: dict[str, Any], findings: list[Finding]) -> None:
        evidence_id = str(evidence.get("evidence_id", "")).strip()
        if not (evidence.get("source_command") or evidence.get("source_paths") or evidence.get("justification")):
            findings.append(Finding("COMPLIANCE_EVIDENCE_SOURCE_MISSING", "Evidence must declare source_command, source_paths or justification.", Severity.BLOCK, path=self.options.evidence_mappings_path, metadata={"evidence_id": evidence_id}))
        command = str(evidence.get("source_command", "")).lower()
        forbidden = sorted(token for token in _FORBIDDEN_SOURCE_TOKENS if token in command)
        if forbidden:
            findings.append(Finding("COMPLIANCE_EVIDENCE_FORBIDDEN_SOURCE_COMMAND", "Evidence source_command contains forbidden external or mutating tokens.", Severity.BLOCK, path=self.options.evidence_mappings_path, metadata={"evidence_id": evidence_id, "forbidden_tokens": forbidden}))
        for source_path in evidence.get("source_paths", []) or []:
            relative_path = Path(str(source_path))
            full_path = relative_path if relative_path.is_absolute() else self.root / relative_path
            try:
                full_path.resolve().relative_to(self.root)
            except ValueError:
                findings.append(Finding("COMPLIANCE_EVIDENCE_SOURCE_PATH_BLOCKED", "Evidence source_path must stay inside the workspace root.", Severity.BLOCK, path=self.options.evidence_mappings_path, metadata={"evidence_id": evidence_id, "source_path": str(source_path)}))
                continue
            if not full_path.exists():
                findings.append(Finding("COMPLIANCE_EVIDENCE_SOURCE_PATH_MISSING", "Evidence source_path does not exist.", Severity.FAIL, path=self.options.evidence_mappings_path, metadata={"evidence_id": evidence_id, "source_path": str(source_path)}))


def _has_disclaimer(payload: dict[str, Any]) -> bool:
    disclaimer = str(payload.get("disclaimer", "")).lower()
    no_certification = (
        "not certification" in disclaimer
        or "not a certification" in disclaimer
        or "no certificación" in disclaimer
    )
    return bool(disclaimer) and no_certification and "legal" in disclaimer


def _exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS
