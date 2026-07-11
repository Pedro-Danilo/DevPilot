from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_registry.builders import StaticCliInventoryExtractor, StaticCliInventoryOptions
from devpilot_core.cli_registry.models import (
    CliCommandRegistry,
    CommandDescriptor,
    CommandGroupDescriptor,
    CommandRiskLevel,
    CommandSideEffect,
)

DECLARATIVE_DESCRIPTOR_SOURCE = "src/devpilot_core/cli_registry/registry.py"
POST_H_006_B_CREATED_BY = "POST-H-006-B"
POST_H_006_C_CREATED_BY = "POST-H-006-C"
POST_H_006_D_CREATED_BY = "POST-H-006-D"
POST_H_006_E_CREATED_BY = "POST-H-006-E"
POST_H_008_B_CREATED_BY = "POST-H-008-B"
POST_H_010_B_CREATED_BY = "POST-H-010-B"
POST_H_010_C_CREATED_BY = "POST-H-010-C"
POST_H_010_D_CREATED_BY = "POST-H-010-D"
POST_H_030_B_CREATED_BY = "POST-H-030-B"
POST_H_030_C_CREATED_BY = "POST-H-030-C"
POST_H_030_D_CREATED_BY = "POST-H-030-D"
POST_H_030_E_CREATED_BY = "POST-H-030-E"

# POST-H-007-E keeps this metadata static to avoid coupling CLI registry
# generation to ApplicationOperationCatalog imports. The runtime integration
# report validates these operation ids against the catalog.
APPLICATION_OPERATION_BY_COMMAND_ID: dict[str, str] = {
    "standards.status": "standards.status",
    "validate": "validation.gateway",
    "workspace.status": "workspace.status",
    "api.shell-gate": "api.shell_gate",
    "operator.dashboard": "operator.dashboard",
    "portfolio.status": "portfolio.status",
}

POST_H_006_B_INITIAL_GROUPS: tuple[str, ...] = (
    "workspace",
    "standards",
    "schema",
    "validate",
    "project-state",
    "test-contracts",
    "quality-gate",
    "evidence",
    "industrial-readiness",
    "release-candidate",
    "package",
)


@dataclass(frozen=True)
class DeclarativeGroupDescriptor:
    """Curated POST-H-006-B declaration for one low/medium-risk CLI group.

    This object is intentionally metadata-only. It does not import handlers, does
    not execute commands and does not load modules from arbitrary strings. The
    actual command surface still comes from the static parser inventory until
    POST-H-006-C migrates selected handlers with parity tests.
    """

    group_id: str
    domain: str
    owner_module: str
    recommended_tests: tuple[str, ...]
    application_service_required: bool = False
    rationale: str = "Initial governed CLI registry group."


@dataclass(frozen=True)
class DeclarativeCommandOverride:
    """Command-level safety override for the declarative registry overlay."""

    command_id: str
    risk_level: CommandRiskLevel | None = None
    side_effects: tuple[CommandSideEffect, ...] | None = None
    writes_files: bool | None = None
    dry_run_supported: bool | None = None
    policy_check_required: bool | None = None
    recommended_tests: tuple[str, ...] | None = None
    rationale: str = "Explicit POST-H-006-B command metadata."


@dataclass(frozen=True)
class MigratedHandlerDescriptor:
    """Explicit handler migration metadata.

    This is not a dynamic loader descriptor. It documents migrated, statically
    imported Python handlers while the public parser/dispatch remains in
    ``src/devpilot_core/cli.py`` for backward compatibility.
    """

    command_id: str
    owner_module: str
    handler: str
    wrapper: str
    recommended_tests: tuple[str, ...]
    rationale: str
    migrated_by: str = POST_H_006_C_CREATED_BY


