from __future__ import annotations

from dataclasses import fields
import json
from pathlib import Path

import pytest
import jsonschema

from devpilot_core.modeling import ModelCapabilityCatalog, ModelRoutingRequest
from devpilot_core.modeling.budget import (
    BUDGET_SCOPES,
    BudgetScopeLimit,
    BudgetScopeUsage,
    ContextBudget,
    CostLedgerEntryV2,
    CostLedgerV2,
    EstimateState,
    TokenBudgetEnforcer,
    TokenBudgetPolicy,
    TokenCostEstimate,
    estimate_route_cost,
    estimate_text_tokens,
)
from devpilot_core.modeling.model_router_v2 import GovernedModelRouteDecision, ModelRouterV2, RoutingRuntimeState
from devpilot_core.policy import CostGuard

ROOT = Path(__file__).resolve().parents[1]


def _policy(**scope_overrides) -> TokenBudgetPolicy:
    base = {
        "request": BudgetScopeLimit(1000, 1.0),
        "artifact": BudgetScopeLimit(2000, 2.0),
        "story": BudgetScopeLimit(3000, 3.0),
        "session": BudgetScopeLimit(4000, 4.0),
        "day": BudgetScopeLimit(5000, 5.0),
        "workspace": BudgetScopeLimit(6000, 6.0),
    }
    base.update(scope_overrides)
    return TokenBudgetPolicy(base, policy_id="test-policy")


def _estimate(tokens=100, cost=0.1, state=EstimateState.ESTIMATED):
    return TokenCostEstimate(tokens, 0, state, None if state is EstimateState.UNKNOWN else cost, source="test", freshness="test")


def _router():
    return ModelRouterV2(ModelCapabilityCatalog(ROOT))


def _runtime(**overrides):
    rows = {
        "mock": RoutingRuntimeState(True, benchmark_score=0.1),
        "ollama-localhost-mistral7b": RoutingRuntimeState(True, benchmark_score=0.9),
        "ollama-localhost-qwen25-15b": RoutingRuntimeState(False, benchmark_score=0.8),
        "lmstudio-localhost": RoutingRuntimeState(False, benchmark_score=0.7),
        "local-openai-compatible-generic": RoutingRuntimeState(False, benchmark_score=0.6),
        "openai-api-direct": RoutingRuntimeState(False, benchmark_score=0.95, approval_required=True, approval_present=False),
    }
    rows.update(overrides)
    return rows


def test_token_budget_policy_loads_all_six_scopes_and_agent_cannot_expand():
    policy = TokenBudgetPolicy.load(ROOT)
    assert tuple(policy.scopes) == BUDGET_SCOPES
    assert policy.hard_stop is True
    assert policy.agent_may_expand is False


def test_unknown_cost_is_null_never_zero():
    estimate = _estimate(state=EstimateState.UNKNOWN)
    assert estimate.cost_usd is None
    assert estimate.to_dict()["cost_usd"] is None


def test_unknown_cost_with_numeric_value_is_invalid():
    with pytest.raises(ValueError):
        TokenCostEstimate(1, 1, EstimateState.UNKNOWN, 0.0)


def test_estimate_route_cost_local_zero_is_known():
    estimate = estimate_route_cost(input_tokens=1000, output_tokens=500, input_per_1k_usd=0.0, output_per_1k_usd=0.0, cost_state="local-hardware/no-api-charge", source="local", freshness="current")
    assert estimate.cost_state is EstimateState.KNOWN
    assert estimate.cost_usd == 0.0


def test_estimate_route_cost_missing_pricing_is_unknown():
    estimate = estimate_route_cost(input_tokens=100, output_tokens=20, input_per_1k_usd=None, output_per_1k_usd=None, cost_state="unknown", source="catalog", freshness="refresh-required")
    assert estimate.cost_state is EstimateState.UNKNOWN and estimate.cost_usd is None


def test_hard_budget_blocks_before_call_on_request_tokens():
    decision = TokenBudgetEnforcer(_policy(request=BudgetScopeLimit(50, 1.0))).evaluate(_estimate(tokens=51))
    assert not decision.allowed and decision.blocked_scope == "request"
    assert decision.reason == "hard-token-budget-exceeded"


