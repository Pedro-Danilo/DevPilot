from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.planning.backlog_workbench import BacklogWorkbench
from devpilot_core.planning.service import PlanningPolicyError
from .ui_workspace_context import UiWorkspaceContextResolver


class BacklogWorkbenchApplicationService:
    """Application boundary for GSDLC-08-C. No HTTP/UI route is introduced in C."""
    def __init__(self, root: Path, *, context_resolver: UiWorkspaceContextResolver) -> None:
        self.root=Path(root).resolve(); self.context_resolver=context_resolver
    def _workbench(self) -> BacklogWorkbench:
        context=self.context_resolver.resolve()
        if context.configured and not context.valid:
            raise PlanningPolicyError("BACKLOG_WORKSPACE_CONTEXT_BLOCK","Configured project workspace context is invalid.")
        return BacklogWorkbench(context.effective_workspace_root,workspace_id=context.active_workspace_id or context.effective_workspace_root.name)
    def status(self, *, effective_roles:list[str]) -> CommandResult:
        return self._call("planning.backlog.status",lambda wb:wb.status(effective_roles=effective_roles))
    def propose(self, *, mode:str, backlog:dict[str,Any], required_requirement_ids:list[str], roadmap_milestone_ids:list[str], known_adr_ids:list[str], known_risk_ids:list[str], known_test_intent_ids:list[str], actor_id:str, actor_role:str, source_label:str) -> CommandResult:
        return self._call("planning.backlog.propose",lambda wb:wb.propose(mode=mode,backlog=backlog,required_requirement_ids=required_requirement_ids,roadmap_milestone_ids=roadmap_milestone_ids,known_adr_ids=known_adr_ids,known_risk_ids=known_risk_ids,known_test_intent_ids=known_test_intent_ids,actor_id=actor_id,actor_role=actor_role,source_label=source_label))
    def review(self, *, actor_id:str, actor_role:str) -> CommandResult: return self._call("planning.backlog.review",lambda wb:wb.review(actor_id=actor_id,actor_role=actor_role))
    def approve(self, *, actor_id:str, actor_role:str) -> CommandResult: return self._call("planning.backlog.approve",lambda wb:wb.approve(actor_id=actor_id,actor_role=actor_role))
    def freeze(self, *, actor_id:str, actor_role:str) -> CommandResult: return self._call("planning.backlog.freeze",lambda wb:wb.freeze(actor_id=actor_id,actor_role=actor_role))
    def _call(self, operation:str, fn) -> CommandResult:
        try:
            data=fn(self._workbench()); return CommandResult(operation,True,ExitCode.PASS,f"{operation} PASS",data={"backlog_workbench":data},findings=[])
        except PlanningPolicyError as exc:
            return CommandResult(operation,False,ExitCode.BLOCK,str(exc),data={},findings=[Finding(exc.code,str(exc),Severity.BLOCK)])
        except (ValueError,TypeError,json.JSONDecodeError) as exc:
            return CommandResult(operation,False,ExitCode.BLOCK,str(exc),data={},findings=[Finding("BACKLOG_INPUT_INVALID",str(exc),Severity.BLOCK)])
