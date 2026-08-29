from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.budget import BudgetScopeUsage, TokenBudgetPolicy, estimate_route_cost
from devpilot_core.modeling.catalog import ModelCapabilityCatalog
from devpilot_core.modeling.contracts import ModelRoutingRequest, RouteLocality
from devpilot_core.modeling.external_provider_enablement import ExternalProviderEnablementService
from devpilot_core.modeling.model_router_v2 import ModelRouterV2, RoutingRuntimeState
from devpilot_core.modeling.providers import ProviderRegistry


def _freshness_state(value: str) -> str:
    text = (value or "unknown").lower()
    if "refresh" in text or "f0/f1" in text:
        return "refresh-required"
    if "current" in text:
        return "current"
    if "historical" in text:
        return "historical"
    return "unknown"


def _credential_reference(provider_id: str, registry: ProviderRegistry) -> dict[str, Any] | None:
    provider = registry.get(provider_id)
    if provider is None or not provider.requires_api_key:
        return None
    reference = provider.api_key_env or "provider-native-reference"
    return {
        "kind": "reference-only",
        "reference_name": reference,
        "masked_display": f"env:{reference} (masked)" if provider.api_key_env else "provider-native reference (masked)",
        "raw_secret_present": False,
    }


class ModelGatewaySettingsService:
    """GSDLC-06-E safe UI projection and hermetic controlled evaluation.

    This service owns *presentation/evaluation* of Model Gateway contracts. It
    does not grant tool/skill authority and never resolves raw credentials.
    Real external networking is intentionally absent from this boundary.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.catalog = ModelCapabilityCatalog(self.root)
        self.provider_registry = ProviderRegistry.load(self.root, prefer_example=True)
        self.enablement = ExternalProviderEnablementService(self.root)
        self.budget_policy = TokenBudgetPolicy.load(self.root)
        self.router = ModelRouterV2(self.catalog)
        self._models = {str(row["model_id"]): row for row in self.catalog.payload["models"]}
        self._auth = {str(row["auth_adapter_id"]): row for row in self.catalog.payload["auth_adapters"]}

    def snapshot(self, *, preview_input_tokens: int = 1200, preview_output_tokens: int = 300) -> CommandResult:
        enablement = self.enablement.status().data or {}
        runtime_external = {
            str(row.get("provider_id")): row
            for row in (enablement.get("providers") or [])
            if isinstance(row, dict)
        }
        routes: list[dict[str, Any]] = []
        for route_row in self.catalog.payload["access_routes"]:
            route = self.catalog.access_route(str(route_row["access_route_id"]))
            assert route is not None
            model = self._models.get(route.model_id, {})
            cost = model.get("cost", {}) if isinstance(model, dict) else {}
            estimate = estimate_route_cost(
                input_tokens=max(0, int(preview_input_tokens)),
                output_tokens=max(0, int(preview_output_tokens)),
                input_per_1k_usd=cost.get("input_per_1k_usd"),
                output_per_1k_usd=cost.get("output_per_1k_usd"),
                cost_state=str(cost.get("state") or "unknown"),
                source=f"model-capability-catalog:{route.model_id}",
                freshness=str(model.get("freshness") or route.freshness or "unknown"),
            )
            provider_cfg = self.provider_registry.get(route.provider_id)
            external_state = runtime_external.get(route.provider_id, {})
            configured_enabled = bool(external_state.get("configured_enabled", False)) if route.external_api else bool(provider_cfg.enabled if provider_cfg else route.runtime_enabled)
            runtime_network_enabled = bool(external_state.get("runtime_network_enabled", False)) if route.external_api else False
            runtime_credential = external_state.get("credential_reference")
            runtime_credential_reference_present = isinstance(runtime_credential, dict) and bool(runtime_credential)
            runtime_revoked = bool(external_state.get("revoked", False)) if route.external_api else False
            runtime_credential_state = "revoked" if runtime_revoked else "present" if runtime_credential_reference_present else "none"
            runtime_last_action = str(external_state.get("last_action") or "") or None
            if route.locality is RouteLocality.MOCK:
                health = "available"
            elif route.locality is RouteLocality.LOOPBACK:
                health = "opt-in-not-probed" if not configured_enabled else "configured-not-probed"
            elif route.locality is RouteLocality.REMOTE:
                health = "governed-disabled" if not runtime_network_enabled else "configured-no-live-probe"
            else:
                health = "blocked"
            auth = self._auth.get(route.auth_adapter_id, {})
            capabilities = model.get("capabilities", {}) if isinstance(model, dict) else {}
            routes.append(
                {
                    **route.to_dict(),
                    "provider_kind": None if provider_cfg is None else provider_cfg.kind.value,
                    "configured_enabled": configured_enabled,
                    "runtime_network_enabled": runtime_network_enabled,
                    "health": health,
                    "capabilities": capabilities,
                    "context_window": model.get("context_window", {}),
                    "privacy_data_class": "local-only-compatible" if route.locality in {RouteLocality.MOCK, RouteLocality.LOOPBACK} else "external-governed",
                    "target_region_display": list(route.target_regions) or (["local-host"] if route.locality in {RouteLocality.MOCK, RouteLocality.LOOPBACK} else ["provider-specific/unresolved"]),
                    "auth_adapter_type": auth.get("kind", route.auth_adapter_id),
                    "auth_adapter_status": auth.get("status", "unknown"),
                    "credential_reference": _credential_reference(route.provider_id, self.provider_registry),
                    "runtime_state_present": bool(external_state) if route.external_api else False,
                    "runtime_credential_reference_present": runtime_credential_reference_present,
                    "runtime_credential_state": runtime_credential_state,
                    "runtime_revoked": runtime_revoked,
                    "runtime_last_action": runtime_last_action,
                    "evidence_freshness": {
                        "raw": route.freshness,
                        "state": _freshness_state(route.freshness),
                        "evidence_refs": list(route.evidence_refs),
                    },
                    "estimated_tokens": estimate.total_tokens,
                    "estimated_cost": estimate.to_dict(),
                    "request_budget": self.budget_policy.scopes["request"].to_dict(),
                    "fallback_policy": "explicit-safe-fallback-to-mock-or-BLOCK",
                    "tool_execution_authority": False,
                }
            )
        summary = {
            "routes_total": len(routes),
            "mock_routes_total": sum(1 for row in routes if row["locality"] == "mock"),
            "local_routes_total": sum(1 for row in routes if row["locality"] == "loopback"),
            "external_routes_total": sum(1 for row in routes if row["external_api"]),
            "external_runtime_network_enabled_total": sum(1 for row in routes if row["runtime_network_enabled"]),
            "blocked_or_unknown_routes_total": sum(1 for row in routes if row["disposition"] in {"blocked", "unknown"}),
            "secrets_redacted": True,
            "raw_credentials_exposed": False,
            "tool_authority_granted": False,
            "network_used": False,
            "external_api_used": False,
            "controlled_eval_modes": ["mock", "fake-local", "fake-external"],
            "real_api_required_for_pass": False,
            "current_micro_sprint": "DEVPL-GSDLC-06-E",
        }
        return CommandResult(
            command="settings model-gateway",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Model Gateway settings projected with provider/model/route, cost, freshness and authority boundaries visible.",
            data={
                "summary": summary,
                "routes": routes,
                "budget_policy": self.budget_policy.to_dict(),
                "routing_policy": dict(self.catalog.payload.get("routing_policy") or {}),
                "authority_boundary": {
                    "model_route_decision_can_grant_tool_execution": False,
                    "tool_execution_decision_contract": "separate/outside-model-gateway",
                    "agent_runtime_authority": "separate",
                    "skills_tools_authority": "separate",
                },
                "notes": [
                    "Mock is the mandatory safe default.",
                    "Local routes remain opt-in and are not probed by this settings projection.",
                    "External routes remain governed and no real external network call is performed.",
                    "Credential values are never resolved or rendered by this service.",
                ],
            },
            findings=[Finding("MODEL_GATEWAY_SETTINGS_PASS", "Model Gateway Settings projection is safe, redacted and provider-agnostic.", Severity.INFO)],
        )

    def controlled_evaluation(
        self,
        *,
        mode: str,
        workload_id: str = "gsdlc-06-e-controlled-eval",
        required_capabilities: tuple[str, ...] = ("text_generation",),
        selected_access_route_id: str | None = None,
        estimated_input_tokens: int = 900,
        estimated_output_tokens: int = 200,
        max_cost_usd: float | None = None,
        hard_stop_case: bool = False,
    ) -> CommandResult:
        mode = str(mode or "mock").strip().lower()
        if mode not in {"mock", "fake-local", "fake-external"}:
            return CommandResult(
                command="settings model-gateway evaluate",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Controlled evaluation mode is unsupported.",
                data={"summary": {"network_used": False, "external_api_used": False, "tool_authority_granted": False}},
                findings=[Finding("MODEL_GATEWAY_EVAL_MODE_BLOCK", f"Unsupported mode: {mode}", Severity.BLOCK)],
            )

        runtime: dict[str, RoutingRuntimeState] = {
            "mock": RoutingRuntimeState(provider_enabled=True, healthy=True, benchmark_score=0.5, reason="mandatory-safe-default")
        }
        preferred_locality: str | None = "mock"
        requested_route = selected_access_route_id
        if mode == "fake-local":
            requested_route = requested_route or "ollama-localhost-mistral7b"
            route = self.catalog.access_route(requested_route)
            if route is None or route.locality is not RouteLocality.LOOPBACK:
                return self._route_input_block(mode, requested_route, "fake-local requires a registered loopback route")
            runtime[requested_route] = RoutingRuntimeState(provider_enabled=True, healthy=True, benchmark_score=1.0, reason="hermetic-fake-local")
            preferred_locality = "loopback"
        elif mode == "fake-external":
            requested_route = requested_route or "openai-api-direct"
            route = self.catalog.access_route(requested_route)
            if route is None or not route.external_api or route.locality is not RouteLocality.REMOTE:
                return self._route_input_block(mode, requested_route, "fake-external requires a registered remote external route")
            # Simulate the governance decision only. Real network remains impossible.
            runtime[requested_route] = RoutingRuntimeState(
                provider_enabled=True,
                region_terms_auth_data_allowed=True,
                healthy=True,
                benchmark_score=1.0,
                approval_required=True,
                approval_present=True,
                reason="hermetic-fake-external-no-network",
            )
            preferred_locality = "remote"

        if hard_stop_case:
            estimated_input_tokens = self.budget_policy.scopes["request"].max_tokens + 1
            estimated_output_tokens = 0

        request = ModelRoutingRequest(
            workload_id=workload_id,
            required_capabilities=tuple(required_capabilities),
            privacy_class="internal",
            data_classes=("source-code",),
            max_cost_usd=max_cost_usd,
            offline_required=False,
            preferred_locality=preferred_locality,
        )
        decision = self.router.route(
            request,
            runtime=runtime,
            budget_policy=self.budget_policy,
            budget_usage={scope: BudgetScopeUsage() for scope in self.budget_policy.scopes},
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
        )
        payload = decision.to_dict()
        rendered = str(payload).lower()
        tool_granted = any(token in rendered for token in ("tool_permission", "skill_permission", "tool_execution_decision"))
        requested_evaluation = next((row for row in payload.get("decision_trace", []) if row.get("access_route_id") == requested_route), None)
        fallback_demonstrated = bool(payload.get("fallback_reason"))
        hard_stop_demonstrated = bool(hard_stop_case and payload.get("route_status") == "blocked")
        decision_trace = payload.get("decision_trace") or []
        hard_stop_reason = next(
            (
                str(reason)
                for row in decision_trace
                if isinstance(row, dict)
                for reason in (row.get("reasons") or [])
                if "hard-token-budget-exceeded" in str(reason)
            ),
            None,
        )
        request_budget = self.budget_policy.scopes["request"]
        ok = not tool_granted
        if mode in {"mock", "fake-local"}:
            ok = ok and payload.get("route_status") == "selected"
        if hard_stop_case:
            ok = ok and hard_stop_demonstrated
        summary = {
            "mode": mode,
            "requested_access_route_id": requested_route,
            "selected_access_route_id": payload.get("access_route_id"),
            "route_status": payload.get("route_status"),
            "fallback_demonstrated": fallback_demonstrated,
            "hard_stop_demonstrated": hard_stop_demonstrated,
            "fallback_reason": payload.get("fallback_reason"),
            "hard_stop_reason": hard_stop_reason,
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_total_tokens": estimated_input_tokens + estimated_output_tokens,
            "request_budget_max_tokens": request_budget.max_tokens,
            "request_budget_max_cost_usd": request_budget.max_cost_usd,
            "network_used": False,
            "external_api_used": False,
            "real_api_called": False,
            "raw_credentials_exposed": False,
            "tool_authority_granted": False,
            "route_decision_tool_boundary_pass": not tool_granted,
            "evaluation_is_hermetic": True,
        }
        findings = [Finding("MODEL_GATEWAY_EVAL_CONTROLLED_PASS" if ok else "MODEL_GATEWAY_EVAL_CONTROLLED_BLOCK", "Controlled Model Gateway evaluation completed without real external network or tool authority.", Severity.INFO if ok else Severity.BLOCK)]
        return CommandResult(
            command="settings model-gateway evaluate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Controlled model evaluation completed." if ok else "Controlled model evaluation blocked by expected governance constraints.",
            data={
                "summary": summary,
                "request": request.to_dict(),
                "decision": payload,
                "requested_route_evaluation": requested_evaluation,
                "budget_policy": self.budget_policy.to_dict(),
                "credential_policy": {"raw_secret_resolution": False, "references_only": True},
            },
            findings=findings,
        )

    def _route_input_block(self, mode: str, route_id: str | None, reason: str) -> CommandResult:
        return CommandResult(
            command="settings model-gateway evaluate",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message=reason,
            data={"summary": {"mode": mode, "requested_access_route_id": route_id, "network_used": False, "external_api_used": False, "tool_authority_granted": False}},
            findings=[Finding("MODEL_GATEWAY_EVAL_ROUTE_BLOCK", reason, Severity.BLOCK)],
        )

    def build_controlled_eval_report(self) -> dict[str, Any]:
        cases = [
            ("mock", {}),
            ("fake-local", {}),
            ("fake-external", {}),
            ("mock-hard-stop", {"mode": "mock", "hard_stop_case": True}),
        ]
        rows: list[dict[str, Any]] = []
        for case_id, kwargs in cases:
            mode = kwargs.pop("mode", case_id)
            result = self.controlled_evaluation(mode=mode, **kwargs)
            rows.append({"case_id": case_id, "ok": result.ok, "result": result.to_dict() if hasattr(result, "to_dict") else {"command": result.command, "ok": result.ok, "exit_code": int(result.exit_code), "message": result.message, "data": result.data, "findings": [f.to_dict() if hasattr(f, "to_dict") else {"id": f.id, "message": f.message, "severity": f.severity.value} for f in result.findings]}})
        snapshot = self.snapshot()
        return {
            "schema_id": "devpilot.gsdlc-06-e.provider-model-eval.v1",
            "micro_sprint": "DEVPL-GSDLC-06-E",
            "status": "PASS" if all(row["ok"] or row["case_id"] == "fake-external" for row in rows) else "BLOCK",
            "network_used": False,
            "external_api_used": False,
            "real_api_required": False,
            "raw_credentials_exposed": False,
            "tool_authority_granted": False,
            "routes_total": (snapshot.data or {}).get("summary", {}).get("routes_total", 0),
            "cases": rows,
            "notes": ["fake-external may fall back or block because unknown external cost/governance remains authoritative; this is expected."],
        }
