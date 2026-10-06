from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

from devpilot_core.generation import (
    GenerationRequest,
    GenerationRouteResolver,
    ProviderAvailability,
    ProviderClass,
    ProviderHealthSnapshot,
    ProviderSelectionPolicy,
    build_execution_receipt,
    build_provenance,
    prompt_reference_snapshot,
    provider_authority_surface,
    provider_runtime_span,
)
from devpilot_core.observability.tracing import TraceContext

ROOT = Path(__file__).resolve().parents[1]


def _request(
    *,
    preferred: str = "deterministic",
    allowed: tuple[str, ...] = ("deterministic",),
    profile: str = "architecture-v1",
) -> GenerationRequest:
    return GenerationRequest(
        request_id="req-mp0d-001",
        artifact_type="architecture",
        profile_version=profile,
        dependency_profile_version="architecture-deps-v1",
        upstream_hashes={"requirements": "a" * 64},
        owner_inputs={"decision": "bounded"},
        preferred_route=preferred,
        allowed_routes=allowed,
        policy_snapshot={"privacy_class": "internal", "offline_required": True},
        budget_snapshot={"max_cost_usd": 0.0},
    )


def _local_health(
    *,
    availability: ProviderAvailability,
    configured: bool = True,
    enabled: bool = True,
    profile_supported: bool = True,
) -> ProviderHealthSnapshot:
    del profile_supported
    return ProviderHealthSnapshot(
        access_route_id="ollama-localhost-mistral7b",
        provider_id="ollama",
        provider_class=ProviderClass.LOCAL_MODEL,
        model_id="mistral:7b",
        availability=availability,
        configured=configured,
        enabled=enabled,
        structured_output_supported=True,
        locality="loopback",
        source="fixture/no-probe",
        provider_version="fixture",
        model_identity="mistral:7b",
        benchmark_score=1.0,
    )


def _external_health() -> ProviderHealthSnapshot:
    return ProviderHealthSnapshot(
        access_route_id="openai-api-direct",
        provider_id="openai",
        provider_class=ProviderClass.EXTERNAL_MODEL,
        model_id="openai-model-unresolved",
        availability=ProviderAvailability.AVAILABLE,
        configured=True,
        enabled=True,
        structured_output_supported=False,
        locality="remote",
        source="fixture/no-probe",
        benchmark_score=1.0,
        approval_required=True,
        approval_present=True,
    )


def test_deterministic_route_is_allowed_without_model_network_or_external_api():
    policy = ProviderSelectionPolicy(
        allowed_provider_classes=(ProviderClass.DETERMINISTIC,),
        execution_enabled_classes=(ProviderClass.DETERMINISTIC,),
    )
    route = GenerationRouteResolver(ROOT).resolve(_request(), policy=policy)
    assert route.status == "selected"
    assert route.used_provider_class is ProviderClass.DETERMINISTIC
    assert route.provider_id == "deterministic"
    assert route.execution_allowed is True
    payload = route.to_dict()
    assert payload["network_policy"] == "DENY"
    assert payload["network_used"] is False
    assert payload["external_api_used"] is False
    assert payload["fallback"]["applied"] is False
    assert provider_authority_surface(payload) == ()


def test_local_unavailable_falls_back_to_deterministic_only_when_policy_authorizes():
    request = _request(preferred="local-model", allowed=("local-model", "deterministic"))
    denied = ProviderSelectionPolicy(
        allowed_provider_classes=(ProviderClass.LOCAL_MODEL, ProviderClass.DETERMINISTIC),
        allow_local_to_deterministic_fallback=False,
    )
    blocked = GenerationRouteResolver(ROOT).resolve(
        request,
        policy=denied,
        health_snapshots=(_local_health(availability=ProviderAvailability.UNAVAILABLE),),
        required_capabilities=("text_generation",),
    )
    assert blocked.status == "blocked"
    assert blocked.fallback.applied is False
    assert "fallback-not-authorized" == blocked.fallback.reason

    allowed = ProviderSelectionPolicy(
        allowed_provider_classes=(ProviderClass.LOCAL_MODEL, ProviderClass.DETERMINISTIC),
        allow_local_to_deterministic_fallback=True,
    )
    route = GenerationRouteResolver(ROOT).resolve(
        request,
        policy=allowed,
        health_snapshots=(_local_health(availability=ProviderAvailability.UNAVAILABLE),),
        required_capabilities=("text_generation",),
    )
    assert route.status == "selected"
    assert route.used_provider_class is ProviderClass.DETERMINISTIC
    assert route.fallback.applied is True
    assert route.fallback.requested_provider_class is ProviderClass.LOCAL_MODEL
    assert route.fallback.used_provider_class is ProviderClass.DETERMINISTIC
    assert route.fallback.explicit is True and route.fallback.owner_visible is True
    assert "health" in route.fallback.reason or "fallback" in route.fallback.reason


