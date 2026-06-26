from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect, SecretGuard, redact_string
from devpilot_core.rag.indexer import _DEFAULT_INDEX_PATH

POST_H_011_B_CREATED_BY = "POST-H-011-B"
RAG_SOURCE_COVERAGE_COMMAND = "rag source-coverage"
DEFAULT_RAG_GROUNDEDNESS_FIXTURE = "evals/fixtures/rag_groundedness_post_h_cases.json"
STALE_STATUSES = {"deprecated", "archived", "obsolete", "superseded", "retired"}
FORBIDDEN_SOURCE_PREFIXES = ("outputs/",)
_ALLOWED_SOURCE_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml"}
_FRONTMATTER_RE = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*\n", re.DOTALL)
_HEADING_RE = re.compile(r"^(?P<level>#{1,6})\s+(?P<title>.+?)\s*$")


@dataclass(frozen=True)
class SourceCoverageOptions:
    """Options for POST-H-011-B local source coverage evaluation."""

    fixture_path: str = DEFAULT_RAG_GROUNDEDNESS_FIXTURE
    index_path: str = _DEFAULT_INDEX_PATH
    use_index: bool = True
    max_snippets_per_source: int = 3
    max_snippet_chars: int = 360


class RagCitationExtractor:
    """Extract local, normalized citation metadata for RAG groundedness.

    POST-H-011-B deliberately stays local-only and deterministic. It does not
    score answer claims; it only builds reliable source evidence so later
    micro-sprints can evaluate claims without inventing citations.
    """

    def __init__(self, root: Path, *, options: SourceCoverageOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SourceCoverageOptions()
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()
        self._index: dict[str, Any] | None = None
        self._chunks_by_path: dict[str, list[dict[str, Any]]] | None = None

    @property
    def fixture_path(self) -> Path:
        return _resolve_inside_root(self.root, self.options.fixture_path) or self.root / self.options.fixture_path

    @property
    def index_path(self) -> Path:
        return _resolve_inside_root(self.root, self.options.index_path) or self.root / self.options.index_path

    def normalize_source_path(self, source: str) -> tuple[str | None, Finding | None]:
        """Normalize a user/fixture source path and reject non-local sources."""

        raw = str(source or "").strip().replace("\\", "/")
        if not raw:
            return None, Finding("RAG_SOURCE_PATH_EMPTY", "Source path is empty.", Severity.BLOCK)
        if "://" in raw:
            return None, Finding(
                "RAG_SOURCE_REMOTE_NOT_ALLOWED",
                "RAG groundedness sources must be local project files; remote URLs are not allowed.",
                Severity.BLOCK,
                path=raw,
                metadata={"network_used": False, "external_api_used": False},
            )
        if raw.startswith(FORBIDDEN_SOURCE_PREFIXES):
            return None, Finding(
                "RAG_SOURCE_RUNTIME_PATH_NOT_CANONICAL",
                "Runtime outputs cannot be treated as canonical RAG sources.",
                Severity.BLOCK,
                path=raw,
            )
        candidate = _resolve_inside_root(self.root, raw)
        if candidate is None:
            return None, Finding(
                "RAG_SOURCE_OUTSIDE_ROOT",
                "RAG source path must stay inside the DevPilot workspace.",
                Severity.BLOCK,
                path=raw,
            )
        rel = _rel(self.root, candidate)
        if rel.startswith(FORBIDDEN_SOURCE_PREFIXES):
            return None, Finding(
                "RAG_SOURCE_RUNTIME_PATH_NOT_CANONICAL",
                "Runtime outputs cannot be treated as canonical RAG sources.",
                Severity.BLOCK,
                path=rel,
            )
        if candidate.suffix.lower() and candidate.suffix.lower() not in _ALLOWED_SOURCE_SUFFIXES:
            return None, Finding(
                "RAG_SOURCE_SUFFIX_NOT_SUPPORTED",
                "RAG source coverage only supports local text/markdown/JSON/YAML sources.",
                Severity.BLOCK,
                path=rel,
                metadata={"suffix": candidate.suffix.lower()},
            )
        return rel, None

    def load_fixture(self) -> tuple[dict[str, Any] | None, list[Finding]]:
        decision = self.path_guard.evaluate(self.fixture_path, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return None, [Finding("RAG_GROUNDEDNESS_FIXTURE_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata)]
        if not self.fixture_path.exists():
            return None, [Finding("RAG_GROUNDEDNESS_FIXTURE_NOT_FOUND", "Groundedness fixture was not found.", Severity.BLOCK, path=_rel(self.root, self.fixture_path))]
        try:
            return json.loads(self.fixture_path.read_text(encoding="utf-8")), []
        except (OSError, json.JSONDecodeError) as exc:
            return None, [Finding("RAG_GROUNDEDNESS_FIXTURE_LOAD_ERROR", f"Groundedness fixture could not be loaded: {exc}", Severity.ERROR, path=_rel(self.root, self.fixture_path))]

    def load_index(self) -> tuple[dict[str, Any] | None, list[Finding]]:
        if not self.options.use_index:
            return None, []
        if self._index is not None:
            return self._index, []
        decision = self.path_guard.evaluate(self.index_path, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return None, [Finding("RAG_INDEX_PATH_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata)]
        if not self.index_path.exists():
            self._index = None
            self._chunks_by_path = {}
            return None, [Finding("RAG_INDEX_NOT_FOUND_FOR_COVERAGE", "RAG docs_index is absent; source coverage will use direct document reads.", Severity.WARNING, path=_rel(self.root, self.index_path))]
        try:
            self._index = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return None, [Finding("RAG_INDEX_LOAD_ERROR_FOR_COVERAGE", f"RAG docs_index could not be loaded: {exc}", Severity.ERROR, path=_rel(self.root, self.index_path))]
        chunks_by_path: dict[str, list[dict[str, Any]]] = {}
        for chunk in self._index.get("chunks") or []:
            source = chunk.get("source") if isinstance(chunk.get("source"), dict) else {}
            path = source.get("path")
            if isinstance(path, str):
                normalized, finding = self.normalize_source_path(path)
                if normalized and finding is None:
                    chunks_by_path.setdefault(normalized, []).append(chunk)
        self._chunks_by_path = chunks_by_path
        return self._index, []

    def source_catalog_entry(self, source: str) -> tuple[dict[str, Any], list[Finding]]:
        findings: list[Finding] = []
        normalized, normalize_finding = self.normalize_source_path(source)
        if normalize_finding is not None:
            findings.append(normalize_finding)
        if normalized is None:
            return {
                "path": str(source),
                "normalized_path": None,
                "exists": False,
                "allowed": False,
                "indexed": False,
                "metadata": {},
                "headings": [],
                "snippets": [],
                "refs": [],
                "stale": False,
            }, findings

        path = self.root / normalized
        decision = self.path_guard.evaluate(path, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            finding = Finding("RAG_SOURCE_PATH_BLOCKED", decision.reason, Severity.BLOCK, path=normalized, metadata=decision.metadata)
            return {
                "path": normalized,
                "normalized_path": normalized,
                "exists": path.exists(),
                "allowed": False,
                "indexed": False,
                "metadata": {},
                "headings": [],
                "snippets": [],
                "refs": [],
                "stale": False,
            }, [*findings, finding]

        if not path.exists():
            return {
                "path": normalized,
                "normalized_path": normalized,
                "exists": False,
                "allowed": True,
                "indexed": False,
                "metadata": {},
                "headings": [],
                "snippets": [],
                "refs": [],
                "stale": False,
            }, [*findings, Finding("RAG_SOURCE_MISSING", "Expected RAG groundedness source does not exist.", Severity.BLOCK, path=normalized)]

        metadata, headings, direct_snippets = _read_source_metadata(self.root, path, max_snippets=self.options.max_snippets_per_source, max_chars=self.options.max_snippet_chars)
        _, index_findings = self.load_index()
        findings.extend(index_findings)
        chunks = (self._chunks_by_path or {}).get(normalized, [])
        indexed_snippets = _snippets_from_index_chunks(chunks, max_snippets=self.options.max_snippets_per_source, max_chars=self.options.max_snippet_chars)
        snippets = indexed_snippets or direct_snippets
        refs = [snippet["ref"] for snippet in snippets]
        stale = _is_stale(metadata)
        if stale:
            findings.append(
                Finding(
                    "RAG_SOURCE_STALE",
                    "Expected RAG source is marked as stale/deprecated by local metadata.",
                    Severity.BLOCK,
                    path=normalized,
                    metadata={"status": metadata.get("status"), "lifecycle": metadata.get("lifecycle")},
                )
            )
        return {
            "path": normalized,
            "normalized_path": normalized,
            "exists": True,
            "allowed": True,
            "indexed": bool(chunks),
            "evidence_mode": "index" if chunks else "direct",
            "metadata": metadata,
            "doc_id": metadata.get("doc_id") or metadata.get("id"),
            "status": metadata.get("status"),
            "updated": metadata.get("updated"),
            "title": metadata.get("title") or _title_from_headings(headings) or normalized,
            "headings": headings,
            "snippets": snippets,
            "refs": refs,
            "stale": stale,
        }, findings

    def evaluate_case_sources(self, case: dict[str, Any]) -> tuple[dict[str, Any], list[Finding]]:
        expected_sources = list(case.get("expected_sources") or [])
        threshold = float(case.get("minimum_source_coverage") or 1.0)
        case_id = str(case.get("case_id") or "unknown-case")
        findings: list[Finding] = []
        source_results: list[dict[str, Any]] = []

        seen: set[str] = set()
        for source in expected_sources:
            entry, entry_findings = self.source_catalog_entry(str(source))
            findings.extend(_case_scoped_findings(entry_findings, case_id))
            normalized = entry.get("normalized_path") or entry.get("path")
            if normalized in seen:
                findings.append(Finding("RAG_SOURCE_DUPLICATE", "Expected source is duplicated in a groundedness case.", Severity.WARNING, path=str(normalized), metadata={"case_id": case_id}))
            seen.add(str(normalized))
            source_results.append(entry)

        expected_total = len(expected_sources)
        matched_sources = [item for item in source_results if item.get("exists") is True and item.get("allowed") is True and not item.get("stale")]
        missing_sources = [item["path"] for item in source_results if not item.get("exists")]
        stale_sources = [item["path"] for item in source_results if item.get("stale")]
        disallowed_sources = [item["path"] for item in source_results if item.get("allowed") is False]
        coverage = round((len(matched_sources) / expected_total) if expected_total else 0.0, 4)
        if coverage < threshold:
            findings.append(
                Finding(
                    "RAG_SOURCE_LOW_COVERAGE",
                    "Source coverage is below the case threshold.",
                    Severity.BLOCK,
                    metadata={"case_id": case_id, "source_coverage": coverage, "minimum_source_coverage": threshold},
                )
            )
        status = "pass"
        if missing_sources or stale_sources or disallowed_sources or coverage < threshold:
            status = "block"

        return {
            "case_id": case_id,
            "status": status,
            "source_coverage": coverage,
            "minimum_source_coverage": threshold,
            "expected_sources_total": expected_total,
            "matched_sources_total": len(matched_sources),
            "missing_sources_total": len(missing_sources),
            "stale_sources_total": len(stale_sources),
            "disallowed_sources_total": len(disallowed_sources),
            "expected_sources": [_source_public_view(item) for item in source_results],
            "matched_sources": [_source_public_view(item) for item in matched_sources],
            "missing_sources": missing_sources,
            "stale_sources": stale_sources,
            "disallowed_sources": disallowed_sources,
            "indexed_sources_total": len([item for item in source_results if item.get("indexed")]),
            "direct_sources_total": len([item for item in source_results if item.get("evidence_mode") == "direct"]),
            "citation_refs": sorted({ref for item in source_results for ref in item.get("refs", [])}),
            "findings": [finding.to_dict() for finding in findings if finding.metadata.get("case_id") == case_id or finding.id.startswith("RAG_SOURCE")],
        }, findings


class RagSourceCoverageEvaluator:
    """Evaluate source availability/coverage for a groundedness fixture suite."""

    def __init__(self, root: Path, *, options: SourceCoverageOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SourceCoverageOptions()
        self.extractor = RagCitationExtractor(self.root, options=self.options)

    def run(self) -> CommandResult:
        fixture, findings = self.extractor.load_fixture()
        if fixture is None:
            exit_code = _exit_code(findings)
            return CommandResult(
                command=RAG_SOURCE_COVERAGE_COMMAND,
                ok=False,
                exit_code=exit_code,
                message="RAG source coverage fixture could not be loaded.",
                data={"summary": _summary_template(self.options, cases_total=0), "report": None},
                findings=findings,
            )

        index, index_findings = self.extractor.load_index()
        findings.extend(index_findings)
        case_results: list[dict[str, Any]] = []
        for case in fixture.get("cases") or []:
            case_result, case_findings = self.extractor.evaluate_case_sources(case)
            case_results.append(case_result)
            findings.extend(case_findings)

        blocking_total = len([finding for finding in findings if finding.severity == Severity.BLOCK])
        cases_total = len(case_results)
        cases_blocked = len([case for case in case_results if case["status"] == "block"])
        source_coverage_avg = round(sum(case["source_coverage"] for case in case_results) / cases_total, 4) if cases_total else 0.0
        missing_sources_total = sum(case["missing_sources_total"] for case in case_results)
        stale_sources_total = sum(case["stale_sources_total"] for case in case_results)
        matched_sources_total = sum(case["matched_sources_total"] for case in case_results)
        expected_sources_total = sum(case["expected_sources_total"] for case in case_results)
        summary = {
            **_summary_template(self.options, cases_total=cases_total),
            "suite_id": fixture.get("suite_id"),
            "cases_passed": len([case for case in case_results if case["status"] == "pass"]),
            "cases_warned": 0,
            "cases_blocked": cases_blocked,
            "expected_sources_total": expected_sources_total,
            "matched_sources_total": matched_sources_total,
            "source_coverage_avg": source_coverage_avg,
            "missing_sources_total": missing_sources_total,
            "stale_sources_total": stale_sources_total,
            "disallowed_sources_total": sum(case["disallowed_sources_total"] for case in case_results),
            "indexed_sources_total": sum(case["indexed_sources_total"] for case in case_results),
            "direct_sources_total": sum(case["direct_sources_total"] for case in case_results),
            "index_loaded": index is not None,
            "index_path": _rel(self.root, self.extractor.index_path),
            "blocking_findings_total": blocking_total,
            "findings_total": len(findings),
        }
        report = _build_report(summary, case_results, findings)
        ok = blocking_total == 0 and cases_blocked == 0
        return CommandResult(
            command=RAG_SOURCE_COVERAGE_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="RAG source coverage passed." if ok else "RAG source coverage found blocking source evidence gaps.",
            data={"summary": summary, "case_results": case_results, "report": report},
            findings=findings,
        )


def _summary_template(options: SourceCoverageOptions, *, cases_total: int) -> dict[str, Any]:
    return {
        "created_by": POST_H_011_B_CREATED_BY,
        "status": "implemented-initial",
        "preliminary": True,
        "fixture_path": options.fixture_path,
        "cases_total": cases_total,
        "source_coverage_avg": 0.0,
        "network_used": False,
        "external_api_used": False,
        "web_search_used": False,
        "llm_judge_used": False,
        "remote_execution_enabled": False,
        "connector_write_enabled": False,
        "plugin_execution_enabled": False,
        "mutations_performed": False,
        "source_mutations_performed": False,
        "raw_payloads_read": False,
        "outputs_as_sources_allowed": False,
        "local_first": True,
        "dry_run": True,
    }


def _build_report(summary: dict[str, Any], case_results: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-RAG-GROUNDEDNESS-REPORT-V1",
        "report_id": "devpilot-rag-source-coverage-report",
        "suite_id": str(summary.get("suite_id") or "unknown-suite"),
        "created_by": POST_H_011_B_CREATED_BY,
        "status": "pass" if summary.get("blocking_findings_total") == 0 and summary.get("cases_blocked") == 0 else "block",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": {
            "cases_total": int(summary.get("cases_total") or 0),
            "cases_passed": int(summary.get("cases_passed") or 0),
            "cases_warned": int(summary.get("cases_warned") or 0),
            "cases_blocked": int(summary.get("cases_blocked") or 0),
            "source_coverage_avg": float(summary.get("source_coverage_avg") or 0.0),
            "claim_support_avg": 0.0,
            "unsupported_claims_total": 0,
            "missing_sources_total": int(summary.get("missing_sources_total") or 0),
            "stale_sources_total": int(summary.get("stale_sources_total") or 0),
            "forbidden_claims_detected_total": 0,
            "network_used": False,
            "external_api_used": False,
            "web_search_used": False,
            "llm_judge_used": False,
        },
        "case_results": [_report_case_result(case) for case in case_results],
        "findings": [finding.to_dict() for finding in findings],
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
            "POST-H-011-B validates local citation/source coverage only; claim support is implemented in POST-H-011-C.",
            "RAG remains non-authoritative: canonical documentation sources remain the source of truth.",
        ],
    }


def _report_case_result(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "status": case["status"],
        "source_coverage": case["source_coverage"],
        "claim_support": 0.0,
        "expected_sources_total": case["expected_sources_total"],
        "matched_sources_total": case["matched_sources_total"],
        "required_claims_total": 0,
        "supported_claims_total": 0,
        "unsupported_claims": [],
        "forbidden_claims_detected": [],
        "findings": case.get("findings") or [],
        "matched_sources": case.get("matched_sources") or [],
        "missing_sources": case.get("missing_sources") or [],
        "stale_sources": case.get("stale_sources") or [],
        "citation_refs": case.get("citation_refs") or [],
    }


def _source_public_view(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": item.get("path"),
        "exists": bool(item.get("exists")),
        "allowed": bool(item.get("allowed")),
        "indexed": bool(item.get("indexed")),
        "evidence_mode": item.get("evidence_mode"),
        "doc_id": item.get("doc_id"),
        "status": item.get("status"),
        "updated": item.get("updated"),
        "title": item.get("title"),
        "stale": bool(item.get("stale")),
        "headings": item.get("headings") or [],
        "snippets": item.get("snippets") or [],
        "refs": item.get("refs") or [],
    }


def _case_scoped_findings(findings: Iterable[Finding], case_id: str) -> list[Finding]:
    scoped: list[Finding] = []
    for finding in findings:
        metadata = dict(finding.metadata)
        metadata.setdefault("case_id", case_id)
        scoped.append(Finding(finding.id, finding.message, finding.severity, path=finding.path, metadata=metadata))
    return scoped


def _read_source_metadata(root: Path, path: Path, *, max_snippets: int, max_chars: int) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}, [], []
    text = redact_string(text)
    rel = _rel(root, path)
    if path.suffix.lower() == ".json":
        metadata = _metadata_from_json(text)
    else:
        metadata = _metadata_from_frontmatter(text)
    headings = _extract_headings(text)
    snippets = _direct_snippets(rel, text, max_snippets=max_snippets, max_chars=max_chars)
    return metadata, headings, snippets


def _metadata_from_frontmatter(text: str) -> dict[str, Any]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    metadata: dict[str, Any] = {}
    for line in match.group("body").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        clean_key = key.strip()
        clean_value = value.strip().strip('"').strip("'")
        if clean_key:
            metadata[clean_key] = clean_value
    return metadata


def _metadata_from_json(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    keys = ("schema_id", "doc_id", "id", "status", "version", "owner", "updated", "title", "lifecycle")
    return {key: payload[key] for key in keys if key in payload and isinstance(payload[key], (str, int, float, bool))}


def _extract_headings(text: str) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = _HEADING_RE.match(line)
        if match:
            headings.append({"level": len(match.group("level")), "title": match.group("title").strip(), "line": line_no})
    return headings[:20]


def _direct_snippets(rel: str, text: str, *, max_snippets: int, max_chars: int) -> list[dict[str, Any]]:
    lines = text.splitlines()
    snippets: list[dict[str, Any]] = []
    starts: list[int] = []
    for idx, line in enumerate(lines, start=1):
        if line.strip() and not line.strip().startswith("---"):
            starts.append(idx)
        if len(starts) >= max_snippets:
            break
    if not starts and lines:
        starts = [1]
    for start in starts:
        end = min(start + 5, len(lines))
        fragment = "\n".join(lines[start - 1 : end]).strip()
        if len(fragment) > max_chars:
            fragment = fragment[: max_chars - 1].rstrip() + "…"
        snippets.append({"line_start": start, "line_end": end, "fragment": fragment, "ref": f"{rel}#L{start}-L{end}"})
    return snippets


def _snippets_from_index_chunks(chunks: list[dict[str, Any]], *, max_snippets: int, max_chars: int) -> list[dict[str, Any]]:
    snippets: list[dict[str, Any]] = []
    for chunk in sorted(chunks, key=lambda item: ((item.get("source") or {}).get("line_start") or 0))[:max_snippets]:
        source = chunk.get("source") if isinstance(chunk.get("source"), dict) else {}
        path = str(source.get("path") or "")
        start = int(source.get("line_start") or 1)
        end = int(source.get("line_end") or start)
        fragment = redact_string(str(chunk.get("fragment") or ""))
        if len(fragment) > max_chars:
            fragment = fragment[: max_chars - 1].rstrip() + "…"
        snippets.append({"line_start": start, "line_end": end, "fragment": fragment, "ref": f"{path}#L{start}-L{end}", "chunk_id": chunk.get("chunk_id")})
    return snippets


def _title_from_headings(headings: list[dict[str, Any]]) -> str | None:
    for heading in headings:
        if heading.get("level") == 1:
            return str(heading.get("title") or "") or None
    return None


def _is_stale(metadata: dict[str, Any]) -> bool:
    status = str(metadata.get("status") or "").strip().lower()
    lifecycle = str(metadata.get("lifecycle") or "").strip().lower()
    return status in STALE_STATUSES or lifecycle in STALE_STATUSES


def _resolve_inside_root(root: Path, path: str | Path) -> Path | None:
    raw = str(path).strip().replace("\\", "/")
    if not raw:
        return None
    if "://" in raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / PurePosixPath(raw)
    try:
        resolved = candidate.resolve()
        resolved.relative_to(root.resolve())
        return resolved
    except (OSError, ValueError):
        return None


def _rel(root: Path, path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _exit_code(findings: list[Finding]) -> ExitCode:
    if any(finding.severity == Severity.ERROR for finding in findings):
        return ExitCode.ERROR
    if any(finding.severity == Severity.BLOCK for finding in findings):
        return ExitCode.BLOCK
    if any(finding.severity == Severity.FAIL for finding in findings):
        return ExitCode.FAIL
    return ExitCode.PASS


__all__ = [
    "DEFAULT_RAG_GROUNDEDNESS_FIXTURE",
    "POST_H_011_B_CREATED_BY",
    "RAG_SOURCE_COVERAGE_COMMAND",
    "RagCitationExtractor",
    "RagSourceCoverageEvaluator",
    "SourceCoverageOptions",
]
