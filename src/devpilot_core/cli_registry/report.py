from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.cli_registry.builders import CLI_REGISTRY_SCHEMA_ID, StaticCliInventoryExtractor, StaticCliInventoryOptions
from devpilot_core.schemas import SchemaValidator


@dataclass(frozen=True)
class CliCommandRegistryReportOptions:
    """Options for rendering the POST-H-006-A CLI registry report."""

    cli_source: Path = Path("src/devpilot_core/cli.py")
    write_report: bool = False
    output_json: Path = Path("outputs/reports/cli_command_registry.json")
    output_markdown: Path = Path("outputs/reports/cli_command_registry.md")


class CliCommandRegistryReportBuilder:
    """Build a read-only static CLI command registry report.

    POST-H-006-A does not migrate handlers and does not alter public command
    behavior. It materializes the current CLI surface as schema-backed evidence
    so later micro-sprints can move handlers with parity tests instead of guesses.
    """

    def __init__(self, root: Path, options: CliCommandRegistryReportOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or CliCommandRegistryReportOptions()

    def build(self) -> CommandResult:
        extractor = StaticCliInventoryExtractor(
            self.root,
            StaticCliInventoryOptions(
                cli_source=self.options.cli_source,
                write_report=self.options.write_report,
                output_json=self.options.output_json,
                output_markdown=self.options.output_markdown,
            ),
        )
        registry = extractor.build_registry()
        payload = registry.to_dict()
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
                    message="Static CLI registry did not detect all expected main groups.",
                    severity=Severity.BLOCK,
                    metadata={"missing_groups": missing_groups},
                )
            )
        else:
            findings.append(
                Finding(
                    id="CLI_REGISTRY_MAIN_GROUPS_PRESENT",
                    message="Static CLI registry detected expected main groups.",
                    severity=Severity.INFO,
                    metadata={"expected_groups": sorted(expected_groups)},
                )
            )

        if self.options.write_report:
            self._write_reports(payload)
            summary["reports_written"] = True
            summary["output_json"] = str(self.options.output_json).replace("\\", "/")
            summary["output_markdown"] = str(self.options.output_markdown).replace("\\", "/")

        summary["blocking_findings_total"] = _blocking_count(findings)
        ok = validation.ok and not missing_groups and summary["commands_total"] > 0
        return CommandResult(
            command="cli-registry report",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="CLI command registry static report passed." if ok else "CLI command registry static report has blocking findings.",
            data={
                "summary": summary,
                "registry": payload,
                "notes": [
                    "POST-H-006-A is a read-only static inventory; it does not migrate handlers or change command semantics.",
                    "Handler strings are advisory until POST-H-006-B/C declare and migrate selected commands explicitly.",
                    "Reports are generated only when --write-report is passed and are intentionally excluded from release ZIPs.",
                ],
            },
            findings=findings,
        )

    def _write_reports(self, payload: dict[str, Any]) -> None:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(_markdown_report(payload), encoding="utf-8")


def _markdown_report(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines = [
        "# POST-H-006-A — CLI command registry static inventory",
        "",
        "Estado: `implemented-initial / read-only static inventory`.",
        "",
        "Este reporte materializa el inventario actual del CLI sin ejecutar comandos, sin importar `build_parser()` y sin migrar handlers.",
        "",
        "## Summary",
        "",
        f"- Groups total: {summary.get('groups_total')}",
        f"- Commands total: {summary.get('commands_total')}",
        f"- Nested commands total: {summary.get('nested_commands_total')}",
        f"- High/critical risk commands total: {summary.get('high_or_critical_risk_commands_total')}",
        f"- Dynamic handler loading enabled: {summary.get('dynamic_handler_loading_enabled')}",
        f"- Remote execution enabled: {summary.get('remote_execution_enabled')}",
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
        "- La migración real de handlers queda para micro-sprints posteriores con pruebas de paridad.",
        "- No habilita remote execution, connector write ni plugin execution.",
        "",
    ])
    return "\n".join(lines)


def _blocking_count(findings: list[Finding]) -> int:
    return sum(1 for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR})
