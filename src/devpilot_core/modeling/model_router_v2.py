from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from devpilot_core.modeling.budget import (
    BudgetScopeUsage,
    EstimateState,
    TokenBudgetEnforcer,
    TokenBudgetPolicy,
    TokenCostEstimate,
    estimate_route_cost,
)
from devpilot_core.modeling.catalog import ModelCapabilityCatalog, SUPPORTED_CAPABILITY_STATES
from devpilot_core.modeling.contracts import ModelRoutingRequest, RouteLocality


@dataclass(frozen=True)
class RoutingRuntimeState:
    provider_enabled: bool
    region_terms_auth_data_allowed: bool = True
    healthy: bool = True
    benchmark_score: float | None = None
    approval_required: bool = False
    approval_present: bool = False
    reason: str = "runtime-state"


@dataclass(frozen=True)
class RouteEvaluation:
    access_route_id: str
    eligible: bool
    rejected_at: str | None
    reasons: tuple[str, ...]
    estimate: TokenCostEstimate
    benchmark_score: float | None
    locality: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_route_id": self.access_route_id,
            "eligible": self.eligible,
            "rejected_at": self.rejected_at,
            "reasons": list(self.reasons),
            "estimate": self.estimate.to_dict(),
            "benchmark_score": self.benchmark_score,
            "locality": self.locality,
        }


