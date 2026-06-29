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

# POST-H-007-E keeps this metadata static to avoid coupling CLI registry
# generation to ApplicationOperationCatalog imports. The runtime integration
# report validates these operation ids against the catalog.
APPLICATION_OPERATION_BY_COMMAND_ID: dict[str, str] = {
    "standards.status": "standards.status",
    "validate": "validation.gateway",
    "workspace.status": "workspace.status",
    "api.shell-gate": "api.shell_gate",
    "operator.dashboard": "operator.dashboard",
}

POST_H_006_B_INITIAL_GROUPS: tuple[str, ...] = (
    "workspace",
    "standards",
    "schema",
    "validate",
    "project-state",
    "test-contracts",
    "quality-gate",
    "industrial-readiness",
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
    """POST-H-006-C explicit handler migration metadata.

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
}


DECLARATIVE_GROUPS: dict[str, DeclarativeGroupDescriptor] = {
    "workspace": DeclarativeGroupDescriptor(
        group_id="workspace",
        domain="operations.workspace",
        owner_module="src/devpilot_core/cli.py",
        application_service_required=True,
        recommended_tests=("python -m pytest tests/test_workspace_manager.py tests/test_post_h_006_b_declarative_registry.py -q",),
        rationale="Workspace commands are a priority ApplicationService boundary candidate, but handlers remain legacy-owned in POST-H-006-B.",
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
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_industrial_readiness.py tests/test_post_h_006_b_declarative_registry.py -q",),
        rationale="Industrial-readiness is deterministic and suitable for early declarative ownership.",
    ),
    "cli-registry": DeclarativeGroupDescriptor(
        group_id="cli-registry",
        domain="interface.cli",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_post_h_006_e_cli_no_growth_gate.py tests/test_post_h_006_d_cli_hotspot_ownership.py tests/test_post_h_006_cli_command_registry.py -q",),
        rationale="CLI registry commands govern the command surface and must be registered before enforcing no-growth gates.",
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
    "audit-pack": DeclarativeGroupDescriptor(
        group_id="audit-pack",
        domain="operations.audit",
        owner_module="src/devpilot_core/cli.py",
        recommended_tests=("python -m pytest tests/test_audit_pack_v2.py tests/test_audit_pack_integrity_gate.py -q",),
        rationale="POST-H-013 audit-pack v2 commands are governed local audit surfaces with explicit dry-run/execute semantics and must be registered before the no-growth gate runs.",
    ),
}


COMMAND_OVERRIDES: dict[str, DeclarativeCommandOverride] = {
    "workspace.init": DeclarativeCommandOverride(
        command_id="workspace.init",
        risk_level=CommandRiskLevel.HIGH,
        side_effects=(CommandSideEffect.MUTATE_STATE, CommandSideEffect.WRITE_FILES, CommandSideEffect.WRITE_REPORT),
        writes_files=True,
        dry_run_supported=True,
        policy_check_required=True,
        rationale="`workspace init --execute` can create local workspace files; dry-run remains default and policy metadata is mandatory.",
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
            "declared_by": POST_H_006_C_CREATED_BY if migration else POST_H_006_B_CREATED_BY,
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
        if migration:
            metadata.update(
                {
                    "migrated_by": POST_H_006_C_CREATED_BY,
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
