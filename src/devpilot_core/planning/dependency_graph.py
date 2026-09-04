from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush

from .models import PlanningState


@dataclass(frozen=True)
class PlanningDependencyGraphReport:
    ok: bool
    topological_order: tuple[str, ...]
    duplicate_ids: tuple[str, ...]
    orphan_dependency_ids: tuple[str, ...]
    self_dependency_ids: tuple[str, ...]
    cycle_nodes: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "topological_order": list(self.topological_order),
            "duplicate_ids": list(self.duplicate_ids),
            "orphan_dependency_ids": list(self.orphan_dependency_ids),
            "self_dependency_ids": list(self.self_dependency_ids),
            "cycle_nodes": list(self.cycle_nodes),
        }


class PlanningDependencyGraphService:
    """Deterministic, side-effect-free graph validation for planning dependencies."""

    def validate(self, state: PlanningState) -> PlanningDependencyGraphReport:
        ids = list(state.entity_ids)
        duplicate_ids = tuple(sorted({item for item in ids if ids.count(item) > 1}))
        node_set = set(ids)
        orphan: list[str] = []
        self_edges: list[str] = []
        adjacency = {node: set() for node in sorted(node_set)}
        indegree = {node: 0 for node in sorted(node_set)}

        for dep in sorted(state.dependencies, key=lambda x: x.id):
            if dep.predecessor_id not in node_set or dep.successor_id not in node_set:
                orphan.append(dep.id)
                continue
            if dep.predecessor_id == dep.successor_id:
                self_edges.append(dep.id)
                continue
            if dep.successor_id not in adjacency[dep.predecessor_id]:
                adjacency[dep.predecessor_id].add(dep.successor_id)
                indegree[dep.successor_id] += 1

        heap: list[str] = []
        for node, degree in indegree.items():
            if degree == 0:
                heappush(heap, node)
        order: list[str] = []
        while heap:
            node = heappop(heap)
            order.append(node)
            for target in sorted(adjacency[node]):
                indegree[target] -= 1
                if indegree[target] == 0:
                    heappush(heap, target)
        cycle_nodes = tuple(sorted(node for node, degree in indegree.items() if degree > 0))
        ok = not duplicate_ids and not orphan and not self_edges and not cycle_nodes
        return PlanningDependencyGraphReport(
            ok=ok,
            topological_order=tuple(order),
            duplicate_ids=duplicate_ids,
            orphan_dependency_ids=tuple(sorted(orphan)),
            self_dependency_ids=tuple(sorted(self_edges)),
            cycle_nodes=cycle_nodes,
        )
