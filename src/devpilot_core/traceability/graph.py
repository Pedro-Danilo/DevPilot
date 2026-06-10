from __future__ import annotations

from collections import Counter
from typing import Any

from devpilot_core.traceability.models import TraceGraph


def summarize_trace_graph(graph: TraceGraph) -> dict[str, Any]:
    """Return a compact summary for a TraceGraph.

    FUNC-SPRINT-25 keeps this helper intentionally small. Coverage and gap
    rules are deferred to the future TraceabilityEngine sprint.
    """

    type_counts = Counter(entity.entity_type.value for entity in graph.entities)
    return {
        "entities_total": len(graph.entities),
        "unique_entities_total": len({entity.entity_id for entity in graph.entities}),
        "links_total": len(graph.links),
        "invalid_tokens_total": len(graph.invalid_tokens),
        "duplicate_entity_ids_total": len(graph.duplicate_entity_ids),
        "source_paths_total": len(graph.source_paths),
        "entity_type_counts": dict(sorted(type_counts.items())),
        "inferred_links": False,
        "preliminary": graph.preliminary,
    }
