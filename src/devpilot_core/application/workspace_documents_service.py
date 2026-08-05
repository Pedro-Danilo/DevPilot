from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect, configured_external_workspace_roots

from .ui_workspace_context import UiWorkspaceContext, UiWorkspaceContextResolver

ALLOWED_EXTENSIONS = (".md", ".json", ".yaml", ".yml", ".txt")
DENIED_DIRECTORY_NAMES = {
    ".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".idea", ".vscode", "dist", "build", "coverage", "outputs",
}
DENIED_FILE_NAMES = {
    ".env", ".env.local", ".env.dev", ".env.prod", "providers.yaml", "providers.yml",
    "devpilot.db", "devpilot.db-wal", "devpilot.db-shm",
}
MAX_INLINE_BYTES = 1_048_576
MAX_DISCOVERY_FILES = 2_500
MAX_DISCOVERY_DEPTH = 12
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 250
DOCUMENT_ID_PREFIX = "doc_"
FOLDER_ID_PREFIX = "dir_"


@dataclass(frozen=True)
class WorkspaceDocumentNode:
    node_id: str
    kind: str
    name: str
    relative_path: str
    parent_id: str | None
    extension: str | None
    category: str
    size_bytes: int | None
    modified_at: str | None
    readable: bool
    blocked_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "document_id": self.node_id if self.kind == "document" else None,
            "kind": self.kind,
            "name": self.name,
            "relative_path": self.relative_path,
            "parent_id": self.parent_id,
            "extension": self.extension,
            "category": self.category,
            "size_bytes": self.size_bytes,
            "modified_at": self.modified_at,
            "readable": self.readable,
            "blocked_reason": self.blocked_reason,
        }


