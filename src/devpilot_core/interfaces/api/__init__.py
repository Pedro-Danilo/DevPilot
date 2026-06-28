from __future__ import annotations

from devpilot_core.interfaces.api.app import DEFAULT_API_HOST, DEFAULT_API_PORT, api_route_paths, api_security_summary, create_app
from devpilot_core.interfaces.api.contracts import (
    DEFAULT_API_ROUTE_CONTRACT_REGISTRY,
    ApiRouteContractRegistryValidator,
    ApiRouteContractValidationOptions,
)
from devpilot_core.interfaces.api.response_mapping import (
    DEFAULT_API_RESPONSE_MAPPING,
    POST_H_014_B_CREATED_BY,
    ApiResponseMapping,
    api_error_response,
    command_result_to_api_response,
    http_status_for_exit_code,
    response_mapping_summary,
    unhandled_exception_response,
    validation_error_response,
)
from devpilot_core.interfaces.api.security import API_TOKEN_ENV_VAR, API_TOKEN_HEADER, DEFAULT_ALLOWED_ORIGINS, generate_api_token, redact_token
from devpilot_core.interfaces.api.ui_contracts import (
    DEFAULT_UI_ROUTE_CONTRACT_REGISTRY,
    POST_H_014_C_CREATED_BY,
    UI_ROUTE_CONTRACT_REGISTRY_SCHEMA,
    UiRouteContractRegistryValidator,
    validate_ui_route_contract_registry,
)

__all__ = [
    "DEFAULT_API_ROUTE_CONTRACT_REGISTRY",
    "DEFAULT_API_RESPONSE_MAPPING",
    "DEFAULT_UI_ROUTE_CONTRACT_REGISTRY",
    "POST_H_014_B_CREATED_BY",
    "POST_H_014_C_CREATED_BY",
    "UI_ROUTE_CONTRACT_REGISTRY_SCHEMA",
    "ApiResponseMapping",
    "api_error_response",
    "command_result_to_api_response",
    "http_status_for_exit_code",
    "response_mapping_summary",
    "unhandled_exception_response",
    "validation_error_response",
    "ApiRouteContractRegistryValidator",
    "ApiRouteContractValidationOptions",
    "UiRouteContractRegistryValidator",
    "validate_ui_route_contract_registry",
    "API_TOKEN_ENV_VAR",
    "API_TOKEN_HEADER",
    "DEFAULT_ALLOWED_ORIGINS",
    "DEFAULT_API_HOST",
    "DEFAULT_API_PORT",
    "api_route_paths",
    "api_security_summary",
    "create_app",
    "generate_api_token",
    "redact_token",
]
