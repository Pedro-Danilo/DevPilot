from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.refactor import RefactorPlanner


class RefactorApplicationService:
    """Application-facing refactor facade.

    Sprint 65 exposes only plan-only refactor operations. Execution and sandboxed
    mutation flows remain outside the Web UI MVP until policy/approval gates are
    bound in later sprints.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def plan(self, *, target: str | Path = ".", goal: str = "", include_code_review: bool = True) -> CommandResult:
        return RefactorPlanner(self.root).plan(target=target, goal=goal, include_code_review=include_code_review)
