from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.guided_sdlc import GuidedSDLCService, ProjectProgressEngine, WorkflowEngineError
from devpilot_core.guided_sdlc.repository import WorkspaceEngineeringStateStoreError


class GuidedSDLCApplicationService:
    """Application boundary for deterministic transition evaluate/preview.

    GSDLC-01-B exposes no HTTP route. These operations are read-only application
    capabilities used by tests and future API/UI adapters.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()

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
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, KeyError) as exc:
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
        except (WorkspaceEngineeringStateStoreError, WorkflowEngineError, KeyError) as exc:
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
            message="Guided SDLC transition request could not be evaluated.",
            data={"network_used": False, "external_api_used": False},
            findings=[
                Finding(
                    id="GUIDED_SDLC_TRANSITION_INPUT_BLOCKED",
                    message=str(exc),
                    severity=Severity.BLOCK,
                )
            ],
        )
