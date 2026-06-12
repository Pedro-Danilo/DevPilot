from __future__ import annotations

from devpilot_core.modeling.contracts import (
    ModelAdapter,
    ModelCallRequest,
    ModelCallResult,
    ModelProviderConfig,
    ModelProviderKind,
    ModelTask,
)
from devpilot_core.modeling.mock_adapter import MockModelAdapter
from devpilot_core.modeling.ollama_adapter import OllamaAdapter
from devpilot_core.modeling.lmstudio_adapter import LMStudioAdapter
from devpilot_core.modeling.providers import ProviderRegistry, parse_provider_config_file, parse_providers_yaml, validate_provider_configs
from devpilot_core.modeling.router import ModelAdapterRouter, ModelRouterConfig

__all__ = [
    "ModelAdapter",
    "ModelAdapterRouter",
    "ModelCallRequest",
    "ModelCallResult",
    "ModelProviderConfig",
    "ModelProviderKind",
    "ModelRouterConfig",
    "ModelTask",
    "LMStudioAdapter",
    "MockModelAdapter",
    "OllamaAdapter",
    "ProviderRegistry",
    "parse_provider_config_file",
    "parse_providers_yaml",
    "validate_provider_configs",
]
