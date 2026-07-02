from __future__ import annotations

from pathlib import Path

from devpilot_core.application import ApplicationService
from devpilot_core.cli_models import CommandResult
from devpilot_core.onboarding import OnboardingReadinessPreviewOptions, OnboardingReadinessPreviewer
from devpilot_core.workspace import ProjectBootstrapOptions, ProjectBootstrapPlanner, WorkspaceManager


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


def handle_workspace_bootstrap(
    root: Path,
    *,
    project_id: str,
    project_name: str,
    project_type: str = "agent-assisted-sdlc",
    target_root: str | None = None,
    execute: bool = False,
    write_report: bool = False,
    output_json: str = "outputs/reports/project_bootstrap_report.json",
    output_markdown: str = "outputs/reports/project_bootstrap_report.md",
) -> CommandResult:
    """Build or execute the POST-H-024-C project bootstrap workflow.

    The handler remains policy-bounded and dry-run-first. Execute mode writes
    only the planned starter files under the configured target workspace and
    refuses existing files by default.
    """

    return ProjectBootstrapPlanner(root).run(
        ProjectBootstrapOptions(
            project_id=project_id,
            project_name=project_name,
            project_type=project_type,
            target_root=target_root,
            execute=execute,
            write_report=write_report,
            output_json=output_json,
            output_markdown=output_markdown,
        )
    )


def handle_workspace_readiness_preview(
    root: Path,
    *,
    target_root: str = "outputs/bootstrap_workspaces/ventas-micro-local",
    project_id: str | None = None,
    project_name: str | None = None,
    write_report: bool = False,
    output_json: str = "outputs/reports/onboarding_readiness_preview_report.json",
    output_markdown: str = "outputs/reports/onboarding_readiness_preview_report.md",
) -> CommandResult:
    """Build the POST-H-024-D onboarding validation/readiness preview result.

    The handler is read-only and local-first. It reports missing artifacts,
    checklist, StandardsRegistry and MIASI items as pending readiness work rather
    than overclaiming project readiness.
    """

    return OnboardingReadinessPreviewer(root).run(
        OnboardingReadinessPreviewOptions(
            target_root=target_root,
            project_id=project_id,
            project_name=project_name,
            write_report=write_report,
            output_json=output_json,
            output_markdown=output_markdown,
        )
    )
