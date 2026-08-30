from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.agents.execution_policy import AgentExecutionPolicy
from devpilot_core.agents.role_bindings import AgentRoleBindingCatalog
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


@dataclass(frozen=True)
class HandoffTransferState:
    transfer_id: str
    session_id: str
    from_role_id: str
    to_role_id: str
    from_step_id: str
    to_step_id: str
    reason: str
    human_checkpoint: bool
    scope_inherited: bool
    status: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class HandoffSupervisor:
    """07-D successor supervisor: explicit transfer, no scope inheritance."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.execution = AgentExecutionPolicy(self.root)
        self.bindings = AgentRoleBindingCatalog(self.root)

    def transfer(self, session_id: str, *, to_role_id: str, to_step_id: str, reason: str, human_checkpoint: bool, actor_id: str) -> CommandResult:
        store = self.execution._load_store()
        session = store.get('sessions', {}).get(session_id)
        if not isinstance(session, dict):
            return CommandResult('agent handoff', False, ExitCode.BLOCK, 'Session not found.', {}, [Finding('HANDOFF_SESSION_NOT_FOUND', 'Execution session was not found.', Severity.BLOCK)])
        if session.get('status') != 'active':
            return CommandResult('agent handoff', False, ExitCode.BLOCK, 'Only active sessions may hand off.', {}, [Finding('HANDOFF_SESSION_TERMINAL', 'Session is not active.', Severity.BLOCK)])
        binding = self.bindings.binding(to_step_id)
        role = self.bindings.role(to_role_id)
        if role is None or binding is None or binding.agent_role_id != to_role_id:
            return CommandResult('agent handoff', False, ExitCode.BLOCK, 'Target role/step binding is invalid.', {}, [Finding('HANDOFF_TARGET_SCOPE_BLOCK', 'Target role does not own the target step.', Severity.BLOCK)])
        if not human_checkpoint:
            return CommandResult('agent handoff', False, ExitCode.BLOCK, 'Human checkpoint is required for 07-D handoff.', {}, [Finding('HANDOFF_HUMAN_CHECKPOINT_REQUIRED', 'Handoff requires explicit human checkpoint.', Severity.BLOCK)])
        transfer = HandoffTransferState(
            transfer_id=f'ht_{uuid.uuid4().hex}', session_id=session_id,
            from_role_id=str(session['role_id']), to_role_id=to_role_id,
            from_step_id=str(session['step_id']), to_step_id=to_step_id,
            reason=reason, human_checkpoint=True, scope_inherited=False, status='transferred', created_at=_now(),
        )
        session.setdefault('handoffs', []).append(transfer.to_dict())
        session['role_id'] = to_role_id; session['step_id'] = to_step_id; session['tool_scope_inherited'] = False; session['last_updated_at'] = _now()
        self.execution._save_store(store)
        return CommandResult('agent handoff', True, ExitCode.PASS, 'Explicit handoff transferred with human checkpoint and isolated tool scope.',
                             {'summary': {'transfer_id': transfer.transfer_id, 'status': 'transferred', 'human_checkpoint': True, 'scope_inherited': False, 'actor_id': actor_id, 'source_mutations_performed': False}, 'transfer': transfer.to_dict(), 'target_tool_allowlist': list(role.tool_allowlist)}, [])
