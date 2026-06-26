"""Documentation governance primitives for DevPilot Local.

POST-H-009-A introduces the canonical source registry and schemas.
POST-H-009-B adds the first deterministic validator for frontmatter,
status and ownership metadata. POST-H-009-C adds deterministic
Markdown/JSON synchronization checks. POST-H-009-D adds executable
backlog governance for roadmap-derived backlog documents without enabling
quality-gate integration yet.
"""

from .backlogs import DocumentationBacklogGovernanceValidator
from .drift import DocumentationSyncValidator
from .registry import (
    DEFAULT_DOCUMENTATION_SOURCE_REGISTRY,
    DOCUMENTATION_GOVERNANCE_REPORT_SCHEMA_ID,
    DOCUMENTATION_SOURCE_REGISTRY_SCHEMA_ID,
    DocumentationSourceRegistry,
    load_documentation_source_registry,
)
from .validator import (
    DEFAULT_DOCUMENTATION_GOVERNANCE_JSON,
    DEFAULT_DOCUMENTATION_GOVERNANCE_MARKDOWN,
    DOCUMENTATION_GOVERNANCE_CONTRACT,
    DOCUMENTATION_GOVERNANCE_REPORT_ID,
    DocumentationGovernanceValidationOptions,
    DocumentationGovernanceValidator,
    render_documentation_governance_markdown,
)

__all__ = [
    "DocumentationBacklogGovernanceValidator",
    "DocumentationSyncValidator",
    "DEFAULT_DOCUMENTATION_SOURCE_REGISTRY",
    "DOCUMENTATION_GOVERNANCE_REPORT_SCHEMA_ID",
    "DOCUMENTATION_SOURCE_REGISTRY_SCHEMA_ID",
    "DocumentationSourceRegistry",
    "load_documentation_source_registry",
    "DEFAULT_DOCUMENTATION_GOVERNANCE_JSON",
    "DEFAULT_DOCUMENTATION_GOVERNANCE_MARKDOWN",
    "DOCUMENTATION_GOVERNANCE_CONTRACT",
    "DOCUMENTATION_GOVERNANCE_REPORT_ID",
    "DocumentationGovernanceValidationOptions",
    "DocumentationGovernanceValidator",
    "render_documentation_governance_markdown",
]
