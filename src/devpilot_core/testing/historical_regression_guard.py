from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.schemas import SchemaValidator

from .contracts import TestContractRegistry
from .impact_rules import TestImpactRuleRegistryOptions, TestImpactRuleRegistryRunner
from .impact_v2 import TestImpactAnalyzerV2, TestImpactV2Options
from .profile_taxonomy import TestProfileTaxonomyOptions, TestProfileTaxonomyRunner
from .profiles_v2 import TestContractRegistryV2Validator
from .release_candidate_profile import ReleaseCandidateTestProfileOptions, ReleaseCandidateTestProfileRunner

POST_H_029_E_CREATED_BY = "POST-H-029-E"
HISTORICAL_REGRESSION_GUARD_COMMAND = "tests regression-guard"
HISTORICAL_REGRESSION_GUARD_SCHEMA_ID = "SCHEMA-DEVPL-HISTORICAL-REGRESSION-GUARD-REPORT-V1"
HISTORICAL_REGRESSION_GUARD_CONTRACT = "HistoricalRegressionGuardReport"
DEFAULT_REGRESSION_GUARD_REPORT_JSON = Path("outputs/reports/historical_regression_guard_report.json")
DEFAULT_REGRESSION_GUARD_REPORT_MARKDOWN = Path("outputs/reports/historical_regression_guard_report.md")

_CONTEXTS_REQUIRING_EXPLICIT_DECISION = {"backlog-closure", "release-candidate", "major-hito"}
_FULL_REGRESSION_CONTEXTS = {"backlog-closure", "release-candidate", "major-hito"}
_FULL_REGRESSION_SENSITIVE_FRAGMENTS = (
    "docs/schemas/schema_catalog.json",
    ".devpilot/project_state.json",
    "src/devpilot_core/quality/gate.py",
    "src/devpilot_core/cli.py",
    "src/devpilot_core/interfaces/api/security",
    "src/devpilot_core/industrial/production_ready.py",
    "docs/schemas/test_contract_registry_v2.schema.json",
    "docs/schemas/test_contract_registry.schema.json",
    ".devpilot/testing/test_contract_registry_v2.json",
    ".devpilot/testing/test_contract_registry.json",
)
_WAIVER_REQUIRED_FIELDS = {"owner", "reason", "risk", "tests_executed", "expires_at"}
_ALLOWED_REGRESSION_DECISIONS = {"auto", "full", "focal-expanded", "waiver", "pending"}


@dataclass(frozen=True)
class HistoricalRegressionGuardOptions:
    context: str = "micro-sprint"
    changed_paths: tuple[str, ...] = field(default_factory=tuple)
    changed_paths_file: str | Path | None = None
    regression_decision: str = "auto"
    full_regression_run: bool = False
    evidence_logs: tuple[str | Path, ...] = field(default_factory=tuple)
    evidence_reports: tuple[str | Path, ...] = field(default_factory=tuple)
    waiver_file: str | Path | None = None
    output_json: str | Path = DEFAULT_REGRESSION_GUARD_REPORT_JSON
    output_markdown: str | Path = DEFAULT_REGRESSION_GUARD_REPORT_MARKDOWN
    write_report: bool = False


