from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect, SecretGuard, redact_string
from devpilot_core.rag.citations import (
    DEFAULT_RAG_GROUNDEDNESS_FIXTURE,
    RagCitationExtractor,
    SourceCoverageOptions,
)
from devpilot_core.rag.indexer import _DEFAULT_INDEX_PATH

POST_H_011_C_CREATED_BY = "POST-H-011-C"
RAG_GROUNDEDNESS_EVAL_COMMAND = "rag groundedness-eval"
_NEGATION_TOKENS = {"no", "not", "sin", "without", "false", "blocked", "bloqueado", "deny", "denied", "disabled"}
_STOP_TOKENS = {"a", "an", "and", "de", "del", "el", "en", "la", "las", "los", "of", "or", "the", "y"}
_WORD_RE = re.compile(r"[a-z0-9_/.-]+", re.IGNORECASE)


@dataclass(frozen=True)
class GroundednessOptions:
    """Options for POST-H-011-C deterministic claim groundedness evaluation.

    Candidate answers are optional in POST-H-011-C because CLI/RAG-query integration
    is intentionally left for POST-H-011-D. When supplied by tests or future CLI
    wiring, forbidden claims are evaluated against the candidate answer and block
    the case deterministically.
    """

    fixture_path: str = DEFAULT_RAG_GROUNDEDNESS_FIXTURE
    index_path: str = _DEFAULT_INDEX_PATH
    use_index: bool = True
    strict: bool = True
    candidate_answers: Mapping[str, str] = field(default_factory=dict)
    detect_forbidden_in_context: bool = False
    max_evidence_chars_per_source: int = 250_000


