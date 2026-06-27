from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect, redact_string
from devpilot_core.rag.citations import DEFAULT_RAG_GROUNDEDNESS_FIXTURE
from devpilot_core.rag.groundedness import (
    GroundednessOptions,
    RagGroundednessEvaluator,
)
from devpilot_core.rag.indexer import _DEFAULT_INDEX_PATH
from devpilot_core.rag.retriever import LocalRagRetriever, RagQueryOptions

POST_H_011_D_CREATED_BY = "POST-H-011-D"
POST_H_011_E_CREATED_BY = "POST-H-011-E"
RAG_GROUNDEDNESS_EVAL_RUNNER_COMMAND = "rag groundedness-eval"
RAG_GROUNDEDNESS_READY_GATE_COMMAND = "quality rag-groundedness-ready"
DEFAULT_RAG_GROUNDEDNESS_REPORT_JSON = "outputs/evals/rag_groundedness_report.json"
DEFAULT_RAG_GROUNDEDNESS_REPORT_MD = "outputs/evals/rag_groundedness_report.md"


@dataclass(frozen=True)
class RagGroundednessEvalRunOptions:
    """Options for POST-H-011-D RAG groundedness eval runner integration.

    The runner connects three existing local pieces without enabling any remote
    capability: lexical ``rag query``, citation/source coverage and deterministic
    claim groundedness. ``write_report`` is deliberately not part of this value
    object because report writing is a command execution concern, not an
    evaluation criterion.
    """

    suite_path: str = DEFAULT_RAG_GROUNDEDNESS_FIXTURE
    index_path: str = _DEFAULT_INDEX_PATH
    case_id: str | None = None
    strict: bool = True
    top_k: int = 5
    run_rag_query: bool = True
    output_json: str = DEFAULT_RAG_GROUNDEDNESS_REPORT_JSON
    output_markdown: str = DEFAULT_RAG_GROUNDEDNESS_REPORT_MD


