from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from devpilot_core.generation.contracts import GenerationRequest, ProviderClass, canonical_sha256
from devpilot_core.modeling.budget import BudgetScopeUsage, TokenBudgetPolicy
from devpilot_core.modeling.catalog import ModelCapabilityCatalog, SUPPORTED_CAPABILITY_STATES
from devpilot_core.modeling.contracts import ModelRoutingRequest, RouteLocality
from devpilot_core.modeling.model_router_v2 import ModelRouterV2, RoutingRuntimeState
from devpilot_core.modeling.providers import ProviderRegistry
from devpilot_core.observability.tracing import SpanRecord, SpanStatus, TraceContext
from devpilot_core.policy.cost_guard import CostGuard, CostPolicy, load_cost_policy
from devpilot_core.policy.decisions import PolicyDecision
from devpilot_core.policy.secrets import redact_sensitive_data
from devpilot_core.prompts.registry import PromptRegistry

PROVIDER_RUNTIME_SCHEMA_ID = "devpilot.mp-v2.provider-runtime.v1"
PROVIDER_PROVENANCE_SCHEMA_ID = "devpilot.mp-v2.generation-provenance-envelope.v1"
PROVIDER_RECEIPT_SCHEMA_ID = "devpilot.mp-v2.provider-execution-receipt.v1"
PROVIDER_TRACE_SCHEMA_ID = "devpilot.mp-v2.provider-runtime-trace.v1"

_FORBIDDEN_AUTHORITY_KEYS = frozenset(
    {
        "source_write",
        "source_apply",
        "apply_authority",
        "freeze_authority",
        "approval_authority",
        "quality_authority",
        "git_authority",
        "tool_execution_authority",
        "shell_authority",
    }
)


