from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator


DEFAULT_CRITERIA_PATH = Path(".devpilot/production/production_ready_local_criteria.json")
DEFAULT_REPORT_JSON_PATH = Path("outputs/reports/production_ready_local_report.json")
DEFAULT_REPORT_MARKDOWN_PATH = Path("outputs/reports/production_ready_local_report.md")


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
