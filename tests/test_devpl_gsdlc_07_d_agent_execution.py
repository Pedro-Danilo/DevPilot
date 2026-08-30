from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.agents.execution_policy import AgentExecutionPolicy, ToolIntent
from devpilot_core.multiagent.supervisor import HandoffSupervisor

ROOT = Path(__file__).resolve().parents[1]


def fresh_policy(tmp_path: Path) -> AgentExecutionPolicy:
    # Runtime store is intentionally under repo outputs; clear it between tests.
    policy = AgentExecutionPolicy(ROOT)
    if policy.store_path.exists(): policy.store_path.unlink()
    return policy


def create(policy: AgentExecutionPolicy, role='requirements', step='requirements') -> str:
    result = policy.create_session(role_id=role, step_id=step, actor_id='owner-local', mode='fake-local')
    assert result.ok, result.to_dict()
    return result.data['summary']['session_id']


def test_07_d_policy_contract_and_authority_boundaries(tmp_path: Path) -> None:
    policy = fresh_policy(tmp_path)
    result = policy.snapshot()
    assert result.ok
    summary = result.data['summary']
    assert summary['tool_intent_contract'] == 'ToolIntent'
    assert summary['tool_execution_decision_contract'] == 'ToolExecutionDecision'
    assert summary['decision_authority'] == ['PolicyEngine', 'RBAC', 'Approval']
    assert summary['model_route_grants_tool_permission'] is False
    assert summary['agent_self_approval'] is False
    assert summary['real_mcp_execution_enabled'] is False
    assert summary['autonomous_recovery_enabled'] is False


def test_07_d_safe_fake_local_policy_check_executes_only_after_decision(tmp_path: Path) -> None:
    policy = fresh_policy(tmp_path); session_id = create(policy)
    result = policy.evaluate_intent(ToolIntent(session_id=session_id, agent_role_id='requirements', step_id='requirements', tool_id='policy.check', action='read', subject='local-policy', model_route_decision_ref='route-does-not-grant-tools'), actor_id='owner-local', role_at_decision='owner')
    assert result.ok, result.to_dict()
    decision = result.data['tool_execution_decision']
    assert decision['executable'] is True
    assert decision['tool_executed'] is True
    assert decision['model_route_granted_permission'] is False


def test_07_d_forbidden_filesystem_delete_is_never_executable(tmp_path: Path) -> None:
    policy = fresh_policy(tmp_path); session_id = create(policy)
    result = policy.evaluate_intent(ToolIntent(session_id=session_id, agent_role_id='requirements', step_id='requirements', tool_id='filesystem.delete', action='delete', subject='important.txt', model_route_decision_ref='model-selected-delete'), actor_id='owner-local', role_at_decision='owner')
    assert not result.ok
    decision = result.data['tool_execution_decision']
    assert decision['executable'] is False
    assert decision['tool_executed'] is False
    assert decision['model_route_granted_permission'] is False


def test_07_d_approval_bypass_for_tests_run_blocks(tmp_path: Path) -> None:
    policy = fresh_policy(tmp_path); session_id = create(policy, role='test', step='test-plan')
    result = policy.evaluate_intent(ToolIntent(session_id=session_id, agent_role_id='test', step_id='test-plan', tool_id='tests.run', action='execute', subject='pytest', dry_run=True), actor_id='owner-local', role_at_decision='owner')
    assert not result.ok
    assert result.data['tool_execution_decision']['approval_required'] is True
    assert result.data['tool_execution_decision']['tool_executed'] is False


