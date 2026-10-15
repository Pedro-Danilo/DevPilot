"""R01-03 offline capability negotiation; NOT a replacement for model routing/CostGuard.

SUPPORTED is a declared adapter contract, never proof of runtime health.
CONFIGURED, HEALTHY, EVALUATED and ELIGIBLE are distinct runtime assertions.
External models and implicit fallback are deliberately excluded in this increment.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet
from urllib.parse import urlsplit

from devpilot_core.modeling.contracts import (
    ModelAdapter, ModelCallRequest, ModelCallResult, ModelProviderConfig,
    ModelProviderKind, ModelTask,
)
from devpilot_core.modeling.mock_adapter import MockModelAdapter


class NegotiationBlocked(ValueError):
    """A requested execution route has not passed explicit capability negotiation."""


@dataclass(frozen=True)
class AdapterCapabilities:
    provider_id: str
    tasks: FrozenSet[ModelTask]
    supports_tools: bool = False
    supports_streaming: bool = False
    max_timeout_seconds: float = 30.0
    configured: bool = False
    healthy: bool = False
    evaluated: bool = False
    eligible: bool = False

    def __post_init__(self) -> None:
        if not self.provider_id.strip() or not self.tasks:
            raise ValueError("provider-id-and-tasks-required")
        if self.max_timeout_seconds <= 0 or self.max_timeout_seconds > 120:
            raise ValueError("timeout-limit-outside-allowed-range")
        if self.eligible and not (self.configured and self.healthy and self.evaluated):
            raise ValueError("eligible-requires-configured-healthy-evaluated")

    def snapshot(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "SUPPORTED": sorted(task.value for task in self.tasks),
            "CONFIGURED": self.configured,
            "HEALTHY": self.healthy,
            "EVALUATED": self.evaluated,
            "ELIGIBLE": self.eligible,
            "tools": self.supports_tools,
            "streaming": self.supports_streaming,
            "timeout_max_seconds": self.max_timeout_seconds,
        }


@dataclass(frozen=True)
class CapabilityRequest:
    provider_id: str
    task: ModelTask
    tools: bool = False
    streaming: bool = False
    timeout_seconds: float = 20.0


@dataclass(frozen=True)
class NegotiatedCapability:
    provider_id: str
    allowed: bool
    reason: str
    state: dict
    fallback: None = None  # no implicit fallback


class LocalStubModelAdapter(ModelAdapter):
    """Adapter boundary for local providers; does not start or contact a server."""

    def __init__(self, provider_config: ModelProviderConfig) -> None:
        if provider_config.kind is not ModelProviderKind.LOCAL or provider_config.external_api or provider_config.requires_api_key:
            raise ValueError("LOCAL_STUB_REQUIRES_LOCAL_NO_KEY")
        parts = urlsplit(provider_config.endpoint or "")
        if parts.scheme != "http" or parts.hostname not in {"localhost", "127.0.0.1", "::1"} or parts.username or parts.password or parts.query or parts.fragment:
            raise ValueError("LOCAL_ENDPOINT_LOOPBACK_REQUIRED")
        self.provider_config = provider_config

    def _unavailable(self, request: ModelCallRequest) -> ModelCallResult:
        return ModelCallResult(
            ok=False,
            provider=self.provider_config.provider_id,
            model=request.model or self.provider_config.default_model,
            task=request.task,
            external_api_used=False,
            metadata={"reason": "LOCAL_STUB_NOT_CONNECTED", "network_used": False, "fallback": None},
        )

    def generate(self, request: ModelCallRequest) -> ModelCallResult:
        return self._unavailable(request)

    def classify(self, request: ModelCallRequest) -> ModelCallResult:
        return self._unavailable(request)

    def embed(self, request: ModelCallRequest) -> ModelCallResult:
        return self._unavailable(request)


class OfflineCapabilityNegotiator:
    """Explicit provider selection, fail-closed, no network and no fallback.

    The caller must provide live/evaluated state; absence of that evidence is false.
    Only the deterministic mock can execute; local profiles use a non-I/O stub.
    This service is NOT authorized to replace the governed ModelRouterV2.
    """

    def __init__(self, configs: tuple[ModelProviderConfig, ...], profiles: tuple[AdapterCapabilities, ...]):
        self._configs = {p.provider_id: p for p in configs}
        self._profiles = {p.provider_id: p for p in profiles}
        if len(self._configs) != len(configs) or len(self._profiles) != len(profiles):
            raise ValueError("DUPLICATE_PROVIDER_ID")
        for identity, config in self._configs.items():
            if config.kind is ModelProviderKind.API or config.external_api:
                raise ValueError("EXTERNAL_PROVIDER_DENIED")
            profile = self._profiles.get(identity)
            if profile is None:
                raise ValueError("MISSING_PROVIDER_PROFILE")
            if config.kind is ModelProviderKind.LOCAL:
                LocalStubModelAdapter(config)  # enforce loopback/secret constraints without IO
            elif config.kind is not ModelProviderKind.MOCK:
                raise ValueError("UNSUPPORTED_PROVIDER_KIND")
            if profile.configured and not config.enabled:
                raise ValueError("CONFIGURED_BUT_PROVIDER_DISABLED")
            if identity != "mock" and profile.eligible:
                raise ValueError("LOCAL_STUB_CANNOT_BE_EXECUTION_ELIGIBLE")

    def negotiate(self, request: CapabilityRequest) -> NegotiatedCapability:
        profile = self._profiles.get(request.provider_id)
        config = self._configs.get(request.provider_id)
        if profile is None or config is None:
            return NegotiatedCapability(request.provider_id, False, "UNKNOWN_PROVIDER", {})
        reason = "ELIGIBLE"
        if request.task not in profile.tasks:
            reason = "UNSUPPORTED_TASK"
        elif request.tools and not profile.supports_tools:
            reason = "TOOLS_UNSUPPORTED"
        elif request.streaming and not profile.supports_streaming:
            reason = "STREAMING_UNSUPPORTED"
        elif not (0 < request.timeout_seconds <= profile.max_timeout_seconds):
            reason = "TIMEOUT_UNSUPPORTED"
        elif not profile.configured:
            reason = "NOT_CONFIGURED"
        elif not profile.healthy:
            reason = "NOT_HEALTHY"
        elif not profile.evaluated:
            reason = "NOT_EVALUATED"
        elif not profile.eligible:
            reason = "NOT_ELIGIBLE"
        elif config.kind is not ModelProviderKind.MOCK:
            reason = "LOCAL_STUB_NOT_EXECUTABLE"
        return NegotiatedCapability(request.provider_id, reason == "ELIGIBLE", reason, profile.snapshot())

    def execute_mock(self, capability: CapabilityRequest, request: ModelCallRequest) -> ModelCallResult:
        decision = self.negotiate(capability)
        if not decision.allowed or capability.provider_id != "mock" or request.task != capability.task or request.provider != "mock":
            raise NegotiationBlocked(decision.reason if not decision.allowed else "REQUEST_IDENTITY_MISMATCH")
        return {
            ModelTask.GENERATE: MockModelAdapter(self._configs["mock"]).generate,
            ModelTask.CLASSIFY: MockModelAdapter(self._configs["mock"]).classify,
            ModelTask.EMBED: MockModelAdapter(self._configs["mock"]).embed,
        }[request.task](request)


def default_offline_negotiator() -> OfflineCapabilityNegotiator:
    """Safe example: configured mock, unconfigured local stub, zero server calls."""
    from devpilot_core.modeling.providers import DEFAULT_PROVIDER_CONFIGS
    mock = next(p for p in DEFAULT_PROVIDER_CONFIGS if p.provider_id == "mock")
    local = next(p for p in DEFAULT_PROVIDER_CONFIGS if p.provider_id == "ollama")
    return OfflineCapabilityNegotiator(
        (mock, local),
        (
            AdapterCapabilities("mock", frozenset(ModelTask), configured=True, healthy=True, evaluated=True, eligible=True),
            AdapterCapabilities("ollama", frozenset({ModelTask.GENERATE}), configured=False, healthy=False, evaluated=False, eligible=False),
        ),
    )
