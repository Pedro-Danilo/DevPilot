from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect, SecretGuard, redact_string

_INDEX_SCHEMA_VERSION = "1.0.0"
_DEFAULT_INDEX_PATH = ".devpilot/rag/docs_index.json"
_ALLOWED_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml"}
_DENIED_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "outputs",
    "dist",
    "__pycache__",
    ".pytest_cache",
    "backups",
    "agent_sessions",
}
_DENIED_FILE_NAMES = {".env", ".env.local", ".env.dev", "providers.yaml", "devpilot.db"}
_WORD_RE = re.compile(r"[\wáéíóúüñÁÉÍÓÚÜÑ]{3,}", re.UNICODE)


@dataclass(frozen=True)
class RagIndexOptions:
    """Options for the local lexical RAG indexer."""

    target: str = "docs"
    index_path: str = _DEFAULT_INDEX_PATH
    chunk_lines: int = 40
    overlap_lines: int = 5
    max_file_bytes: int = 512_000


class LocalRagIndexer:
    """Build a deterministic local lexical index over approved project artifacts.

    FUNC-SPRINT-87 intentionally avoids external APIs, remote embeddings and
    heavyweight dependencies. The index is local JSON under ``.devpilot/rag`` and
    stores redacted text chunks with document/range metadata so every retrieval
    can cite grounded sources.
    """

    def __init__(self, root: Path, *, options: RagIndexOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or RagIndexOptions()
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()

    @property
    def index_path(self) -> Path:
        candidate = Path(self.options.index_path)
        return candidate if candidate.is_absolute() else self.root / candidate

    def build(self) -> CommandResult:
        target_path = _resolve_inside_root(self.root, self.options.target)
        findings: list[Finding] = []
        if target_path is None:
            return _blocked_result(
                command="rag index",
                finding_id="RAG_TARGET_OUTSIDE_ROOT",
                message="RAG indexing target must stay inside the DevPilot workspace.",
                path=str(self.options.target),
            )
        decision = self.path_guard.evaluate(target_path, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return CommandResult(
                command="rag index",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="RAG indexing target was blocked by PathGuard.",
                data={"summary": _index_summary_template(self.options, target_path, self.index_path, target_allowed=False)},
                findings=[
                    Finding(
                        "RAG_TARGET_PATH_BLOCKED",
                        decision.reason,
                        Severity.BLOCK,
                        path=decision.subject,
                        metadata=decision.metadata,
                    )
                ],
            )
        if not target_path.exists():
            return CommandResult(
                command="rag index",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="RAG indexing target does not exist.",
                data={"summary": _index_summary_template(self.options, target_path, self.index_path, target_allowed=True)},
                findings=[Finding("RAG_TARGET_NOT_FOUND", "RAG indexing target does not exist.", Severity.BLOCK, path=_rel(self.root, target_path))],
            )

        files = list(_iter_indexable_files(self.root, target_path, max_file_bytes=self.options.max_file_bytes))
        chunks: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        redactions_total = 0
        for file_path in files:
            rel_path = _rel(self.root, file_path)
            guard_decision = self.path_guard.evaluate(file_path, action="read")
            if guard_decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
                skipped.append({"path": rel_path, "reason": guard_decision.rule_id})
                continue
            try:
                raw_text = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                skipped.append({"path": rel_path, "reason": f"read_error:{exc.__class__.__name__}"})
                continue
            redaction = self.secret_guard.redact(raw_text)
            safe_text = str(redaction.value)
            redactions_total += redaction.redactions
            chunks.extend(_chunk_document(self.root, file_path, safe_text, self.options.chunk_lines, self.options.overlap_lines))

        index = {
            "schema_version": _INDEX_SCHEMA_VERSION,
            "index_id": _index_id(self.options.target, chunks),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "generator": {
                "component": "devpilot_core.rag.LocalRagIndexer",
                "sprint": "FUNC-SPRINT-87",
                "mode": "lexical-local",
                "preliminary": True,
            },
            "scope": {
                "target": _rel(self.root, target_path),
                "index_path": _rel(self.root, self.index_path),
                "allowed_suffixes": sorted(_ALLOWED_SUFFIXES),
                "denied_parts": sorted(_DENIED_PARTS),
                "denied_file_names": sorted(_DENIED_FILE_NAMES),
            },
            "security": {
                "network_used": False,
                "external_api_used": False,
                "embeddings_used": False,
                "llm_used": False,
                "secret_guard_used": True,
                "redactions_total": redactions_total,
                "raw_secrets_stored": False,
                "path_guard_used": True,
            },
            "summary": {
                "files_indexed_total": len(files) - len(skipped),
                "files_skipped_total": len(skipped),
                "chunks_total": len(chunks),
                "redactions_total": redactions_total,
                "lexical_index": True,
                "embeddings_enabled": False,
                "local_only": True,
            },
            "chunks": chunks,
            "skipped_files": skipped,
        }

        output_decision = self.path_guard.evaluate(self.index_path, action="write")
        if output_decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return CommandResult(
                command="rag index",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="RAG index output path was blocked by PathGuard.",
                data={"summary": _index_summary_template(self.options, target_path, self.index_path, target_allowed=True)},
                findings=[Finding("RAG_INDEX_OUTPUT_BLOCKED", output_decision.reason, Severity.BLOCK, path=output_decision.subject, metadata=output_decision.metadata)],
            )
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

        findings.append(
            Finding(
                "RAG_INDEX_CREATED",
                "Local lexical RAG index was created with source metadata and SecretGuard redaction.",
                Severity.INFO,
                metadata={"chunks_total": len(chunks), "files_indexed_total": index["summary"]["files_indexed_total"], "index_path": _rel(self.root, self.index_path)},
            )
        )
        if redactions_total:
            findings.append(
                Finding(
                    "RAG_INDEX_REDACTIONS_APPLIED",
                    "SecretGuard redacted content before indexing.",
                    Severity.WARNING,
                    metadata={"redactions_total": redactions_total},
                )
            )
        return CommandResult(
            command="rag index",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local lexical RAG index created.",
            data={
                "summary": {
                    **_index_summary_template(self.options, target_path, self.index_path, target_allowed=True),
                    **index["summary"],
                    "reports_written": False,
                    "mutations_performed": True,
                    "runtime_state_mutated": True,
                },
                "index": {key: value for key, value in index.items() if key != "chunks"},
                "sample_sources": [chunk["source"] for chunk in chunks[:5]],
            },
            findings=findings,
        )


def _index_summary_template(options: RagIndexOptions, target_path: Path, index_path: Path, *, target_allowed: bool) -> dict[str, Any]:
    return {
        "schema_version": _INDEX_SCHEMA_VERSION,
        "target": str(target_path).replace("\\", "/"),
        "index_path": str(index_path).replace("\\", "/"),
        "target_allowed": target_allowed,
        "chunk_lines": options.chunk_lines,
        "overlap_lines": options.overlap_lines,
        "network_used": False,
        "external_api_used": False,
        "embeddings_enabled": False,
        "llm_used": False,
        "secret_guard_used": True,
        "path_guard_used": True,
        "preliminary": True,
    }


def _blocked_result(*, command: str, finding_id: str, message: str, path: str | None = None) -> CommandResult:
    return CommandResult(
        command=command,
        ok=False,
        exit_code=ExitCode.BLOCK,
        message=message,
        data={"summary": {"network_used": False, "external_api_used": False, "preliminary": True}},
        findings=[Finding(finding_id, message, Severity.BLOCK, path=path)],
    )


def _resolve_inside_root(root: Path, value: str | Path) -> Path | None:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        resolved = candidate.resolve()
        resolved.relative_to(root.resolve())
        return resolved
    except ValueError:
        return None


def _iter_indexable_files(root: Path, target: Path, *, max_file_bytes: int) -> Iterable[Path]:
    paths = [target] if target.is_file() else sorted(target.rglob("*"))
    for path in paths:
        if not path.is_file():
            continue
        rel_parts = Path(_rel(root, path)).parts
        if any(part in _DENIED_PARTS for part in rel_parts):
            continue
        if path.name in _DENIED_FILE_NAMES:
            continue
        if path.suffix.lower() not in _ALLOWED_SUFFIXES:
            continue
        try:
            if path.stat().st_size > max_file_bytes:
                continue
        except OSError:
            continue
        yield path


def _chunk_document(root: Path, path: Path, text: str, chunk_lines: int, overlap_lines: int) -> list[dict[str, Any]]:
    safe_chunk_lines = max(5, int(chunk_lines))
    safe_overlap = max(0, min(int(overlap_lines), safe_chunk_lines - 1))
    lines = text.splitlines()
    if not lines:
        return []
    chunks: list[dict[str, Any]] = []
    start = 0
    while start < len(lines):
        end = min(len(lines), start + safe_chunk_lines)
        fragment = "\n".join(lines[start:end]).strip()
        if fragment:
            token_counts = _token_counts(fragment)
            chunk_id = _chunk_id(path, start + 1, end, fragment)
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "source": {
                        "path": _rel(root, path),
                        "line_start": start + 1,
                        "line_end": end,
                        "title": _extract_title(lines, default=path.name),
                    },
                    "fragment": fragment,
                    "tokens": token_counts,
                    "terms_total": sum(token_counts.values()),
                    "hash_sha256": hashlib.sha256(fragment.encode("utf-8")).hexdigest(),
                }
            )
        if end >= len(lines):
            break
        start = max(end - safe_overlap, start + 1)
    return chunks


def _extract_title(lines: list[str], *, default: str) -> str:
    for line in lines[:30]:
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()[:160] or default
        if stripped and not stripped.startswith("---"):
            return stripped[:160]
    return default


def _token_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in _tokens(text):
        counts[token] = counts.get(token, 0) + 1
    return counts


def _tokens(text: str) -> list[str]:
    return [match.group(0).lower() for match in _WORD_RE.finditer(text)]


def _chunk_id(path: Path, start: int, end: int, fragment: str) -> str:
    digest = hashlib.sha256(f"{path}:{start}:{end}:{fragment}".encode("utf-8")).hexdigest()[:16]
    return f"ragchunk_{digest}"


def _index_id(target: str, chunks: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256((target + ":" + str(len(chunks))).encode("utf-8")).hexdigest()[:16]
    return f"ragidx_{digest}"


def _rel(root: Path, path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


__all__ = ["LocalRagIndexer", "RagIndexOptions", "_tokens", "_DEFAULT_INDEX_PATH"]
