from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvidenceGraphSourceSpec:
    """Source declaration consumed by the POST-H-031-A evidence graph builder.

    The declaration is metadata-only. It never grants permission to execute a
    command, read secrets or treat runtime evidence as versioned source of truth.
    """

    source_id: str
    path: str
    node_type: str
    evidence_class: str
    title: str
    required: bool = False
    category: str | None = None
    expected_schema_id: str | None = None
    generated_by: str | None = None
    validates_against: str | None = None
    supports_claims: tuple[str, ...] = field(default_factory=tuple)
    relates_to_gates: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvidenceGraphSourceSpec":
        return cls(
            source_id=str(payload.get("source_id") or ""),
            path=str(payload.get("path") or ""),
            node_type=str(payload.get("node_type") or "evidence"),
            evidence_class=str(payload.get("evidence_class") or "versioned_source"),
            title=str(payload.get("title") or payload.get("source_id") or "Evidence source"),
            required=bool(payload.get("required", False)),
            category=payload.get("category"),
            expected_schema_id=payload.get("expected_schema_id"),
            generated_by=payload.get("generated_by"),
            validates_against=payload.get("validates_against"),
            supports_claims=tuple(str(item) for item in payload.get("supports_claims", []) if item),
            relates_to_gates=tuple(str(item) for item in payload.get("relates_to_gates", []) if item),
            tags=tuple(str(item) for item in payload.get("tags", []) if item),
            notes=tuple(str(item) for item in payload.get("notes", []) if item),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "path": self.path,
            "node_type": self.node_type,
            "evidence_class": self.evidence_class,
            "title": self.title,
            "required": self.required,
            "category": self.category,
            "expected_schema_id": self.expected_schema_id,
            "generated_by": self.generated_by,
            "validates_against": self.validates_against,
            "supports_claims": list(self.supports_claims),
            "relates_to_gates": list(self.relates_to_gates),
            "tags": list(self.tags),
            "notes": list(self.notes),
        }

    def resolved(self, root: Path) -> Path:
        return root / self.path


@dataclass(frozen=True)
class EvidenceGraphOptions:
    sources_path: Path = Path(".devpilot/evidence/evidence_graph_sources.json")
    write_report: bool = False
    output_json: Path = Path("outputs/reports/evidence_graph.json")
    output_markdown: Path = Path("outputs/reports/evidence_graph.md")
