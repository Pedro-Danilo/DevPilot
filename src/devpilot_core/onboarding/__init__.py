"""Operator onboarding helpers for POST-H-024.

The package is local-first and exposes template metadata plus onboarding readiness preview helpers.
It does not call networks, invoke LLMs or perform source mutations.
"""

from devpilot_core.onboarding.readiness_preview import (
    DEFAULT_ONBOARDING_READINESS_PREVIEW_JSON,
    DEFAULT_ONBOARDING_READINESS_PREVIEW_MARKDOWN,
    DEFAULT_PREVIEW_TARGET_ROOT,
    ONBOARDING_READINESS_PREVIEW_SCHEMA_ID,
    ONBOARDING_READINESS_PREVIEW_SCHEMA_PATH,
    OnboardingReadinessPreviewOptions,
    OnboardingReadinessPreviewer,
)

_QUALITY_GATE_EXPORTS = {
    "OnboardingBootstrapReadyGateOptions",
    "OnboardingBootstrapReadyGate",
    "POST_H_024_E_CREATED_BY",
    "ONBOARDING_BOOTSTRAP_READY_SUBGATE",
    "DEFAULT_ONBOARDING_PILOT_FIXTURE",
}


def __getattr__(name: str):
    """Lazily expose POST-H-024-E quality gate symbols.

    The lazy import avoids a workspace -> onboarding -> quality_gate -> workspace
    cycle when workspace bootstrap imports onboarding template metadata during CLI startup.
    """
    if name in _QUALITY_GATE_EXPORTS:
        from devpilot_core.onboarding import quality_gate as _quality_gate

        return getattr(_quality_gate, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

from devpilot_core.onboarding.templates import (
    MARKDOWN_TEMPLATE_PATHS,
    MIASI_TEMPLATE_PATHS,
    REQUIRED_TEMPLATE_PATHS,
    TemplateValidationResult,
    validate_new_project_templates,
)

__all__ = [
    "OnboardingBootstrapReadyGateOptions",
    "OnboardingBootstrapReadyGate",
    "POST_H_024_E_CREATED_BY",
    "ONBOARDING_BOOTSTRAP_READY_SUBGATE",
    "DEFAULT_ONBOARDING_PILOT_FIXTURE",
    "MARKDOWN_TEMPLATE_PATHS",
    "MIASI_TEMPLATE_PATHS",
    "REQUIRED_TEMPLATE_PATHS",
    "TemplateValidationResult",
    "validate_new_project_templates",
    "DEFAULT_ONBOARDING_READINESS_PREVIEW_JSON",
    "DEFAULT_ONBOARDING_READINESS_PREVIEW_MARKDOWN",
    "DEFAULT_PREVIEW_TARGET_ROOT",
    "ONBOARDING_READINESS_PREVIEW_SCHEMA_ID",
    "ONBOARDING_READINESS_PREVIEW_SCHEMA_PATH",
    "OnboardingReadinessPreviewOptions",
    "OnboardingReadinessPreviewer",
]
