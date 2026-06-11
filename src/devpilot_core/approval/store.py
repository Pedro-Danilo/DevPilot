from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.observability import EventLogger, EventRecord
from devpilot_core.store import LocalStore

from .models import ApprovalDecision, ApprovalRecord, ApprovalRequest, ApprovalStatus, TERMINAL_STATUSES, is_expired, utc_now_iso


class ApprovalStore:
    """Operational approval persistence facade over LocalStore.

    Sprint 28 keeps this package deliberately small: it creates, lists and
    transitions approval records. It does not authorize PolicyEngine decisions
    and it never executes sensitive tools.
    """

    def __init__(self, root: Path, *, db_path: str | Path = ".devpilot/devpilot.db") -> None:
        self.root = root.resolve()
        self.local_store = LocalStore(self.root, db_path=db_path)
        self.events = EventLogger(self.root)

    def request(self, request: ApprovalRequest) -> CommandResult:
        findings = request.validate()
        if findings:
            return CommandResult(
                command="approval request",
                ok=False,
                exit_code=exit_code_for_findings(findings, default_ok=False),
                message="Approval request is invalid.",
                data={"request": request.to_dict(), "summary": {"created": False, "findings_total": len(findings)}},
                findings=findings,
            )

        record = request.to_record()
        created, stored = self.local_store.create_approval(record.to_dict())
        event_type = "approval.requested" if created else "approval.requested.idempotent"
        self._emit(event_type, stored, status=stored.status)
        return CommandResult(
            command="approval request",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Approval request persisted." if created else "Approval request already existed and was returned unchanged.",
            data={
                "approval": stored.to_dict(),
                "summary": {
                    "created": created,
                    "approvals_total": 1,
                    "status": stored.status,
                    "event_type": event_type,
                    "preliminary": True,
                },
            },
            findings=[
                Finding(
                    id="APPROVAL_REQUEST_PERSISTED" if created else "APPROVAL_REQUEST_IDEMPOTENT",
                    message="Approval record persisted with scope and expiration." if created else "Existing approval record was returned without overwrite.",
                    severity=Severity.INFO,
                    metadata={"approval_id": stored.approval_id, "status": stored.status},
                )
            ],
        )

    def list(self, *, status: str | None = None, tool_id: str | None = None, action: str | None = None) -> CommandResult:
        records = self.local_store.list_approvals(status=status, tool_id=tool_id, action=action)
        return CommandResult(
            command="approval list",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Approval records listed.",
            data={
                "approvals": [record.to_dict() for record in records],
                "summary": {
                    "approvals_total": len(records),
                    "status_filter": status,
                    "tool_id_filter": tool_id,
                    "action_filter": action,
                    "preliminary": True,
                },
            },
            findings=[],
        )

    def get(self, approval_id: str) -> ApprovalRecord | None:
        return self.local_store.get_approval(approval_id)

    def decide(self, decision: ApprovalDecision) -> CommandResult:
        findings = decision.validate()
        existing = self.get(decision.approval_id)
        if existing is None:
            findings.append(
                Finding(
                    id="APPROVAL_NOT_FOUND",
                    message="Approval record does not exist.",
                    severity=Severity.BLOCK,
                    metadata={"approval_id": decision.approval_id},
                )
            )
        elif existing.status in TERMINAL_STATUSES or existing.status == ApprovalStatus.APPROVED.value:
            findings.append(
                Finding(
                    id="APPROVAL_TRANSITION_INVALID",
                    message="Approval cannot be overwritten from its current state.",
                    severity=Severity.BLOCK,
                    metadata={"approval_id": decision.approval_id, "current_status": existing.status, "requested_status": decision.status},
                )
            )
        elif is_expired(existing.expires_at):
            findings.append(
                Finding(
                    id="APPROVAL_EXPIRED",
                    message="Expired approval cannot be approved or denied as active.",
                    severity=Severity.BLOCK,
                    metadata={"approval_id": decision.approval_id, "expires_at": existing.expires_at},
                )
            )

        if findings:
            return CommandResult(
                command="approval decide",
                ok=False,
                exit_code=exit_code_for_findings(findings, default_ok=False),
                message="Approval transition is invalid.",
                data={"decision": decision.to_dict(), "summary": {"updated": False, "findings_total": len(findings)}},
                findings=findings,
            )

        assert existing is not None
        updated = ApprovalRecord(
            approval_id=existing.approval_id,
            subject=existing.subject,
            tool_id=existing.tool_id,
            action=existing.action,
            status=decision.status,
            actor=existing.actor,
            reason=decision.reason,
            scope=existing.scope,
            created_at=existing.created_at,
            updated_at=utc_now_iso(),
            expires_at=existing.expires_at,
            decision_at=utc_now_iso(),
            decided_by=decision.actor,
            metadata={**existing.metadata, **decision.metadata},
        )
        stored = self.local_store.update_approval(updated.to_dict())
        event_type = f"approval.{stored.status}"
        self._emit(event_type, stored, status=stored.status)
        return CommandResult(
            command="approval decide",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Approval transition persisted.",
            data={
                "approval": stored.to_dict(),
                "summary": {"updated": True, "status": stored.status, "event_type": event_type, "preliminary": True},
            },
            findings=[
                Finding(
                    id="APPROVAL_TRANSITION_PERSISTED",
                    message="Approval transition was persisted as an audited event.",
                    severity=Severity.INFO,
                    metadata={"approval_id": stored.approval_id, "status": stored.status},
                )
            ],
        )

    def _emit(self, event_type: str, record: ApprovalRecord, *, status: str) -> None:
        try:
            self.events.emit(
                EventRecord(
                    event_type=event_type,
                    command="approval store",
                    status=status,
                    ok=True,
                    exit_code=0,
                    message="Approval event persisted.",
                    subject=record.subject,
                    summary={
                        "approval_id": record.approval_id,
                        "status": record.status,
                        "tool_id": record.tool_id,
                        "action": record.action,
                        "has_scope": bool(record.scope),
                        "expires_at": record.expires_at,
                    },
                    metadata={"component": "ApprovalStore", "sprint": "FUNC-SPRINT-28"},
                )
            )
            self.local_store.record_event(
                event_type=event_type,
                command="approval store",
                status=status,
                ok=True,
                exit_code=0,
                subject=record.subject,
                summary={"approval_id": record.approval_id, "status": record.status},
                metadata={"tool_id": record.tool_id, "action": record.action, "sprint": "FUNC-SPRINT-28"},
            )
        except Exception:
            # Approval persistence is already done at this point. Event/logging
            # hardening is intentionally best-effort until Fase B later sprints.
            return
