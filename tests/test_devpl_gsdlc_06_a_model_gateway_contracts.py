from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

import jsonschema

from devpilot_core.application.model_service import ModelApplicationService
from devpilot_core.modeling import (
    ModelCapabilityCatalog,
    ModelProviderConfig,
    ModelProviderKind,
    ModelRouteDecision,
    ModelRoutingRequest,
    RouteDisposition,
)

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_06_a_catalog_schema_and_referential_semantics_pass():
    catalog = load(".devpilot/modeling/model_capability_catalog.json")
    schema = load("docs/schemas/model_capability_catalog.schema.json")
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(catalog)
    authority = ModelCapabilityCatalog(ROOT)
    assert authority.snapshot()["routing_policy"]["unknown_route"] == "deny"
    assert set(authority.capability_vocabulary) >= {"structured_output", "tool_calling_output", "vision", "coding", "embeddings"}


def test_06_a_mock_is_always_available_default_safe_and_zero_external_dependency():
    catalog = ModelCapabilityCatalog(ROOT)
    route = catalog.access_route("mock")
    assert route is not None
    assert route.disposition is RouteDisposition.ENABLED
    assert route.runtime_enabled is True
    assert route.external_api is False
    assert route.research_disposition == "default-safe"


def test_06_a_r01_local_allowed_is_not_promoted_to_runtime_enabled():
    catalog = ModelCapabilityCatalog(ROOT)
    for route_id in ["ollama-localhost-mistral7b", "ollama-localhost-qwen25-15b", "lmstudio-localhost"]:
        route = catalog.access_route(route_id)
        assert route is not None
        assert route.research_disposition == "allowed"
        assert route.research_route_id in {"ollama-localhost", "lmstudio-localhost"}
        assert route.runtime_enabled is False
        assert route.disposition is RouteDisposition.DISABLED
        assert route.opt_in_required is True


def test_06_a_external_routes_remain_disabled_conditional_unknown_or_blocked():
    payload = ModelCapabilityCatalog(ROOT).snapshot()
    external = [row for row in payload["access_routes"] if row["external_api"]]
    assert external
    assert all(row["runtime_enabled"] is False for row in external)
    assert {row["disposition"] for row in external} <= {"conditional", "unknown", "blocked", "disabled"}
    remote_compat = next(row for row in external if row["access_route_id"] == "remote-openai-compatible-generic")
    assert remote_compat["disposition"] == "unknown"
    assert payload["routing_policy"]["external_openai_compatibility_implies_authorization"] is False


def test_06_a_provider_model_route_gateway_and_auth_identities_are_separate():
    for row in ModelCapabilityCatalog(ROOT).snapshot()["access_routes"]:
        assert row["provider_id"] and row["model_id"] and row["access_route_id"] and row["gateway_adapter_id"] and row["auth_adapter_id"]
        if row["access_route_id"] == "mock":
            assert len({row["provider_id"], row["model_id"], row["access_route_id"], row["gateway_adapter_id"], row["auth_adapter_id"]}) == 5


def test_06_a_provider_agnostic_capability_matching_is_deterministic():
    catalog = ModelCapabilityCatalog(ROOT)
    request = ModelRoutingRequest(workload_id="DVP-06A-OFFLINE", required_capabilities=("text_generation",), offline_required=True, max_cost_usd=0.0)
    first = catalog.decide(request)
    second = catalog.decide(request)
    assert first == second
    assert first.route_status == "selected"
    assert first.access_route_id == "mock"
    assert first.provider_id == "devpilot-local"
    assert not hasattr(request, "provider_id") and not hasattr(request, "model_id")


