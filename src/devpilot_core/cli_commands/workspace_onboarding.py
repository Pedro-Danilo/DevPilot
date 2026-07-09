from __future__ import annotations

from pathlib import Path

from devpilot_core.application import ApplicationService
from devpilot_core.cli_models import CommandResult
from devpilot_core.portfolio import WorkspacePortfolioHardeningGate, WorkspacePortfolioHardeningGateOptions


def handle_portfolio_status(
    root: Path,
    *,
    registry_path: str = ".devpilot/workspaces/workspace_registry.json",
) -> CommandResult:
    """Build the result for ``portfolio status`` through ApplicationService.

    POST-H-030-D extracts the portfolio/workspace result-building boundary from
    ``cli.py`` without changing the public command, JSON envelope, exit codes or
    local-first ApplicationService contract introduced in POST-H-016-D.
    """

    return ApplicationService(root).portfolio_status(registry_path=registry_path)


def handle_portfolio_hardening_gate(
    root: Path,
    *,
    registry_path: str = ".devpilot/workspaces/workspace_registry.json",
    write_report: bool = False,
) -> CommandResult:
    """Build the result for ``portfolio hardening-gate``.

    The underlying gate remains read-only over workspace source evidence and
    writes only optional reports under governed outputs paths when explicitly
    requested by the CLI wrapper.
    """

    return WorkspacePortfolioHardeningGate(
        root,
        WorkspacePortfolioHardeningGateOptions(registry_path=registry_path, write_report=write_report),
    ).run()
