from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity


DEFAULT_CRITERIA_PATH = Path(".devpilot/production/production_ready_local_criteria.json")


@dataclass(frozen=True)
class ProductionReadyEvidenceAggregatorOptions:
    """Options for the POST-H-025-B read-only evidence aggregator."""

    criteria_path: str = str(DEFAULT_CRITERIA_PATH)
    report_id_suffix: str = "intermediate"


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