class ProviderAvailability(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"
    DISABLED = "disabled"


def _provider_class(value: str | ProviderClass) -> ProviderClass:
    if isinstance(value, ProviderClass):
        return value
    normalized = str(value or "").strip().lower()
    aliases = {
        "deterministic": ProviderClass.DETERMINISTIC,
        "local": ProviderClass.LOCAL_MODEL,
        "local-model": ProviderClass.LOCAL_MODEL,
        "external": ProviderClass.EXTERNAL_MODEL,
        "external-model": ProviderClass.EXTERNAL_MODEL,
    }
    if normalized not in aliases:
        raise ValueError(f"unsupported provider route class: {value!r}")
    return aliases[normalized]


def _safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return dict(redact_sensitive_data(dict(value or {})))


@dataclass(frozen=True)
class ProviderHealthSnapshot:
    """No-network provider/model health evidence used by MP-0D routing.

    A snapshot is data, not a probe. Tests and callers may construct it from
    fixtures or static configuration. ``network_used`` and
    ``external_api_used`` must remain false in MP-0.
    """

    access_route_id: str
    provider_id: str
    provider_class: ProviderClass
    model_id: str | None
    availability: ProviderAvailability = ProviderAvailability.UNKNOWN
    configured: bool = False
    enabled: bool = False
    structured_output_supported: bool = False
    locality: str = "none"
    checked_at: str | None = None
    source: str = "static/no-probe"
    provider_version: str | None = None
    model_identity: str | None = None
    benchmark_score: float | None = None
    approval_required: bool = False
    approval_present: bool = False
    network_used: bool = False
    external_api_used: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.access_route_id.strip():
            raise ValueError("access_route_id is required")
        if not self.provider_id.strip():
            raise ValueError("provider_id is required")
        if self.network_used or self.external_api_used:
            raise ValueError("MP-0 health snapshots cannot represent live provider/network execution")

    @property
    def healthy(self) -> bool:
        return self.availability is ProviderAvailability.AVAILABLE

    @property
    def snapshot_sha256(self) -> str:
        return canonical_sha256(self.to_dict())

    def routing_state(self) -> RoutingRuntimeState:
        return RoutingRuntimeState(
            provider_enabled=bool(self.configured and self.enabled),
            region_terms_auth_data_allowed=True,
            healthy=self.healthy,
            benchmark_score=self.benchmark_score,
            approval_required=self.approval_required,
            approval_present=self.approval_present,
            reason=f"mp0d-health:{self.source}",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_route_id": self.access_route_id,
            "provider_id": self.provider_id,
            "provider_class": self.provider_class.value,
            "model_id": self.model_id,
            "availability": self.availability.value,
            "configured": self.configured,
            "enabled": self.enabled,
            "structured_output_supported": self.structured_output_supported,
            "locality": self.locality,
            "checked_at": self.checked_at,
            "source": self.source,
            "provider_version": self.provider_version,
            "model_identity": self.model_identity,
            "benchmark_score": self.benchmark_score,
            "approval_required": self.approval_required,
            "approval_present": self.approval_present,
            "network_used": False,
            "external_api_used": False,
            "metadata": _safe_mapping(self.metadata),
        }


@dataclass(frozen=True)
class ProviderSelectionPolicy:
    policy_id: str = "mp-v2-provider-selection-default"
    allowed_provider_classes: tuple[ProviderClass, ...] = (ProviderClass.DETERMINISTIC,)
    allow_local_to_deterministic_fallback: bool = True
    allow_external_fallback: bool = False
    external_enabled: bool = False
    execution_enabled_classes: tuple[ProviderClass, ...] = (ProviderClass.DETERMINISTIC,)
    provider_profile_support: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    provider_artifact_support: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    max_estimated_cost_usd: float | None = None
    network_policy: str = "DENY"

    def __post_init__(self) -> None:
        if not self.policy_id.strip():
            raise ValueError("policy_id is required")
        if self.allow_external_fallback:
            raise ValueError("external fallback is not permitted by MP-0D baseline")
        if self.network_policy.upper() != "DENY":
            raise ValueError("MP-0D provider execution network policy must remain DENY")

    def class_allowed(self, provider_class: ProviderClass) -> bool:
        return provider_class in self.allowed_provider_classes

    def profile_allowed(self, provider_id: str, profile_version: str) -> bool:
        declared = tuple(self.provider_profile_support.get(provider_id, ()))
        return not declared or "*" in declared or profile_version in declared

    def artifact_allowed(self, provider_id: str, artifact_type: str) -> bool:
        declared = tuple(self.provider_artifact_support.get(provider_id, ()))
        return not declared or "*" in declared or artifact_type in declared


@dataclass(frozen=True)
class FallbackDecision:
    applied: bool
    requested_provider_class: ProviderClass
    used_provider_class: ProviderClass | None
    reason: str
    policy_id: str
    explicit: bool = True
    owner_visible: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "applied": self.applied,
            "requested_provider_class": self.requested_provider_class.value,
            "used_provider_class": self.used_provider_class.value if self.used_provider_class else None,
            "reason": self.reason,
            "policy_id": self.policy_id,
            "explicit": self.explicit,
            "owner_visible": self.owner_visible,
        }


@dataclass(frozen=True)
class GenerationRoute:
    request_id: str
    artifact_type: str
    profile_version: str
    requested_provider_class: ProviderClass
    used_provider_class: ProviderClass | None
    status: str
    provider_id: str | None
    model_id: str | None
    access_route_id: str | None
    execution_allowed: bool
    fallback: FallbackDecision
    health_snapshot_sha256: str | None
    cost_decision: Mapping[str, Any]
    network_policy: str
    network_used: bool = False
    external_api_used: bool = False
    reasons: tuple[str, ...] = ()
    model_gateway_decision: Mapping[str, Any] = field(default_factory=dict)

    @property
    def route_sha256(self) -> str:
        return canonical_sha256(self.to_dict(include_hash=False))

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload = {
            "schema_id": PROVIDER_RUNTIME_SCHEMA_ID,
            "request_id": self.request_id,
            "artifact_type": self.artifact_type,
            "profile_version": self.profile_version,
            "requested_provider_class": self.requested_provider_class.value,
            "used_provider_class": self.used_provider_class.value if self.used_provider_class else None,
            "status": self.status,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "access_route_id": self.access_route_id,
            "execution_allowed": self.execution_allowed,
            "fallback": self.fallback.to_dict(),
            "health_snapshot_sha256": self.health_snapshot_sha256,
            "cost_decision": _safe_mapping(self.cost_decision),
            "network_policy": self.network_policy,
            "network_used": self.network_used,
            "external_api_used": self.external_api_used,
            "reasons": list(self.reasons),
            "model_gateway_decision": _safe_mapping(self.model_gateway_decision),
            "authority_boundary": {
                "source_write": False,
                "source_apply": False,
                "approval": False,
                "freeze": False,
                "quality": False,
                "git": False,
                "tool_execution": False,
                "arbitrary_shell": False,
            },
        }
        if include_hash:
            payload["route_sha256"] = canonical_sha256(payload)
        return payload


