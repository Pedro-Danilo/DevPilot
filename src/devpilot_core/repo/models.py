from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DependencyGraphNode:
    """One Python module discovered without executing repository code."""

    module: str
    path: str
    package: str | None = None
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    external_imports: list[str] = field(default_factory=list)
    syntax_error: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "path": self.path,
            "package": self.package,
            "dependencies": sorted(set(self.dependencies)),
            "dependents": sorted(set(self.dependents)),
            "external_imports": sorted(set(self.external_imports)),
            "fan_out": len(set(self.dependencies)),
            "fan_in": len(set(self.dependents)),
            "syntax_error": self.syntax_error,
        }


@dataclass(frozen=True)
class DependencyGraphEdge:
    """Directed internal dependency edge: source module imports target module."""

    source: str
    target: str
    import_name: str
    import_type: str
    lineno: int | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "source": self.source,
            "target": self.target,
            "import_name": self.import_name,
            "import_type": self.import_type,
        }
        if self.lineno is not None:
            data["lineno"] = self.lineno
        return data


@dataclass(frozen=True)
class DependencyGraphResult:
    """Serializable dependency graph produced by the Python import analyzer."""

    root_package: str | None
    target: str
    nodes: list[DependencyGraphNode]
    edges: list[DependencyGraphEdge]
    external_imports: list[str]
    syntax_error_files: list[str]
    ignored_dirs: list[str]
    truncated: bool = False
    max_files: int | None = None

    def to_dict(self) -> dict[str, Any]:
        nodes = [node.to_dict() for node in self.nodes]
        edges = [edge.to_dict() for edge in self.edges]
        fan_in = sorted(nodes, key=lambda item: (-item["fan_in"], item["module"]))
        fan_out = sorted(nodes, key=lambda item: (-item["fan_out"], item["module"]))
        return {
            "summary": {
                "target": self.target,
                "root_package": self.root_package,
                "nodes_total": len(nodes),
                "edges_total": len(edges),
                "external_imports_total": len(set(self.external_imports)),
                "syntax_error_files_total": len(self.syntax_error_files),
                "ignored_dirs": sorted(set(self.ignored_dirs)),
                "truncated": self.truncated,
                "max_files": self.max_files,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "preliminary": True,
            },
            "nodes": nodes,
            "edges": edges,
            "external_imports": sorted(set(self.external_imports)),
            "syntax_error_files": sorted(set(self.syntax_error_files)),
            "metrics": {
                "top_fan_in": fan_in[:10],
                "top_fan_out": fan_out[:10],
            },
            "notes": [
                "FUNC-SPRINT-36 extracts Python imports with AST without executing analyzed code.",
                "Dynamic imports, runtime plugin loading and conditional imports may be incomplete.",
                "Edges represent detected internal imports, not guaranteed runtime call relationships.",
            ],
        }
