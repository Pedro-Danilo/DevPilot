from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from devpilot_core.application.ui_workspace_context import UiWorkspaceContextResolver
from devpilot_core.workspace.manager import parse_project_yaml_metadata

from .context_pack import StoryContextPackBuilder, StoryContextPackError
from .dor import StoryDoREvaluator
from .models import StoryExecutionState, StoryExecutionStatus, StoryExecutionTransitionError, canonical_sha256
from .store import StoryExecutionStore


@dataclass(frozen=True)
class StoryExecutionResult:
    status: str
    message: str
    data: dict[str, Any]


class StoryExecutionApplicationService:
    """GSDLC-09-A bounded application boundary.

    A may create runtime-only state/context/DoR evidence under outputs/. It never
    mutates workspace source and does not expose code apply/editor behavior.
    """

    def __init__(self, platform_root: Path, *, context_resolver: UiWorkspaceContextResolver | None = None) -> None:
        self.platform_root = Path(platform_root).resolve()
        if context_resolver is None:
            from devpilot_core.application.ui_workspace_context import UiWorkspaceContextResolver
            context_resolver = UiWorkspaceContextResolver(self.platform_root)
        self.context_resolver = context_resolver

    def prepare(
        self,
        *,
        story: dict[str, Any],
        frozen_sprint_record: dict[str, Any],
        source_fragments: dict[str, dict[str, Any]],
        relevant_files: list[str] | tuple[str, ...],
        observed_at_utc: str,
    ) -> StoryExecutionResult:
        context = self.context_resolver.resolve()
        summary = context.summary()
        evaluator = StoryDoREvaluator()
        dor = evaluator.evaluate(
            story=story,
            frozen_sprint_record=frozen_sprint_record,
            source_fragments=source_fragments,
            project_context=summary,
            evaluated_at_utc=observed_at_utc,
        )
        workspace_id = str(context.active_workspace_id or "").strip()
        if not workspace_id or not context.configured or not context.valid:
            return StoryExecutionResult("BLOCK", "Story DoR blocked: active server-valid project context is required.", {"dor_report": dor, "story_execution_state": None, "context_pack": None})
        root = context.effective_workspace_root
        store = StoryExecutionStore(root, workspace_id=workspace_id)
        store.save_dor(dor)
        if dor["status"] != "PASS":
            return StoryExecutionResult("BLOCK", "Story DoR blocked before execution state creation.", {"dor_report": dor, "story_execution_state": None, "context_pack": None})

        project_file = context.project_file or (root / ".devpilot" / "project.yaml")
        metadata = parse_project_yaml_metadata(project_file)
        project_id = str(metadata.get("project_id") or "").strip()
        if not project_id:
            return StoryExecutionResult("BLOCK", "Story execution requires a project_id in .devpilot/project.yaml.", {"dor_report": dor, "story_execution_state": None, "context_pack": None})

        try:
            pack = StoryContextPackBuilder(root).build(
                workspace_id=workspace_id,
                project_id=project_id,
                story=story,
                source_fragments=source_fragments,
                relevant_files=relevant_files,
                created_at_utc=observed_at_utc,
            )
        except StoryContextPackError as exc:
            return StoryExecutionResult("BLOCK", str(exc), {"dor_report": dor, "story_execution_state": None, "context_pack": None})

        store.save_context(pack)
        execution_id = "story-exec-" + canonical_sha256({"workspace_id": workspace_id, "project_id": project_id, "story_id": story.get("id"), "story_version": story.get("version"), "context": pack["context_sha256"]})[:24]
        state = StoryExecutionState(
            execution_id=execution_id,
            workspace_id=workspace_id,
            project_id=project_id,
            story_id=str(story.get("id") or ""),
            story_version=str(story.get("version") or ""),
            status=StoryExecutionStatus.PLANNED,
            sequence=0,
            dor_report_sha256=str(dor["dor_report_sha256"]),
            context_pack_id=str(pack["context_pack_id"]),
            context_pack_sha256=str(pack["context_sha256"]),
            created_at_utc=observed_at_utc,
            updated_at_utc=observed_at_utc,
        )
        state_payload = store.save_state(state)
        return StoryExecutionResult("PASS", "Story execution PLANNED with DoR PASS and deterministic context pack.", {"dor_report": dor, "context_pack": pack, "story_execution_state": state_payload})

    def start(self, *, expected_state_sha256: str, actor_id: str, observed_at_utc: str) -> StoryExecutionResult:
        context = self.context_resolver.resolve()
        workspace_id = str(context.active_workspace_id or "").strip()
        if not context.configured or not context.valid or not workspace_id:
            return StoryExecutionResult("BLOCK", "Story start requires active server-valid project context.", {})
        store = StoryExecutionStore(context.effective_workspace_root, workspace_id=workspace_id)
        state = store.load_state()
        if state is None:
            return StoryExecutionResult("BLOCK", "No PLANNED story execution state exists.", {})
        current = state.to_dict()
        if str(expected_state_sha256) != str(current["state_sha256"]):
            return StoryExecutionResult("BLOCK", "Story state preimage changed; refresh before start.", {"expected_state_sha256": expected_state_sha256, "actual_state_sha256": current["state_sha256"]})
        dor = store.load_dor() or {}
        pack = store.load_context() or {}
        if dor.get("status") != "PASS" or dor.get("dor_report_sha256") != state.dor_report_sha256 or pack.get("context_sha256") != state.context_pack_sha256:
            return StoryExecutionResult("BLOCK", "DoR/context durable evidence no longer matches PLANNED state.", {})
        try:
            transitioned = state.transition(StoryExecutionStatus.IN_PROGRESS, actor_id=actor_id, observed_at_utc=observed_at_utc)
        except StoryExecutionTransitionError as exc:
            return StoryExecutionResult("BLOCK", str(exc), {})
        payload = store.save_state(transitioned)
        return StoryExecutionResult("PASS", "Story execution entered IN_PROGRESS after DoR/context revalidation.", {"story_execution_state": payload})
