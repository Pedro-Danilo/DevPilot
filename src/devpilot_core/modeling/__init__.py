from __future__ import annotations

from devpilot_core.modeling.contracts import (
    ModelAdapter,
    ModelCallRequest,
    ModelCallResult,
    ModelProviderConfig,
    ModelProviderKind,
    ModelRouteDecision,
    ModelRoutingRequest,
    ModelTask,
    ProviderAccessRoute,
    RouteDisposition,
    RouteLocality,
)
from devpilot_core.modeling.catalog import CapabilityMatch, ModelCapabilityCatalog, ModelCapabilityCatalogError
from devpilot_core.modeling.mock_adapter import MockModelAdapter
from devpilot_core.modeling.ollama_adapter import OllamaAdapter
from devpilot_core.modeling.lmstudio_adapter import LMStudioAdapter
from devpilot_core.modeling.health import ModelHealthService
from devpilot_core.modeling.local_provider_health import LocalLlmProviderHealthOptions, LocalLlmProviderHealthReporter
from devpilot_core.modeling.external_api_pilot import ExternalApiProviderPilotOptions, ExternalApiProviderPilotReporter, FakeExternalApiProvider
from devpilot_core.modeling.capabilities import CapabilityMatrix
from devpilot_core.modeling.budget import BudgetLedger
from devpilot_core.modeling.evals import ModelEvalRunner, ModelEvalRunnerConfig
from devpilot_core.modeling.providers import ProviderRegistry, parse_provider_config_file, parse_providers_yaml, validate_provider_configs
from devpilot_core.modeling.router import ModelAdapterRouter, ModelRouterConfig

__all__ = [
    "ModelAdapter", "ModelAdapterRouter", "ModelCallRequest", "ModelCallResult", "ModelProviderConfig", "ModelProviderKind",
    "ModelRouteDecision", "ModelRoutingRequest", "ProviderAccessRoute", "RouteDisposition", "RouteLocality",
    "ModelCapabilityCatalog", "ModelCapabilityCatalogError", "CapabilityMatch",
    "ModelRouterConfig", "ModelTask", "BudgetLedger", "CapabilityMatrix", "LMStudioAdapter", "ModelHealthService",
    "LocalLlmProviderHealthOptions", "LocalLlmProviderHealthReporter", "FakeExternalApiProvider", "ExternalApiProviderPilotReporter",
    "ExternalApiProviderPilotOptions", "ModelEvalRunner", "ModelEvalRunnerConfig", "MockModelAdapter", "OllamaAdapter", "ProviderRegistry",
    "parse_provider_config_file", "parse_providers_yaml", "validate_provider_configs",
]
from .local_endpoint_policy import LocalEndpointPolicy, LocalEndpointDecision, LocalEndpointPolicyError, LocalHttpLimits
from .local_provider_discovery import LocalProviderDiscoveryService, LocalProviderDiscoveryOptions
from .openai_compatible_local_adapter import OpenAICompatibleLocalAdapter

from .provider_credentials import (
    ProviderCredentialReference, CredentialReferenceType, CredentialMaterial, CredentialResolutionError,
    LocalLoopbackNoSecretAdapter, EnvApiKeyAdapter, ProviderNativeIdentityAdapter, ConsumerSessionAdapter, auth_adapter_for,
)
from .external_provider_enablement import (
    EnablementGateReport, ProviderEnablementRequest, ProviderEnablementStore, ExternalProviderEnablementService,
    FakeConnectivityResponse, REQUIRED_GATE_IDS, REQUIRED_NOTICE_IDS, enablement_request_from_dict,
)
