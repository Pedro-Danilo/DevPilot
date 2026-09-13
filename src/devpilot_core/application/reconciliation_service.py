from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.reconciliation import AdvancedWorkspaceReconciliationService, ReconciliationStateError

from .ui_workspace_context import UiWorkspaceContextResolver


class ReconciliationApplicationService:
    """GSDLC-12-B application boundary for branch/external-edit reconciliation."""

    def __init__(self, root: Path, *, context_resolver: UiWorkspaceContextResolver | None = None) -> None:
        self.root = Path(root).resolve()
        self.context_resolver = context_resolver or UiWorkspaceContextResolver(self.root)
        self.reconciliation = AdvancedWorkspaceReconciliationService(self.root, context_resolver=self.context_resolver)

    def status(self, *, actor: str, roles: list[str], workspace_scopes: list[str], session_created_at: str, rotation_counter: int) -> CommandResult:
        try:
            self._require_scope(workspace_scopes)
            report = self.reconciliation.inspect(actor=actor, session_created_at=session_created_at, rotation_counter=rotation_counter)
        except (ReconciliationStateError, ValueError, RuntimeError) as exc:
            return self._block("reconciliation.status", "GSDLC12B_RECONCILIATION_STATUS_BLOCK", str(exc))
        return CommandResult(
            command="reconciliation.status",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Branch/filesystem reconciliation state projected without source or Git mutation.",
            data={"reconciliation": report, "roles": list(roles), "safety": self._safety(mutated=False)},
            findings=[Finding("GSDLC12B_RECONCILIATION_VISIBLE", f"Reconciliation state is explicit: {report['classification']}", Severity.INFO)],
        )

    def baseline(self, *, actor: str, roles: list[str], workspace_scopes: list[str], session_created_at: str, rotation_counter: int, execute: bool, confirmation: str) -> CommandResult:
        try:
            self._require_scope(workspace_scopes)
            result = self.reconciliation.baseline(actor=actor, session_created_at=session_created_at, rotation_counter=rotation_counter, execute=execute, confirmation=confirmation)
        except (ReconciliationStateError, ValueError, RuntimeError) as exc:
            return self._block("reconciliation.baseline", "GSDLC12B_BASELINE_BLOCK", str(exc))
        return CommandResult("reconciliation.baseline", True, ExitCode.PASS, "Reconciliation baseline dry-run completed." if not execute else "Reviewed reconciliation baseline captured.", data={"result": result, "roles": list(roles), "safety": self._safety(mutated=execute)}, findings=[])

    def adopt(self, *, actor: str, roles: list[str], workspace_scopes: list[str], session_created_at: str, rotation_counter: int, execute: bool, confirmation: str) -> CommandResult:
        try:
            self._require_scope(workspace_scopes)
            result = self.reconciliation.adopt(actor=actor, session_created_at=session_created_at, rotation_counter=rotation_counter, execute=execute, confirmation=confirmation)
        except (ReconciliationStateError, ValueError, RuntimeError) as exc:
            return self._block("reconciliation.adopt", "GSDLC12B_ADOPT_BLOCK", str(exc))
        return CommandResult("reconciliation.adopt", True, ExitCode.PASS, "Reconciliation adoption dry-run completed." if not execute else "Reviewed current authority adopted as reconciliation baseline.", data={"result": result, "roles": list(roles), "safety": self._safety(mutated=execute)}, findings=[])

    def _require_scope(self, scopes: list[str]) -> None:
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or not context.active_workspace_id:
            raise ReconciliationStateError("active server-valid workspace is required")
        normalized = {str(value).strip() for value in scopes if str(value).strip()}
        if str(context.active_workspace_id) not in normalized:
            raise ReconciliationStateError("authenticated workspace scope does not authorize the active workspace")

    @staticmethod
    def _safety(*, mutated: bool) -> dict[str, Any]:
        return {"local_only": True, "network_used": False, "external_api_used": False, "secrets_exposed": False, "source_mutations_performed": False, "git_mutations_performed": False, "runtime_metadata_mutated": mutated, "dry_run_default": True}

    @staticmethod
    def _block(command: str, finding_id: str, message: str) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={"safety": ReconciliationApplicationService._safety(mutated=False)}, findings=[Finding(finding_id, message, Severity.BLOCK)])
