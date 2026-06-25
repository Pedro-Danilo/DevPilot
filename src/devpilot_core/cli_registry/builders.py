from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_registry.models import (
    CliCommandRegistry,
    CommandDescriptor,
    CommandGroupDescriptor,
    CommandOptionDescriptor,
    CommandRiskLevel,
    CommandSideEffect,
)

CLI_REGISTRY_SCHEMA_ID = "SCHEMA-DEVPL-CLI-COMMAND-REGISTRY-V1"
CLI_REGISTRY_CONTRACT = "CliCommandRegistry"
DEFAULT_CLI_SOURCE = Path("src/devpilot_core/cli.py")
DEFAULT_TOP_LEVEL_TESTS = {
    "architecture": "python -m pytest tests/test_architecture_map_report.py tests/test_architecture_hotspots.py tests/test_architecture_dependencies.py tests/test_architecture_inventory.py tests/test_post_h_005_architecture_map.py -q",
    "schema": "python -m pytest tests/test_schema_registry.py -q",
    "validate": "python -m pytest tests/test_validation_gateway.py -q",
    "workspace": "python -m pytest tests/test_workspace_manager.py -q",
    "quality-gate": "python -m pytest tests/test_quality_gate.py -q",
    "test-contracts": "python -m pytest tests/test_test_contract_registry.py tests/test_test_contract_registry_v2.py -q",
    "policy": "python -m pytest tests/test_policy_engine.py -q",
    "miasi": "python -m pytest tests/test_miasi_registry.py tests/test_miasi_semantic_validator.py -q",
    "project-state": "python -m pytest tests/test_project_global_state.py -q",
    "industrial-readiness": "python -m pytest tests/test_industrial_readiness.py -q",
}

DOMAIN_BY_GROUP = {
    "api": "product.api",
    "app": "application.service",
    "architecture": "interface.cli",
    "approval": "security.approval",
    "audit-pack": "operations.audit",
    "backup": "release",
    "checklist-pre-code": "documentation.governance",
    "compliance": "governance.compliance",
    "connector": "integration.connectors",
    "enterprise": "enterprise.reporting",
    "eval": "governance.testing",
    "history": "operations.observability",
    "identity": "security.rbac",
    "industrial-readiness": "quality.gate",
    "install": "release",
    "maturity": "quality.gate",
    "metrics": "operations.observability",
    "miasi": "governance.miasi",
    "model": "agentic.runtime",
    "multiagent": "agentic.multiagent",
    "package": "release",
    "patch": "quality.gate",
    "plugin": "extensibility.plugins",
    "policy": "governance.policy",
    "portfolio": "operations.workspace",
    "prompt": "agentic.runtime",
    "quality-gate": "quality.gate",
    "rag": "knowledge.rag",
    "readiness-check": "documentation.governance",
    "release": "release",
    "remote": "enterprise.remote",
    "repo": "quality.gate",
    "schema": "governance.schemas",
    "security": "security.guards",
    "standards": "documentation.governance",
    "state": "governance.project_state",
    "test-contracts": "governance.testing",
    "tests": "governance.testing",
    "trace": "operations.observability",
    "traceability": "documentation.governance",
    "upgrade": "release",
    "validate": "documentation.governance",
    "validate-artifact": "documentation.governance",
    "validate-frontmatter": "documentation.governance",
    "workspace": "operations.workspace",
}

HIGH_RISK_GROUPS = {"backup", "package", "patch", "release", "remote", "connector", "plugin", "api", "tests"}
CRITICAL_GROUPS = {"remote", "connector", "plugin"}
POLICY_REQUIRED_GROUPS = {"policy", "approval", "security", "connector", "plugin", "remote", "patch", "backup", "package"}


@dataclass(frozen=True)
class StaticCliInventoryOptions:
    """Options for the POST-H-006-A static CLI registry extractor."""

    cli_source: Path = DEFAULT_CLI_SOURCE
    write_report: bool = False
    output_json: Path = Path("outputs/reports/cli_command_registry.json")
    output_markdown: Path = Path("outputs/reports/cli_command_registry.md")