def test_local_available_is_route_eligible_but_model_execution_stays_disabled_in_mp0():
    request = _request(preferred="local-model", allowed=("local-model", "deterministic"))
    policy = ProviderSelectionPolicy(
        allowed_provider_classes=(ProviderClass.LOCAL_MODEL, ProviderClass.DETERMINISTIC),
        execution_enabled_classes=(ProviderClass.DETERMINISTIC,),
        provider_profile_support={"ollama": ("architecture-v1",)},
        provider_artifact_support={"ollama": ("architecture",)},
    )
    route = GenerationRouteResolver(ROOT).resolve(
        request,
        policy=policy,
        health_snapshots=(_local_health(availability=ProviderAvailability.AVAILABLE),),
        required_capabilities=("text_generation", "structured_output"),
    )
    assert route.status == "selected"
    assert route.used_provider_class is ProviderClass.LOCAL_MODEL
    assert route.provider_id == "ollama"
    assert route.access_route_id == "ollama-localhost-mistral7b"
    assert route.execution_allowed is False
    assert route.network_used is False
    assert "eligible-but-provider-execution-disabled-in-mp0" in route.reasons


def test_external_disabled_fails_closed_and_never_implicitly_falls_back():
    request = _request(preferred="external-model", allowed=("external-model", "deterministic"))
    policy = ProviderSelectionPolicy(
        allowed_provider_classes=(ProviderClass.EXTERNAL_MODEL, ProviderClass.DETERMINISTIC),
        external_enabled=False,
    )
    route = GenerationRouteResolver(ROOT).resolve(
        request,
        policy=policy,
        health_snapshots=(_external_health(),),
        required_capabilities=(),
    )
    assert route.status == "blocked"
    assert route.used_provider_class is None
    assert route.fallback.applied is False
    assert route.fallback.reason == "external-never-implicit-fallback"
    assert "external-disabled" in route.reasons
    assert route.network_used is False and route.external_api_used is False


def test_costguard_denial_blocks_before_any_provider_execution():
    request = _request(preferred="local-model", allowed=("local-model",))
    policy = ProviderSelectionPolicy(
        allowed_provider_classes=(ProviderClass.LOCAL_MODEL,),
        allow_local_to_deterministic_fallback=False,
    )
    route = GenerationRouteResolver(ROOT).resolve(
        request,
        policy=policy,
        health_snapshots=(_local_health(availability=ProviderAvailability.AVAILABLE),),
        required_capabilities=("text_generation",),
        estimated_cost_usd=1.0,
    )
    assert route.status == "blocked"
    assert route.execution_allowed is False
    assert any(reason.startswith("costguard:COSTGUARD_") for reason in route.reasons)
    assert route.cost_decision["ok"] is False
    assert route.network_used is False and route.external_api_used is False


