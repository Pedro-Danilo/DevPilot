from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.guided_sdlc import AdvisorContext, ExecutionModeAdvisor, GuidedSDLCService, ProjectProgressEngine, ReconciliationError, WorkflowEngineError
from devpilot_core.guided_sdlc.repository import WorkspaceEngineeringStateStoreError

from .portfolio_service import PortfolioApplicationService
from .ui_workspace_context import UiWorkspaceContextResolver


class GuidedSDLCApplicationService:
    """Application boundary for Guided SDLC deterministic services.

    B/C operations are read-only. GSDLC-01-D adds bounded reconciliation:
    preview remains source/state read-only; execute may persist only the local
    WorkspaceEngineeringState through its atomic repository. No HTTP route is
    exposed before GSDLC-01-E and managed workspace source/Git stay read-only.
    """

    def __init__(self, root: Path, *, context_resolver: UiWorkspaceContextResolver | None = None) -> None:
        self.root = Path(root).resolve()
        self.context_resolver = context_resolver or UiWorkspaceContextResolver(self.root)

    def _service(self) -> GuidedSDLCService:
        # Lazy construction preserves ApplicationService compatibility for
        # tests/tools that instantiate a facade over a minimal temporary root.
        return GuidedSDLCService.from_platform_root(self.root)

    def evaluate_transition(
        self,
        *,
        workspace_id: str,
        transition_id: str,
        evidence: dict[str, Any] | None = None,
    ) -> CommandResult:
        try:
            result = self._service().evaluate_transition(
                workspace_id=workspace_id,
                transition_id=transition_id,
                evidence=evidence,
            )
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, ReconciliationError, KeyError) as exc:
            return self._error("guided_sdlc.transition.evaluate", exc)
        return self._result("guided_sdlc.transition.evaluate", result.to_payload())

    def preview_transition(
        self,
        *,
        workspace_id: str,
        transition_id: str,
        evidence: dict[str, Any] | None = None,
        updated_at_utc: str,
    ) -> CommandResult:
        try:
            preview = self._service().preview_transition(
                workspace_id=workspace_id,
                transition_id=transition_id,
                evidence=evidence,
                updated_at_utc=updated_at_utc,
            )
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, ReconciliationError, KeyError) as exc:
            return self._error("guided_sdlc.transition.preview", exc)
        return self._result("guided_sdlc.transition.preview", preview.to_payload())

    def project_status(
        self,
        *,
        workspace_id: str,
        observed_at_utc: str,
        expected_state_fingerprint: str | None = None,
    ) -> CommandResult:
        try:
            projection = self._service().project_status(
                workspace_id=workspace_id,
                observed_at_utc=observed_at_utc,
                expected_state_fingerprint=expected_state_fingerprint,
            )
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, KeyError, ValueError):
            projection = ProjectProgressEngine.unknown(
                workspace_id=workspace_id,
                observed_at_utc=observed_at_utc,
            )
        return self._projection_result("guided_sdlc.project.status", projection.status.to_payload())

    def next_action(
        self,
        *,
        workspace_id: str,
        observed_at_utc: str,
        expected_state_fingerprint: str | None = None,
    ) -> CommandResult:
        try:
            projection = self._service().next_action(
                workspace_id=workspace_id,
                observed_at_utc=observed_at_utc,
                expected_state_fingerprint=expected_state_fingerprint,
            )
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, KeyError, ValueError):
            projection = ProjectProgressEngine.unknown(
                workspace_id=workspace_id,
                observed_at_utc=observed_at_utc,
            )
        return self._projection_result("guided_sdlc.next_action", projection.next_action.to_payload())

    def project_status_primary(
        self,
        *,
        workspace_id: str | None,
        observed_at_utc: str,
        expected_state_fingerprint: str | None = None,
    ) -> CommandResult:
        """Return the actor-neutral Project Status payload for API/UI consumption.

        GSDLC-01-E keeps this operation read-only. If workspace_id is omitted,
        the active registered workspace is resolved through the existing
        PortfolioApplicationService. Missing engineering state is represented
        honestly as EMPTY/UNKNOWN instead of being synthesized as PASS.
        """

        explicit = str(workspace_id or "").strip()
        context = self.context_resolver.resolve()
        server_active = ""
        if context.configured and context.valid:
            server_active = str(context.active_workspace_id or "").strip()
        portfolio = PortfolioApplicationService(self.root, context_resolver=self.context_resolver).status()
        portfolio_active = ""
        if isinstance(portfolio.data, dict):
            portfolio_active = str((portfolio.data.get("summary") or {}).get("active_workspace_id") or "").strip()
        resolved = explicit or server_active or portfolio_active
        if not resolved:
            unknown = ProjectProgressEngine.unknown(workspace_id="unknown", observed_at_utc=observed_at_utc)
            return CommandResult(
                command="guided_sdlc.project_status",
                ok=True,
                exit_code=ExitCode.PASS,
                message="No active registered workspace is available for Project Status.",
                data={
                    "ui_state": "EMPTY",
                    "workspace_id": None,
                    "project_status": unknown.status.to_payload(),
                    "next_action": unknown.next_action.to_payload(),
                    "read_only": True,
                    "actor_neutral": True,
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                },
                findings=[],
            )

        try:
            projection = self._service().project_status(
                workspace_id=resolved,
                observed_at_utc=observed_at_utc,
                expected_state_fingerprint=expected_state_fingerprint,
            )
            next_projection = self._service().next_action(
                workspace_id=resolved,
                observed_at_utc=observed_at_utc,
                expected_state_fingerprint=expected_state_fingerprint,
            )
            status_payload = projection.status.to_payload()
            next_payload = next_projection.next_action.to_payload()
            freshness = str((status_payload.get("freshness") or {}).get("status") or "UNKNOWN").upper()
            revalidation = str((status_payload.get("revalidation") or {}).get("status") or "UNKNOWN").upper()
            lifecycle = str(status_payload.get("lifecycle_status") or "UNKNOWN").upper()
            miasi_gate = str((status_payload.get("miasi") or {}).get("gate_status") or "UNKNOWN").upper()
            if revalidation in {"REQUIRED", "IN_PROGRESS"} or lifecycle == "REVALIDATION_REQUIRED":
                ui_state = "REVALIDATION_REQUIRED"
            elif lifecycle == "BLOCKED" or miasi_gate == "BLOCK" or status_payload.get("blockers"):
                ui_state = "BLOCKED"
            elif freshness == "STALE":
                ui_state = "STALE"
            elif status_payload.get("reason") == "unknown":
                ui_state = "UNKNOWN"
            else:
                ui_state = "READY"
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, ReconciliationError, KeyError, ValueError):
            unknown = ProjectProgressEngine.unknown(workspace_id=resolved, observed_at_utc=observed_at_utc)
            status_payload = unknown.status.to_payload()
            next_payload = unknown.next_action.to_payload()
            ui_state = "EMPTY"

        return CommandResult(
            command="guided_sdlc.project_status",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Project Status projected through the Guided SDLC application boundary.",
            data={
                "ui_state": ui_state,
                "workspace_id": resolved,
                "project_status": status_payload,
                "next_action": next_payload,
                "read_only": True,
                "actor_neutral": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
            },
            findings=[],
        )

    def step_actions_primary(
        self,
        *,
        workspace_id: str | None,
        observed_at_utc: str,
        effective_roles: list[str] | tuple[str, ...],
        workspace_scopes: list[str] | tuple[str, ...],
        expected_state_fingerprint: str | None = None,
    ) -> CommandResult:
        """Return the actor-aware, server-policy-bound Step Action Advisor projection.

        The authenticated principal is resolved by the API security/RBAC layer;
        this method receives only sanitized canonical roles/scopes. The advisor
        is read-only and never grants target-route capability.
        """

        status_result = self.project_status_primary(
            workspace_id=workspace_id,
            observed_at_utc=observed_at_utc,
            expected_state_fingerprint=expected_state_fingerprint,
        )
        resolved = str((status_result.data or {}).get("workspace_id") or "").strip()
        project_status = (status_result.data or {}).get("project_status")
        if not resolved or not isinstance(project_status, dict):
            return CommandResult(
                command="guided_sdlc.step_actions",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Step Action Advisor requires an active server-valid project context.",
                data={
                    "ui_state": "BLOCKED",
                    "workspace_id": None,
                    "current_step": None,
                    "advisor": None,
                    "read_only": True,
                    "actor_neutral": False,
                    "server_authoritative": True,
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "source_mutations_performed": False,
                },
                findings=[Finding(id="STEP_ACTION_ACTIVE_PROJECT_REQUIRED", message="An active registered workspace/project is required.", severity=Severity.BLOCK)],
            )

        current_step = str(project_status.get("current_step") or "").strip()
        context = AdvisorContext.from_payload(
            workspace_id=resolved,
            current_step=current_step,
            effective_roles=effective_roles,
            workspace_scopes=workspace_scopes,
            project_status=project_status,
        )
        decision = ExecutionModeAdvisor(self.root).advise(context)
        payload = decision.to_payload()
        allowed = decision.status == "PASS" and bool(decision.recommended_action_id)
        findings = [] if allowed else [
            Finding(
                id="STEP_ACTION_NO_EXECUTABLE_ROUTE",
                message="No current-step action is executable under the authoritative prerequisites/RBAC/policy.",
                severity=Severity.BLOCK,
                metadata={"current_step": current_step},
            )
        ]
        return CommandResult(
            command="guided_sdlc.step_actions",
            ok=allowed,
            exit_code=ExitCode.PASS if allowed else ExitCode.BLOCK,
            message="Step Action Advisor derived deterministic server-policy-bound options." if allowed else "Step Action Advisor is explicitly blocked.",
            data={
                "ui_state": "READY" if allowed else "BLOCKED",
                "workspace_id": resolved,
                "current_step": current_step,
                "advisor": payload,
                "read_only": True,
                "actor_neutral": False,
                "server_authoritative": True,
                "network_used": False,
                "external_api_used": False,
                "model_execution_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
            },
            findings=findings,
        )

    def reconcile_preview(
        self,
        *,
        workspace_id: str,
        updated_at_utc: str,
        observed_at_utc: str,
    ) -> CommandResult:
        try:
            reconciliation, projection = self._service().reconcile_project_status(
                workspace_id=workspace_id,
                updated_at_utc=updated_at_utc,
                observed_at_utc=observed_at_utc,
                execute=False,
            )
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, ReconciliationError, KeyError, ValueError) as exc:
            return self._error("guided_sdlc.reconcile.preview", exc)
        return CommandResult(
            command="guided_sdlc.reconcile.preview",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Guided SDLC reconciliation preview completed deterministically.",
            data={
                "reconciliation": reconciliation.to_payload(),
                "project_status": projection.status.to_payload(),
                "next_action": projection.next_action.to_payload(),
                "execute": False,
            },
            findings=[],
        )

    def reconcile_execute(
        self,
        *,
        workspace_id: str,
        updated_at_utc: str,
        observed_at_utc: str,
    ) -> CommandResult:
        try:
            reconciliation, projection = self._service().reconcile_project_status(
                workspace_id=workspace_id,
                updated_at_utc=updated_at_utc,
                observed_at_utc=observed_at_utc,
                execute=True,
            )
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, ReconciliationError, KeyError, ValueError) as exc:
            return self._error("guided_sdlc.reconcile.execute", exc)
        return CommandResult(
            command="guided_sdlc.reconcile.execute",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Guided SDLC reconciliation persisted engineering-state only.",
            data={
                "reconciliation": reconciliation.to_payload(),
                "project_status": projection.status.to_payload(),
                "next_action": projection.next_action.to_payload(),
                "execute": True,
                "managed_workspace_source_mutated": False,
            },
            findings=[],
        )

    def _projection_result(self, command: str, payload: dict[str, Any]) -> CommandResult:
        unknown = payload.get("reason") == "unknown" or payload.get("reason_code") in {
            "WORKSPACE_ENGINEERING_STATE_UNKNOWN",
            "NEXT_ACTION_UNKNOWN",
        }
        return CommandResult(
            command=command,
            ok=not unknown,
            exit_code=ExitCode.PASS if not unknown else ExitCode.BLOCK,
            message="Guided SDLC projection derived deterministically." if not unknown else "Guided SDLC projection is unknown.",
            data=payload,
            findings=[] if not unknown else [
                Finding(
                    id=str(payload.get("reason_code") or "WORKSPACE_ENGINEERING_STATE_UNKNOWN"),
                    message="Project status/next action could not be derived from authoritative state.",
                    severity=Severity.BLOCK,
                )
            ],
        )

    def _result(self, command: str, payload: dict[str, Any]) -> CommandResult:
        evaluation = payload.get("evaluation", payload)
        allowed = evaluation.get("decision") == "PASS"
        findings = [
            Finding(
                id=str(item.get("code", "GUIDED_SDLC_BLOCKER")),
                message=str(item.get("message", "Transition is blocked.")),
                severity=Severity.BLOCK,
                metadata={
                    "category": item.get("category"),
                    "subject": item.get("subject"),
                },
            )
            for item in evaluation.get("blockers", [])
        ]
        return CommandResult(
            command=command,
            ok=allowed,
            exit_code=ExitCode.PASS if allowed else ExitCode.BLOCK,
            message="Guided SDLC transition is allowed." if allowed else "Guided SDLC transition is blocked.",
            data=payload,
            findings=findings,
        )

    def _error(self, command: str, exc: Exception) -> CommandResult:
        return CommandResult(
            command=command,
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Guided SDLC request could not be evaluated.",
            data={"network_used": False, "external_api_used": False},
            findings=[
                Finding(
                    id="GUIDED_SDLC_TRANSITION_INPUT_BLOCKED",
                    message=str(exc),
                    severity=Severity.BLOCK,
                )
            ],
        )
