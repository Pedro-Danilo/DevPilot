from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from devpilot_core.cli_models import CommandResult
from devpilot_core.policy import configured_external_workspace_roots
from devpilot_core.workspace.environment_discovery import DEFAULT_TIMEOUT_SECONDS, EnvironmentDiscoveryService


class ProjectEntryPlanningApplicationService:
    """Application-facing read-only facade for GSDLC-03-B.

    This service is intentionally planning-only. It exposes environment
    discovery and deterministic BootstrapPlan generation to API/UI callers
    without enabling project writes, installers, Git mutation or network.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()

    def environment_discovery(self, *, intake: Mapping[str, Any], timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> CommandResult:
        service = EnvironmentDiscoveryService(
            self.root,
            allowed_roots=configured_external_workspace_roots(),
            timeout_seconds=timeout_seconds,
        )
        return service.discover({"intake": dict(intake)})

    def bootstrap_plan(self, *, intake: Mapping[str, Any], timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> CommandResult:
        service = EnvironmentDiscoveryService(
            self.root,
            allowed_roots=configured_external_workspace_roots(),
            timeout_seconds=timeout_seconds,
        )
        return service.build_bootstrap_plan({"intake": dict(intake)})
