from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.portfolio import PortfolioStatusBuilder


class PortfolioApplicationService:
    """Application boundary for read-only workspace portfolio operations."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()

    def status(self, *, registry_path: str = ".devpilot/workspaces/workspace_registry.json") -> CommandResult:
        """Build hardened portfolio status without workspace selection or state mutation."""

        return PortfolioStatusBuilder(self.root, registry_path=registry_path).build()
