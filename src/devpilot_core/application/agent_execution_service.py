from __future__ import annotations
from pathlib import Path
from typing import Any

from devpilot_core.agents.execution_policy import AgentExecutionPolicy, ToolIntent
from devpilot_core.cli_models import CommandResult
from devpilot_core.multiagent.supervisor import HandoffSupervisor

class AgentExecutionApplicationService:
    """Application boundary for GSDLC-07-D bounded agent execution controls."""
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.policy = AgentExecutionPolicy(self.root)
        self.handoffs = HandoffSupervisor(self.root)

    def snapshot(self) -> CommandResult:
        return self.policy.snapshot()

    def create_session(self, *, role_id: str, step_id: str, actor_id: str, mode: str = 'fake-local') -> CommandResult:
        return self.policy.create_session(role_id=role_id, step_id=step_id, actor_id=actor_id, mode=mode)

    def tool_intent(self, *, session_id: str, payload: dict[str, Any], actor_id: str, role_at_decision: str | None = None) -> CommandResult:
        intent = ToolIntent(
            session_id=session_id, agent_role_id=str(payload.get('agent_role_id') or ''), step_id=str(payload.get('step_id') or ''),
            tool_id=str(payload.get('tool_id') or ''), action=str(payload.get('action') or 'read'), subject=str(payload.get('subject') or 'local-fixture'),
            arguments=dict(payload.get('arguments') or {}), dry_run=bool(payload.get('dry_run', True)), approval_id=(str(payload.get('approval_id')) if payload.get('approval_id') else None),
            model_route_decision_ref=(str(payload.get('model_route_decision_ref')) if payload.get('model_route_decision_ref') else None),
            estimated_input_tokens=max(0, int(payload.get('estimated_input_tokens') or 0)), estimated_output_tokens=max(0, int(payload.get('estimated_output_tokens') or 0)), estimated_cost_usd=max(0.0, float(payload.get('estimated_cost_usd') or 0.0)),
        )
        return self.policy.evaluate_intent(intent, actor_id=actor_id, role_at_decision=role_at_decision)

    def handoff(self, *, session_id: str, to_role_id: str, to_step_id: str, reason: str, human_checkpoint: bool, actor_id: str) -> CommandResult:
        return self.handoffs.transfer(session_id, to_role_id=to_role_id, to_step_id=to_step_id, reason=reason, human_checkpoint=human_checkpoint, actor_id=actor_id)

    def cancel(self, *, session_id: str, actor_id: str, reason: str, kill: bool = False) -> CommandResult:
        return self.policy.cancel(session_id, actor_id=actor_id, reason=reason, kill=kill)