def test_06_a_unknown_capability_and_unsatisfied_enabled_route_deny():
    catalog = ModelCapabilityCatalog(ROOT)
    unknown = catalog.decide(ModelRoutingRequest(workload_id="unknown", required_capabilities=("telepathy",)))
    assert unknown.route_status == "blocked" and unknown.blocked_reason.startswith("unknown-capabilities:")
    coding = catalog.decide(ModelRoutingRequest(workload_id="coding", required_capabilities=("coding",), offline_required=True))
    assert coding.route_status == "blocked"
    assert coding.blocked_reason == "no-runtime-enabled-route-satisfies-request"


def test_06_a_unknown_route_returns_explicit_deny_and_never_synthesizes_authority():
    catalog = ModelCapabilityCatalog(ROOT)
    assert catalog.access_route("not-a-route") is None
    decision = catalog.decide_access_route("not-a-route", ModelRoutingRequest(workload_id="unknown-route", required_capabilities=("text_generation",)))
    assert decision.route_status == "blocked"
    assert decision.blocked_reason == "unknown-route:not-a-route"


def test_06_a_catalog_contains_no_raw_secret_fields_or_secret_values():
    payload = ModelCapabilityCatalog(ROOT).snapshot()
    forbidden_keys = {"api_key", "api_key_value", "raw_key", "password", "access_token", "refresh_token", "secret_value", "credential_value"}
    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                assert key.lower() not in forbidden_keys
                yield from walk(item)
        elif isinstance(value, list):
            for item in value:
                yield from walk(item)
        elif isinstance(value, str):
            yield value
    strings = list(walk(payload))
    assert not any(value.startswith(("sk-", "AIza", "ghp_", "xoxb-")) for value in strings)


def test_06_a_model_route_decision_contract_cannot_grant_tool_or_skill_execution():
    names = {field.name for field in fields(ModelRouteDecision)}
    forbidden = {"tool_execution_decision", "tool_execution_allowed", "allowed_tools", "approved_tools", "skills", "approval_id", "permissions"}
    assert names.isdisjoint(forbidden)
    decision = ModelCapabilityCatalog(ROOT).decide(ModelRoutingRequest(workload_id="safe", required_capabilities=("text_generation",)))
    serialized = json.dumps(decision.to_dict(), sort_keys=True).lower()
    for token in ["tool_execution_allowed", "allowed_tools", "approved_tools", "skill_grant"]:
        assert token not in serialized


def test_06_a_legacy_provider_config_migration_never_promotes_external_runtime():
    external = ModelProviderConfig(provider_id="openai", kind=ModelProviderKind.API, enabled=True, default_model="legacy-external", external_api=True, requires_api_key=True, api_key_env="OPENAI_API_KEY")
    route = ModelCapabilityCatalog.legacy_provider_config_to_access_route(external)
    assert route.external_api is True
    assert route.runtime_enabled is False
    assert route.disposition is RouteDisposition.CONDITIONAL
    assert route.auth_adapter_id == "env-api-key-future"


def test_06_a_application_facade_loads_catalog_lazily_and_routes_without_network(tmp_path):
    service = ModelApplicationService(tmp_path)
    # Construction remains compatible with minimal historical roots: catalog is lazy.
    assert service.root == tmp_path.resolve()
    result = ModelApplicationService(ROOT).route_model(ModelRoutingRequest(workload_id="mock", required_capabilities=("text_generation",), offline_required=True))
    assert result.ok is True
    assert result.data["decision"]["access_route_id"] == "mock"
    assert result.data["summary"] == {"network_used": False, "external_api_used": False, "tool_execution_authority": False}


def test_06_a_guided_workflows_do_not_hardcode_vendor_model_names():
    roots = [ROOT / "src/devpilot_core/guided_sdlc", ROOT / "src/devpilot_core/application/pre_code_wizard_service.py"]
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore").lower() for root in roots for path in ([root] if root.is_file() else root.rglob("*.py")))
    forbidden_model_literals = ["gpt-4", "gpt-5", "claude-", "gemini-", "qwen2.5:", "mistral:7b"]
    assert all(token not in text for token in forbidden_model_literals)