def test_hard_budget_blocks_cumulative_workspace_usage():
    usage = {"workspace": BudgetScopeUsage(5900, 0.0)}
    decision = TokenBudgetEnforcer(_policy()).evaluate(_estimate(tokens=101, cost=0.0), usage=usage)
    assert not decision.allowed and decision.blocked_scope == "workspace"


def test_hard_budget_blocks_unknown_monetary_cost():
    decision = TokenBudgetEnforcer(_policy()).evaluate(_estimate(state=EstimateState.UNKNOWN))
    assert not decision.allowed
    assert decision.reason == "unknown-cost-cannot-satisfy-hard-budget"


def test_agent_requested_policy_override_is_rejected():
    widened = _policy(request=BudgetScopeLimit(9999, 99.0))
    decision = TokenBudgetEnforcer(_policy()).evaluate(_estimate(), requested_policy_override=widened)
    assert not decision.allowed and decision.agent_budget_expansion_rejected


def test_cost_guard_successor_blocks_unknown_cost_without_breaking_legacy_evaluate():
    policy = _policy()
    guard = CostGuard()
    legacy = guard.evaluate(provider="mock", estimated_cost_usd=0.0)
    assert legacy.effect.value == "allow"
    new = guard.evaluate_token_budget(estimate=_estimate(state=EstimateState.UNKNOWN), token_budget_policy=policy)
    assert new.effect.value == "block"
    assert new.rule_id == "COSTGUARD_TOKEN_BUDGET_BLOCK"


def test_cost_guard_successor_allows_within_budget():
    decision = CostGuard().evaluate_token_budget(estimate=_estimate(tokens=100, cost=0.1), token_budget_policy=_policy())
    assert decision.effect.value == "allow"


def test_context_budget_passes_when_input_fits():
    plan = ContextBudget(1000, 200, 100, 300, 400).plan(requested_input_tokens=600, invariant_min_tokens=200)
    assert plan.allowed and plan.strategy == "pass"


def test_context_budget_prefers_diff_first():
    plan = ContextBudget(1000, 200, 100, 300, 400).plan(requested_input_tokens=900, invariant_min_tokens=200, diff_first_tokens=500, summary_tokens=250)
    assert plan.strategy == "diff-first" and plan.selected_input_tokens == 500


def test_context_budget_uses_summary_when_diff_unavailable():
    plan = ContextBudget(1000, 200, 100, 300, 400).plan(requested_input_tokens=900, invariant_min_tokens=200, summary_tokens=250)
    assert plan.strategy == "summary"


def test_context_budget_uses_retrieval_after_summary():
    plan = ContextBudget(1000, 200, 100, 150, 400).plan(requested_input_tokens=900, invariant_min_tokens=200, summary_tokens=180, retrieval_tokens=300)
    assert plan.strategy == "retrieval"


def test_context_budget_hard_trims_when_invariant_still_fits():
    plan = ContextBudget(1000, 200, 100, 100, 100).plan(requested_input_tokens=900, invariant_min_tokens=500)
    assert plan.allowed and plan.strategy == "hard-trim" and plan.selected_input_tokens == 700


def test_context_budget_blocks_when_invariant_cannot_fit():
    plan = ContextBudget(1000, 200, 100, 100, 100).plan(requested_input_tokens=900, invariant_min_tokens=800)
    assert not plan.allowed and plan.strategy == "block"


def test_estimate_text_tokens_is_bounded_and_deterministic():
    assert estimate_text_tokens("abcd") == 1
    assert estimate_text_tokens("abcd" * 100) == 100


def test_cost_ledger_v2_planned_and_actual_parity(tmp_path):
    ledger = CostLedgerV2(tmp_path)
    planned = _estimate(tokens=100, cost=0.10)
    entry = CostLedgerEntryV2("run-1", "workload", "mock", "mock-deterministic-v1", "mock", planned, None, "test-policy", provenance=("unit-test",))
    payload = ledger.append(entry)
    assert payload["actual"] is None and payload["raw_secret_present"] is False
    reconciled, decision = ledger.reconcile_actual(entry, actual=planned, enforcer=TokenBudgetEnforcer(_policy()))
    assert decision.allowed and reconciled.adjustment_reason is None
    assert len(ledger.entries()) == 2


