from __future__ import annotations

from pathlib import Path
from typing import Any

from .operation_catalog import ApplicationOperationCatalogBuilder


class ApplicationCapabilityRegistry:
    """Read-only facade over the POST-H-007-B ApplicationOperationCatalog.

    This class gives later interface-policy and DTO-normalization sprints a small
    lookup surface without coupling them to report generation details. It is not
    a runtime router and does not execute operations.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def catalog(self) -> dict[str, Any]:
        return ApplicationOperationCatalogBuilder(self.root).build_catalog().to_dict()

    def get(self, operation_id: str) -> dict[str, Any] | None:
        for operation in self.catalog().get("operations", []):
            if operation.get("operation_id") == operation_id:
                return operation
        return None

    def list_operation_ids(self) -> list[str]:
        return [str(operation["operation_id"]) for operation in self.catalog().get("operations", [])]
