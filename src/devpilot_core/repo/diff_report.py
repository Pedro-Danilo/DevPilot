from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.repo.git_adapter import GitAdapter


class GitDiffReportBuilder:
    """Build structured read-only Git diff reports.

    Purpose:
        Provide an explicit Sprint 35 boundary for diff-report generation so
        future repo-quality and patch-preflight sprints can depend on a stable
        component instead of calling GitAdapter internals directly.

    Functioning:
        Delegates to GitAdapter.diff_report(), which enforces read-only Git
        allowlisting and never applies patches, stages files or mutates Git.

    Integration:
        Used by the CLI command `git diff-report`.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def build(self, *, max_files: int = 200) -> CommandResult:
        return GitAdapter(self.root).diff_report(max_files=max_files)
