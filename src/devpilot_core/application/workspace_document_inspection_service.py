from __future__ import annotations

import hashlib
import json
import posixpath
import re
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlsplit

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.repo.git_adapter import GitAdapter
from devpilot_core.validators.frontmatter import parse_frontmatter_text

from .workspace_documents_service import (
    MAX_DISCOVERY_FILES,
    MAX_INLINE_BYTES,
    WorkspaceDocumentNode,
    WorkspaceDocumentsApplicationService,
    _blocked,
    _error,
    _read_bytes_no_follow,
    _safety,
    sha_bytes,
)

MAX_SEARCH_QUERY_LENGTH = 200
MAX_SEARCH_RESULTS = 100
MAX_HISTORY_PAGE_SIZE = 50
MAX_HISTORY_OFFSET = 1000
DEFAULT_DIFF_BYTES = 262_144
MAX_DIFF_BYTES = 1_048_576
MAX_LINKS = 500
_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")


@dataclass(frozen=True)
class _SearchCacheEntry:
    relative_path: str
    document_id: str
    modified_ns: int
    size_bytes: int
    sha256: str
    text: str
    folded: str
    title: str
    category: str
    classification: str


# Search index contract: memory-only, active-workspace scoped, never externally persisted.
class WorkspaceDocumentInspectionApplicationService:
    """UOC-002 read-only metadata, Git, search and link inspection boundary.

    The service composes UOC-001 discovery and opaque-id resolution. It never
    accepts an absolute browser path, never persists document content outside
    the active workspace, and invokes Git exclusively through typed read-only
    adapter methods.
    """

    def __init__(self, documents: WorkspaceDocumentsApplicationService, platform_root: Path) -> None:
        self.documents = documents
        self.platform_root = Path(platform_root).resolve()
        self._search_caches: dict[str, dict[str, _SearchCacheEntry]] = {}

    def metadata(self, document_id: str) -> CommandResult:
        started = time.perf_counter()
        resolved = self._resolve(document_id, command="workspace documents inspection metadata")
        if isinstance(resolved, CommandResult):
            return resolved
        context, path, node = resolved
        raw = self._read(path, node, command="workspace documents inspection metadata")
        if isinstance(raw, CommandResult):
            return raw
        content = raw.decode("utf-8-sig")
        frontmatter = _frontmatter_metadata(node, content)
        classification = self._classification(node.relative_path)
        adapter = GitAdapter(context.active_workspace_root)
        status = adapter.file_status(node.relative_path)
        history = adapter.file_history(node.relative_path, limit=1, offset=0)
        git_summary = _git_metadata(status, history)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        document = {
            **node.to_dict(),
            "sha256": sha_bytes(raw),
            "encoding": "utf-8",
            "frontmatter": frontmatter,
            "classification": classification,
            "git": git_summary,
        }
        findings = list(context.findings) + list(status.findings) + list(history.findings)
        findings.append(Finding("WORKSPACE_DOCUMENT_INSPECTION_METADATA_PASS", "Document metadata, frontmatter and Git state were inspected read-only.", Severity.INFO, path=node.relative_path))
        return CommandResult(
            command="workspace documents inspection metadata",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Workspace document inspection metadata is available.",
            data={
                "summary": {
                    "workspace_id": context.active_workspace_id,
                    "document_id": document_id,
                    "elapsed_ms": elapsed_ms,
                    "read_only": True,
                    "mutations_performed": False,
                    "preliminary": True,
                },
                "document": document,
                "ui_workspace_context": context.summary(),
                "safety": _inspection_safety(),
            },
            findings=findings,
        )

    def history(self, document_id: str, *, limit: int = 20, offset: int = 0) -> CommandResult:
        resolved = self._resolve(document_id, command="workspace documents history")
        if isinstance(resolved, CommandResult):
            return resolved
        context, _, node = resolved
        safe_limit = max(1, min(int(limit), MAX_HISTORY_PAGE_SIZE))
        safe_offset = max(0, min(int(offset), MAX_HISTORY_OFFSET))
        result = GitAdapter(context.active_workspace_root).file_history(node.relative_path, limit=safe_limit, offset=safe_offset)
        if not result.ok:
            return result
        data = dict(result.data)
        data["document"] = {"document_id": document_id, "relative_path": node.relative_path, "name": node.name}
        data["ui_workspace_context"] = context.summary()
        data["safety"] = _inspection_safety()
        return CommandResult("workspace documents history", True, ExitCode.PASS, "Document Git history is available.", data=data, findings=result.findings)

    def diff(self, document_id: str, *, base_ref: str = "HEAD", max_bytes: int = DEFAULT_DIFF_BYTES) -> CommandResult:
        resolved = self._resolve(document_id, command="workspace documents diff")
        if isinstance(resolved, CommandResult):
            return resolved
        context, path, node = resolved
        bounded_bytes = max(1, min(int(max_bytes), MAX_DIFF_BYTES))
        adapter = GitAdapter(context.active_workspace_root)
        status = adapter.file_status(node.relative_path)
        if not status.ok:
            return status
        result = adapter.file_diff(node.relative_path, base_ref=base_ref, max_bytes=bounded_bytes)
        if not result.ok:
            return result
        status_data = (status.data or {}).get("status", {})
        diff_text = str((result.data or {}).get("diff", ""))
        findings = list(status.findings) + list(result.findings)
        synthetic = False
        if status_data.get("untracked") and not diff_text:
            raw = self._read(path, node, command="workspace documents diff")
            if isinstance(raw, CommandResult):
                return raw
            rendered = raw[:bounded_bytes].decode("utf-8", errors="replace")
            diff_text = "--- /dev/null\n+++ b/" + node.relative_path + "\n" + "\n".join(f"+{line}" for line in rendered.splitlines())
            synthetic = True
            if len(raw) > bounded_bytes:
                findings.append(Finding("WORKSPACE_DOCUMENT_UNTRACKED_DIFF_TRUNCATED", "Synthetic untracked document diff was truncated by the byte budget.", Severity.WARNING, path=node.relative_path, metadata={"max_bytes": bounded_bytes, "original_bytes": len(raw)}))
        data = dict(result.data)
        data["diff"] = diff_text
        data["document"] = {"document_id": document_id, "relative_path": node.relative_path, "name": node.name}
        data["git_status"] = status_data
        data["summary"] = dict(data.get("summary", {})) | {"synthetic_untracked_diff": synthetic}
        data["ui_workspace_context"] = context.summary()
        data["safety"] = _inspection_safety()
        return CommandResult("workspace documents diff", True, ExitCode.PASS, "Document diff is available in read-only mode.", data=data, findings=findings)

    def search(self, *, query: str, limit: int = 50, offset: int = 0) -> CommandResult:
        started = time.perf_counter()
        normalized = str(query or "").strip()
        if len(normalized) < 2 or len(normalized) > MAX_SEARCH_QUERY_LENGTH:
            return _blocked("workspace documents search", "WORKSPACE_DOCUMENT_SEARCH_QUERY_BLOCK", "Full-text search query must contain between 2 and 200 characters.")
        context, failure = self.documents._require_workspace_context("workspace documents search")
        if failure is not None:
            return failure
        assert context is not None and context.active_workspace_root is not None
        nodes, discovery_findings, discovery = self.documents._discover(context)
        documents = [node for node in nodes if node.kind == "document" and node.readable]
        cache_key = str(context.active_workspace_root)
        cache = self._search_caches.setdefault(cache_key, {})
        active_paths: set[str] = set()
        reused = 0
        reindexed = 0
        skipped = 0
        for node in documents:
            active_paths.add(node.relative_path)
            path = context.active_workspace_root / PurePosixPath(node.relative_path)
            raw = self._read(path, node, command="workspace documents search")
            if isinstance(raw, CommandResult):
                skipped += 1
                continue
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                skipped += 1
                continue
            digest = sha_bytes(raw)
            stat_result = path.stat()
            current = cache.get(node.relative_path)
            if current is not None and current.sha256 == digest:
                reused += 1
                continue
            cache[node.relative_path] = _SearchCacheEntry(
                relative_path=node.relative_path,
                document_id=node.node_id,
                modified_ns=stat_result.st_mtime_ns,
                size_bytes=len(raw),
                sha256=digest,
                text=text,
                folded=text.casefold(),
                title=_document_title(node, text),
                category=node.category,
                classification=self._classification(node.relative_path)["level"],
            )
            reindexed += 1
        removed = 0
        for stale in sorted(set(cache) - active_paths):
            del cache[stale]
            removed += 1
        folded_query = normalized.casefold()
        matches: list[dict[str, Any]] = []
        for entry in cache.values():
            name_match = folded_query in entry.relative_path.casefold() or folded_query in entry.title.casefold()
            content_count = entry.folded.count(folded_query)
            if not name_match and content_count == 0:
                continue
            snippet, line_number = _search_snippet(entry.text, folded_query)
            matches.append({
                "document_id": entry.document_id,
                "relative_path": entry.relative_path,
                "title": entry.title,
                "category": entry.category,
                "classification": entry.classification,
                "sha256": entry.sha256,
                "size_bytes": entry.size_bytes,
                "match_count": content_count + (1 if name_match else 0),
                "line_number": line_number,
                "snippet": snippet,
            })
        matches.sort(key=lambda item: (-int(item["match_count"]), str(item["relative_path"])))
        safe_limit = max(1, min(int(limit), MAX_SEARCH_RESULTS))
        safe_offset = max(0, min(int(offset), 100_000))
        page = matches[safe_offset : safe_offset + safe_limit]
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        findings = list(context.findings) + discovery_findings + [Finding("WORKSPACE_DOCUMENT_FULL_TEXT_SEARCH_PASS", "Bounded local full-text search completed without external persistence.", Severity.INFO, metadata={"matching_total": len(matches), "reindexed": reindexed, "reused": reused})]
        return CommandResult(
            command="workspace documents search",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local full-text document search completed.",
            data={
                "summary": {
                    "workspace_id": context.active_workspace_id,
                    "query": normalized,
                    "matching_total": len(matches),
                    "returned_total": len(page),
                    "offset": safe_offset,
                    "limit": safe_limit,
                    "next_offset": safe_offset + len(page) if safe_offset + len(page) < len(matches) else None,
                    "indexed_documents": len(cache),
                    "cache_reused": reused,
                    "cache_reindexed": reindexed,
                    "cache_removed": removed,
                    "skipped_documents": skipped,
                    "cache_scope": "in-memory-active-workspace",
                    "cache_invalidated_by": ["sha256", "mtime", "size"],
                    "elapsed_ms": elapsed_ms,
                    "read_only": True,
                    "mutations_performed": False,
                    "external_persistence": False,
                    **discovery,
                },
                "results": page,
                "ui_workspace_context": context.summary(),
                "safety": _inspection_safety(),
            },
            findings=findings,
        )

    def links(self, document_id: str) -> CommandResult:
        resolved = self._resolve(document_id, command="workspace documents links")
        if isinstance(resolved, CommandResult):
            return resolved
        context, path, node = resolved
        raw = self._read(path, node, command="workspace documents links")
        if isinstance(raw, CommandResult):
            return raw
        try:
            content = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            return _blocked("workspace documents links", "WORKSPACE_DOCUMENT_LINK_ENCODING_BLOCK", "Only UTF-8 documents can be inspected for links.", path=node.relative_path)
        nodes, discovery_findings, _ = self.documents._discover(context)
        document_by_path = {item.relative_path: item for item in nodes if item.kind == "document"}
        outgoing = _extract_outgoing(node.relative_path, content, document_by_path)
        incoming: list[dict[str, Any]] = []
        assert context.active_workspace_root is not None
        for candidate in nodes:
            if candidate.kind != "document" or candidate.extension != ".md" or not candidate.readable or candidate.relative_path == node.relative_path:
                continue
            candidate_path = context.active_workspace_root / PurePosixPath(candidate.relative_path)
            candidate_raw = self._read(candidate_path, candidate, command="workspace documents links")
            if isinstance(candidate_raw, CommandResult):
                continue
            try:
                candidate_text = candidate_raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                continue
            for link in _extract_outgoing(candidate.relative_path, candidate_text, document_by_path):
                if link.get("resolved_relative_path") == node.relative_path:
                    incoming.append({
                        "source_document_id": candidate.node_id,
                        "source_relative_path": candidate.relative_path,
                        "label": link.get("label"),
                        "target": link.get("target"),
                        "anchor": link.get("anchor"),
                    })
                    if len(incoming) >= MAX_LINKS:
                        break
            if len(incoming) >= MAX_LINKS:
                break
        findings = list(context.findings) + discovery_findings
        if len(outgoing) >= MAX_LINKS or len(incoming) >= MAX_LINKS:
            findings.append(Finding("WORKSPACE_DOCUMENT_LINKS_TRUNCATED", "Document link graph reached the bounded link limit.", Severity.WARNING, path=node.relative_path, metadata={"max_links": MAX_LINKS}))
        findings.append(Finding("WORKSPACE_DOCUMENT_LINKS_PASS", "Incoming and outgoing document links were resolved within the active workspace.", Severity.INFO, path=node.relative_path))
        return CommandResult(
            command="workspace documents links",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Document link relationships are available.",
            data={
                "summary": {
                    "workspace_id": context.active_workspace_id,
                    "document_id": document_id,
                    "outgoing_total": len(outgoing),
                    "incoming_total": len(incoming),
                    "max_links": MAX_LINKS,
                    "read_only": True,
                    "mutations_performed": False,
                    "preliminary": True,
                },
                "document": {"document_id": document_id, "relative_path": node.relative_path, "name": node.name},
                "outgoing": outgoing[:MAX_LINKS],
                "incoming": incoming[:MAX_LINKS],
                "ui_workspace_context": context.summary(),
                "safety": _inspection_safety(),
            },
            findings=findings,
        )

    def _resolve(self, document_id: str, *, command: str) -> tuple[Any, Path, WorkspaceDocumentNode] | CommandResult:
        context, failure = self.documents._require_workspace_context(command)
        if failure is not None:
            return failure
        assert context is not None
        resolved = self.documents._resolve_document(context, document_id)
        if isinstance(resolved, CommandResult):
            return resolved
        path, node = resolved
        return context, path, node

    @staticmethod
    def _read(path: Path, node: WorkspaceDocumentNode, *, command: str) -> bytes | CommandResult:
        if not node.readable:
            return _blocked(command, "WORKSPACE_DOCUMENT_SIZE_LIMIT_BLOCK", "Document exceeds the UOC-002 inspection budget.", path=node.relative_path, metadata={"maximum_inline_bytes": MAX_INLINE_BYTES})
        try:
            raw = _read_bytes_no_follow(path, maximum_bytes=MAX_INLINE_BYTES)
        except ValueError as exc:
            return _blocked(command, "WORKSPACE_DOCUMENT_SAFE_OPEN_BLOCK", str(exc), path=node.relative_path)
        except OSError as exc:
            return _error(command, "WORKSPACE_DOCUMENT_INSPECTION_READ_ERROR", "Document could not be inspected.", path=node.relative_path, metadata={"exception_type": exc.__class__.__name__})
        if len(raw) > MAX_INLINE_BYTES or b"\x00" in raw:
            return _blocked(command, "WORKSPACE_DOCUMENT_INSPECTION_CONTENT_BLOCK", "Document is binary-like or exceeds the inspection budget.", path=node.relative_path)
        return raw

    def _classification(self, relative_path: str) -> dict[str, Any]:
        normalized = relative_path.replace("\\", "/")
        registry = self.platform_root / ".devpilot" / "readiness" / "readiness_requirements.json"
        required: set[str] = set()
        optional: set[str] = set()
        source = "built-in-safe-fallback"
        if registry.is_file():
            try:
                payload = json.loads(registry.read_text(encoding="utf-8"))
                required.update(str(item).replace("\\", "/") for item in payload.get("required_artifacts", []))
                required.update(str(item).replace("\\", "/") for item in payload.get("strict_required_artifacts", []))
                optional.update(str(item).replace("\\", "/") for item in payload.get("optional_artifacts", []))
                source = ".devpilot/readiness/readiness_requirements.json"
            except (OSError, json.JSONDecodeError, TypeError):
                pass
        if normalized in required:
            level = "required"
        elif normalized in optional:
            level = "optional"
        elif "/adrs/" in f"/{normalized.lower()}/" or normalized.startswith("docs/onboarding/") or normalized.endswith("workspace_onboarding_baseline.md"):
            level = "recommended"
        elif normalized == ".devpilot/project.yaml":
            level = "required"
        else:
            level = "optional"
        return {"level": level, "source": source, "badges": [level.upper(), "READ-ONLY", "UOC-002"]}


