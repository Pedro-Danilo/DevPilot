from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect, SecretGuard, redact_string
from devpilot_core.rag.indexer import _DEFAULT_INDEX_PATH, _tokens


@dataclass(frozen=True)
class RagQueryOptions:
    """Options for local lexical RAG retrieval."""

    query: str
    index_path: str = _DEFAULT_INDEX_PATH
    top_k: int = 5
    max_fragment_chars: int = 700


class LocalRagRetriever:
    """Retrieve source-grounded chunks from a local lexical RAG index."""

    def __init__(self, root: Path, *, options: RagQueryOptions) -> None:
        self.root = Path(root).resolve()
        self.options = options
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()

    @property
    def index_path(self) -> Path:
        candidate = Path(self.options.index_path)
        return candidate if candidate.is_absolute() else self.root / candidate

    def query(self) -> CommandResult:
        safe_query_result = self.secret_guard.redact(self.options.query)
        safe_query = str(safe_query_result.value).strip()
        if not safe_query:
            return CommandResult(
                command="rag query",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="RAG query requires non-empty text.",
                data={"summary": _query_summary_template(self.options, self.index_path, index_loaded=False)},
                findings=[Finding("RAG_QUERY_EMPTY", "RAG query requires non-empty text.", Severity.BLOCK)],
            )
        decision = self.path_guard.evaluate(self.index_path, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return CommandResult(
                command="rag query",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="RAG index path was blocked by PathGuard.",
                data={"summary": _query_summary_template(self.options, self.index_path, index_loaded=False)},
                findings=[Finding("RAG_INDEX_PATH_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata)],
            )
        if not self.index_path.exists():
            return CommandResult(
                command="rag query",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="RAG index not found. Run `python -m devpilot_core rag index --target docs --json` first.",
                data={"summary": _query_summary_template(self.options, self.index_path, index_loaded=False)},
                findings=[Finding("RAG_INDEX_NOT_FOUND", "RAG index was not found.", Severity.BLOCK, path=_rel(self.root, self.index_path))],
            )
        try:
            index = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return CommandResult(
                command="rag query",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="RAG index could not be loaded.",
                data={"summary": _query_summary_template(self.options, self.index_path, index_loaded=False)},
                findings=[Finding("RAG_INDEX_LOAD_ERROR", f"RAG index could not be loaded: {exc}", Severity.ERROR, path=_rel(self.root, self.index_path))],
            )

        chunks = index.get("chunks") or []
        scored = _score_chunks(safe_query, chunks)
        top_k = max(1, min(int(self.options.top_k), 20))
        hits = scored[:top_k]
        sources = [_source_from_hit(hit, max_fragment_chars=self.options.max_fragment_chars) for hit in hits]
        if not sources:
            return CommandResult(
                command="rag query",
                ok=False,
                exit_code=ExitCode.FAIL,
                message="RAG query did not find grounded sources; no answer was generated.",
                data={
                    "summary": {
                        **_query_summary_template(self.options, self.index_path, index_loaded=True),
                        "sources_total": 0,
                        "answer_generated": False,
                        "grounded": False,
                    },
                    "answer": None,
                    "sources": [],
                },
                findings=[Finding("RAG_QUERY_NO_SOURCES", "No grounded source chunks matched the query; DevPilot did not invent an answer.", Severity.FAIL)],
            )

        answer = _build_grounded_answer(safe_query, sources)
        findings = [
            Finding(
                "RAG_QUERY_GROUNDED_SOURCES",
                "RAG query returned a grounded answer with local source references.",
                Severity.INFO,
                metadata={"sources_total": len(sources), "index_path": _rel(self.root, self.index_path)},
            )
        ]
        if safe_query_result.redactions:
            findings.append(
                Finding(
                    "RAG_QUERY_REDACTED_INPUT",
                    "SecretGuard redacted sensitive-looking content in the query before retrieval.",
                    Severity.WARNING,
                    metadata={"redactions": safe_query_result.redactions},
                )
            )
        return CommandResult(
            command="rag query",
            ok=True,
            exit_code=ExitCode.PASS,
            message="RAG query completed with grounded local sources.",
            data={
                "summary": {
                    **_query_summary_template(self.options, self.index_path, index_loaded=True),
                    "sources_total": len(sources),
                    "answer_generated": True,
                    "grounded": True,
                    "chunks_available_total": len(chunks),
                    "redactions_total": safe_query_result.redactions,
                },
                "answer": answer,
                "sources": sources,
                "index": {key: value for key, value in index.items() if key != "chunks"},
            },
            findings=findings,
        )


def _query_summary_template(options: RagQueryOptions, index_path: Path, *, index_loaded: bool) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "index_path": str(index_path).replace("\\", "/"),
        "index_loaded": index_loaded,
        "top_k": options.top_k,
        "lexical_retrieval": True,
        "embeddings_enabled": False,
        "llm_used": False,
        "network_used": False,
        "external_api_used": False,
        "secret_guard_used": True,
        "path_guard_used": True,
        "preliminary": True,
    }


def _score_chunks(query: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query_tokens = _tokens(query)
    query_counts: dict[str, int] = {}
    for token in query_tokens:
        query_counts[token] = query_counts.get(token, 0) + 1
    if not query_counts:
        return []
    scored: list[dict[str, Any]] = []
    for chunk in chunks:
        token_counts = chunk.get("tokens") if isinstance(chunk.get("tokens"), dict) else {}
        if not token_counts:
            continue
        score = 0.0
        matched_terms: list[str] = []
        terms_total = max(int(chunk.get("terms_total") or 1), 1)
        for token, q_count in query_counts.items():
            count = int(token_counts.get(token, 0) or 0)
            if count:
                matched_terms.append(token)
                score += (1.0 + math.log(count + 1.0)) * q_count
        if score <= 0:
            continue
        normalized = round(score / math.sqrt(terms_total), 6)
        scored.append({"chunk": chunk, "score": normalized, "matched_terms": sorted(set(matched_terms))})
    return sorted(scored, key=lambda item: (-item["score"], item["chunk"]["source"]["path"], item["chunk"]["source"]["line_start"]))


def _source_from_hit(hit: dict[str, Any], *, max_fragment_chars: int) -> dict[str, Any]:
    chunk = hit["chunk"]
    fragment = str(chunk.get("fragment") or "")
    fragment = redact_string(fragment)
    if len(fragment) > max_fragment_chars:
        fragment = fragment[: max_fragment_chars - 1].rstrip() + "…"
    return {
        "chunk_id": chunk.get("chunk_id"),
        "path": chunk["source"]["path"],
        "title": chunk["source"].get("title"),
        "line_start": chunk["source"]["line_start"],
        "line_end": chunk["source"]["line_end"],
        "score": hit["score"],
        "matched_terms": hit["matched_terms"],
        "fragment": fragment,
        "ref": f"{chunk['source']['path']}#L{chunk['source']['line_start']}-L{chunk['source']['line_end']}",
    }


def _build_grounded_answer(query: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    lead = sources[0]
    return {
        "text": (
            "Respuesta basada únicamente en fuentes locales recuperadas. "
            f"La evidencia principal está en `{lead['ref']}`. Revise las fuentes listadas para validar el contexto completo."
        ),
        "query": query,
        "grounded": True,
        "sources_required": True,
        "source_refs": [source["ref"] for source in sources],
        "limitations": [
            "FUNC-SPRINT-87 usa recuperación lexical, no embeddings semánticos.",
            "La respuesta no usa LLM y no sintetiza más allá de las fuentes recuperadas.",
        ],
    }


def _rel(root: Path, path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


__all__ = ["LocalRagRetriever", "RagQueryOptions"]
