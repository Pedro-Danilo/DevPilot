from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SchemaSpec:
    """Metadata for one registered DevPilot schema.

    FUNC-SPRINT-21 introduces Schema Registry as a catalog-only capability: it
    lists versioned JSON contracts and verifies catalog integrity, but it does
    not perform JSON Schema instance validation. Full instance validation is
    intentionally deferred to FUNC-SPRINT-22 so DevPilot can keep the registry
    dependency-free and local-first in this sprint.
    """

    schema_id: str
    title: str
    version: str
    path: str
    description: str
    status: str = "draft"
    contract: str | None = None
    owner: str = "Ordóñez"
    sprint: str = "FUNC-SPRINT-21"
    dialect: str = "https://json-schema.org/draft/2020-12/schema"
    validates_instances: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SchemaSpec":
        return cls(
            schema_id=str(data.get("schema_id", "")).strip(),
            title=str(data.get("title", "")).strip(),
            version=str(data.get("version", "")).strip(),
            path=str(data.get("path", "")).strip().replace("\\", "/"),
            description=str(data.get("description", "")).strip(),
            status=str(data.get("status", "draft")).strip(),
            contract=str(data["contract"]).strip() if data.get("contract") is not None else None,
            owner=str(data.get("owner", "Ordóñez")).strip(),
            sprint=str(data.get("sprint", "FUNC-SPRINT-21")).strip(),
            dialect=str(data.get("dialect", "https://json-schema.org/draft/2020-12/schema")).strip(),
            validates_instances=bool(data.get("validates_instances", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_id": self.schema_id,
            "title": self.title,
            "version": self.version,
            "path": self.path,
            "description": self.description,
            "status": self.status,
            "owner": self.owner,
            "sprint": self.sprint,
            "dialect": self.dialect,
            "validates_instances": self.validates_instances,
        }
        if self.contract:
            payload["contract"] = self.contract
        return payload

    def absolute_path(self, root: Path) -> Path:
        return root / self.path


@dataclass(frozen=True)
class SchemaRegistrySummary:
    """Compact integrity summary for the schema registry."""

    schemas_total: int
    schemas_existing: int
    duplicate_schema_ids: list[str]
    missing_schema_paths: list[str]
    catalog_path: str
    preliminary: bool = True

    @property
    def ok(self) -> bool:
        return not self.duplicate_schema_ids and not self.missing_schema_paths

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemas_total": self.schemas_total,
            "schemas_existing": self.schemas_existing,
            "duplicate_schema_ids": self.duplicate_schema_ids,
            "missing_schema_paths": self.missing_schema_paths,
            "catalog_path": self.catalog_path,
            "preliminary": self.preliminary,
        }
