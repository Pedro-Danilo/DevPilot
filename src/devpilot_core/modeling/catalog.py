from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.modeling.contracts import (
    ModelProviderConfig,
    ModelProviderKind,
    ModelRouteDecision,
    ModelRoutingRequest,
    ProviderAccessRoute,
    RouteDisposition,
    RouteLocality,
)


SUPPORTED_CAPABILITY_STATES = {
    "supported",
    "supported-model-output-only",
    "conditional-model-dependent",
}


class ModelCapabilityCatalogError(ValueError):
    """Fail-closed catalog contract error."""


@dataclass(frozen=True)
class CapabilityMatch:
    route: ProviderAccessRoute
    matched_capabilities: tuple[str, ...]
    missing_capabilities: tuple[str, ...]
    eligible: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.route.to_dict(),
            "matched_capabilities": list(self.matched_capabilities),
            "missing_capabilities": list(self.missing_capabilities),
            "eligible": self.eligible,
            "reasons": list(self.reasons),
        }


class ModelCapabilityCatalog:
    """Static Model Gateway v2 capability/access-route authority for 06-A.

    Loading and matching are offline/read-only. The catalog never probes a
    provider. Research disposition and runtime authority are intentionally
    separate so an R01 ``allowed`` local route does not become enabled merely
    by loading this class.
    """

    DEFAULT_PATH = Path(".devpilot/modeling/model_capability_catalog.json")

    def __init__(self, root: Path, *, payload: dict[str, Any] | None = None) -> None:
        self.root = root.resolve()
        self.source_path = self.root / self.DEFAULT_PATH
        self.payload = payload if payload is not None else self._load()
        self._validate_semantics()
        self._providers = {str(row["provider_id"]): row for row in self.payload["providers"]}
        self._models = {str(row["model_id"]): row for row in self.payload["models"]}
        self._routes = {str(row["access_route_id"]): self._route(row) for row in self.payload["access_routes"]}

    def _load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.source_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ModelCapabilityCatalogError(f"model capability catalog is unreadable: {exc}") from exc
        if not isinstance(data, dict):
            raise ModelCapabilityCatalogError("model capability catalog root must be an object")
        return data

    def _validate_semantics(self) -> None:
        required = {"capability_vocabulary", "providers", "models", "access_routes", "routing_policy", "gateway_adapters", "auth_adapters"}
        missing = sorted(required - set(self.payload))
        if missing:
            raise ModelCapabilityCatalogError(f"catalog missing required sections: {missing}")
        vocabulary = tuple(str(x) for x in self.payload.get("capability_vocabulary", []))
        if len(vocabulary) != len(set(vocabulary)) or not vocabulary:
            raise ModelCapabilityCatalogError("capability vocabulary must be non-empty and unique")
        providers = {str(row.get("provider_id")) for row in self.payload.get("providers", [])}
        models = {str(row.get("model_id")): str(row.get("provider_id")) for row in self.payload.get("models", [])}
        gateways = {str(row.get("gateway_adapter_id")) for row in self.payload.get("gateway_adapters", [])}
        auth = {str(row.get("auth_adapter_id")) for row in self.payload.get("auth_adapters", [])}
        route_ids: set[str] = set()
        mock_enabled = False
        for row in self.payload.get("access_routes", []):
            route_id = str(row.get("access_route_id") or "")
            if not route_id or route_id in route_ids:
                raise ModelCapabilityCatalogError(f"duplicate/empty access_route_id: {route_id!r}")
            route_ids.add(route_id)
            provider_id = str(row.get("provider_id") or "")
            model_id = str(row.get("model_id") or "")
            if provider_id not in providers:
                raise ModelCapabilityCatalogError(f"route {route_id} references unknown provider {provider_id}")
            if model_id not in models:
                raise ModelCapabilityCatalogError(f"route {route_id} references unknown model {model_id}")
            if models[model_id] != provider_id:
                raise ModelCapabilityCatalogError(f"route {route_id} model/provider identity mismatch")
            if str(row.get("gateway_adapter_id")) not in gateways:
                raise ModelCapabilityCatalogError(f"route {route_id} references unknown gateway adapter")
            if str(row.get("auth_adapter_id")) not in auth:
                raise ModelCapabilityCatalogError(f"route {route_id} references unknown auth adapter")
            runtime_enabled = bool(row.get("runtime_enabled"))
            disposition = str(row.get("disposition"))
            external = bool(row.get("external_api"))
            if runtime_enabled and disposition != RouteDisposition.ENABLED.value:
                raise ModelCapabilityCatalogError(f"route {route_id} runtime_enabled requires disposition=enabled")
            if external and runtime_enabled:
                raise ModelCapabilityCatalogError(f"external route {route_id} cannot be runtime-enabled in GSDLC-06-A")
            if row.get("endpoint_class") == "remote-openai-compatible" and disposition == RouteDisposition.ENABLED.value:
                raise ModelCapabilityCatalogError("OpenAI-compatible protocol cannot enable an unresolved remote provider")
            if route_id == "mock" and runtime_enabled and disposition == RouteDisposition.ENABLED.value:
                mock_enabled = True
        if not mock_enabled:
            raise ModelCapabilityCatalogError("mock route must remain enabled")
        policy = self.payload.get("routing_policy", {})
        if policy.get("unknown_route") != "deny" or policy.get("unknown_capability") != "deny":
            raise ModelCapabilityCatalogError("unknown route/capability must deny")
        if policy.get("tool_execution_authority") != "outside-model-gateway":
            raise ModelCapabilityCatalogError("Model Gateway cannot own tool execution authority")

    @property
    def capability_vocabulary(self) -> tuple[str, ...]:
        return tuple(str(x) for x in self.payload["capability_vocabulary"])

    def snapshot(self) -> dict[str, Any]:
        return json.loads(json.dumps(self.payload))

    def access_route(self, access_route_id: str) -> ProviderAccessRoute | None:
        return self._routes.get(access_route_id)

    def match(self, request: ModelRoutingRequest) -> tuple[CapabilityMatch, ...]:
        unknown = tuple(sorted(set(request.required_capabilities) - set(self.capability_vocabulary)))
        if unknown:
            return ()
        matches: list[CapabilityMatch] = []
        for row in self.payload["access_routes"]:
            route = self._routes[str(row["access_route_id"])]
            model = self._models.get(route.model_id)
            capabilities = model.get("capabilities", {}) if model else {}
            matched: list[str] = []
            missing: list[str] = []
            for capability in request.required_capabilities:
                state = str(capabilities.get(capability, "unknown"))
                (matched if state in SUPPORTED_CAPABILITY_STATES else missing).append(capability)
            reasons: list[str] = []
            if missing:
                reasons.append("required-capability-unavailable")
            if request.offline_required and route.locality not in {RouteLocality.MOCK, RouteLocality.LOOPBACK}:
                reasons.append("offline-required")
            if request.target_region and route.target_regions and request.target_region not in route.target_regions:
                reasons.append("target-region-not-allowed")
            if request.allowed_regions and route.target_regions and not set(request.allowed_regions).intersection(route.target_regions):
                reasons.append("allowed-region-mismatch")
            if request.max_cost_usd is not None and request.max_cost_usd < 0:
                reasons.append("invalid-cost-ceiling")
            if not route.runtime_enabled or route.disposition is not RouteDisposition.ENABLED:
                reasons.append("route-not-runtime-enabled")
            eligible = not reasons
            matches.append(CapabilityMatch(route, tuple(matched), tuple(missing), eligible, tuple(reasons)))
        return tuple(matches)

    def decide(self, request: ModelRoutingRequest) -> ModelRouteDecision:
        if not request.workload_id.strip():
            return ModelRouteDecision(workload_id=request.workload_id, route_status="blocked", blocked_reason="workload-id-required")
        unknown = tuple(sorted(set(request.required_capabilities) - set(self.capability_vocabulary)))
        if unknown:
            return ModelRouteDecision(workload_id=request.workload_id, route_status="blocked", blocked_reason=f"unknown-capabilities:{','.join(unknown)}")
        matches = self.match(request)
        eligible = [match for match in matches if match.eligible]
        # 06-A uses stable catalog order; mock is first and is the only enabled route.
        if not eligible:
            return ModelRouteDecision(
                workload_id=request.workload_id,
                route_status="blocked",
                evidence_refs=("GSDLC-06-A:model-capability-catalog",),
                blocked_reason="no-runtime-enabled-route-satisfies-request",
            )
        selected = eligible[0]
        route = selected.route
        model = self._models.get(route.model_id, {})
        cost = model.get("cost", {}) if isinstance(model, dict) else {}
        input_cost = cost.get("input_per_1k_usd")
        output_cost = cost.get("output_per_1k_usd")
        estimated = 0.0 if input_cost == 0.0 and output_cost == 0.0 else None
        return ModelRouteDecision(
            workload_id=request.workload_id,
            route_status="selected",
            provider_id=route.provider_id,
            model_id=route.model_id,
            access_route_id=route.access_route_id,
            gateway_adapter_id=route.gateway_adapter_id,
            auth_adapter_id=route.auth_adapter_id,
            matched_capabilities=selected.matched_capabilities,
            evidence_refs=route.evidence_refs,
            estimated_cost_usd=estimated,
            fallback_access_route_id="mock" if route.access_route_id != "mock" else None,
        )

    def decide_access_route(self, access_route_id: str, request: ModelRoutingRequest) -> ModelRouteDecision:
        """Administrative exact-route decision; unknown IDs fail closed."""
        route = self.access_route(access_route_id)
        if route is None:
            return ModelRouteDecision(workload_id=request.workload_id, route_status="blocked", blocked_reason=f"unknown-route:{access_route_id}")
        match = next((row for row in self.match(request) if row.route.access_route_id == access_route_id), None)
        if match is None or not match.eligible:
            reasons = ",".join(match.reasons) if match else "route-not-matchable"
            return ModelRouteDecision(workload_id=request.workload_id, route_status="blocked", access_route_id=access_route_id, blocked_reason=reasons)
        return ModelRouteDecision(
            workload_id=request.workload_id, route_status="selected", provider_id=route.provider_id, model_id=route.model_id,
            access_route_id=route.access_route_id, gateway_adapter_id=route.gateway_adapter_id, auth_adapter_id=route.auth_adapter_id,
            matched_capabilities=match.matched_capabilities, evidence_refs=route.evidence_refs, estimated_cost_usd=0.0 if not route.external_api else None,
            fallback_access_route_id="mock" if route.access_route_id != "mock" else None,
        )

    @staticmethod
    def legacy_provider_config_to_access_route(config: ModelProviderConfig) -> ProviderAccessRoute:
        """Safe compatibility view; never promotes a historical external config."""
        if config.kind is ModelProviderKind.MOCK:
            return ProviderAccessRoute(
                provider_id="devpilot-local", model_id=config.default_model, access_route_id="mock", research_route_id="mock", gateway_adapter_id="mock-adapter",
                auth_adapter_id="no-secret-local", locality=RouteLocality.MOCK, endpoint_class="none",
                disposition=RouteDisposition.ENABLED if config.enabled else RouteDisposition.DISABLED,
                runtime_enabled=bool(config.enabled), research_disposition="legacy-safe", reason="Historical mock provider compatibility view.",
                evidence_refs=("ModelProviderConfig",), freshness="legacy-current", external_api=False,
            )
        if config.kind is ModelProviderKind.LOCAL:
            return ProviderAccessRoute(
                provider_id=config.provider_id, model_id=config.default_model, access_route_id=f"{config.provider_id}-legacy-local", research_route_id=f"{config.provider_id}-legacy-local",
                gateway_adapter_id=f"{config.provider_id}-adapter-v1", auth_adapter_id="no-secret-local", locality=RouteLocality.LOOPBACK,
                endpoint_class="localhost", disposition=RouteDisposition.ENABLED if config.enabled else RouteDisposition.DISABLED,
                runtime_enabled=bool(config.enabled), research_disposition="legacy-local", reason="Historical local provider compatibility view.",
                evidence_refs=("ModelProviderConfig",), freshness="legacy-current", external_api=False, opt_in_required=True,
            )
        return ProviderAccessRoute(
            provider_id=config.provider_id, model_id=config.default_model, access_route_id=f"{config.provider_id}-legacy-external", research_route_id=f"{config.provider_id}-legacy-external",
            gateway_adapter_id="external-provider-adapter-future", auth_adapter_id="env-api-key-future", locality=RouteLocality.REMOTE,
            endpoint_class="vendor-api", disposition=RouteDisposition.CONDITIONAL, runtime_enabled=False,
            research_disposition="legacy-external-unadjudicated", reason="Historical external config is never promoted by migration; GSDLC-06-C gates are required.",
            evidence_refs=("ModelProviderConfig",), freshness="refresh-required", external_api=True,
        )

    @staticmethod
    def _route(row: dict[str, Any]) -> ProviderAccessRoute:
        return ProviderAccessRoute(
            provider_id=str(row["provider_id"]), model_id=str(row["model_id"]), access_route_id=str(row["access_route_id"]), research_route_id=str(row["research_route_id"]),
            gateway_adapter_id=str(row["gateway_adapter_id"]), auth_adapter_id=str(row["auth_adapter_id"]),
            locality=RouteLocality(str(row["locality"])), endpoint_class=str(row["endpoint_class"]),
            disposition=RouteDisposition(str(row["disposition"])), runtime_enabled=bool(row["runtime_enabled"]),
            research_disposition=str(row["research_disposition"]), reason=str(row["reason"]),
            evidence_refs=tuple(str(x) for x in row.get("evidence_refs", [])), freshness=str(row.get("freshness") or "unknown"),
            target_regions=tuple(str(x) for x in row.get("target_regions", [])), external_api=bool(row.get("external_api")),
            opt_in_required=bool(row.get("opt_in_required")),
        )
