"""MP132 R01-08: side-effect-free successor proposal and selective change impact.

This is a *planning* boundary. Existing FROZEN artifacts and dependency records
are never written or transitioned here. A separate governed approval/apply is
required to publish the proposed successor and persist revalidation states.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Mapping, Sequence

from devpilot_core.application.artifact_lifecycle_service import ArtifactLifecycleService

_SHA = re.compile(r"^[0-9a-f]{64}$")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
_ALLOWED_KINDS = {"requirement", "adr", "story", "test", "api", "security", "release", "other"}


@dataclass(frozen=True)
class DependencyNode:
    node_id: str
    kind: str
    relative_path: str


@dataclass(frozen=True)
class DependencyEdge:
    upstream_id: str
    dependent_id: str
    topics: tuple[str, ...]


def _path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/") or ":" in value:
        raise ValueError("UNSAFE_RELATIVE_PATH")
    p = PurePosixPath(value)
    if any(part in ("", ".", "..") for part in value.split("/")) or str(p) != value:
        raise ValueError("UNSAFE_RELATIVE_PATH")
    if any(part.lower() == ".git" for part in p.parts):
        raise ValueError("UNSAFE_RELATIVE_PATH")
    return value


def _identity(value: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError("INVALID_ARTIFACT_OR_NODE_ID")
    return value


def _topics(items: Sequence[str]) -> frozenset[str]:
    if isinstance(items, (str, bytes)) or not items:
        raise ValueError("EMPTY_OR_INVALID_TOPICS")
    valid = frozenset(items)
    if not all(isinstance(x, str) and re.fullmatch(r"[a-z][a-z0-9_.-]{1,63}", x) for x in valid):
        raise ValueError("INVALID_TOPICS")
    return valid


class FrozenSuccessorPlanner:
    """Produce an immutable successor *candidate* and exact impact recommendations."""

    def plan(
        self,
        *,
        original_record: Mapping[str, object],
        original_content: str,
        successor_content: str,
        successor_id: str,
        successor_path: str,
        change_kind: str,
        change_topics: Sequence[str],
        reason: str,
        nodes: Sequence[DependencyNode],
        edges: Sequence[DependencyEdge],
        semantic_review_reference: str | None = None,
    ) -> dict:
        if original_record.get("state") != "FROZEN":
            raise ValueError("SOURCE_NOT_FROZEN")
        source_id = _identity(original_record.get("artifact_id"))
        source_path = _path(original_record.get("relative_path"))
        declared = original_record.get("content_hash")
        if not isinstance(declared, str) or not _SHA.fullmatch(declared):
            raise ValueError("INVALID_SOURCE_HASH")
        if not isinstance(original_content, str) or not isinstance(successor_content, str):
            raise ValueError("INVALID_CONTENT")
        actual = ArtifactLifecycleService.hash_normalized(original_content)
        if actual != declared:
            raise ValueError("FROZEN_SOURCE_DRIFT")
        succ_id = _identity(successor_id)
        succ_path = _path(successor_path)
        if succ_id == source_id or succ_path == source_path:
            raise ValueError("SUCCESSOR_MUST_HAVE_NEW_ID_AND_PATH")
        if not isinstance(reason, str) or len(reason.strip()) < 10:
            raise ValueError("CHANGE_REASON_REQUIRED")
        if change_kind not in ("COSMETIC", "SEMANTIC"):
            raise ValueError("UNKNOWN_CHANGE_KIND")
        tags = _topics(change_topics)
        if change_kind == "COSMETIC" and not (semantic_review_reference and len(semantic_review_reference.strip()) >= 8):
            raise ValueError("COSMETIC_EQUIVALENCE_EVIDENCE_REQUIRED")
        if successor_content == original_content:
            raise ValueError("EMPTY_SUCCESSOR_DIFF")
        if len(original_content.encode()) > 1048576 or len(successor_content.encode()) > 1048576:
            raise ValueError("CONTENT_SIZE_LIMIT")
        version = original_record.get("provenance", {}).get("artifact_version") if isinstance(original_record.get("provenance"), dict) else None
        if type(version) is not int or version < 1:
            raise ValueError("SOURCE_VERSION_UNVERIFIED")
        node_index: dict[str, DependencyNode] = {}
        for node in nodes:
            if not isinstance(node, DependencyNode) or node.node_id in node_index:
                raise ValueError("DUPLICATE_OR_INVALID_NODE")
            _identity(node.node_id)
            _path(node.relative_path)
            if node.kind not in _ALLOWED_KINDS:
                raise ValueError("INVALID_NODE_KIND")
            node_index[node.node_id] = node
        if source_id not in node_index or node_index[source_id].relative_path != source_path:
            raise ValueError("SOURCE_NODE_MISSING_OR_MISMATCHED")
        if succ_id in node_index or any(x.relative_path == succ_path for x in nodes):
            raise ValueError("SUCCESSOR_PATH_OR_ID_COLLISION")
        adjacency: dict[str, list[DependencyEdge]] = {x: [] for x in node_index}
        duplicates: set[tuple[str, str]] = set()
        for edge in edges:
            if not isinstance(edge, DependencyEdge) or edge.upstream_id not in node_index or edge.dependent_id not in node_index:
                raise ValueError("UNKNOWN_DEPENDENCY_EDGE")
            k = (edge.upstream_id, edge.dependent_id)
            if edge.upstream_id == edge.dependent_id or k in duplicates:
                raise ValueError("SELF_OR_DUPLICATE_EDGE")
            duplicates.add(k)
            _topics(edge.topics)
            adjacency[edge.upstream_id].append(edge)
        # A cycle is an invalid authority graph, even if the BFS below terminates.
        visiting, visited = set(), set()
        def visit(node_id: str) -> None:
            if node_id in visiting:
                raise ValueError("DEPENDENCY_CYCLE")
            if node_id in visited:
                return
            visiting.add(node_id)
            for edge in adjacency[node_id]:
                visit(edge.dependent_id)
            visiting.remove(node_id)
            visited.add(node_id)
        for node_id in node_index:
            visit(node_id)

        affected: dict[str, dict] = {}
        if change_kind == "SEMANTIC":
            frontier = [(source_id, tags, (source_id,))]
            while frontier:
                parent, active, lineage = frontier.pop(0)
                for edge in sorted(adjacency[parent], key=lambda e: e.dependent_id):
                    common = active & frozenset(edge.topics)
                    if not common:
                        continue
                    target = edge.dependent_id
                    evidence = {"via": list(lineage + (target,)), "topics": sorted(common)}
                    old = affected.get(target)
                    if old is None:
                        affected[target] = evidence
                        frontier.append((target, common, lineage + (target,)))
                    elif not common.issubset(set(old["topics"])):
                        merged = set(old["topics"]) | common
                        old["topics"] = sorted(merged)
                        frontier.append((target, common, lineage + (target,)))
        impacts = []
        for node_id, node in sorted(node_index.items()):
            if node_id == source_id:
                continue
            evidence = affected.get(node_id)
            if evidence is None:
                why = ("Cambio cosmético revisado: " + semantic_review_reference) if change_kind == "COSMETIC" else "Sin ruta de dependencia compatible con los temas modificados"
                impacts.append({"node_id": node_id, "kind": node.kind, "path": node.relative_path,
                                "decision": "NO_IMPACT_WITH_REASON", "reason": why})
            else:
                impacts.append({"node_id": node_id, "kind": node.kind, "path": node.relative_path,
                                "decision": "STALE_REVALIDATION_REQUIRED", "reason": "Dependencia declarada afectada",
                                "via": evidence["via"], "topics": evidence["topics"]})
        old_lines = original_content.replace("\r\n", "\n").splitlines()
        new_lines = successor_content.replace("\r\n", "\n").splitlines()
        summary = {"added_lines": 0, "removed_lines": 0}
        for item in difflib.ndiff(old_lines, new_lines):
            if item.startswith("+ "):
                summary["added_lines"] += 1
            elif item.startswith("- "):
                summary["removed_lines"] += 1
        successor_hash = ArtifactLifecycleService.hash_normalized(successor_content)
        successor = {"artifact_id": succ_id, "relative_path": succ_path, "state": "DRAFT",
                     "artifact_version": version + 1, "content_hash": successor_hash,
                     "supersedes": {"artifact_id": source_id, "version": version, "content_hash": declared},
                     "approval_required": True, "publication_authorized": False}
        canonical = {"source": {"artifact_id": source_id, "relative_path": source_path,
                                "state": "FROZEN", "content_hash": declared},
                     "successor": successor, "change": {"kind": change_kind, "topics": sorted(tags),
                     "reason": reason.strip(), "diff_summary": summary,
                     "semantic_review_reference": semantic_review_reference}, "impacts": impacts}
        plan_id = hashlib.sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        return {"schema": "devpilot.mp132.r01.08.successor_plan.v1", "plan_id": plan_id,
                "status": "REVIEW_REQUIRED", **canonical, "source_mutations_performed": False,
                "network_used": False, "full_regression_required": False}