@dataclass(frozen=True)
class GovernedModelRouteDecision:
    workload_id: str
    route_status: str
    provider_id: str | None = None
    model_id: str | None = None
    access_route_id: str | None = None
    gateway_adapter_id: str | None = None
    auth_adapter_id: str | None = None
    estimate: TokenCostEstimate | None = None
    fallback_from_access_route_id: str | None = None
    fallback_reason: str | None = None
    blocked_reason: str | None = None
    approval_required: bool = False
    decision_trace: tuple[RouteEvaluation, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        # Deliberately no tool/skill permission fields. Routing authority and
        # ToolExecutionDecision remain separate contracts.
        return {
            "workload_id": self.workload_id,
            "route_status": self.route_status,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "access_route_id": self.access_route_id,
            "gateway_adapter_id": self.gateway_adapter_id,
            "auth_adapter_id": self.auth_adapter_id,
            "estimate": None if self.estimate is None else self.estimate.to_dict(),
            "fallback_from_access_route_id": self.fallback_from_access_route_id,
            "fallback_reason": self.fallback_reason,
            "blocked_reason": self.blocked_reason,
            "approval_required": self.approval_required,
            "decision_trace": [item.to_dict() for item in self.decision_trace],
            "evidence_refs": list(self.evidence_refs),
        }


class ModelRouterV2:
    """Deterministic GSDLC-06-D router.

    Rule order is binding and visible in ``decision_trace``:
    capabilities -> privacy/offline -> provider enablement ->
    region/terms/auth/data -> cost ceiling -> health -> workload benchmark ->
    explicit safe fallback/BLOCK.
    """

    RULE_ORDER = (
        "capabilities",
        "privacy-offline",
        "provider-enablement",
        "region-terms-auth-data",
        "cost-ceiling",
        "health",
        "workload-benchmark",
        "safe-fallback",
    )

    def __init__(self, catalog: ModelCapabilityCatalog) -> None:
        self.catalog = catalog
        self._model_rows = {str(row["model_id"]): row for row in catalog.payload["models"]}
        self._catalog_order = {str(row["access_route_id"]): index for index, row in enumerate(catalog.payload["access_routes"])}

    def route(
        self,
        request: ModelRoutingRequest,
        *,
        runtime: Mapping[str, RoutingRuntimeState] | None,
        budget_policy: TokenBudgetPolicy,
        budget_usage: Mapping[str, BudgetScopeUsage] | None = None,
        estimated_input_tokens: int = 0,
        estimated_output_tokens: int = 0,
    ) -> GovernedModelRouteDecision:
        if not request.workload_id.strip():
            return GovernedModelRouteDecision(request.workload_id, "blocked", blocked_reason="workload-id-required")
        unknown = sorted(set(request.required_capabilities) - set(self.catalog.capability_vocabulary))
        if unknown:
            return GovernedModelRouteDecision(request.workload_id, "blocked", blocked_reason=f"unknown-capabilities:{','.join(unknown)}")
        runtime = runtime or {}
        evaluations: list[RouteEvaluation] = []
        eligible_rows: list[tuple[Any, RoutingRuntimeState, TokenCostEstimate, float]] = []
        rejected_before_selection: list[str] = []

        for route_row in self.catalog.payload["access_routes"]:
            route = self.catalog.access_route(str(route_row["access_route_id"]))
            assert route is not None
            state = runtime.get(route.access_route_id)
            if state is None:
                state = RoutingRuntimeState(provider_enabled=(route.access_route_id == "mock"), healthy=True, benchmark_score=0.0, reason="default-fail-closed")
            model = self._model_rows.get(route.model_id, {})
            cost = model.get("cost", {}) if isinstance(model, dict) else {}
            estimate = estimate_route_cost(
                input_tokens=estimated_input_tokens,
                output_tokens=estimated_output_tokens,
                input_per_1k_usd=cost.get("input_per_1k_usd"),
                output_per_1k_usd=cost.get("output_per_1k_usd"),
                cost_state=str(cost.get("state") or "unknown"),
                source=f"model-capability-catalog:{route.model_id}",
                freshness=str(model.get("freshness") or "unknown"),
            )
            reasons: list[str] = []
            rejected_at: str | None = None

            capabilities = model.get("capabilities", {}) if isinstance(model, dict) else {}
            if any(str(capabilities.get(cap, "unknown")) not in SUPPORTED_CAPABILITY_STATES for cap in request.required_capabilities):
                rejected_at = "capabilities"; reasons.append("required-capability-unavailable")
            if rejected_at is None:
                if request.offline_required and route.locality not in {RouteLocality.MOCK, RouteLocality.LOOPBACK}:
                    rejected_at = "privacy-offline"; reasons.append("offline-required")
                elif request.privacy_class.lower() in {"restricted", "secret", "local-only"} and route.locality is RouteLocality.REMOTE:
                    rejected_at = "privacy-offline"; reasons.append("privacy-class-forbids-remote")
            if rejected_at is None and not state.provider_enabled:
                rejected_at = "provider-enablement"; reasons.append("provider-disabled")
            if rejected_at is None:
                if not state.region_terms_auth_data_allowed:
                    rejected_at = "region-terms-auth-data"; reasons.append("region-terms-auth-data-gate-denied")
                elif request.target_region and route.target_regions and request.target_region not in route.target_regions:
                    rejected_at = "region-terms-auth-data"; reasons.append("target-region-not-allowed")
                elif request.allowed_regions and route.target_regions and not set(request.allowed_regions).intersection(route.target_regions):
                    rejected_at = "region-terms-auth-data"; reasons.append("allowed-region-mismatch")
                elif state.approval_required and not state.approval_present:
                    rejected_at = "region-terms-auth-data"; reasons.append("approval-required")
            if rejected_at is None:
                if request.max_cost_usd is not None:
                    if estimate.cost_state is EstimateState.UNKNOWN:
                        rejected_at = "cost-ceiling"; reasons.append("cost-unknown-under-request-ceiling")
                    elif float(estimate.cost_usd or 0.0) > request.max_cost_usd:
                        rejected_at = "cost-ceiling"; reasons.append("request-cost-ceiling-exceeded")
                if rejected_at is None:
                    budget_decision = TokenBudgetEnforcer(budget_policy).evaluate(estimate, usage=budget_usage)
                    if not budget_decision.allowed:
                        rejected_at = "cost-ceiling"; reasons.append(budget_decision.reason)
            if rejected_at is None and not state.healthy:
                rejected_at = "health"; reasons.append("provider-unhealthy")
            score = float(state.benchmark_score) if state.benchmark_score is not None else -1.0
            if rejected_at is None and state.benchmark_score is None:
                # Missing benchmark is not fatal when only one safe route exists;
                # it is recorded so the selection remains explainable.
                reasons.append("benchmark-unknown")
            eligible = rejected_at is None
            evaluation = RouteEvaluation(route.access_route_id, eligible, rejected_at, tuple(reasons), estimate, state.benchmark_score, route.locality.value)
            evaluations.append(evaluation)
            if eligible:
                locality_rank = 0
                if request.preferred_locality:
                    locality_rank = 0 if route.locality.value == request.preferred_locality else 1
                # Prefer explicit locality, then workload benchmark descending,
                # then lower known cost, then immutable catalog order.
                cost_rank = float(estimate.cost_usd) if estimate.cost_usd is not None else float("inf")
                rank = locality_rank * 1_000_000 + (-score) * 1000 + cost_rank
                eligible_rows.append((route, state, estimate, rank))
            else:
                rejected_before_selection.append(route.access_route_id)

        if not eligible_rows:
            return GovernedModelRouteDecision(
                request.workload_id,
                "blocked",
                blocked_reason="no-route-survived-governance-order",
                decision_trace=tuple(evaluations),
                evidence_refs=("GSDLC-06-D:routing-decision-matrix",),
            )
        eligible_rows.sort(key=lambda item: (item[3], self._catalog_order[item[0].access_route_id]))
        route, state, estimate, _ = eligible_rows[0]
        fallback_from = None
        fallback_reason = None
        if route.access_route_id == "mock" and rejected_before_selection:
            fallback_from = rejected_before_selection[0]
            first = next(item for item in evaluations if item.access_route_id == fallback_from)
            fallback_reason = f"explicit-safe-fallback:{first.rejected_at}:{','.join(first.reasons)}"
        return GovernedModelRouteDecision(
            workload_id=request.workload_id,
            route_status="selected",
            provider_id=route.provider_id,
            model_id=route.model_id,
            access_route_id=route.access_route_id,
            gateway_adapter_id=route.gateway_adapter_id,
            auth_adapter_id=route.auth_adapter_id,
            estimate=estimate,
            fallback_from_access_route_id=fallback_from,
            fallback_reason=fallback_reason,
            approval_required=state.approval_required,
            decision_trace=tuple(evaluations),
            evidence_refs=tuple(route.evidence_refs) + ("GSDLC-06-D:routing-decision-matrix",),
        )
