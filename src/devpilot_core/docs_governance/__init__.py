"""Documentation governance primitives for DevPilot Local.

POST-H-009-A introduces the canonical source registry and schemas only.
Executable drift/frontmatter validation is intentionally deferred to later
micro-sprints in POST-H-009.
"""

from .registry import (
    DEFAULT_DOCUMENTATION_SOURCE_REGISTRY,
    DOCUMENTATION_GOVERNANCE_REPORT_SCHEMA_ID,
    DOCUMENTATION_SOURCE_REGISTRY_SCHEMA_ID,
    DocumentationSourceRegistry,
    load_documentation_source_registry,
)

__all__ = [
    "DEFAULT_DOCUMENTATION_SOURCE_REGISTRY",
    "DOCUMENTATION_GOVERNANCE_REPORT_SCHEMA_ID",
    "DOCUMENTATION_SOURCE_REGISTRY_SCHEMA_ID",
    "DocumentationSourceRegistry",
    "load_documentation_source_registry",
]