MIGRATED_HANDLERS: dict[str, MigratedHandlerDescriptor] = {
    "workspace.init": MigratedHandlerDescriptor(
        command_id="workspace.init",
        owner_module="src/devpilot_core/cli_commands/workspace.py",
        handler="handle_workspace_init",
        wrapper="workspace_init_command",
        recommended_tests=(
            "python -m pytest tests/test_workspace_manager.py tests/test_post_h_006_c_handler_migration.py -q",
        ),
        rationale="Workspace init result-building logic migrated; cli.py preserves parser, flags, events, reports and persistence.",
    ),
    "workspace.status": MigratedHandlerDescriptor(
        command_id="workspace.status",
        owner_module="src/devpilot_core/cli_commands/workspace.py",
        handler="handle_workspace_status",
        wrapper="workspace_status_command",
        recommended_tests=(
            "python -m pytest tests/test_workspace_manager.py tests/test_post_h_006_c_handler_migration.py -q",
        ),
        rationale="Workspace status result-building logic migrated with CLI JSON parity tests.",
    ),
    "workspace.bootstrap": MigratedHandlerDescriptor(
        command_id="workspace.bootstrap",
        owner_module="src/devpilot_core/cli_commands/workspace.py",
        handler="handle_workspace_bootstrap",
        wrapper="workspace_bootstrap_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_024_project_bootstrap.py -q",
        ),
        rationale="POST-H-024-C moves project bootstrap result-building logic into cli_commands/workspace.py while cli.py preserves parser, events and persistence.",
    ),
    "workspace.readiness-preview": MigratedHandlerDescriptor(
        command_id="workspace.readiness-preview",
        owner_module="src/devpilot_core/cli_commands/workspace.py",
        handler="handle_workspace_readiness_preview",
        wrapper="workspace_readiness_preview_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_024_onboarding_readiness_preview.py -q",
        ),
        rationale="POST-H-024-D moves onboarding readiness preview result-building logic into cli_commands/workspace.py while cli.py preserves parser, events and persistence.",
    ),
    "workspace.register": MigratedHandlerDescriptor(
        command_id="workspace.register",
        owner_module="src/devpilot_core/cli_commands/workspace.py",
        handler="handle_workspace_register",
        wrapper="workspace_register_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_016_workspace_registry_v2.py tests/test_post_h_030_workspace_onboarding_command_extraction.py -q",
        ),
        rationale="POST-H-030-D moves workspace register result-building into cli_commands/workspace.py while cli.py preserves parser, optional reports, events, persistence and rendering.",
        migrated_by=POST_H_030_D_CREATED_BY,
    ),
    "workspace.list": MigratedHandlerDescriptor(
        command_id="workspace.list",
        owner_module="src/devpilot_core/cli_commands/workspace.py",
        handler="handle_workspace_list",
        wrapper="workspace_list_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_016_workspace_registry_v2.py tests/test_post_h_030_workspace_onboarding_command_extraction.py -q",
        ),
        rationale="POST-H-030-D moves workspace list result-building into cli_commands/workspace.py while preserving read-only registry inspection semantics.",
        migrated_by=POST_H_030_D_CREATED_BY,
    ),
    "workspace.select": MigratedHandlerDescriptor(
        command_id="workspace.select",
        owner_module="src/devpilot_core/cli_commands/workspace.py",
        handler="handle_workspace_select",
        wrapper="workspace_select_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_016_workspace_registry_v2.py tests/test_post_h_030_workspace_onboarding_command_extraction.py -q",
        ),
        rationale="POST-H-030-D moves workspace select result-building into cli_commands/workspace.py while preserving explicit CLI-only active workspace mutation semantics.",
        migrated_by=POST_H_030_D_CREATED_BY,
    ),
    "workspace.registry-validate": MigratedHandlerDescriptor(
        command_id="workspace.registry-validate",
        owner_module="src/devpilot_core/cli_commands/workspace.py",
        handler="handle_workspace_registry_validate",
        wrapper="workspace_registry_validate_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_016_workspace_registry_v2.py tests/test_post_h_030_workspace_onboarding_command_extraction.py -q",
        ),
        rationale="POST-H-030-D moves workspace registry validation result-building into cli_commands/workspace.py while preserving v1/v2 validation behavior.",
        migrated_by=POST_H_030_D_CREATED_BY,
    ),
    "workspace.isolation-check": MigratedHandlerDescriptor(
        command_id="workspace.isolation-check",
        owner_module="src/devpilot_core/cli_commands/workspace.py",
        handler="handle_workspace_isolation_check",
        wrapper="workspace_isolation_check_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_016_workspace_isolation_check.py tests/test_post_h_030_workspace_onboarding_command_extraction.py -q",
        ),
        rationale="POST-H-030-D moves workspace isolation-check result-building into cli_commands/workspace.py while preserving read-only isolation report semantics.",
        migrated_by=POST_H_030_D_CREATED_BY,
    ),
    "portfolio.status": MigratedHandlerDescriptor(
        command_id="portfolio.status",
        owner_module="src/devpilot_core/cli_commands/workspace_onboarding.py",
        handler="handle_portfolio_status",
        wrapper="portfolio_status_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_016_portfolio_status_hardening.py tests/test_post_h_030_workspace_onboarding_command_extraction.py -q",
        ),
        rationale="POST-H-030-D moves portfolio status result-building into workspace_onboarding.py while preserving the ApplicationService boundary.",
        migrated_by=POST_H_030_D_CREATED_BY,
    ),
    "portfolio.hardening-gate": MigratedHandlerDescriptor(
        command_id="portfolio.hardening-gate",
        owner_module="src/devpilot_core/cli_commands/workspace_onboarding.py",
        handler="handle_portfolio_hardening_gate",
        wrapper="portfolio_hardening_gate_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_016_workspace_portfolio_hardening_gate.py tests/test_post_h_030_workspace_onboarding_command_extraction.py -q",
        ),
        rationale="POST-H-030-D moves portfolio hardening gate result-building into workspace_onboarding.py while preserving local-first no-go and report behavior.",
        migrated_by=POST_H_030_D_CREATED_BY,
    ),

    "validate": MigratedHandlerDescriptor(
        command_id="validate",
        owner_module="src/devpilot_core/cli_commands/validation.py",
        handler="handle_validate_scope",
        wrapper="validate_gateway_command",
        recommended_tests=(
            "python -m pytest tests/test_validation_gateway.py tests/test_post_h_006_c_handler_migration.py -q",
        ),
        rationale="Validation gateway scope handler migrated for docs/contracts/all while preserving public UX.",
    ),

    "industrial-readiness.check": MigratedHandlerDescriptor(
        command_id="industrial-readiness.check",
        owner_module="src/devpilot_core/cli_commands/industrial_readiness.py",
        handler="handle_industrial_readiness_check",
        wrapper="industrial_readiness_check_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_030_industrial_readiness_command_extraction.py tests/test_industrial_readiness.py -q",
        ),
        rationale="POST-H-030-B moves industrial readiness result-building logic into cli_commands/industrial_readiness.py while cli.py preserves parser, optional reports, events, persistence and rendering.",
        migrated_by=POST_H_030_B_CREATED_BY,
    ),
    "industrial-readiness.production-ready-local": MigratedHandlerDescriptor(
        command_id="industrial-readiness.production-ready-local",
        owner_module="src/devpilot_core/cli_commands/industrial_readiness.py",
        handler="handle_industrial_readiness_production_ready_local",
        wrapper="industrial_readiness_production_ready_local_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_030_industrial_readiness_command_extraction.py tests/test_post_h_025_production_ready_declaration_gate.py -q",
        ),
        rationale="POST-H-030-B moves production-ready-local CLI result-building into a domain-owned module while preserving the ApplicationService boundary and output contract.",
        migrated_by=POST_H_030_B_CREATED_BY,
    ),
    "industrial-readiness.production-ready-local-final": MigratedHandlerDescriptor(
        command_id="industrial-readiness.production-ready-local-final",
        owner_module="src/devpilot_core/cli_commands/industrial_readiness.py",
        handler="handle_industrial_readiness_production_ready_local_final",
        wrapper="industrial_readiness_production_ready_local_final_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_030_industrial_readiness_command_extraction.py tests/test_post_h_025_production_ready_final_declaration.py -q",
        ),
        rationale="POST-H-030-B moves final production-ready-local declaration CLI result-building into a domain-owned module while preserving claims/no-go behavior.",
        migrated_by=POST_H_030_B_CREATED_BY,
    ),
    "release.manifest": MigratedHandlerDescriptor(
        command_id="release.manifest",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_manifest",
        wrapper="release_manifest_command",
        recommended_tests=(
            "python -m pytest tests/test_release_manifest.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release.changelog": MigratedHandlerDescriptor(
        command_id="release.changelog",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_changelog",
        wrapper="release_changelog_command",
        recommended_tests=(
            "python -m pytest tests/test_release_changelog.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release.sbom": MigratedHandlerDescriptor(
        command_id="release.sbom",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_sbom",
        wrapper="release_sbom_command",
        recommended_tests=(
            "python -m pytest tests/test_release_sbom.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release.environment-snapshot": MigratedHandlerDescriptor(
        command_id="release.environment-snapshot",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_environment_snapshot",
        wrapper="release_environment_snapshot_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_017_release_reproducibility_pack.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release.source-archive-manifest": MigratedHandlerDescriptor(
        command_id="release.source-archive-manifest",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_source_archive_manifest",
        wrapper="release_source_archive_manifest_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_017_source_archive_manifest.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release.reproducibility-verify": MigratedHandlerDescriptor(
        command_id="release.reproducibility-verify",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_reproducibility_verify",
        wrapper="release_reproducibility_verify_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_017_release_reproducibility_pack.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release.reproducibility-pack": MigratedHandlerDescriptor(
        command_id="release.reproducibility-pack",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_reproducibility_pack",
        wrapper="release_reproducibility_pack_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_017_release_reproducibility_pack.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release.checksum": MigratedHandlerDescriptor(
        command_id="release.checksum",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_checksum",
        wrapper="release_checksum_command",
        recommended_tests=(
            "python -m pytest tests/test_release_verification.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release.smoke-test": MigratedHandlerDescriptor(
        command_id="release.smoke-test",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_smoke_test",
        wrapper="release_smoke_test_command",
        recommended_tests=(
            "python -m pytest tests/test_release_verification.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release.verify": MigratedHandlerDescriptor(
        command_id="release.verify",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_verify",
        wrapper="release_verify_command",
        recommended_tests=(
            "python -m pytest tests/test_release_verification.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release.artifact-manifest": MigratedHandlerDescriptor(
        command_id="release.artifact-manifest",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_artifact_manifest",
        wrapper="release_artifact_manifest_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_027_artifact_manifest_checksums.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release.upgrade-rollback-dry-run": MigratedHandlerDescriptor(
        command_id="release.upgrade-rollback-dry-run",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_upgrade_rollback_dry_run",
        wrapper="release_upgrade_rollback_dry_run_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_027_upgrade_rollback_dry_run.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release.python-artifact-verify": MigratedHandlerDescriptor(
        command_id="release.python-artifact-verify",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_python_artifact_verify",
        wrapper="release_python_artifact_verify_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_027_python_artifact_install_verification.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "install.plan": MigratedHandlerDescriptor(
        command_id="install.plan",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_install_plan",
        wrapper="install_plan_command",
        recommended_tests=(
            "python -m pytest tests/test_installation_plan.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "install.windows-smoke": MigratedHandlerDescriptor(
        command_id="install.windows-smoke",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_install_windows_smoke",
        wrapper="install_windows_smoke_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_027_windows_install_smoke.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "backup.create": MigratedHandlerDescriptor(
        command_id="backup.create",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_backup_create",
        wrapper="backup_create_command",
        recommended_tests=(
            "python -m pytest tests/test_backup_upgrade.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "backup.list": MigratedHandlerDescriptor(
        command_id="backup.list",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_backup_list",
        wrapper="backup_list_command",
        recommended_tests=(
            "python -m pytest tests/test_backup_upgrade.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "backup.restore": MigratedHandlerDescriptor(
        command_id="backup.restore",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_backup_restore",
        wrapper="backup_restore_command",
        recommended_tests=(
            "python -m pytest tests/test_backup_upgrade.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "upgrade.check": MigratedHandlerDescriptor(
        command_id="upgrade.check",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_upgrade_check",
        wrapper="upgrade_check_command",
        recommended_tests=(
            "python -m pytest tests/test_backup_upgrade.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "package.build": MigratedHandlerDescriptor(
        command_id="package.build",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_package_build",
        wrapper="package_build_command",
        recommended_tests=(
            "python -m pytest tests/test_package_builder.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "package.source-zip-policy": MigratedHandlerDescriptor(
        command_id="package.source-zip-policy",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_package_source_zip_policy",
        wrapper="package_source_zip_policy_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_027_source_zip_policy.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release-candidate.evidence-freshness": MigratedHandlerDescriptor(
        command_id="release-candidate.evidence-freshness",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_candidate_evidence_freshness",
        wrapper="release_candidate_evidence_freshness_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_026_evidence_freshness.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release-candidate.profile": MigratedHandlerDescriptor(
        command_id="release-candidate.profile",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_candidate_profile",
        wrapper="release_candidate_profile_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_026_release_candidate_profile.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release-candidate.ui-api-smoke": MigratedHandlerDescriptor(
        command_id="release-candidate.ui-api-smoke",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_candidate_ui_api_smoke",
        wrapper="release_candidate_ui_api_smoke_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_026_ui_api_rc_smoke.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release-candidate.install-smoke": MigratedHandlerDescriptor(
        command_id="release-candidate.install-smoke",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_candidate_install_smoke",
        wrapper="release_candidate_install_smoke_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_026_install_smoke.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),

    "release-candidate.final": MigratedHandlerDescriptor(
        command_id="release-candidate.final",
        owner_module="src/devpilot_core/cli_commands/release.py",
        handler="handle_release_candidate_final",
        wrapper="release_candidate_final_command",
        recommended_tests=(
            "python -m pytest tests/test_post_h_026_release_candidate_report.py tests/test_post_h_030_release_command_extraction.py -q",
        ),
        rationale="POST-H-030-C moves release-family result-building logic into cli_commands/release.py while cli.py preserves parser, events, persistence, optional report wiring, JSON rendering and exit codes.",
        migrated_by=POST_H_030_C_CREATED_BY,
    ),
}


DECLARATIVE_GROUPS: dict[str, DeclarativeGroupDescriptor] = {
    "workspace": DeclarativeGroupDescriptor(
        group_id="workspace",
        domain="operations.workspace",
        owner_module="src/devpilot_core/cli_commands/workspace.py",
        application_service_required=True,
        recommended_tests=("python -m pytest tests/test_post_h_030_workspace_onboarding_command_extraction.py tests/test_workspace_manager.py tests/test_post_h_024_project_bootstrap.py tests/test_post_h_024_onboarding_readiness_preview.py tests/test_post_h_016_workspace_registry_v2.py -q",),
        rationale="POST-H-030-D consolidates workspace/onboarding handlers in a domain-owned CLI module while cli.py preserves parser, wrappers, events, reports and rendering.",
    ),
    "standards": DeclarativeGroupDescriptor(
        group_id="standards",
        domain="documentation.governance",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_standards_registry.py tests/test_post_h_006_b_declarative_registry.py -q",),
        rationale="Standards status is low-risk and suitable as a declarative registry baseline.",
    ),
    "schema": DeclarativeGroupDescriptor(
        group_id="schema",
        domain="governance.schemas",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_schema_registry.py tests/test_cli_command_registry_schema.py tests/test_post_h_006_b_declarative_registry.py -q",),
        rationale="Schema commands are deterministic validators with schema-backed outputs.",
    ),
    "validate": DeclarativeGroupDescriptor(
        group_id="validate",
        domain="documentation.governance",
        owner_module="src/devpilot_core/cli.py",
        application_service_required=True,
        recommended_tests=("python -m pytest tests/test_validation_gateway.py tests/test_post_h_006_b_declarative_registry.py -q",),
        rationale="Validation gateway commands are a safe initial registry candidate and later migration target.",
    ),
    "project-state": DeclarativeGroupDescriptor(
        group_id="project-state",
        domain="governance.project_state",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_project_global_state.py tests/test_post_h_006_b_declarative_registry.py -q",),
        rationale="Project-state validation is deterministic and critical for sprint synchronization.",
    ),
    "test-contracts": DeclarativeGroupDescriptor(
        group_id="test-contracts",
        domain="governance.testing",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_test_contract_registry.py tests/test_test_contract_registry_v2.py tests/test_test_contract_registry_profiles_v2.py tests/test_post_h_006_b_declarative_registry.py -q",),
        rationale="Test contract commands govern impact selection and must be explicit before handler migration.",
    ),
    "tests": DeclarativeGroupDescriptor(
        group_id="tests",
        domain="governance.testing",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_post_h_029_test_profile_taxonomy.py tests/test_post_h_029_release_candidate_test_profile.py tests/test_post_h_029_historical_regression_guard.py tests/test_tests_run_tool.py -q",),
        rationale="POST-H-029 registers tests taxonomy/profiles/run/release-candidate-profile as governed local testing surfaces; taxonomy/profile validators are read-only and tests.run remains approval-gated.",
    ),
    "quality-gate": DeclarativeGroupDescriptor(
        group_id="quality-gate",
        domain="quality.gate",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_quality_gate.py tests/test_post_h_006_b_declarative_registry.py -q",),
        rationale="Quality-gate commands are high-value orchestration surfaces and require explicit risk metadata.",
    ),
    "industrial-readiness": DeclarativeGroupDescriptor(
        group_id="industrial-readiness",
        domain="quality.gate",
        owner_module="src/devpilot_core/cli_commands/industrial_readiness.py",
        recommended_tests=("python -m pytest tests/test_post_h_030_industrial_readiness_command_extraction.py tests/test_industrial_readiness.py tests/test_post_h_006_b_declarative_registry.py -q",),
        rationale="Industrial-readiness handlers are extracted to a domain-owned CLI module in POST-H-030-B while public parser/dispatch compatibility remains in cli.py.",
    ),
    "release-candidate": DeclarativeGroupDescriptor(
        group_id="release-candidate",
        domain="release",
        owner_module="src/devpilot_core/cli_commands/release.py",
        recommended_tests=("python -m pytest tests/test_post_h_026_evidence_freshness.py tests/test_post_h_026_release_candidate_profile.py tests/test_post_h_026_ui_api_rc_smoke.py tests/test_post_h_026_ui_api_rc_smoke_contract.py tests/test_post_h_026_install_smoke.py tests/test_post_h_026_release_candidate_report.py tests/test_post_h_006_b_declarative_registry.py -q",),
        rationale="POST-H-030-C extracts local release-candidate result builders to cli_commands/release.py while preserving RC evidence contracts and local-first behavior.",
    ),

    "install": DeclarativeGroupDescriptor(
        group_id="install",
        domain="release",
        owner_module="src/devpilot_core/cli_commands/release.py",
        recommended_tests=("python -m pytest tests/test_post_h_027_windows_install_smoke.py tests/test_installation_plan.py tests/test_post_h_006_b_declarative_registry.py -q",),
        rationale="POST-H-030-C extracts install release-family handlers to cli_commands/release.py while preserving local-first smoke and plan semantics.",
    ),
    "package": DeclarativeGroupDescriptor(
        group_id="package",
        domain="release",
        owner_module="src/devpilot_core/cli_commands/release.py",
        recommended_tests=("python -m pytest tests/test_post_h_027_source_zip_policy.py tests/test_post_h_027_python_artifact_install_verification.py tests/test_post_h_027_artifact_manifest_checksums.py tests/test_post_h_027_windows_install_smoke.py tests/test_package_builder.py tests/test_post_h_006_b_declarative_registry.py -q",),
        rationale="POST-H-030-C extracts package/release packaging handlers to cli_commands/release.py while preserving dry-run, no-publish and no-deploy contracts.",
    ),

    "backup": DeclarativeGroupDescriptor(
        group_id="backup",
        domain="release",
        owner_module="src/devpilot_core/cli_commands/release.py",
        recommended_tests=("python -m pytest tests/test_post_h_030_release_command_extraction.py -q",),
        rationale="POST-H-030-C registers and extracts backup lifecycle handlers as release-family local safety commands while preserving dry-run/approval semantics.",
    ),
    "upgrade": DeclarativeGroupDescriptor(
        group_id="upgrade",
        domain="release",
        owner_module="src/devpilot_core/cli_commands/release.py",
        recommended_tests=("python -m pytest tests/test_post_h_030_release_command_extraction.py -q",),
        rationale="POST-H-030-C registers and extracts upgrade readiness handlers as release-family local safety commands while preserving dry-run semantics.",
    ),

    "cli-registry": DeclarativeGroupDescriptor(
        group_id="cli-registry",
        domain="interface.cli",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_post_h_006_e_cli_no_growth_gate.py tests/test_post_h_006_d_cli_hotspot_ownership.py tests/test_post_h_006_cli_command_registry.py tests/test_post_h_030_cli_compatibility_contracts.py -q",),
        rationale="CLI registry commands govern the command surface, no-growth gates and POST-H-030-E compatibility contracts.",
    ),
    "runtime-state": DeclarativeGroupDescriptor(
        group_id="runtime-state",
        domain="operations.runtime_state",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_runtime_state_inventory.py tests/test_runtime_state_cleanup_plan.py tests/test_runtime_state_export.py tests/test_runtime_state_hygiene.py tests/test_post_h_008_runtime_state_lifecycle.py -q",),
        rationale="POST-H-008 runtime-state commands inspect local lifecycle artifacts and plan cleanup/export with dry-run defaults and explicit execution guards.",
    ),

    "observability": DeclarativeGroupDescriptor(
        group_id="observability",
        domain="operations.observability",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_observability_inventory.py tests/test_observability_cleanup_plan.py tests/test_observability_export.py tests/test_post_h_010_observability_retention.py -q",),
        rationale="POST-H-010 observability commands inspect local retention targets, generate dry-run cleanup plans and export local redacted evidence without enabling destructive cleanup or remote export.",
    ),
    "evidence": DeclarativeGroupDescriptor(
        group_id="evidence",
        domain="operations.observability",
        owner_module="src/devpilot_core/evidence_graph/builder.py",
        application_service_required=True,
        recommended_tests=("python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_031_evidence_graph_model.py tests/test_post_h_031_operator_health_summary.py tests/test_post_h_031_gap_to_action_mapping.py tests/test_post_h_031_claims_no_go_dashboard.py tests/test_schema_registry.py -q",),
        rationale="POST-H-031 registers local read-only evidence graph, operator health, gap-to-action and claims/no-go dashboard surfaces; they write only optional outputs/reports evidence and do not replace formal readiness gates.",
    ),
    "docs-governance": DeclarativeGroupDescriptor(
        group_id="docs-governance",
        domain="documentation.governance",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_documentation_governance_validator.py tests/test_post_h_009_documentation_governance.py -q",),
        rationale="POST-H-009-B documentation governance commands validate canonical-source metadata without using LLM judge, network or source mutations.",
    ),
    "api": DeclarativeGroupDescriptor(
        group_id="api",
        domain="product.api",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_post_h_014_ui_api_shell_gate.py tests/test_api_contract.py -q",),
        rationale="POST-H-014-E API shell-gate is a governed local quality surface; it must be registered instead of remaining legacy-unregistered.",
    ),
    "operator": DeclarativeGroupDescriptor(
        group_id="operator",
        domain="product.operator",
        owner_module="src/devpilot_core/cli.py",
        application_service_required=True,
        recommended_tests=("python -m pytest tests/test_post_h_015_operator_dashboard_ready_gate.py tests/test_post_h_015_operator_dashboard_application_api.py -q",),
        rationale="POST-H-015-E exposes the local operator dashboard snapshot through the ApplicationService boundary and writes evidence only under outputs/reports when requested.",
    ),
    "portfolio": DeclarativeGroupDescriptor(
        group_id="portfolio",
        domain="workspace.portfolio",
        owner_module="src/devpilot_core/cli_commands/workspace_onboarding.py",
        application_service_required=True,
        recommended_tests=("python -m pytest tests/test_post_h_030_workspace_onboarding_command_extraction.py tests/test_post_h_016_portfolio_status_hardening.py tests/test_post_h_016_workspace_portfolio_hardening_gate.py -q",),
        rationale="POST-H-030-D extracts portfolio/workspace readiness result-building into workspace_onboarding.py while preserving ApplicationService and hardening-gate boundaries.",
    ),
    "audit-pack": DeclarativeGroupDescriptor(
        group_id="audit-pack",
        domain="operations.audit",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_audit_pack_v2.py tests/test_audit_pack_integrity_gate.py -q",),
        rationale="POST-H-013 audit-pack v2 commands are governed local audit surfaces with explicit dry-run/execute semantics and must be registered before the no-growth gate runs.",
    ),
    "release": DeclarativeGroupDescriptor(
        group_id="release",
        domain="release",
        owner_module="src/devpilot_core/cli_commands/release.py",
        recommended_tests=("python -m pytest tests/test_post_h_017_release_reproducibility_pack.py tests/test_post_h_017_source_archive_manifest.py tests/test_post_h_027_artifact_manifest_checksums.py tests/test_post_h_027_upgrade_rollback_dry_run.py tests/test_release_verification.py tests/test_release_manifest.py -q",),
        rationale="POST-H-030-C extracts release-family handlers to a domain-owned CLI module while preserving parser, optional reports and local dry-run evidence semantics.",
    ),
    "connector": DeclarativeGroupDescriptor(
        group_id="connector",
        domain="integration.connectors",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_post_h_018_connector_sandbox_runner.py tests/test_post_h_018_connector_sandbox_policy.py -q",),
        rationale="POST-H-018 connector commands validate local deny-write connector contracts and run local sandbox simulation without connector write, network, external APIs, remote execution or plugin execution.",
    ),
}


COMMAND_OVERRIDES: dict[str, DeclarativeCommandOverride] = {
    "cli-registry.compatibility": DeclarativeCommandOverride(
        command_id="cli-registry.compatibility",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_030_cli_compatibility_contracts.py -q",
        ),
        rationale="POST-H-030-E validates source-controlled CLI compatibility contracts and writes only optional reports under outputs/reports.",
    ),
    "evidence.graph": DeclarativeCommandOverride(
        command_id="evidence.graph",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_031_evidence_graph_model.py -q",
        ),
        rationale="POST-H-031-A builds a local read-only EvidenceGraph and writes reports only under outputs/reports when --write-report is explicit; it does not execute commands or declare readiness.",
    ),
    "evidence.health": DeclarativeCommandOverride(
        command_id="evidence.health",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_031_operator_health_summary.py -q",
        ),
        rationale="POST-H-031-B builds a local read-only OperatorHealthSummary derived from EvidenceGraph and source-controlled metadata; top actions are advisory and no commands are executed.",
    ),
    "evidence.gaps": DeclarativeCommandOverride(
        command_id="evidence.gaps",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_031_gap_to_action_mapping.py -q",
        ),
        rationale="POST-H-031-C builds a local read-only GapActionMap from EvidenceGraph and OperatorHealthSummary; actions are advisory, safe and never executed by the builder.",
    ),
    "evidence.claims-dashboard": DeclarativeCommandOverride(
        command_id="evidence.claims-dashboard",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_031_claims_no_go_dashboard.py -q",
        ),
        rationale="POST-H-031-D builds a local read-only ClaimsNoGoDashboard from POST-H-025 criteria, EvidenceGraph and ProductionReadyClaimsValidator; it does not mutate claims or gates.",
    ),

    "workspace.init": DeclarativeCommandOverride(
        command_id="workspace.init",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.MUTATE_STATE, CommandSideEffect.WRITE_FILES, CommandSideEffect.WRITE_REPORT),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        rationale="`workspace init --execute` can create local workspace files; dry-run remains default and policy metadata is mandatory.",
    ),
    "workspace.bootstrap": DeclarativeCommandOverride(
        command_id="workspace.bootstrap",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_FILES, CommandSideEffect.WRITE_REPORT),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_024_project_bootstrap.py -q",
        ),
        rationale="POST-H-024-C workspace bootstrap defaults to dry-run, writes only bounded starter files under explicit execute, emits reports only with --write-report and refuses overwrite by default.",
    ),
    "workspace.readiness-preview": DeclarativeCommandOverride(
        command_id="workspace.readiness-preview",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_024_onboarding_readiness_preview.py -q",
        ),
        rationale="POST-H-024-D readiness preview is read-only with respect to project/workspace source and writes only optional evidence reports under outputs/reports.",
    ),
    "tests.taxonomy": DeclarativeCommandOverride(
        command_id="tests.taxonomy",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_029_test_profile_taxonomy.py -q",
        ),
        rationale="POST-H-029-A validates the local TestProfileTaxonomy and writes only outputs/reports evidence when --write-report is explicit; it never executes pytest/npm from taxonomy metadata.",
    ),

    "tests.release-candidate-profile": DeclarativeCommandOverride(
        command_id="tests.release-candidate-profile",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_029_release_candidate_test_profile.py tests/test_post_h_026_release_candidate_profile.py tests/test_quality_gate.py tests/test_project_global_state.py -q",
        ),
        rationale="POST-H-029-D validates the formal release-candidate-local test profile and writes only outputs/reports evidence when --write-report is explicit; it never executes tests from JSON.",
    ),
    "tests.regression-guard": DeclarativeCommandOverride(
        command_id="tests.regression-guard",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_029_historical_regression_guard.py tests/test_post_h_029_release_candidate_test_profile.py tests/test_quality_gate.py tests/test_project_global_state.py -q",
        ),
        rationale="POST-H-029-E validates the historical regression closure guard and writes only outputs/reports evidence when --write-report is explicit; it never executes pytest or accepts permanent waivers.",
    ),
    "tests.profiles": DeclarativeCommandOverride(
        command_id="tests.profiles",
        risk_level=CommandRiskLevel.LOW,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=False,
        recommended_tests=(
            "python -m pytest tests/test_post_h_029_test_profile_taxonomy.py tests/test_post_h_029_release_candidate_test_profile.py tests/test_post_h_029_historical_regression_guard.py tests/test_tests_run_tool.py -q",
        ),
        rationale="tests profiles remains a read-only listing command for configured approval-gated test profiles; --write-report writes only outputs/reports evidence.",
    ),
    "tests.run": DeclarativeCommandOverride(
        command_id="tests.run",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.EXECUTE_SUBPROCESS, CommandSideEffect.WRITE_REPORT),
        writes_files=True,
        dry_run_supported=False,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_tests_run_tool.py -q",
        ),
        rationale="tests.run executes only fixed configured pytest profiles after PolicyEngine approval; POST-H-029-A expands profile ids without allowing arbitrary shell or user-provided pytest args.",
    ),
    "test-contracts.migrate-v2": DeclarativeCommandOverride(
        command_id="test-contracts.migrate-v2",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_FILES, CommandSideEffect.WRITE_REPORT),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        rationale="Registry migration can materialize files when explicitly requested; it stays governed and dry-run capable.",
    ),
    "quality-gate.run": DeclarativeCommandOverride(
        command_id="quality-gate.run",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.EXECUTE_SUBPROCESS, CommandSideEffect.WRITE_REPORT),
        writes_files=True,
        dry_run_supported=False,
        policy_check_required=True,
        rationale="`quality-gate run --include-pytest` can invoke pytest; subprocess side effect is explicit even when the default path is bounded.",
    ),
    "industrial-readiness.production-ready-local": DeclarativeCommandOverride(
        command_id="industrial-readiness.production-ready-local",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_025_production_ready_declaration_gate.py -q",
        ),
        rationale="POST-H-025-C exposes the production-ready-local declaration gate through ApplicationService; it reads local evidence and writes JSON/Markdown reports only when --write-report is explicit.",
    ),
    "industrial-readiness.production-ready-local-final": DeclarativeCommandOverride(
        command_id="industrial-readiness.production-ready-local-final",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_025_production_ready_final_declaration.py -q",
        ),
        rationale="POST-H-025-E packages the final production-ready-local PASS/BLOCK declaration; it writes runtime reports and audit Markdown only when explicit flags are used.",
    ),

    "api.contract-drift": DeclarativeCommandOverride(
        command_id="api.contract-drift",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_028_api_contract_drift_guard.py tests/test_api_contract.py tests/test_schema_registry.py -q",
        ),
        rationale="POST-H-028-A compares FastAPI runtime/canonical routes, ApiRouteContractRegistry, API_ROUTE_POLICIES and static OpenAPI without starting servers, opening sockets, network, external APIs or source mutations; --write-report writes only outputs/reports evidence.",
    ),
    "api.security-hardening": DeclarativeCommandOverride(
        command_id="api.security-hardening",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_028_local_auth_cors_hardening.py tests/test_post_h_014_security_hardening.py tests/test_api_security.py tests/test_api_settings.py tests/test_schema_registry.py -q",
        ),
        rationale="POST-H-028-B verifies local API token enforcement, restricted CORS, localhost bind refusal, security headers and redaction with in-process TestClient; --write-report writes only outputs/reports evidence.",
    ),

    "api.visual-smoke-report": DeclarativeCommandOverride(
        command_id="api.visual-smoke-report",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_028_visual_smoke_contract.py tests/test_web_ui_mvp.py tests/test_web_ui_report_trace_viewer.py tests/test_web_ui_approval_center.py tests/test_web_ui_settings.py tests/test_post_h_015_operator_dashboard_ui.py -q",
            "npm --prefix ui/web test",
        ),
        rationale="POST-H-028-C creates a dependency-light UI visual smoke report for critical local operator surfaces; --write-report writes only outputs/reports evidence and browser tooling remains optional/advisory for the core gate.",
    ),

    "api.operator-flow-smoke": DeclarativeCommandOverride(
        command_id="api.operator-flow-smoke",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_028_operator_flows_error_states.py tests/test_api_reports_traces.py tests/test_api_approvals_actions.py tests/test_api_settings.py tests/test_post_h_015_operator_dashboard_application_api.py tests/test_post_h_015_operator_dashboard_ui.py tests/test_web_ui_mvp.py -q",
            "python -m devpilot_core api operator-flow-smoke --json --write-report",
        ),
        rationale="POST-H-028-D creates a local operator flow and error-state smoke report for API down, missing/invalid token, empty states, approvals, dry-run actions, forbidden action BLOCK, settings redaction and operator dashboard next actions; --write-report writes only outputs/reports evidence.",
    ),

    "api.ui-route-enforcement": DeclarativeCommandOverride(
        command_id="api.ui-route-enforcement",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_028_ui_route_registry_enforcement.py tests/test_post_h_014_ui_shell_contract.py tests/test_post_h_014_ui_api_shell_gate.py tests/test_web_ui_mvp.py tests/test_schema_registry.py tests/test_project_global_state.py -q",
            "python -m devpilot_core api ui-route-enforcement --json --write-report",
        ),
        rationale="POST-H-028-E enforces UiRouteContractRegistry, UI/API route bindings, critical view registration, forbidden UI actions and API-only boundaries; --write-report writes only outputs/reports evidence.",
    ),
    "api.shell-gate": DeclarativeCommandOverride(
        command_id="api.shell-gate",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.EXECUTE_SUBPROCESS, CommandSideEffect.WRITE_REPORT),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_014_ui_api_shell_gate.py -q",
        ),
        rationale="POST-H-014-E UI/API shell-gate runs only local registry/docs checks plus the existing npm smoke test and writes evidence only under outputs/reports when --write-report is explicit.",
    ),
    "operator.dashboard": DeclarativeCommandOverride(
        command_id="operator.dashboard",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_015_operator_dashboard_ready_gate.py tests/test_post_h_015_operator_dashboard_application_api.py -q",
        ),
        rationale="POST-H-015-E operator dashboard is read-only by default and writes only operator_dashboard_snapshot JSON/Markdown under outputs/reports when --write-report is explicit.",
    ),
    "portfolio.status": DeclarativeCommandOverride(
        command_id="portfolio.status",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_016_portfolio_status_hardening.py -q",
        ),
        rationale="POST-H-016-C portfolio status is read-only over the workspace registry and writes evidence only when --write-report is explicit.",
    ),
    "portfolio.hardening-gate": DeclarativeCommandOverride(
        command_id="portfolio.hardening-gate",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_016_workspace_portfolio_hardening_gate.py -q",
        ),
        rationale="POST-H-016-E workspace portfolio hardening gate is a governed local read-only quality surface and writes evidence only when --write-report is explicit.",
    ),
    "release.environment-snapshot": DeclarativeCommandOverride(
        command_id="release.environment-snapshot",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_017_environment_snapshot.py tests/test_post_h_017_release_reproducibility_schema.py -q",
        ),
        rationale="POST-H-017-B reads local project manifests only and writes redacted environment evidence under outputs/release when --write-report is explicit.",
    ),
    "release.source-archive-manifest": DeclarativeCommandOverride(
        command_id="release.source-archive-manifest",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT, CommandSideEffect.EXECUTE_SUBPROCESS),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_017_source_archive_manifest.py tests/test_post_h_017_release_reproducibility_schema.py -q",
        ),
        rationale="POST-H-017-C optionally inspects git archive HEAD in memory and writes source archive/checksum evidence under outputs/release when --write-report is explicit.",
    ),
    "release.reproducibility-verify": DeclarativeCommandOverride(
        command_id="release.reproducibility-verify",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT, CommandSideEffect.EXECUTE_SUBPROCESS),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_017_reproducibility_verify.py tests/test_post_h_017_release_reproducibility_schema.py -q",
        ),
        rationale="POST-H-017-D verifies local reproducibility-pack evidence and critical checksums without publishing, deploying, network, external APIs or source mutations; --write-report writes only outputs/release evidence.",
    ),

    "install.windows-smoke": DeclarativeCommandOverride(
        command_id="install.windows-smoke",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_027_windows_install_smoke.py tests/test_installation_plan.py tests/test_schema_registry.py -q",
        ),
        rationale="POST-H-027-D writes optional Windows install smoke evidence under outputs/reports when --write-report is explicit; it does not run pip/npm, open sockets, require admin, publish, deploy, call network/external APIs or mutate source files.",
    ),
    "release.artifact-manifest": DeclarativeCommandOverride(
        command_id="release.artifact-manifest",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_027_artifact_manifest_checksums.py tests/test_schema_registry.py -q",
        ),
        rationale="POST-H-027-C writes local artifact manifest/checksum evidence under outputs/release when --write-report is explicit; it never publishes, deploys, signs, calls network/external APIs or mutates source files.",
    ),
    "release.upgrade-rollback-dry-run": DeclarativeCommandOverride(
        command_id="release.upgrade-rollback-dry-run",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_027_upgrade_rollback_dry_run.py tests/test_backup_upgrade.py tests/test_quality_gate.py tests/test_schema_registry.py -q",
        ),
        rationale="POST-H-027-E writes optional upgrade/rollback dry-run evidence under outputs/reports when --write-report is explicit; it validates backup, artifact manifest/checksum and restore dry-run safety without auto-update, restore execution, migrations, publish, deploy, network or external APIs.",
    ),
    "release.reproducibility-pack": DeclarativeCommandOverride(
        command_id="release.reproducibility-pack",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT, CommandSideEffect.EXECUTE_SUBPROCESS),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_017_release_reproducibility_pack.py tests/test_post_h_017_reproducibility_verify.py tests/test_post_h_017_release_reproducibility_schema.py -q",
        ),
        rationale="POST-H-017-E generates local reproducibility pack evidence under outputs/release and may invoke the local verifier; it never publishes, deploys, calls network/external APIs or mutates source files.",
    ),
    "connector.validate": DeclarativeCommandOverride(
        command_id="connector.validate",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_connector_registry.py tests/test_post_h_018_connector_sandbox_policy.py -q",
        ),
        rationale="Connector registry validation is local-first/read-only and writes evidence only when --write-report is explicit.",
    ),
    "connector.call": DeclarativeCommandOverride(
        command_id="connector.call",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_connector_adapter.py tests/test_post_h_018_connector_sandbox_policy.py -q",
        ),
        rationale="Existing connector call remains governed local read-only dry-run evidence; connector write, network and external APIs remain disabled.",
    ),
    "connector.sandbox.run": DeclarativeCommandOverride(
        command_id="connector.sandbox.run",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_018_connector_sandbox_runner.py tests/test_post_h_018_connector_replay.py tests/test_post_h_018_connector_policy_binding.py tests/test_post_h_018_connector_sandbox_policy.py -q",
        ),
        rationale="POST-H-018-D connector sandbox run validates/dry-runs/replays locally through policy, deterministic fixtures, redaction checks, Policy/Approval/RBAC binding and report generation only; it does not enable connector write, network, external APIs, remote execution or plugin execution.",
    ),
    "connector.sandbox.exposure": DeclarativeCommandOverride(
        command_id="connector.sandbox.exposure",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_018_connector_policy_binding.py tests/test_post_h_018_connector_sandbox_policy.py -q",
        ),
        rationale="POST-H-018-D connector sandbox exposure builds a local Policy/Approval/RBAC report proving connector.write_future is blocked, high-risk connectors evaluate RBAC and read-only connectors keep policy coverage without network or external APIs.",
    ),
    "cli-registry.guard": DeclarativeCommandOverride(
        command_id="cli-registry.guard",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_post_h_006_e_cli_no_growth_gate.py tests/test_post_h_006_d_cli_hotspot_ownership.py -q",
        ),
        rationale="No-growth enforcement can block merges and optionally writes evidence reports; it remains local/read-only for source files.",
    ),
    "runtime-state.inventory": DeclarativeCommandOverride(
        command_id="runtime-state.inventory",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_runtime_state_inventory.py tests/test_post_h_008_runtime_state_lifecycle.py -q",
        ),
        rationale="Inventory is read-only for source/runtime artifacts. --write-report may materialize JSON/Markdown evidence under outputs/reports.",
    ),

    "runtime-state.cleanup-plan": DeclarativeCommandOverride(
        command_id="runtime-state.cleanup-plan",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_runtime_state_cleanup_plan.py tests/test_post_h_008_runtime_state_lifecycle.py -q",
        ),
        rationale="Cleanup plan is dry-run by default and only writes explicit JSON/Markdown evidence with --write-report.",
    ),
    "runtime-state.cleanup": DeclarativeCommandOverride(
        command_id="runtime-state.cleanup",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_FILES, CommandSideEffect.WRITE_REPORT),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_runtime_state_cleanup_plan.py tests/test_runtime_state_inventory.py -q",
        ),
        rationale="Cleanup is dry-run by default; --execute requires explicit confirmation and may delete only safe-cleanup runtime artifacts, never source-of-truth paths.",
    ),

    "runtime-state.export": DeclarativeCommandOverride(
        command_id="runtime-state.export",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_FILES,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_runtime_state_export.py tests/test_runtime_state_inventory.py tests/test_post_h_008_runtime_state_lifecycle.py -q",
        ),
        rationale="Runtime evidence export is dry-run by default; execute mode writes only redacted evidence, manifest and checksums under outputs/runtime_exports/.",
    ),


    "runtime-state.hygiene": DeclarativeCommandOverride(
        command_id="runtime-state.hygiene",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT, CommandSideEffect.EXECUTE_SUBPROCESS),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_runtime_state_hygiene.py tests/test_runtime_state_inventory.py tests/test_post_h_008_runtime_state_lifecycle.py -q",
        ),
        rationale="Runtime-state hygiene is read-only for source/runtime artifacts and optionally writes evidence; it may inspect git archive HEAD in memory when Git metadata is available.",
    ),

    "observability.inventory": DeclarativeCommandOverride(
        command_id="observability.inventory",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_observability_inventory.py tests/test_post_h_010_observability_retention.py -q",
        ),
        rationale="Observability inventory is read-only for runtime/source artifacts. --write-report may materialize JSON/Markdown evidence under outputs/reports only.",
    ),


    "observability.cleanup-plan": DeclarativeCommandOverride(
        command_id="observability.cleanup-plan",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_observability_cleanup_plan.py tests/test_observability_inventory.py tests/test_post_h_010_observability_retention.py -q",
        ),
        rationale="Observability cleanup-plan is dry-run-only: it computes would_rotate/would_delete/would_archive/would_redact/would_export actions, embeds PolicyEngine simulations for destructive actions and writes evidence only with --write-report.",
    ),

    "observability.export": DeclarativeCommandOverride(
        command_id="observability.export",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT, CommandSideEffect.WRITE_FILES),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_observability_export.py tests/test_observability_inventory.py tests/test_post_h_010_observability_retention.py -q",
        ),
        rationale="Observability export writes only local redacted summaries/metadata under outputs/reports and outputs/audit_exports when --write-report is explicit; raw payloads, secrets, network and remote export are blocked.",
    ),

    "docs-governance.validate": DeclarativeCommandOverride(
        command_id="docs-governance.validate",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_documentation_governance_validator.py tests/test_post_h_009_documentation_governance.py -q",
        ),
        rationale="Documentation governance validation is read-only for source documents; --write-report writes JSON/Markdown evidence under outputs/reports only.",
    ),
    "docs-governance.report": DeclarativeCommandOverride(
        command_id="docs-governance.report",
        risk_level=CommandRiskLevel.MEDIUM,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_documentation_governance_validator.py tests/test_documentation_governance_sync.py tests/test_post_h_009_documentation_governance.py -q",
        ),
        rationale="Documentation governance report is read-only for source documents and writes JSON/Markdown evidence under outputs/reports only; POST-H-009-D adds backlog governance checks and POST-H-009-E integrates the same validator into quality-gate hardening without source mutations.",
    ),
    "audit-pack.build-v2": DeclarativeCommandOverride(
        command_id="audit-pack.build-v2",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_FILES, CommandSideEffect.WRITE_REPORT),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_audit_pack_v2.py tests/test_post_h_013_audit_pack_manifest_v2.py -q",
        ),
        rationale="POST-H-013-B audit-pack builder is dry-run by default and writes local audit-pack artifacts only when execute mode is explicit.",
    ),
    "audit-pack.verify-v2": DeclarativeCommandOverride(
        command_id="audit-pack.verify-v2",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.WRITE_REPORT,),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        recommended_tests=(
            "python -m pytest tests/test_audit_pack_v2.py tests/test_post_h_013_audit_pack_manifest_v2.py -q",
        ),
        rationale="POST-H-013-C audit-pack verifier reads local audit packs and optionally writes verification evidence under outputs/reports.",
    ),
}


