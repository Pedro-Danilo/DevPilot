from __future__ import annotations

from .git_adapter import (
    GitAdapter,
    GitBranchInfo,
    GitCommandResult,
    GitCommitInfo,
    GitDiffFile,
    GitStatusSnapshot,
    GitTagInfo,
)
from .inventory import RepoInventory, RepoInventoryConfig, RepoInventoryItem
from .dependency_graph import DependencyGraphBuilder
from .analyzer import RepoAnalyzer, RepoAnalyzerConfig
from .architecture_drift import ArchitectureDriftConfig, ArchitectureDriftDetector
from .quality_gate import RepoQualityGate, RepoQualityGateConfig
from .engineering_gate import RepoEngineeringGate, RepoEngineeringGateConfig
from .models import (
    DependencyGraphEdge,
    DependencyGraphNode,
    DependencyGraphResult,
    RepoHealthSummary,
    RepoHotspot,
    RepoRiskSignal,
    ArchitectureComponentRecord,
    ArchitectureDriftMatrixRow,
)

__all__ = [
    "GitAdapter",
    "GitBranchInfo",
    "GitCommandResult",
    "GitCommitInfo",
    "GitDiffFile",
    "GitStatusSnapshot",
    "GitTagInfo",
    "DependencyGraphBuilder",
    "DependencyGraphEdge",
    "DependencyGraphNode",
    "DependencyGraphResult",
    "RepoAnalyzer",
    "RepoAnalyzerConfig",
    "ArchitectureDriftConfig",
    "ArchitectureDriftDetector",
    "RepoQualityGate",
    "RepoQualityGateConfig",
    "RepoEngineeringGate",
    "RepoEngineeringGateConfig",
    "RepoHealthSummary",
    "RepoHotspot",
    "RepoRiskSignal",
    "ArchitectureComponentRecord",
    "ArchitectureDriftMatrixRow",
    "RepoInventory",
    "RepoInventoryConfig",
    "RepoInventoryItem",
]
