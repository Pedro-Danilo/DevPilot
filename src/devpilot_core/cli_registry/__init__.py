from .compatibility import (
    CLI_COMPATIBILITY_REPORT_CONTRACT,
    CLI_COMPATIBILITY_REPORT_SCHEMA_ID,
    CLI_COMPATIBILITY_SUBGATE,
    CliCompatibilityContractRunner,
    CliCompatibilityOptions,
    render_cli_compatibility_markdown,
)
from .builders import CLI_REGISTRY_CONTRACT, CLI_REGISTRY_SCHEMA_ID, StaticCliInventoryExtractor, StaticCliInventoryOptions
from .hotspots import CliHotspotOwnershipReportBuilder, HOTSPOT_REPORT_ID, render_hotspot_markdown
from .growth_gate import CliNoGrowthGate, CliNoGrowthGateOptions, NO_GROWTH_GATE_ID, render_no_growth_markdown
from .registry import DeclarativeCliRegistryBuilder, DeclarativeCommandOverride, DeclarativeGroupDescriptor
from .models import (
    CliCommandRegistry,
    CommandDescriptor,
    CommandGroupDescriptor,
    CommandOptionDescriptor,
    CommandRiskLevel,
    CommandSideEffect,
)
from .ownership import (
    CLI_COMMAND_OWNERSHIP_MATRIX_CONTRACT,
    CLI_COMMAND_OWNERSHIP_MATRIX_SCHEMA_ID,
    CLI_EXTRACTION_PLAN_CONTRACT,
    CLI_EXTRACTION_PLAN_SCHEMA_ID,
    CliCommandOwnershipMatrixBuilder,
    CliCommandOwnershipOptions,
)
from .report import CliCommandRegistryReportBuilder, CliCommandRegistryReportOptions

__all__ = [
    "render_cli_compatibility_markdown",
    "CliCompatibilityOptions",
    "CliCompatibilityContractRunner",
    "CLI_COMPATIBILITY_SUBGATE",
    "CLI_COMPATIBILITY_REPORT_SCHEMA_ID",
    "CLI_COMPATIBILITY_REPORT_CONTRACT",
    "CLI_REGISTRY_CONTRACT",
    "CLI_REGISTRY_SCHEMA_ID",
    "CLI_COMMAND_OWNERSHIP_MATRIX_CONTRACT",
    "CLI_COMMAND_OWNERSHIP_MATRIX_SCHEMA_ID",
    "CLI_EXTRACTION_PLAN_CONTRACT",
    "CLI_EXTRACTION_PLAN_SCHEMA_ID",
    "CliCommandRegistry",
    "CliCommandRegistryReportBuilder",
    "CliCommandRegistryReportOptions",
    "CliCommandOwnershipMatrixBuilder",
    "CliCommandOwnershipOptions",
    "CliHotspotOwnershipReportBuilder",
    "CliNoGrowthGate",
    "CliNoGrowthGateOptions",
    "HOTSPOT_REPORT_ID",
    "NO_GROWTH_GATE_ID",
    "render_hotspot_markdown",
    "render_no_growth_markdown",
    "DeclarativeCliRegistryBuilder",
    "DeclarativeCommandOverride",
    "DeclarativeGroupDescriptor",
    "CommandDescriptor",
    "CommandGroupDescriptor",
    "CommandOptionDescriptor",
    "CommandRiskLevel",
    "CommandSideEffect",
    "StaticCliInventoryExtractor",
    "StaticCliInventoryOptions",
]