def test_cost_ledger_v2_preserves_unknown_actual_cost(tmp_path):
    ledger = CostLedgerV2(tmp_path)
    planned = _estimate(tokens=10, cost=0.0, state=EstimateState.KNOWN)
    entry = CostLedgerEntryV2("run-u", "workload", "mock", "m", "mock", planned, None, "test-policy")
    actual = _estimate(tokens=10, state=EstimateState.UNKNOWN)
    reconciled, decision = ledger.reconcile_actual(entry, actual=actual, enforcer=TokenBudgetEnforcer(_policy()))
    assert not decision.allowed
    assert reconciled.actual.cost_usd is None
    assert ledger.entries()[-1]["actual"]["cost_state"] == "unknown"


def test_cost_ledger_v2_detects_actual_overspend(tmp_path):
    ledger = CostLedgerV2(tmp_path)
    planned = _estimate(tokens=10, cost=0.1)
    entry = CostLedgerEntryV2("run-over", "workload", "mock", "m", "mock", planned, None, "test-policy")
    actual = _estimate(tokens=1200, cost=0.1)
    _, decision = ledger.reconcile_actual(entry, actual=actual, enforcer=TokenBudgetEnforcer(_policy()))
    assert not decision.allowed and decision.reason == "hard-token-budget-exceeded"


def test_cost_ledger_v2_contains_no_prompt_content_or_secret(tmp_path):
    ledger = CostLedgerV2(tmp_path)
    entry = CostLedgerEntryV2("run-safe", "workload", "mock", "m", "mock", _estimate(), None, "test-policy")
    rendered = json.dumps(ledger.append(entry), sort_keys=True).lower()
    assert "raw_secret_present\": true" not in rendered
    assert "prompt\":" not in rendered
    assert "content\":" not in rendered


def test_router_is_deterministic_and_prefers_better_healthy_local_benchmark():
    request = ModelRoutingRequest(workload_id="route-1", required_capabilities=("text_generation",), offline_required=True)
    a = _router().route(request, runtime=_runtime(), budget_policy=_policy(request=BudgetScopeLimit(1000, None)), estimated_input_tokens=100, estimated_output_tokens=50)
    b = _router().route(request, runtime=_runtime(), budget_policy=_policy(request=BudgetScopeLimit(1000, None)), estimated_input_tokens=100, estimated_output_tokens=50)
    assert a.to_dict() == b.to_dict()
    assert a.access_route_id == "ollama-localhost-mistral7b"


def test_router_privacy_offline_precedes_remote_enablement():
    runtime = _runtime(**{"openai-api-direct": RoutingRuntimeState(True, benchmark_score=1.0, approval_required=False)})
    decision = _router().route(ModelRoutingRequest(workload_id="privacy", offline_required=True), runtime=runtime, budget_policy=_policy(request=BudgetScopeLimit(1000, None)))
    row = next(x for x in decision.decision_trace if x.access_route_id == "openai-api-direct")
    assert row.rejected_at == "privacy-offline"


def test_router_provider_disabled_produces_explicit_mock_fallback():
    runtime = _runtime(**{"ollama-localhost-mistral7b": RoutingRuntimeState(False, benchmark_score=1.0)})
    decision = _router().route(ModelRoutingRequest(workload_id="fallback", required_capabilities=("coding",)), runtime=runtime, budget_policy=_policy(request=BudgetScopeLimit(1000, None)))
    assert decision.route_status == "blocked"  # mock does not satisfy coding; no unsafe silent fallback
    row = next(x for x in decision.decision_trace if x.access_route_id == "ollama-localhost-mistral7b")
    assert row.rejected_at == "provider-enablement"


def test_router_health_degradation_falls_back_explicitly_to_mock():
    runtime = _runtime(**{"ollama-localhost-mistral7b": RoutingRuntimeState(True, healthy=False, benchmark_score=1.0)})
    decision = _router().route(ModelRoutingRequest(workload_id="health", required_capabilities=("text_generation",), offline_required=True), runtime=runtime, budget_policy=_policy(request=BudgetScopeLimit(1000, None)))
    assert decision.access_route_id == "mock"
    assert decision.fallback_reason and "health" in decision.fallback_reason


def test_router_region_terms_auth_data_gate_precedes_cost_and_health():
    runtime = _runtime(**{"openai-api-direct": RoutingRuntimeState(True, region_terms_auth_data_allowed=False, healthy=False, benchmark_score=1.0, approval_required=False)})
    decision = _router().route(ModelRoutingRequest(workload_id="gates"), runtime=runtime, budget_policy=_policy(request=BudgetScopeLimit(1000, None)))
    row = next(x for x in decision.decision_trace if x.access_route_id == "openai-api-direct")
    assert row.rejected_at == "region-terms-auth-data"


