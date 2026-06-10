from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TraceEntityType(str, Enum):
    """Supported traceability entity types for FUNC-SPRINT-25.

    The model intentionally mirrors the conservative ID prefixes requested by
    the Fase A backlog. It does not infer business semantics or relationships;
    later sprints can add richer types without changing the scan command shape.
    """

    FUNCTIONAL_REQUIREMENT = "functional_requirement"
    REQUIREMENT = "requirement"
    USER_STORY = "user_story"
    ACCEPTANCE_CRITERION = "acceptance_criterion"
    TEST = "test"
    ADR = "adr"


PREFIX_TO_ENTITY_TYPE: dict[str, TraceEntityType] = {
    "FR": TraceEntityType.FUNCTIONAL_REQUIREMENT,
    "REQ": TraceEntityType.REQUIREMENT,
    "US": TraceEntityType.USER_STORY,
    "AC": TraceEntityType.ACCEPTANCE_CRITERION,
    "TEST": TraceEntityType.TEST,
    "ADR": TraceEntityType.ADR,
}


@dataclass(frozen=True)
class TraceEntity:
    """One conservative traceability entity occurrence detected in source text."""

    entity_id: str
    entity_type: TraceEntityType
    source_path: str
    line: int
    column: int
    raw_id: str | None = None
    context: str = ""

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "source_path": self.source_path,
            "line": self.line,
            "column": self.column,
            "context": self.context,
        }
        if self.raw_id is not None and self.raw_id != self.entity_id:
            data["raw_id"] = self.raw_id
        return data


@dataclass(frozen=True)
class TraceLink:
    """Explicit relationship between trace entities.

    FUNC-SPRINT-25 defines the model but does not infer links. Instances should
    only be created from explicit evidence in a later sprint.
    """

    source_entity_id: str
    target_entity_id: str
    link_type: str
    source_path: str
    evidence: str
    explicit: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_entity_id": self.source_entity_id,
            "target_entity_id": self.target_entity_id,
            "link_type": self.link_type,
            "source_path": self.source_path,
            "evidence": self.evidence,
            "explicit": self.explicit,
        }


@dataclass(frozen=True)
class InvalidTraceToken:
    """Malformed ID-like token detected by the conservative extractor."""

    raw_id: str
    normalized_candidate: str
    source_path: str
    line: int
    column: int
    reason: str
    context: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_id": self.raw_id,
            "normalized_candidate": self.normalized_candidate,
            "source_path": self.source_path,
            "line": self.line,
            "column": self.column,
            "reason": self.reason,
            "context": self.context,
        }


@dataclass(frozen=True)
class TraceGraph:
    """Serializable traceability graph snapshot.

    Sprint 25 stores entity occurrences and an empty link list by design. It is
    the data model foundation for Sprint 26 coverage/validation rules.
    """

    entities: list[TraceEntity] = field(default_factory=list)
    links: list[TraceLink] = field(default_factory=list)
    invalid_tokens: list[InvalidTraceToken] = field(default_factory=list)
    duplicate_entity_ids: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    source_paths: list[str] = field(default_factory=list)
    preliminary: bool = True

    def to_dict(self) -> dict[str, Any]:
        unique_ids = sorted({entity.entity_id for entity in self.entities})
        entity_type_counts: dict[str, int] = {}
        for entity in self.entities:
            entity_type_counts[entity.entity_type.value] = entity_type_counts.get(entity.entity_type.value, 0) + 1
        return {
            "summary": {
                "entities_total": len(self.entities),
                "unique_entities_total": len(unique_ids),
                "links_total": len(self.links),
                "invalid_tokens_total": len(self.invalid_tokens),
                "duplicate_entity_ids_total": len(self.duplicate_entity_ids),
                "source_paths_total": len(self.source_paths),
                "entity_type_counts": dict(sorted(entity_type_counts.items())),
                "preliminary": self.preliminary,
                "inferred_links": False,
            },
            "source_paths": self.source_paths,
            "entities": [entity.to_dict() for entity in self.entities],
            "links": [link.to_dict() for link in self.links],
            "invalid_tokens": [token.to_dict() for token in self.invalid_tokens],
            "duplicate_entity_ids": self.duplicate_entity_ids,
            "notes": [
                "FUNC-SPRINT-25 extracts ID occurrences only; it does not infer semantic traceability relationships.",
                "Trace links are intentionally empty unless future sprints add explicit evidence extraction.",
            ],
        }
