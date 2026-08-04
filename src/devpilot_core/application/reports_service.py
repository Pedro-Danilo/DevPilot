from __future__ import annotations

import base64
import json
import os
import re
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import redact_sensitive_data, redact_string

from .ui_workspace_context import UiWorkspaceContextResolver

_REPORT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")
_SUPPORTED_FORMATS = {"json", "markdown", "md"}
_MAX_TEXT_CHARS = 20000
_MAX_DISCOVERY_FILES = 2500
_MAX_DISCOVERY_DEPTH = 6
_MAX_SUMMARY_PARSE_FILES = 300
_MAX_SUMMARY_JSON_BYTES = 1_000_000
_REPORT_ID_PREFIX = "rpt_"


@dataclass(frozen=True)
class _ReportSource:
    scope: str
    root: Path
    workspace_id: str | None = None


@dataclass
class _ReportGroup:
    source: _ReportSource
    relative_stem: str
    formats: dict[str, Path]
    modified_at: str
    size_bytes: int

    @property
    def report_id(self) -> str:
        return _encode_report_id(self.source.scope, self.relative_stem)


class ReportsApplicationService:
    """Read-only evidence report facade for API/UI viewers.

    The service supports bounded recursive discovery, nested report identifiers,
    multiple governed local roots (platform plus an explicitly configured active
    workspace), stable pagination and lazy JSON summary parsing. Browser clients
    never receive direct filesystem access and all payloads remain redacted.
    """

    def __init__(
        self,
        root: Path,
        *,
        reports_dir: str | Path = "outputs/reports",
        context_resolver: UiWorkspaceContextResolver | None = None,
    ) -> None:
        self.root = root.resolve()
        self.reports_dir = self._resolve_reports_dir(reports_dir)
        self.context_resolver = context_resolver or UiWorkspaceContextResolver(self.root)

    def list_reports(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        severity: str | None = None,
        status: str | None = None,
        command: str | None = None,
        query: str | None = None,
        scope: str | None = None,
    ) -> CommandResult:
        started = time.perf_counter()
        safe_limit = _safe_limit(limit, cap=200)
        safe_offset = _safe_offset(offset, cap=10000)
        severity_filter = _normalize_filter(severity)
        status_filter = _normalize_filter(status)
        command_filter = _normalize_filter(command)
        query_filter = _normalize_filter(query)
        scope_filter = _normalize_scope(scope)

        sources, context_findings = self._sources(scope_filter)
        groups, discovery = self._discover_groups(sources)
        groups.sort(key=lambda item: item.modified_at, reverse=True)

        if query_filter:
            groups = [
                group
                for group in groups
                if query_filter in group.relative_stem.lower()
                or query_filter in (group.source.workspace_id or "").lower()
                or query_filter in group.source.scope.lower()
            ]

        structured_filters = any((severity_filter, status_filter, command_filter))
        parsed_total = 0
        matching: list[dict[str, Any]] = []
        findings: list[Finding] = list(context_findings)
        parse_budget_exhausted = False

        if structured_filters:
            candidates: Iterable[_ReportGroup] = groups
        else:
            candidates = groups[safe_offset : safe_offset + safe_limit]

        for group in candidates:
            parse_summary = structured_filters or len(matching) < safe_limit
            summary_loaded = False
            payload_summary: dict[str, Any] = {}
            if parse_summary and "json" in group.formats:
                if parsed_total >= _MAX_SUMMARY_PARSE_FILES:
                    parse_budget_exhausted = True
                else:
                    parsed_total += 1
                    json_path = group.formats["json"]
                    if json_path.stat().st_size <= _MAX_SUMMARY_JSON_BYTES:
                        payload_summary = _summarize_json_report(_load_json_safely(json_path))
                        summary_loaded = True

            item = self._group_to_item(group, payload_summary, summary_loaded=summary_loaded)
            if severity_filter and int(item.get("findings_by_severity", {}).get(severity_filter, 0)) <= 0:
                continue
            if status_filter and str(item.get("status", "")).lower() != status_filter:
                continue
            if command_filter and command_filter not in str(item.get("command", "")).lower():
                continue
            matching.append(item)
            if structured_filters and len(matching) >= safe_offset + safe_limit:
                break

        if structured_filters:
            bounded = matching[safe_offset : safe_offset + safe_limit]
            filtered_total = len(matching)
            filtered_total_exact = not parse_budget_exhausted and len(matching) < safe_offset + safe_limit
        else:
            bounded = matching
            filtered_total = len(groups)
            filtered_total_exact = True

        duration_ms = max(0, round((time.perf_counter() - started) * 1000))
        summary = {
            "reports_dir": self._relative(self.reports_dir),
            "sources": [
                {
                    "scope": source.scope,
                    "workspace_id": source.workspace_id,
                    "root": self._relative_or_absolute(source.root),
                    "exists": source.root.is_dir(),
                }
                for source in sources
            ],
            "scope": scope_filter,
            "reports_total": len(groups),
            "filtered_total": filtered_total,
            "filtered_total_exact": filtered_total_exact,
            "returned_total": len(bounded),
            "limit": safe_limit,
            "offset": safe_offset,
            "filters": {
                "severity": severity_filter,
                "status": status_filter,
                "command": command_filter,
                "query": query_filter,
                "scope": scope_filter,
            },
            "formats_supported": sorted(_SUPPORTED_FORMATS),
            "recursive_discovery": True,
            "max_depth": _MAX_DISCOVERY_DEPTH,
            "files_discovered_total": discovery["files_discovered_total"],
            "directories_scanned_total": discovery["directories_scanned_total"],
            "discovery_truncated": discovery["discovery_truncated"],
            "unsafe_entries_skipped_total": discovery["unsafe_entries_skipped_total"],
            "json_summaries_parsed_total": parsed_total,
            "summary_parse_budget_exhausted": parse_budget_exhausted,
            "duration_ms": duration_ms,
            "redacted": True,
            "preliminary": True,
            "network_used": False,
            "external_api_used": False,
            "filesystem_access": "api_service_only_outputs_reports",
            "filesystem_access_policy": "api_service_only_governed_report_roots",
            "workspace_context": self.context_resolver.resolve().summary(),
        }

        if discovery["discovery_truncated"]:
            findings.append(
                Finding(
                    id="REPORT_INDEX_DISCOVERY_TRUNCATED",
                    message="Report discovery reached its bounded file limit; refine scope or filters.",
                    severity=Severity.WARNING,
                    metadata={"max_files": _MAX_DISCOVERY_FILES},
                )
            )
        if parse_budget_exhausted:
            findings.append(
                Finding(
                    id="REPORT_INDEX_SUMMARY_BUDGET_EXHAUSTED",
                    message="Structured report filtering reached the bounded JSON summary budget.",
                    severity=Severity.WARNING,
                    metadata={"max_json_summaries": _MAX_SUMMARY_PARSE_FILES},
                )
            )
        if not any(source.root.exists() for source in sources):
            findings.append(
                Finding(
                    id="REPORT_INDEX_EMPTY",
                    message="No governed report directory exists yet; report index is empty.",
                    severity=Severity.INFO,
                    path=self._relative(self.reports_dir),
                )
            )
        elif not bounded:
            findings.append(
                Finding(
                    id="REPORT_INDEX_NO_MATCHES",
                    message="No reports matched the current filters.",
                    severity=Severity.INFO,
                    path=self._relative(self.reports_dir),
                )
            )
        return CommandResult(
            command="reports list",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local report index generated." if bounded else "No local reports found; empty report index generated.",
            data={"summary": summary, "reports": bounded, "preliminary": True},
            findings=findings,
        )

    def read_report(self, report_id: str, *, format: str = "json", max_chars: int = _MAX_TEXT_CHARS) -> CommandResult:
        safe_report_id = str(report_id or "").strip()
        safe_format = _normalize_format(format)
        safe_max_chars = _safe_limit(max_chars, cap=_MAX_TEXT_CHARS)
        decoded = _decode_report_id(safe_report_id)
        if decoded is None:
            return CommandResult(
                command="reports read",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Report id is invalid or attempts path traversal.",
                data={"summary": {"report_id": safe_report_id, "format": safe_format, "preliminary": True}},
                findings=[
                    Finding(
                        id="REPORT_ID_INVALID_BLOCK",
                        message="Report id must be a safe root basename or a server-issued nested report id.",
                        severity=Severity.BLOCK,
                        metadata={"report_id": safe_report_id},
                    )
                ],
            )
        scope, relative_stem = decoded
        source = next((item for item in self._all_sources() if item.scope == scope), None)
        if source is None:
            return self._not_found(safe_report_id, safe_format, path=f"unknown-scope:{scope}")

        extension = "md" if safe_format == "markdown" else safe_format
        path = self._resolve_report_file(source.root, relative_stem, extension)
        if path is None or not path.exists():
            return self._not_found(safe_report_id, safe_format, path=f"{source.scope}:{relative_stem}.{extension}")
        if extension == "json":
            payload = _load_json_safely(path)
            content: Any = redact_sensitive_data(payload)
            content_type = "application/json"
            truncated = False
        else:
            raw = path.read_text(encoding="utf-8", errors="replace")
            redacted = redact_string(raw)
            truncated = len(redacted) > safe_max_chars
            content = redacted[:safe_max_chars]
            content_type = "text/markdown"
        summary = {
            "report_id": safe_report_id,
            "relative_stem": relative_stem,
            "scope": source.scope,
            "workspace_id": source.workspace_id,
            "format": safe_format,
            "path": self._relative_or_absolute(path),
            "content_type": content_type,
            "truncated": truncated,
            "max_chars": safe_max_chars,
            "redacted": True,
            "preliminary": True,
            "network_used": False,
            "external_api_used": False,
        }
        return CommandResult(
            command="reports read",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local report loaded and redacted for API/UI consumption.",
            data={"summary": summary, "report": content, "preliminary": True},
            findings=[],
        )

    def _not_found(self, report_id: str, format: str, *, path: str) -> CommandResult:
        return CommandResult(
            command="reports read",
            ok=False,
            exit_code=ExitCode.FAIL,
            message="Report was not found in governed report roots.",
            data={"summary": {"report_id": report_id, "format": format, "found": False, "preliminary": True}},
            findings=[
                Finding(
                    id="REPORT_NOT_FOUND",
                    message="Requested report was not found in governed report roots.",
                    severity=Severity.WARNING,
                    path=path,
                )
            ],
        )

    def _sources(self, scope: str) -> tuple[list[_ReportSource], list[Finding]]:
        all_sources = self._all_sources()
        context = self.context_resolver.resolve()
        findings = list(context.findings)
        if scope == "platform":
            return [item for item in all_sources if item.scope == "platform"], findings
        if scope == "workspace":
            workspace = [item for item in all_sources if item.scope == "workspace"]
            if not workspace:
                findings.append(
                    Finding(
                        "REPORT_WORKSPACE_SCOPE_UNAVAILABLE",
                        "Workspace report scope was requested but no valid active workspace is configured.",
                        Severity.WARNING,
                    )
                )
            return workspace, findings
        return all_sources, findings

    def _all_sources(self) -> list[_ReportSource]:
        sources = [_ReportSource(scope="platform", root=self.reports_dir)]
        context = self.context_resolver.resolve()
        if context.valid and context.active_workspace_root and context.reports_root:
            if context.reports_root.resolve() != self.reports_dir.resolve():
                sources.append(
                    _ReportSource(
                        scope="workspace",
                        root=context.reports_root.resolve(),
                        workspace_id=context.active_workspace_id,
                    )
                )
        return sources

    def _discover_groups(self, sources: list[_ReportSource]) -> tuple[list[_ReportGroup], dict[str, int | bool]]:
        grouped: dict[tuple[str, str], _ReportGroup] = {}
        files_total = 0
        dirs_total = 0
        unsafe_total = 0
        truncated = False

        for source in sources:
            if not source.root.is_dir():
                continue
            for path, depth, event in _walk_report_files(source.root):
                if event == "dir":
                    dirs_total += 1
                    continue
                if event == "unsafe":
                    unsafe_total += 1
                    continue
                if files_total >= _MAX_DISCOVERY_FILES:
                    truncated = True
                    break
                files_total += 1
                relative = path.relative_to(source.root).as_posix()
                relative_stem = str(Path(relative).with_suffix("")).replace("\\", "/")
                key = (source.scope, relative_stem)
                fmt = "json" if path.suffix.lower() == ".json" else "markdown"
                current = grouped.get(key)
                stat = path.stat()
                modified = _mtime_iso_from_stat(stat.st_mtime)
                size = stat.st_size
                if current is None:
                    grouped[key] = _ReportGroup(
                        source=source,
                        relative_stem=relative_stem,
                        formats={fmt: path},
                        modified_at=modified,
                        size_bytes=size,
                    )
                else:
                    current.formats[fmt] = path
                    current.modified_at = max(current.modified_at, modified)
                    current.size_bytes += size
            if truncated:
                break
        return list(grouped.values()), {
            "files_discovered_total": files_total,
            "directories_scanned_total": dirs_total,
            "unsafe_entries_skipped_total": unsafe_total,
            "discovery_truncated": truncated,
        }

    def _group_to_item(self, group: _ReportGroup, payload_summary: dict[str, Any], *, summary_loaded: bool) -> dict[str, Any]:
        item: dict[str, Any] = {
            "report_id": group.report_id,
            "display_id": Path(group.relative_stem).name,
            "relative_stem": group.relative_stem,
            "relative_path": group.relative_stem,
            "scope": group.source.scope,
            "workspace_id": group.source.workspace_id,
            "nested": "/" in group.relative_stem,
            "depth": max(0, len(Path(group.relative_stem).parts) - 1),
            "formats": sorted(group.formats),
            "paths": {fmt: self._relative_or_absolute(path) for fmt, path in group.formats.items()},
            "modified_at": group.modified_at,
            "size_bytes": group.size_bytes,
            "summary_loaded": summary_loaded,
        }
        item.update(payload_summary)
        return _redact_report_summary(item)

    def _resolve_reports_dir(self, reports_dir: str | Path) -> Path:
        candidate = Path(reports_dir)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("ReportsApplicationService primary root must remain inside the DevPilot project root.") from exc
        return candidate

    def _resolve_report_file(self, source_root: Path, relative_stem: str, extension: str) -> Path | None:
        if not _is_safe_relative_stem(relative_stem):
            return None
        path = (source_root / f"{relative_stem}.{extension}").resolve()
        try:
            path.relative_to(source_root.resolve())
        except ValueError:
            return None
        if _is_link_or_junction(path):
            return None
        return path

    def _relative(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    def _relative_or_absolute(self, path: Path) -> str:
        return self._relative(path)


def _walk_report_files(root: Path) -> Iterable[tuple[Path, int, str]]:
    root = root.resolve()

    def walk(current: Path, depth: int) -> Iterable[tuple[Path, int, str]]:
        if depth > _MAX_DISCOVERY_DEPTH:
            return
        try:
            entries = sorted(os.scandir(current), key=lambda item: item.name.lower())
        except OSError:
            return
        for entry in entries:
            path = Path(entry.path)
            try:
                if entry.is_symlink():
                    yield path, depth, "unsafe"
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if _is_junction(path):
                        yield path, depth, "unsafe"
                        continue
                    yield path, depth, "dir"
                    if depth < _MAX_DISCOVERY_DEPTH:
                        yield from walk(path, depth + 1)
                elif entry.is_file(follow_symlinks=False) and path.suffix.lower() in {".json", ".md"}:
                    yield path, depth, "file"
            except OSError:
                yield path, depth, "unsafe"

    yield from walk(root, 0)


def _is_link_or_junction(path: Path) -> bool:
    try:
        return path.is_symlink() or _is_junction(path)
    except OSError:
        return True


def _is_junction(path: Path) -> bool:
    junction = getattr(path, "is_junction", None)
    return bool(junction and junction())


def _safe_limit(value: int | str | None, *, cap: int) -> int:
    try:
        parsed = int(value) if value is not None else cap
    except (TypeError, ValueError):
        parsed = cap
    return max(1, min(parsed, cap))


def _safe_offset(value: int | str | None, *, cap: int) -> int:
    try:
        parsed = int(value) if value is not None else 0
    except (TypeError, ValueError):
        parsed = 0
    return max(0, min(parsed, cap))


def _normalize_filter(value: str | None) -> str | None:
    normalized = str(value or "").strip().lower()
    return normalized or None


def _normalize_scope(value: str | None) -> str:
    normalized = str(value or "all").strip().lower()
    return normalized if normalized in {"all", "platform", "workspace"} else "all"


def _normalize_format(value: str | None) -> str:
    normalized = str(value or "json").strip().lower()
    if normalized == "md":
        return "markdown"
    return normalized if normalized in _SUPPORTED_FORMATS else "json"


def _encode_report_id(scope: str, relative_stem: str) -> str:
    if scope == "platform" and "/" not in relative_stem and _REPORT_ID_PATTERN.fullmatch(relative_stem):
        return relative_stem
    payload = f"{scope}:{relative_stem}".encode("utf-8")
    return _REPORT_ID_PREFIX + base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_report_id(value: str) -> tuple[str, str] | None:
    if not value:
        return None
    if value.startswith(_REPORT_ID_PREFIX):
        token = value[len(_REPORT_ID_PREFIX) :]
        try:
            padding = "=" * (-len(token) % 4)
            decoded = base64.urlsafe_b64decode(token + padding).decode("utf-8")
            scope, relative_stem = decoded.split(":", 1)
        except Exception:
            return None
        if scope not in {"platform", "workspace"} or not _is_safe_relative_stem(relative_stem):
            return None
        return scope, relative_stem
    if _REPORT_ID_PATTERN.fullmatch(value) and ".." not in Path(value).parts:
        return "platform", value
    return None


def _is_safe_relative_stem(value: str) -> bool:
    if not value or "\\" in value:
        return False
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return False
    return all(part not in {"", ".", ".."} for part in path.parts)


def _load_json_safely(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {"raw": payload}
    except Exception as exc:
        return {"parse_error": str(exc), "report_id": path.stem}


def _summarize_json_report(payload: dict[str, Any]) -> dict[str, Any]:
    findings = payload.get("findings") if isinstance(payload.get("findings"), list) else []
    severity_counts = Counter(
        str(finding.get("severity") or "info").lower()
        for finding in findings
        if isinstance(finding, dict)
    )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "command": redact_string(str(payload.get("command") or payload.get("operation") or "")),
        "status": str(payload.get("status") or payload.get("decision") or summary.get("status") or ""),
        "ok": bool(payload.get("ok", False)),
        "exit_code": payload.get("exit_code"),
        "message": redact_string(str(payload.get("message") or "")),
        "generated_at": str(payload.get("generated_at") or payload.get("generated_at_utc") or ""),
        "findings_total": len(findings),
        "findings_by_severity": dict(sorted(severity_counts.items())),
        "summary": redact_sensitive_data(summary),
        "parse_error": payload.get("parse_error"),
    }


def _redact_report_summary(report: dict[str, Any]) -> dict[str, Any]:
    payload = dict(report)
    if "formats" in payload:
        payload["formats"] = sorted(set(payload["formats"]))
    return redact_sensitive_data(payload)


def _mtime_iso_from_stat(st_mtime: float) -> str:
    return datetime.fromtimestamp(st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