def test_router_unknown_external_cost_under_ceiling_falls_back_explicitly():
    runtime = _runtime(**{"openai-api-direct": RoutingRuntimeState(True, benchmark_score=1.0, approval_required=False)})
    decision = _router().route(ModelRoutingRequest(workload_id="cost", max_cost_usd=1.0), runtime=runtime, budget_policy=_policy(request=BudgetScopeLimit(1000, None)))
    row = next(x for x in decision.decision_trace if x.access_route_id == "openai-api-direct")
    assert row.rejected_at == "cost-ceiling"
    assert "cost-unknown-under-request-ceiling" in row.reasons
    assert decision.access_route_id in {"mock", "ollama-localhost-mistral7b"}


def test_router_approval_requirement_cannot_be_skipped():
    runtime = _runtime(**{"openai-api-direct": RoutingRuntimeState(True, benchmark_score=1.0, approval_required=True, approval_present=False)})
    decision = _router().route(ModelRoutingRequest(workload_id="approval"), runtime=runtime, budget_policy=_policy(request=BudgetScopeLimit(1000, None)))
    row = next(x for x in decision.decision_trace if x.access_route_id == "openai-api-direct")
    assert row.rejected_at == "region-terms-auth-data" and "approval-required" in row.reasons


def test_router_decision_contract_cannot_escalate_tool_or_skill_authority():
    names = {field.name for field in fields(GovernedModelRouteDecision)}
    forbidden = {"tool_execution_decision", "tool_execution_allowed", "allowed_tools", "approved_tools", "skills", "permissions"}
    assert names.isdisjoint(forbidden)
    decision = _router().route(ModelRoutingRequest(workload_id="safe"), runtime=_runtime(), budget_policy=_policy(request=BudgetScopeLimit(1000, None)))
    rendered = json.dumps(decision.to_dict(), sort_keys=True).lower()
    assert "tool_execution_allowed" not in rendered and "allowed_tools" not in rendered


def test_versioned_06_d_policy_declares_binding_order_and_no_agent_expansion():
    payload = json.loads((ROOT / ".devpilot/modeling/token_budget_policy.json").read_text(encoding="utf-8"))
    assert payload["routing_order"] == list(ModelRouterV2.RULE_ORDER)
    assert payload["hard_stop"] is True
    assert payload["agent_may_expand"] is False
    assert payload["unknown_cost_policy"].startswith("block")


def test_06_d_versioned_artifacts_validate_against_registered_schemas():
    schema = json.loads((ROOT / "docs/schemas/token_budget_policy.schema.json").read_text())
    instance = json.loads((ROOT / ".devpilot/modeling/token_budget_policy.json").read_text())
    jsonschema.Draft202012Validator(schema).validate(instance)

def test_06_d_cost_ledger_samples_validate_and_unknown_remains_null():
    schema = json.loads((ROOT / "docs/schemas/cost_ledger_v2.schema.json").read_text())
    samples = json.loads((ROOT / "docs/audits/devpl_gsdlc_06_d/cost_ledger_samples.json").read_text())
    for entry in samples["entries"]:
        jsonschema.Draft202012Validator(schema).validate(entry)
    unknown = next(row for row in samples["entries"] if row["run_id"] == "sample-2")
    assert unknown["actual"]["cost_state"] == "unknown" and unknown["actual"]["cost_usd"] is None

def test_06_d_routing_decision_matrix_validates_and_has_explicit_trace():
    schema = json.loads((ROOT / "docs/schemas/model_routing_decision_v2.schema.json").read_text())
    matrix = json.loads((ROOT / "docs/audits/devpl_gsdlc_06_d/routing_decision_matrix.json").read_text())
    for decision in matrix["decisions"]:
        jsonschema.Draft202012Validator(schema).validate(decision)
        assert decision["decision_trace"]

def test_06_d_context_budget_cases_validate():
    schema = json.loads((ROOT / "docs/schemas/context_budget_plan.schema.json").read_text())
    payload = json.loads((ROOT / "docs/audits/devpl_gsdlc_06_d/context_budget_cases.json").read_text())
    for case in payload["cases"]:
        jsonschema.Draft202012Validator(schema).validate(case["plan"])
