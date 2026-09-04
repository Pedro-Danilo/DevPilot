from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.planning.roadmap_workbench import RoadmapWorkbench
from devpilot_core.planning.service import PlanningPolicyError

from .ui_workspace_context import UiWorkspaceContextResolver


class RoadmapWorkbenchApplicationService:
    def __init__(self, root: Path, *, context_resolver: UiWorkspaceContextResolver) -> None:
        self.root = Path(root).resolve()
        self.context_resolver = context_resolver

    def _workbench(self) -> RoadmapWorkbench:
        context = self.context_resolver.resolve()
        if context.configured and not context.valid:
            raise PlanningPolicyError("ROADMAP_WORKSPACE_CONTEXT_BLOCK", "Configured project workspace context is invalid.")
        return RoadmapWorkbench(context.effective_workspace_root, workspace_id=context.active_workspace_id or context.effective_workspace_root.name)

    def status(self, *, effective_roles: list[str]) -> CommandResult:
        return self._call("planning.roadmap.status", lambda wb: wb.status(effective_roles=effective_roles))

    def propose(self, *, mode: str, roadmap: dict[str, Any], required_requirement_ids: list[str], required_risk_ids: list[str], actor_id: str, actor_role: str, source_label: str) -> CommandResult:
        return self._call("planning.roadmap.propose", lambda wb: wb.propose(mode=mode, roadmap=roadmap, required_requirement_ids=required_requirement_ids, required_risk_ids=required_risk_ids, actor_id=actor_id, actor_role=actor_role, source_label=source_label))

    def review(self, *, actor_id: str, actor_role: str) -> CommandResult:
        return self._call("planning.roadmap.review", lambda wb: wb.review(actor_id=actor_id, actor_role=actor_role))

    def approve(self, *, actor_id: str, actor_role: str) -> CommandResult:
        return self._call("planning.roadmap.approve", lambda wb: wb.approve(actor_id=actor_id, actor_role=actor_role))

    def freeze(self, *, actor_id: str, actor_role: str) -> CommandResult:
        return self._call("planning.roadmap.freeze", lambda wb: wb.freeze(actor_id=actor_id, actor_role=actor_role))

    def _call(self, operation: str, fn) -> CommandResult:
        try:
            data = fn(self._workbench())
            return CommandResult(operation, True, ExitCode.PASS, f"{operation} PASS", data={"roadmap_workbench": data}, findings=[])
        except PlanningPolicyError as exc:
            return CommandResult(operation, False, ExitCode.BLOCK, str(exc), data={}, findings=[Finding(exc.code, str(exc), Severity.BLOCK)])
        except (ValueError, TypeError, json.JSONDecodeError) as exc:  # type: ignore[name-defined]
            return CommandResult(operation, False, ExitCode.BLOCK, str(exc), data={}, findings=[Finding("ROADMAP_INPUT_INVALID", str(exc), Severity.BLOCK)])
