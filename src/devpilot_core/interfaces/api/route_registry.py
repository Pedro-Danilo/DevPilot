from __future__ import annotations

from pathlib import Path

from devpilot_core.interfaces.api.contracts import (
    DEFAULT_API_ROUTE_CONTRACT_REGISTRY,
    ApiRouteContractRegistryValidator,
    ApiRouteContractValidationOptions,
)


def validate_api_route_contract_registry(root: Path, *, registry_path: str | Path = DEFAULT_API_ROUTE_CONTRACT_REGISTRY):
    """Validate the API route contract registry for POST-H-014-A."""

    return ApiRouteContractRegistryValidator(root, options=ApiRouteContractValidationOptions(registry_path=Path(registry_path))).validate()


__all__ = [
    "DEFAULT_API_ROUTE_CONTRACT_REGISTRY",
    "ApiRouteContractRegistryValidator",
    "ApiRouteContractValidationOptions",
    "validate_api_route_contract_registry",
]
