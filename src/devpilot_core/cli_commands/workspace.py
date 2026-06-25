from __future__ import annotations

from pathlib import Path

from devpilot_core.application import ApplicationService
from devpilot_core.cli_models import CommandResult
from devpilot_core.workspace import WorkspaceManager


def handle_workspace_init(
    root: Path,
    *,
    execute: bool = False,
    project_id: str | None = None,
    project_name: str | None = None,
    project_type: str | None = None,
) -> CommandResult:
    """Build the result for ``workspace init`` without rendering CLI output.

    POST-H-006-C moves the workspace initialization command logic out of
    ``cli.py`` while keeping the public parser, flags, event emission and
    persistence behavior unchanged in the CLI wrapper. The command remains
    dry-run by default; writes only happen when the existing ``--execute`` flag
    is passed by the caller.
    """

    manager = WorkspaceManager(root)
    return manager.init_workspace(
        execute=execute,
        project_id=project_id or "devpilot-local",
        project_name=project_name or "DevPilot Local",
        project_type=project_type or "agent-assisted-sdlc",
    )


def handle_workspace_status(root: Path) -> CommandResult:
    """Build the result for ``workspace status`` without rendering CLI output."""

    return ApplicationService(root).workspace_status()
