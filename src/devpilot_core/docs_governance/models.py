from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DOCUMENT_CLASSIFICATIONS = {
    "source-of-truth",
    "machine-readable-source",
    "derived",
    "generated-runtime",
    "historical",
    "deprecated",
}


@dataclass(frozen=True)
class DocumentationSource:
    """One document or registry governed by the canonical source registry."""

    doc_id: str
    path: str
    classification: str
    domain: str
    owner: str
    status_required: str
    criticality: str
    required_tests: tuple[str, ...] = field(default_factory=tuple)
    sync_rules: tuple[str, ...] = field(default_factory=tuple)
    machine_readable_counterparts: tuple[str, ...] = field(default_factory=tuple)
    human_readable_counterparts: tuple[str, ...] = field(default_factory=tuple)
    derived_documents: tuple[str, ...] = field(default_factory=tuple)
    related_adrs: tuple[str, ...] = field(default_factory=tuple)
    roadmap_milestones: tuple[str, ...] = field(default_factory=tuple)
    lifecycle: str = "active"
    notes: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DocumentationSource":
        return cls(
            doc_id=str(payload.get("doc_id", "")),
            path=str(payload.get("path", "")),
            classification=str(payload.get("classification", "")),
            domain=str(payload.get("domain", "")),
            owner=str(payload.get("owner", "")),
            status_required=str(payload.get("status_required", "")),
            criticality=str(payload.get("criticality", "")),
            required_tests=tuple(str(item) for item in payload.get("required_tests", []) if isinstance(item, str)),
            sync_rules=tuple(str(item) for item in payload.get("sync_rules", []) if isinstance(item, str)),
            machine_readable_counterparts=tuple(str(item) for item in payload.get("machine_readable_counterparts", []) if isinstance(item, str)),
            human_readable_counterparts=tuple(str(item) for item in payload.get("human_readable_counterparts", []) if isinstance(item, str)),
            derived_documents=tuple(str(item) for item in payload.get("derived_documents", []) if isinstance(item, str)),
            related_adrs=tuple(str(item) for item in payload.get("related_adrs", []) if isinstance(item, str)),
            roadmap_milestones=tuple(str(item) for item in payload.get("roadmap_milestones", []) if isinstance(item, str)),
            lifecycle=str(payload.get("lifecycle", "active")),
            notes=tuple(str(item) for item in payload.get("notes", []) if isinstance(item, str)),
        )

    @property
    def is_source_of_truth(self) -> bool:
        return self.classification == "source-of-truth"

    @property
    def is_machine_readable_source(self) -> bool:
        return self.classification == "machine-readable-source"

    @property
    def is_critical(self) -> bool:
        return self.criticality in {"P0", "P1"}


@dataclass(frozen=True)
class DocumentationSourceRegistry:
    """In-memory representation of .devpilot/docs_governance/source_registry.json."""

    registry_id: str
    schema_id: str
    status: str
    documents: tuple[DocumentationSource, ...]
    summary: dict[str, Any]
    rules: dict[str, Any]
    safety: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DocumentationSourceRegistry":
        return cls(
            registry_id=str(payload.get("registry_id", "")),
            schema_id=str(payload.get("schema_id", "")),
            status=str(payload.get("status", "")),
            documents=tuple(DocumentationSource.from_dict(item) for item in payload.get("documents", []) if isinstance(item, dict)),
            summary=dict(payload.get("summary", {})),
            rules=dict(payload.get("rules", {})),
            safety=dict(payload.get("safety", {})),
        )

    def by_path(self) -> dict[str, DocumentationSource]:
        return {item.path: item for item in self.documents}

    def source_of_truth_documents(self) -> tuple[DocumentationSource, ...]:
        return tuple(item for item in self.documents if item.is_source_of_truth)

    def machine_readable_sources(self) -> tuple[DocumentationSource, ...]:
        return tuple(item for item in self.documents if item.is_machine_readable_source)
