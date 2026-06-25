from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CommandRiskLevel(str, Enum):
    """Coarse operational risk class for registered CLI commands."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CommandSideEffect(str, Enum):
    """Declared side effects for static CLI inventory entries."""

    NONE = "none"
    WRITE_REPORT = "write-report"
    WRITE_FILES = "write-files"
    MUTATE_STATE = "mutate-state"
    EXECUTE_SUBPROCESS = "execute-subprocess"
    POTENTIAL_NETWORK = "potential-network"


@dataclass(frozen=True)
class CommandOptionDescriptor:
    """Static description of a parser option or positional argument."""

    name: str
    option_strings: list[str] = field(default_factory=list)
    required: bool = False
    action: str | None = None
    default: Any | None = None
    help: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "option_strings": list(self.option_strings),
            "required": self.required,
        }
        if self.action is not None:
            data["action"] = self.action
        if self.default is not None:
            data["default"] = self.default
        if self.help:
            data["help"] = self.help
        return data


@dataclass(frozen=True)
class CommandDescriptor:
    """Machine-readable static descriptor for one public CLI command path."""

    command_id: str
    command_path: list[str]
    public_invocation: str
    group_id: str
    domain: str
    owner_module: str
    handler: str
    returns: str = "CommandResult"
    risk_level: CommandRiskLevel = CommandRiskLevel.MEDIUM
    side_effects: list[CommandSideEffect] = field(default_factory=lambda: [CommandSideEffect.NONE])
    writes_files: bool = False
    dry_run_supported: bool = False
    policy_check_required: bool = False
    recommended_tests: list[str] = field(default_factory=list)
    options: list[CommandOptionDescriptor] = field(default_factory=list)
    legacy_cli_owned: bool = True
    remote_execution_enabled: bool = False
    connector_write_enabled: bool = False
    plugin_execution_enabled: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "command_path": list(self.command_path),
            "public_invocation": self.public_invocation,
            "group_id": self.group_id,
            "domain": self.domain,
            "owner_module": self.owner_module,
            "handler": self.handler,
            "returns": self.returns,
            "risk_level": self.risk_level.value,
            "side_effects": [item.value for item in self.side_effects],
            "writes_files": self.writes_files,
            "dry_run_supported": self.dry_run_supported,
            "policy_check_required": self.policy_check_required,
            "recommended_tests": list(self.recommended_tests),
            "options": [option.to_dict() for option in self.options],
            "legacy_cli_owned": self.legacy_cli_owned,
            "remote_execution_enabled": self.remote_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "plugin_execution_enabled": self.plugin_execution_enabled,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CommandGroupDescriptor:
    """Group-level descriptor for a top-level CLI command family."""

    group_id: str
    domain: str
    owner_module: str
    risk_level: CommandRiskLevel
    commands: list[CommandDescriptor]
    application_service_required: bool = False
    legacy_cli_owned: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "domain": self.domain,
            "owner_module": self.owner_module,
            "risk_level": self.risk_level.value,
            "application_service_required": self.application_service_required,
            "legacy_cli_owned": self.legacy_cli_owned,
            "commands_total": len(self.commands),
            "commands": [command.to_dict() for command in self.commands],
        }


@dataclass(frozen=True)
class CliCommandRegistry:
    """Top-level static CLI registry payload."""

    schema_version: str
    schema_id: str
    registry_id: str
    generated_from: str
    created_by: str
    groups: list[CommandGroupDescriptor]
    summary: dict[str, Any]
    safety: dict[str, Any]
    recommendations: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "schema_id": self.schema_id,
            "registry_id": self.registry_id,
            "generated_from": self.generated_from,
            "created_by": self.created_by,
            "commands_total": self.summary.get("commands_total", sum(len(group.commands) for group in self.groups)),
            "groups_total": len(self.groups),
            "summary": dict(self.summary),
            "groups": [group.to_dict() for group in self.groups],
            "safety": dict(self.safety),
            "recommendations": list(self.recommendations),
            "metadata": dict(self.metadata),
        }
