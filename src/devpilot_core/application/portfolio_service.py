from __future__ import annotations

import os
from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.portfolio import PortfolioStatusBuilder

from .ui_workspace_context import UI_WORKSPACE_REGISTRY_ENV, UiWorkspaceContextResolver


class PortfolioApplicationService:
    """Application boundary for read-only workspace portfolio operations."""

    def __init__(self, root: Path, *, context_resolver: UiWorkspaceContextResolver | None = None) -> None:
        self.root = Path(root).resolve()
        self.context_resolver = context_resolver or UiWorkspaceContextResolver(self.root)

    def status(self, *, registry_path: str | None = None) -> CommandResult:
        """Build hardened portfolio status without workspace selection or state mutation.

        An explicitly configured UI registry is used only when the caller does
        not supply a registry path. The registry remains validated by PathGuard,
        schema and isolation rules before any workspace data is projected.
        """

        resolved_registry = str(registry_path or "").strip()
        if not resolved_registry:
            resolved_registry = os.environ.get(UI_WORKSPACE_REGISTRY_ENV, "").strip()
        if not resolved_registry:
            resolved_registry = ".devpilot/workspaces/workspace_registry.json"
        result = PortfolioStatusBuilder(self.root, registry_path=resolved_registry).build()
        if isinstance(result.data, dict):
            result.data.setdefault("ui_workspace_context", self.context_resolver.resolve().summary())
        return result
