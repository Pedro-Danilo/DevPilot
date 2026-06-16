from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.approval.models import ApprovalStatus
from devpilot_core.approval.service import ApprovalCliInput, ApprovalService
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity


class ApprovalApplicationService:
    """Application facade for local human approval workflow.

    FUNC-SPRINT-71 exposes the Fase B approval workflow to the secured local API
    and Web UI. It deliberately delegates persistence and transition rules to
    ApprovalService/ApprovalStore instead of reimplementing approval semantics in
    route handlers. The service is local-only and redaction-aware.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.service = ApprovalService(self.root)

    def list(self, *, status: str | None = None, tool_id: str | None = None, action: str | None = None, limit: int = 100) -> CommandResult:
        return self.service.list(status=status or None, tool_id=tool_id or None, action=action or None, limit=max(1, min(int(limit), 200)))

    def show(self, *, approval_id: str) -> CommandResult:
        return self.service.show(approval_id.strip())

    def request(
        self,
        *,
        tool_id: str,
        action: str,
        subject: str,
        actor: str,
        reason: str,
        scope: str | None = None,
        expires_at: str | None = None,
        ttl_minutes: int = 60,
    ) -> CommandResult:
        return self.service.request(
            ApprovalCliInput(
                tool_id=tool_id.strip(),
                action=action.strip(),
                subject=subject.strip(),
                actor=actor.strip() or "ui-local",
                reason=reason.strip() or "Requested from DevPilot Approval Center.",
                scope=scope,
                expires_at=expires_at,
                ttl_minutes=max(1, min(int(ttl_minutes), 24 * 60)),
                metadata={"source": "web-ui", "sprint": "FUNC-SPRINT-71", "api_only": True},
            )
        )

    def decide(self, *, approval_id: str, decision: str, actor: str, reason: str) -> CommandResult:
        normalized = decision.strip().lower()
        if normalized == ApprovalStatus.APPROVED.value:
            return self.service.approve(approval_id.strip(), actor=actor.strip() or "ui-local", reason=reason.strip() or "Approved from DevPilot Approval Center.")
        if normalized == ApprovalStatus.DENIED.value:
            return self.service.deny(approval_id.strip(), actor=actor.strip() or "ui-local", reason=reason.strip() or "Denied from DevPilot Approval Center.")
        if normalized == ApprovalStatus.REVOKED.value:
            return self.service.revoke(approval_id.strip(), actor=actor.strip() or "ui-local", reason=reason.strip() or "Revoked from DevPilot Approval Center.")
        return CommandResult(
            command="approval decide",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Approval decision is not supported by the UI/API contract.",
            data={"summary": {"updated": False, "decision": normalized, "preliminary": True}},
            findings=[Finding("APPROVAL_DECISION_UNSUPPORTED_BLOCK", "Only approve, deny and revoke decisions are supported.", Severity.BLOCK, metadata={"decision": normalized})],
        )