def _frontmatter_metadata(node: WorkspaceDocumentNode, content: str) -> dict[str, Any]:
    if node.extension != ".md":
        return {"has_frontmatter": False, "fields": {}, "parse_warnings": [], "source": "not-applicable"}
    parsed = parse_frontmatter_text(content, path=Path(node.relative_path))
    warnings = [str(value) for key, value in parsed.frontmatter.items() if str(key).startswith("__unparsed_line_")]
    fields = {str(key): value for key, value in parsed.frontmatter.items() if not str(key).startswith("__unparsed_line_")}
    return {"has_frontmatter": parsed.has_frontmatter, "fields": fields, "parse_warnings": warnings, "source": "devpilot_core.validators.frontmatter.parse_frontmatter_text"}


def _git_metadata(status: CommandResult, history: CommandResult) -> dict[str, Any]:
    status_data = (status.data or {}).get("status", {}) if status.ok else {}
    history_data = history.data or {}
    commits = history_data.get("commits", []) if history.ok else []
    last_commit = commits[0] if commits else None
    is_repo = bool((history_data.get("summary", {}) if history.ok else {}).get("is_git_repo", (status.data or {}).get("summary", {}).get("is_git_repo", False)))
    return {
        "is_git_repo": is_repo,
        "status": status_data,
        "last_commit": last_commit,
        "history_available": bool(commits),
        "status_ok": status.ok,
        "history_ok": history.ok,
        "read_only": True,
    }


