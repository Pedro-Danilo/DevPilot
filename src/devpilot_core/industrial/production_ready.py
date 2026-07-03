from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator


DEFAULT_CRITERIA_PATH = Path(".devpilot/production/production_ready_local_criteria.json")
DEFAULT_REPORT_JSON_PATH = Path("outputs/reports/production_ready_local_report.json")
DEFAULT_REPORT_MARKDOWN_PATH = Path("outputs/reports/production_ready_local_report.md")
DEFAULT_CLAIMS_DOCUMENT_PATHS = (
    "README.md",
    "docs/05_operations/runbook.md",
    "docs/release/CHANGELOG.md",
)


@dataclass(frozen=True)
class ProductionReadyEvidenceAggregatorOptions:
    """Options for the POST-H-025-B read-only evidence aggregator."""

    criteria_path: str = str(DEFAULT_CRITERIA_PATH)
    report_id_suffix: str = "intermediate"


@dataclass(frozen=True)
class ProductionReadyDeclarationGateOptions:
    """Options for the POST-H-025-C production-ready-local declaration gate."""

    criteria_path: str = str(DEFAULT_CRITERIA_PATH)
    output_json: str = str(DEFAULT_REPORT_JSON_PATH)
    output_markdown: str = str(DEFAULT_REPORT_MARKDOWN_PATH)
    write_report: bool = False
    report_id_suffix: str = "post_h_025_c"


@dataclass(frozen=True)
class ProductionReadyClaimsValidatorOptions:
    """Options for the POST-H-025-D no-go and claims validator."""

    document_paths: tuple[str, ...] = DEFAULT_CLAIMS_DOCUMENT_PATHS
    report_path: str | None = None
    project_state_path: str | None = ".devpilot/project_state.json"
    include_gate_report: bool = True


