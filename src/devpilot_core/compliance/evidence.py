from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.compliance.mapping import ComplianceMappingValidator, ComplianceMappingValidatorOptions

_BLOCKING_SEVERITIES = {Severity.FAIL, Severity.BLOCK, Severity.ERROR}


@dataclass(frozen=True)
class ComplianceEvidenceCollectorOptions:
    """Options for POST-H-020-C local compliance evidence collection."""

    control_mappings_path: str = ".devpilot/compliance/control_mappings.json"
    evidence_mappings_path: str = ".devpilot/compliance/evidence_mappings.json"


class ComplianceEvidenceCollector:
    """Collect local metadata about declared compliance evidence.

    POST-H-020-C intentionally treats evidence commands as declarations. It
    validates mappings and inspects only filesystem metadata for declared
    source_paths; it does not execute commands, read evidence file contents,
    send data outside the workspace, call network APIs or mutate source files.
    """

    def __init__(self, root: Path, options: ComplianceEvidenceCollectorOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ComplianceEvidenceCollectorOptions()

    def collect(self) -> CommandResult:
        validator_options = ComplianceMappingValidatorOptions(
            control_mappings_path=self.options.control_mappings_path,
            evidence_mappings_path=self.options.evidence_mappings_path,
        )
        validation = ComplianceMappingValidator(self.root, validator_options).validate()
        findings: list[Finding] = list(validation.findings)
        mappings = validation.data.get("mappings", {}) if isinstance(validation.data, dict) else {}
        controls_payload = mappings.get("controls", {}) if isinstance(mappings, dict) else {}
        evidence_payload = mappings.get("evidence", {}) if isinstance(mappings, dict) else {}
        controls = controls_payload.get("controls", []) if isinstance(controls_payload, dict) else []
        evidence_items = evidence_payload.get("evidence", []) if isinstance(evidence_payload, dict) else []

        collected_evidence: list[dict[str, Any]] = []
        available_total = 0
        missing_source_paths_total = 0
        blocked_source_paths_total = 0
        command_declarations_total = 0
        for item in evidence_items if isinstance(evidence_items, list) else []:
            if not isinstance(item, dict):
                continue
            collected = self._collect_item(item, findings)
            collected_evidence.append(collected)
            if collected["available"]:
                available_total += 1
            missing_source_paths_total += int(collected["missing_source_paths_total"])
            blocked_source_paths_total += int(collected["blocked_source_paths_total"])
            if collected["source_command_declared"]:
                command_declarations_total += 1

        validation_summary = validation.data.get("summary", {}) if isinstance(validation.data, dict) else {}
        blocking = [finding for finding in findings if finding.severity in _BLOCKING_SEVERITIES]
        summary = {
            "control_mappings_path": self.options.control_mappings_path,
            "evidence_mappings_path": self.options.evidence_mappings_path,
            "pack_id": validation_summary.get("pack_id") or controls_payload.get("pack_id"),
            "controls_total": len(controls) if isinstance(controls, list) else 0,
            "controls_mapped": sum(1 for control in controls if isinstance(control, dict) and control.get("status") == "mapped") if isinstance(controls, list) else 0,
            "controls_with_evidence": int(validation_summary.get("controls_with_evidence", 0) or 0),
            "controls_missing_evidence": int(validation_summary.get("controls_missing_evidence", 0) or 0),
            "critical_controls_missing_evidence": int(validation_summary.get("critical_controls_missing_evidence", 0) or 0),
            "evidence_total": len(collected_evidence),
            "evidence_available_total": available_total,
            "evidence_missing_total": max(len(collected_evidence) - available_total, 0),
            "missing_source_paths_total": missing_source_paths_total,
            "blocked_source_paths_total": blocked_source_paths_total,
            "command_declarations_total": command_declarations_total,
            "commands_executed": False,
            "certification_claimed": bool(validation_summary.get("certification_claimed")),
            "legal_advice_claimed": bool(validation_summary.get("legal_advice_claimed")),
            "disclaimer_present": validation_summary.get("disclaimer_present") is True,
            "domain_coverage": validation_summary.get("domain_coverage", {}),
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
            "blocking_findings_total": len(blocking),
        }
        ok = validation.ok and not blocking
        return CommandResult(
            command="compliance evidence collect",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Compliance evidence collection passed." if ok else "Compliance evidence collection found blocking gaps.",
            data={
                "summary": summary,
                "evidence": collected_evidence,
                "validation_summary": validation_summary,
                "notes": [
                    "POST-H-020-C collection is local metadata-only evidence inspection.",
                    "source_command values are declarations and were not executed.",
                    "Reports are evidence mapping aids; they are not certification, legal advice or an external audit.",
                ],
            },
            findings=findings
            or [
                Finding(
                    "COMPLIANCE_EVIDENCE_COLLECTION_PASS",
                    "Compliance evidence collection confirmed local declared evidence availability.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _collect_item(self, item: dict[str, Any], findings: list[Finding]) -> dict[str, Any]:
        evidence_id = str(item.get("evidence_id", "")).strip()
        source_paths = item.get("source_paths", []) or []
        path_statuses: list[dict[str, Any]] = []
        missing = 0
        blocked = 0
        for raw_path in source_paths:
            status = self._path_status(evidence_id, str(raw_path), findings)
            path_statuses.append(status)
            if status["status"] == "missing":
                missing += 1
            if status["status"] == "blocked":
                blocked += 1
        available = bool(path_statuses) and missing == 0 and blocked == 0
        if not source_paths and item.get("justification"):
            available = True
        if not available:
            findings.append(
                Finding(
                    "COMPLIANCE_EVIDENCE_NOT_AVAILABLE",
                    "Declared compliance evidence has missing or blocked local source paths.",
                    Severity.FAIL,
                    path=self.options.evidence_mappings_path,
                    metadata={"evidence_id": evidence_id, "missing_source_paths_total": missing, "blocked_source_paths_total": blocked},
                )
            )
        return {
            "evidence_id": evidence_id,
            "control_ids": [str(control_id) for control_id in item.get("control_ids", []) or []],
            "evidence_type": str(item.get("evidence_type", "")),
            "retention_class": str(item.get("retention_class", "")),
            "source_command_declared": bool(item.get("source_command")),
            "source_command_executed": False,
            "source_paths_total": len(source_paths),
            "missing_source_paths_total": missing,
            "blocked_source_paths_total": blocked,
            "available": available,
            "required_fields_total": len(item.get("required_fields", []) or []),
            "expected_values_total": len(item.get("expected_values", {}) or {}),
            "source_paths": path_statuses,
        }

    def _path_status(self, evidence_id: str, raw_path: str, findings: list[Finding]) -> dict[str, Any]:
        relative = Path(raw_path)
        full_path = relative if relative.is_absolute() else self.root / relative
        try:
            resolved = full_path.resolve()
            resolved.relative_to(self.root)
        except ValueError:
            findings.append(
                Finding(
                    "COMPLIANCE_EVIDENCE_SOURCE_PATH_BLOCKED",
                    "Evidence source_path must stay inside the workspace root.",
                    Severity.BLOCK,
                    path=self.options.evidence_mappings_path,
                    metadata={"evidence_id": evidence_id, "source_path": raw_path},
                )
            )
            return {"path": raw_path, "status": "blocked", "exists": False, "kind": "outside-workspace"}
        if not resolved.exists():
            findings.append(
                Finding(
                    "COMPLIANCE_EVIDENCE_SOURCE_PATH_MISSING",
                    "Evidence source_path does not exist.",
                    Severity.FAIL,
                    path=self.options.evidence_mappings_path,
                    metadata={"evidence_id": evidence_id, "source_path": raw_path},
                )
            )
            return {"path": raw_path, "status": "missing", "exists": False, "kind": "missing"}
        kind = "directory" if resolved.is_dir() else "file" if resolved.is_file() else "other"
        status: dict[str, Any] = {"path": raw_path, "status": "available", "exists": True, "kind": kind}
        if resolved.is_file():
            status["size_bytes"] = resolved.stat().st_size
        return status


def _exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS
