
from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.cli_registry.registry import APPLICATION_OPERATION_BY_COMMAND_ID, DeclarativeCliRegistryBuilder

POST_H_030_A_CREATED_BY = "POST-H-030-A"
CLI_COMMAND_OWNERSHIP_MATRIX_SCHEMA_ID = "SCHEMA-DEVPL-CLI-COMMAND-OWNERSHIP-MATRIX-V1"
CLI_EXTRACTION_PLAN_SCHEMA_ID = "SCHEMA-DEVPL-CLI-EXTRACTION-PLAN-V1"
CLI_COMMAND_OWNERSHIP_MATRIX_CONTRACT = "CliCommandOwnershipMatrix"
CLI_EXTRACTION_PLAN_CONTRACT = "CliExtractionPlan"
DEFAULT_OWNERSHIP_MATRIX_PATH = Path(".devpilot/cli_registry/command_ownership_matrix.json")
DEFAULT_EXTRACTION_PLAN_PATH = Path(".devpilot/cli_registry/cli_extraction_plan.json")

POST_H_030_TARGET_MODULES: dict[str, tuple[str, str, str]] = {
    "industrial-readiness": ("src/devpilot_core/cli_commands/industrial_readiness.py", "POST-H-030-B", "quality.gate"),
    "release": ("src/devpilot_core/cli_commands/release.py", "POST-H-030-C", "release"),
    "release-candidate": ("src/devpilot_core/cli_commands/release.py", "POST-H-030-C", "release"),
    "package": ("src/devpilot_core/cli_commands/release.py", "POST-H-030-C", "release"),
    "install": ("src/devpilot_core/cli_commands/release.py", "POST-H-030-C", "release"),
    "backup": ("src/devpilot_core/cli_commands/release.py", "POST-H-030-C", "release"),
    "upgrade": ("src/devpilot_core/cli_commands/release.py", "POST-H-030-C", "release"),
    "workspace": ("src/devpilot_core/cli_commands/workspace.py", "POST-H-030-D", "operations.workspace"),
    "portfolio": ("src/devpilot_core/cli_commands/workspace_onboarding.py", "POST-H-030-D", "operations.workspace"),
}

CLI_ONLY_GROUPS = {
    "cli-registry",
    "schema",
    "test-contracts",
    "tests",
    "test-impact",
    "quality-gate",
    "docs-governance",
    "project-state",
}


@dataclass(frozen=True)
class CliCommandOwnershipOptions:
    matrix_path: Path = DEFAULT_OWNERSHIP_MATRIX_PATH
    plan_path: Path = DEFAULT_EXTRACTION_PLAN_PATH