class RagGroundednessEvaluator:
    """Evaluate required and forbidden RAG claims against local source evidence.

    The evaluator is deterministic and local-first: required claims are supported
    only by local expected sources, while forbidden claims block when they appear
    in a candidate answer. It does not call an LLM judge, embeddings, web search,
    external APIs, connectors or plugins.
    """

    def __init__(self, root: Path, *, options: GroundednessOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or GroundednessOptions()
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()
        self.extractor = RagCitationExtractor(
            self.root,
            options=SourceCoverageOptions(
                fixture_path=self.options.fixture_path,
                index_path=self.options.index_path,
                use_index=self.options.use_index,
            ),
        )

    def run(self) -> CommandResult:
        fixture, findings = self.extractor.load_fixture()
        if fixture is None:
            exit_code = _exit_code(findings)
            return CommandResult(
                command=RAG_GROUNDEDNESS_EVAL_COMMAND,
                ok=False,
                exit_code=exit_code,
                message="RAG groundedness fixture could not be loaded.",
                data={"summary": _summary_template(self.options, cases_total=0), "report": None},
                findings=findings,
            )

        index, index_findings = self.extractor.load_index()
        findings.extend(index_findings)
        case_results: list[dict[str, Any]] = []
        for case in fixture.get("cases") or []:
            source_case, source_findings = self.extractor.evaluate_case_sources(case)
            findings.extend(source_findings)
            case_result, claim_findings = self.evaluate_case_claims(case, source_case)
            case_results.append(case_result)
            findings.extend(claim_findings)

        blocking_total = len([finding for finding in findings if finding.severity == Severity.BLOCK])
        error_total = len([finding for finding in findings if finding.severity == Severity.ERROR])
        cases_total = len(case_results)
        cases_blocked = len([case for case in case_results if case["status"] == "block"])
        cases_warned = len([case for case in case_results if case["status"] == "warning"])
        claim_support_avg = round(sum(case["claim_support"] for case in case_results) / cases_total, 4) if cases_total else 0.0
        source_coverage_avg = round(sum(case["source_coverage"] for case in case_results) / cases_total, 4) if cases_total else 0.0
        unsupported_claims_total = sum(len(case["unsupported_claims"]) for case in case_results)
        forbidden_claims_detected_total = sum(len(case["forbidden_claims_detected"]) for case in case_results)
        summary = {
            **_summary_template(self.options, cases_total=cases_total),
            "suite_id": fixture.get("suite_id"),
            "cases_passed": len([case for case in case_results if case["status"] == "pass"]),
            "cases_warned": cases_warned,
            "cases_blocked": cases_blocked,
            "source_coverage_avg": source_coverage_avg,
            "claim_support_avg": claim_support_avg,
            "required_claims_total": sum(case["required_claims_total"] for case in case_results),
            "supported_claims_total": sum(case["supported_claims_total"] for case in case_results),
            "unsupported_claims_total": unsupported_claims_total,
            "forbidden_claims_detected_total": forbidden_claims_detected_total,
            "missing_sources_total": sum(len(case.get("missing_sources") or []) for case in case_results),
            "stale_sources_total": sum(len(case.get("stale_sources") or []) for case in case_results),
            "index_loaded": index is not None,
            "blocking_findings_total": blocking_total,
            "error_findings_total": error_total,
            "findings_total": len(findings),
        }
        report = _build_report(summary, case_results, findings)
        ok = error_total == 0 and blocking_total == 0 and cases_blocked == 0
        return CommandResult(
            command=RAG_GROUNDEDNESS_EVAL_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(findings),
            message="RAG groundedness claims passed." if ok else "RAG groundedness claims found blocking evidence gaps.",
            data={"summary": summary, "case_results": case_results, "report": report},
            findings=findings,
        )

    def evaluate_case_claims(self, case: dict[str, Any], source_case: dict[str, Any]) -> tuple[dict[str, Any], list[Finding]]:
        case_id = str(case.get("case_id") or source_case.get("case_id") or "unknown-case")
        required_claims = [str(claim) for claim in case.get("required_claims") or []]
        forbidden_claims = [str(claim) for claim in case.get("forbidden_claims") or []]
        threshold = float(case.get("minimum_claim_support") or 1.0)
        findings: list[Finding] = []
        evidence_text_by_source = self._evidence_text_by_source(source_case)
        evidence_corpus = "\n".join(evidence_text_by_source.values())
        source_paths = list(evidence_text_by_source)

        supported_claims: list[str] = []
        unsupported_claims: list[str] = []
        claim_evidence: list[dict[str, Any]] = []
        for claim in required_claims:
            supporting_sources = [path for path, text in evidence_text_by_source.items() if _claim_supported_by_text(claim, text)]
            if not supporting_sources and _claim_supported_by_text(claim, "\n".join(source_paths)):
                supporting_sources = [path for path in source_paths if _claim_supported_by_text(claim, path)] or source_paths[:1]
            if supporting_sources:
                supported_claims.append(claim)
                claim_evidence.append({"claim": claim, "supported": True, "sources": supporting_sources})
            else:
                unsupported_claims.append(claim)
                claim_evidence.append({"claim": claim, "supported": False, "sources": []})
                findings.append(
                    Finding(
                        "RAG_REQUIRED_CLAIM_UNSUPPORTED",
                        "Required claim is not supported by local expected sources.",
                        Severity.BLOCK if self.options.strict else Severity.WARNING,
                        metadata={"case_id": case_id, "claim": claim},
                    )
                )

        required_total = len(required_claims)
        claim_support = round((len(supported_claims) / required_total) if required_total else 0.0, 4)
        if claim_support < threshold:
            findings.append(
                Finding(
                    "RAG_CLAIM_SUPPORT_BELOW_THRESHOLD",
                    "Required claim support is below the case threshold.",
                    Severity.BLOCK if self.options.strict else Severity.WARNING,
                    metadata={"case_id": case_id, "claim_support": claim_support, "minimum_claim_support": threshold},
                )
            )

        candidate_answer = self.options.candidate_answers.get(case_id, "")
        redacted_candidate = str(self.secret_guard.redact(candidate_answer).value) if candidate_answer else ""
        forbidden_scan_text = redacted_candidate
        if self.options.detect_forbidden_in_context:
            forbidden_scan_text = "\n".join([forbidden_scan_text, evidence_corpus])
        forbidden_detected = [claim for claim in forbidden_claims if _forbidden_claim_detected(claim, forbidden_scan_text)]
        for claim in forbidden_detected:
            findings.append(
                Finding(
                    "RAG_FORBIDDEN_CLAIM_DETECTED",
                    "Forbidden claim was detected in the candidate answer/context and blocks groundedness.",
                    Severity.BLOCK,
                    metadata={"case_id": case_id, "claim": claim, "candidate_answer_evaluated": bool(candidate_answer)},
                )
            )

        status = "pass"
        source_blocked = source_case.get("status") == "block"
        if source_blocked or forbidden_detected or (self.options.strict and claim_support < threshold):
            status = "block"
        elif claim_support < threshold:
            status = "warning"

        if source_blocked and source_case.get("source_coverage", 0.0) <= 0:
            findings.append(
                Finding(
                    "RAG_CLAIMS_BLOCKED_WITHOUT_SOURCES",
                    "A RAG answer cannot pass groundedness without local source evidence.",
                    Severity.BLOCK,
                    metadata={"case_id": case_id},
                )
            )

        result = {
            "case_id": case_id,
            "status": status,
            "source_coverage": float(source_case.get("source_coverage") or 0.0),
            "claim_support": claim_support,
            "minimum_claim_support": threshold,
            "expected_sources_total": int(source_case.get("expected_sources_total") or 0),
            "matched_sources_total": int(source_case.get("matched_sources_total") or 0),
            "required_claims_total": required_total,
            "supported_claims_total": len(supported_claims),
            "unsupported_claims": unsupported_claims,
            "forbidden_claims_detected": forbidden_detected,
            "forbidden_claims_total": len(forbidden_claims),
            "supported_claims": supported_claims,
            "claim_evidence": claim_evidence,
            "candidate_answer_evaluated": bool(candidate_answer),
            "findings": [finding.to_dict() for finding in findings],
            "matched_sources": source_case.get("matched_sources") or [],
            "missing_sources": source_case.get("missing_sources") or [],
            "stale_sources": source_case.get("stale_sources") or [],
            "citation_refs": source_case.get("citation_refs") or [],
        }
        return result, findings

    def _evidence_text_by_source(self, source_case: dict[str, Any]) -> dict[str, str]:
        evidence: dict[str, str] = {}
        for source in source_case.get("matched_sources") or []:
            path = str(source.get("path") or "").strip()
            if not path:
                continue
            source_text = _source_metadata_text(source)
            source_path = self.root / path
            decision = self.path_guard.evaluate(source_path, action="read")
            if decision.effect not in {PolicyEffect.BLOCK, PolicyEffect.DENY} and source_path.exists():
                try:
                    raw = source_path.read_text(encoding="utf-8", errors="replace")
                    raw = raw[: self.options.max_evidence_chars_per_source]
                    source_text = "\n".join([source_text, redact_string(raw)])
                except OSError:
                    pass
            evidence[path] = source_text
        return evidence


def _source_metadata_text(source: dict[str, Any]) -> str:
    fragments: list[str] = []
    for key in ("path", "doc_id", "status", "updated", "title"):
        value = source.get(key)
        if value is not None:
            fragments.append(str(value))
    for heading in source.get("headings") or []:
        fragments.append(str(heading.get("title") or ""))
    for snippet in source.get("snippets") or []:
        fragments.append(str(snippet.get("fragment") or ""))
        fragments.append(str(snippet.get("ref") or ""))
    return "\n".join(fragments)


def _summary_template(options: GroundednessOptions, *, cases_total: int) -> dict[str, Any]:
    return {
        "created_by": POST_H_011_C_CREATED_BY,
        "status": "implemented-initial",
        "preliminary": True,
        "fixture_path": options.fixture_path,
        "cases_total": cases_total,
        "strict": options.strict,
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
        "raw_payloads_read": False,
        "local_first": True,
        "dry_run": True,
    }


def _build_report(summary: dict[str, Any], case_results: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
    status = "pass"
    if summary.get("cases_blocked", 0) or summary.get("blocking_findings_total", 0) or summary.get("error_findings_total", 0):
        status = "block"
    elif summary.get("cases_warned", 0):
        status = "warning"
    return {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-RAG-GROUNDEDNESS-REPORT-V1",
        "report_id": "devpilot-rag-groundedness-claims-report",
        "suite_id": str(summary.get("suite_id") or "unknown-suite"),
        "created_by": POST_H_011_C_CREATED_BY,
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": {
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
        },
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
            "POST-H-011-C validates required/forbidden claims deterministically against local evidence.",
            "CLI wiring and persistent outputs/evals reports remain scoped to POST-H-011-D.",
            "RAG remains non-authoritative: canonical documentation sources remain the source of truth.",
        ],
    }


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
    }


