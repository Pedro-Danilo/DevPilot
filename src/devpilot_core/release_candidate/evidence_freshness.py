from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator


DEFAULT_LOCAL_RELEASE_CANDIDATE_CRITERIA_PATH = Path(".devpilot/release/local_release_candidate_criteria.json")
DEFAULT_EVIDENCE_FRESHNESS_JSON_PATH = Path("outputs/reports/evidence_freshness_report.json")
DEFAULT_EVIDENCE_FRESHNESS_MARKDOWN_PATH = Path("outputs/reports/evidence_freshness_report.md")


@dataclass(frozen=True)
class EvidenceFreshnessOptions:
    criteria_path: str = str(DEFAULT_LOCAL_RELEASE_CANDIDATE_CRITERIA_PATH)
    output_json: str = str(DEFAULT_EVIDENCE_FRESHNESS_JSON_PATH)
    output_markdown: str = str(DEFAULT_EVIDENCE_FRESHNESS_MARKDOWN_PATH)
    write_report: bool = False
    report_id_suffix: str = "post_h_026_a"


class EvidenceFreshnessScanner:
    """Classify RC evidence freshness without executing commands.

    POST-H-026-A deliberately separates freshness from evidence generation. The
    scanner reads versioned source artifacts, optional runtime reports when they
    already exist, and contextual metadata such as project_state.current_repo. It
    never invokes pytest, never calls network services and never fixes stale
    documents automatically.
    """

    VALID_STATUSES = {"fresh", "stale", "missing", "invalid", "not_applicable"}

    def __init__(self, root: Path, *, options: EvidenceFreshnessOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or EvidenceFreshnessOptions()

    def scan(self) -> CommandResult:
        criteria_path = self._resolve_inside_root(self.options.criteria_path)
        criteria_result = self._load_json(criteria_path)
        if criteria_result["status"] != "pass":
            report = self._error_report(criteria_path=criteria_path, criteria_result=criteria_result)
            return CommandResult(
                "release-candidate evidence-freshness",
                False,
                ExitCode.ERROR,
                "Evidence freshness criteria could not be loaded.",
                data={"summary": report["summary"], "report": report, "safety": report["safety"]},
                findings=[
                    Finding(
                        "EVIDENCE_FRESHNESS_CRITERIA_UNREADABLE",
                        "Local release candidate criteria are missing or invalid.",
                        Severity.ERROR,
                        path=self._relative(criteria_path),
                        metadata=criteria_result,
                    )
                ],
            )

        criteria = criteria_result["content"]
        items = [self._evaluate_item(item) for item in criteria.get("evidence", []) if isinstance(item, dict)]
        critical_items = [item for item in items if item["critical"]]
        critical_stale = [item for item in critical_items if item["status"] == "stale"]
        critical_missing = [item for item in critical_items if item["status"] == "missing"]
        critical_invalid = [item for item in critical_items if item["status"] == "invalid"]
        no_go_gates = dict(criteria.get("no_go_gates", {}))
        no_go_gates_passed = all(value is False for value in no_go_gates.values())
        decision = "PASS" if not critical_stale and not critical_missing and not critical_invalid and no_go_gates_passed else "BLOCK"

        report = {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-EVIDENCE-FRESHNESS-REPORT-V1",
            "report_id": f"evidence-freshness-{self.options.report_id_suffix}",
            "created_by": "POST-H-026-A",
            "created_at": self._now(),
            "scope": "local-release-candidate",
            "decision": decision,
            "repo_version": criteria.get("expected_current_repo"),
            "criteria_id": criteria.get("criteria_id"),
            "criteria_path": self._relative(criteria_path),
            "evidence_total": len(items),
            "fresh_total": self._count(items, "fresh"),
            "stale_total": self._count(items, "stale"),
            "missing_total": self._count(items, "missing"),
            "invalid_total": self._count(items, "invalid"),
            "not_applicable_total": self._count(items, "not_applicable"),
            "critical_total": len(critical_items),
            "critical_stale_total": len(critical_stale),
            "critical_missing_total": len(critical_missing),
            "critical_invalid_total": len(critical_invalid),
            "no_go_gates_passed": no_go_gates_passed,
            "no_go_gates": no_go_gates,
            "items": items,
            "summary": {
                "implemented_status": "implemented-initial",
                "freshness_policy": criteria.get("freshness_policy", "contextual-signature"),
                "reports_written": False,
                "preliminary": True,
                "runtime_evidence_required": False,
            },
            "safety": self._safety(reports_written=False),
            "limitations": [
                "POST-H-026-A checks freshness metadata and local artifact integrity; it does not regenerate evidence.",
                "Optional runtime outputs are classified as not_applicable when absent from a clean repository.",
                "The scanner does not replace the final release candidate PASS/BLOCK report planned for POST-H-026-E.",
            ],
        }

        report["summary"]["reports_written"] = self.options.write_report
        report["safety"] = self._safety(reports_written=self.options.write_report)

        schema_findings, schema_blocked = self._validate_report_contract(report)
        if schema_blocked:
            decision = "BLOCK"
            report["decision"] = "BLOCK"
        findings = self._findings(report)
        findings.extend(schema_findings)

        if self.options.write_report:
            self._write_report(report)

        ok = decision == "PASS"
        return CommandResult(
            "release-candidate evidence-freshness",
            ok,
            ExitCode.PASS if ok else ExitCode.BLOCK,
            "Evidence freshness passed for local release candidate." if ok else "Evidence freshness blocked local release candidate.",
            data={
                "summary": report["summary"] | {
                    "decision": report["decision"],
                    "evidence_total": report["evidence_total"],
                    "fresh_total": report["fresh_total"],
                    "critical_stale_total": report["critical_stale_total"],
                    "critical_missing_total": report["critical_missing_total"],
                    "critical_invalid_total": report["critical_invalid_total"],
                    "reports_written": self.options.write_report,
                },
                "report": report,
                "items": items,
                "safety": report["safety"],
                "reports": self._report_paths() if self.options.write_report else {},
            },
            findings=findings,
        )

    def _evaluate_item(self, item: dict[str, Any]) -> dict[str, Any]:
        path_value = str(item.get("path", ""))
        path = self._resolve_inside_root(path_value)
        critical = bool(item.get("critical", False))
        runtime_optional = bool(item.get("runtime_optional", False))
        checks: list[dict[str, Any]] = []
        status = "fresh"
        reason = "freshness checks passed"
        metadata: dict[str, Any] = {}
        content: Any = None

        if not path.exists():
            status = "not_applicable" if runtime_optional else "missing"
            reason = "optional runtime evidence absent" if runtime_optional else "path does not exist"
        elif path.is_dir():
            status = "invalid"
            reason = "expected evidence file, found directory"
        else:
            if item.get("json_required") or path.suffix.lower() == ".json":
                parsed = self._load_json(path)
                if parsed["status"] != "pass":
                    status = "invalid"
                    reason = parsed["reason"]
                    metadata = parsed.get("metadata", {})
                else:
                    content = parsed["content"]
                    schema_status = self._check_schema_id(content, item.get("expected_schema_id"))
                    checks.append(schema_status)
                    if schema_status["status"] != "pass":
                        status = "invalid"
                        reason = schema_status["reason"]
                        metadata = schema_status.get("metadata", {})

            if status == "fresh":
                text = None if content is not None else self._read_text(path)
                stale_checks = self._context_checks(item=item, content=content, text=text)
                checks.extend(stale_checks)
                failed = [check for check in stale_checks if check["status"] != "pass"]
                if failed:
                    status = "stale"
                    reason = failed[0]["reason"]
                    metadata = {"failed_checks": failed}

        return {
            "evidence_id": item.get("evidence_id"),
            "title": item.get("title"),
            "path": self._relative(path),
            "category": item.get("category"),
            "critical": critical,
            "runtime_optional": runtime_optional,
            "expected_schema_id": item.get("expected_schema_id"),
            "producer_sprint": item.get("producer_sprint"),
            "freshness_policy": item.get("freshness_policy", "contextual-signature"),
            "status": status,
            "reason": reason,
            "checks": checks,
            "metadata": metadata,
        }

    def _context_checks(self, *, item: dict[str, Any], content: Any, text: str | None) -> list[dict[str, Any]]:
        checks: list[dict[str, Any]] = []
        for key, expected in (item.get("expected_fields") or {}).items():
            actual = self._lookup(content, key) if content is not None else None
            checks.append(
                {
                    "check": f"field:{key}",
                    "status": "pass" if actual == expected else "fail",
                    "reason": "field matches expected value" if actual == expected else f"expected {expected!r}, got {actual!r}",
                    "expected": expected,
                    "actual": actual,
                }
            )
        if text is None and content is not None:
            text = json.dumps(content, sort_keys=True, ensure_ascii=False)
        for marker in item.get("required_markers", []) or []:
            found = bool(text and str(marker) in text)
            checks.append(
                {
                    "check": "required_marker",
                    "status": "pass" if found else "fail",
                    "reason": "marker present" if found else f"required marker not found: {marker}",
                    "marker": marker,
                }
            )
        return checks

    def _check_schema_id(self, content: Any, expected: Any) -> dict[str, Any]:
        if not expected:
            return {"check": "schema_id", "status": "pass", "reason": "no schema_id required"}
        actual = self._extract_schema_id(content)
        return {
            "check": "schema_id",
            "status": "pass" if actual == expected else "fail",
            "reason": "schema_id matches expected value" if actual == expected else "schema_id mismatch",
            "metadata": {"expected_schema_id": expected, "actual_schema_id": actual},
        }

    def _validate_report_contract(self, report: dict[str, Any]) -> tuple[list[Finding], bool]:
        """Validate the generated report when the schema contract is available.

        Real DevPilot workspaces include docs/schemas/evidence_freshness_report.schema.json
        and should keep this self-validation blocking. Minimal synthetic workspaces
        used by unit tests may intentionally include only .devpilot/project_state.json
        and local RC criteria; in that case the scanner must still be able to test
        freshness semantics without requiring the whole schema catalog.
        """

        schema_path = self.root / "docs/schemas/evidence_freshness_report.schema.json"
        if not schema_path.exists():
            return [
                Finding(
                    "EVIDENCE_FRESHNESS_SCHEMA_VALIDATION_SKIPPED",
                    "EvidenceFreshnessReport schema validation was skipped because the schema contract is not present in this workspace.",
                    Severity.WARNING,
                    path="docs/schemas/evidence_freshness_report.schema.json",
                    metadata={"reason": "schema_contract_absent", "minimal_workspace_supported": True},
                )
            ], False

        schema_result = SchemaValidator(self.root).validate_payload(
            schema=schema_path.relative_to(self.root).as_posix(),
            payload=report,
            instance_label="in-memory-evidence-freshness-report",
        )
        dependency_missing_only = (
            not schema_result.ok
            and schema_result.findings
            and all(finding.id == "SCHEMA_VALIDATOR_DEPENDENCY_MISSING" for finding in schema_result.findings)
        )
        if dependency_missing_only:
            return [
                Finding(
                    "EVIDENCE_FRESHNESS_SCHEMA_VALIDATION_SKIPPED",
                    "EvidenceFreshnessReport schema validation was skipped because jsonschema is unavailable in this runtime.",
                    Severity.WARNING,
                    metadata={"dependency": "jsonschema"},
                )
            ], False
        if not schema_result.ok:
            return list(schema_result.findings), True
        return [], False

    def _findings(self, report: dict[str, Any]) -> list[Finding]:
        findings = [
            Finding(
                "EVIDENCE_FRESHNESS_EVALUATED",
                "Evidence freshness was evaluated without command execution.",
                Severity.INFO,
                metadata={
                    "decision": report["decision"],
                    "evidence_total": report["evidence_total"],
                    "critical_stale_total": report["critical_stale_total"],
                    "critical_missing_total": report["critical_missing_total"],
                    "critical_invalid_total": report["critical_invalid_total"],
                },
            )
        ]
        for item in report["items"]:
            if item["status"] in {"stale", "missing", "invalid"}:
                findings.append(
                    Finding(
                        "EVIDENCE_FRESHNESS_ITEM_BLOCK" if item["critical"] else "EVIDENCE_FRESHNESS_ITEM_WARNING",
                        f"Evidence item {item['evidence_id']} is {item['status']}: {item['reason']}.",
                        Severity.BLOCK if item["critical"] else Severity.WARNING,
                        path=item["path"],
                        metadata={"evidence_id": item["evidence_id"], "status": item["status"]},
                    )
                )
        return findings

    def _error_report(self, *, criteria_path: Path, criteria_result: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-EVIDENCE-FRESHNESS-REPORT-V1",
            "report_id": f"evidence-freshness-{self.options.report_id_suffix}",
            "created_by": "POST-H-026-A",
            "created_at": self._now(),
            "scope": "local-release-candidate",
            "decision": "BLOCK",
            "repo_version": None,
            "criteria_id": None,
            "criteria_path": self._relative(criteria_path),
            "evidence_total": 0,
            "fresh_total": 0,
            "stale_total": 0,
            "missing_total": 0,
            "invalid_total": 1,
            "not_applicable_total": 0,
            "critical_total": 0,
            "critical_stale_total": 0,
            "critical_missing_total": 0,
            "critical_invalid_total": 1,
            "no_go_gates_passed": False,
            "no_go_gates": {},
            "items": [],
            "summary": {"criteria_status": criteria_result["status"], "reports_written": False, "preliminary": True},
            "safety": self._safety(reports_written=False),
            "limitations": ["Criteria must be readable before freshness can be evaluated."],
        }

    def _write_report(self, report: dict[str, Any]) -> None:
        json_path = self._resolve_inside_root(self.options.output_json)
        markdown_path = self._resolve_inside_root(self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(self._markdown(report), encoding="utf-8")

    def _markdown(self, report: dict[str, Any]) -> str:
        lines = [
            "# Evidence freshness report",
            "",
            f"- Decision: `{report['decision']}`",
            f"- Scope: `{report['scope']}`",
            f"- Repo version: `{report.get('repo_version')}`",
            f"- Critical stale: `{report['critical_stale_total']}`",
            f"- Critical missing: `{report['critical_missing_total']}`",
            f"- Critical invalid: `{report['critical_invalid_total']}`",
            "",
            "| Evidence | Status | Critical | Path | Reason |",
            "|---|---:|---:|---|---|",
        ]
        for item in report["items"]:
            lines.append(
                f"| `{item['evidence_id']}` | `{item['status']}` | `{item['critical']}` | `{item['path']}` | {item['reason']} |"
            )
        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- Local-first: true",
                "- Network used: false",
                "- External API used: false",
                "- Source mutations: false",
            ]
        )
        return "\n".join(lines) + "\n"

    def _report_paths(self) -> dict[str, str]:
        return {
            "json": self._relative(self._resolve_inside_root(self.options.output_json)),
            "markdown": self._relative(self._resolve_inside_root(self.options.output_markdown)),
        }

    def _load_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {"status": "missing", "reason": "path does not exist"}
        try:
            return {"status": "pass", "reason": "valid json", "content": json.loads(path.read_text(encoding="utf-8"))}
        except json.JSONDecodeError as exc:
            return {
                "status": "invalid",
                "reason": "invalid json",
                "metadata": {"line": exc.lineno, "column": exc.colno, "message": exc.msg},
            }

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ""

    def _lookup(self, content: Any, dotted_key: str) -> Any:
        current = content
        for part in dotted_key.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    def _extract_schema_id(self, payload: Any) -> str | None:
        if not isinstance(payload, dict):
            return None
        for key in ("schema_id", "x-devpilot-schema-id"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
        return None

    def _resolve_inside_root(self, value: str | Path) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Evidence freshness path escapes project root: {value}") from exc
        return resolved

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def _safety(self, *, reports_written: bool) -> dict[str, bool]:
        return {
            "local_first": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "source_mutations": False,
            "source_mutations_performed": False,
            "mutations_performed": reports_written,
            "reports_written": reports_written,
        }

    def _count(self, items: list[dict[str, Any]], status: str) -> int:
        return sum(1 for item in items if item["status"] == status)

    def _now(self) -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
