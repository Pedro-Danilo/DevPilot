from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_DOCUMENTATION_AUTHORITY_GRAPH = Path('.devpilot/docs_governance/documentation_authority_graph.json')
DEFAULT_DOCUMENTATION_DRIFT_LEDGER = Path('.devpilot/docs_governance/documentation_drift_ledger.json')


@dataclass(frozen=True)
class DocumentationAuthorityNode:
    node_id: str
    doc_id: str
    path: str
    subject: str
    authority_rank: int
    authority_kind: str
    lifecycle: str
    classification: str
    successor: str | None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> 'DocumentationAuthorityNode':
        return cls(
            node_id=str(payload.get('node_id', '')),
            doc_id=str(payload.get('doc_id', '')),
            path=str(payload.get('path', '')),
            subject=str(payload.get('subject', '')),
            authority_rank=int(payload.get('authority_rank', 0)),
            authority_kind=str(payload.get('authority_kind', '')),
            lifecycle=str(payload.get('lifecycle', '')),
            classification=str(payload.get('classification', '')),
            successor=str(payload.get('successor')) if payload.get('successor') is not None else None,
        )


class DocumentationAuthorityGraph:
    """Read-only authority/lifecycle graph for documentation state reconciliation."""

    def __init__(self, root: Path, path: str | Path = DEFAULT_DOCUMENTATION_AUTHORITY_GRAPH) -> None:
        self.root = Path(root).resolve()
        self.path = Path(path)
        resolved = self.path if self.path.is_absolute() else self.root / self.path
        self.payload: dict[str, Any] = json.loads(resolved.read_text(encoding='utf-8'))
        self.nodes = tuple(
            DocumentationAuthorityNode.from_dict(item)
            for item in self.payload.get('nodes', [])
            if isinstance(item, dict)
        )
        self.closure_contracts = tuple(
            dict(item) for item in self.payload.get('closure_contracts', []) if isinstance(item, dict)
        )

    def by_node_id(self) -> dict[str, DocumentationAuthorityNode]:
        return {item.node_id: item for item in self.nodes}

    def nodes_for_subject(self, subject: str) -> tuple[DocumentationAuthorityNode, ...]:
        return tuple(item for item in self.nodes if item.subject == subject)

    def current_authorities(self, subject: str) -> tuple[DocumentationAuthorityNode, ...]:
        return tuple(
            item
            for item in self.nodes_for_subject(subject)
            if item.authority_kind == 'current-active' and item.lifecycle == 'active'
        )

    def validate_paths(self) -> list[str]:
        return sorted(
            item.path for item in self.nodes if item.path and not (self.root / item.path).exists()
        )


class DerivedMetadataProjection:
    """Derive mutable summaries from live collections instead of hard-coded counters."""

    SUMMARY_KEYS = (
        'documents_total',
        'source_of_truth_total',
        'machine_readable_source_total',
        'derived_total',
        'generated_runtime_total',
        'historical_total',
        'deprecated_total',
        'critical_sources_total',
        'markdown_json_pairs_total',
        'documents_with_required_tests_total',
    )

    @classmethod
    def source_registry_summary(cls, payload: dict[str, Any]) -> dict[str, int]:
        docs = [item for item in payload.get('documents', []) if isinstance(item, dict)]
        classification = lambda value: sum(1 for item in docs if item.get('classification') == value)
        return {
            'documents_total': len(docs),
            'source_of_truth_total': classification('source-of-truth'),
            'machine_readable_source_total': classification('machine-readable-source'),
            'derived_total': classification('derived'),
            'generated_runtime_total': classification('generated-runtime'),
            'historical_total': classification('historical'),
            'deprecated_total': classification('deprecated'),
            'critical_sources_total': sum(1 for item in docs if item.get('criticality') in {'P0', 'P1'}),
            'markdown_json_pairs_total': sum(
                len(item.get('machine_readable_counterparts', []))
                for item in docs
                if str(item.get('path', '')).lower().endswith('.md')
            ),
            'documents_with_required_tests_total': sum(1 for item in docs if item.get('required_tests')),
        }

    @classmethod
    def source_registry_mismatches(cls, payload: dict[str, Any]) -> dict[str, dict[str, int | None]]:
        projected = cls.source_registry_summary(payload)
        stored = payload.get('summary', {}) if isinstance(payload.get('summary'), dict) else {}
        mismatches: dict[str, dict[str, int | None]] = {}
        for key, expected in projected.items():
            current = stored.get(key)
            if current != expected:
                mismatches[key] = {'expected': expected, 'current': current}
        return mismatches


class DocumentationDriftLedger:
    """Source-controlled ledger for cross-authority documentation drift."""

    def __init__(self, root: Path, path: str | Path = DEFAULT_DOCUMENTATION_DRIFT_LEDGER) -> None:
        self.root = Path(root).resolve()
        self.path = Path(path)
        resolved = self.path if self.path.is_absolute() else self.root / self.path
        self.payload: dict[str, Any] = json.loads(resolved.read_text(encoding='utf-8'))
        self.findings = tuple(dict(item) for item in self.payload.get('findings', []) if isinstance(item, dict))

    def open_findings(self) -> tuple[dict[str, Any], ...]:
        return tuple(item for item in self.findings if str(item.get('resolution_status', '')).lower() not in {'resolved', 'closed', 'accepted'})

    def open_blocking_findings(self) -> tuple[dict[str, Any], ...]:
        return tuple(item for item in self.open_findings() if str(item.get('severity', '')).upper() in {'P0', 'P1'})
