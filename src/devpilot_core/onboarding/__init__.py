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
from devpilot_core.onboarding.templates import (
    MARKDOWN_TEMPLATE_PATHS,
    MIASI_TEMPLATE_PATHS,
    REQUIRED_TEMPLATE_PATHS,
    TemplateValidationResult,
    validate_new_project_templates,
)

__all__ = [
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
