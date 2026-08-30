from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.agents.role_bindings import AgentRoleBindingCatalog
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest

POLICY_PATH = Path('.devpilot/agents/agent_execution_policy.json')
TOOL_REGISTRY_PATH = Path('.devpilot/miasi/tool_registry.json')
RUNTIME_STORE_PATH = Path('outputs/runtime/gsdlc_07_d_agent_execution.json')
GLOBAL_FORBIDDEN = {
    'filesystem.delete', 'connector.write', 'plugin.code.execute',
    'remote.runner.execute', 'rollback.execute',
}
SAFE_FAKE_LOCAL_EXECUTABLE = {'policy.check'}
TERMINAL_SESSION_STATES = {'cancelled', 'killed', 'blocked-budget', 'blocked-time'}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class ToolIntent:
    session_id: str
    agent_role_id: str
    step_id: str
    tool_id: str
    action: str
    subject: str
    arguments: dict[str, Any] = field(default_factory=dict)
    dry_run: bool = True
    approval_id: str | None = None
    model_route_decision_ref: str | None = None
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    intent_id: str = field(default_factory=lambda: f'ti_{uuid.uuid4().hex}')
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToolExecutionDecision:
    decision_id: str
    intent_id: str
    effect: str
    executable: bool
    tool_executed: bool
    approval_required: bool
    dry_run_required: bool
    reason: str
    authority: tuple[str, ...]
    policy_ok: bool
    rbac_actor: str | None
    role_scope_ok: bool
    step_scope_ok: bool
    model_route_granted_permission: bool
    session_state: str
    decision_at: str = field(default_factory=_now)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['authority'] = list(self.authority)
        return payload


