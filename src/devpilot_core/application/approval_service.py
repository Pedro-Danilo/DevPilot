from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.approval.authenticated_binding import AuthenticatedApprovalAuthority
from devpilot_core.approval.models import ApprovalDecision, ApprovalStatus
from devpilot_core.approval.service import ApprovalCliInput, ApprovalService
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.identity.auth_models import AuthenticatedPrincipal, SessionContext
from devpilot_core.identity.auth_store import LocalAuthStore


class ApprovalApplicationService:
    """Application facade for local human approval workflow.

    DEVPL-GSDLC-02-D adds authenticated request/decision methods. Legacy actor-
    based methods remain only for historical/internal compatibility and are not
    used by the current API authority path.
    """

    def __init__(self, root: Path, *, auth_store: LocalAuthStore | None = None) -> None:
        self.root = root.resolve()
        self.service = ApprovalService(self.root)
        self.auth_store = auth_store
        self._authority: AuthenticatedApprovalAuthority | None = None

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
        """Historical actor-based request path retained for non-current internals."""
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
                metadata={"source": "legacy-application", "api_only": False, "authority": "non-current"},
            )
        )

    def request_authenticated(
        self,
        *,
        principal: AuthenticatedPrincipal,
        session: SessionContext,
        tool_id: str,
        action: str,
        subject: str,
        caller_actor: str | None,
        reason: str,
        scope: str | None = None,
        expires_at: str | None = None,
        ttl_minutes: int = 60,
        workspace_id: str | None = None,
    ) -> CommandResult:
        if caller_actor and caller_actor.strip() and caller_actor.strip() != principal.actor_id:
            return self._block(
                "approval request",
                "APPROVAL_REQUEST_ACTOR_SPOOF_BLOCK",
                "Approval requester actor is derived from the authenticated session; caller actor cannot override it.",
                {"caller_actor": caller_actor, "authenticated_actor": principal.actor_id},
            )
        metadata={
            "source":"authenticated-api",
            "sprint":"DEVPL-GSDLC-02-D",
            "api_only":True,
            "workspace_id":workspace_id,
            **self._get_authority().request_metadata(principal,session,workspace_id=workspace_id),
        }
        return self.service.request(
            ApprovalCliInput(
                tool_id=tool_id.strip(),
                action=action.strip(),
                subject=subject.strip(),
                actor=principal.actor_id,
                reason=reason.strip() or "Requested from authenticated DevPilot Approval Center.",
                scope=scope,
                expires_at=expires_at,
                ttl_minutes=max(1,min(int(ttl_minutes),24*60)),
                metadata=metadata,
            )
        )

    def decide(self, *, approval_id: str, decision: str, actor: str, reason: str) -> CommandResult:
        """Historical actor-based decision path retained only for frozen tests/internal code."""
        normalized = decision.strip().lower()
        if normalized == ApprovalStatus.APPROVED.value:
            return self.service.approve(approval_id.strip(), actor=actor.strip() or "ui-local", reason=reason.strip() or "Approved from legacy application path.")
        if normalized == ApprovalStatus.DENIED.value:
            return self.service.deny(approval_id.strip(), actor=actor.strip() or "ui-local", reason=reason.strip() or "Denied from legacy application path.")
        if normalized == ApprovalStatus.REVOKED.value:
            return self.service.revoke(approval_id.strip(), actor=actor.strip() or "ui-local", reason=reason.strip() or "Revoked from legacy application path.")
        return self._block("approval decide","APPROVAL_DECISION_UNSUPPORTED_BLOCK","Approval decision is not supported.",{"decision":normalized})

    def decide_authenticated(
        self,
        *,
        approval_id: str,
        decision: str,
        principal: AuthenticatedPrincipal,
        session: SessionContext,
        caller_actor: str | None,
        reason: str,
    ) -> CommandResult:
        normalized=decision.strip().lower()
        if normalized not in {ApprovalStatus.APPROVED.value,ApprovalStatus.DENIED.value,ApprovalStatus.REVOKED.value}:
            return self._block("approval decide","APPROVAL_DECISION_UNSUPPORTED_BLOCK","Approval decision is not supported.",{"decision":normalized})
        record=self.service.store.get(approval_id.strip())
        if record is None:
            return self._block("approval decide","APPROVAL_NOT_FOUND","Approval record does not exist.",{"approval_id":approval_id})
        authority_service=self._get_authority()
        authority=authority_service.evaluate(record,principal=principal,session=session,decision=normalized,caller_actor=caller_actor)
        if not authority.allowed:
            return self._block(
                "approval decide",
                authority.reason_code,
                "Authenticated approval authority denied the requested decision.",
                {"approval_id":approval_id,"authority":authority.to_dict()},
            )
        metadata={
            "source":"authenticated-api",
            "sprint":"DEVPL-GSDLC-02-D",
            "caller_actor_authoritative":False,
            **authority_service.decision_metadata(authority,session),
        }
        scope_updates={
            "actor_id":principal.actor_id,
            "role_at_decision":authority.role_at_decision,
            "workspace_id":authority.workspace_id or record.scope.get("workspace_id"),
            "decision_session_binding_id":authority.session_binding_id,
            "approval_risk_level":authority.risk_level,
            "approval_domain":authority.domain,
            "approval_policy_refs":list(authority.policy_refs),
        }
        result=self.service.store.decide(
            ApprovalDecision(
                approval_id=approval_id.strip(),
                status=normalized,
                actor=principal.actor_id,
                reason=reason.strip() or f"{normalized} from authenticated Approval Center.",
                metadata=metadata,
                scope_updates=scope_updates,
            )
        )
        return result

    def _get_authority(self) -> AuthenticatedApprovalAuthority:
        """Load D-wave source policy only when an authenticated approval path needs it.

        Auth/session-only API tests and isolated runtime stores may intentionally
        omit source-controlled approval policy. Current approval mutations remain
        fail-closed because this loader raises if the matrix is absent.
        """
        if self._authority is None:
            self._authority = AuthenticatedApprovalAuthority(self.root, auth_store=self.auth_store)
        return self._authority

    @staticmethod
    def _block(command: str, finding_id: str, message: str, metadata: dict[str, Any]) -> CommandResult:
        return CommandResult(
            command=command,
            ok=False,
            exit_code=ExitCode.BLOCK,
            message=message,
            data={"summary":{"updated":False,"preliminary":False},"authority":metadata},
            findings=[Finding(finding_id,message,Severity.BLOCK,metadata=metadata)],
        )