def _report_finding(finding: Finding) -> dict[str, Any]:
    data = finding.to_dict()
    if data.get("severity") == "fail":
        data["severity"] = "block"
    return data


def _claim_supported_by_text(claim: str, text: str) -> bool:
    normalized_claim = _normalize_text(claim)
    normalized_text = _normalize_text(text)
    if not normalized_claim or not normalized_text:
        return False
    if normalized_claim in normalized_text:
        return True
    claim_tokens = _claim_tokens(normalized_claim)
    if not claim_tokens:
        return False
    text_tokens = set(_WORD_RE.findall(normalized_text))
    text_joined = " ".join(sorted(text_tokens))
    return all(_token_supported(token, text_tokens, text_joined) for token in claim_tokens)


def _forbidden_claim_detected(claim: str, text: str) -> bool:
    normalized_claim = _normalize_text(claim)
    normalized_text = _normalize_text(text)
    if not normalized_claim or not normalized_text:
        return False
    if normalized_claim in normalized_text:
        return True
    claim_tokens = _claim_tokens(normalized_claim)
    if len(claim_tokens) < 2:
        return False
    text_tokens = set(_WORD_RE.findall(normalized_text))
    text_joined = " ".join(sorted(text_tokens))
    return all(_token_supported(token, text_tokens, text_joined) for token in claim_tokens)


