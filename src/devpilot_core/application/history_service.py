from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.store import LocalStore


class HistoryApplicationService:
    """Application-facing local history facade."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def list_runs(self, *, limit: int = 10) -> CommandResult:
        return LocalStore(self.root).list_runs(limit=limit)