class DeclarativeCliRegistryBuilder:
    """Build the POST-H-006-B declarative CLI registry overlay.

    The builder composes the POST-H-006-A static AST inventory with curated
    descriptors for the initial groups. It is not a runtime router and cannot
    execute or import arbitrary handlers.
    """

    def __init__(self, root: Path, options: StaticCliInventoryOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or StaticCliInventoryOptions()

    def build_registry(self) -> CliCommandRegistry:
        static_registry = StaticCliInventoryExtractor(self.root, self.options).build_registry()
        original_groups = static_registry.groups
        declared_group_ids = set(DECLARATIVE_GROUPS)
        transformed_groups: list[CommandGroupDescriptor] = []
        registered_commands = 0
        registered_groups = 0
        missing_declared_groups = sorted(declared_group_ids - {group.group_id for group in original_groups})

        for group in original_groups:
            group_declaration = DECLARATIVE_GROUPS.get(group.group_id)
            if group_declaration is None:
                commands = [self._mark_legacy_command(command) for command in group.commands]
                transformed_groups.append(
                    CommandGroupDescriptor(
                        group_id=group.group_id,
                        domain=group.domain,
                        owner_module=group.owner_module,
                        risk_level=group.risk_level,
                        application_service_required=group.application_service_required,
                        legacy_cli_owned=group.legacy_cli_owned,
                        commands=commands,
                    )
                )
                continue

            registered_groups += 1
            commands = [self._apply_declaration(command, group_declaration) for command in group.commands]
            registered_commands += len(commands)
            transformed_groups.append(
                CommandGroupDescriptor(
                    group_id=group.group_id,
                    domain=group_declaration.domain,
                    owner_module=group_declaration.owner_module,
                    risk_level=_max_risk([command.risk_level for command in commands]),
                    application_service_required=group_declaration.application_service_required,
                    legacy_cli_owned=True,
                    commands=commands,
                )
            )

        commands_total = sum(len(group.commands) for group in transformed_groups)
        summary = dict(static_registry.summary)
        summary.update(
            {
                "created_by": POST_H_006_E_CREATED_BY,
                "declarative_descriptor_source": DECLARATIVE_DESCRIPTOR_SOURCE,
                "declarative_registered_groups_total": registered_groups,
                "declarative_expected_groups_total": len(DECLARATIVE_GROUPS),
                "declarative_missing_groups_total": len(missing_declared_groups),
                "declarative_missing_groups": missing_declared_groups,
                "declarative_registered_commands_total": registered_commands,
                "legacy_unregistered_commands_total": commands_total - registered_commands,
                "legacy_unregistered_groups_total": len(transformed_groups) - registered_groups,
                "handler_migration_performed": True,
                "migrated_handlers_total": len(MIGRATED_HANDLERS),
                "migrated_command_ids": sorted(MIGRATED_HANDLERS),
                "migrated_handler_owner_modules": sorted({item.owner_module for item in MIGRATED_HANDLERS.values()}),
                "registered_command_ids": sorted(
                    command.command_id
                    for group in transformed_groups
                    for command in group.commands
                    if command.metadata.get("declarative_registered") is True
                ),
                "legacy_unregistered_command_ids": sorted(
                    command.command_id
                    for group in transformed_groups
                    for command in group.commands
                    if command.metadata.get("declarative_registered") is False
                ),
            }
        )

        return CliCommandRegistry(
            schema_version=static_registry.schema_version,
            schema_id=static_registry.schema_id,
            registry_id=static_registry.registry_id,
            generated_from="static-cli-parser-ast-plus-declarative-descriptors-plus-migrated-handlers-plus-hotspot-ownership-report-plus-no-growth-gate",
            created_by=POST_H_006_E_CREATED_BY,
            groups=transformed_groups,
            summary=summary,
            safety={
                **static_registry.safety,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "dynamic_handler_loading_enabled": False,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "preliminary": True,
            },
            recommendations=[
                "Use migrated_handlers_total and migrated_command_ids to verify POST-H-006-C coverage.",
                "Use POST-H-006-D hotspot and ownership metrics plus POST-H-006-E no-growth gate results to prioritize POST-H-007 work.",
                "Keep cli.py as the public parser/dispatch boundary until registry routing is designed and tested.",
                "Treat non-migrated registered commands as governed metadata only; dynamic handler loading remains disabled.",
            ],
            metadata={
                **static_registry.metadata,
                "declarative_descriptor_source": DECLARATIVE_DESCRIPTOR_SOURCE,
                "declarative_initial_groups": list(POST_H_006_B_INITIAL_GROUPS),
                "handler_migration_performed": True,
                "migrated_handlers_total": len(MIGRATED_HANDLERS),
                "migrated_command_ids": sorted(MIGRATED_HANDLERS),
                "runtime_router_enabled": False,
                "hotspot_ownership_report_enabled": True,
                "hotspot_ownership_report_id": "devpilot-cli-command-hotspot-ownership-report",
                "no_growth_gate_enabled": True,
                "no_growth_gate_id": "devpilot-cli-no-growth-gate",
                "legacy_allowlist_path": ".devpilot/cli_registry/legacy_command_allowlist.json",
                "no_runtime_behavior_changed": True,
                "advisory_only": True,
            },
        )

    def _apply_declaration(self, command: CommandDescriptor, group_declaration: DeclarativeGroupDescriptor) -> CommandDescriptor:
        override = COMMAND_OVERRIDES.get(command.command_id)
        migration = MIGRATED_HANDLERS.get(command.command_id)
        side_effects = list(override.side_effects) if override and override.side_effects is not None else list(command.side_effects)
        writes_files = override.writes_files if override and override.writes_files is not None else command.writes_files
        dry_run_supported = override.dry_run_supported if override and override.dry_run_supported is not None else command.dry_run_supported
        policy_required = override.policy_check_required if override and override.policy_check_required is not None else command.policy_check_required
        if any(effect in side_effects for effect in (CommandSideEffect.MUTATE_STATE, CommandSideEffect.EXECUTE_SUBPROCESS)):
            policy_required = True
        if migration is not None:
            recommended_tests = list(migration.recommended_tests)
        elif override and override.recommended_tests:
            recommended_tests = list(override.recommended_tests)
        else:
            recommended_tests = list(group_declaration.recommended_tests)
        risk_level = override.risk_level if override and override.risk_level is not None else command.risk_level
        operation_id = APPLICATION_OPERATION_BY_COMMAND_ID.get(command.command_id)
        metadata: dict[str, Any] = {
            **command.metadata,
            "registry_phase": "handler-migrated-incremental" if migration else "declarative-initial",
            "registration_status": "handler-migrated" if migration else "registered-declarative",
            "declarative_registered": True,
            "declarative_descriptor_source": DECLARATIVE_DESCRIPTOR_SOURCE,
            "declared_by": migration.migrated_by if migration else POST_H_006_B_CREATED_BY,
            "handler_migration_performed": bool(migration),
            "group_rationale": group_declaration.rationale,
            "application_service_boundary_present": bool(operation_id),
        }
        if operation_id:
            metadata.update(
                {
                    "application_operation_id": operation_id,
                    "application_operation_mapping_source": "POST-H-007-E static CLI registry mapping",
                    "application_operation_mapping_status": "mapped-initial",
                }
            )
        elif group_declaration.application_service_required:
            metadata.update(
                {
                    "application_operation_mapping_status": "missing-initial",
                    "application_operation_mapping_warning": True,
                }
            )
        if override:
            metadata["command_rationale"] = override.rationale
        if command.command_id == "cli-registry.compatibility":
            metadata["declared_by"] = POST_H_030_E_CREATED_BY
            metadata["compatibility_contract_runner"] = "src/devpilot_core/cli_registry/compatibility.py"
        if migration:
            metadata.update(
                {
                    "migrated_by": migration.migrated_by,
                    "migration_source": migration.owner_module,
                    "cli_wrapper": migration.wrapper,
                    "wrapper_module": "src/devpilot_core/cli.py",
                    "runtime_router_enabled": False,
                    "migration_rationale": migration.rationale,
                }
            )

        return CommandDescriptor(
            command_id=command.command_id,
            command_path=list(command.command_path),
            public_invocation=command.public_invocation,
            group_id=command.group_id,
            domain=group_declaration.domain,
            owner_module=migration.owner_module if migration else group_declaration.owner_module,
            handler=migration.handler if migration else command.handler,
            returns=command.returns,
            risk_level=risk_level,
            side_effects=side_effects,
            writes_files=bool(writes_files),
            dry_run_supported=bool(dry_run_supported),
            policy_check_required=bool(policy_required),
            recommended_tests=recommended_tests,
            options=list(command.options),
            legacy_cli_owned=False if migration else True,
            remote_execution_enabled=False,
            connector_write_enabled=False,
            plugin_execution_enabled=False,
            metadata=metadata,
        )

    def _mark_legacy_command(self, command: CommandDescriptor) -> CommandDescriptor:
        metadata = {
            **command.metadata,
            "registry_phase": "legacy-unregistered",
            "registration_status": "legacy-unregistered",
            "declarative_registered": False,
            "declarative_descriptor_source": None,
            "declared_by": None,
            "handler_migration_performed": False,
        }
        return CommandDescriptor(
            command_id=command.command_id,
            command_path=list(command.command_path),
            public_invocation=command.public_invocation,
            group_id=command.group_id,
            domain=command.domain,
            owner_module=command.owner_module,
            handler=command.handler,
            returns=command.returns,
            risk_level=command.risk_level,
            side_effects=list(command.side_effects),
            writes_files=command.writes_files,
            dry_run_supported=command.dry_run_supported,
            policy_check_required=command.policy_check_required,
            recommended_tests=list(command.recommended_tests),
            options=list(command.options),
            legacy_cli_owned=command.legacy_cli_owned,
            remote_execution_enabled=False,
            connector_write_enabled=False,
            plugin_execution_enabled=False,
            metadata=metadata,
        )


def _max_risk(risks: list[CommandRiskLevel]) -> CommandRiskLevel:
    order = {CommandRiskLevel.LOW: 1, CommandRiskLevel.MEDIUM: 2, CommandRiskLevel.HIGH: 3, CommandRiskLevel.CRITICAL: 4}
    return max(risks, key=lambda risk: order[risk]) if risks else CommandRiskLevel.LOW
