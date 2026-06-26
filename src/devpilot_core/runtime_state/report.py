from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.runtime_state.cleanup import RuntimeStateCleanupOptions, RuntimeStateCleanupPlanner, render_runtime_state_cleanup_plan_markdown
from devpilot_core.runtime_state.export import RuntimeStateExportOptions, RuntimeStateExporter, render_runtime_state_export_manifest_markdown
from devpilot_core.runtime_state.inventory import RuntimeStateInventoryBuilder, RuntimeStateInventoryOptions, render_runtime_state_inventory_markdown
from devpilot_core.runtime_state.hygiene import RuntimeStateHygieneGate, RuntimeStateHygieneOptions, render_runtime_state_hygiene_markdown


def runtime_state_inventory(root: Path, *, write_report: bool = False) -> CommandResult:
    return RuntimeStateInventoryBuilder(root, RuntimeStateInventoryOptions(write_report=write_report)).run()


def runtime_state_cleanup_plan(root: Path, *, write_report: bool = False) -> CommandResult:
    return RuntimeStateCleanupPlanner(root, RuntimeStateCleanupOptions(write_report=write_report)).run()


def runtime_state_hygiene(root: Path, *, write_report: bool = False):
    return RuntimeStateHygieneGate(root, RuntimeStateHygieneOptions(write_report=write_report)).run()


def runtime_state_export(root: Path, *, dry_run: bool = True, execute: bool = False, output: str | Path | None = None) -> CommandResult:
    return RuntimeStateExporter(root, RuntimeStateExportOptions(dry_run=dry_run, execute=execute, output=output)).run()


__all__ = [
    "RuntimeStateCleanupOptions",
    "RuntimeStateCleanupPlanner",
    "RuntimeStateExportOptions",
    "RuntimeStateExporter",
    "RuntimeStateHygieneGate",
    "RuntimeStateHygieneOptions",
    "runtime_state_hygiene",
    "render_runtime_state_hygiene_markdown",
    "RuntimeStateInventoryBuilder",
    "RuntimeStateInventoryOptions",
    "render_runtime_state_cleanup_plan_markdown",
    "render_runtime_state_export_manifest_markdown",
    "render_runtime_state_inventory_markdown",
    "runtime_state_cleanup_plan",
    "runtime_state_export",
    "runtime_state_inventory",
]
