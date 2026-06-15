from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.workspace import WorkspaceManager


class WorkspaceApplicationService:
    """Application-facing workspace facade.

    Provides UI/API-safe access to WorkspaceManager without exposing lower-level
    path handling. Writes remain explicit: init defaults to dry-run.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.manager = WorkspaceManager(self.root)

    def status(self) -> CommandResult:
        return self.manager.status()

    def init_plan(self, *, project_id: str | None = None, project_name: str | None = None, project_type: str | None = None) -> CommandResult:
        return self.manager.init_workspace(
            execute=False,
            project_id=project_id or "devpilot-local",
            project_name=project_name or "DevPilot Local",
            project_type=project_type or "agent-assisted-sdlc",
        )
