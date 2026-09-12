from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.recovery import RecoveryStateError, ResumeService, WorkspaceLockService

from .guided_sdlc_service import GuidedSDLCApplicationService
from .ui_workspace_context import UiWorkspaceContextResolver


class RecoveryApplicationService:
    """GSDLC-12-A application boundary for durable resumability and locks."""

    def __init__(self, root: Path, *, context_resolver: UiWorkspaceContextResolver | None = None) -> None:
        self.root = Path(root).resolve()
        self.context_resolver = context_resolver or UiWorkspaceContextResolver(self.root)
        self.resume = ResumeService(self.root, context_resolver=self.context_resolver)
        self.locks = WorkspaceLockService(self.root, context_resolver=self.context_resolver)

    def status(self, *, actor: str, roles: list[str], workspace_scopes: list[str], session_created_at: str, rotation_counter: int) -> CommandResult:
        try:
            self._require_scope(workspace_scopes)
            recovery = self.resume.status(actor=actor, session_created_at=session_created_at, rotation_counter=rotation_counter)
            locks = self.locks.status(actor=actor, session_created_at=session_created_at, rotation_counter=rotation_counter)
            coherence = self._project_status_coherence(workspace_id=str(recovery.get("workspace_id") or ""))
        except (RecoveryStateError, ValueError, RuntimeError) as exc:
            return self._block("recovery.status", "GSDLC12A_RECOVERY_STATUS_BLOCK", str(exc))
        return CommandResult(
            command="recovery.status",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Durable recovery context projected from server-side authority.",
            data={
                "recovery": recovery,
                "locks": locks,
                "project_status_coherence": coherence,
                "authority": {
                    "server_side": True,
                    "browser_storage_authority": False,
                    "runtime_db_snapshot_used": False,
                    "roles": list(roles),
                },
                "safety": self._safety(mutated=False),
            },
            findings=[],
        )

    def checkpoint(
        self,
        *,
        actor: str,
        roles: list[str],
        workspace_scopes: list[str],
        session_created_at: str,
        rotation_counter: int,
        draft_refs: list[str],
        pending_work: list[dict[str, Any]],
        evidence_refs: list[str],
        recovery_reason: str,
    ) -> CommandResult:
        try:
            self._require_scope(workspace_scopes)
            checkpoint = self.resume.checkpoint(
                actor=actor,
                session_created_at=session_created_at,
                rotation_counter=rotation_counter,
                draft_refs=draft_refs,
                pending_work=pending_work,
                evidence_refs=evidence_refs,
                recovery_reason=recovery_reason,
            )
        except (RecoveryStateError, ValueError, RuntimeError) as exc:
            return self._block("recovery.checkpoint", "GSDLC12A_CHECKPOINT_BLOCK", str(exc))
        return CommandResult(
            command="recovery.checkpoint",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Metadata-only durable recovery checkpoint persisted.",
            data={"checkpoint": checkpoint, "roles": list(roles), "safety": self._safety(mutated=True)},
            findings=[Finding("GSDLC12A_CHECKPOINT_PASS", "Durable checkpoint is server-side, versioned and metadata-only.", Severity.INFO)],
        )

    def lock_acquire(self, *, actor: str, roles: list[str], workspace_scopes: list[str], session_created_at: str, rotation_counter: int, action_id: str, sensitive: bool, ttl_seconds: int) -> CommandResult:
        try:
            self._require_scope(workspace_scopes)
            lock = self.locks.acquire(actor=actor, session_created_at=session_created_at, rotation_counter=rotation_counter, action_id=action_id, sensitive=sensitive, ttl_seconds=ttl_seconds)
        except (RecoveryStateError, ValueError, RuntimeError) as exc:
            return self._block("recovery.lock.acquire", "GSDLC12A_LOCK_ACQUIRE_BLOCK", str(exc))
        return CommandResult("recovery.lock.acquire", True, ExitCode.PASS, "Workspace/action lock acquired or heartbeated idempotently.", data={"lock": lock, "roles": list(roles), "safety": self._safety(mutated=True)}, findings=[])

    def lock_release(self, *, actor: str, roles: list[str], workspace_scopes: list[str], session_created_at: str, rotation_counter: int, action_id: str) -> CommandResult:
        try:
            self._require_scope(workspace_scopes)
            result = self.locks.release(actor=actor, session_created_at=session_created_at, rotation_counter=rotation_counter, action_id=action_id)
        except (RecoveryStateError, ValueError, RuntimeError) as exc:
            return self._block("recovery.lock.release", "GSDLC12A_LOCK_RELEASE_BLOCK", str(exc))
        return CommandResult("recovery.lock.release", True, ExitCode.PASS, "Workspace/action lock released by its exact owner session.", data={"result": result, "roles": list(roles), "safety": self._safety(mutated=True)}, findings=[])

    def lock_recover(self, *, actor: str, roles: list[str], workspace_scopes: list[str], action_id: str, confirmation: str) -> CommandResult:
        try:
            self._require_scope(workspace_scopes)
            result = self.locks.recover_stale(action_id=action_id, actor=actor, roles=roles, confirmation=confirmation)
        except (RecoveryStateError, ValueError, RuntimeError) as exc:
            return self._block("recovery.lock.recover", "GSDLC12A_STALE_LOCK_RECOVERY_BLOCK", str(exc))
        return CommandResult("recovery.lock.recover", True, ExitCode.PASS, "Stale lock removed explicitly; sensitive work remains revalidation-bound.", data={"result": result, "safety": self._safety(mutated=True)}, findings=[])

    def _project_status_coherence(self, *, workspace_id: str) -> dict[str, Any]:
        observed = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        result = GuidedSDLCApplicationService(self.root, context_resolver=self.context_resolver).project_status_primary(workspace_id=workspace_id, observed_at_utc=observed)
        data = dict(result.data or {})
        status = dict(data.get("project_status") or {})
        lifecycle = str(status.get("lifecycle_status") or "UNKNOWN").upper()
        aggregate = str(data.get("ui_state") or "UNKNOWN").upper()
        reconciliation = dict(data.get("lifecycle_reconciliation") or {})
        return {
            "lifecycle_status": lifecycle,
            "aggregate_ui_state": aggregate,
            "display_state": str(reconciliation.get("display_state") or aggregate),
            "non_authoritative_gap_count": int(reconciliation.get("non_authoritative_gap_count") or 0),
            "authoritative_blocker_count": int(reconciliation.get("authoritative_blocker_count") or 0),
            "contradictory_message_present": lifecycle == "RELEASED" and aggregate == "BLOCKED" and not reconciliation,
        }

    def _require_scope(self, scopes: list[str]) -> None:
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or not context.active_workspace_id:
            raise RecoveryStateError("active server-valid workspace is required")
        normalized = {str(value).strip() for value in scopes if str(value).strip()}
        if str(context.active_workspace_id) not in normalized:
            raise RecoveryStateError("authenticated workspace scope does not authorize the active workspace")

    @staticmethod
    def _safety(*, mutated: bool) -> dict[str, Any]:
        return {
            "local_only": True,
            "network_used": False,
            "external_api_used": False,
            "secrets_exposed": False,
            "source_mutations_performed": False,
            "runtime_metadata_mutated": mutated,
            "auto_resume_mutation": False,
            "browser_storage_authority": False,
        }

    @staticmethod
    def _block(command: str, finding_id: str, message: str) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={"safety": RecoveryApplicationService._safety(mutated=False)}, findings=[Finding(finding_id, message, Severity.BLOCK)])
