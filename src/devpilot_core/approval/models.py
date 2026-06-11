from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from devpilot_core.cli_models import Finding, Severity


class ApprovalStatus(str, Enum):
    """Allowed states for local human approval records."""

    REQUESTED = "requested"
    APPROVED = "approved"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"


APPROVAL_STATUSES = {status.value for status in ApprovalStatus}
TERMINAL_STATUSES = {ApprovalStatus.DENIED.value, ApprovalStatus.REVOKED.value, ApprovalStatus.EXPIRED.value}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_approval_id() -> str:
    return f"APPROVAL-{uuid.uuid4().hex[:12].upper()}"


def parse_utc_iso(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def is_expired(expires_at: str, *, now: str | None = None) -> bool:
    reference = parse_utc_iso(now) if now else datetime.now(timezone.utc)
    return parse_utc_iso(expires_at) <= reference


@dataclass(frozen=True)
class ApprovalRequest:
    """Input model for creating a local human approval request.

    Sprint 28 models approvals only. It does not authorize or execute critical
    actions. Later sprints bind this contract to PolicyEngine and tools.
    """

    subject: str
    tool_id: str
    action: str
    actor: str
    reason: str
    scope: dict[str, Any]
    expires_at: str
    metadata: dict[str, Any] = field(default_factory=dict)
    approval_id: str | None = None

    def validate(self) -> list[Finding]:
        findings: list[Finding] = []
        for field_name, value in (
            ("subject", self.subject),
            ("tool_id", self.tool_id),
            ("action", self.action),
            ("actor", self.actor),
            ("reason", self.reason),
            ("expires_at", self.expires_at),
        ):
            if not str(value or "").strip():
                findings.append(
                    Finding(
                        id="APPROVAL_REQUIRED_FIELD_MISSING",
                        message=f"Approval request requires field: {field_name}.",
                        severity=Severity.BLOCK,
                        metadata={"field": field_name},
                    )
                )
        if not isinstance(self.scope, dict) or not self.scope:
            findings.append(
                Finding(
                    id="APPROVAL_SCOPE_REQUIRED",
                    message="Approval request requires a non-empty scope.",
                    severity=Severity.BLOCK,
                    metadata={"field": "scope"},
                )
            )
        try:
            if self.expires_at:
                if is_expired(self.expires_at):
                    findings.append(
                        Finding(
                            id="APPROVAL_EXPIRY_IN_PAST",
                            message="Approval request expiration must be in the future.",
                            severity=Severity.BLOCK,
                            metadata={"expires_at": self.expires_at},
                        )
                    )
        except ValueError as exc:
            findings.append(
                Finding(
                    id="APPROVAL_EXPIRY_INVALID",
                    message="Approval request expiration must be an ISO-8601 datetime.",
                    severity=Severity.BLOCK,
                    metadata={"expires_at": self.expires_at, "error": str(exc)},
                )
            )
        return findings

    def to_record(self, *, approval_id: str | None = None, created_at: str | None = None) -> "ApprovalRecord":
        timestamp = created_at or utc_now_iso()
        return ApprovalRecord(
            approval_id=approval_id or self.approval_id or new_approval_id(),
            subject=self.subject,
            tool_id=self.tool_id,
            action=self.action,
            status=ApprovalStatus.REQUESTED.value,
            actor=self.actor,
            reason=self.reason,
            scope=dict(self.scope),
            created_at=timestamp,
            updated_at=timestamp,
            expires_at=self.expires_at,
            decision_at=None,
            decided_by=None,
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "subject": self.subject,
            "tool_id": self.tool_id,
            "action": self.action,
            "actor": self.actor,
            "reason": self.reason,
            "scope": self.scope,
            "expires_at": self.expires_at,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ApprovalDecision:
    """Input model for a controlled approval state transition."""

    approval_id: str
    status: str
    actor: str
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[Finding]:
        findings: list[Finding] = []
        if self.status not in APPROVAL_STATUSES:
            findings.append(
                Finding(
                    id="APPROVAL_STATUS_INVALID",
                    message="Approval decision status is not allowed.",
                    severity=Severity.BLOCK,
                    metadata={"status": self.status, "allowed": sorted(APPROVAL_STATUSES)},
                )
            )
        if not self.approval_id.strip():
            findings.append(Finding("APPROVAL_ID_REQUIRED", "Approval decision requires approval_id.", Severity.BLOCK))
        if not self.actor.strip():
            findings.append(Finding("APPROVAL_ACTOR_REQUIRED", "Approval decision requires actor.", Severity.BLOCK))
        if not self.reason.strip():
            findings.append(Finding("APPROVAL_REASON_REQUIRED", "Approval decision requires reason.", Severity.BLOCK))
        return findings

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "status": self.status,
            "actor": self.actor,
            "reason": self.reason,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ApprovalRecord:
    """Persisted approval record used by ApprovalStore and LocalStore."""

    approval_id: str
    subject: str
    tool_id: str
    action: str
    status: str
    actor: str
    reason: str
    scope: dict[str, Any]
    created_at: str
    updated_at: str
    expires_at: str
    decision_at: str | None = None
    decided_by: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[Finding]:
        findings: list[Finding] = []
        if not self.approval_id.strip():
            findings.append(Finding("APPROVAL_ID_REQUIRED", "Approval record requires an ID.", Severity.BLOCK))
        if self.status not in APPROVAL_STATUSES:
            findings.append(
                Finding(
                    "APPROVAL_STATUS_INVALID",
                    "Approval record has an invalid status.",
                    Severity.BLOCK,
                    metadata={"status": self.status, "allowed": sorted(APPROVAL_STATUSES)},
                )
            )
        if not self.scope:
            findings.append(Finding("APPROVAL_SCOPE_REQUIRED", "Approval record requires non-empty scope.", Severity.BLOCK))
        if not self.expires_at.strip():
            findings.append(Finding("APPROVAL_EXPIRY_REQUIRED", "Approval record requires expires_at.", Severity.BLOCK))
        else:
            try:
                parse_utc_iso(self.expires_at)
            except ValueError as exc:
                findings.append(
                    Finding(
                        "APPROVAL_EXPIRY_INVALID",
                        "Approval record expires_at must be ISO-8601.",
                        Severity.BLOCK,
                        metadata={"expires_at": self.expires_at, "error": str(exc)},
                    )
                )
        return findings

    @property
    def expired(self) -> bool:
        return is_expired(self.expires_at)

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "subject": self.subject,
            "tool_id": self.tool_id,
            "action": self.action,
            "status": self.status,
            "actor": self.actor,
            "reason": self.reason,
            "scope": self.scope,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "decision_at": self.decision_at,
            "decided_by": self.decided_by,
            "expired": self.expired,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApprovalRecord":
        return cls(
            approval_id=str(data.get("approval_id", "")),
            subject=str(data.get("subject", "")),
            tool_id=str(data.get("tool_id", "")),
            action=str(data.get("action", "")),
            status=str(data.get("status", "")),
            actor=str(data.get("actor", "")),
            reason=str(data.get("reason", "")),
            scope=dict(data.get("scope") or {}),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
            expires_at=str(data.get("expires_at", "")),
            decision_at=data.get("decision_at"),
            decided_by=data.get("decided_by"),
            metadata=dict(data.get("metadata") or {}),
        )
