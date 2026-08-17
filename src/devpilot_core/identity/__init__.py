from __future__ import annotations

from .models import DEFAULT_IDENTITY_REGISTRY_PATH, DEFAULT_IDENTITY_SCHEMA_PATH, LocalActor, LocalRole, permission_for_action

__all__ = [
    "DEFAULT_IDENTITY_REGISTRY_PATH",
    "DEFAULT_IDENTITY_SCHEMA_PATH",
    "IdentityRegistry",
    "IdentityRegistryOptions",
    "LocalActor",
    "LocalRole",
    "RbacExposureOptions",
    "RbacExposureReporter",
    "RbacCheckInput",
    "permission_for_action",
]


def __getattr__(name: str):
    # Lazy imports avoid the historical identity <-> policy import cycle while
    # preserving the public package API used by existing callers.
    if name in {"IdentityRegistry", "IdentityRegistryOptions", "RbacCheckInput"}:
        from .rbac import IdentityRegistry, IdentityRegistryOptions, RbacCheckInput
        return {"IdentityRegistry": IdentityRegistry, "IdentityRegistryOptions": IdentityRegistryOptions, "RbacCheckInput": RbacCheckInput}[name]
    if name in {"RbacExposureOptions", "RbacExposureReporter"}:
        from .exposure import RbacExposureOptions, RbacExposureReporter
        return {"RbacExposureOptions": RbacExposureOptions, "RbacExposureReporter": RbacExposureReporter}[name]
    raise AttributeError(name)
