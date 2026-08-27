from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModelProviderKind(str, Enum):
    """Supported provider classes for DevPilot ModelAdapter routing."""

    MOCK = "mock"
    LOCAL = "local"
    API = "api"


class ModelTask(str, Enum):
    """Model tasks exposed by the historical ModelAdapter contract."""

    GENERATE = "generate"
    CLASSIFY = "classify"
    EMBED = "embed"


class RouteDisposition(str, Enum):
    """Runtime disposition of a provider/model access route.

    R01 research decisions such as ``allowed`` are intentionally kept in a
    separate field on :class:`ProviderAccessRoute`; they do not enable runtime.
    """

    ENABLED = "enabled"
    DISABLED = "disabled"
    CONDITIONAL = "conditional"
    UNKNOWN = "unknown"
    BLOCKED = "blocked"


class RouteLocality(str, Enum):
    MOCK = "mock"
    LOOPBACK = "loopback"
    REMOTE = "remote"
    CONSUMER_SESSION = "consumer-session"


@dataclass(frozen=True)
class ModelProviderConfig:
    """Safe historical provider configuration without raw secrets."""

    provider_id: str
    kind: ModelProviderKind
    enabled: bool
    default_model: str
    external_api: bool = False
    requires_api_key: bool = False
    api_key_env: str | None = None
    endpoint: str | None = None
    estimated_cost_per_1k_tokens_usd: float = 0.0
    status: str = "planned"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "kind": self.kind.value,
            "enabled": self.enabled,
            "default_model": self.default_model,
            "external_api": self.external_api,
            "requires_api_key": self.requires_api_key,
            "api_key_env": self.api_key_env,
            "endpoint": self.endpoint,
            "estimated_cost_per_1k_tokens_usd": self.estimated_cost_per_1k_tokens_usd,
            "status": self.status,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ProviderAccessRoute:
    """Identity-separated access route used by Model Gateway v2 decisions.

    A route is not a permission to execute tools. ``research_disposition``
    preserves the R01 evidence decision, while ``disposition`` and
    ``runtime_enabled`` express current runtime authority.
    """

    provider_id: str
    model_id: str
    access_route_id: str
    research_route_id: str
    gateway_adapter_id: str
    auth_adapter_id: str
    locality: RouteLocality
    endpoint_class: str
    disposition: RouteDisposition
    runtime_enabled: bool
    research_disposition: str
    reason: str
    evidence_refs: tuple[str, ...] = ()
    freshness: str = "historical"
    target_regions: tuple[str, ...] = ()
    external_api: bool = False
    opt_in_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "access_route_id": self.access_route_id,
            "research_route_id": self.research_route_id,
            "gateway_adapter_id": self.gateway_adapter_id,
            "auth_adapter_id": self.auth_adapter_id,
            "locality": self.locality.value,
            "endpoint_class": self.endpoint_class,
            "disposition": self.disposition.value,
            "runtime_enabled": self.runtime_enabled,
            "research_disposition": self.research_disposition,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
            "freshness": self.freshness,
            "target_regions": list(self.target_regions),
            "external_api": self.external_api,
            "opt_in_required": self.opt_in_required,
        }


@dataclass(frozen=True)
class ModelRoutingRequest:
    """Provider-agnostic routing request.

    Workflows request capabilities and constraints. They do not select a vendor
    model as an implicit implementation branch.
    """

    workload_id: str
    required_capabilities: tuple[str, ...] = ()
    privacy_class: str = "internal"
    data_classes: tuple[str, ...] = ()
    max_cost_usd: float | None = None
    offline_required: bool = False
    target_region: str | None = None
    allowed_regions: tuple[str, ...] = ()
    preferred_locality: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "workload_id": self.workload_id,
            "required_capabilities": list(self.required_capabilities),
            "privacy_class": self.privacy_class,
            "data_classes": list(self.data_classes),
            "max_cost_usd": self.max_cost_usd,
            "offline_required": self.offline_required,
            "target_region": self.target_region,
            "allowed_regions": list(self.allowed_regions),
            "preferred_locality": self.preferred_locality,
        }


@dataclass(frozen=True)
class ModelRouteDecision:
    """Model Gateway routing decision, explicitly separate from tool authority."""

    workload_id: str
    route_status: str
    provider_id: str | None = None
    model_id: str | None = None
    access_route_id: str | None = None
    gateway_adapter_id: str | None = None
    auth_adapter_id: str | None = None
    matched_capabilities: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    estimated_cost_usd: float | None = None
    fallback_access_route_id: str | None = None
    blocked_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        # Deliberately no ToolExecutionDecision, tool permission, skill grant,
        # approval or capability-escalation fields exist in this contract.
        return {
            "workload_id": self.workload_id,
            "route_status": self.route_status,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "access_route_id": self.access_route_id,
            "gateway_adapter_id": self.gateway_adapter_id,
            "auth_adapter_id": self.auth_adapter_id,
            "matched_capabilities": list(self.matched_capabilities),
            "evidence_refs": list(self.evidence_refs),
            "estimated_cost_usd": self.estimated_cost_usd,
            "fallback_access_route_id": self.fallback_access_route_id,
            "blocked_reason": self.blocked_reason,
        }


@dataclass(frozen=True)
class ModelCallRequest:
    """Normalized request sent to a ModelAdapter."""

    task: ModelTask
    prompt: str | None = None
    text: str | None = None
    labels: tuple[str, ...] = ()
    provider: str = "mock"
    model: str | None = None
    dry_run: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelCallResult:
    """Provider-level model result before conversion to CommandResult."""

    ok: bool
    provider: str
    model: str
    task: ModelTask
    content: str | None = None
    label: str | None = None
    embedding: list[float] = field(default_factory=list)
    tokens_estimated: int = 0
    cost_estimate_usd: float = 0.0
    external_api_used: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "provider": self.provider,
            "model": self.model,
            "task": self.task.value,
            "content": self.content,
            "label": self.label,
            "embedding": self.embedding,
            "tokens_estimated": self.tokens_estimated,
            "cost_estimate_usd": self.cost_estimate_usd,
            "external_api_used": self.external_api_used,
            "metadata": self.metadata,
        }


class ModelAdapter(ABC):
    """Abstract base class for provider-specific adapters."""

    provider_config: ModelProviderConfig

    @abstractmethod
    def generate(self, request: ModelCallRequest) -> ModelCallResult:
        """Generate text for a prompt."""

    @abstractmethod
    def classify(self, request: ModelCallRequest) -> ModelCallResult:
        """Classify text into one of the provided labels."""

    @abstractmethod
    def embed(self, request: ModelCallRequest) -> ModelCallResult:
        """Return a deterministic embedding vector for text."""