def _document_title(node: WorkspaceDocumentNode, content: str) -> str:
    if node.extension == ".md":
        metadata = _frontmatter_metadata(node, content)
        title = metadata.get("fields", {}).get("title")
        if title:
            return str(title).strip('"\'')
        for line in content.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return node.name


def _search_snippet(text: str, folded_query: str) -> tuple[str, int | None]:
    folded = text.casefold()
    index = folded.find(folded_query)
    if index < 0:
        return "", None
    line_number = text.count("\n", 0, index) + 1
    start = max(0, index - 100)
    end = min(len(text), index + len(folded_query) + 180)
    snippet = " ".join(text[start:end].replace("\r", " ").replace("\n", " ").split())
    return snippet, line_number


def _extract_outgoing(source_relative_path: str, content: str, document_by_path: dict[str, WorkspaceDocumentNode]) -> list[dict[str, Any]]:
    if not source_relative_path.lower().endswith(".md"):
        return []
    outgoing: list[dict[str, Any]] = []
    source_parent = PurePosixPath(source_relative_path).parent
    for label, raw_target in _LINK_RE.findall(content):
        target = raw_target.strip().strip("<>")
        if not target:
            continue
        split = urlsplit(target)
        if split.scheme or split.netloc:
            outgoing.append({"label": label, "target": target, "kind": "external", "resolved": False})
            continue
        if target.startswith("#"):
            outgoing.append({"label": label, "target": target, "kind": "anchor", "anchor": target[1:], "resolved": True, "resolved_relative_path": source_relative_path})
            continue
        decoded_path = unquote(split.path).replace("\\", "/")
        if decoded_path.startswith("/") or re.match(r"^[A-Za-z]:", decoded_path) or ":" in decoded_path:
            outgoing.append({"label": label, "target": target, "kind": "blocked", "resolved": False, "reason": "absolute-or-ads-like-target"})
            continue
        normalized = posixpath.normpath(str(source_parent / decoded_path))
        if normalized == ".":
            normalized = source_relative_path
        if normalized.startswith("../") or normalized == "..":
            outgoing.append({"label": label, "target": target, "kind": "blocked", "resolved": False, "reason": "workspace-escape"})
            continue
        candidate = document_by_path.get(normalized)
        outgoing.append({
            "label": label,
            "target": target,
            "kind": "document" if candidate else "missing",
            "anchor": split.fragment or None,
            "resolved": candidate is not None,
            "resolved_relative_path": normalized,
            "document_id": candidate.node_id if candidate else None,
        })
        if len(outgoing) >= MAX_LINKS:
            break
    return outgoing


def _inspection_safety() -> dict[str, Any]:
    return _safety() | {
        "git_commands_typed": True,
        "git_write_enabled": False,
        "search_index_external_persistence": False,
        "search_index_scope": "active-workspace-in-memory",
        "cross_workspace_results_allowed": False,
        "document_content_persisted_externally": False,
    }