def test_provider_profile_and_capability_contract_rejects_unsupported_route():
    request = _request(preferred="local-model", allowed=("local-model",), profile="architecture-v2")
    policy = ProviderSelectionPolicy(
        allowed_provider_classes=(ProviderClass.LOCAL_MODEL,),
        allow_local_to_deterministic_fallback=False,
        provider_profile_support={"ollama": ("architecture-v1",)},
    )
    route = GenerationRouteResolver(ROOT).resolve(
        request,
        policy=policy,
        health_snapshots=(_local_health(availability=ProviderAvailability.AVAILABLE),),
        required_capabilities=("vision",),
    )
    assert route.status == "blocked"
    assert route.fallback.applied is False
    assert any(
        reason.startswith("provider-profile-unsupported")
        or reason.startswith("required-capability-unsupported")
        for reason in route.reasons
    )


def test_static_health_projection_uses_existing_registry_without_probe_or_example_as_operator_config():
    resolver = GenerationRouteResolver(ROOT)
    rows = resolver.registry.static_health_snapshots()
    local = next(row for row in rows if row.provider_id == "openai-compatible-local")
    external = next(row for row in rows if row.provider_id == "openai")
    assert local.configured is False
    assert local.enabled is False
    assert local.network_used is False and local.external_api_used is False
    assert external.enabled is False
    assert external.availability is ProviderAvailability.DISABLED
    assert all(row.network_used is False and row.external_api_used is False for row in rows)


def test_prompt_registry_reference_is_hash_only_and_never_exposes_raw_prompt():
    records, findings = __import__("devpilot_core.prompts.registry", fromlist=["PromptRegistry"]).PromptRegistry(ROOT).load_records()
    assert records and not [f for f in findings if getattr(f.severity, "value", "") in {"block", "error"}]
    ref = prompt_reference_snapshot(ROOT, records[0].spec.prompt_id, version=records[0].spec.version)
    assert ref["template_sha256"]
    assert ref["template_redacted"] is True
    assert ref["raw_prompt_stored"] is False
    assert "template" not in ref


def test_provenance_receipt_and_trace_are_stable_redacted_and_authority_safe():
    policy = ProviderSelectionPolicy(allowed_provider_classes=(ProviderClass.DETERMINISTIC,))
    request = _request()
    route = GenerationRouteResolver(ROOT).resolve(request, policy=policy)
    provenance = build_provenance(
        request,
        route,
        prompt_ref={"prompt_id": "p", "version": "1.0.0", "template_sha256": "b" * 64},
        context_sha256="c" * 64,
        validation_refs=("VAL-1",),
        metadata={"api_key": "sk-this-must-not-leak", "note": "safe"},
    )
    receipt = build_execution_receipt(
        route,
        provenance,
        metadata={"authorization": "Bearer secret-value", "result": "route-only"},
    )
    p1 = provenance.to_dict()
    p2 = provenance.to_dict()
    r1 = receipt.to_dict()
    r2 = receipt.to_dict()
    assert p1["provenance_sha256"] == p2["provenance_sha256"]
    assert r1["receipt_sha256"] == r2["receipt_sha256"]
    rendered = json.dumps({"provenance": p1, "receipt": r1}, sort_keys=True)
    assert "sk-this-must-not-leak" not in rendered
    assert "Bearer secret-value" not in rendered
    assert '"raw_secret_present": true' not in rendered.lower()
    assert receipt.execution_attempted is False and receipt.model_call_performed is False
    assert provider_authority_surface(r1) == ()

    span = provider_runtime_span(
        TraceContext.start(command="mp0d-test", trace_id="trace-mp0d", run_id="run-mp0d"),
        provenance,
        receipt,
    )
    span_payload = span.to_dict()
    rendered_span = json.dumps(span_payload, sort_keys=True)
    assert "sk-this-must-not-leak" not in rendered_span
    assert span_payload["payload"]["schema_id"] == "devpilot.mp-v2.provider-runtime-trace.v1"


def test_provider_runtime_contracts_do_not_expose_source_approval_freeze_quality_git_or_shell_authority():
    from devpilot_core.generation.runtime import GenerationRoute, ProviderExecutionReceipt

    route_fields = {field.name for field in fields(GenerationRoute)}
    receipt_fields = {field.name for field in fields(ProviderExecutionReceipt)}
    forbidden = {
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
    assert route_fields.isdisjoint(forbidden)
    assert receipt_fields.isdisjoint(forbidden)