@dataclass(frozen=True)
class GenerationProvenanceEnvelope:
    request_id: str
    artifact_type: str
    profile_version: str
    dependency_profile_version: str
    canonical_input_sha256: str
    provider_class: ProviderClass
    provider_id: str
    model_id: str | None
    route_sha256: str
    context_sha256: str | None = None
    prompt_ref: Mapping[str, Any] = field(default_factory=dict)
    prompt_sha256: str | None = None
    input_hashes: Mapping[str, str] = field(default_factory=dict)
    fallback: Mapping[str, Any] = field(default_factory=dict)
    validation_refs: tuple[str, ...] = ()
    agent_review_ids: tuple[str, ...] = ()
    human_edit_ids: tuple[str, ...] = ()
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: int | None = None
    cost_usd: float = 0.0
    network_used: bool = False
    external_api_used: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def provenance_sha256(self) -> str:
        return canonical_sha256(self.to_dict(include_hash=False))

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload = {
            "schema_id": PROVIDER_PROVENANCE_SCHEMA_ID,
            "request_id": self.request_id,
            "artifact_type": self.artifact_type,
            "profile_version": self.profile_version,
            "dependency_profile_version": self.dependency_profile_version,
            "canonical_input_sha256": self.canonical_input_sha256,
            "provider_class": self.provider_class.value,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "route_sha256": self.route_sha256,
            "context_sha256": self.context_sha256,
            "prompt_ref": _safe_mapping(self.prompt_ref),
            "prompt_sha256": self.prompt_sha256,
            "input_hashes": dict(self.input_hashes),
            "fallback": _safe_mapping(self.fallback),
            "validation_refs": list(self.validation_refs),
            "agent_review_ids": list(self.agent_review_ids),
            "human_edit_ids": list(self.human_edit_ids),
            "tokens": {"input": self.tokens_input, "output": self.tokens_output},
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "network_used": self.network_used,
            "external_api_used": self.external_api_used,
            "metadata": _safe_mapping(self.metadata),
            "raw_secret_present": False,
        }
        if include_hash:
            payload["provenance_sha256"] = canonical_sha256(payload)
        return payload


@dataclass(frozen=True)
class ProviderExecutionReceipt:
    request_id: str
    route_sha256: str
    provenance_sha256: str
    provider_class: ProviderClass
    provider_id: str
    model_id: str | None
    outcome: str
    execution_attempted: bool
    model_call_performed: bool
    fallback: Mapping[str, Any] = field(default_factory=dict)
    denial_reason: str | None = None
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: int | None = None
    cost_usd: float = 0.0
    network_used: bool = False
    external_api_used: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def receipt_sha256(self) -> str:
        return canonical_sha256(self.to_dict(include_hash=False))

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload = {
            "schema_id": PROVIDER_RECEIPT_SCHEMA_ID,
            "request_id": self.request_id,
            "route_sha256": self.route_sha256,
            "provenance_sha256": self.provenance_sha256,
            "provider_class": self.provider_class.value,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "outcome": self.outcome,
            "execution_attempted": self.execution_attempted,
            "model_call_performed": self.model_call_performed,
            "fallback": _safe_mapping(self.fallback),
            "denial_reason": self.denial_reason,
            "tokens": {"input": self.tokens_input, "output": self.tokens_output},
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "network_used": self.network_used,
            "external_api_used": self.external_api_used,
            "metadata": _safe_mapping(self.metadata),
            "raw_secret_present": False,
            "authority_boundary": {
                "source_write": False,
                "source_apply": False,
                "approval": False,
                "freeze": False,
                "quality": False,
                "git": False,
                "tool_execution": False,
                "arbitrary_shell": False,
            },
        }
        if include_hash:
            payload["receipt_sha256"] = canonical_sha256(payload)
        return payload