class CliCommandOwnershipMatrixBuilder:
    """Build and validate POST-H-030-A CLI ownership metadata.

    The builder reads the static DeclarativeCliRegistry only. It does not call
    public commands, does not import handler target strings dynamically and does
    not change CLI runtime behavior.
    """

    def __init__(self, root: Path, options: CliCommandOwnershipOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or CliCommandOwnershipOptions()

    def build(self) -> tuple[dict[str, Any], dict[str, Any]]:
        registry = DeclarativeCliRegistryBuilder(self.root).build_registry().to_dict()
        commands = _flatten_commands(registry)
        matrix_commands = [self._command_record(command) for command in commands]
        plan = self._build_plan(matrix_commands)
        summary = self._matrix_summary(matrix_commands)
        matrix = {
            "schema_version": "1.0",
            "schema_id": CLI_COMMAND_OWNERSHIP_MATRIX_SCHEMA_ID,
            "matrix_id": "devpilot-cli-command-ownership-matrix",
            "created_by": POST_H_030_A_CREATED_BY,
            "status": "implemented-initial",
            "version": "1.0.0",
            "updated": "2026-07-09",
            "generated_from": "DeclarativeCliRegistryBuilder",
            "registry_path": "src/devpilot_core/cli_registry/registry.py",
            "cli_source": "src/devpilot_core/cli.py",
            "summary": summary,
            "commands": matrix_commands,
            "safety": _safety(),
            "notes": [
                "POST-H-030-A is metadata-only and does not migrate handlers.",
                "Every public CLI command discovered by the declarative registry is represented once.",
                "Commands planned for POST-H-030-B/C/D keep public invocation, JSON envelope and exit-code contracts unchanged.",
                "CLI-only commands are justified until compatibility contracts and deeper extraction decisions are implemented in later micro-sprints.",
            ],
        }
        return matrix, plan

    def write(self) -> tuple[dict[str, Any], dict[str, Any]]:
        matrix, plan = self.build()
        matrix_path = self.root / self.options.matrix_path
        plan_path = self.root / self.options.plan_path
        matrix_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        matrix_path.write_text(json.dumps(matrix, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return matrix, plan

    def validate(self, matrix: dict[str, Any] | None = None, plan: dict[str, Any] | None = None) -> CommandResult:
        if matrix is None or plan is None:
            matrix, plan = self.build()
        findings: list[Finding] = []
        commands = matrix.get("commands", [])
        command_ids = [item.get("command_id") for item in commands]
        duplicates = sorted(_duplicates(command_ids))
        missing_owner = [item.get("command_id") for item in commands if not item.get("domain_owner")]
        missing_contract = [item.get("command_id") for item in commands if not item.get("compatibility_contract_id")]
        high_without_owner = [
            item.get("command_id")
            for item in commands
            if item.get("risk_level") in {"high", "critical"} and not item.get("domain_owner")
        ]
        planned_modules = {item.get("module_path") for item in plan.get("target_modules", [])}
        missing_target_plan = [
            item.get("command_id")
            for item in commands
            if item.get("migration_state") == "planned"
            and item.get("target_module")
            and not (self.root / item.get("target_module")).exists()
            and item.get("target_module") not in planned_modules
        ]
        invalid_non_migrable = [
            item.get("command_id")
            for item in commands
            if item.get("migration_state") == "deferred-cli-only" and not item.get("cli_only_reason")
        ]
        invented_app_ops = [
            item.get("command_id")
            for item in commands
            if item.get("application_operation_id") and item.get("application_operation_id") != APPLICATION_OPERATION_BY_COMMAND_ID.get(item.get("command_id"))
        ]
        for fid, values, message in [
            ("CLI_OWNERSHIP_DUPLICATE_COMMANDS", duplicates, "Ownership matrix contains duplicate command ids."),
            ("CLI_OWNERSHIP_MISSING_OWNER", missing_owner, "Ownership matrix contains commands without owner."),
            ("CLI_OWNERSHIP_MISSING_CONTRACT", missing_contract, "Ownership matrix contains commands without compatibility contract."),
            ("CLI_OWNERSHIP_HIGH_RISK_WITHOUT_OWNER", high_without_owner, "High/critical commands must have explicit owners."),
            ("CLI_OWNERSHIP_MISSING_TARGET_PLAN", missing_target_plan, "Planned target module is missing and not represented in the extraction plan."),
            ("CLI_OWNERSHIP_CLI_ONLY_REASON_MISSING", invalid_non_migrable, "Deferred CLI-only command lacks justification."),
            ("CLI_OWNERSHIP_INVENTED_APPLICATION_OPERATION", invented_app_ops, "ApplicationOperation mapping must reference an existing static mapping only."),
        ]:
            if values:
                findings.append(Finding(id=fid, message=message, severity=Severity.BLOCK, metadata={"command_ids": values}))
        if not findings:
            findings.append(Finding(id="CLI_OWNERSHIP_MATRIX_PASS", message="CLI ownership matrix is complete and compatible with the extraction plan.", severity=Severity.INFO, metadata={"commands_total": len(commands)}))
        blocking = sum(1 for finding in findings if finding.severity == Severity.BLOCK)
        summary = {
            "created_by": POST_H_030_A_CREATED_BY,
            "status": "implemented-initial",
            "decision": "PASS" if blocking == 0 else "BLOCK",
            "commands_total": len(commands),
            "plan_items_total": len(plan.get("plan_items", [])),
            "target_modules_total": len(plan.get("target_modules", [])),
            "duplicate_commands_total": len(duplicates),
            "missing_owner_total": len(missing_owner),
            "missing_compatibility_contract_total": len(missing_contract),
            "missing_target_plan_total": len(missing_target_plan),
            "cli_only_reason_missing_total": len(invalid_non_migrable),
            "invented_application_operation_total": len(invented_app_ops),
            "blocking_findings_total": blocking,
            "tests_executed": False,
            "dry_run": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        return CommandResult(
            command="cli-registry ownership-matrix",
            ok=blocking == 0,
            exit_code=ExitCode.PASS if blocking == 0 else ExitCode.BLOCK,
            message="CLI ownership matrix passed." if blocking == 0 else "CLI ownership matrix blocked.",
            data={"summary": summary, "matrix": matrix, "plan": plan},
            findings=findings,
        )

    def _command_record(self, command: dict[str, Any]) -> dict[str, Any]:
        command_id = command["command_id"]
        group_id = command["group_id"]
        phase = command.get("metadata", {}).get("registry_phase", "static-inventory")
        current_module = command.get("owner_module") or "src/devpilot_core/cli.py"
        target_module, planned_micro_sprint, domain_owner = _target_for(command)
        already_migrated = phase == "handler-migrated-incremental"
        if already_migrated:
            migration_state = "already-migrated"
        elif group_id in POST_H_030_TARGET_MODULES:
            migration_state = "planned"
        elif phase == "declarative-initial":
            migration_state = "registered-only"
        else:
            migration_state = "deferred-cli-only"
        app_operation = APPLICATION_OPERATION_BY_COMMAND_ID.get(command_id)
        cli_only_reason = None if app_operation else _cli_only_reason(command, migration_state)
        return {
            "command_id": command_id,
            "command_path": command.get("command_path", []),
            "public_name": command.get("public_invocation", "python -m devpilot_core " + command_id.replace(".", " ")),
            "domain_owner": domain_owner,
            "current_handler": command.get("handler") or "legacy_dispatch::unknown",
            "target_handler": _target_handler(command),
            "current_module": current_module,
            "target_module": target_module,
            "registry_phase": phase,
            "migration_state": migration_state,
            "application_operation_id": app_operation,
            "cli_only_reason": cli_only_reason,
            "risk_level": command.get("risk_level", "medium"),
            "compatibility_contract_id": f"cli-compat:{command_id}",
            "json_output_contract": "Preserve CommandResult JSON envelope: command, ok, exit_code, message, data and findings when --json is supported.",
            "exit_code_contract": "Preserve PASS=0, FAIL=1 and BLOCK=2 semantics exposed by existing CommandResult/ExitCode mapping.",
            "human_output_contract": "Preserve current command name, operator-facing PASS/BLOCK/FAIL wording and help surface unless POST-H-030-E contract explicitly approves a change.",
            "test_coverage_refs": command.get("recommended_tests") or ["python -m pytest tests/test_post_h_006_cli_command_registry.py -q"],
            "planned_micro_sprint": planned_micro_sprint,
            "side_effects": command.get("side_effects", []),
            "writes_files": command.get("writes_files", False),
            "dry_run_supported": command.get("dry_run_supported", False),
            "policy_check_required": command.get("policy_check_required", False),
            "notes": _notes_for(command, migration_state),
        }

    def _matrix_summary(self, commands: list[dict[str, Any]]) -> dict[str, Any]:
        high = [item for item in commands if item.get("risk_level") in {"high", "critical"}]
        state_counts = Counter(item.get("migration_state") for item in commands)
        phase_counts = Counter(item.get("registry_phase") for item in commands)
        return {
            "commands_total": len(commands),
            "commands_covered_total": len(commands),
            "coverage_complete": True,
            "registry_phase_counts": dict(sorted(phase_counts.items())),
            "migration_state_counts": dict(sorted(state_counts.items())),
            "high_or_critical_commands_total": len(high),
            "high_or_critical_with_owner_total": sum(1 for item in high if item.get("domain_owner")),
            "missing_owner_total": 0,
            "missing_compatibility_contract_total": 0,
            "migrable_commands_total": state_counts.get("planned", 0) + state_counts.get("already-migrated", 0),
            "cli_only_commands_total": state_counts.get("deferred-cli-only", 0),
            "dynamic_handler_loading_enabled": False,
            "runtime_router_enabled": False,
            "public_behavior_changes_allowed": False,
            "tests_executed": False,
            "network_used": False,
            "external_api_used": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }

    def _build_plan(self, commands: list[dict[str, Any]]) -> dict[str, Any]:
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for command in commands:
            if command["migration_state"] in {"planned", "already-migrated"}:
                grouped[(command["planned_micro_sprint"], command["target_module"])].append(command)
        plan_items: list[dict[str, Any]] = []
        target_modules: dict[str, dict[str, Any]] = {}
        for (sprint, module), items in sorted(grouped.items()):
            domain_owner = _common_domain(items)
            target_modules[module] = {
                "module_path": module,
                "planned_micro_sprint": sprint,
                "exists_now": (self.root / module).exists(),
                "creation_required": not (self.root / module).exists(),
                "domain_owner": domain_owner,
                "purpose": _purpose_for_module(module, sprint),
            }
            risk_level = _max_risk(item.get("risk_level", "medium") for item in items)
            plan_items.append({
                "plan_id": f"{sprint.lower()}:{module}",
                "planned_micro_sprint": sprint,
                "domain_owner": domain_owner,
                "target_module": module,
                "command_ids": sorted(item["command_id"] for item in items),
                "migration_goal": _migration_goal_for(sprint, module),
                "compatibility_strategy": "Keep command names, arguments, JSON envelope, exit codes and operator-facing messages stable; POST-H-030-E will snapshot observable contracts.",
                "application_boundary_strategy": "Use existing ApplicationService/ApplicationOperation mapping when present; otherwise keep CLI-only rationale explicit until a later ADR or boundary story exists.",
                "risk_level": risk_level,
                "status": "already-started" if all(item["migration_state"] == "already-migrated" for item in items) else "planned",
            })
        return {
            "schema_version": "1.0",
            "schema_id": CLI_EXTRACTION_PLAN_SCHEMA_ID,
            "plan_id": "devpilot-cli-extraction-plan",
            "created_by": POST_H_030_A_CREATED_BY,
            "status": "implemented-initial",
            "version": "1.0.0",
            "updated": "2026-07-09",
            "summary": {
                "planned_items_total": len(plan_items),
                "target_modules_total": len(target_modules),
                "commands_referenced_total": sum(len(item["command_ids"]) for item in plan_items),
                "dynamic_handler_loading_enabled": False,
                "runtime_router_enabled": False,
                "public_behavior_changes_allowed": False,
                "tests_executed": False,
                "network_used": False,
                "external_api_used": False,
                "source_mutations_performed": False,
                "preliminary": True,
            },
            "target_modules": sorted(target_modules.values(), key=lambda item: (item["planned_micro_sprint"], item["module_path"])),
            "plan_items": plan_items,
            "safety": _safety(),
            "notes": [
                "POST-H-030-A creates an extraction plan only; behavior migration starts in POST-H-030-B.",
                "Missing target modules are acceptable only when listed as creation_required in this plan.",
                "No dynamic router or handler-loading mechanism is introduced by this plan.",
            ],
        }


def _flatten_commands(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return [command for group in registry.get("groups", []) for command in group.get("commands", [])]


def _target_for(command: dict[str, Any]) -> tuple[str, str, str]:
    group = command.get("group_id", "interface")
    phase = command.get("metadata", {}).get("registry_phase")
    if phase == "handler-migrated-incremental":
        module = command.get("owner_module") or "src/devpilot_core/cli.py"
        migrated_by = command.get("metadata", {}).get("migrated_by")
        if migrated_by == "POST-H-030-B":
            return module, "POST-H-030-B", command.get("domain", "interface.cli")
        if migrated_by == "POST-H-030-C":
            return module, "POST-H-030-C", command.get("domain", "interface.cli")
        if migrated_by == "POST-H-030-D":
            return module, "POST-H-030-D", command.get("domain", "interface.cli")
        return module, "POST-H-030-A", command.get("domain", "interface.cli")
    if group in POST_H_030_TARGET_MODULES:
        return POST_H_030_TARGET_MODULES[group]
    return command.get("owner_module") or "src/devpilot_core/cli.py", "POST-H-030-E", command.get("domain", "interface.cli")


def _target_handler(command: dict[str, Any]) -> str:
    command_id = command.get("command_id", "unknown")
    base = "handle_" + command_id.replace(".", "_").replace("-", "_")
    phase = command.get("metadata", {}).get("registry_phase")
    return command.get("handler") if phase == "handler-migrated-incremental" else base


def _cli_only_reason(command: dict[str, Any], migration_state: str) -> str:
    group = command.get("group_id")
    if migration_state == "planned":
        return "ApplicationService mapping is not required yet; command will first move to a domain-owned CLI module with compatibility tests."
    if group in CLI_ONLY_GROUPS:
        return "Governance/registry/testing command is currently CLI-only and metadata-driven; no API/UI operation boundary is required in POST-H-030-A."
    return "No existing ApplicationOperation mapping is registered; keep explicit CLI-only rationale until a future boundary story or ADR introduces one."


def _notes_for(command: dict[str, Any], migration_state: str) -> list[str]:
    notes = ["No runtime behavior change in POST-H-030-A."]
    if migration_state == "planned":
        notes.append("Handler extraction is planned but not performed in POST-H-030-A.")
    if command.get("risk_level") in {"high", "critical"}:
        notes.append("High/critical command requires explicit compatibility contract before migration.")
    return notes


def _common_domain(items: list[dict[str, Any]]) -> str:
    counts = Counter(item.get("domain_owner", "interface.cli") for item in items)
    return counts.most_common(1)[0][0]


def _purpose_for_module(module: str, sprint: str) -> str:
    if sprint == "POST-H-030-B":
        return "Own industrial/production readiness CLI handlers while preserving claims/no-go behavior."
    if sprint == "POST-H-030-C":
        return "Own release, package, install and reproducibility CLI handlers while preserving local-first release contracts."
    if sprint == "POST-H-030-D":
        return "Own workspace/onboarding CLI handlers while preserving dry-run and ApplicationService boundary candidates."
    return "Existing or future compatibility boundary for CLI command ownership."


def _migration_goal_for(sprint: str, module: str) -> str:
    if sprint == "POST-H-030-A":
        return "Document already migrated handlers and keep them in the ownership baseline."
    if sprint == "POST-H-030-B":
        return "Extract industrial readiness handlers from cli.py into a domain-owned module."
    if sprint == "POST-H-030-C":
        return "Extract release/package/install handlers from cli.py into a domain-owned release module."
    if sprint == "POST-H-030-D":
        return "Extract workspace/onboarding handlers or consolidate existing workspace command ownership."
    return "Keep CLI-only commands under compatibility contracts before future refactor."


def _max_risk(risks: Any) -> str:
    order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    values = list(risks)
    return max(values, key=lambda item: order.get(item, 0)) if values else "medium"


def _duplicates(values: list[Any]) -> list[Any]:
    seen = set()
    duplicates = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _safety() -> dict[str, Any]:
    return {
        "local_first": True,
        "read_only": True,
        "dry_run": True,
        "commands_executed": False,
        "dynamic_handler_loading_enabled": False,
        "runtime_router_enabled": False,
        "network_used": False,
        "external_api_used": False,
        "remote_execution_enabled": False,
        "connector_write_enabled": False,
        "plugin_execution_enabled": False,
        "source_mutations_performed": False,
        "preliminary": True,
    }
