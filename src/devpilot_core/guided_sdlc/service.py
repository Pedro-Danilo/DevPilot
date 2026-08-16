from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .repository import WorkspaceEngineeringStateRepository
from .project_progress import ProjectProgressEngine, ProjectProjection
from .reconciler import ReconciliationResult, WorkspaceReconciler
from .workflow_engine import TransitionEvidence, TransitionEvaluation, TransitionPreview, WorkflowEngine


class GuidedSDLCService:
    """Project-centric Guided SDLC orchestration.

    Transition evaluation/projection remain read-only. GSDLC-01-D adds bounded
    reconciliation; `execute=True` may persist only WorkspaceEngineeringState
    through its atomic repository and never writes managed workspace source.
    No HTTP/UI route is exposed here.
    """

    def __init__(
        self,
        repository: WorkspaceEngineeringStateRepository,
        workflow_engine: WorkflowEngine,
    ) -> None:
        self.repository = repository
        self.workflow_engine = workflow_engine

    @classmethod
    def from_platform_root(
        cls,
        platform_root: Path,
        *,
        catalog_path: str | Path = ".devpilot/gsdlc/workflow_transition_catalog.json",
    ) -> "GuidedSDLCService":
        root = Path(platform_root).resolve()
        raw = Path(catalog_path)
        resolved = raw if raw.is_absolute() else root / raw
        return cls(
            WorkspaceEngineeringStateRepository(root),
            WorkflowEngine.from_catalog_path(resolved),
        )

    def evaluate_transition(
        self,
        *,
        workspace_id: str,
        transition_id: str,
        evidence: TransitionEvidence | Mapping[str, Any] | None = None,
    ) -> TransitionEvaluation:
        state = self.repository.load(workspace_id)
        return self.workflow_engine.evaluate(state, transition_id, evidence)

    def preview_transition(
        self,
        *,
        workspace_id: str,
        transition_id: str,
        evidence: TransitionEvidence | Mapping[str, Any] | None = None,
        updated_at_utc: str,
    ) -> TransitionPreview:
        state = self.repository.load(workspace_id)
        return self.workflow_engine.preview_advance(
            state,
            transition_id,
            evidence,
            updated_at_utc=updated_at_utc,
        )

    def project_status(
        self,
        *,
        workspace_id: str,
        observed_at_utc: str,
        expected_state_fingerprint: str | None = None,
    ) -> ProjectProjection:
        state = self.repository.load(workspace_id)
        return ProjectProgressEngine(self.workflow_engine).project(
            state,
            observed_at_utc=observed_at_utc,
            expected_state_fingerprint=expected_state_fingerprint,
        )

    def next_action(
        self,
        *,
        workspace_id: str,
        observed_at_utc: str,
        expected_state_fingerprint: str | None = None,
    ) -> ProjectProjection:
        # Same deterministic projection source as project_status. Keeping one
        # implementation prevents future API/UI semantic drift.
        return self.project_status(
            workspace_id=workspace_id,
            observed_at_utc=observed_at_utc,
            expected_state_fingerprint=expected_state_fingerprint,
        )

    def reconcile(
        self,
        *,
        workspace_id: str,
        updated_at_utc: str,
        execute: bool = False,
    ) -> ReconciliationResult:
        state = self.repository.load(workspace_id)
        result = WorkspaceReconciler(self.repository).inspect(
            state,
            updated_at_utc=updated_at_utc,
        )
        if not execute or not result.state_changed:
            return result
        self.repository.save(
            result.successor_state,
            expected_sequence=state.sequence,
        )
        return ReconciliationResult(
            report=result.report.__class__(
                workspace_id=result.report.workspace_id,
                project_id=result.report.project_id,
                decision=result.report.decision,
                drift_entries=result.report.drift_entries,
                prior_git=result.report.prior_git,
                observed_git=result.report.observed_git,
                required_revalidation=result.report.required_revalidation,
                source_refs=result.report.source_refs,
                mutation_declaration={
                    **dict(result.report.mutation_declaration),
                    "engineering_state_saved": True,
                },
            ),
            current_state=result.current_state,
            successor_state=result.successor_state,
            state_changed=result.state_changed,
            state_persisted=True,
        )

    def reconcile_project_status(
        self,
        *,
        workspace_id: str,
        updated_at_utc: str,
        observed_at_utc: str,
        execute: bool = False,
    ) -> tuple[ReconciliationResult, ProjectProjection]:
        reconciliation = self.reconcile(
            workspace_id=workspace_id,
            updated_at_utc=updated_at_utc,
            execute=execute,
        )
        state = reconciliation.successor_state
        projection = ProjectProgressEngine(self.workflow_engine).project(
            state,
            observed_at_utc=observed_at_utc,
            expected_state_fingerprint=state.fingerprint(),
        )
        return reconciliation, projection
