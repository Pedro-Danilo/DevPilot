"""Operator onboarding helpers for POST-H-024.

The package is local-first and currently exposes only template metadata/validation helpers.
It does not create workspaces, write project files, call networks or invoke LLMs.
"""

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
]