class ProductionReadyEvidenceAggregator:
    """Aggregate production-ready-local evidence without declaring readiness.

    POST-H-025-B intentionally produces an intermediate, read-only model. It
    reads the criteria/evidence map, classifies available and missing evidence,
    and leaves report writing plus CLI/API declaration semantics to later
    POST-H-025 micro-sprints.
    """

    def __init__(self, root: Path, *, options: ProductionReadyEvidenceAggregatorOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ProductionReadyEvidenceAggregatorOptions()

    def aggregate(self) -> CommandResult:
        criteria_path = self._resolve_inside_root(self.options.criteria_path)
        criteria_result = self._load_json(criteria_path)
        if criteria_result["status"] != "pass":
            return CommandResult(
                "production-ready evidence aggregate",
                False,
                ExitCode.ERROR,
                "Production-ready-local criteria could not be loaded.",
                data={
                    "summary": self._base_summary(criteria_path=criteria_path),
                    "criteria_path": self._relative(criteria_path),
                    "safety": self._safety(),
                },
                findings=[
                    Finding(
                        "PRODUCTION_READY_CRITERIA_UNREADABLE",
                        "Criteria JSON is missing or invalid.",
                        Severity.ERROR,
                        path=self._relative(criteria_path),
                        metadata=criteria_result,
                    )
                ],
            )

        criteria = criteria_result["content"]
        evidence_results: list[dict[str, Any]] = []
        evidence_details: list[dict[str, Any]] = []
        gaps: list[dict[str, Any]] = []

        for hito in criteria.get("evidence_map", []):
            hito_details: list[dict[str, Any]] = []
            for evidence in hito.get("evidence", []):
                detail = self._evaluate_evidence(hito=hito, evidence=evidence)
                hito_details.append(detail)
                evidence_details.append(detail)
                if detail["status"] != "pass":
                    gaps.append(self._gap_for_evidence(detail))
            evidence_results.append(self._hito_result(hito, hito_details))

        required_hitos = [item for item in evidence_results if item["required_for_pass"]]
        passed_required = [item for item in required_hitos if item["status"] == "pass"]
        blocking_gaps = [gap for gap in gaps if gap["severity"] == "block"]
        warning_gaps = [gap for gap in gaps if gap["severity"] == "warning"]
        info_gaps = [gap for gap in gaps if gap["severity"] == "info"]
        score = self._score(criteria, evidence_results)
        no_go_gates = dict(criteria.get("no_go_gates", {}))
        no_go_gates_passed = all(value is False for value in no_go_gates.values())
        candidate_decision = (
            "PASS_CANDIDATE"
            if score >= float(criteria.get("minimum_score", 100))
            and not blocking_gaps
            and no_go_gates_passed
            else "BLOCK_CANDIDATE"
        )
        summary = {
            "scope": criteria.get("scope", "production-ready-local"),
            "criteria_path": self._relative(criteria_path),
            "criteria_status": criteria.get("status"),
            "candidate_decision": candidate_decision,
            "production_ready_local_declared": False,
            "minimum_score": criteria.get("minimum_score", 90),
            "score": score,
            "required_hitos_total": len(required_hitos),
            "passed_hitos_total": len(passed_required),
            "evidence_total": len(evidence_details),
            "evidence_passed_total": sum(1 for item in evidence_details if item["status"] == "pass"),
            "gaps_total": len(gaps),
            "blocking_gaps_total": len(blocking_gaps),
            "warning_gaps_total": len(warning_gaps),
            "info_gaps_total": len(info_gaps),
            "missing_evidence_total": sum(1 for item in evidence_details if item["status"] == "missing"),
            "failed_evidence_total": sum(1 for item in evidence_details if item["status"] == "failed"),
            "no_go_gates_passed": no_go_gates_passed,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
            "preliminary": True,
        }
        intermediate_model = {
            "schema_version": "1.0",
            "created_by": "POST-H-025-B",
            "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "scope": criteria.get("scope", "production-ready-local"),
            "candidate_decision": candidate_decision,
            "score": score,
            "minimum_score": criteria.get("minimum_score", 90),
            "claims": {
                "production_ready_local": False,
                "enterprise_ready": False,
                "remote_ready": False,
                "compliance_certified": False,
                "saas_ready": False,
            },
            "no_go_gates": no_go_gates,
            "evidence_results": evidence_results,
            "evidence_details": evidence_details,
            "gaps": gaps,
            "safety": self._safety(),
            "limitations": [
                "POST-H-025-B aggregates evidence only; CLI/API declaration and final PASS/BLOCK report remain pending.",
                "The aggregator does not execute validation commands from the evidence map; it checks local artifacts read-only.",
                "A PASS_CANDIDATE is not a production-ready-local declaration.",
            ],
        }
        findings = [
            Finding(
                "PRODUCTION_READY_EVIDENCE_AGGREGATED",
                "Production-ready-local evidence was aggregated read-only.",
                Severity.INFO,
                metadata={
                    "candidate_decision": candidate_decision,
                    "score": score,
                    "blocking_gaps_total": len(blocking_gaps),
                },
            )
        ]
        if gaps:
            findings.append(
                Finding(
                    "PRODUCTION_READY_EVIDENCE_GAPS_REPORTED",
                    "Evidence aggregator reported gaps without mutating files.",
                    Severity.WARNING,
                    metadata={
                        "gaps_total": len(gaps),
                        "blocking_gaps_total": len(blocking_gaps),
                        "warning_gaps_total": len(warning_gaps),
                    },
                )
            )
        return CommandResult(
            "production-ready evidence aggregate",
            True,
            ExitCode.PASS,
            "Production-ready-local evidence aggregated read-only.",
            data={
                "summary": summary,
                "criteria": {
                    "schema_id": criteria.get("schema_id"),
                    "criteria_id": criteria.get("criteria_id"),
                    "scope": criteria.get("scope"),
                    "required_hitos": criteria.get("required_hitos", []),
                    "optional_design_hitos": criteria.get("optional_design_hitos", []),
                },
                "evidence_results": evidence_results,
                "evidence_details": evidence_details,
                "gaps": gaps,
                "intermediate_model": intermediate_model,
                "safety": self._safety(),
            },
            findings=findings,
        )

    def _evaluate_evidence(self, *, hito: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve_inside_root(evidence.get("path", ""))
        status = "pass"
        reason = "present"
        metadata: dict[str, Any] = {}
        if not path.exists():
            status = "missing"
            reason = "path does not exist"
        elif path.is_dir():
            status = "failed"
            reason = "expected evidence file, found directory"
        elif path.suffix.lower() == ".json":
            parsed = self._load_json(path)
            status = parsed["status"]
            reason = parsed["reason"]
            metadata = parsed.get("metadata", {})
            if status == "pass":
                expected_schema_id = evidence.get("expected_schema_id")
                actual_schema_id = self._extract_schema_id(parsed["content"])
                if expected_schema_id and actual_schema_id and actual_schema_id != expected_schema_id:
                    status = "failed"
                    reason = "schema_id mismatch"
                    metadata = {"expected_schema_id": expected_schema_id, "actual_schema_id": actual_schema_id}

        return {
            "hito_id": hito.get("hito_id"),
            "classification": hito.get("classification"),
            "required_for_pass": bool(hito.get("required_for_pass")),
            "evidence_id": evidence.get("evidence_id"),
            "title": evidence.get("title"),
            "path": self._relative(path),
            "category": evidence.get("category"),
            "requirement_level": evidence.get("requirement_level"),
            "blocker_on_missing": bool(evidence.get("blocker_on_missing")),
            "expected_schema_id": evidence.get("expected_schema_id"),
            "validation_command": evidence.get("validation_command"),
            "status": status,
            "reason": reason,
            "metadata": metadata,
        }

    def _hito_result(self, hito: dict[str, Any], details: list[dict[str, Any]]) -> dict[str, Any]:
        statuses = [detail["status"] for detail in details]
        if not details or "failed" in statuses:
            status = "failed"
        elif "missing" in statuses:
            status = "missing" if all(item == "missing" for item in statuses) else "partial"
        elif all(item == "pass" for item in statuses):
            status = "pass"
        else:
            status = "partial"
        return {
            "hito_id": hito.get("hito_id"),
            "status": status,
            "required_for_pass": bool(hito.get("required_for_pass")),
            "classification": hito.get("classification"),
            "weight": hito.get("weight", 0),
            "findings_total": sum(1 for detail in details if detail["status"] != "pass"),
            "evidence_total": len(details),
            "passed_evidence_total": sum(1 for detail in details if detail["status"] == "pass"),
        }

    def _gap_for_evidence(self, detail: dict[str, Any]) -> dict[str, Any]:
        severity = "block" if detail["required_for_pass"] and detail["blocker_on_missing"] else "warning"
        if detail["requirement_level"] == "advisory":
            severity = "info"
        return {
            "gap_id": f"{detail['hito_id'].lower()}-{detail['evidence_id']}-{detail['status']}",
            "hito_id": detail["hito_id"],
            "evidence_id": detail["evidence_id"],
            "severity": severity,
            "status": detail["status"],
            "message": f"{detail['hito_id']} evidence '{detail['title']}' is {detail['status']}: {detail['reason']}.",
            "path": detail["path"],
            "action": "Generate or restore the mapped local evidence artifact before final declaration.",
        }

    def _score(self, criteria: dict[str, Any], evidence_results: list[dict[str, Any]]) -> float:
        required = [item for item in evidence_results if item["required_for_pass"]]
        if not required:
            return 0.0
        if all(item["status"] == "pass" for item in required):
            return 100.0
        weighted_total = sum(float(item.get("weight") or 0) for item in required)
        if weighted_total > 0:
            score = sum(float(item.get("weight") or 0) for item in required if item["status"] == "pass")
            return round(min(score, 100.0), 3)
        passed = sum(1 for item in required if item["status"] == "pass")
        return round((passed / len(required)) * 100, 3)

    def _load_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {"status": "missing", "reason": "path does not exist"}
        try:
            return {"status": "pass", "reason": "valid json", "content": json.loads(path.read_text(encoding="utf-8"))}
        except json.JSONDecodeError as exc:
            return {
                "status": "failed",
                "reason": "invalid json",
                "metadata": {"line": exc.lineno, "column": exc.colno, "message": exc.msg},
            }

    def _extract_schema_id(self, payload: Any) -> str | None:
        if not isinstance(payload, dict):
            return None
        for key in ("schema_id", "x-devpilot-schema-id"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
        return None

    def _resolve_inside_root(self, value: str) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Evidence path escapes project root: {value}") from exc
        return resolved

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def _base_summary(self, *, criteria_path: Path) -> dict[str, Any]:
        return {
            "scope": "production-ready-local",
            "criteria_path": self._relative(criteria_path),
            "production_ready_local_declared": False,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
            "preliminary": True,
        }

    def _safety(self) -> dict[str, bool]:
        return {
            "local_first": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
        }


class ProductionReadyClaimsValidator:
    """Validate production-ready-local claims and no-go gates.

    POST-H-025-D deliberately validates documentation and machine-readable report
    claims without interpreting prose through a model. Affirmative enterprise,
    compliance, remote or SaaS readiness claims block. Negative, bounded or
    design-only statements are allowed because DevPilot must keep documenting
    what is intentionally not enabled.
    """

    CLAIM_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
        (
            "enterprise_ready",
            re.compile(r"\benterprise[- ]ready\b|\benterprise production-ready\b|\bplataforma enterprise productiva completa\b", re.IGNORECASE),
            "Enterprise-ready claims are out of scope for POST-H-025.",
        ),
        (
            "compliance_certified",
            re.compile(r"\bcompliance[- ]certified\b|\bcompliance certificado\b|\bcertificaci[oó]n compliance\b|\bcertification_claimed\s*[:=]\s*true\b|\bcompliance_certification_claim\s*[:=]\s*true\b", re.IGNORECASE),
            "Compliance certification claims are out of scope for POST-H-025.",
        ),
        (
            "remote_ready",
            re.compile(r"\bremote[- ]ready\b|\bremote execution\s+(enabled|true|allowed|segura)\b|\bremote_execution_enabled\s*[:=]\s*true\b", re.IGNORECASE),
            "Remote readiness and enabled remote execution are out of scope for POST-H-025.",
        ),
        (
            "saas_ready",
            re.compile(r"\bsaas[- ]ready\b|\bplataforma saas\b|\bsaas productiv", re.IGNORECASE),
            "SaaS-ready claims are out of scope for POST-H-025.",
        ),
        (
            "generic_production_ready",
            re.compile(r"\bproduction-ready\b(?!-local)", re.IGNORECASE),
            "Generic production-ready claims must be scoped as production-ready-local.",
        ),
    )
    NEGATION_MARKERS = (
        "no ",
        "not ",
        "never",
        "nunca",
        "sin ",
        "false",
        "disabled",
        "deshabilitad",
        "block",
        "blocked",
        "bloque",
        "pendiente",
        "design-only",
        "does not",
        "must not",
        "not declare",
        "!= ",
        "queda para",
        "reserved",
        "limit",
        "solo",
        "only",
        "local-only",
        "no-certific",
        "no certific",
        "impedir",
        "disallow",
        "forbid",
        "prohibit",
        "fuera del alcance",
        "out of scope",
        "remain false",
        "remains false",
        "no-go",
        "future",
        "diferencia",
    )
    NO_GO_FIELDS = (
        "remote_execution_enabled",
        "connector_write_enabled",
        "plugin_execution_enabled",
        "external_apis_required",
        "compliance_certification_claim",
        "enterprise_ready_claim",
        "remote_ready_claim",
        "saas_ready_claim",
    )
    PROJECT_STATE_NO_GO_FIELDS = (
        "remote_execution_enabled",
        "connector_write_enabled",
        "plugin_execution_enabled",
        "post_h_025_remote_execution_enabled",
        "post_h_025_connector_write_enabled",
        "post_h_025_plugin_execution_enabled",
        "post_h_025_external_apis_required",
        "post_h_025_enterprise_ready_claimed",
        "post_h_025_compliance_certified_claimed",
        "post_h_025_remote_ready_claimed",
        "post_h_025_saas_ready_claimed",
    )

    def __init__(self, root: Path, *, options: ProductionReadyClaimsValidatorOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ProductionReadyClaimsValidatorOptions()

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        document_results: list[dict[str, Any]] = []
        for relative_path in self.options.document_paths:
            result = self._scan_document(relative_path)
            document_results.append(result)
            for violation in result["violations"]:
                findings.append(
                    Finding(
                        "PRODUCTION_READY_FORBIDDEN_DOCUMENT_CLAIM",
                        violation["message"],
                        Severity.BLOCK,
                        path=relative_path,
                        metadata=violation,
                    )
                )
            if result["status"] == "missing":
                findings.append(
                    Finding(
                        "PRODUCTION_READY_CLAIMS_DOCUMENT_MISSING",
                        "Required claims document is missing.",
                        Severity.BLOCK,
                        path=relative_path,
                    )
                )

        report_result = self._load_or_build_report()
        report = report_result.get("report")
        if report_result["status"] != "pass":
            findings.append(
                Finding(
                    "PRODUCTION_READY_REPORT_UNAVAILABLE_FOR_CLAIMS_VALIDATION",
                    "ProductionReadyLocalReport could not be loaded or built for claims validation.",
                    Severity.BLOCK,
                    metadata=report_result,
                )
            )
        elif isinstance(report, dict):
            findings.extend(self._report_findings(report))

        project_state_result = self._validate_project_state_flags()
        for violation in project_state_result["violations"]:
            findings.append(
                Finding(
                    "PRODUCTION_READY_PROJECT_STATE_NO_GO_ENABLED",
                    "Project state enables or claims a POST-H-025 no-go capability.",
                    Severity.BLOCK,
                    path=project_state_result.get("path"),
                    metadata=violation,
                )
            )

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.FAIL, Severity.ERROR}]
        ok = not blocking
        summary = {
            "quality_gate_subgate": "production-ready-claims-validator",
            "documents_scanned_total": len(document_results),
            "documents_missing_total": sum(1 for item in document_results if item["status"] == "missing"),
            "forbidden_document_claims_total": sum(len(item["violations"]) for item in document_results),
            "report_validated": report_result["status"] == "pass",
            "report_source": report_result.get("source"),
            "report_claim_violations_total": report_result.get("claim_violations_total", 0),
            "report_no_go_violations_total": report_result.get("no_go_violations_total", 0),
            "project_state_validated": project_state_result["status"] == "pass",
            "project_state_no_go_violations_total": len(project_state_result["violations"]),
            "claims_valid": ok,
            "no_go_gates_valid": ok,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
            "preliminary": True,
        }
        return CommandResult(
            "production-ready claims validate",
            ok,
            ExitCode.PASS if ok else ExitCode.BLOCK,
            "Production-ready-local claims and no-go gates passed." if ok else "Production-ready-local claims validation blocked.",
            data={
                "summary": summary,
                "documents": document_results,
                "report": report_result,
                "project_state": project_state_result,
                "safety": {
                    "local_first": True,
                    "read_only": True,
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "source_mutations_performed": False,
                },
            },
            findings=findings or [
                Finding(
                    "PRODUCTION_READY_CLAIMS_VALIDATOR_PASS",
                    "Documentation, report claims and no-go flags stay within production-ready-local scope.",
                    Severity.INFO,
                    metadata={"documents_scanned_total": len(document_results)},
                )
            ],
        )

    def _scan_document(self, relative_path: str) -> dict[str, Any]:
        path = self._resolve_inside_root(relative_path)
        if not path.exists():
            return {"path": relative_path, "status": "missing", "violations": [], "lines_scanned": 0}
        text = path.read_text(encoding="utf-8")
        violations: list[dict[str, Any]] = []
        for index, line in enumerate(text.splitlines(), start=1):
            normalized = line.strip()
            if not normalized:
                continue
            for claim_type, pattern, message in self.CLAIM_RULES:
                if not pattern.search(normalized):
                    continue
                lowered = normalized.lower()
                if claim_type == "generic_production_ready" and (
                    "production-ready-local" in lowered
                    or "production-ready local" in lowered
                    or "production-ready-claims-validator" in lowered
                ):
                    continue
                if self._line_is_bounded_or_negated(normalized):
                    continue
                violations.append(
                    {
                        "claim_type": claim_type,
                        "line": index,
                        "message": message,
                        "excerpt": normalized[:240],
                    }
                )
        return {"path": relative_path, "status": "pass" if not violations else "block", "violations": violations, "lines_scanned": len(text.splitlines())}

    def _load_or_build_report(self) -> dict[str, Any]:
        if self.options.report_path:
            path = self._resolve_inside_root(self.options.report_path)
            if not path.exists():
                return {"status": "missing", "source": self._relative(path), "reason": "report path does not exist"}
            try:
                report = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                return {"status": "failed", "source": self._relative(path), "reason": "invalid json", "error": str(exc)}
            result = {"status": "pass", "source": self._relative(path), "report": report}
            result.update(self._report_violation_counts(report))
            return result
        if not self.options.include_gate_report:
            return {"status": "skipped", "source": "none", "reason": "include_gate_report=false"}
        gate_result = ProductionReadyDeclarationGate(self.root).check()
        if not gate_result.ok and "report" not in (gate_result.data or {}):
            return {"status": "failed", "source": "ProductionReadyDeclarationGate", "reason": gate_result.message}
        report = (gate_result.data or {}).get("report")
        result = {"status": "pass", "source": "ProductionReadyDeclarationGate", "report": report}
        result.update(self._report_violation_counts(report if isinstance(report, dict) else {}))
        return result

    def _report_findings(self, report: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        claims = dict(report.get("claims") or {})
        for key in ("enterprise_ready", "remote_ready", "compliance_certified", "saas_ready"):
            if claims.get(key) is not False:
                findings.append(
                    Finding(
                        "PRODUCTION_READY_REPORT_FORBIDDEN_CLAIM",
                        f"ProductionReadyLocalReport claim must remain false: {key}.",
                        Severity.BLOCK,
                        metadata={"claim": key, "value": claims.get(key)},
                    )
                )
        if claims.get("production_ready_local") is True:
            if report.get("decision") != "PASS" or int(report.get("blocking_gaps_total") or 0) != 0 or report.get("no_go_gates_passed") is not True:
                findings.append(
                    Finding(
                        "PRODUCTION_READY_LOCAL_REPORT_PASS_CONDITION_MISMATCH",
                        "production_ready_local=true is allowed only for PASS reports with zero blockers and passed no-go gates.",
                        Severity.BLOCK,
                        metadata={
                            "decision": report.get("decision"),
                            "blocking_gaps_total": report.get("blocking_gaps_total"),
                            "no_go_gates_passed": report.get("no_go_gates_passed"),
                        },
                    )
                )
        no_go_gates = dict(report.get("no_go_gates") or {})
        safety = dict(report.get("safety") or {})
        for field in self.NO_GO_FIELDS:
            if no_go_gates.get(field) is not False:
                findings.append(
                    Finding(
                        "PRODUCTION_READY_REPORT_NO_GO_ENABLED",
                        f"ProductionReadyLocalReport no-go gate must remain false: {field}.",
                        Severity.BLOCK,
                        metadata={"field": field, "value": no_go_gates.get(field)},
                    )
                )
        for field in ("network_used", "external_api_used", "mutations_performed", "source_mutations_performed"):
            if safety.get(field) is not False:
                findings.append(
                    Finding(
                        "PRODUCTION_READY_REPORT_SAFETY_FLAG_ENABLED",
                        f"ProductionReadyLocalReport safety flag must remain false: {field}.",
                        Severity.BLOCK,
                        metadata={"field": field, "value": safety.get(field)},
                    )
                )
        return findings

    def _report_violation_counts(self, report: dict[str, Any]) -> dict[str, int]:
        claim_violations = 0
        no_go_violations = 0
        claims = dict(report.get("claims") or {})
        for key in ("enterprise_ready", "remote_ready", "compliance_certified", "saas_ready"):
            if claims.get(key) is not False:
                claim_violations += 1
        no_go_gates = dict(report.get("no_go_gates") or {})
        no_go_violations += sum(1 for field in self.NO_GO_FIELDS if no_go_gates.get(field) is not False)
        safety = dict(report.get("safety") or {})
        no_go_violations += sum(1 for field in ("network_used", "external_api_used", "mutations_performed", "source_mutations_performed") if safety.get(field) is not False)
        return {"claim_violations_total": claim_violations, "no_go_violations_total": no_go_violations}

    def _validate_project_state_flags(self) -> dict[str, Any]:
        if not self.options.project_state_path:
            return {"status": "skipped", "path": None, "violations": []}
        path = self._resolve_inside_root(self.options.project_state_path)
        if not path.exists():
            return {"status": "missing", "path": self._relative(path), "violations": [{"field": "project_state", "value": "missing"}]}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {"status": "failed", "path": self._relative(path), "violations": [{"field": "project_state", "value": "invalid_json", "error": str(exc)}]}
        violations = [
            {"field": field, "value": payload.get(field)}
            for field in self.PROJECT_STATE_NO_GO_FIELDS
            if payload.get(field) is not False
        ]
        return {"status": "pass" if not violations else "block", "path": self._relative(path), "violations": violations}

    def _line_is_bounded_or_negated(self, line: str) -> bool:
        lowered = line.lower()
        return any(marker in lowered for marker in self.NEGATION_MARKERS)

    def _resolve_inside_root(self, value: str) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Claims validation path escapes project root: {value}") from exc
        return resolved

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()


class ProductionReadyDeclarationGate:
    """Expose a deterministic PASS/BLOCK gate for production-ready-local.

    POST-H-025-C is the first public CLI/API wrapper around the read-only
    evidence aggregator. It converts PASS_CANDIDATE/BLOCK_CANDIDATE into a
    schema-validated ProductionReadyLocalReport, writes evidence only when
    explicitly requested, and keeps enterprise/remote/compliance/SaaS claims
    disabled.
    """

    def __init__(self, root: Path, *, options: ProductionReadyDeclarationGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ProductionReadyDeclarationGateOptions()

    def check(self) -> CommandResult:
        aggregate_result = ProductionReadyEvidenceAggregator(
            self.root,
            options=ProductionReadyEvidenceAggregatorOptions(criteria_path=self.options.criteria_path),
        ).aggregate()
        if not aggregate_result.ok:
            return CommandResult(
                "industrial-readiness production-ready-local",
                False,
                aggregate_result.exit_code,
                "Production-ready-local declaration gate could not load evidence.",
                data={
                    "summary": {
                        "scope": "production-ready-local",
                        "decision": "ERROR",
                        "production_ready_local_declared": False,
                        "reports_written": False,
                        "read_only": True,
                        "network_used": False,
                        "external_api_used": False,
                        "mutations_performed": False,
                        "source_mutations_performed": False,
                        "preliminary": True,
                    },
                    "aggregate": aggregate_result.data,
                    "safety": self._safety(),
                },
                findings=aggregate_result.findings,
            )

        report = self._build_report(aggregate_result)
        validation = SchemaValidator(self.root).validate_payload(
            schema="ProductionReadyLocalReport",
            payload=report,
            instance_label="in-memory:production-ready-local-report",
        )
        if not validation.ok:
            return CommandResult(
                "industrial-readiness production-ready-local",
                False,
                validation.exit_code,
                "Production-ready-local report failed schema validation.",
                data={
                    "summary": {
                        "scope": "production-ready-local",
                        "decision": report["decision"],
                        "production_ready_local_declared": False,
                        "reports_written": False,
                        "read_only": True,
                        "network_used": False,
                        "external_api_used": False,
                        "mutations_performed": False,
                        "source_mutations_performed": False,
                        "preliminary": True,
                    },
                    "report": report,
                    "validation": validation.data,
                    "safety": self._safety(),
                },
                findings=validation.findings,
            )

        reports: dict[str, str] = {}
        if self.options.write_report:
            reports = self._write_reports(report)
            report["summary"]["reports_written"] = True

        decision = report["decision"]
        ok = decision == "PASS"
        findings = list(aggregate_result.findings)
        if ok:
            findings.append(
                Finding(
                    "PRODUCTION_READY_LOCAL_GATE_PASS",
                    "Production-ready-local gate passed with zero blockers and bounded claims.",
                    Severity.INFO,
                    metadata={"score": report["score"], "required_hitos_total": report["required_hitos_total"]},
                )
            )
        else:
            findings.append(
                Finding(
                    "PRODUCTION_READY_LOCAL_GATE_BLOCK",
                    "Production-ready-local gate blocked because required blockers remain.",
                    Severity.BLOCK,
                    metadata={"blocking_gaps_total": report["blocking_gaps_total"], "score": report["score"]},
                )
            )

        summary = dict(report["summary"])
        summary["reports_written"] = bool(reports)
        return CommandResult(
            "industrial-readiness production-ready-local",
            ok,
            ExitCode.PASS if ok else ExitCode.BLOCK,
            "Production-ready-local gate passed." if ok else "Production-ready-local gate blocked.",
            data={
                "summary": summary,
                "report": report,
                "reports": reports,
                "aggregate": aggregate_result.data,
                "safety": self._safety(),
            },
            findings=findings,
        )

    def _build_report(self, aggregate_result: CommandResult) -> dict[str, Any]:
        aggregate = aggregate_result.data or {}
        aggregate_summary = dict(aggregate.get("summary") or {})
        score = float(aggregate_summary.get("score") or 0)
        minimum_score = float(aggregate_summary.get("minimum_score") or 90)
        blocking_gaps_total = int(aggregate_summary.get("blocking_gaps_total") or 0)
        required_hitos_total = int(aggregate_summary.get("required_hitos_total") or 0)
        passed_hitos_total = int(aggregate_summary.get("passed_hitos_total") or 0)
        no_go_gates_passed = bool(aggregate_summary.get("no_go_gates_passed") is True)
        decision = (
            "PASS"
            if score >= minimum_score
            and blocking_gaps_total == 0
            and passed_hitos_total == required_hitos_total
            and no_go_gates_passed
            else "BLOCK"
        )
        gaps = list(aggregate.get("gaps") or [])
        summary = {
            "scope": "production-ready-local",
            "decision": decision,
            "candidate_decision": aggregate_summary.get("candidate_decision"),
            "production_ready_local_declared": decision == "PASS",
            "formal_audit_declaration_pending": True,
            "minimum_score": minimum_score,
            "score": score,
            "required_hitos_total": required_hitos_total,
            "passed_hitos_total": passed_hitos_total,
            "blocking_gaps_total": blocking_gaps_total,
            "warning_gaps_total": aggregate_summary.get("warning_gaps_total", 0),
            "info_gaps_total": aggregate_summary.get("info_gaps_total", 0),
            "gaps_total": aggregate_summary.get("gaps_total", len(gaps)),
            "no_go_gates_passed": no_go_gates_passed,
            "block_actions_total": sum(1 for gap in gaps if gap.get("severity") == "block" and gap.get("action")),
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
            "preliminary": True,
        }
        return {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-PRODUCTION-READY-LOCAL-REPORT-V1",
            "report_id": f"production-ready-local-report-{self.options.report_id_suffix}",
            "created_by": "POST-H-025-C",
            "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "scope": "production-ready-local",
            "decision": decision,
            "score": score,
            "minimum_score": minimum_score,
            "blocking_gaps_total": blocking_gaps_total,
            "passed_hitos_total": passed_hitos_total,
            "required_hitos_total": required_hitos_total,
            "no_go_gates_passed": no_go_gates_passed,
            "claims": {
                "production_ready_local": decision == "PASS",
                "enterprise_ready": False,
                "remote_ready": False,
                "compliance_certified": False,
                "saas_ready": False,
            },
            "no_go_gates": dict((aggregate.get("intermediate_model") or {}).get("no_go_gates") or {}),
            "evidence_results": list(aggregate.get("evidence_results") or []),
            "evidence_details": list(aggregate.get("evidence_details") or []),
            "gaps": gaps,
            "safety": self._safety(),
            "summary": summary,
            "limitations": [
                "POST-H-025-C exposes the declaration gate via CLI/API and writes report evidence on request.",
                "POST-H-025-C does not validate documentation claims; POST-H-025-D owns no-go claims validation.",
                "POST-H-025-C does not emit the final audit declaration artifact; POST-H-025-E owns final PASS/BLOCK declaration packaging.",
                "The gate remains local-first, read-only over source evidence and does not use network or external APIs.",
            ],
        }

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self._resolve_inside_root(self.options.output_json)
        markdown_path = self._resolve_inside_root(self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(self._markdown_report(report), encoding="utf-8")
        return {"json": self._relative(json_path), "markdown": self._relative(markdown_path)}

    def _markdown_report(self, report: dict[str, Any]) -> str:
        summary = report["summary"]
        lines = [
            "# Production-ready-local gate report",
            "",
            f"- Decision: `{report['decision']}`",
            f"- Score: `{report['score']}` / minimum `{report['minimum_score']}`",
            f"- Required hitos: `{report['passed_hitos_total']}/{report['required_hitos_total']}`",
            f"- Blocking gaps: `{report['blocking_gaps_total']}`",
            f"- No-go gates passed: `{report['no_go_gates_passed']}`",
            f"- Production-ready-local declared by gate: `{summary['production_ready_local_declared']}`",
            f"- Formal audit declaration pending: `{summary['formal_audit_declaration_pending']}`",
            "",
            "## Claims",
            "",
        ]
        for key, value in report["claims"].items():
            lines.append(f"- `{key}`: `{value}`")
        lines.extend(["", "## Gaps", ""])
        if report["gaps"]:
            for gap in report["gaps"]:
                action = gap.get("action") or "Review mapped evidence and restore the missing artifact."
                lines.append(f"- `{gap.get('severity')}` `{gap.get('gap_id')}`: {gap.get('message')} Action: {action}")
        else:
            lines.append("- No gaps reported.")
        lines.extend(["", "## Limitations", ""])
        for item in report["limitations"]:
            lines.append(f"- {item}")
        return "\n".join(lines) + "\n"

    def _resolve_inside_root(self, value: str) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Report path escapes project root: {value}") from exc
        return resolved

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def _safety(self) -> dict[str, bool]:
        return {
            "local_first": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
        }
