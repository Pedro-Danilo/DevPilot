from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.cli_registry.builders import CLI_REGISTRY_SCHEMA_ID, StaticCliInventoryOptions
from devpilot_core.cli_registry.hotspots import CliHotspotOwnershipReportBuilder, render_hotspot_markdown
from devpilot_core.cli_registry.registry import DeclarativeCliRegistryBuilder
from devpilot_core.schemas import SchemaValidator


@dataclass(frozen=True)
class CliCommandRegistryReportOptions:
    """Options for rendering the POST-H-006-A/B/C/D CLI registry report."""

    cli_source: Path = Path("src/devpilot_core/cli.py")
    write_report: bool = False
    output_json: Path = Path("outputs/reports/cli_command_registry.json")
    output_markdown: Path = Path("outputs/reports/cli_command_registry.md")
    output_hotspot_json: Path = Path("outputs/reports/cli_command_registry_report.json")
    output_hotspot_markdown: Path = Path("outputs/reports/cli_command_registry_report.md")


class CliCommandRegistryReportBuilder:
    """Build a read-only CLI command registry report.

    POST-H-006-D composes the POST-H-006-A static CLI inventory, POST-H-006-B
    declarative overlay, POST-H-006-C migrated handlers and a read-only hotspot
    / ownership report for remaining CLI debt. It does not enable a runtime
    registry router and does not alter public command behavior.
    """

    def __init__(self, root: Path, options: CliCommandRegistryReportOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or CliCommandRegistryReportOptions()

    def build(self) -> CommandResult:
        registry = DeclarativeCliRegistryBuilder(
            self.root,
            StaticCliInventoryOptions(
                cli_source=self.options.cli_source,
                write_report=self.options.write_report,
                output_json=self.options.output_json,
                output_markdown=self.options.output_markdown,
            ),
        ).build_registry()
        payload = registry.to_dict()
        hotspot_report = CliHotspotOwnershipReportBuilder(self.root, payload).build()
        payload.setdefault("summary", {}).update(
            {
                "hotspot_report_id": hotspot_report["report_id"],
                "hotspot_report_created_by": hotspot_report["created_by"],
                "migrated_commands_total": hotspot_report["summary"].get("migrated_commands_total"),
                "registered_only_commands_total": hotspot_report["summary"].get("registered_only_commands_total"),
                "legacy_commands_total": hotspot_report["summary"].get("legacy_commands_total"),
                "commands_with_side_effects_total": hotspot_report["summary"].get("commands_with_side_effects_total"),
                "commands_without_application_service_boundary_total": hotspot_report["summary"].get("commands_without_application_service_boundary_total"),
                "commands_without_test_contract_total": hotspot_report["summary"].get("commands_without_test_contract_total"),
                "ownership_status_counts": hotspot_report["summary"].get("ownership_status_counts"),
            }
        )
        validation = SchemaValidator(self.root).validate_payload(
            schema="CliCommandRegistry",
            payload=payload,
            instance_label="memory:cli-command-registry",
        )

        findings: list[Finding] = []
        findings.extend(validation.findings)
        summary = dict(payload["summary"])
        summary.update(
            {
                "schema_validation_ok": validation.ok,
                "reports_written": False,
                "output_json": None,
                "output_markdown": None,
                "blocking_findings_total": _blocking_count(findings),
                "hotspot_report_id": hotspot_report["report_id"],
                "hotspot_report_created_by": hotspot_report["created_by"],
                "hotspot_report_written": False,
                "output_hotspot_json": None,
                "output_hotspot_markdown": None,
                "migrated_commands_total": hotspot_report["summary"].get("migrated_commands_total"),
                "registered_only_commands_total": hotspot_report["summary"].get("registered_only_commands_total"),
                "legacy_commands_total": hotspot_report["summary"].get("legacy_commands_total"),
                "commands_with_side_effects_total": hotspot_report["summary"].get("commands_with_side_effects_total"),
                "commands_without_application_service_boundary_total": hotspot_report["summary"].get("commands_without_application_service_boundary_total"),
                "commands_without_test_contract_total": hotspot_report["summary"].get("commands_without_test_contract_total"),
                "dry_run": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "preliminary": True,
            }
        )

        expected_groups = {"workspace", "schema", "validate", "quality-gate", "test-contracts", "architecture"}
        present_groups = {group["group_id"] for group in payload["groups"]}
        missing_groups = sorted(expected_groups - present_groups)
        if missing_groups:
            findings.append(
                Finding(
                    id="CLI_REGISTRY_MAIN_GROUPS_MISSING",
                    message="CLI registry did not detect all expected main groups.",
                    severity=Severity.BLOCK,
                    metadata={"missing_groups": missing_groups},
                )
            )
        else:
            findings.append(
                Finding(
                    id="CLI_REGISTRY_MAIN_GROUPS_PRESENT",
                    message="CLI registry detected expected main groups.",
                    severity=Severity.INFO,
                    metadata={"expected_groups": sorted(expected_groups)},
                )
            )

        declarative_missing = summary.get("declarative_missing_groups", [])
        if declarative_missing:
            findings.append(
                Finding(
                    id="CLI_REGISTRY_DECLARATIVE_GROUPS_MISSING",
                    message="Declarative CLI registry is missing expected POST-H-006-B groups.",
                    severity=Severity.BLOCK,
                    metadata={"missing_groups": declarative_missing},
                )
            )
        else:
            findings.append(
                Finding(
                    id="CLI_REGISTRY_DECLARATIVE_GROUPS_PRESENT",
                    message="Declarative CLI registry includes the initial POST-H-006-B groups, POST-H-006-C migrated handlers and POST-H-006-D hotspot report inputs.",
                    severity=Severity.INFO,
                    metadata={
                        "declarative_registered_groups_total": summary.get("declarative_registered_groups_total"),
                        "declarative_registered_commands_total": summary.get("declarative_registered_commands_total"),
                    },
                )
            )

        if self.options.write_report:
            self._write_reports(payload, hotspot_report)
            summary["reports_written"] = True
            summary["output_json"] = str(self.options.output_json).replace("\\", "/")
            summary["output_markdown"] = str(self.options.output_markdown).replace("\\", "/")
            summary["hotspot_report_written"] = True
            summary["output_hotspot_json"] = str(self.options.output_hotspot_json).replace("\\", "/")
            summary["output_hotspot_markdown"] = str(self.options.output_hotspot_markdown).replace("\\", "/")

        summary["blocking_findings_total"] = _blocking_count(findings)
        ok = validation.ok and not missing_groups and not declarative_missing and summary["commands_total"] > 0
        return CommandResult(
            command="cli-registry report",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="CLI command registry hotspot and ownership report passed." if ok else "CLI command registry hotspot and ownership report has blocking findings.",
            data={
                "summary": summary,
                "registry": payload,
                "hotspot_report": hotspot_report,
                "notes": [
                    "POST-H-006-D adds a read-only hotspot and ownership report derived from the CLI registry and Test Contract Registry.",
                    "POST-H-006-C migrated selected workspace/validation handlers; cli.py remains the public parser/dispatch wrapper.",
                    "Runtime registry routing and dynamic handler loading remain disabled.",
                    "Reports are generated only when --write-report is passed and are intentionally excluded from release ZIPs.",
                ],
            },
            findings=findings,
        )

    def _write_reports(self, payload: dict[str, Any], hotspot_report: dict[str, Any]) -> None:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        hotspot_json_path = self.root / self.options.output_hotspot_json
        hotspot_markdown_path = self.root / self.options.output_hotspot_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(_markdown_report(payload), encoding="utf-8")
        hotspot_json_path.write_text(json.dumps(hotspot_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        hotspot_markdown_path.write_text(render_hotspot_markdown(hotspot_report), encoding="utf-8")


def _markdown_report(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines = [
        "# POST-H-006-D — CLI command registry hotspots and ownership",
        "",
        "Estado: `implemented-initial / hotspot ownership report, no runtime registry router`.",
        "",
        "Este reporte combina inventario AST del CLI, descriptors declarativos iniciales, migración incremental de handlers seleccionados y métricas read-only de hotspots/ownership sin habilitar carga dinámica ni cambiar comandos públicos.",
        "",
        "## Summary",
        "",
        f"- Groups total: {summary.get('groups_total')}",
        f"- Commands total: {summary.get('commands_total')}",
        f"- Nested commands total: {summary.get('nested_commands_total')}",
        f"- High/critical risk commands total: {summary.get('high_or_critical_risk_commands_total')}",
        f"- Declarative registered groups total: {summary.get('declarative_registered_groups_total')}",
        f"- Declarative registered commands total: {summary.get('declarative_registered_commands_total')}",
        f"- Legacy unregistered commands total: {summary.get('legacy_unregistered_commands_total')}",
        f"- Migrated handlers total: {summary.get('migrated_handlers_total')}",
        f"- Migrated command ids: {summary.get('migrated_command_ids')}",
        f"- Dynamic handler loading enabled: {summary.get('dynamic_handler_loading_enabled')}",
        f"- Remote execution enabled: {summary.get('remote_execution_enabled')}",
        f"- Migrated commands total: {summary.get('migrated_commands_total')}",
        f"- Registered-only commands total: {summary.get('registered_only_commands_total')}",
        f"- Legacy commands total: {summary.get('legacy_commands_total')}",
        f"- Commands without ApplicationService boundary total: {summary.get('commands_without_application_service_boundary_total')}",
        f"- Commands without test-contract association total: {summary.get('commands_without_test_contract_total')}",
        "",
        "## Groups",
        "",
        "| Group | Domain | Risk | Commands |",
        "|---|---|---:|---:|",
    ]
    for group in payload.get("groups", []):
        lines.append(f"| `{group['group_id']}` | `{group['domain']}` | `{group['risk_level']}` | {group['commands_total']} |")
    lines.extend([
        "",
        "## Industrial notes",
        "",
        "- Esta versión es preliminar y advisory; no debe usarse todavía para cargar handlers dinámicamente.",
        "- La reducción completa de hotspot CLI queda para micro-sprints posteriores con pruebas de paridad y gate de no crecimiento.",
        "- No habilita remote execution, connector write ni plugin execution.",
        "",
    ])
    return "\n".join(lines)


def _blocking_count(findings: list[Finding]) -> int:
    return sum(1 for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR})
