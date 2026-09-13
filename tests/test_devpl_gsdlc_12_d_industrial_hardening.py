from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.security.industrial_hardening import IndustrialHardeningEvaluator

ROOT = Path(__file__).resolve().parents[1]


def evaluator() -> IndustrialHardeningEvaluator:
    return IndustrialHardeningEvaluator(ROOT)


def test_12_d_policy_is_current_active_local_first_and_full_remains_reserved() -> None:
    policy = json.loads((ROOT / '.devpilot/security/industrial_hardening_policy.json').read_text(encoding='utf-8'))
    assert policy['status'] == 'current-active'
    assert policy['local_only'] is True
    assert policy['network_allowed'] is False
    assert policy['external_api_allowed'] is False
    assert policy['real_mcp_write_allowed'] is False
    assert policy['model_may_grant_tool_permission'] is False
    state = json.loads((ROOT / '.devpilot/project_state.json').read_text(encoding='utf-8'))
    assert state['gsdlc_12_full_regression_budget_consumed'] == 0
    assert state['gsdlc_12_full_regression_budget_total'] == 1
    assert state['gsdlc_12_full_regression_reserved_for'] == 'DEVPL-GSDLC-12-E'


def test_12_d_performance_baseline_respects_hard_ceilings() -> None:
    report = evaluator().performance_baseline(large_fixture_files=400)
    assert report['status'] == 'PASS', report
    assert all(report['hard_ceiling_checks'].values())
    assert report['network_used'] is False
    assert report['external_api_used'] is False
    assert report['runtime_stores_copied'] is False


def test_12_d_red_team_closes_all_s0_s1_and_uses_only_safe_local_fakes() -> None:
    report = evaluator().red_team()
    assert report['status'] == 'PASS', report
    assert report['s0_open'] == 0
    assert report['s1_open'] == 0
    assert report['network_used'] is False
    assert report['external_api_used'] is False
    assert report['real_mcp_used'] is False
    assert report['harmful_package_used'] is False
    by_id = {item['id']: item for item in report['findings']}
    required = {
        'CSRF-MISMATCH', 'SESSION-FIXATION-ROTATION', 'ROLE-DOWNGRADE-STALE-SESSION',
        'CROSS-WORKSPACE-SCOPE', 'PATH-ESCAPE', 'DESTRUCTIVE-FILESYSTEM', 'SYMLINK-REPARSE-ESCAPE',
        'ARCHIVE-PATH-TRAVERSAL', 'MODEL-ROUTE-TOOL-ESCALATION', 'PROMPT-INJECTION-FORBIDDEN-TOOL',
        'CONSUMER-SESSION-PIGGYBACK', 'CROSS-ACTOR-CANCEL', 'OVERSIZED-AGENT-INPUT',
        'AUTONOMOUS-RECOVERY-AFTER-ERROR', 'REAL-MCP-WRITE',
        'TOKEN-COST-BUDGET-ABUSE', 'HIDDEN-EXTERNAL-FALLBACK',
        'STALE-PROVIDER-EVIDENCE', 'APPROVAL-REUSE-HASH-MISMATCH', 'DUPLICATE-EXECUTE-IDEMPOTENCY', 'SUPPLY-CHAIN-BYPASS',
        'GUIDED-EXPERT-AUTHORITY-PARITY',
    }
    assert required <= set(by_id)
    assert all(by_id[item]['status'] == 'PASS' for item in required)


def test_12_d_resource_and_cost_ceilings_are_server_side_and_bounded() -> None:
    report = evaluator().resource_cost()
    assert report['status'] == 'PASS', report
    assert all(report['checks'].values())
    assert report['ceilings']['autonomous_loop_max_iterations'] == 0
    assert report['observed']['story_validation_safety']['full_regression_allowed'] is False


def test_12_d_model_route_decision_is_not_tool_execution_authority() -> None:
    route_source = (ROOT / 'src/devpilot_core/modeling/model_router_v2.py').read_text(encoding='utf-8')
    tool_source = (ROOT / 'src/devpilot_core/agents/execution_policy.py').read_text(encoding='utf-8')
    assert 'Deliberately no tool/skill permission fields' in route_source
    assert "model_route_granted_permission=False" in tool_source
    assert "decision_authority': ['PolicyEngine', 'RBAC', 'Approval']" in tool_source


def test_12_d_no_ux_change_reuses_hash_bound_12_c_browser_acceptance() -> None:
    binding = json.loads((ROOT / 'docs/audits/DEVPL_GSDLC_12_D_PRIOR_BROWSER_EVIDENCE_BINDING.json').read_text(encoding='utf-8'))
    assert binding['status'] == 'PASS/HASH-BOUND-REUSE'
    assert binding['ux_surface_changed'] is False
    assert binding['prior_browser']['real_browser_runs'] == 1
    assert len(binding['prior_browser']['screenshots']) == 5
    assert binding['full_regression_runs'] == 0


def test_12_d_reports_and_policy_documents_are_present() -> None:
    for rel in (
        'docs/audits/DEVPL_GSDLC_12_D_INDUSTRIAL_HARDENING_REPORT.md',
        'docs/audits/DEVPL_GSDLC_12_D_PERFORMANCE_BUDGET.json',
        'docs/audits/DEVPL_GSDLC_12_D_PERFORMANCE_RESULTS.json',
        'docs/audits/DEVPL_GSDLC_12_D_RED_TEAM_REPORT.json',
        'docs/audits/DEVPL_GSDLC_12_D_RESOURCE_COST_REPORT.json',
        'docs/audits/DEVPL_GSDLC_12_D_S0_S1_LEDGER.json',
        'docs/audits/DEVPL_GSDLC_12_D_PRIOR_BROWSER_EVIDENCE_BINDING.json',
    ):
        assert (ROOT / rel).is_file(), rel


def test_consumer_session_piggyback_and_cross_actor_cancel_are_blocked(tmp_path: Path) -> None:
    from devpilot_core.agents.execution_policy import AgentExecutionPolicy, ToolIntent

    policy = AgentExecutionPolicy(ROOT)
    policy.store_path = tmp_path / "agent-runtime.json"
    created = policy.create_session(role_id="requirements", step_id="requirements", actor_id="owner-a", mode="fake-local")
    assert created.ok is True
    session_id = created.data["summary"]["session_id"]

    piggyback = policy.evaluate_intent(
        ToolIntent(
            session_id=session_id,
            agent_role_id="requirements",
            step_id="requirements",
            tool_id="policy.check",
            action="check",
            subject="same-session-other-consumer",
            dry_run=True,
        ),
        actor_id="owner-b",
    )
    assert piggyback.ok is False
    assert any(f.id == "AGENT_EXECUTION_SESSION_ACTOR_MISMATCH" for f in piggyback.findings)

    cancel = policy.cancel(session_id, actor_id="owner-b", reason="cross actor cancellation")
    assert cancel.ok is False
    assert any(f.id == "AGENT_EXECUTION_SESSION_ACTOR_MISMATCH" for f in cancel.findings)

    owner = policy.evaluate_intent(
        ToolIntent(
            session_id=session_id,
            agent_role_id="requirements",
            step_id="requirements",
            tool_id="policy.check",
            action="check",
            subject="same-session-owner",
            dry_run=True,
        ),
        actor_id="owner-a",
    )
    assert owner.ok is True
