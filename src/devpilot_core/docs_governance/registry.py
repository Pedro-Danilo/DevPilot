from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import DocumentationSourceRegistry

DOCUMENTATION_SOURCE_REGISTRY_SCHEMA_ID = "SCHEMA-DEVPL-DOCUMENTATION-SOURCE-REGISTRY-V1"
DOCUMENTATION_GOVERNANCE_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-DOCUMENTATION-GOVERNANCE-REPORT-V1"
DEFAULT_DOCUMENTATION_SOURCE_REGISTRY = Path(".devpilot/docs_governance/source_registry.json")


def load_documentation_source_registry(root: Path, path: str | Path = DEFAULT_DOCUMENTATION_SOURCE_REGISTRY) -> DocumentationSourceRegistry:
    """Load the POST-H-009-A documentation source registry without side effects."""

    registry_path = Path(path)
    resolved = registry_path if registry_path.is_absolute() else Path(root) / registry_path
    payload: dict[str, Any] = json.loads(resolved.read_text(encoding="utf-8"))
    return DocumentationSourceRegistry.from_dict(payload)


class DocumentationSourceRegistryReader:
    """Small read-only helper reserved for POST-H-009-B validator evolution."""

    def __init__(self, root: Path, path: str | Path = DEFAULT_DOCUMENTATION_SOURCE_REGISTRY) -> None:
        self.root = Path(root)
        self.path = Path(path)

    def load(self) -> DocumentationSourceRegistry:
        return load_documentation_source_registry(self.root, self.path)

    def source_paths(self) -> list[str]:
        return sorted(item.path for item in self.load().documents)
