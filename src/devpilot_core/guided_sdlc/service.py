from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .repository import WorkspaceEngineeringStateRepository
from .workflow_engine import TransitionEvidence, TransitionEvaluation, TransitionPreview, WorkflowEngine


class GuidedSDLCService:
    """Project-centric read-only transition use cases for GSDLC-01-B.

    This service coordinates repository reads with the pure WorkflowEngine.
    It does not persist preview states, execute side effects or expose HTTP/UI.
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
