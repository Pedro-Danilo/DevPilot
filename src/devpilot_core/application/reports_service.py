from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import redact_sensitive_data, redact_string

_REPORT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")
_SUPPORTED_FORMATS = {"json", "markdown", "md"}
_MAX_TEXT_CHARS = 20000


class ReportsApplicationService:
    """Read-only evidence report facade for API/UI viewers.

    FUNC-SPRINT-70 introduces this application-facing service to keep the Web UI
    away from direct filesystem access. It indexes and reads reports only under
    `outputs/reports`, applies stable limits, redacts sensitive payloads and
    returns CommandResult envelopes consumable by ApplicationService/API.
    """

    def __init__(self, root: Path, *, reports_dir: str | Path = "outputs/reports") -> None:
        self.root = root.resolve()
        self.reports_dir = self._resolve_reports_dir(reports_dir)

    def list_reports(
        self,
        *,
        limit: int = 50,
        severity: str | None = None,
        status: str | None = None,
        command: str | None = None,
    ) -> CommandResult:
        safe_limit = _safe_limit(limit, cap=200)
        severity_filter = _normalize_filter(severity)
        status_filter = _normalize_filter(status)
        command_filter = _normalize_filter(command)
        reports = [_redact_report_summary(report) for report in self._collect_reports()]
        if severity_filter:
            reports = [report for report in reports if int(report.get("findings_by_severity", {}).get(severity_filter, 0)) > 0]
        if status_filter:
            reports = [report for report in reports if str(report.get("status", "")).lower() == status_filter]
        if command_filter:
            reports = [report for report in reports if command_filter in str(report.get("command", "")).lower()]
        reports = sorted(reports, key=lambda item: str(item.get("generated_at") or item.get("modified_at") or ""), reverse=True)
        bounded = reports[:safe_limit]
        summary = {
            "reports_dir": self._relative(self.reports_dir),
            "reports_total": len(reports),
            "returned_total": len(bounded),
            "limit": safe_limit,
            "filters": {"severity": severity_filter, "status": status_filter, "command": command_filter},
            "formats_supported": sorted(_SUPPORTED_FORMATS),
            "redacted": True,
            "preliminary": True,
            "network_used": False,
            "external_api_used": False,
            "filesystem_access": "api_service_only_outputs_reports",
        }
        findings: list[Finding] = []
        if not self.reports_dir.exists():
            findings.append(Finding(id="REPORT_INDEX_EMPTY", message="No outputs/reports directory exists yet; report index is empty.", severity=Severity.INFO, path=self._relative(self.reports_dir)))
        elif not reports:
            findings.append(Finding(id="REPORT_INDEX_NO_MATCHES", message="No reports matched the current filters.", severity=Severity.INFO, path=self._relative(self.reports_dir)))
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
        if not _is_safe_report_id(safe_report_id):
            return CommandResult(
                command="reports read",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Report id is invalid or attempts path traversal.",
                data={"summary": {"report_id": safe_report_id, "format": safe_format, "preliminary": True}},
                findings=[Finding(id="REPORT_ID_INVALID_BLOCK", message="Report id must be a basename without path separators.", severity=Severity.BLOCK, metadata={"report_id": safe_report_id})],
            )
        extension = "md" if safe_format == "markdown" else safe_format
        path = self._resolve_report_file(safe_report_id, extension)
        if path is None or not path.exists():
            return CommandResult(
                command="reports read",
                ok=False,
                exit_code=ExitCode.FAIL,
                message="Report was not found in outputs/reports.",
                data={"summary": {"report_id": safe_report_id, "format": safe_format, "found": False, "preliminary": True}},
                findings=[Finding(id="REPORT_NOT_FOUND", message="Requested report was not found in outputs/reports.", severity=Severity.WARNING, path=f"outputs/reports/{safe_report_id}.{extension}")],
            )
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
            "format": safe_format,
            "path": self._relative(path),
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

    def _collect_reports(self) -> list[dict[str, Any]]:
        if not self.reports_dir.exists():
            return []
        grouped: dict[str, dict[str, Any]] = {}
        for path in self.reports_dir.glob("*"):
            if not path.is_file() or path.suffix.lower() not in {".json", ".md"}:
                continue
            try:
                path.resolve().relative_to(self.reports_dir.resolve())
            except ValueError:
                continue
            report_id = path.stem
            item = grouped.setdefault(report_id, {"report_id": report_id, "formats": [], "paths": {}})
            fmt = "json" if path.suffix.lower() == ".json" else "markdown"
            item["formats"].append(fmt)
            item["paths"][fmt] = self._relative(path)
            item["modified_at"] = max(str(item.get("modified_at") or ""), _mtime_iso(path))
            if fmt == "json":
                item.update(_summarize_json_report(_load_json_safely(path)))
        return list(grouped.values())

    def _resolve_reports_dir(self, reports_dir: str | Path) -> Path:
        candidate = Path(reports_dir)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("ReportsApplicationService only reads inside the DevPilot project root.") from exc
        return candidate

    def _resolve_report_file(self, report_id: str, extension: str) -> Path | None:
        path = (self.reports_dir / f"{report_id}.{extension}").resolve()
        try:
            path.relative_to(self.reports_dir.resolve())
        except ValueError:
            return None
        return path

    def _relative(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")


def _safe_limit(value: int | str | None, *, cap: int) -> int:
    try:
        parsed = int(value) if value is not None else cap
    except (TypeError, ValueError):
        parsed = cap
    return max(1, min(parsed, cap))


def _normalize_filter(value: str | None) -> str | None:
    normalized = str(value or "").strip().lower()
    return normalized or None


def _normalize_format(value: str | None) -> str:
    normalized = str(value or "json").strip().lower()
    if normalized == "md":
        return "markdown"
    return normalized if normalized in _SUPPORTED_FORMATS else "json"


def _is_safe_report_id(value: str) -> bool:
    return bool(value) and "/" not in value and "\\" not in value and ".." not in Path(value).parts and bool(_REPORT_ID_PATTERN.match(value))


def _load_json_safely(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {"raw": payload}
    except Exception as exc:
        return {"parse_error": str(exc), "report_id": path.stem}


def _summarize_json_report(payload: dict[str, Any]) -> dict[str, Any]:
    findings = payload.get("findings") if isinstance(payload.get("findings"), list) else []
    severity_counts = Counter(str(finding.get("severity") or "info").lower() for finding in findings if isinstance(finding, dict))
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "command": str(payload.get("command") or ""),
        "status": str(payload.get("status") or ""),
        "ok": bool(payload.get("ok", False)),
        "exit_code": payload.get("exit_code"),
        "message": redact_string(str(payload.get("message") or "")),
        "generated_at": str(payload.get("generated_at") or ""),
        "findings_total": len(findings),
        "findings_by_severity": dict(sorted(severity_counts.items())),
        "summary": redact_sensitive_data(summary),
    }


def _redact_report_summary(report: dict[str, Any]) -> dict[str, Any]:
    payload = dict(report)
    if "formats" in payload:
        payload["formats"] = sorted(set(payload["formats"]))
    return redact_sensitive_data(payload)


def _mtime_iso(path: Path) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
