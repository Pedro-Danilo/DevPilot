from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import redact_sensitive_data

from .models import ApprovalDecision, ApprovalRequest, ApprovalStatus, parse_utc_iso
from .store import ApprovalStore


DEFAULT_APPROVAL_TTL_MINUTES = 60


def future_expiry_iso(minutes: int = DEFAULT_APPROVAL_TTL_MINUTES) -> str:
    """Return a UTC expiration timestamp for CLI-created approvals."""

    return (datetime.now(timezone.utc) + timedelta(minutes=max(1, minutes))).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_scope(scope: str | None, *, tool_id: str, action: str, subject: str) -> tuple[dict[str, Any], list[Finding]]:
    """Parse optional CLI scope JSON and fall back to a minimal safe scope.

    The Sprint 29 command examples do not include a `--scope` argument, but
    Sprint 28 made scope mandatory. To keep the CLI ergonomic without weakening
    the model, DevPilot derives a minimal scope from tool/action/subject and
    lets advanced users provide a JSON object to narrow it further.
    """

    derived_scope: dict[str, Any] = {"tool_id": tool_id, "action": action, "subject": subject}
    if scope is None or not scope.strip():
        return derived_scope, []
    try:
        parsed = json.loads(scope)
    except json.JSONDecodeError as exc:
        return derived_scope, [
            Finding(
                id="APPROVAL_SCOPE_JSON_INVALID",
                message="Approval scope must be a JSON object when provided through --scope.",
                severity=Severity.BLOCK,
                metadata={"error": str(exc)},
            )
        ]
    if not isinstance(parsed, dict) or not parsed:
        return derived_scope, [
            Finding(
                id="APPROVAL_SCOPE_JSON_INVALID",
                message="Approval scope must be a non-empty JSON object.",
                severity=Severity.BLOCK,
            )
        ]
    return {**derived_scope, **parsed}, []


def _redact_command_result(result: CommandResult) -> CommandResult:
    """Return a presentation-safe result without exposing raw secrets."""

    return CommandResult(
        command=result.command,
        ok=result.ok,
        exit_code=result.exit_code,
        message=result.message,
        data=redact_sensitive_data(result.data),
        findings=[
            Finding(
                id=finding.id,
                message=finding.message,
                severity=finding.severity,
                path=finding.path,
                metadata=redact_sensitive_data(finding.metadata),
            )
            for finding in result.findings
        ],
    )


@dataclass(frozen=True)
class ApprovalCliInput:
    """Normalized input for local approval CLI commands."""

    tool_id: str
    action: str
    subject: str
    actor: str
    reason: str
    scope: str | None = None
    expires_at: str | None = None
    ttl_minutes: int = DEFAULT_APPROVAL_TTL_MINUTES
    metadata: dict[str, Any] | None = None


class ApprovalService:
    """CLI-facing approval workflow service.

    FUNC-SPRINT-29 exposes the Sprint 28 approval domain through local CLI
    commands. This service deliberately does not bind approvals to PolicyEngine
    or execute tools; those controls belong to later Fase B sprints.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.store = ApprovalStore(self.root)

    def request(self, data: ApprovalCliInput) -> CommandResult:
        scope, findings = parse_scope(data.scope, tool_id=data.tool_id, action=data.action, subject=data.subject)
        expires_at = data.expires_at or future_expiry_iso(data.ttl_minutes)
        if data.expires_at:
            try:
                # Normalize and validate early so error metadata is clearer for CLI users.
                parse_utc_iso(data.expires_at)
            except ValueError as exc:
                findings.append(
                    Finding(
                        id="APPROVAL_EXPIRY_INVALID",
                        message="Approval expiration must be an ISO-8601 datetime.",
                        severity=Severity.BLOCK,
                        metadata={"expires_at": data.expires_at, "error": str(exc)},
                    )
                )
        if findings:
            return _redact_command_result(
                CommandResult(
                    command="approval request",
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message="Approval request is invalid.",
                    data={"summary": {"created": False, "findings_total": len(findings)}, "scope": scope},
                    findings=findings,
                )
            )
        result = self.store.request(
            ApprovalRequest(
                subject=data.subject,
                tool_id=data.tool_id,
                action=data.action,
                actor=data.actor,
                reason=data.reason,
                scope=scope,
                expires_at=expires_at,
                metadata={"source": "approval-cli", "sprint": "FUNC-SPRINT-29", **(data.metadata or {})},
            )
        )
        redacted = _redact_command_result(_rename_command(result, "approval request"))
        self._record_approval_observability(redacted, operation="request", subject=data.subject)
        return redacted

    def list(self, *, status: str | None = None, tool_id: str | None = None, action: str | None = None, limit: int = 100) -> CommandResult:
        result = self.store.list(status=status, tool_id=tool_id, action=action, limit=limit)
        return _redact_command_result(_rename_command(result, "approval list"))

    def show(self, approval_id: str) -> CommandResult:
        record = self.store.get(approval_id)
        if record is None:
            return CommandResult(
                command="approval show",
                ok=False,
                exit_code=ExitCode.FAIL,
                message="Approval record was not found.",
                data={"summary": {"found": False}, "approval_id": approval_id},
                findings=[
                    Finding(
                        id="APPROVAL_NOT_FOUND",
                        message="Approval record does not exist.",
                        severity=Severity.FAIL,
                        metadata={"approval_id": approval_id},
                    )
                ],
            )
        return _redact_command_result(
            CommandResult(
                command="approval show",
                ok=True,
                exit_code=ExitCode.PASS,
                message="Approval record loaded.",
                data={"approval": record.to_dict(), "summary": {"found": True, "status": record.status, "expired": record.expired, "preliminary": True}},
                findings=[],
            )
        )

    def approve(self, approval_id: str, *, actor: str, reason: str) -> CommandResult:
        return self._transition(approval_id, status=ApprovalStatus.APPROVED.value, actor=actor, reason=reason, command="approval approve")

    def deny(self, approval_id: str, *, actor: str, reason: str) -> CommandResult:
        return self._transition(approval_id, status=ApprovalStatus.DENIED.value, actor=actor, reason=reason, command="approval deny")

    def revoke(self, approval_id: str, *, actor: str, reason: str) -> CommandResult:
        return self._transition(approval_id, status=ApprovalStatus.REVOKED.value, actor=actor, reason=reason, command="approval revoke")

    def _transition(self, approval_id: str, *, status: str, actor: str, reason: str, command: str) -> CommandResult:
        result = self.store.decide(
            ApprovalDecision(
                approval_id=approval_id,
                status=status,
                actor=actor,
                reason=reason,
                metadata={"source": "approval-cli", "sprint": "FUNC-SPRINT-29", "command": command},
            )
        )
        redacted = _redact_command_result(_rename_command(result, command))
        self._record_approval_observability(redacted, operation=status, approval_id=approval_id)
        return redacted

    def _record_approval_observability(
        self,
        result: CommandResult,
        *,
        operation: str,
        approval_id: str | None = None,
        subject: str | None = None,
    ) -> None:
        """Record Sprint 60 approval workflow observability best-effort."""

        try:
            from devpilot_core.observability.agentops import AgentOpsInstrumentor

            AgentOpsInstrumentor(self.root).record_approval_result(
                result=result,
                operation=operation,
                approval_id=approval_id,
                subject=subject,
                metadata={"component": "ApprovalService", "payload_redacted": True},
            )
        except Exception:
            return


def _rename_command(result: CommandResult, command: str) -> CommandResult:
    return CommandResult(
        command=command,
        ok=result.ok,
        exit_code=result.exit_code,
        message=result.message,
        data=result.data,
        findings=result.findings,
    )
