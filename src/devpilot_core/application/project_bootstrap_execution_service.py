from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from devpilot_core.approval.models import ApprovalStatus
from devpilot_core.approval.authenticated_binding import safe_session_binding_id
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.identity.auth_models import AuthenticatedPrincipal, SessionContext
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.policy import PolicyEffect, PolicyEngine, PolicyRequest, configured_external_workspace_roots
from devpilot_core.workspace.environment_discovery import DEFAULT_TIMEOUT_SECONDS
from devpilot_core.workspace.project_bootstrap_execution import BootstrapExecutionInput, ProjectBootstrapExecutor
from devpilot_core.workspace.project_entry_contracts import ProjectIntake
from devpilot_core.workspace.project_entry_dry_run import ProjectEntryDryRunService

from .approval_service import ApprovalApplicationService


BOOTSTRAP_ACTION = "filesystem.project_bootstrap_execute"
BOOTSTRAP_TOOL_ID = "project.bootstrap.execute"


class ProjectBootstrapExecutionApplicationService:
    """Authenticated, approval-bound application boundary for GSDLC-03-D.

    The boundary re-runs the 03-C dry-run immediately before approval request
    and again immediately before execution. It binds exact plan/preimage/target
    scope to the authenticated actor and delegates mutation only after
    PolicyEngine + StrongApprovalBinding accept the approved record.
    """

    def __init__(
        self,
        root: Path,
        *,
        approvals: ApprovalApplicationService,
        approval_auth_store: LocalAuthStore | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.approvals = approvals
        self.approval_auth_store = approval_auth_store

    def request_approval_authenticated(
        self,
        *,
        intake: Mapping[str, Any],
        expected_plan_hash: str,
        expected_preimage_hash: str,
        principal: AuthenticatedPrincipal,
        session: SessionContext,
        reason: str,
        ttl_minutes: int = 30,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> CommandResult:
        current = ProjectEntryDryRunService(self.root, timeout_seconds=timeout_seconds).dry_run(intake=intake)
        if not current.ok:
            return self._dependency_block(
                "project bootstrap approval request",
                current,
                "PROJECT_BOOTSTRAP_PRE_APPROVAL_REVALIDATION_BLOCK",
            )

        dry_run = dict(current.data.get("dry_run") or {})
        plan_hash = str(dry_run.get("plan_hash") or "")
        preimage_hash = str(dry_run.get("preimage_hash") or "")
        if plan_hash != expected_plan_hash or preimage_hash != expected_preimage_hash:
            return self._block(
                "project bootstrap approval request",
                "PROJECT_BOOTSTRAP_APPROVAL_HASH_MISMATCH",
                "Approval request must bind the exact current plan and preimage hashes.",
            )

        parsed = ProjectIntake.from_mapping(intake)
        target = str(Path(parsed.target_root).expanduser().resolve(strict=False))
        scope = {
            "schema_id": "devpilot.gsdlc03d.bootstrap_approval_scope.v1",
            "actor_id": principal.actor_id,
            "tool_id": BOOTSTRAP_TOOL_ID,
            "action": BOOTSTRAP_ACTION,
            "action_id": BOOTSTRAP_ACTION,
            "subject": parsed.project_id,
            "subject_hash": plan_hash,
            "plan_hash": plan_hash,
            "preimage_hash": preimage_hash,
            "target_root": target,
            "entry_mode": parsed.entry_mode.value,
            "workspace_id": parsed.project_id,
            "network_execution_authorized": False,
            "dependency_mode": "defer-network",
            "remote_git_execution_authorized": False,
        }
        result = self.approvals.request_authenticated(
            principal=principal,
            session=session,
            tool_id=BOOTSTRAP_TOOL_ID,
            action=BOOTSTRAP_ACTION,
            subject=parsed.project_id,
            caller_actor=None,
            reason=reason.strip() or "Execute reviewed GSDLC-03-D project bootstrap plan.",
            scope=json.dumps(scope, sort_keys=True, separators=(",", ":")),
            expires_at=None,
            ttl_minutes=max(1, min(int(ttl_minutes), 60)),
            workspace_id=parsed.project_id,
        )
        if not result.ok:
            return result

        data = dict(result.data)
        data["bootstrap_binding"] = {
            "project_id": parsed.project_id,
            "entry_mode": parsed.entry_mode.value,
            "target_root": target,
            "plan_hash": plan_hash,
            "preimage_hash": preimage_hash,
            "network_execution_authorized": False,
            "dependency_mode": "defer-network",
        }
        return CommandResult(
            command="project bootstrap approval request",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Approval request created for the exact current bootstrap plan and preimage.",
            data=data,
            findings=[
                *result.findings,
                Finding(
                    "PROJECT_BOOTSTRAP_APPROVAL_REQUEST_PASS",
                    "Bootstrap approval request is bound to authenticated actor, plan hash and preimage hash.",
                    Severity.INFO,
                ),
            ],
        )

    def execute_authenticated(
        self,
        *,
        intake: Mapping[str, Any],
        expected_plan_hash: str,
        expected_preimage_hash: str,
        approval_id: str,
        principal: AuthenticatedPrincipal,
        session: SessionContext,
        dependency_mode: str = "defer-network",
        fault_stage: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> CommandResult:
        if dependency_mode not in {"defer-network", "offline-cache"}:
            return self._block(
                "project bootstrap execute",
                "PROJECT_BOOTSTRAP_DEPENDENCY_MODE_BLOCK",
                "Unsupported dependency execution mode.",
            )
        if fault_stage and os.environ.get("DEVPILOT_GSDLC03D_FAULT_INJECTION") != "1":
            return self._block(
                "project bootstrap execute",
                "PROJECT_BOOTSTRAP_FAULT_INJECTION_DISABLED",
                "Fault injection is restricted to the explicit GSDLC-03-D evaluation harness.",
            )

        current = ProjectEntryDryRunService(self.root, timeout_seconds=timeout_seconds).dry_run(intake=intake)
        if not current.ok:
            return self._dependency_block(
                "project bootstrap execute",
                current,
                "PROJECT_BOOTSTRAP_PRE_EXECUTION_REVALIDATION_BLOCK",
            )

        dry_run = dict(current.data.get("dry_run") or {})
        plan = dict(current.data.get("bootstrap_plan") or {})
        if not plan:
            return self._block(
                "project bootstrap execute",
                "PROJECT_BOOTSTRAP_PLAN_MISSING",
                "Revalidated dry-run does not contain the typed bootstrap plan.",
            )
        plan_hash = str(dry_run.get("plan_hash") or "")
        preimage_hash = str(dry_run.get("preimage_hash") or "")
        if plan_hash != expected_plan_hash or preimage_hash != expected_preimage_hash:
            return self._block(
                "project bootstrap execute",
                "PROJECT_BOOTSTRAP_STALE_PLAN_BLOCK",
                "Plan or preimage changed after approval review.",
            )

        parsed = ProjectIntake.from_mapping(intake)
        target = Path(parsed.target_root).expanduser().resolve(strict=False)
        record = self.approvals.service.store.get(str(approval_id or "").strip())
        if record is None:
            return self._block(
                "project bootstrap execute",
                "PROJECT_BOOTSTRAP_APPROVAL_NOT_FOUND",
                "Bootstrap execution requires an existing approval record.",
            )
        if record.status != ApprovalStatus.APPROVED.value or record.expired:
            return self._block(
                "project bootstrap execute",
                "PROJECT_BOOTSTRAP_APPROVAL_NOT_APPROVED",
                "Bootstrap execution requires a current approved approval record.",
            )

        scope = dict(record.scope or {})
        exact = {
            "actor_id": principal.actor_id,
            "tool_id": BOOTSTRAP_TOOL_ID,
            "action": BOOTSTRAP_ACTION,
            "subject": parsed.project_id,
            "plan_hash": plan_hash,
            "preimage_hash": preimage_hash,
            "target_root": str(target),
            "entry_mode": parsed.entry_mode.value,
        }
        mismatches = {
            key: {"expected": value, "recorded": scope.get(key)}
            for key, value in exact.items()
            if str(scope.get(key) or "") != str(value)
        }
        authenticated_binding = dict(record.metadata.get("authenticated_approval_binding") or {})
        role_at_decision = str(authenticated_binding.get("role_at_decision") or scope.get("role_at_decision") or "")
        persisted_binding_ok, persisted_binding_reason = self.approvals._get_authority().revalidate_persisted_binding(record)
        if mismatches or not role_at_decision or not persisted_binding_ok:
            return self._block(
                "project bootstrap execute",
                "PROJECT_BOOTSTRAP_APPROVAL_SCOPE_MISMATCH",
                "Approved record is not exactly bound to the current bootstrap scope and authenticated decision authority.",
                {
                    "mismatches": mismatches,
                    "role_at_decision_present": bool(role_at_decision),
                    "authenticated_decision_binding_valid": persisted_binding_ok,
                    "authenticated_decision_binding_reason": persisted_binding_reason,
                },
            )

        policy = PolicyEngine(
            self.root,
            allowed_external_roots=configured_external_workspace_roots(),
            approval_auth_store=self.approval_auth_store,
        ).evaluate(
            PolicyRequest(
                action=BOOTSTRAP_ACTION,
                path=str(target),
                text=None,
                external_api=False,
                dry_run=False,
                approval_id=record.approval_id,
                tool_id=BOOTSTRAP_TOOL_ID,
                subject=parsed.project_id,
                actor=principal.actor_id,
                role_at_decision=role_at_decision,
                subject_hash=plan_hash,
                interface="api",
                metadata={
                    "workspace_id": parsed.project_id,
                    "plan_hash": plan_hash,
                    "preimage_hash": preimage_hash,
                    "entry_mode": parsed.entry_mode.value,
                    "network_execution_authorized": False,
                    "remote_git_execution_authorized": False,
                    "authenticated_session_binding_id": safe_session_binding_id(principal.actor_id, session.created_at, session.rotation_counter),
                },
            )
        )
        if not policy.ok:
            return CommandResult(
                command="project bootstrap execute",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Approval/policy binding blocked project bootstrap execution.",
                data={"policy": policy.to_dict(), "mutations_performed": False},
                findings=policy.findings,
            )

        result = ProjectBootstrapExecutor(
            self.root,
            allowed_roots=configured_external_workspace_roots(),
        ).execute(
            BootstrapExecutionInput(
                intake=intake,
                bootstrap_plan=plan,
                plan_hash=plan_hash,
                preimage_hash=preimage_hash,
                approval_id=record.approval_id,
                actor_id=principal.actor_id,
                role_at_decision=role_at_decision,
                fault_stage=fault_stage,
                dependency_mode=dependency_mode,
            )
        )
        data = dict(result.data)
        data["policy"] = {
            "status": "PASS",
            "approval_bound": True,
            "approval_id": record.approval_id,
            "actor_id": principal.actor_id,
            "role_at_decision": role_at_decision,
            "action": BOOTSTRAP_ACTION,
            "tool_id": BOOTSTRAP_TOOL_ID,
        }
        return CommandResult(
            command="project bootstrap execute",
            ok=result.ok,
            exit_code=result.exit_code,
            message=result.message,
            data=data,
            findings=result.findings,
        )

    @staticmethod
    def _block(
        command: str,
        finding_id: str,
        message: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> CommandResult:
        return CommandResult(
            command=command,
            ok=False,
            exit_code=ExitCode.BLOCK,
            message=message,
            data={"mutations_performed": False},
            findings=[Finding(finding_id, message, Severity.BLOCK, metadata=dict(metadata or {}))],
        )

    @staticmethod
    def _dependency_block(command: str, result: CommandResult, finding_id: str) -> CommandResult:
        return CommandResult(
            command=command,
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Bootstrap execution dependency did not pass.",
            data={"dependency": result.to_dict(), "mutations_performed": False},
            findings=[
                Finding(
                    finding_id,
                    "Current dry-run/plan/preimage did not revalidate; execution remains blocked.",
                    Severity.BLOCK,
                ),
                *result.findings,
            ],
        )