def _claim_tokens(normalized_claim: str) -> list[str]:
    return [token for token in _WORD_RE.findall(normalized_claim) if token not in _STOP_TOKENS]


def _token_supported(token: str, text_tokens: set[str], text_joined: str) -> bool:
    if token in _NEGATION_TOKENS:
        return bool(text_tokens.intersection(_NEGATION_TOKENS))
    variants = _token_variants(token)
    if text_tokens.intersection(variants):
        return True
    return any(variant and variant in text_joined for variant in variants if len(variant) >= 4)


def _token_variants(token: str) -> set[str]:
    variants = {token}
    if token.endswith("es") and len(token) > 5:
        variants.add(token[:-2])
    if token.endswith("s") and len(token) > 4:
        variants.add(token[:-1])
    if token.endswith("ing") and len(token) > 6:
        variants.add(token[:-3])
    if token.endswith("ado") and len(token) > 5:
        variants.add(token[:-3])
    if token.endswith("ados") and len(token) > 6:
        variants.add(token[:-4])
    if token in {"bloqueado", "bloqueados", "bloqueada", "blocked"}:
        variants.update({"bloque", "blocked", "block", "deny", "denied"})
    if token in {"versionables", "versionable"}:
        variants.update({"versionable", "versionables"})
    if token == "deploy":
        variants.update({"deploy", "deploys", "deployment"})
    if token == "publish":
        variants.update({"publish", "publishes", "publication"})
    return {variant for variant in variants if variant}


def _normalize_text(text: str) -> str:
    lowered = unicodedata.normalize("NFKD", str(text).lower())
    without_marks = "".join(ch for ch in lowered if not unicodedata.combining(ch))
    normalized = re.sub(r"[^a-z0-9_/.-]+", " ", without_marks)
    return re.sub(r"\s+", " ", normalized).strip()


def _exit_code(findings: list[Finding]) -> ExitCode:
    if any(finding.severity == Severity.ERROR for finding in findings):
        return ExitCode.ERROR
    if any(finding.severity == Severity.BLOCK for finding in findings):
        return ExitCode.BLOCK
    if any(finding.severity == Severity.FAIL for finding in findings):
        return ExitCode.FAIL
    return ExitCode.PASS


__all__ = [
    "GroundednessOptions",
    "POST_H_011_C_CREATED_BY",
    "RAG_GROUNDEDNESS_EVAL_COMMAND",
    "RagGroundednessEvaluator",
]
