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
    """Model tasks exposed by FUNC-SPRINT-17."""

    GENERATE = "generate"
    CLASSIFY = "classify"
    EMBED = "embed"


@dataclass(frozen=True)
class ModelProviderConfig:
    """Safe provider configuration without raw secrets.

    The configuration stores only provider metadata and environment variable
    names. API keys or secret values must never be written here.
    """

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
    """Abstract base class for provider-specific adapters.

    FUNC-SPRINT-17 defines this contract so future local/API integrations can be
    plugged into DevPilot without changing agents, evaluators or CLI commands.
    """

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