class StaticCliInventoryExtractor:
    """Parse `cli.py` without importing or executing the CLI parser.

    The extractor intentionally operates on the AST instead of calling
    `build_parser()`: POST-H-006-A is a read-only architecture inventory sprint,
    and importing parser code would pull many domain modules into the test path.
    """

    def __init__(self, root: Path, options: StaticCliInventoryOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or StaticCliInventoryOptions()
        self.cli_source = self.root / self.options.cli_source

    def build_registry(self) -> CliCommandRegistry:
        source = self.cli_source.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(self.options.cli_source))
        parser_paths, parser_options = self._extract_parser_paths_and_options(tree)
        dispatch_handlers = self._extract_dispatch_handlers(tree)

        descriptors = self._build_descriptors(parser_paths, parser_options, dispatch_handlers)
        groups = self._group_descriptors(descriptors)
        summary = self._summary(groups, descriptors)
        registry = CliCommandRegistry(
            schema_version="1.0",
            schema_id=CLI_REGISTRY_SCHEMA_ID,
            registry_id="devpilot-cli-command-registry",
            generated_from="static-cli-parser-ast",
            created_by="POST-H-006-A",
            groups=groups,
            summary=summary,
            safety={
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
                "Use this registry as the baseline for POST-H-006-B declarative descriptors.",
                "Move only low-risk validation/workspace handlers in POST-H-006-C after parity tests exist.",
                "Keep cli.py public command names stable until registry coverage and parity are reviewed.",
            ],
            metadata={
                "cli_source": str(self.options.cli_source).replace("\\", "/"),
                "owner_module": str(self.options.cli_source).replace("\\", "/"),
                "advisory_only": True,
                "no_runtime_behavior_changed": True,
            },
        )
        return registry

    def _extract_parser_paths_and_options(self, tree: ast.AST) -> tuple[dict[str, tuple[str, ...]], dict[str, list[CommandOptionDescriptor]]]:
        parser_paths: dict[str, tuple[str, ...]] = {"parser": ()}
        subparser_parents: dict[str, tuple[str, ...]] = {}
        parser_options: dict[str, list[CommandOptionDescriptor]] = defaultdict(list)

        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.Expr)):
                continue
            call = node.value if isinstance(node, ast.Expr) else node.value
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
                continue

            method = call.func.attr
            receiver = _name_of(call.func.value)
            target = _first_target_name(node) if isinstance(node, ast.Assign) else None

            if method == "add_subparsers" and target and receiver in parser_paths:
                subparser_parents[target] = parser_paths[receiver]
                continue

            if method == "add_parser" and target and receiver in subparser_parents:
                command_name = _literal_arg(call, 0)
                if command_name:
                    parser_paths[target] = (*subparser_parents[receiver], command_name)
                continue

            if method == "add_argument" and receiver in parser_paths:
                option = _option_from_call(call)
                if option is not None:
                    parser_options[receiver].append(option)
                continue

        return parser_paths, parser_options

    def _extract_dispatch_handlers(self, tree: ast.AST) -> dict[tuple[str, ...], str]:
        handlers: dict[tuple[str, ...], str] = {}
        dispatch = next((node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_dispatch"), None)
        if dispatch is None:
            return handlers

        def visit_statements(statements: list[ast.stmt], active_path: tuple[str, ...] = ()) -> None:
            for stmt in statements:
                if isinstance(stmt, ast.If):
                    condition_path = _command_path_from_condition(stmt.test)
                    next_path = condition_path or active_path
                    handler = _first_return_call_name(stmt.body)
                    if handler and next_path:
                        handlers[next_path] = handler
                    visit_statements(stmt.body, next_path)
                    visit_statements(stmt.orelse, active_path)

        visit_statements(dispatch.body)
        return handlers

    def _build_descriptors(
        self,
        parser_paths: dict[str, tuple[str, ...]],
        parser_options: dict[str, list[CommandOptionDescriptor]],
        dispatch_handlers: dict[tuple[str, ...], str],
    ) -> list[CommandDescriptor]:
        children: set[tuple[str, ...]] = set()
        for path in parser_paths.values():
            if len(path) > 1:
                children.add(path[:-1])
        leaf_paths = sorted(path for path in parser_paths.values() if path and path not in children)

        descriptors: list[CommandDescriptor] = []
        path_to_parser_var = {path: var for var, path in parser_paths.items()}
        for path in leaf_paths:
            parser_var = path_to_parser_var.get(path)
            options = parser_options.get(parser_var or "", [])
            group_id = path[0]
            side_effects = _side_effects_for(path, options)
            writes_files = any(item in side_effects for item in (CommandSideEffect.WRITE_REPORT, CommandSideEffect.WRITE_FILES, CommandSideEffect.MUTATE_STATE))
            dry_run_supported = any("--dry-run" in option.option_strings for option in options) or "dry-run" in " ".join(path)
            descriptor = CommandDescriptor(
                command_id=".".join(path),
                command_path=list(path),
                public_invocation="python -m devpilot_core " + " ".join(path),
                group_id=group_id,
                domain=DOMAIN_BY_GROUP.get(group_id, "interface.cli"),
                owner_module=str(self.options.cli_source).replace("\\", "/"),
                handler=dispatch_handlers.get(path) or _fallback_handler_name(path),
                risk_level=_risk_for(group_id, side_effects),
                side_effects=side_effects,
                writes_files=writes_files,
                dry_run_supported=dry_run_supported,
                policy_check_required=group_id in POLICY_REQUIRED_GROUPS,
                recommended_tests=_recommended_tests_for(group_id),
                options=options,
                metadata={
                    "parser_path_depth": len(path),
                    "handler_inferred": path not in dispatch_handlers,
                    "registry_phase": "static-inventory",
                },
            )
            descriptors.append(descriptor)
        return descriptors

    def _group_descriptors(self, descriptors: list[CommandDescriptor]) -> list[CommandGroupDescriptor]:
        grouped: dict[str, list[CommandDescriptor]] = defaultdict(list)
        for descriptor in descriptors:
            grouped[descriptor.group_id].append(descriptor)

        groups: list[CommandGroupDescriptor] = []
        for group_id in sorted(grouped):
            commands = sorted(grouped[group_id], key=lambda item: item.command_id)
            risk = _max_risk([command.risk_level for command in commands])
            groups.append(
                CommandGroupDescriptor(
                    group_id=group_id,
                    domain=DOMAIN_BY_GROUP.get(group_id, "interface.cli"),
                    owner_module=str(self.options.cli_source).replace("\\", "/"),
                    risk_level=risk,
                    application_service_required=group_id in {"workspace", "validate", "quality-gate", "app", "api", "maturity"},
                    commands=commands,
                )
            )
        return groups

    def _summary(self, groups: list[CommandGroupDescriptor], descriptors: list[CommandDescriptor]) -> dict[str, Any]:
        top_level = [command for command in descriptors if len(command.command_path) == 1]
        nested = [command for command in descriptors if len(command.command_path) > 1]
        return {
            "groups_total": len(groups),
            "commands_total": len(descriptors),
            "top_level_commands_total": len(top_level),
            "nested_commands_total": len(nested),
            "commands_with_json_flag_total": sum(1 for command in descriptors if any("--json" in option.option_strings for option in command.options)),
            "commands_with_write_report_total": sum(1 for command in descriptors if any("--write-report" in option.option_strings for option in command.options)),
            "commands_with_dry_run_total": sum(1 for command in descriptors if command.dry_run_supported),
            "commands_requiring_policy_total": sum(1 for command in descriptors if command.policy_check_required),
            "high_or_critical_risk_commands_total": sum(1 for command in descriptors if command.risk_level in {CommandRiskLevel.HIGH, CommandRiskLevel.CRITICAL}),
            "legacy_cli_owned_commands_total": sum(1 for command in descriptors if command.legacy_cli_owned),
            "dynamic_handler_loading_enabled": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "advisory_only": True,
            "preliminary": True,
        }


def _name_of(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    return None


def _first_target_name(node: ast.Assign) -> str | None:
    if not node.targets:
        return None
    target = node.targets[0]
    if isinstance(target, ast.Name):
        return target.id
    return None


def _literal_arg(call: ast.Call, index: int) -> str | None:
    if len(call.args) <= index:
        return None
    value = call.args[index]
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    return None


def _literal_keyword(call: ast.Call, name: str) -> Any | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return _literal_value(keyword.value)
    return None


def _literal_value(node: ast.AST) -> Any | None:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_literal_value(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return [_literal_value(item) for item in node.elts]
    return None


def _option_from_call(call: ast.Call) -> CommandOptionDescriptor | None:
    strings = [arg.value for arg in call.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
    if not strings:
        return None
    option_strings = [item for item in strings if item.startswith("-")]
    name_source = option_strings[-1] if option_strings else strings[0]
    name = name_source.lstrip("-").replace("-", "_")
    action = _literal_keyword(call, "action")
    default = _literal_keyword(call, "default")
    help_text = _literal_keyword(call, "help")
    required = bool(_literal_keyword(call, "required"))
    return CommandOptionDescriptor(
        name=name,
        option_strings=option_strings,
        required=required,
        action=action if isinstance(action, str) else None,
        default=default,
        help=help_text if isinstance(help_text, str) else None,
    )


def _command_path_from_condition(node: ast.AST) -> tuple[str, ...] | None:
    if not isinstance(node, ast.Compare) or len(node.ops) != 1 or not isinstance(node.ops[0], ast.Eq) or len(node.comparators) != 1:
        return None
    right = node.comparators[0]
    value = right.value if isinstance(right, ast.Constant) and isinstance(right.value, str) else None
    if not value:
        return None
    left = node.left
    if isinstance(left, ast.Attribute) and isinstance(left.value, ast.Name) and left.value.id == "args":
        attr = left.attr
        if attr == "command":
            return (value,)
        if attr.endswith("_command"):
            group = attr.removesuffix("_command").replace("_", "-")
            return (group, value)
        if attr == "remote_runner_command":
            return ("remote", "runner", value)
    return None


def _first_return_call_name(statements: list[ast.stmt]) -> str | None:
    for stmt in statements:
        if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
            func = stmt.value.func
            if isinstance(func, ast.Name):
                return func.id
    return None


def _fallback_handler_name(path: tuple[str, ...]) -> str:
    return "legacy_dispatch::" + "_".join(part.replace("-", "_") for part in path)


def _side_effects_for(path: tuple[str, ...], options: list[CommandOptionDescriptor]) -> list[CommandSideEffect]:
    option_strings = {flag for option in options for flag in option.option_strings}
    group = path[0]
    effects: set[CommandSideEffect] = set()
    if "--write-report" in option_strings:
        effects.add(CommandSideEffect.WRITE_REPORT)
    if "--execute" in option_strings or "--confirm-restore" in option_strings:
        effects.add(CommandSideEffect.MUTATE_STATE)
    if group in {"backup", "package", "patch", "tests", "api"}:
        effects.add(CommandSideEffect.EXECUTE_SUBPROCESS if group == "tests" else CommandSideEffect.WRITE_FILES)
    if group in {"connector", "remote", "plugin"}:
        effects.add(CommandSideEffect.POTENTIAL_NETWORK)
    if not effects:
        effects.add(CommandSideEffect.NONE)
    return sorted(effects, key=lambda item: item.value)


def _risk_for(group_id: str, side_effects: list[CommandSideEffect]) -> CommandRiskLevel:
    if group_id in CRITICAL_GROUPS:
        return CommandRiskLevel.CRITICAL
    if group_id in HIGH_RISK_GROUPS or CommandSideEffect.MUTATE_STATE in side_effects:
        return CommandRiskLevel.HIGH
    if any(effect in side_effects for effect in (CommandSideEffect.WRITE_FILES, CommandSideEffect.EXECUTE_SUBPROCESS, CommandSideEffect.POTENTIAL_NETWORK)):
        return CommandRiskLevel.HIGH
    if CommandSideEffect.WRITE_REPORT in side_effects:
        return CommandRiskLevel.MEDIUM
    return CommandRiskLevel.LOW


def _max_risk(risks: list[CommandRiskLevel]) -> CommandRiskLevel:
    order = {CommandRiskLevel.LOW: 1, CommandRiskLevel.MEDIUM: 2, CommandRiskLevel.HIGH: 3, CommandRiskLevel.CRITICAL: 4}
    return max(risks, key=lambda risk: order[risk]) if risks else CommandRiskLevel.LOW


def _recommended_tests_for(group_id: str) -> list[str]:
    if group_id in DEFAULT_TOP_LEVEL_TESTS:
        return [DEFAULT_TOP_LEVEL_TESTS[group_id]]
    return ["python -m pytest tests/test_post_h_006_cli_command_registry.py -q"]
