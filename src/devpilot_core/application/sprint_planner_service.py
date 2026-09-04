from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.planning.sprint_planner import SprintPlanner
from devpilot_core.planning.service import PlanningPolicyError
from .ui_workspace_context import UiWorkspaceContextResolver


class SprintPlannerApplicationService:
    """Application boundary for GSDLC-08-D. No HTTP/UI route is introduced in D."""
    def __init__(self, root: Path, *, context_resolver: UiWorkspaceContextResolver) -> None:
        self.root=Path(root).resolve(); self.context_resolver=context_resolver
    def _workbench(self) -> SprintPlanner:
        context=self.context_resolver.resolve()
        if context.configured and not context.valid:
            raise PlanningPolicyError("SPRINT_WORKSPACE_CONTEXT_BLOCK","Configured project workspace context is invalid.")
        return SprintPlanner(context.effective_workspace_root,workspace_id=context.active_workspace_id or context.effective_workspace_root.name)
    def status(self, *, effective_roles:list[str]) -> CommandResult:
        return self._call("planning.sprint.status",lambda wb:wb.status(effective_roles=effective_roles))
    def propose(self, *, sprint_plan:dict[str,Any], backlog:dict[str,Any], dependencies:list[dict[str,Any]], actor_id:str, actor_role:str) -> CommandResult:
        return self._call("planning.sprint.propose",lambda wb:wb.propose(sprint_plan=sprint_plan,backlog=backlog,dependencies=dependencies,actor_id=actor_id,actor_role=actor_role))
    def review(self, *, actor_id:str, actor_role:str) -> CommandResult: return self._call("planning.sprint.review",lambda wb:wb.review(actor_id=actor_id,actor_role=actor_role))
    def approve(self, *, actor_id:str, actor_role:str) -> CommandResult: return self._call("planning.sprint.approve",lambda wb:wb.approve(actor_id=actor_id,actor_role=actor_role))
    def freeze(self, *, actor_id:str, actor_role:str) -> CommandResult: return self._call("planning.sprint.freeze",lambda wb:wb.freeze(actor_id=actor_id,actor_role=actor_role))
    def _call(self, operation:str, fn) -> CommandResult:
        try:
            data=fn(self._workbench()); return CommandResult(operation,True,ExitCode.PASS,f"{operation} PASS",data={"sprint_planner":data},findings=[])
        except PlanningPolicyError as exc:
            return CommandResult(operation,False,ExitCode.BLOCK,str(exc),data={},findings=[Finding(exc.code,str(exc),Severity.BLOCK)])
        except (ValueError,TypeError,json.JSONDecodeError) as exc:
            return CommandResult(operation,False,ExitCode.BLOCK,str(exc),data={},findings=[Finding("SPRINT_INPUT_INVALID",str(exc),Severity.BLOCK)])