class WorkspaceDocumentsApplicationService:
    """Read-only, bounded document explorer for the explicitly active workspace.

    Browser clients submit opaque identifiers only. Filesystem paths are derived
    from the validated active workspace context, enumerated without following
    symlinks/reparse points and constrained to an extension/size allowlist.
    """

    def __init__(
        self,
        platform_root: Path,
        *,
        context_resolver: UiWorkspaceContextResolver | None = None,
    ) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.context_resolver = context_resolver or UiWorkspaceContextResolver(self.platform_root)
        self.path_guard = PathGuard(
            self.platform_root,
            allowed_external_roots=configured_external_workspace_roots(),
        )

    def list_documents(
        self,
        *,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
        query: str | None = None,
        extension: str | None = None,
        category: str | None = None,
    ) -> CommandResult:
        started = time.perf_counter()
        context, failure = self._require_workspace_context("workspace.documents.list")
        if failure is not None:
            return failure
        assert context is not None and context.active_workspace_root is not None
        nodes, findings, discovery = self._discover(context)
        normalized_query = str(query or "").strip().lower()
        normalized_extension = _normalize_extension(extension)
        normalized_category = str(category or "").strip().lower()
        filtered = [
            node
            for node in nodes
            if (not normalized_query or normalized_query in node.name.lower() or normalized_query in node.relative_path.lower())
            and (not normalized_extension or node.extension == normalized_extension)
            and (not normalized_category or node.category.lower() == normalized_category)
        ]
        safe_limit = max(1, min(int(limit), MAX_PAGE_SIZE))
        safe_offset = max(0, min(int(offset), 100_000))
        page = filtered[safe_offset : safe_offset + safe_limit]
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        summary = {
            "workspace_id": context.active_workspace_id,
            "workspace_mode": context.mode,
            "nodes_total": len(nodes),
            "matching_total": len(filtered),
            "returned_total": len(page),
            "documents_total": sum(1 for node in nodes if node.kind == "document"),
            "folders_total": sum(1 for node in nodes if node.kind == "folder"),
            "offset": safe_offset,
            "limit": safe_limit,
            "next_offset": safe_offset + len(page) if safe_offset + len(page) < len(filtered) else None,
            "query": normalized_query or None,
            "extension": normalized_extension or None,
            "category": normalized_category or None,
            "allowed_extensions": list(ALLOWED_EXTENSIONS),
            "maximum_inline_bytes": MAX_INLINE_BYTES,
            "elapsed_ms": elapsed_ms,
            "read_only": True,
            "mutations_performed": False,
            "network_used": False,
            "external_api_used": False,
            **discovery,
        }
        findings = list(context.findings) + findings
        findings.append(
            Finding(
                "WORKSPACE_DOCUMENT_INDEX_PASS",
                "Workspace document index was built through bounded read-only discovery.",
                Severity.INFO,
                metadata={"workspace_id": context.active_workspace_id, "matching_total": len(filtered)},
            )
        )
        return CommandResult(
            command="workspace documents list",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Workspace documents were indexed without filesystem mutation.",
            data={
                "summary": summary,
                "nodes": [node.to_dict() for node in page],
                "ui_workspace_context": context.summary(),
                "safety": _safety(),
            },
            findings=findings,
        )

    def read_document(self, document_id: str) -> CommandResult:
        context, failure = self._require_workspace_context("workspace.documents.read")
        if failure is not None:
            return failure
        assert context is not None
        resolved = self._resolve_document(context, document_id)
        if isinstance(resolved, CommandResult):
            return resolved
        path, node = resolved
        if not node.readable:
            return _blocked(
                "workspace documents read",
                "WORKSPACE_DOCUMENT_SIZE_LIMIT_BLOCK",
                "Document exceeds the inline read budget.",
                path=node.relative_path,
                metadata={"size_bytes": node.size_bytes, "maximum_inline_bytes": MAX_INLINE_BYTES},
            )
        try:
            raw = _read_bytes_no_follow(path, maximum_bytes=MAX_INLINE_BYTES)
        except ValueError as exc:
            return _blocked("workspace documents read", "WORKSPACE_DOCUMENT_SAFE_OPEN_BLOCK", str(exc), path=node.relative_path)
        except OSError as exc:
            return _error("workspace documents read", "WORKSPACE_DOCUMENT_READ_ERROR", "Document could not be read.", path=node.relative_path, metadata={"exception_type": exc.__class__.__name__})
        if len(raw) > MAX_INLINE_BYTES:
            return _blocked("workspace documents read", "WORKSPACE_DOCUMENT_SIZE_LIMIT_BLOCK", "Document exceeds the inline read budget.", path=node.relative_path)
        if b"\x00" in raw:
            return _blocked("workspace documents read", "WORKSPACE_DOCUMENT_BINARY_BLOCK", "Binary-like content is not permitted in the document viewer.", path=node.relative_path)
        try:
            content = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            return _blocked("workspace documents read", "WORKSPACE_DOCUMENT_ENCODING_BLOCK", "Only UTF-8 text documents are permitted.", path=node.relative_path)

        findings: list[Finding] = list(context.findings)
        structured: Any = None
        parse_status = "not-applicable"
        if node.extension == ".json":
            try:
                structured = json.loads(content)
                parse_status = "valid"
            except json.JSONDecodeError as exc:
                parse_status = "invalid"
                findings.append(Finding("WORKSPACE_DOCUMENT_JSON_PARSE_WARNING", "JSON content could not be parsed; raw safe text remains available.", Severity.WARNING, path=node.relative_path, metadata={"line": exc.lineno, "column": exc.colno}))
        data = {
            "summary": {
                "workspace_id": context.active_workspace_id,
                "document_id": document_id,
                "content_type": _content_type(node.extension or ""),
                "parse_status": parse_status,
                "read_only": True,
                "mutations_performed": False,
            },
            "document": {
                **node.to_dict(),
                "sha256": sha_bytes(raw),
                "encoding": "utf-8",
                "content": content,
                "structured": structured,
                "breadcrumbs": _breadcrumbs(node.relative_path, context.active_workspace_id or "workspace"),
            },
            "ui_workspace_context": context.summary(),
            "safety": _safety(),
        }
        findings.append(Finding("WORKSPACE_DOCUMENT_READ_PASS", "Document content was read from the active workspace without mutation.", Severity.INFO, path=node.relative_path))
        return CommandResult("workspace documents read", True, ExitCode.PASS, "Workspace document was read successfully.", data=data, findings=findings)

    def document_metadata(self, document_id: str) -> CommandResult:
        context, failure = self._require_workspace_context("workspace.documents.metadata")
        if failure is not None:
            return failure
        assert context is not None
        resolved = self._resolve_document(context, document_id)
        if isinstance(resolved, CommandResult):
            return resolved
        path, node = resolved
        if not node.readable:
            return _blocked("workspace documents metadata", "WORKSPACE_DOCUMENT_SIZE_LIMIT_BLOCK", "Document exceeds the metadata hash budget.", path=node.relative_path, metadata={"size_bytes": node.size_bytes, "maximum_inline_bytes": MAX_INLINE_BYTES})
        try:
            raw = _read_bytes_no_follow(path, maximum_bytes=MAX_INLINE_BYTES)
        except ValueError as exc:
            return _blocked("workspace documents metadata", "WORKSPACE_DOCUMENT_SAFE_OPEN_BLOCK", str(exc), path=node.relative_path)
        except OSError as exc:
            return _error("workspace documents metadata", "WORKSPACE_DOCUMENT_METADATA_ERROR", "Document metadata could not be calculated.", path=node.relative_path, metadata={"exception_type": exc.__class__.__name__})
        metadata = {
            **node.to_dict(),
            "sha256": sha_bytes(raw),
            "encoding": "utf-8" if _utf8_decodable(raw) else "unsupported",
            "breadcrumbs": _breadcrumbs(node.relative_path, context.active_workspace_id or "workspace"),
        }
        return CommandResult(
            "workspace documents metadata",
            True,
            ExitCode.PASS,
            "Workspace document metadata is available.",
            data={"summary": {"workspace_id": context.active_workspace_id, "read_only": True, "mutations_performed": False}, "document": metadata, "ui_workspace_context": context.summary(), "safety": _safety()},
            findings=list(context.findings) + [Finding("WORKSPACE_DOCUMENT_METADATA_PASS", "Document metadata was calculated without mutation.", Severity.INFO, path=node.relative_path)],
        )

    def _require_workspace_context(self, command: str) -> tuple[UiWorkspaceContext | None, CommandResult | None]:
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or context.active_workspace_root is None:
            return None, _blocked(
                command,
                "WORKSPACE_DOCUMENT_CONTEXT_REQUIRED_BLOCK",
                "An explicit valid active workspace context is required for document browsing.",
                metadata={"context": context.summary()},
                findings=list(context.findings),
            )
        decision = self.path_guard.evaluate(context.active_workspace_root, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return None, _blocked(command, "WORKSPACE_DOCUMENT_ROOT_BLOCK", decision.reason, metadata=decision.metadata)
        return context, None

    def _resolve_document(self, context: UiWorkspaceContext, document_id: str) -> tuple[Path, WorkspaceDocumentNode] | CommandResult:
        if not isinstance(document_id, str) or not document_id.startswith(DOCUMENT_ID_PREFIX) or len(document_id) > 128:
            return _blocked("workspace documents read", "WORKSPACE_DOCUMENT_ID_BLOCK", "Document identifier is invalid or not opaque.")
        nodes, _, _ = self._discover(context)
        candidate = next((node for node in nodes if node.kind == "document" and node.node_id == document_id), None)
        if candidate is None:
            return CommandResult(
                "workspace documents read",
                False,
                ExitCode.FAIL,
                "Document identifier was not found in the active workspace index.",
                data={"summary": {"document_id": document_id, "read_only": True, "mutations_performed": False}},
                findings=[Finding("WORKSPACE_DOCUMENT_NOT_FOUND", "Opaque document identifier is unknown in the active workspace.", Severity.FAIL)],
            )
        root = context.active_workspace_root
        assert root is not None
        path = root / PurePosixPath(candidate.relative_path)
        safe = self._validate_file_path(root, path)
        if safe is not None:
            return safe
        return path, candidate

    def _discover(self, context: UiWorkspaceContext) -> tuple[list[WorkspaceDocumentNode], list[Finding], dict[str, Any]]:
        root = context.active_workspace_root
        assert root is not None
        workspace_id = context.active_workspace_id or root.name
        nodes: list[WorkspaceDocumentNode] = []
        findings: list[Finding] = []
        files_seen = 0
        folders_seen = 0
        skipped_denied = 0
        skipped_links = 0
        budget_exhausted = False

        stack: list[tuple[Path, str, int, str | None]] = [(root, "", 0, None)]
        while stack:
            directory, relative_dir, depth, parent_id = stack.pop()
            if depth > MAX_DISCOVERY_DEPTH:
                budget_exhausted = True
                continue
            try:
                entries = sorted(os.scandir(directory), key=lambda item: (not item.is_dir(follow_symlinks=False), item.name.lower()))
            except OSError as exc:
                findings.append(Finding("WORKSPACE_DOCUMENT_DIRECTORY_READ_WARNING", "A directory could not be inspected and was skipped.", Severity.WARNING, path=relative_dir or ".", metadata={"exception_type": exc.__class__.__name__}))
                continue
            for entry in reversed(entries):
                name = entry.name
                relative = f"{relative_dir}/{name}".strip("/").replace("\\", "/")
                if _is_denied_path(relative, is_dir=entry.is_dir(follow_symlinks=False)):
                    skipped_denied += 1
                    continue
                if _is_link_or_reparse(entry.path):
                    skipped_links += 1
                    findings.append(Finding("WORKSPACE_DOCUMENT_LINK_SKIPPED", "Symlink, junction or reparse-point entry was excluded from read-only discovery.", Severity.WARNING, path=relative))
                    continue
                if entry.is_dir(follow_symlinks=False):
                    folder_id = _opaque_id(FOLDER_ID_PREFIX, workspace_id, relative)
                    nodes.append(WorkspaceDocumentNode(folder_id, "folder", name, relative, parent_id, None, _category(relative, True), None, _mtime(entry), True))
                    folders_seen += 1
                    stack.append((Path(entry.path), relative, depth + 1, folder_id))
                    continue
                if not entry.is_file(follow_symlinks=False):
                    continue
                extension = Path(name).suffix.lower()
                if extension not in ALLOWED_EXTENSIONS:
                    continue
                files_seen += 1
                if files_seen > MAX_DISCOVERY_FILES:
                    budget_exhausted = True
                    break
                try:
                    size = entry.stat(follow_symlinks=False).st_size
                except OSError:
                    size = None
                readable = size is not None and size <= MAX_INLINE_BYTES
                nodes.append(
                    WorkspaceDocumentNode(
                        _opaque_id(DOCUMENT_ID_PREFIX, workspace_id, relative),
                        "document",
                        name,
                        relative,
                        parent_id,
                        extension,
                        _category(relative, False),
                        size,
                        _mtime(entry),
                        readable,
                        None if readable else "size-limit",
                    )
                )
            if budget_exhausted:
                break
        nodes.sort(key=lambda node: (node.relative_path.lower(), node.kind))
        if budget_exhausted:
            findings.append(Finding("WORKSPACE_DOCUMENT_DISCOVERY_BUDGET_WARNING", "Document discovery reached its bounded depth/file budget.", Severity.WARNING, metadata={"maximum_files": MAX_DISCOVERY_FILES, "maximum_depth": MAX_DISCOVERY_DEPTH}))
        return nodes, findings, {
            "discovered_files_total": files_seen,
            "discovered_folders_total": folders_seen,
            "skipped_denied_total": skipped_denied,
            "skipped_links_total": skipped_links,
            "discovery_budget_exhausted": budget_exhausted,
            "maximum_discovery_files": MAX_DISCOVERY_FILES,
            "maximum_discovery_depth": MAX_DISCOVERY_DEPTH,
        }

    def _validate_file_path(self, root: Path, path: Path) -> CommandResult | None:
        try:
            absolute = path.absolute()
            absolute.relative_to(root.absolute())
        except ValueError:
            return _blocked("workspace documents read", "WORKSPACE_DOCUMENT_PATH_ESCAPE_BLOCK", "Resolved document path escaped the active workspace root.")
        if not path.is_file() or _is_link_or_reparse(path):
            return _blocked("workspace documents read", "WORKSPACE_DOCUMENT_LINK_OR_MISSING_BLOCK", "Document is missing or resolves through a link/reparse point.")
        for parent in [path, *path.parents]:
            if parent == root.parent:
                break
            if parent != root and _is_link_or_reparse(parent):
                return _blocked("workspace documents read", "WORKSPACE_DOCUMENT_ANCESTOR_LINK_BLOCK", "Document path contains a symlink, junction or reparse-point ancestor.")
            if parent == root:
                break
        decision = self.path_guard.evaluate(path, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return _blocked("workspace documents read", "WORKSPACE_DOCUMENT_PATHGUARD_BLOCK", decision.reason, metadata=decision.metadata)
        return None



def _read_bytes_no_follow(path: Path, *, maximum_bytes: int) -> bytes:
    """Read a regular file through a descriptor and reject link-swap races.

    `O_NOFOLLOW` is used where the host exposes it. On Windows, where Python
    does not provide a portable FILE_FLAG_OPEN_REPARSE_POINT mapping through
    `os.open`, the pre/post lstat and descriptor identity comparison detects a
    path replacement between validation and open. Reads are bounded to one byte
    beyond the configured budget.
    """
    before = os.lstat(path)
    if _is_link_or_reparse(path) or not stat.S_ISREG(before.st_mode):
        raise ValueError("Document path is not a regular no-follow file.")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        after = os.lstat(path)
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError("Opened document is not a regular file.")
        before_identity = (getattr(before, "st_dev", None), getattr(before, "st_ino", None))
        opened_identity = (getattr(opened, "st_dev", None), getattr(opened, "st_ino", None))
        after_identity = (getattr(after, "st_dev", None), getattr(after, "st_ino", None))
        if before_identity != opened_identity or opened_identity != after_identity:
            raise ValueError("Document changed identity during safe read.")
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _opaque_id(prefix: str, workspace_id: str, relative_path: str) -> str:
    payload = f"uoc-001\x00{workspace_id}\x00{relative_path}".encode("utf-8")
    token = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()[:18]).decode("ascii").rstrip("=")
    return f"{prefix}{token}"


def _normalize_extension(value: str | None) -> str:
    value = str(value or "").strip().lower()
    if not value:
        return ""
    return value if value.startswith(".") else f".{value}"


def _is_denied_path(relative: str, *, is_dir: bool) -> bool:
    path = PurePosixPath(relative)
    parts = path.parts
    lowered = [part.lower() for part in parts]
    if any(part in DENIED_DIRECTORY_NAMES for part in lowered):
        return True
    if path.name.lower() in DENIED_FILE_NAMES or path.name.lower().startswith(".env"):
        return True
    normalized = relative.replace("\\", "/").lower()
    if parts and parts[0].lower() == ".devpilot":
        if is_dir and normalized == ".devpilot":
            return False
        if normalized != ".devpilot/project.yaml":
            return True
    if ":" in path.name:  # Windows Alternate Data Stream syntax
        return True
    return False


def _is_link_or_reparse(path: str | Path) -> bool:
    candidate = Path(path)
    try:
        if candidate.is_symlink():
            return True
        st = os.lstat(candidate)
    except OSError:
        return False
    attributes = getattr(st, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def _mtime(entry: os.DirEntry[str]) -> str | None:
    try:
        value = entry.stat(follow_symlinks=False).st_mtime
    except OSError:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _category(relative: str, is_dir: bool) -> str:
    lower = relative.lower()
    name = PurePosixPath(lower).name
    if "adr" in PurePosixPath(lower).parts or name.startswith("adr_") or name.startswith("adr-"):
        return "adr"
    if "requirement" in lower or "requisito" in lower:
        return "requirements"
    if "architecture" in lower or "arquitect" in lower:
        return "architecture"
    if "security" in lower or "threat" in lower or "risk" in lower:
        return "security"
    if "test" in lower or "quality" in lower:
        return "quality"
    if "vision" in lower or "scope" in lower or "product" in lower or "mvp" in lower:
        return "product"
    if is_dir:
        return "folder"
    return "documentation"


def _content_type(extension: str) -> str:
    return {
        ".md": "text/markdown",
        ".json": "application/json",
        ".yaml": "application/yaml",
        ".yml": "application/yaml",
        ".txt": "text/plain",
    }.get(extension, "text/plain")


def _breadcrumbs(relative_path: str, workspace_id: str) -> list[dict[str, str | None]]:
    items: list[dict[str, str | None]] = [{"label": workspace_id, "relative_path": None}]
    current: list[str] = []
    for part in PurePosixPath(relative_path).parts:
        current.append(part)
        items.append({"label": part, "relative_path": "/".join(current)})
    return items


def _utf8_decodable(raw: bytes) -> bool:
    try:
        raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return False
    return True


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safety() -> dict[str, Any]:
    return {
        "read_only": True,
        "mutations_performed": False,
        "source_mutations_performed": False,
        "network_used": False,
        "external_api_used": False,
        "remote_execution_enabled": False,
        "connector_write_enabled": False,
        "plugin_execution_enabled": False,
        "absolute_paths_accepted_from_browser": False,
        "symlink_junction_following_enabled": False,
        "symlink_following": False,
    }


def _blocked(command: str, finding_id: str, message: str, *, path: str | None = None, metadata: dict[str, Any] | None = None, findings: list[Finding] | None = None) -> CommandResult:
    items = list(findings or [])
    items.append(Finding(finding_id, message, Severity.BLOCK, path=path, metadata=metadata or {}))
    return CommandResult(command, False, ExitCode.BLOCK, message, data={"summary": {"read_only": True, "mutations_performed": False}, "safety": _safety()}, findings=items)


def _error(command: str, finding_id: str, message: str, *, path: str | None = None, metadata: dict[str, Any] | None = None) -> CommandResult:
    return CommandResult(command, False, ExitCode.ERROR, message, data={"summary": {"read_only": True, "mutations_performed": False}, "safety": _safety()}, findings=[Finding(finding_id, message, Severity.ERROR, path=path, metadata=metadata or {})])
