from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.runtime_state.inventory import RuntimeStateInventoryBuilder, RuntimeStateInventoryOptions, render_runtime_state_inventory_markdown


def runtime_state_inventory(root: Path, *, write_report: bool = False) -> CommandResult:
    return RuntimeStateInventoryBuilder(root, RuntimeStateInventoryOptions(write_report=write_report)).run()


__all__ = ["RuntimeStateInventoryBuilder", "RuntimeStateInventoryOptions", "render_runtime_state_inventory_markdown", "runtime_state_inventory"]
