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


@dataclass(frozen=True)
class RepoRiskSignal:
    """One heuristic repository risk signal emitted by RepoAnalyzer v2."""

    kind: str
    path: str
    severity: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "kind": self.kind,
            "path": self.path,
            "severity": self.severity,
            "message": self.message,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data


@dataclass(frozen=True)
class RepoHotspot:
    """One dependency hotspot derived from static fan-in/fan-out metrics."""

    module: str
    path: str
    metric: str
    score: int

    def to_dict(self) -> dict[str, Any]:
        return {"module": self.module, "path": self.path, "metric": self.metric, "score": self.score}


@dataclass(frozen=True)
class RepoHealthSummary:
    """Serializable repository health summary for RepoAnalyzer v2.

    The score is deliberately heuristic. It is an engineering signal for local
    review and future quality gates, not a certification of production quality.
    """

    target: str
    score: int
    rating: str
    sections: dict[str, Any]
    risk_counts: dict[str, int]
    dependency_summary: dict[str, Any]
    git_summary: dict[str, Any]
    hotspots_total: int

    @classmethod
    def from_inputs(
        cls,
        *,
        target: str,
        sections: dict[str, Any],
        risk_signals: list[RepoRiskSignal],
        dependency_summary: dict[str, Any],
        git_summary: dict[str, Any],
        hotspots: list[RepoHotspot],
    ) -> "RepoHealthSummary":
        risk_counts = {"block": 0, "fail": 0, "warning": 0, "info": 0}
        for signal in risk_signals:
            risk_counts[signal.severity] = risk_counts.get(signal.severity, 0) + 1
        score = 100
        score -= min(risk_counts.get("block", 0) * 25, 50)
        score -= min(risk_counts.get("fail", 0) * 15, 40)
        score -= min(risk_counts.get("warning", 0) * 2, 30)
        if dependency_summary.get("syntax_error_files_total", 0):
            score -= 10
        git_counts = git_summary.get("counts") if isinstance(git_summary.get("counts"), dict) else {}
        if git_counts and git_counts.get("entries_total", 0):
            score -= min(int(git_counts.get("entries_total", 0)), 10)
        score = max(0, min(100, score))
        rating = "healthy"
        if score < 90:
            rating = "review"
        if score < 70:
            rating = "risk"
        if risk_counts.get("block", 0):
            rating = "blocked-review-required"
        return cls(
            target=target,
            score=score,
            rating=rating,
            sections=sections,
            risk_counts=risk_counts,
            dependency_summary=dependency_summary,
            git_summary=git_summary,
            hotspots_total=len(hotspots),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "health_score": self.score,
            "rating": self.rating,
            "risk_counts": self.risk_counts,
            "sections_summary": self.sections.get("summary", {}),
            "dependency": {
                "nodes_total": self.dependency_summary.get("nodes_total", 0),
                "edges_total": self.dependency_summary.get("edges_total", 0),
                "external_imports_total": self.dependency_summary.get("external_imports_total", 0),
                "syntax_error_files_total": self.dependency_summary.get("syntax_error_files_total", 0),
            },
            "git": {
                "is_git_repo": self.git_summary.get("is_git_repo"),
                "branch": self.git_summary.get("branch"),
                "counts": self.git_summary.get("counts", {}),
                "git_available": self.git_summary.get("git_available"),
            },
            "hotspots_total": self.hotspots_total,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "preliminary": True,
        }


@dataclass(frozen=True)
class ArchitectureComponentRecord:
    """One architecture component extracted from controlled Markdown docs."""

    name: str
    normalized_name: str
    status: str
    source_doc: str
    source_type: str
    documented_path: str | None = None
    aliases: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "normalized_name": self.normalized_name,
            "status": self.status,
            "source_doc": self.source_doc,
            "source_type": self.source_type,
            "aliases": sorted(set(self.aliases)),
        }
        if self.documented_path is not None:
            data["documented_path"] = self.documented_path
        return data


@dataclass(frozen=True)
class ArchitectureDriftMatrixRow:
    """One documented-component/code-module matching row."""

    documented_component: str | None
    documented_status: str | None
    source_doc: str | None
    documented_path: str | None
    code_module: str | None
    code_path: str | None
    match_type: str
    confidence: float
    drift_type: str
    severity: str
    rationale: str

    def severity_order(self) -> int:
        return {"block": 0, "fail": 1, "warning": 2, "info": 3}.get(self.severity, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "documented_component": self.documented_component,
            "documented_status": self.documented_status,
            "source_doc": self.source_doc,
            "documented_path": self.documented_path,
            "code_module": self.code_module,
            "code_path": self.code_path,
            "match_type": self.match_type,
            "confidence": self.confidence,
            "drift_type": self.drift_type,
            "severity": self.severity,
            "rationale": self.rationale,
        }
