from __future__ import annotations

from pathlib import Path

from devpilot_core.application import ApplicationService
from devpilot_core.cli_models import CommandResult
from devpilot_core.onboarding import OnboardingReadinessPreviewOptions, OnboardingReadinessPreviewer
from devpilot_core.workspace import (
    DEFAULT_WORKSPACE_ISOLATION_REPORT_JSON,
    DEFAULT_WORKSPACE_ISOLATION_REPORT_MD,
    DEFAULT_WORKSPACE_REGISTRY_V2_SCHEMA,
    MultiworkspaceRegistry,
    MultiworkspaceRegistryV2,
    ProjectBootstrapOptions,
    ProjectBootstrapPlanner,
    WorkspaceIsolationOptions,
    WorkspaceIsolationValidator,
    WorkspaceManager,
    WorkspaceRegisterOptions,
    WorkspaceRegistryOptions,
    WorkspaceRegistryV2Options,
    WorkspaceSelectOptions,
)


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


def handle_workspace_register(
    root: Path,
    *,
    path: str,
    workspace_id: str | None = None,
    name: str | None = None,
    registry_path: str = ".devpilot/workspaces/workspace_registry.json",
) -> CommandResult:
    """Build the result for ``workspace register`` without CLI rendering.

    POST-H-030-D keeps the public CLI wrapper in ``cli.py`` but moves the
    registry mutation planning/execution call into the workspace-owned handler
    module. The underlying registry service preserves its existing PathGuard,
    source isolation and explicit local workspace constraints.
    """

    return MultiworkspaceRegistry(root, options=WorkspaceRegistryOptions(registry_path=registry_path)).register(
        WorkspaceRegisterOptions(path=path, workspace_id=workspace_id, name=name, registry_path=registry_path)
    )


def handle_workspace_list(
    root: Path,
    *,
    registry_path: str = ".devpilot/workspaces/workspace_registry.json",
) -> CommandResult:
    """Build the result for ``workspace list`` without CLI rendering."""

    return MultiworkspaceRegistry(root, options=WorkspaceRegistryOptions(registry_path=registry_path)).list()


def handle_workspace_select(
    root: Path,
    *,
    workspace_id: str,
    registry_path: str = ".devpilot/workspaces/workspace_registry.json",
) -> CommandResult:
    """Build the result for ``workspace select`` without CLI rendering."""

    return MultiworkspaceRegistry(root, options=WorkspaceRegistryOptions(registry_path=registry_path)).select(
        WorkspaceSelectOptions(workspace_id=workspace_id, registry_path=registry_path)
    )


def handle_workspace_registry_validate(
    root: Path,
    *,
    registry_path: str = ".devpilot/workspaces/workspace_registry.json",
    schema_path: str = "docs/schemas/multiworkspace_registry.schema.json",
    registry_version: str = "v1",
) -> CommandResult:
    """Build the result for ``workspace registry-validate``.

    The handler keeps the existing v1/v2 semantics: v2 migrates the v1 registry
    in memory only, while v1 validates the source registry with the historical
    contract. No runtime router or dynamic handler loading is introduced.
    """

    normalized_version = registry_version.strip().lower()
    if normalized_version == "v2":
        effective_schema_path = DEFAULT_WORKSPACE_REGISTRY_V2_SCHEMA if schema_path == "docs/schemas/multiworkspace_registry.schema.json" else schema_path
        return MultiworkspaceRegistryV2(
            root,
            options=WorkspaceRegistryV2Options(registry_path=registry_path, schema_path=effective_schema_path),
        ).validate()
    return MultiworkspaceRegistry(root, options=WorkspaceRegistryOptions(registry_path=registry_path, schema_path=schema_path)).validate()


def handle_workspace_isolation_check(
    root: Path,
    *,
    registry_path: str = ".devpilot/workspaces/workspace_registry.json",
    write_report: bool = False,
    output_json: str | Path = DEFAULT_WORKSPACE_ISOLATION_REPORT_JSON,
    output_markdown: str | Path = DEFAULT_WORKSPACE_ISOLATION_REPORT_MD,
) -> CommandResult:
    """Build the result for ``workspace isolation-check`` in read-only mode."""

    return WorkspaceIsolationValidator(
        root,
        options=WorkspaceIsolationOptions(
            registry_path=registry_path,
            write_report=write_report,
            output_json=output_json,
            output_markdown=output_markdown,
        ),
    ).run()