class RagGroundednessEvalRunner:
    """Run the POST-H-011 groundedness suite through local RAG integration.

    POST-H-011-D keeps the execution path local/offline and deterministic. It
    uses ``LocalRagRetriever`` only to prove that each fixture question can be
    backed by local retrieved chunks, then delegates source/claim scoring to the
    POST-H-011-B/C evaluators. No provider, external API, LLM judge, embedding
    service, connector or plugin is required.
    """

    def __init__(self, root: Path, *, options: RagGroundednessEvalRunOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or RagGroundednessEvalRunOptions()
        self.path_guard = PathGuard(self.root)

    def run(self, *, write_report: bool = False) -> CommandResult:
        fixture, fixture_findings = self._load_fixture_cases()
        if fixture is None:
            return CommandResult(
                command=RAG_GROUNDEDNESS_EVAL_RUNNER_COMMAND,
                ok=False,
                exit_code=_exit_code(fixture_findings),
                message="RAG groundedness suite could not be loaded.",
                data={"summary": self._summary_template(cases_total=0), "case_results": [], "report": None},
                findings=fixture_findings,
            )

        cases = list(fixture.get("cases") or [])
        if self.options.case_id:
            cases = [case for case in cases if str(case.get("case_id")) == self.options.case_id]
            if not cases:
                finding = Finding(
                    "RAG_GROUNDEDNESS_CASE_NOT_FOUND",
                    "Requested RAG groundedness case was not found in the selected suite.",
                    Severity.ERROR,
                    metadata={"case_id": self.options.case_id, "suite_path": self.options.suite_path},
                )
                return CommandResult(
                    command=RAG_GROUNDEDNESS_EVAL_RUNNER_COMMAND,
                    ok=False,
                    exit_code=ExitCode.ERROR,
                    message="RAG groundedness case was not found.",
                    data={"summary": self._summary_template(cases_total=0), "case_results": [], "report": None},
                    findings=[finding],
                )

        query_results, candidate_answers, query_findings = self._run_rag_queries(cases)
        evaluator = RagGroundednessEvaluator(
            self.root,
            options=GroundednessOptions(
                fixture_path=self.options.suite_path,
                index_path=self.options.index_path,
                use_index=True,
                strict=self.options.strict,
                candidate_answers=candidate_answers,
                case_id=self.options.case_id,
            ),
        )
        result = evaluator.run()
        findings = [*fixture_findings, *query_findings, *result.findings]
        data = dict(result.data or {})
        case_results = [dict(case) for case in data.get("case_results") or []]
        query_by_case = {item["case_id"]: item for item in query_results}
        for case in case_results:
            query = query_by_case.get(case.get("case_id"), {})
            case.update(
                {
                    "query_executed": bool(query.get("query_executed", False)),
                    "query_grounded": bool(query.get("query_grounded", False)),
                    "query_sources_total": int(query.get("query_sources_total") or 0),
                    "query_source_refs": list(query.get("query_source_refs") or []),
                }
            )

        blocking_total = len([finding for finding in findings if finding.severity == Severity.BLOCK])
        error_total = len([finding for finding in findings if finding.severity == Severity.ERROR])
        query_failures_total = len([item for item in query_results if item.get("query_executed") and not item.get("query_grounded")])
        queries_with_sources_total = len([item for item in query_results if item.get("query_grounded")])
        summary = {
            **self._summary_template(cases_total=len(case_results)),
            **{key: value for key, value in dict(data.get("summary") or {}).items() if key not in {"created_by", "status"}},
            "created_by": POST_H_011_D_CREATED_BY,
            "suite_id": fixture.get("suite_id"),
            "cases_total": len(case_results),
            "queries_total": len(query_results),
            "queries_with_sources_total": queries_with_sources_total,
            "query_failures_total": query_failures_total,
            "rag_query_used": self.options.run_rag_query,
            "reports_written": False,
            "blocking_findings_total": blocking_total,
            "error_findings_total": error_total,
            "findings_total": len(findings),
        }
        ok = bool(result.ok) and blocking_total == 0 and error_total == 0 and query_failures_total == 0
        if query_failures_total:
            findings.insert(
                0,
                Finding(
                    "RAG_GROUNDEDNESS_QUERY_COVERAGE_BLOCK",
                    "One or more groundedness cases could not retrieve local RAG sources for their question.",
                    Severity.BLOCK,
                    metadata={"query_failures_total": query_failures_total},
                ),
            )
            summary["blocking_findings_total"] = summary["blocking_findings_total"] + 1
            summary["findings_total"] = len(findings)
            ok = False
        else:
            findings.insert(
                0,
                Finding(
                    "RAG_GROUNDEDNESS_EVAL_RUNNER_PASS",
                    "RAG groundedness eval runner completed offline with local retrieved sources and deterministic claim scoring.",
                    Severity.INFO,
                    metadata={"cases_total": len(case_results), "queries_total": len(query_results)},
                )
            )
            summary["findings_total"] = len(findings)

        report = _build_eval_runner_report(summary, case_results, findings)
        data = {"summary": summary, "case_results": case_results, "query_results": query_results, "report": report}
        message = "RAG groundedness eval runner passed." if ok else "RAG groundedness eval runner found blocking evidence gaps."
        command_result = CommandResult(
            command=RAG_GROUNDEDNESS_EVAL_RUNNER_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(findings),
            message=message,
            data=data,
            findings=findings,
        )
        if write_report:
            return self.write_reports(command_result)
        return command_result

    def write_reports(self, result: CommandResult) -> CommandResult:
        json_path = self._resolve_output_path(self.options.output_json)
        markdown_path = self._resolve_output_path(self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        report = dict(data.get("report") or {})
        summary["reports_written"] = True
        data["summary"] = summary
        if report:
            report["summary"] = _report_summary_from_command_summary(summary)
        json_path.write_text(json.dumps(report or data, indent=2, ensure_ascii=False), encoding="utf-8")
        markdown_path.write_text(_render_groundedness_markdown(report or data, summary=summary), encoding="utf-8")
        data["report"] = report
        data["reports"] = {"json": _rel(json_path, self.root), "markdown": _rel(markdown_path, self.root)}
        return CommandResult(result.command, result.ok, result.exit_code, result.message, data=data, findings=result.findings)

    def _run_rag_queries(self, cases: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str], list[Finding]]:
        if not self.options.run_rag_query:
            return [], {}, []
        results: list[dict[str, Any]] = []
        candidate_answers: dict[str, str] = {}
        findings: list[Finding] = []
        for case in cases:
            case_id = str(case.get("case_id") or "unknown-case")
            question = str(case.get("question") or "").strip()
            if not question:
                findings.append(Finding("RAG_GROUNDEDNESS_QUESTION_EMPTY", "Groundedness case has no question for RAG query integration.", Severity.BLOCK, metadata={"case_id": case_id}))
                results.append({"case_id": case_id, "query_executed": False, "query_grounded": False, "query_sources_total": 0, "query_source_refs": []})
                continue
            query_result = LocalRagRetriever(
                self.root,
                options=RagQueryOptions(query=question, index_path=self.options.index_path, top_k=self.options.top_k),
            ).query()
            sources = list(((query_result.data or {}).get("sources") or []))
            refs = [str(source.get("ref")) for source in sources if source.get("ref")]
            answer = (query_result.data or {}).get("answer") or {}
            answer_text = str(answer.get("text") or "")
            if answer_text:
                candidate_answers[case_id] = answer_text
            query_grounded = bool(query_result.ok and sources)
            results.append(
                {
                    "case_id": case_id,
                    "query_executed": True,
                    "query_grounded": query_grounded,
                    "query_sources_total": len(sources),
                    "query_source_refs": refs,
                    "query_answer_preview": redact_string(answer_text[:240]) if answer_text else "",
                    "exit_code": int(query_result.exit_code),
                }
            )
            if not query_grounded:
                findings.append(
                    Finding(
                        "RAG_GROUNDEDNESS_QUERY_NO_SOURCES",
                        "RAG query did not return local grounded sources for a groundedness case.",
                        Severity.BLOCK,
                        metadata={"case_id": case_id, "query_exit_code": int(query_result.exit_code)},
                    )
                )
        return results, candidate_answers, findings

    def _load_fixture_cases(self) -> tuple[dict[str, Any] | None, list[Finding]]:
        path = self._resolve_input_path(self.options.suite_path)
        decision = self.path_guard.evaluate(path, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return None, [Finding("RAG_GROUNDEDNESS_SUITE_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata)]
        if not path.exists():
            return None, [Finding("RAG_GROUNDEDNESS_SUITE_NOT_FOUND", "RAG groundedness suite fixture was not found.", Severity.BLOCK, path=_rel(path, self.root))]
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return None, [Finding("RAG_GROUNDEDNESS_SUITE_LOAD_ERROR", f"RAG groundedness suite fixture could not be loaded: {exc}", Severity.ERROR, path=_rel(path, self.root))]
        if not isinstance(payload.get("cases"), list):
            return None, [Finding("RAG_GROUNDEDNESS_SUITE_CASES_INVALID", "RAG groundedness suite must declare a cases array.", Severity.ERROR, path=_rel(path, self.root))]
        return payload, []

    def _summary_template(self, *, cases_total: int) -> dict[str, Any]:
        return {
            "created_by": POST_H_011_D_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "suite_path": self.options.suite_path,
            "index_path": self.options.index_path,
            "case_id": self.options.case_id,
            "cases_total": cases_total,
            "strict": self.options.strict,
            "rag_query_used": self.options.run_rag_query,
            "queries_total": 0,
            "queries_with_sources_total": 0,
            "query_failures_total": 0,
            "source_coverage_avg": 0.0,
            "claim_support_avg": 0.0,
            "network_used": False,
            "external_api_used": False,
            "web_search_used": False,
            "llm_judge_used": False,
            "embeddings_used": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "outputs_as_sources_allowed": False,
            "local_first": True,
            "dry_run": True,
        }

    def _resolve_input_path(self, value: str) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()

    def _resolve_output_path(self, value: str) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        try:
            rel = candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("RAG groundedness reports must be written inside the DevPilot project root.") from exc
        if not str(rel).replace("\\", "/").startswith("outputs/evals/"):
            raise ValueError("RAG groundedness reports must be written under outputs/evals/.")
        return candidate



@dataclass(frozen=True)
class RagGroundednessReadyGateOptions:
    """Options for POST-H-011-E quality-gate integration.

    The gate intentionally does not write runtime reports. It verifies that the
    POST-H-011 suite can run offline, that local RAG query evidence is present,
    that deterministic claim scoring reaches thresholds, and that at least one
    negative/forbidden-claim case blocks when exercised with a synthetic bad
    candidate answer.
    """

    suite_path: str = DEFAULT_RAG_GROUNDEDNESS_FIXTURE
    index_path: str = _DEFAULT_INDEX_PATH
    min_cases: int = 10
    min_source_coverage: float = 1.0
    min_claim_support: float = 0.8
    top_k: int = 5


class RagGroundednessReadyGate:
    """Quality subgate for POST-H-011 RAG groundedness readiness.

    The gate is local-first, read-only and dry-run. It is designed for
    ``quality-gate run --profile hardening`` and ``industrial`` profiles, and it
    does not create ``outputs/evals`` artifacts. Report writing remains an
    explicit operator action through ``rag groundedness-eval --write-report``.
    """

    def __init__(self, root: Path, *, options: RagGroundednessReadyGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or RagGroundednessReadyGateOptions()

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        runner = RagGroundednessEvalRunner(
            self.root,
            options=RagGroundednessEvalRunOptions(
                suite_path=self.options.suite_path,
                index_path=self.options.index_path,
                strict=True,
                top_k=self.options.top_k,
                run_rag_query=True,
            ),
        )
        result = runner.run(write_report=False)
        findings.extend(result.findings)
        summary = dict((result.data or {}).get("summary") or {})
        case_results = list((result.data or {}).get("case_results") or [])

        negative_ok, negative_summary, negative_findings = self._exercise_negative_case()
        findings.extend(negative_findings)

        cases_total = int(summary.get("cases_total") or 0)
        source_coverage_avg = float(summary.get("source_coverage_avg") or 0.0)
        claim_support_avg = float(summary.get("claim_support_avg") or 0.0)
        reports_written = bool(summary.get("reports_written"))
        cases_with_forbidden = len([case for case in case_results if int(case.get("forbidden_claims_total") or 0) > 0])

        if cases_total < self.options.min_cases:
            findings.append(Finding("RAG_GROUNDEDNESS_READY_MIN_CASES_BLOCK", "RAG groundedness suite has fewer cases than the readiness threshold.", Severity.BLOCK, metadata={"cases_total": cases_total, "min_cases": self.options.min_cases}))
        if source_coverage_avg < self.options.min_source_coverage:
            findings.append(Finding("RAG_GROUNDEDNESS_READY_SOURCE_COVERAGE_BLOCK", "RAG groundedness source coverage is below the readiness threshold.", Severity.BLOCK, metadata={"source_coverage_avg": source_coverage_avg, "min_source_coverage": self.options.min_source_coverage}))
        if claim_support_avg < self.options.min_claim_support:
            findings.append(Finding("RAG_GROUNDEDNESS_READY_CLAIM_SUPPORT_BLOCK", "RAG groundedness claim support is below the readiness threshold.", Severity.BLOCK, metadata={"claim_support_avg": claim_support_avg, "min_claim_support": self.options.min_claim_support}))
        if cases_with_forbidden <= 0:
            findings.append(Finding("RAG_GROUNDEDNESS_READY_NEGATIVE_CASES_MISSING", "RAG groundedness suite must include forbidden_claims negative cases.", Severity.BLOCK))
        if not negative_ok:
            findings.append(Finding("RAG_GROUNDEDNESS_READY_NEGATIVE_CASE_NOT_BLOCKED", "Synthetic forbidden-claim candidate did not block as expected.", Severity.BLOCK, metadata=negative_summary))
        if reports_written:
            findings.append(Finding("RAG_GROUNDEDNESS_READY_REPORT_WRITTEN", "Quality subgate must not write outputs/evals reports.", Severity.BLOCK))
        if summary.get("network_used") or summary.get("external_api_used") or summary.get("web_search_used") or summary.get("llm_judge_used"):
            findings.append(Finding("RAG_GROUNDEDNESS_READY_REMOTE_DEPENDENCY_BLOCK", "RAG groundedness readiness must stay offline and must not use external providers.", Severity.BLOCK))
        if summary.get("outputs_as_sources_allowed"):
            findings.append(Finding("RAG_GROUNDEDNESS_READY_OUTPUTS_AS_SOURCES_BLOCK", "outputs/evals must not be accepted as canonical groundedness sources.", Severity.BLOCK))

        blocking = [item for item in findings if item.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        gate_summary = {
            "created_by": POST_H_011_E_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "quality_gate_ready": not blocking and bool(result.ok),
            "quality_gate_subgate": "rag-groundedness-ready",
            "suite_path": self.options.suite_path,
            "index_path": self.options.index_path,
            "cases_total": cases_total,
            "min_cases": self.options.min_cases,
            "source_coverage_avg": source_coverage_avg,
            "min_source_coverage": self.options.min_source_coverage,
            "claim_support_avg": claim_support_avg,
            "min_claim_support": self.options.min_claim_support,
            "cases_passed": int(summary.get("cases_passed") or 0),
            "cases_blocked": int(summary.get("cases_blocked") or 0),
            "queries_total": int(summary.get("queries_total") or 0),
            "queries_with_sources_total": int(summary.get("queries_with_sources_total") or 0),
            "query_failures_total": int(summary.get("query_failures_total") or 0),
            "cases_with_forbidden_claims_total": cases_with_forbidden,
            "negative_case_block_checked": True,
            "negative_case_blocked": negative_ok,
            "negative_case_id": negative_summary.get("case_id"),
            "forbidden_claim_tested": negative_summary.get("forbidden_claim"),
            "reports_written": reports_written,
            "read_only": True,
            "dry_run": True,
            "local_first": True,
            "network_used": False,
            "external_api_used": False,
            "web_search_used": False,
            "llm_judge_used": False,
            "embeddings_used": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "outputs_as_sources_allowed": False,
            "blocking_findings_total": len(blocking),
            "findings_total": len(findings),
        }
        ok = bool(result.ok) and not blocking
        gate_findings = []
        if ok:
            gate_findings.append(Finding("RAG_GROUNDEDNESS_READY_PASS", "RAG groundedness readiness gate passed offline with local sources, deterministic claims and negative-case blocking.", Severity.INFO, metadata={"cases_total": cases_total, "source_coverage_avg": source_coverage_avg, "claim_support_avg": claim_support_avg}))
        else:
            gate_findings = findings
        return CommandResult(
            command=RAG_GROUNDEDNESS_READY_GATE_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(findings),
            message="RAG groundedness readiness gate passed." if ok else "RAG groundedness readiness gate failed or blocked.",
            data={"summary": gate_summary, "runner_summary": summary, "negative_case": negative_summary},
            findings=gate_findings,
        )

    def _exercise_negative_case(self) -> tuple[bool, dict[str, Any], list[Finding]]:
        suite_path = self.root / self.options.suite_path
        try:
            suite = json.loads(suite_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive; load failures are covered by runner too
            return False, {"error": str(exc), "case_id": None, "forbidden_claim": None}, [Finding("RAG_GROUNDEDNESS_READY_NEGATIVE_LOAD_ERROR", "Could not load groundedness fixture for negative-case readiness check.", Severity.ERROR, path=self.options.suite_path, metadata={"error": str(exc)})]
        cases = suite.get("cases") if isinstance(suite, dict) else None
        if not isinstance(cases, list):
            return False, {"case_id": None, "forbidden_claim": None}, [Finding("RAG_GROUNDEDNESS_READY_NEGATIVE_CASES_INVALID", "Groundedness fixture has no cases array for negative-case readiness check.", Severity.ERROR, path=self.options.suite_path)]
        candidate_case = next((case for case in cases if case.get("forbidden_claims")), None)
        if not candidate_case:
            return False, {"case_id": None, "forbidden_claim": None}, []
        case_id = str(candidate_case.get("case_id"))
        forbidden_claim = str((candidate_case.get("forbidden_claims") or [""])[0])
        evaluator = RagGroundednessEvaluator(
            self.root,
            options=GroundednessOptions(
                fixture_path=self.options.suite_path,
                index_path=self.options.index_path,
                use_index=True,
                strict=True,
                case_id=case_id,
                candidate_answers={case_id: f"This unsafe candidate asserts: {forbidden_claim}."},
            ),
        )
        result = evaluator.run()
        summary = dict((result.data or {}).get("summary") or {})
        case_results = list((result.data or {}).get("case_results") or [])
        blocked = (not result.ok) and bool(case_results) and case_results[0].get("status") == "block" and int(summary.get("forbidden_claims_detected_total") or 0) > 0
        return blocked, {"case_id": case_id, "forbidden_claim": forbidden_claim, "result_ok": result.ok, "case_status": case_results[0].get("status") if case_results else None, "forbidden_claims_detected_total": int(summary.get("forbidden_claims_detected_total") or 0)}, []

def _build_eval_runner_report(summary: dict[str, Any], case_results: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
    status = "pass"
    if summary.get("cases_blocked", 0) or summary.get("blocking_findings_total", 0) or summary.get("error_findings_total", 0):
        status = "block"
    elif summary.get("cases_warned", 0):
        status = "warning"
    return {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-RAG-GROUNDEDNESS-REPORT-V1",
        "report_id": "devpilot-rag-groundedness-eval-runner-report",
        "suite_id": str(summary.get("suite_id") or "unknown-suite"),
        "created_by": POST_H_011_D_CREATED_BY,
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": _report_summary_from_command_summary(summary),
        "case_results": [_report_case_result(case) for case in case_results],
        "findings": [_report_finding(finding) for finding in findings],
        "safety": {
            "local_first": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "web_search_used": False,
            "llm_judge_used": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
        },
        "notes": [
            "POST-H-011-D integrates local rag query, deterministic source coverage and deterministic claim groundedness.",
            "The report is generated under outputs/evals when --write-report is explicit and must not be versioned as source of truth.",
            "RAG remains non-authoritative: canonical documentation sources remain the source of truth.",
        ],
    }


def _report_summary_from_command_summary(summary: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "cases_total": int(summary.get("cases_total") or 0),
        "cases_passed": int(summary.get("cases_passed") or 0),
        "cases_warned": int(summary.get("cases_warned") or 0),
        "cases_blocked": int(summary.get("cases_blocked") or 0),
        "source_coverage_avg": float(summary.get("source_coverage_avg") or 0.0),
        "claim_support_avg": float(summary.get("claim_support_avg") or 0.0),
        "unsupported_claims_total": int(summary.get("unsupported_claims_total") or 0),
        "missing_sources_total": int(summary.get("missing_sources_total") or 0),
        "stale_sources_total": int(summary.get("stale_sources_total") or 0),
        "forbidden_claims_detected_total": int(summary.get("forbidden_claims_detected_total") or 0),
        "network_used": False,
        "external_api_used": False,
        "web_search_used": False,
        "llm_judge_used": False,
        "rag_query_used": bool(summary.get("rag_query_used")),
        "queries_total": int(summary.get("queries_total") or 0),
        "queries_with_sources_total": int(summary.get("queries_with_sources_total") or 0),
        "query_failures_total": int(summary.get("query_failures_total") or 0),
        "reports_written": bool(summary.get("reports_written", False)),
    }
    return payload


def _report_case_result(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "status": case["status"],
        "source_coverage": case["source_coverage"],
        "claim_support": case["claim_support"],
        "expected_sources_total": case["expected_sources_total"],
        "matched_sources_total": case["matched_sources_total"],
        "required_claims_total": case["required_claims_total"],
        "supported_claims_total": case["supported_claims_total"],
        "unsupported_claims": case.get("unsupported_claims") or [],
        "forbidden_claims_detected": case.get("forbidden_claims_detected") or [],
        "findings": case.get("findings") or [],
        "matched_sources": case.get("matched_sources") or [],
        "missing_sources": case.get("missing_sources") or [],
        "stale_sources": case.get("stale_sources") or [],
        "citation_refs": case.get("citation_refs") or [],
        "supported_claims": case.get("supported_claims") or [],
        "claim_evidence": case.get("claim_evidence") or [],
        "minimum_claim_support": case.get("minimum_claim_support"),
        "forbidden_claims_total": case.get("forbidden_claims_total", 0),
        "candidate_answer_evaluated": bool(case.get("candidate_answer_evaluated")),
        "query_executed": bool(case.get("query_executed")),
        "query_grounded": bool(case.get("query_grounded")),
        "query_sources_total": int(case.get("query_sources_total") or 0),
        "query_source_refs": list(case.get("query_source_refs") or []),
    }


def _report_finding(finding: Finding) -> dict[str, Any]:
    data = finding.to_dict()
    if data.get("severity") == "fail":
        data["severity"] = "block"
    return data


def _render_groundedness_markdown(report: dict[str, Any], *, summary: dict[str, Any]) -> str:
    lines = [
        "# DevPilot RAG Groundedness Eval Report",
        "",
        f"- Report ID: `{report.get('report_id', 'unknown')}`",
        f"- Created by: `{report.get('created_by', POST_H_011_D_CREATED_BY)}`",
        f"- Suite: `{report.get('suite_id', summary.get('suite_id', 'unknown'))}`",
        f"- Status: `{report.get('status', 'unknown')}`",
        "- Local-first: `true`",
        "- Network used: `false`",
        "- External API used: `false`",
        "",
        "## Summary",
        "",
    ]
    for key, value in sorted((report.get("summary") or summary).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Cases", ""])
    for case in report.get("case_results", []):
        lines.append(f"### {case.get('case_id')}")
        lines.append("")
        lines.append(f"- Status: `{case.get('status')}`")
        lines.append(f"- Source coverage: `{case.get('source_coverage')}`")
        lines.append(f"- Claim support: `{case.get('claim_support')}`")
        lines.append(f"- Query grounded: `{str(case.get('query_grounded', False)).lower()}`")
        if case.get("unsupported_claims"):
            lines.append(f"- Unsupported claims: `{', '.join(case['unsupported_claims'])}`")
        if case.get("forbidden_claims_detected"):
            lines.append(f"- Forbidden claims detected: `{', '.join(case['forbidden_claims_detected'])}`")
        lines.append("")
    lines.extend(["## Findings", ""])
    findings = report.get("findings", [])
    if not findings:
        lines.append("No findings.")
    for finding in findings:
        lines.append(f"- **{str(finding.get('severity', 'info')).upper()}** `{finding.get('id')}`: {finding.get('message')}")
    lines.append("")
    return "\n".join(lines)


def _exit_code(findings: list[Finding]) -> ExitCode:
    if any(finding.severity == Severity.ERROR for finding in findings):
        return ExitCode.ERROR
    if any(finding.severity == Severity.BLOCK for finding in findings):
        return ExitCode.BLOCK
    if any(finding.severity == Severity.FAIL for finding in findings):
        return ExitCode.FAIL
    return ExitCode.PASS


def _rel(path: Path, root: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


__all__ = [
    "DEFAULT_RAG_GROUNDEDNESS_REPORT_JSON",
    "DEFAULT_RAG_GROUNDEDNESS_REPORT_MD",
    "POST_H_011_D_CREATED_BY",
    "RAG_GROUNDEDNESS_EVAL_RUNNER_COMMAND",
    "RagGroundednessEvalRunOptions",
    "RagGroundednessEvalRunner",
]