class HistoricalRegressionGuardRunner:
    """Evaluate whether a DevPilot closure has enough regression evidence.

    The guard is deliberately non-executing. It formalizes the decision that was
    previously implicit: full regression, expanded focal regression, or a bounded
    waiver. Runtime validation logs are referenced as evidence, never versioned
    as source-of-truth artifacts.
    """

    def __init__(self, root: Path, options: HistoricalRegressionGuardOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or HistoricalRegressionGuardOptions()
        self.output_json = self._resolve(self.options.output_json)
        self.output_markdown = self._resolve(self.options.output_markdown)

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        context = self.options.context
        if context not in {"micro-sprint", "backlog-closure", "release-candidate", "major-hito"}:
            findings.append(Finding("HISTORICAL_REGRESSION_CONTEXT_INVALID", "Regression guard context is unsupported.", Severity.ERROR, metadata={"context": context}))
        decision = self.options.regression_decision
        if decision not in _ALLOWED_REGRESSION_DECISIONS:
            findings.append(Finding("HISTORICAL_REGRESSION_DECISION_INVALID", "Regression decision is unsupported.", Severity.ERROR, metadata={"decision": decision}))

        changed_paths = self._collect_changed_paths(findings)
        impact_result = self._impact(changed_paths)
        component_results = self._component_results()
        for result in component_results:
            findings.extend(self._component_findings(result))

        unmatched_paths = []
        if isinstance(impact_result.data, dict):
            unmatched_paths = list(impact_result.data.get("unmatched_paths") or [])
            findings.extend(self._component_findings(impact_result, prefix="IMPACT_ANALYZER"))

        full_reasons = self._full_regression_reasons(context, changed_paths, unmatched_paths)
        full_regression_required = bool(full_reasons)
        explicit_decision_required = context in _CONTEXTS_REQUIRING_EXPLICIT_DECISION or full_regression_required
        effective_decision = self._effective_decision(context, decision, full_regression_required)
        evidence = self._evidence(findings)
        waiver = self._waiver(findings) if effective_decision == "waiver" else {"provided": False, "valid": False, "reason": None}

        if explicit_decision_required and effective_decision == "pending":
            findings.append(Finding("HISTORICAL_REGRESSION_DECISION_REQUIRED", "Closure context requires an explicit regression decision.", Severity.BLOCK, metadata={"context": context, "full_regression_required": full_regression_required}))
        if full_regression_required and effective_decision == "focal-expanded":
            findings.append(Finding("HISTORICAL_REGRESSION_FULL_REQUIRED", "Full regression is required for this context/change set; expanded focal evidence is insufficient without waiver.", Severity.BLOCK, metadata={"reasons": full_reasons}))
        if effective_decision == "full" and not self.options.full_regression_run:
            findings.append(Finding("HISTORICAL_REGRESSION_FULL_EVIDENCE_PENDING", "Full regression decision is selected but full_regression_run evidence was not declared.", Severity.WARNING, metadata={"evidence_logs_total": len(evidence["logs"]), "evidence_reports_total": len(evidence["reports"])}))
        if effective_decision == "waiver" and not waiver.get("valid"):
            findings.append(Finding("HISTORICAL_REGRESSION_WAIVER_INVALID", "Waiver decision requires owner, reason, risk, tests_executed and future expires_at.", Severity.BLOCK, metadata={"waiver": waiver}))
        if not evidence["logs"] and not evidence["reports"]:
            findings.append(Finding("HISTORICAL_REGRESSION_EVIDENCE_PENDING", "Validation logs/reports are not attached; guard records evidence as pending.", Severity.WARNING, metadata={"context": context}))

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
        decision_label = "PASS" if not blocking else "BLOCK"
        status = "pass" if not blocking else "blocked"
        report = self._build_report(
            context=context,
            decision=effective_decision,
            decision_label=decision_label,
            status=status,
            changed_paths=changed_paths,
            impact_result=impact_result,
            component_results=component_results,
            full_regression_required=full_regression_required,
            full_reasons=full_reasons,
            explicit_decision_required=explicit_decision_required,
            evidence=evidence,
            waiver=waiver,
            findings=findings,
            warnings=warnings,
            blocking=blocking,
        )
        schema_result = SchemaValidator(self.root).validate_payload(
            schema=HISTORICAL_REGRESSION_GUARD_CONTRACT,
            payload=report,
            instance_label="HistoricalRegressionGuardReport(payload)",
        )
        findings.extend(schema_result.findings)
        if not schema_result.ok:
            report["status"] = "blocked"
            report["summary"]["decision"] = "BLOCK"
            findings.append(Finding("HISTORICAL_REGRESSION_GUARD_SCHEMA_INVALID", "Generated historical regression guard report does not validate against schema.", Severity.BLOCK))
            blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]

        reports: dict[str, str] = {}
        if self.options.write_report:
            reports = self._write_report(report)
            report["summary"]["reports_written"] = True
            report["safety"]["reports_written"] = True

        ok = not blocking
        summary = report["summary"]
        return CommandResult(
            command=HISTORICAL_REGRESSION_GUARD_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else exit_code_for_findings(blocking, default_ok=False),
            message="Historical regression guard passed." if ok else "Historical regression guard blocked closure.",
            data={"summary": summary, "report": report, "reports": reports, "notes": report["notes"]},
            findings=findings or [Finding("HISTORICAL_REGRESSION_GUARD_PASS", "Historical regression guard passed.", Severity.INFO, metadata=summary)],
        )

    def _collect_changed_paths(self, findings: list[Finding]) -> list[str]:
        paths = [str(item).replace("\\", "/") for item in self.options.changed_paths if str(item).strip()]
        if self.options.changed_paths_file:
            path = self._resolve(self.options.changed_paths_file)
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    value = line.strip()
                    if value and not value.startswith("#"):
                        paths.append(value.replace("\\", "/"))
            except Exception as exc:
                findings.append(Finding("HISTORICAL_REGRESSION_CHANGED_PATHS_FILE_INVALID", f"Could not read changed paths file: {exc}", Severity.ERROR, path=self._relative(path)))
        return sorted(dict.fromkeys(paths))

    def _impact(self, changed_paths: list[str]) -> CommandResult:
        if not changed_paths:
            return CommandResult(
                command="test-impact analyze-v2",
                ok=True,
                exit_code=ExitCode.PASS,
                message="No changed paths supplied to regression guard impact pass.",
                data={"summary": {"changed_paths_total": 0, "unmatched_paths_total": 0, "tests_executed": False, "preliminary": True}, "unmatched_paths": []},
                findings=[Finding("HISTORICAL_REGRESSION_IMPACT_NOT_REQUESTED", "No changed paths were supplied; impact analysis is treated as not requested.", Severity.INFO)],
            )
        return TestImpactAnalyzerV2(self.root, TestImpactV2Options(changed_paths=tuple(changed_paths))).analyze()

    def _component_results(self) -> list[CommandResult]:
        return [
            TestProfileTaxonomyRunner(self.root, TestProfileTaxonomyOptions(write_report=False)).run(),
            TestImpactRuleRegistryRunner(self.root, TestImpactRuleRegistryOptions(write_report=False)).validate(),
            TestContractRegistry(self.root).validate(),
            TestContractRegistryV2Validator(self.root).validate(),
            ReleaseCandidateTestProfileRunner(self.root, ReleaseCandidateTestProfileOptions(write_report=False)).run(),
        ]

    def _component_findings(self, result: CommandResult, prefix: str | None = None) -> list[Finding]:
        if result.ok:
            return []
        stem = prefix or result.command.upper().replace(" ", "_").replace("-", "_")
        return [
            Finding(
                id=f"HISTORICAL_REGRESSION_COMPONENT_{stem}_BLOCKED",
                message=f"Required regression guard component failed: {result.command}",
                severity=Severity.BLOCK,
                metadata={"source_command": result.command, "exit_code": int(result.exit_code)},
            )
        ]

    def _full_regression_reasons(self, context: str, changed_paths: list[str], unmatched_paths: list[str]) -> list[dict[str, Any]]:
        reasons: list[dict[str, Any]] = []
        if context in _FULL_REGRESSION_CONTEXTS:
            reasons.append({"id": "context", "reason": f"{context} requires explicit full/focal/waiver decision", "context": context})
        if unmatched_paths:
            reasons.append({"id": "unmatched-paths", "reason": "Changed paths are not mapped by TCR v2 impact rules", "paths": unmatched_paths})
        sensitive = [path for path in changed_paths if any(fragment in path for fragment in _FULL_REGRESSION_SENSITIVE_FRAGMENTS)]
        if sensitive:
            reasons.append({"id": "sensitive-paths", "reason": "Changed paths touch P0/P1 regression-sensitive surfaces", "paths": sensitive})
        return reasons

    def _effective_decision(self, context: str, decision: str, full_required: bool) -> str:
        if decision != "auto":
            return decision
        if context == "micro-sprint" and not full_required:
            return "focal-expanded"
        return "pending"

    def _evidence(self, findings: list[Finding]) -> dict[str, Any]:
        logs = []
        reports = []
        for raw in self.options.evidence_logs:
            path = self._resolve(raw)
            logs.append({"path": self._relative(path), "exists": path.exists(), "kind": "log"})
            if not path.exists():
                findings.append(Finding("HISTORICAL_REGRESSION_EVIDENCE_LOG_MISSING", "Declared validation log does not exist.", Severity.WARNING, path=self._relative(path)))
        for raw in self.options.evidence_reports:
            path = self._resolve(raw)
            reports.append({"path": self._relative(path), "exists": path.exists(), "kind": "report"})
            if not path.exists():
                findings.append(Finding("HISTORICAL_REGRESSION_EVIDENCE_REPORT_MISSING", "Declared validation report does not exist.", Severity.WARNING, path=self._relative(path)))
        return {"logs": logs, "reports": reports, "logs_total": len(logs), "reports_total": len(reports), "pending": not logs and not reports}

    def _waiver(self, findings: list[Finding]) -> dict[str, Any]:
        if not self.options.waiver_file:
            return {"provided": False, "valid": False, "reason": "missing waiver file"}
        path = self._resolve(self.options.waiver_file)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(Finding("HISTORICAL_REGRESSION_WAIVER_FILE_INVALID", f"Could not parse waiver file: {exc}", Severity.BLOCK, path=self._relative(path)))
            return {"provided": True, "valid": False, "path": self._relative(path), "reason": "invalid json"}
        missing = sorted(_WAIVER_REQUIRED_FIELDS - set(payload))
        tests = payload.get("tests_executed")
        expires_at = str(payload.get("expires_at") or "")
        future_expiry = self._future_expiry(expires_at)
        valid = not missing and isinstance(tests, list) and bool(tests) and future_expiry
        return {
            "provided": True,
            "valid": valid,
            "path": self._relative(path),
            "owner": payload.get("owner"),
            "reason": payload.get("reason"),
            "risk": payload.get("risk"),
            "tests_executed": tests if isinstance(tests, list) else [],
            "expires_at": expires_at,
            "missing_fields": missing,
            "future_expiry": future_expiry,
        }

    def _future_expiry(self, value: str) -> bool:
        try:
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized) > datetime.now(UTC)
        except Exception:
            return False

    def _build_report(
        self,
        *,
        context: str,
        decision: str,
        decision_label: str,
        status: str,
        changed_paths: list[str],
        impact_result: CommandResult,
        component_results: list[CommandResult],
        full_regression_required: bool,
        full_reasons: list[dict[str, Any]],
        explicit_decision_required: bool,
        evidence: dict[str, Any],
        waiver: dict[str, Any],
        findings: list[Finding],
        warnings: list[Finding],
        blocking: list[Finding],
    ) -> dict[str, Any]:
        impact_summary = dict((impact_result.data or {}).get("summary") or {})
        components = [
            {
                "command": result.command,
                "ok": result.ok,
                "exit_code": int(result.exit_code),
                "summary": dict((result.data or {}).get("summary") or {}),
            }
            for result in component_results
        ]
        summary = {
            "created_by": POST_H_029_E_CREATED_BY,
            "status": "implemented-initial",
            "decision": decision_label,
            "context": context,
            "regression_decision": decision,
            "changed_paths_total": len(changed_paths),
            "unmatched_paths_total": int(impact_summary.get("unmatched_paths_total", 0) or 0),
            "full_regression_required": full_regression_required,
            "full_regression_reasons_total": len(full_reasons),
            "explicit_decision_required": explicit_decision_required,
            "waiver_provided": bool(waiver.get("provided")),
            "waiver_valid": bool(waiver.get("valid")),
            "evidence_logs_total": int(evidence.get("logs_total", 0)),
            "evidence_reports_total": int(evidence.get("reports_total", 0)),
            "evidence_pending": bool(evidence.get("pending")),
            "components_total": len(components),
            "components_passed_total": sum(1 for item in components if item["ok"]),
            "warnings_total": len(warnings),
            "blocking_findings_total": len(blocking),
            "tests_executed": False,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
            "preliminary": True,
        }
        return {
            "schema_version": "1.0",
            "schema_id": HISTORICAL_REGRESSION_GUARD_SCHEMA_ID,
            "report_id": "devpilot-historical-regression-guard-report",
            "created_by": POST_H_029_E_CREATED_BY,
            "status": status,
            "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "summary": summary,
            "context": context,
            "changed_paths": changed_paths,
            "impact": {"ok": impact_result.ok, "exit_code": int(impact_result.exit_code), "summary": impact_summary},
            "components": components,
            "regression_decision": {
                "selected": decision,
                "full_regression_required": full_regression_required,
                "full_regression_reasons": full_reasons,
                "full_regression_run_declared": self.options.full_regression_run,
                "explicit_decision_required": explicit_decision_required,
            },
            "evidence": evidence,
            "waiver": waiver,
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "tests_executed": False,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "llm_judge_used": False,
                "reports_written": False,
            },
            "findings": [finding.to_dict() for finding in findings],
            "notes": [
                "POST-H-029-E formalizes regression evidence decisions without executing pytest or storing heavy runtime logs in source.",
                "Backlog/release/major-hito closure must decide full, focal-expanded or waiver; undecided closure is blocked.",
                "Waivers are temporary and require owner, reason, risk, tests_executed and expiration.",
                "Full regression remains preserved and mandatory for mapped closure contexts or sensitive/unmapped changes.",
            ],
        }

    def _write_report(self, report: dict[str, Any]) -> dict[str, str]:
        self.output_json.parent.mkdir(parents=True, exist_ok=True)
        self.output_markdown.parent.mkdir(parents=True, exist_ok=True)
        self.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        lines = [
            "# Historical regression guard report",
            "",
            f"- decision: `{report['summary']['decision']}`",
            f"- context: `{report['summary']['context']}`",
            f"- regression_decision: `{report['summary']['regression_decision']}`",
            f"- full_regression_required: `{report['summary']['full_regression_required']}`",
            f"- explicit_decision_required: `{report['summary']['explicit_decision_required']}`",
            f"- blocking_findings_total: `{report['summary']['blocking_findings_total']}`",
            f"- warnings_total: `{report['summary']['warnings_total']}`",
            f"- tests_executed: `{report['summary']['tests_executed']}`",
            "",
            "This report is generated evidence and must not be versioned as a source-of-truth runtime log.",
        ]
        self.output_markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"json": self._relative(self.output_json), "markdown": self._relative(self.output_markdown)}

    def _resolve(self, path: str | Path) -> Path:
        value = Path(path)
        return value if value.is_absolute() else self.root / value

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except Exception:
            return str(path).replace("\\", "/")
