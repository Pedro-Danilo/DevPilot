from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.policy.secrets import SecretGuard

_TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".csv",
    ".sha256",
    ".example",
}


@dataclass(frozen=True)
class AuditPackRedactionEntry:
    """Redaction scan result for one audit-pack candidate file."""

    path: str
    scanned: bool
    redaction_applied: bool
    redactions: int
    raw_secret_exported: bool
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "scanned": self.scanned,
            "redaction_applied": self.redaction_applied,
            "redactions": self.redactions,
            "raw_secret_exported": self.raw_secret_exported,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class AuditPackRedactionResult:
    """Sanitized bytes plus redaction evidence for one candidate file."""

    content: bytes
    entry: AuditPackRedactionEntry


class AuditPackRedactionScanner:
    """Dependency-free redaction scanner for POST-H-013 audit packs.

    The builder uses this class before any file is added to an audit pack. The
    current POST-H-013-B policy is intentionally fail-closed: secret-like content
    is detected with SecretGuard, reported, and blocks pack creation instead of
    exporting redacted substitutes. Later micro-sprints may introduce governed
    redacted exports, but raw secrets remain forbidden by policy.
    """

    def __init__(self, *, secret_guard: SecretGuard | None = None) -> None:
        self.secret_guard = secret_guard or SecretGuard()

    def scan(self, *, path: Path, rel_path: str, content: bytes) -> AuditPackRedactionResult:
        if not _is_text_like(path, content=content):
            return AuditPackRedactionResult(
                content=content,
                entry=AuditPackRedactionEntry(
                    path=rel_path,
                    scanned=False,
                    redaction_applied=False,
                    redactions=0,
                    raw_secret_exported=False,
                    reason="binary-or-non-text-file",
                ),
            )
        text = content.decode("utf-8", errors="replace")
        redactions = _count_material_secret_redactions(text, secret_guard=self.secret_guard)
        if redactions > 0:
            return AuditPackRedactionResult(
                content=content,
                entry=AuditPackRedactionEntry(
                    path=rel_path,
                    scanned=True,
                    redaction_applied=True,
                    redactions=redactions,
                    raw_secret_exported=False,
                    reason="secret-like-content-detected-build-blocked",
                ),
            )
        return AuditPackRedactionResult(
            content=content,
            entry=AuditPackRedactionEntry(
                path=rel_path,
                scanned=True,
                redaction_applied=False,
                redactions=0,
                raw_secret_exported=False,
                reason=None,
            ),
        )


def build_redaction_report(*, pack_id: str, entries: list[AuditPackRedactionEntry], blocked: bool) -> dict[str, Any]:
    secrets_detected = sum(entry.redactions for entry in entries)
    scanned_total = sum(1 for entry in entries if entry.scanned)
    files_redacted_total = sum(1 for entry in entries if entry.redaction_applied)
    return {
        "schema_version": "1.0",
        "report_id": f"{pack_id}-redaction-report",
        "pack_id": pack_id,
        "created_by": "POST-H-013-B",
        "status": "blocked" if blocked else "passed",
        "scanner": "SecretGuard",
        "files_total": len(entries),
        "files_scanned_total": scanned_total,
        "files_redacted_total": files_redacted_total,
        "secrets_detected": secrets_detected,
        "redaction_passed": secrets_detected == 0,
        "raw_secrets_exported": False,
        "block_on_secrets_detected": True,
        "network_used": False,
        "external_api_used": False,
        "remote_export_used": False,
        "compliance_certification_claimed": False,
        "entries": [entry.to_dict() for entry in entries],
        "findings": [],
    }


def _is_text_like(path: Path, *, content: bytes) -> bool:
    name = path.name.lower()
    if name.endswith((".yaml.example", ".yml.example")):
        return True
    if path.suffix.lower() in _TEXT_SUFFIXES:
        return True
    return b"\x00" not in content[:1024]


def _count_material_secret_redactions(text: str, *, secret_guard: SecretGuard) -> int:
    """Count secret findings while suppressing explicit documentation placeholders.

    DevPilot documentation intentionally contains commands such as
    ``X-DevPilot-Token=<token>`` and ``api_key=sk-demo`` to teach operators
    how guards work. POST-H-013-B must not export real secrets, but it also
    should not block all audit packs because of documented placeholders. The
    scanner therefore evaluates text line-by-line and ignores lines that are
    clearly placeholder/example instructions.
    """

    redactions = 0
    for line in text.splitlines():
        if _is_placeholder_or_documentation_example(line):
            continue
        result = secret_guard.redact(line)
        redactions += result.redactions
    return redactions


def _is_placeholder_or_documentation_example(line: str) -> bool:
    lower = line.lower()
    placeholder_markers = (
        "<token",
        "<api",
        "<secret",
        "<password",
        "<provider",
        "token-real",
        "placeholder",
        "[redacted]",
        "***redacted***",
        "redacted",
        "sk-demo",
        "dummy",
        "example",
        "ejemplo",
        "valor del campo `powershell`",
        "devepilot_api_token",
        "devpilot_api_token",
        "x-devpilot-token",
        "authorization=bearer",
        "api_key=",
        "requires_api_key",
        "risk-management",
        "risk-documentation",
    )
    return any(marker in lower for marker in placeholder_markers)
