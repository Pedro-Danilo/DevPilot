from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from devpilot_core.miasi.semantic_rules import (
    SemanticRuleStatus,
    SemanticSeverity,
    highest_semantic_severity,
    normalize_semantic_severity,
    severity_to_rule_status,
)

MIASI_SEMANTIC_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-MIASI-SEMANTIC-REPORT-V1"
MIASI_SEMANTIC_REPORT_CONTRACT = "MiasiSemanticReport"
MIASI_SEMANTIC_REPORT_VERSION = "1.0"


def _now_utc_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class SemanticFinding:
    """Machine-readable Policy/MIASI semantic finding.

    The shape is intentionally close to ``devpilot_core.cli_models.Finding`` but
    adds semantic context: rule id, category and subject coordinates. This lets
    POST-H-004-B/C/D classify agent/tool/policy violations without changing the
    public report schema.
    """

    finding_id: str
    rule_id: str
    severity: SemanticSeverity | str
    message: str
    category: str
    subject_type: str
    subject_id: str
    path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "severity": normalize_semantic_severity(self.severity).value,
            "message": self.message,
            "category": self.category,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
        }
        if self.path:
            data["path"] = self.path
        if self.metadata:
            data["metadata"] = self.metadata
        return data


@dataclass(frozen=True)
class SemanticRuleResult:
    """Result emitted by one semantic rule after evaluating zero or more subjects."""

    rule_id: str
    title: str
    status: SemanticRuleStatus | str
    severity: SemanticSeverity | str
    subjects_evaluated: int = 0
    findings: tuple[SemanticFinding, ...] = ()
    summary: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_findings(
        cls,
        *,
        rule_id: str,
        title: str,
        findings: list[SemanticFinding],
        subjects_evaluated: int = 0,
        summary: dict[str, Any] | None = None,
    ) -> "SemanticRuleResult":
        severity = highest_semantic_severity([finding.severity for finding in findings])
        status = severity_to_rule_status(severity)
        return cls(
            rule_id=rule_id,
            title=title,
            status=status,
            severity=severity,
            subjects_evaluated=subjects_evaluated,
            findings=tuple(findings),
            summary=summary or {},
        )

    def to_dict(self) -> dict[str, Any]:
        severity = normalize_semantic_severity(self.severity)
        status = self.status.value if isinstance(self.status, SemanticRuleStatus) else str(self.status)
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "status": status,
            "severity": severity.value,
            "subjects_evaluated": self.subjects_evaluated,
            "findings": [finding.to_dict() for finding in self.findings],
            "summary": self.summary,
        }


@dataclass(frozen=True)
class MiasiSemanticReport:
    """Top-level semantic report contract for POST-H-004.

    POST-H-004-A defines the stable report payload only. The actual semantic
    validator and rule execution are introduced in the next micro-sprints.
    """

    report_id: str
    created_by: str
    status: str
    rule_results: tuple[SemanticRuleResult, ...] = ()
    source_paths: dict[str, str] = field(default_factory=dict)
    generated_at_utc: str = field(default_factory=_now_utc_iso)
    schema_version: str = MIASI_SEMANTIC_REPORT_VERSION
    schema_id: str = MIASI_SEMANTIC_REPORT_SCHEMA_ID
    preliminary: bool = True
    dry_run: bool = True
    network_used: bool = False
    external_api_used: bool = False
    mutations_performed: bool = False
    source_mutations_performed: bool = False
    no_go_gates: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def findings(self) -> tuple[SemanticFinding, ...]:
        return tuple(finding for rule in self.rule_results for finding in rule.findings)

    def summary(self) -> dict[str, Any]:
        findings = self.findings
        return {
            "rules_total": len(self.rule_results),
            "rules_passed": sum(1 for rule in self.rule_results if _status_value(rule.status) == SemanticRuleStatus.PASS.value),
            "rules_warning": sum(1 for rule in self.rule_results if _status_value(rule.status) == SemanticRuleStatus.WARNING.value),
            "rules_error": sum(1 for rule in self.rule_results if _status_value(rule.status) == SemanticRuleStatus.ERROR.value),
            "rules_blocked": sum(1 for rule in self.rule_results if _status_value(rule.status) == SemanticRuleStatus.BLOCK.value),
            "findings_total": len(findings),
            "info_findings_total": sum(1 for finding in findings if normalize_semantic_severity(finding.severity) == SemanticSeverity.INFO),
            "warning_findings_total": sum(1 for finding in findings if normalize_semantic_severity(finding.severity) == SemanticSeverity.WARNING),
            "error_findings_total": sum(1 for finding in findings if normalize_semantic_severity(finding.severity) == SemanticSeverity.ERROR),
            "block_findings_total": sum(1 for finding in findings if normalize_semantic_severity(finding.severity) == SemanticSeverity.BLOCK),
            "blocking_findings_total": sum(1 for finding in findings if normalize_semantic_severity(finding.severity) in {SemanticSeverity.ERROR, SemanticSeverity.BLOCK}),
            "dry_run": self.dry_run,
            "network_used": self.network_used,
            "external_api_used": self.external_api_used,
            "mutations_performed": self.mutations_performed,
            "source_mutations_performed": self.source_mutations_performed,
            "preliminary": self.preliminary,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "schema_id": self.schema_id,
            "report_id": self.report_id,
            "created_by": self.created_by,
            "status": self.status,
            "generated_at_utc": self.generated_at_utc,
            "preliminary": self.preliminary,
            "dry_run": self.dry_run,
            "network_used": self.network_used,
            "external_api_used": self.external_api_used,
            "mutations_performed": self.mutations_performed,
            "source_mutations_performed": self.source_mutations_performed,
            "source_paths": self.source_paths,
            "summary": self.summary(),
            "rule_results": [rule.to_dict() for rule in self.rule_results],
            "findings": [finding.to_dict() for finding in self.findings],
            "no_go_gates": list(self.no_go_gates),
            "notes": list(self.notes),
        }


def _status_value(value: SemanticRuleStatus | str) -> str:
    return value.value if isinstance(value, SemanticRuleStatus) else str(value)