class GenerationProviderRegistryView:
    """Read-only Multiprovider projection over existing provider/model authorities."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.provider_registry = ProviderRegistry.load(self.root)
        self.catalog = ModelCapabilityCatalog(self.root)
        self._models = {str(row["model_id"]): row for row in self.catalog.payload["models"]}

    @property
    def config_is_operator_local(self) -> bool:
        return not self.provider_registry.used_example and self.provider_registry.source_path != "built-in-defaults"

    def validate_snapshot_support(
        self,
        snapshot: ProviderHealthSnapshot,
        request: GenerationRequest,
        policy: ProviderSelectionPolicy,
        required_capabilities: Iterable[str],
    ) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        if not policy.profile_allowed(snapshot.provider_id, request.profile_version):
            reasons.append("provider-profile-unsupported")
        if not policy.artifact_allowed(snapshot.provider_id, request.artifact_type):
            reasons.append("provider-artifact-unsupported")
        route = self.catalog.access_route(snapshot.access_route_id)
        if route is None:
            reasons.append("access-route-unregistered")
            return False, tuple(reasons)
        if route.provider_id != snapshot.provider_id or route.model_id != snapshot.model_id:
            reasons.append("health-route-identity-mismatch")
        if snapshot.provider_class is ProviderClass.LOCAL_MODEL and route.locality is not RouteLocality.LOOPBACK:
            reasons.append("local-provider-route-not-loopback")
        if snapshot.provider_class is ProviderClass.EXTERNAL_MODEL and not route.external_api:
            reasons.append("external-provider-route-not-external")
        model = self._models.get(str(snapshot.model_id or ""), {})
        caps = model.get("capabilities", {}) if isinstance(model, dict) else {}
        for capability in required_capabilities:
            if str(caps.get(capability, "unknown")) not in SUPPORTED_CAPABILITY_STATES:
                reasons.append(f"required-capability-unsupported:{capability}")
        if "structured_output" in set(required_capabilities) and not snapshot.structured_output_supported:
            reasons.append("structured-output-health-unsupported")
        if snapshot.provider_class is not ProviderClass.DETERMINISTIC:
            config = self.provider_registry.get(snapshot.provider_id)
            if config is None:
                reasons.append("provider-config-unregistered")
        return not reasons, tuple(reasons)

    def static_health_snapshots(self) -> tuple[ProviderHealthSnapshot, ...]:
        """Project config/catalog state without probing any provider."""

        rows: list[ProviderHealthSnapshot] = []
        config_local = self.config_is_operator_local
        for route_row in self.catalog.payload["access_routes"]:
            route = self.catalog.access_route(str(route_row["access_route_id"]))
            assert route is not None
            if route.locality is RouteLocality.MOCK:
                rows.append(
                    ProviderHealthSnapshot(
                        access_route_id=route.access_route_id,
                        provider_id=route.provider_id,
                        provider_class=ProviderClass.DETERMINISTIC,
                        model_id=route.model_id,
                        availability=ProviderAvailability.AVAILABLE,
                        configured=True,
                        enabled=True,
                        structured_output_supported=True,
                        locality=route.locality.value,
                        source="model-capability-catalog/static",
                        benchmark_score=0.0,
                    )
                )
                continue
            provider_class = ProviderClass.EXTERNAL_MODEL if route.external_api else ProviderClass.LOCAL_MODEL
            cfg = self.provider_registry.get(route.provider_id)
            configured = bool(cfg and config_local)
            enabled = bool(cfg and cfg.enabled and configured)
            model = self._models.get(route.model_id, {})
            caps = model.get("capabilities", {}) if isinstance(model, dict) else {}
            rows.append(
                ProviderHealthSnapshot(
                    access_route_id=route.access_route_id,
                    provider_id=route.provider_id,
                    provider_class=provider_class,
                    model_id=route.model_id,
                    availability=ProviderAvailability.DISABLED if not enabled else ProviderAvailability.UNKNOWN,
                    configured=configured,
                    enabled=enabled,
                    structured_output_supported=str(caps.get("structured_output", "unknown")) in SUPPORTED_CAPABILITY_STATES,
                    locality=route.locality.value,
                    source="provider-registry+model-capability-catalog/static/no-probe",
                    benchmark_score=None,
                    approval_required=bool(route.opt_in_required),
                    approval_present=False,
                )
            )
        return tuple(rows)


class GenerationRouteResolver:
    """Candidate-generation route resolver over existing Model Gateway policy.

    The resolver selects *eligibility only*. It never calls a ModelAdapter.
    Deterministic/local/external provider execution remains a separate boundary.
    """

    def __init__(self, root: Path, *, cost_guard: CostGuard | None = None) -> None:
        self.root = Path(root).resolve()
        self.registry = GenerationProviderRegistryView(self.root)
        self.model_router = ModelRouterV2(self.registry.catalog)
        self.budget_policy = TokenBudgetPolicy.load(self.root)
        self.cost_guard = cost_guard or CostGuard(load_cost_policy(self.root))

    def resolve(
        self,
        request: GenerationRequest,
        *,
        policy: ProviderSelectionPolicy,
        health_snapshots: Iterable[ProviderHealthSnapshot] = (),
        required_capabilities: tuple[str, ...] = ("text_generation", "structured_output"),
        estimated_input_tokens: int = 0,
        estimated_output_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
    ) -> GenerationRoute:
        requested = _provider_class(request.preferred_route)
        allowed_request = tuple(_provider_class(item) for item in request.allowed_routes)
        if requested not in allowed_request:
            return self._blocked(request, requested, policy, "requested-route-not-allowed-by-request")
        if not policy.class_allowed(requested):
            return self._blocked(request, requested, policy, "requested-route-not-allowed-by-policy")
        if requested is ProviderClass.DETERMINISTIC:
            return self._deterministic(request, requested, policy, reason="requested-deterministic")

        snapshots = [row for row in health_snapshots if row.provider_class is requested]
        if requested is ProviderClass.EXTERNAL_MODEL and not policy.external_enabled:
            return self._blocked(
                request,
                requested,
                policy,
                "external-disabled",
                fallback_reason="external-never-implicit-fallback",
            )
        if not snapshots:
            return self._fallback_or_block(request, requested, policy, "provider-health-snapshot-missing", allowed_request)

        support_reasons: list[str] = []
        supported: list[ProviderHealthSnapshot] = []
        for snapshot in snapshots:
            ok, reasons = self.registry.validate_snapshot_support(snapshot, request, policy, required_capabilities)
            if ok:
                supported.append(snapshot)
            else:
                support_reasons.extend(reasons)
        if not supported:
            reason = support_reasons[0] if support_reasons else "provider-support-unavailable"
            return self._fallback_or_block(request, requested, policy, reason, allowed_request)

        runtime = {
            "mock": RoutingRuntimeState(provider_enabled=True, healthy=True, benchmark_score=0.0, reason="deterministic-fallback")
        }
        for snapshot in supported:
            runtime[snapshot.access_route_id] = snapshot.routing_state()

        preferred_locality = "loopback" if requested is ProviderClass.LOCAL_MODEL else "remote"
        max_cost = policy.max_estimated_cost_usd
        model_request = ModelRoutingRequest(
            workload_id=request.request_id,
            required_capabilities=tuple(required_capabilities),
            privacy_class=str(request.policy_snapshot.get("privacy_class") or "internal"),
            data_classes=tuple(str(x) for x in request.policy_snapshot.get("data_classes") or ()),
            max_cost_usd=max_cost,
            offline_required=bool(request.policy_snapshot.get("offline_required", False)),
            preferred_locality=preferred_locality,
        )
        decision = self.model_router.route(
            model_request,
            runtime=runtime,
            budget_policy=self.budget_policy,
            budget_usage={scope: BudgetScopeUsage() for scope in self.budget_policy.scopes},
            estimated_input_tokens=max(0, int(estimated_input_tokens)),
            estimated_output_tokens=max(0, int(estimated_output_tokens)),
        )
        decision_payload = decision.to_dict()
        if decision.route_status != "selected":
            return self._fallback_or_block(
                request,
                requested,
                policy,
                decision.blocked_reason or "model-gateway-blocked",
                allowed_request,
                model_gateway_decision=decision_payload,
            )
        if decision.access_route_id == "mock":
            return self._fallback_or_block(
                request,
                requested,
                policy,
                decision.fallback_reason or "model-gateway-selected-deterministic-fallback",
                allowed_request,
                model_gateway_decision=decision_payload,
            )

        snapshot = next((row for row in supported if row.access_route_id == decision.access_route_id), None)
        if snapshot is None:
            return self._blocked(request, requested, policy, "selected-route-health-snapshot-missing", model_gateway_decision=decision_payload)

        cost_provider = snapshot.provider_id
        cost = self.cost_guard.evaluate(
            external_api=(requested is ProviderClass.EXTERNAL_MODEL),
            provider=cost_provider,
            estimated_cost_usd=max(0.0, float(estimated_cost_usd)),
        )
        if not cost.ok:
            return self._fallback_or_block(
                request,
                requested,
                policy,
                f"costguard:{cost.rule_id}",
                allowed_request,
                health_snapshot=snapshot,
                cost_decision=cost,
                model_gateway_decision=decision_payload,
            )

        execution_allowed = requested in policy.execution_enabled_classes
        reasons = ("eligible-no-model-call",) if execution_allowed else ("eligible-but-provider-execution-disabled-in-mp0",)
        return GenerationRoute(
            request_id=request.request_id,
            artifact_type=request.artifact_type,
            profile_version=request.profile_version,
            requested_provider_class=requested,
            used_provider_class=requested,
            status="selected",
            provider_id=snapshot.provider_id,
            model_id=snapshot.model_id,
            access_route_id=snapshot.access_route_id,
            execution_allowed=execution_allowed,
            fallback=FallbackDecision(False, requested, requested, "not-applied", policy.policy_id),
            health_snapshot_sha256=snapshot.snapshot_sha256,
            cost_decision=cost.to_dict(),
            network_policy=policy.network_policy,
            network_used=False,
            external_api_used=False,
            reasons=reasons,
            model_gateway_decision=decision_payload,
        )

    def _deterministic(
        self,
        request: GenerationRequest,
        requested: ProviderClass,
        policy: ProviderSelectionPolicy,
        *,
        reason: str,
        fallback_from: ProviderClass | None = None,
        fallback_reason: str | None = None,
        model_gateway_decision: Mapping[str, Any] | None = None,
    ) -> GenerationRoute:
        cost = self.cost_guard.evaluate(external_api=False, provider="mock", estimated_cost_usd=0.0)
        if not cost.ok:
            return self._blocked(request, requested, policy, f"costguard:{cost.rule_id}", model_gateway_decision=model_gateway_decision)
        applied = fallback_from is not None
        fallback = FallbackDecision(
            applied,
            fallback_from or requested,
            ProviderClass.DETERMINISTIC,
            fallback_reason or ("not-applied" if not applied else reason),
            policy.policy_id,
        )
        return GenerationRoute(
            request_id=request.request_id,
            artifact_type=request.artifact_type,
            profile_version=request.profile_version,
            requested_provider_class=fallback_from or requested,
            used_provider_class=ProviderClass.DETERMINISTIC,
            status="selected",
            provider_id="deterministic",
            model_id=None,
            access_route_id=None,
            execution_allowed=ProviderClass.DETERMINISTIC in policy.execution_enabled_classes,
            fallback=fallback,
            health_snapshot_sha256=None,
            cost_decision=cost.to_dict(),
            network_policy=policy.network_policy,
            reasons=(reason,),
            model_gateway_decision=dict(model_gateway_decision or {}),
        )

    def _fallback_or_block(
        self,
        request: GenerationRequest,
        requested: ProviderClass,
        policy: ProviderSelectionPolicy,
        reason: str,
        allowed_request: tuple[ProviderClass, ...],
        *,
        health_snapshot: ProviderHealthSnapshot | None = None,
        cost_decision: PolicyDecision | None = None,
        model_gateway_decision: Mapping[str, Any] | None = None,
    ) -> GenerationRoute:
        if (
            requested is ProviderClass.LOCAL_MODEL
            and policy.allow_local_to_deterministic_fallback
            and ProviderClass.DETERMINISTIC in allowed_request
            and policy.class_allowed(ProviderClass.DETERMINISTIC)
        ):
            return self._deterministic(
                request,
                ProviderClass.DETERMINISTIC,
                policy,
                reason="policy-authorized-local-to-deterministic-fallback",
                fallback_from=requested,
                fallback_reason=reason,
                model_gateway_decision=model_gateway_decision,
            )
        fallback_reason = "external-never-implicit-fallback" if requested is ProviderClass.EXTERNAL_MODEL else "fallback-not-authorized"
        return self._blocked(
            request,
            requested,
            policy,
            reason,
            fallback_reason=fallback_reason,
            health_snapshot=health_snapshot,
            cost_decision=cost_decision,
            model_gateway_decision=model_gateway_decision,
        )

    def _blocked(
        self,
        request: GenerationRequest,
        requested: ProviderClass,
        policy: ProviderSelectionPolicy,
        reason: str,
        *,
        fallback_reason: str = "not-applied",
        health_snapshot: ProviderHealthSnapshot | None = None,
        cost_decision: PolicyDecision | None = None,
        model_gateway_decision: Mapping[str, Any] | None = None,
    ) -> GenerationRoute:
        return GenerationRoute(
            request_id=request.request_id,
            artifact_type=request.artifact_type,
            profile_version=request.profile_version,
            requested_provider_class=requested,
            used_provider_class=None,
            status="blocked",
            provider_id=health_snapshot.provider_id if health_snapshot else None,
            model_id=health_snapshot.model_id if health_snapshot else None,
            access_route_id=health_snapshot.access_route_id if health_snapshot else None,
            execution_allowed=False,
            fallback=FallbackDecision(False, requested, None, fallback_reason, policy.policy_id),
            health_snapshot_sha256=health_snapshot.snapshot_sha256 if health_snapshot else None,
            cost_decision=cost_decision.to_dict() if cost_decision else {},
            network_policy=policy.network_policy,
            reasons=(reason,),
            model_gateway_decision=dict(model_gateway_decision or {}),
        )


def prompt_reference_snapshot(root: Path, prompt_id: str, *, version: str | None = None) -> dict[str, Any]:
    """Return a redacted PromptRegistry reference with template hash only."""

    record = PromptRegistry(Path(root)).get(prompt_id, version=version)
    if record is None:
        raise KeyError(f"prompt not found: {prompt_id}@{version or 'latest'}")
    payload = record.to_dict(include_template=False, root=Path(root).resolve())
    return {
        "prompt_id": payload["id"],
        "version": payload["version"],
        "template_sha256": payload["template_sha256"],
        "path": payload["path"],
        "template_redacted": True,
        "raw_prompt_stored": False,
    }


def build_provenance(
    request: GenerationRequest,
    route: GenerationRoute,
    *,
    prompt_ref: Mapping[str, Any] | None = None,
    context_sha256: str | None = None,
    validation_refs: Iterable[str] = (),
    metadata: Mapping[str, Any] | None = None,
) -> GenerationProvenanceEnvelope:
    if route.used_provider_class is None or route.provider_id is None:
        raise ValueError("provenance requires a selected route")
    prompt = dict(prompt_ref or {})
    return GenerationProvenanceEnvelope(
        request_id=request.request_id,
        artifact_type=request.artifact_type,
        profile_version=request.profile_version,
        dependency_profile_version=request.dependency_profile_version,
        canonical_input_sha256=request.canonical_input_sha256,
        provider_class=route.used_provider_class,
        provider_id=route.provider_id,
        model_id=route.model_id,
        route_sha256=route.route_sha256,
        context_sha256=context_sha256,
        prompt_ref=prompt,
        prompt_sha256=prompt.get("template_sha256"),
        input_hashes=dict(request.upstream_hashes),
        fallback=route.fallback.to_dict(),
        validation_refs=tuple(str(x) for x in validation_refs),
        network_used=False,
        external_api_used=False,
        metadata=dict(metadata or {}),
    )


def build_execution_receipt(
    route: GenerationRoute,
    provenance: GenerationProvenanceEnvelope,
    *,
    outcome: str = "route-adjudicated/no-model-call",
    denial_reason: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ProviderExecutionReceipt:
    if route.used_provider_class is None or route.provider_id is None:
        provider_class = route.requested_provider_class
        provider_id = route.provider_id or "unselected"
    else:
        provider_class = route.used_provider_class
        provider_id = route.provider_id
    return ProviderExecutionReceipt(
        request_id=route.request_id,
        route_sha256=route.route_sha256,
        provenance_sha256=provenance.provenance_sha256,
        provider_class=provider_class,
        provider_id=provider_id,
        model_id=route.model_id,
        outcome=outcome,
        execution_attempted=False,
        model_call_performed=False,
        fallback=route.fallback.to_dict(),
        denial_reason=denial_reason,
        network_used=False,
        external_api_used=False,
        metadata=dict(metadata or {}),
    )


def provider_runtime_span(
    trace_context: TraceContext,
    provenance: GenerationProvenanceEnvelope,
    receipt: ProviderExecutionReceipt,
) -> SpanRecord:
    """Project provider runtime evidence into the existing redacted trace schema."""

    payload = {
        "schema_id": PROVIDER_TRACE_SCHEMA_ID,
        "request_id": receipt.request_id,
        "provider_class": receipt.provider_class.value,
        "provider_id": receipt.provider_id,
        "model_id": receipt.model_id,
        "route_sha256": receipt.route_sha256,
        "provenance_sha256": provenance.provenance_sha256,
        "receipt_sha256": receipt.receipt_sha256,
        "fallback": receipt.fallback,
        "network_used": receipt.network_used,
        "external_api_used": receipt.external_api_used,
        "cost_usd": receipt.cost_usd,
        "tokens": {"input": receipt.tokens_input, "output": receipt.tokens_output},
        "raw_secret_present": False,
    }
    return trace_context.child_span(
        name="Multiprovider route governance",
        span_type="generation.provider.route",
        status=SpanStatus.OK if receipt.denial_reason is None else SpanStatus.BLOCK,
        subject=receipt.provider_id,
        payload=payload,
    ).finish(status=SpanStatus.OK if receipt.denial_reason is None else SpanStatus.BLOCK)


def provider_authority_surface(payload: Mapping[str, Any]) -> tuple[str, ...]:
    """Return forbidden authority keys found in a serialized provider contract."""

    found: set[str] = set()
    stack: list[Any] = [dict(payload)]
    while stack:
        value = stack.pop()
        if isinstance(value, Mapping):
            for key, item in value.items():
                normalized = str(key).strip().lower()
                if normalized in _FORBIDDEN_AUTHORITY_KEYS and item not in (False, None, "false", "none", "outside"):
                    found.add(normalized)
                stack.append(item)
        elif isinstance(value, (list, tuple)):
            stack.extend(value)
    return tuple(sorted(found))
