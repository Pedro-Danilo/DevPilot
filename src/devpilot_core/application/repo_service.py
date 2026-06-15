from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.repo import ArchitectureDriftDetector, DependencyGraphBuilder, GitAdapter, RepoAnalyzer, RepoEngineeringGate, RepoInventory, RepoQualityGate
from devpilot_core.repo.diff_report import GitDiffReportBuilder


class RepoApplicationService:
    """Application-facing read-only repository facade."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def git_status(self) -> CommandResult:
        return GitAdapter(self.root).status()

    def git_diff_report(self, *, max_files: int = 200) -> CommandResult:
        return GitDiffReportBuilder(self.root).build(max_files=max_files)

    def inventory(self) -> CommandResult:
        return RepoInventory(self.root).build()

    def dependency_graph(self, *, target: str | Path = "src/devpilot_core") -> CommandResult:
        return DependencyGraphBuilder(self.root).build(target=target)

    def analyze(self, *, target: str | Path = ".") -> CommandResult:
        return RepoAnalyzer(self.root).analyze(target=target)

    def architecture_drift(self) -> CommandResult:
        return ArchitectureDriftDetector(self.root).detect()

    def engineering_gate(self) -> CommandResult:
        return RepoEngineeringGate(self.root).run()

    def quality_gate(self) -> CommandResult:
        return RepoQualityGate(self.root).run()
