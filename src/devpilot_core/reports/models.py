from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult


class ReportFormat(str, Enum):
    """Output formats supported by the local evidence contract."""

    JSON = "json"
    MARKDOWN = "markdown"


class ReportStatus(str, Enum):
    """Canonical status for persisted evidence reports."""

    PASS = "PASS"
    FAIL = "FAIL"
    BLOCK = "BLOCK"
    ERROR = "ERROR"


@dataclass(frozen=True)
class EvidenceReport:
    """Serializable evidence report produced from a DevPilot command result.

    The report is the stable audit envelope introduced in FUNC-SPRINT-06. It
    wraps the normalized `CommandResult` with reproducibility metadata:
    timestamp, report id, subject path, root-relative output paths and a compact
    summary. It is intentionally dependency-free and local-first.
    """

    report_id: str
    command: str
    status: ReportStatus
    ok: bool
    exit_code: int
    message: str
    generated_at: str
    findings: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)
    subject: str | None = None
    project_root: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_command_result(
        cls,
        result: CommandResult,
        *,
        report_id: str,
        generated_at: datetime | None = None,
        subject: str | Path | None = None,
        project_root: str | Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "EvidenceReport":
        """Create an evidence report from the common CLI result contract."""

        generated_at = generated_at or datetime.now(timezone.utc)
        status = status_from_result(result)
        data = result.data or {}
        summary = _extract_summary(data)
        return cls(
            report_id=report_id,
            command=result.command,
            status=status,
            ok=result.ok,
            exit_code=int(result.exit_code),
            message=result.message,
            generated_at=generated_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            findings=[finding.to_dict() for finding in result.findings],
            summary=summary,
            data=data,
            subject=str(subject).replace("\\", "/") if subject is not None else None,
            project_root=str(project_root).replace("\\", "/") if project_root is not None else None,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable representation."""

        payload: dict[str, Any] = {
            "report_id": self.report_id,
            "command": self.command,
            "status": self.status.value,
            "ok": self.ok,
            "exit_code": self.exit_code,
            "message": self.message,
            "generated_at": self.generated_at,
            "summary": self.summary,
            "findings": self.findings,
            "data": self.data,
        }
        if self.subject is not None:
            payload["subject"] = self.subject
        if self.project_root is not None:
            payload["project_root"] = self.project_root
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


def status_from_result(result: CommandResult) -> ReportStatus:
    """Map a CommandResult into the report status vocabulary."""

    if result.ok:
        return ReportStatus.PASS
    exit_code = int(result.exit_code)
    if exit_code == 2:
        return ReportStatus.BLOCK
    if exit_code == 3:
        return ReportStatus.ERROR
    return ReportStatus.FAIL


def _extract_summary(data: dict[str, Any]) -> dict[str, Any]:
    """Extract or derive a compact report summary from command data."""

    if isinstance(data.get("summary"), dict):
        return dict(data["summary"])
    if isinstance(data.get("data"), dict) and isinstance(data["data"].get("summary"), dict):
        return dict(data["data"]["summary"])

    summary: dict[str, Any] = {}
    if "path" in data:
        summary["path"] = data["path"]
    if "status" in data:
        summary["artifact_status"] = data["status"]
    if "strict" in data:
        summary["strict"] = data["strict"]
    if "has_frontmatter" in data:
        summary["has_frontmatter"] = data["has_frontmatter"]
    if "heading_count" in data:
        summary["heading_count"] = data["heading_count"]
    if "h1_count" in data:
        summary["h1_count"] = data["h1_count"]
    if "checks" in data and isinstance(data["checks"], list):
        summary["checks_total"] = len(data["checks"])
    return summary