class AgentExecutionPolicy:
    """GSDLC-07-D deterministic ToolIntent -> ToolExecutionDecision authority.

    The model/agent may propose ToolIntent only.  This class joins exact role and
    step allowlists with MIASI Tool Registry, PolicyEngine/RBAC/Approval and
    server-side limits.  It never delegates permission to ModelRouteDecision.
    Only the explicitly safe `policy.check` tool can be executed in fake-local
    mode in 07-D; mutating tools remain dry-run/approval gated and real MCP,
    autonomous recovery, shell, remote and destructive execution stay disabled.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.role_catalog = AgentRoleBindingCatalog(self.root)
        self.policy_engine = PolicyEngine(self.root)
        self.policy = self._load_json(POLICY_PATH)
        tool_payload = self._load_json(TOOL_REGISTRY_PATH)
        self.tools = {str(row['tool_id']): row for row in tool_payload.get('tools', []) if isinstance(row, dict) and row.get('tool_id')}
        self.store_path = self.root / RUNTIME_STORE_PATH

    def _load_json(self, rel: Path) -> dict[str, Any]:
        payload = json.loads((self.root / rel).read_text(encoding='utf-8'))
        if not isinstance(payload, dict):
            raise ValueError(f'{rel} must contain a JSON object')
        return payload

    def snapshot(self) -> CommandResult:
        validation = self.role_catalog.validate()
        payload = {
            'summary': {
                'status': 'PASS' if validation['status'] == 'PASS' else 'BLOCK',
                'tool_intent_contract': 'ToolIntent',
                'tool_execution_decision_contract': 'ToolExecutionDecision',
                'decision_authority': ['PolicyEngine', 'RBAC', 'Approval'],
                'model_route_grants_tool_permission': False,
                'agent_self_approval': False,
                'dry_run_first': True,
                'safe_fake_local_execution_tools': sorted(SAFE_FAKE_LOCAL_EXECUTABLE),
                'real_mcp_execution_enabled': False,
                'autonomous_recovery_enabled': False,
                'arbitrary_shell_enabled': False,
                'network_used': False,
                'external_api_used': False,
                'preliminary': True,
            },
            'policy': self.policy,
            'roles': [role for role in self.role_catalog.roles_payload.get('roles', []) if isinstance(role, dict)],
            'sessions': self._public_sessions(),
            'notes': [
                '07-D is bounded and implemented-initial. Safe fake-local policy.check is the only direct execution fixture.',
                'Mutating and approval-gated tools require deterministic ToolExecutionDecision and remain dry-run-first.',
                'Real MCP write execution and autonomous recovery remain NOT_ENABLED/CANDIDATE_EXPERIMENT.',
            ],
        }
        ok = validation['status'] == 'PASS'
        return CommandResult('settings agent-execution', ok, ExitCode.PASS if ok else ExitCode.BLOCK,
                             'Agent execution policy loaded.' if ok else 'Agent execution policy blocked.', payload,
                             [] if ok else [Finding('GSDLC_07_D_ROLE_BINDING_BLOCK', 'Inherited agent role binding validation failed.', Severity.BLOCK)])

    def create_session(self, *, role_id: str, step_id: str, actor_id: str, mode: str = 'fake-local') -> CommandResult:
        role = self.role_catalog.role(role_id)
        binding = self.role_catalog.binding(step_id)
        findings: list[Finding] = []
        if role is None:
            findings.append(Finding('AGENT_EXECUTION_ROLE_UNKNOWN', 'Agent role is not registered.', Severity.BLOCK))
        if binding is None or binding.agent_role_id != role_id:
            findings.append(Finding('AGENT_EXECUTION_STEP_ROLE_MISMATCH', 'Step binding does not authorize this agent role.', Severity.BLOCK))
        if mode not in {'mock', 'fake-local'}:
            findings.append(Finding('AGENT_EXECUTION_MODE_BLOCK', 'Only mock/fake-local modes are enabled in 07-D.', Severity.BLOCK))
        if findings:
            return CommandResult('agent execution session create', False, ExitCode.BLOCK, 'Session creation blocked.', {'summary': {'created': False}}, findings)
        store = self._load_store()
        session_id = f'aes_{uuid.uuid4().hex}'
        now = time.time()
        session = {
            'session_id': session_id, 'role_id': role_id, 'step_id': step_id, 'actor_id': actor_id, 'mode': mode,
            'status': 'active', 'created_at': _now(), 'created_epoch': now, 'last_updated_at': _now(),
            'limits': dict(role.limits), 'steps_used': 0, 'input_tokens_used': 0, 'output_tokens_used': 0,
            'cost_used_usd': 0.0, 'intents': [], 'decisions': [], 'handoffs': [], 'cancel_requested': False,
            'kill_switch': False, 'tool_scope_inherited': False,
        }
        store['sessions'][session_id] = session
        self._save_store(store)
        return CommandResult('agent execution session create', True, ExitCode.PASS, 'Bounded agent execution session created.',
                             {'summary': {'created': True, 'session_id': session_id, 'role_id': role_id, 'step_id': step_id, 'mode': mode, 'status': 'active', 'source_mutations_performed': False}, 'session': self._public_session(session)}, [])

    def evaluate_intent(self, intent: ToolIntent, *, actor_id: str, role_at_decision: str | None = None) -> CommandResult:
        store = self._load_store()
        session = store['sessions'].get(intent.session_id)
        if not isinstance(session, dict):
            return self._block_intent(intent, 'AGENT_EXECUTION_SESSION_NOT_FOUND', 'Execution session was not found.', actor_id, store=None)
        if session.get('status') in TERMINAL_SESSION_STATES or session.get('cancel_requested') or session.get('kill_switch'):
            return self._block_intent(intent, 'AGENT_EXECUTION_SESSION_TERMINAL', 'Execution session is cancelled/killed/terminal.', actor_id, store=store, session=session)
        if session.get('role_id') != intent.agent_role_id or session.get('step_id') != intent.step_id:
            return self._block_intent(intent, 'AGENT_EXECUTION_SESSION_SCOPE_MISMATCH', 'Intent role/step does not match current session transfer state.', actor_id, store=store, session=session)

        limit_reason = self._limit_violation(session, intent)
        if limit_reason:
            session['status'] = limit_reason[0]
            self._save_store(store)
            return self._block_intent(intent, 'AGENT_EXECUTION_LIMIT_BLOCK', limit_reason[1], actor_id, store=store, session=session)

        role = self.role_catalog.role(intent.agent_role_id)
        binding = self.role_catalog.binding(intent.step_id)
        role_tools = set(role.tool_allowlist if role else ())
        step_tools = set(binding.tool_allowlist if binding else ())
        role_scope_ok = intent.tool_id in role_tools
        step_scope_ok = intent.tool_id in step_tools
        tool = self.tools.get(intent.tool_id)
        global_forbidden = intent.tool_id in GLOBAL_FORBIDDEN
        mcp_forbidden = intent.tool_id.startswith('mcp.') or bool(intent.arguments.get('real_mcp'))
        autonomous_forbidden = bool(intent.arguments.get('autonomous_recovery')) or intent.action in {'autonomous-recovery', 'self-recover'}
        shell_forbidden = intent.action in {'shell', 'execute-shell'} or intent.tool_id in {'shell.raw_execute'}
        approval_required = bool(tool and tool.get('requires_approval'))
        side_effect = str((tool or {}).get('side_effect') or 'unknown')
        dry_run_required = side_effect in {'controlled_write', 'optional_write', 'controlled_execution', 'network_cost'} or approval_required

        preblocks: list[str] = []
        if not role_scope_ok: preblocks.append('tool outside agent role allowlist')
        if not step_scope_ok: preblocks.append('tool outside step allowlist')
        if tool is None: preblocks.append('tool not present in MIASI Tool Registry')
        if global_forbidden: preblocks.append('tool is globally forbidden in 07-D')
        if mcp_forbidden: preblocks.append('real MCP execution is disabled')
        if autonomous_forbidden: preblocks.append('autonomous recovery is disabled')
        if shell_forbidden: preblocks.append('arbitrary shell is disabled')
        if dry_run_required and not intent.dry_run: preblocks.append('mutating/approval-gated tool requires dry-run first')

        policy_result = self.policy_engine.evaluate(PolicyRequest(
            action=intent.action, text=json.dumps(intent.arguments, sort_keys=True), dry_run=intent.dry_run,
            estimated_cost_usd=float(intent.estimated_cost_usd), approval_id=intent.approval_id,
            tool_id=intent.tool_id, subject=intent.subject, actor=actor_id, role_at_decision=role_at_decision,
            tool_call_id=intent.intent_id, interface='agent-runtime', metadata={'agent_role_id': intent.agent_role_id, 'step_id': intent.step_id},
        ))
        policy_ok = policy_result.ok
        if not policy_ok: preblocks.append('PolicyEngine/RBAC/Approval blocked the intent')

        executable = not preblocks
        tool_executed = executable and session.get('mode') == 'fake-local' and intent.tool_id in SAFE_FAKE_LOCAL_EXECUTABLE
        effect = 'ALLOW' if executable else 'BLOCK'
        reason = 'ToolIntent authorized by deterministic policy.' if executable else '; '.join(dict.fromkeys(preblocks))
        decision = ToolExecutionDecision(
            decision_id=f'ted_{uuid.uuid4().hex}', intent_id=intent.intent_id, effect=effect,
            executable=executable, tool_executed=tool_executed, approval_required=approval_required,
            dry_run_required=dry_run_required, reason=reason, authority=('PolicyEngine', 'RBAC', 'Approval'),
            policy_ok=policy_ok, rbac_actor=actor_id, role_scope_ok=role_scope_ok, step_scope_ok=step_scope_ok,
            model_route_granted_permission=False, session_state=str(session.get('status') or 'active'),
            evidence={'tool_registry_side_effect': side_effect, 'model_route_decision_ref': intent.model_route_decision_ref,
                      'policy_result': policy_result.to_dict(), 'fake_local_dispatch': intent.tool_id if tool_executed else None},
        )
        session['steps_used'] = int(session.get('steps_used', 0)) + 1
        session['input_tokens_used'] = int(session.get('input_tokens_used', 0)) + max(0, int(intent.estimated_input_tokens))
        session['output_tokens_used'] = int(session.get('output_tokens_used', 0)) + max(0, int(intent.estimated_output_tokens))
        session['cost_used_usd'] = round(float(session.get('cost_used_usd', 0.0)) + max(0.0, float(intent.estimated_cost_usd)), 8)
        session['intents'].append(intent.to_dict())
        session['decisions'].append(decision.to_dict())
        session['last_updated_at'] = _now()
        self._save_store(store)
        summary = {
            'intent_id': intent.intent_id, 'decision_id': decision.decision_id, 'effect': effect,
            'executable': executable, 'tool_executed': tool_executed, 'approval_required': approval_required,
            'dry_run_required': dry_run_required, 'model_route_grants_tool_permission': False,
            'agent_self_approval': False, 'session_status': session['status'], 'limits': self._usage_summary(session),
            'network_used': False, 'external_api_used': False, 'source_mutations_performed': False,
        }
        return CommandResult('agent execution tool-intent', executable, ExitCode.PASS if executable else ExitCode.BLOCK,
                             'ToolExecutionDecision allows bounded fake-local execution.' if executable else 'ToolExecutionDecision blocks execution.',
                             {'summary': summary, 'tool_intent': intent.to_dict(), 'tool_execution_decision': decision.to_dict(), 'session': self._public_session(session)},
                             [] if executable else [Finding('AGENT_EXECUTION_TOOL_INTENT_BLOCK', reason, Severity.BLOCK)])

    def cancel(self, session_id: str, *, actor_id: str, reason: str, kill: bool = False) -> CommandResult:
        store = self._load_store(); session = store['sessions'].get(session_id)
        if not isinstance(session, dict):
            return CommandResult('agent execution kill' if kill else 'agent execution cancel', False, ExitCode.BLOCK, 'Session not found.', {}, [Finding('AGENT_EXECUTION_SESSION_NOT_FOUND', 'Execution session was not found.', Severity.BLOCK)])
        session['kill_switch'] = bool(kill)
        session['cancel_requested'] = not kill
        session['status'] = 'killed' if kill else 'cancelled'
        session['cancelled_by'] = actor_id; session['cancel_reason'] = reason; session['last_updated_at'] = _now()
        self._save_store(store)
        return CommandResult('agent execution kill' if kill else 'agent execution cancel', True, ExitCode.PASS,
                             'Kill switch applied.' if kill else 'Cancellation applied.',
                             {'summary': {'session_id': session_id, 'status': session['status'], 'kill_switch': bool(kill), 'cancelled': not kill, 'server_enforced': True, 'tool_executed': False, 'source_mutations_performed': False}, 'session': self._public_session(session)}, [])

    def _limit_violation(self, session: dict[str, Any], intent: ToolIntent) -> tuple[str, str] | None:
        limits = session.get('limits') or {}
        if time.time() - float(session.get('created_epoch') or time.time()) > float(limits.get('wall_time_seconds') or 0):
            return ('blocked-time', 'Server-side wall-time limit exhausted.')
        if int(session.get('steps_used', 0)) >= int(limits.get('max_steps') or 0):
            return ('blocked-budget', 'Server-side max-steps limit exhausted.')
        if int(session.get('input_tokens_used', 0)) + int(intent.estimated_input_tokens) > int(limits.get('max_input_tokens') or 0):
            return ('blocked-budget', 'Server-side input-token limit exhausted.')
        if int(session.get('output_tokens_used', 0)) + int(intent.estimated_output_tokens) > int(limits.get('max_output_tokens') or 0):
            return ('blocked-budget', 'Server-side output-token limit exhausted.')
        if float(session.get('cost_used_usd', 0.0)) + float(intent.estimated_cost_usd) > float(limits.get('max_cost_usd') or 0.0):
            return ('blocked-budget', 'Server-side cost limit exhausted.')
        return None

    def _block_intent(self, intent: ToolIntent, code: str, reason: str, actor_id: str, *, store: dict[str, Any] | None, session: dict[str, Any] | None = None) -> CommandResult:
        decision = ToolExecutionDecision(f'ted_{uuid.uuid4().hex}', intent.intent_id, 'BLOCK', False, False, False, False, reason,
                                         ('PolicyEngine', 'RBAC', 'Approval'), False, actor_id, False, False, False,
                                         str((session or {}).get('status') or 'missing'))
        if store is not None and session is not None:
            session.setdefault('intents', []).append(intent.to_dict()); session.setdefault('decisions', []).append(decision.to_dict()); self._save_store(store)
        return CommandResult('agent execution tool-intent', False, ExitCode.BLOCK, reason,
                             {'summary': {'effect': 'BLOCK', 'executable': False, 'tool_executed': False, 'model_route_grants_tool_permission': False}, 'tool_intent': intent.to_dict(), 'tool_execution_decision': decision.to_dict()},
                             [Finding(code, reason, Severity.BLOCK)])

    def _usage_summary(self, session: dict[str, Any]) -> dict[str, Any]:
        return {k: session.get(k) for k in ('steps_used', 'input_tokens_used', 'output_tokens_used', 'cost_used_usd')} | {'configured': session.get('limits', {})}

    def _load_store(self) -> dict[str, Any]:
        if not self.store_path.is_file(): return {'schema_version': '1.0', 'sessions': {}}
        try:
            payload = json.loads(self.store_path.read_text(encoding='utf-8'))
        except Exception:
            return {'schema_version': '1.0', 'sessions': {}}
        if not isinstance(payload, dict) or not isinstance(payload.get('sessions'), dict): return {'schema_version': '1.0', 'sessions': {}}
        return payload

    def _save_store(self, payload: dict[str, Any]) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    def _public_sessions(self) -> list[dict[str, Any]]:
        return [self._public_session(v) for v in self._load_store().get('sessions', {}).values() if isinstance(v, dict)][-20:]

    @staticmethod
    def _public_session(session: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in session.items() if k not in {'created_epoch'}}