def test_07_d_budget_and_iteration_caps_are_server_side(tmp_path: Path) -> None:
    policy = fresh_policy(tmp_path); session_id = create(policy)
    cost = policy.evaluate_intent(ToolIntent(session_id=session_id, agent_role_id='requirements', step_id='requirements', tool_id='policy.check', action='read', subject='cost', estimated_cost_usd=0.01), actor_id='owner-local')
    assert not cost.ok
    assert 'cost limit' in cost.message.lower()
    policy = fresh_policy(tmp_path); session_id = create(policy)
    store = policy._load_store(); store['sessions'][session_id]['steps_used'] = store['sessions'][session_id]['limits']['max_steps']; policy._save_store(store)
    capped = policy.evaluate_intent(ToolIntent(session_id=session_id, agent_role_id='requirements', step_id='requirements', tool_id='policy.check', action='read', subject='steps'), actor_id='owner-local')
    assert not capped.ok
    assert 'max-steps' in capped.message.lower()


def test_07_d_cancel_and_kill_make_future_intents_non_executable(tmp_path: Path) -> None:
    policy = fresh_policy(tmp_path); session_id = create(policy)
    assert policy.cancel(session_id, actor_id='owner-local', reason='operator cancel').ok
    blocked = policy.evaluate_intent(ToolIntent(session_id=session_id, agent_role_id='requirements', step_id='requirements', tool_id='policy.check', action='read', subject='after-cancel'), actor_id='owner-local')
    assert not blocked.ok and blocked.data['tool_execution_decision']['tool_executed'] is False
    policy = fresh_policy(tmp_path); session_id = create(policy)
    assert policy.cancel(session_id, actor_id='owner-local', reason='kill', kill=True).ok
    blocked = policy.evaluate_intent(ToolIntent(session_id=session_id, agent_role_id='requirements', step_id='requirements', tool_id='policy.check', action='read', subject='after-kill'), actor_id='owner-local')
    assert not blocked.ok


def test_07_d_handoff_requires_human_checkpoint_and_does_not_inherit_tool_scope(tmp_path: Path) -> None:
    policy = fresh_policy(tmp_path); session_id = create(policy)
    supervisor = HandoffSupervisor(ROOT)
    denied = supervisor.transfer(session_id, to_role_id='review', to_step_id='validation', reason='review', human_checkpoint=False, actor_id='owner-local')
    assert not denied.ok
    allowed = supervisor.transfer(session_id, to_role_id='review', to_step_id='validation', reason='review', human_checkpoint=True, actor_id='owner-local')
    assert allowed.ok
    assert allowed.data['summary']['scope_inherited'] is False
    blocked = policy.evaluate_intent(ToolIntent(session_id=session_id, agent_role_id='review', step_id='validation', tool_id='traceability.coverage', action='read', subject='old-scope'), actor_id='owner-local')
    assert not blocked.ok


def test_07_d_mcp_and_autonomous_recovery_remain_disabled(tmp_path: Path) -> None:
    policy = fresh_policy(tmp_path); session_id = create(policy)
    mcp = policy.evaluate_intent(ToolIntent(session_id=session_id, agent_role_id='requirements', step_id='requirements', tool_id='mcp.real.write', action='execute', subject='mcp', arguments={'real_mcp': True}), actor_id='owner-local')
    assert not mcp.ok and mcp.data['tool_execution_decision']['tool_executed'] is False
    auto = policy.evaluate_intent(ToolIntent(session_id=session_id, agent_role_id='requirements', step_id='requirements', tool_id='policy.check', action='autonomous-recovery', subject='self', arguments={'autonomous_recovery': True}), actor_id='owner-local')
    assert not auto.ok


def test_07_d_schemas_and_policy_files_are_registered_sources() -> None:
    assert (ROOT / '.devpilot/agents/agent_execution_policy.json').is_file()
    payload = json.loads((ROOT / '.devpilot/agents/agent_execution_policy.json').read_text())
    assert payload['authority_invariants']['model_route_can_grant_tool_permission'] is False
    assert 'filesystem.delete' in payload['global_forbidden_tools']
    for rel in ('docs/schemas/agent_execution_policy.schema.json','docs/schemas/tool_intent.schema.json','docs/schemas/tool_execution_decision.schema.json','docs/schemas/handoff_transfer_state.schema.json'):
        assert (ROOT / rel).is_file()
