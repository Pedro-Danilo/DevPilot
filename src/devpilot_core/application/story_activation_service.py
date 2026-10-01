from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.story_execution import StoryExecutionApplicationService, StoryExecutionStatus, StoryExecutionStore


class StoryActivationApplicationService:
    """Bridge Planning FROZEN -> StoryExecution runtime authority.

    This service deliberately reuses GSDLC-09-A StoryExecutionApplicationService.
    It only resolves the authoritative READY story and its trace inputs from the
    already-FROZEN planning/pre-code artifacts.  It never writes managed source,
    never grants model/tool/apply/approval authority and never mutates FROZEN
    planning artifacts.
    """

    def __init__(self, root: Path, *, context_resolver) -> None:
        self.root = Path(root).resolve()
        self.context_resolver = context_resolver

    def status(self) -> CommandResult:
        command = "story activation status"
        context = self.context_resolver.resolve()
        workspace_id = str(context.active_workspace_id or "").strip()
        if not context.configured or not context.valid or not workspace_id:
            return self._block(command, "GSDLC13D01_PROJECT_CONTEXT_BLOCK", "Story activation requires active server-valid project context.")
        workspace = Path(context.effective_workspace_root).resolve()
        store = StoryExecutionStore(workspace, workspace_id=workspace_id)
        current = store.load_state()
        authority = self._authority(workspace, workspace_id, store)
        if isinstance(authority, CommandResult):
            return authority
        payload = self._projection(store, authority, current)
        return self._pass(command, "Story activation projected from frozen Sprint/Backlog and current StoryExecution authority.", payload)

    def prepare(self, *, story_id: str, actor_id: str, actor_role: str, observed_at_utc: str) -> CommandResult:
        command = "story activation prepare"
        role = str(actor_role).strip().lower()
        if role not in {"owner", "developer"}:
            return self._block(command, "GSDLC13D01_STORY_ACTIVATION_ROLE_BLOCK", "Story preparation requires owner or developer human role.")
        if str(actor_id).strip().lower().startswith("agent"):
            return self._block(command, "GSDLC13D01_STORY_ACTIVATION_HUMAN_BLOCK", "Agent-originated actor cannot activate a StoryExecution.")
        context = self.context_resolver.resolve()
        workspace_id = str(context.active_workspace_id or "").strip()
        if not context.configured or not context.valid or not workspace_id:
            return self._block(command, "GSDLC13D01_PROJECT_CONTEXT_BLOCK", "Story activation requires active server-valid project context.")
        workspace = Path(context.effective_workspace_root).resolve()
        store = StoryExecutionStore(workspace, workspace_id=workspace_id)
        current = store.load_state()

        # Repeated UI/network requests are idempotent for the same current story.
        if current is not None and current.status is not StoryExecutionStatus.DONE:
            if current.story_id == str(story_id) and current.status in {StoryExecutionStatus.PLANNED, StoryExecutionStatus.IN_PROGRESS}:
                return self._pass(command, "Story execution already prepared/active; returning current runtime authority without mutation.", self._projection(store, self._authority_or_raise(workspace, workspace_id, store), current))
            return self._block(command, "GSDLC13D01_ACTIVE_STORY_BLOCK", f"Story {current.story_id} is {current.status.value}; finish it before activating another story.")

        authority = self._authority(workspace, workspace_id, store)
        if isinstance(authority, CommandResult):
            return authority
        candidates = {x["story_id"]: x for x in authority["ready_candidates"]}
        if str(story_id) not in candidates:
            return self._block(command, "GSDLC13D01_READY_STORY_REQUIRED_BLOCK", "Requested story is not a current READY story in the FROZEN sprint.")
        story = authority["stories_by_id"].get(str(story_id))
        if not isinstance(story, dict):
            return self._block(command, "GSDLC13D01_STORY_SOURCE_BLOCK", "READY sprint story is missing from the FROZEN backlog authority.")

        if current is not None and current.status is StoryExecutionStatus.DONE:
            store.archive_current_completed()

        source_fragments = self._source_fragments(workspace, story)
        service = StoryExecutionApplicationService(self.root, context_resolver=self.context_resolver)
        result = service.prepare(
            story=story,
            frozen_sprint_record=authority["sprint_record"],
            source_fragments=source_fragments,
            relevant_files=[],
            observed_at_utc=observed_at_utc,
        )
        if result.status != "PASS":
            return self._block(
                command,
                "GSDLC13D01_STORY_PREPARE_BLOCK",
                result.message,
                data={**result.data, "activation": self._activation_summary(authority, store)},
            )
        prepared = store.load_state()
        return self._pass(command, result.message, self._projection(store, authority, prepared))

    def start(self, *, expected_state_sha256: str, actor_id: str, actor_role: str, observed_at_utc: str) -> CommandResult:
        command = "story activation start"
        role = str(actor_role).strip().lower()
        if role not in {"owner", "developer"}:
            return self._block(command, "GSDLC13D01_STORY_START_ROLE_BLOCK", "Story start requires owner or developer human role.")
        if str(actor_id).strip().lower().startswith("agent"):
            return self._block(command, "GSDLC13D01_STORY_START_HUMAN_BLOCK", "Agent-originated actor cannot start a StoryExecution.")
        service = StoryExecutionApplicationService(self.root, context_resolver=self.context_resolver)
        result = service.start(expected_state_sha256=expected_state_sha256, actor_id=actor_id, observed_at_utc=observed_at_utc)
        if result.status != "PASS":
            return self._block(command, "GSDLC13D01_STORY_START_BLOCK", result.message, data=result.data)
        context = self.context_resolver.resolve()
        workspace_id = str(context.active_workspace_id or "").strip()
        workspace = Path(context.effective_workspace_root).resolve()
        store = StoryExecutionStore(workspace, workspace_id=workspace_id)
        authority = self._authority(workspace, workspace_id, store)
        if isinstance(authority, CommandResult):
            return authority
        return self._pass(command, result.message, self._projection(store, authority, store.load_state()))

    def _authority_or_raise(self, workspace: Path, workspace_id: str, store: StoryExecutionStore) -> dict[str, Any]:
        authority = self._authority(workspace, workspace_id, store)
        if isinstance(authority, CommandResult):
            raise RuntimeError(authority.message)
        return authority

    def _authority(self, workspace: Path, workspace_id: str, store: StoryExecutionStore) -> dict[str, Any] | CommandResult:
        command = "story activation status"
        sprint_path = workspace / "outputs" / "planning" / "gsdlc_08_d" / self._safe(workspace_id) / "sprint_planner.json"
        if not sprint_path.is_file():
            return self._block(command, "GSDLC13D01_FROZEN_SPRINT_MISSING_BLOCK", "Story activation requires the FROZEN SprintPlan runtime authority.")
        try:
            sprint_record = json.loads(sprint_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return self._block(command, "GSDLC13D01_FROZEN_SPRINT_READ_BLOCK", f"FROZEN SprintPlan could not be read: {exc}")
        if str(sprint_record.get("lifecycle") or "") != "FROZEN":
            return self._block(command, "GSDLC13D01_FROZEN_SPRINT_REQUIRED_BLOCK", "Story activation requires SprintPlan lifecycle FROZEN.")
        sprint_plan = sprint_record.get("sprint_plan") if isinstance(sprint_record.get("sprint_plan"), dict) else {}
        backlog = sprint_record.get("backlog") if isinstance(sprint_record.get("backlog"), dict) else {}
        stories = [x for x in backlog.get("stories") or [] if isinstance(x, dict)]
        stories_by_id = {str(x.get("id") or ""): x for x in stories if str(x.get("id") or "")}
        completed = set(str(x) for x in sprint_plan.get("completed_story_ids") or [] if str(x)) | store.completed_story_ids()
        selected = [x for x in sprint_plan.get("selected_stories") or [] if isinstance(x, dict)]
        candidates: list[dict[str, Any]] = []
        for idx, row in enumerate(selected):
            sid = str(row.get("story_id") or "")
            story = stories_by_id.get(sid)
            if not sid or story is None or sid in completed:
                continue
            blockers = [str(x) for x in row.get("blocking_reasons") or [] if str(x)]
            if str(row.get("readiness") or "") != "READY" or blockers:
                continue
            candidates.append({
                "story_id": sid,
                "story_version": str(story.get("version") or ""),
                "title": str(story.get("title") or sid),
                "acceptance_criteria": [str(x) for x in story.get("acceptance_criteria") or [] if str(x)],
                "trace_links": [dict(x) for x in story.get("trace_links") or [] if isinstance(x, dict)],
                "estimate": row.get("estimate"),
                "readiness": "READY",
                "blocking_reasons": [],
                "sprint_order": idx,
            })
        return {
            "sprint_path": str(sprint_path.relative_to(workspace)).replace("\\", "/"),
            "sprint_record": sprint_record,
            "sprint_plan_id": str(sprint_plan.get("sprint_plan_id") or ""),
            "sprint_lifecycle": "FROZEN",
            "definition_of_ready": [str(x) for x in sprint_plan.get("definition_of_ready") or [] if str(x)],
            "ready_candidates": candidates,
            "stories_by_id": stories_by_id,
            "completed_story_ids": sorted(completed),
        }

    def _projection(self, store: StoryExecutionStore, authority: dict[str, Any], current) -> dict[str, Any]:
        state = current.to_dict() if current is not None else None
        dor = store.load_dor() if current is not None else None
        context_pack = store.load_context() if current is not None else None
        activation = self._activation_summary(authority, store, state=state)
        return {
            "story_activation": activation,
            "story_execution_state": state,
            "dor_report": dor,
            "context_pack": context_pack,
            "implementation_route": {
                "manual": {"available": True, "first_class": True, "source_write": "approval-gated", "terminal_required": False},
                "agent_assisted": {"available": True, "modes": ["mock", "fake-local"], "proposal_only": True, "source_write_authority": False, "approval_authority": False},
                "real_local_model_required": False,
                "external_api_required": False,
                "network_required": False,
                "model_route_grants_tool_authority": False,
                "model_route_grants_apply_authority": False,
                "model_route_grants_approval_authority": False,
            },
            "safety": {
                "runtime_only_story_state": True,
                "planning_artifacts_mutated": False,
                "source_mutations_performed": False,
                "network_used": False,
                "external_api_used": False,
                "operator_project_writes_required": False,
            },
        }

    def _activation_summary(self, authority: dict[str, Any], store: StoryExecutionStore, *, state: dict[str, Any] | None = None) -> dict[str, Any]:
        if state is None:
            current = store.load_state()
            state = current.to_dict() if current is not None else None
        status = str((state or {}).get("status") or "NONE")
        available = state is None or status == "DONE"
        candidates = list(authority["ready_candidates"])
        return {
            "status": "READY_TO_PREPARE" if available and candidates else ("ACTIVE" if state is not None and status != "DONE" else "NO_READY_STORY"),
            "available": bool(available and candidates),
            "sprint_plan_id": authority["sprint_plan_id"],
            "sprint_lifecycle": authority["sprint_lifecycle"],
            "definition_of_ready": authority["definition_of_ready"],
            "completed_story_ids": authority["completed_story_ids"],
            "ready_candidates": candidates,
            "recommended_story_id": candidates[0]["story_id"] if available and candidates else None,
            "current_story_id": (state or {}).get("story_id"),
            "current_story_status": status,
            "next_action": "PREPARE_READY_STORY" if available and candidates else ("START_PLANNED_STORY" if status == "PLANNED" else ("CONTINUE_ACTIVE_STORY" if state is not None and status != "DONE" else "NO_READY_STORY")),
            "server_authoritative": True,
        }

    def _source_fragments(self, workspace: Path, story: dict[str, Any]) -> dict[str, dict[str, Any]]:
        fragments: dict[str, dict[str, Any]] = {}
        for link in story.get("trace_links") or []:
            if not isinstance(link, dict):
                continue
            kind = str(link.get("kind") or "").strip()
            target = str(link.get("target_id") or "").strip()
            if not target:
                continue
            path: Path | None = None
            if kind == "requirement":
                path = workspace / "docs" / "01_requirements" / "requirements_specification.md"
            elif kind == "adr":
                adr_root = workspace / "docs" / "02_architecture" / "adrs"
                if adr_root.is_dir():
                    direct = adr_root / f"{target}.md"
                    if direct.is_file():
                        path = direct
                    else:
                        for candidate in sorted(adr_root.glob("*.md")):
                            if target.lower() in candidate.name.lower() or target.lower() in candidate.read_text(encoding="utf-8", errors="ignore").lower():
                                path = candidate
                                break
            elif kind == "risk":
                path = workspace / "docs" / "03_security" / "security_threat_model.md"
            elif kind == "test-intent":
                path = workspace / "docs" / "04_quality" / "test_strategy.md"
            if path is None or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            content = self._markdown_fragment(text, target)
            if not content:
                continue
            fragments[target] = {
                "content": content,
                "source_ref": str(path.relative_to(workspace)).replace("\\", "/") + f"#{target}",
                "authority_scope": "current-active/frozen-pre-code",
            }
        return fragments

    @staticmethod
    def _markdown_fragment(text: str, target: str, *, max_chars: int = 4000) -> str:
        lines = text.splitlines()
        needle = target.lower()
        hit = next((i for i, line in enumerate(lines) if needle in line.lower()), None)
        if hit is None:
            return ""
        heading = re.compile(r"^(#{1,6})\s+")
        start = hit
        level = 7
        for idx in range(hit, -1, -1):
            match = heading.match(lines[idx].strip())
            if match:
                start = idx
                level = len(match.group(1))
                break
        end = min(len(lines), hit + 12)
        if level <= 6:
            end = len(lines)
            for idx in range(start + 1, len(lines)):
                match = heading.match(lines[idx].strip())
                if match and len(match.group(1)) <= level:
                    end = idx
                    break
        fragment = "\n".join(lines[start:end]).strip()
        return fragment[:max_chars]

    @staticmethod
    def _safe(value: str) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "-" for c in str(value)).strip("-") or "platform"

    @staticmethod
    def _pass(command: str, message: str, data: dict[str, Any]) -> CommandResult:
        return CommandResult(command, True, ExitCode.PASS, message, data=data, findings=[])

    @staticmethod
    def _block(command: str, code: str, message: str, *, data: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data=data or {}, findings=[Finding(code, message, Severity.BLOCK)])
