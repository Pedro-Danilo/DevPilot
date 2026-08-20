from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from devpilot_core.cli_models import CommandResult
from devpilot_core.workspace.environment_discovery import DEFAULT_TIMEOUT_SECONDS
from devpilot_core.workspace.project_entry_dry_run import ProjectEntryDryRunService


class ProjectEntryDryRunApplicationService:
    """Application boundary for review-only Create/Open/Import dry-runs."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()

    def dry_run(self, *, intake: Mapping[str, Any], timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> CommandResult:
        return ProjectEntryDryRunService(self.root, timeout_seconds=timeout_seconds).dry_run(intake=intake)

    def revalidate(self, *, intake: Mapping[str, Any], expected_plan_hash: str, expected_preimage_hash: str, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> CommandResult:
        return ProjectEntryDryRunService(self.root, timeout_seconds=timeout_seconds).revalidate(intake=intake, expected_plan_hash=expected_plan_hash, expected_preimage_hash=expected_preimage_hash)
