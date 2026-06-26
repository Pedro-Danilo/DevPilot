from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.cli_registry import DeclarativeCliRegistryBuilder

from .operation_catalog import ApplicationOperationCatalogBuilder

POST_H_007_E_CREATED_BY = "POST-H-007-E"
APPLICATION_CLI_BOUNDARY_INTEGRATION_REPORT_ID = "devpilot-application-cli-boundary-integration-report"


@dataclass(frozen=True)
class CliBoundaryIntegrationOptions:
    """Options for the POST-H-007-E CLI/ApplicationService integration report."""

    write_report: bool = False
    output_json: Path = Path("outputs/reports/application_cli_boundary_integration_report.json")
    output_markdown: Path = Path("outputs/reports/application_cli_boundary_integration_report.md")


class CliApplicationBoundaryIntegrationReportBuilder:
    """Relate POST-H-006 CommandDescriptor rows with POST-H-007 operation descriptors.

    The builder is a local/read-only governance check. It does not route CLI
    commands dynamically, does not import command handlers, does not execute
    subprocesses and does not change the public CLI/API/UI surface. It produces
    evidence for POST-H-007-E and feeds the hardening quality gate with explicit
    warnings when registered commands that should cross the ApplicationService
    boundary still lack an operation mapping.
    """

    def __init__(self, root: Path, options: CliBoundaryIntegrationOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or CliBoundaryIntegrationOptions()

    def run(self) -> CommandResult:
        payload = self.build_report()
        reports: dict[str, str] = {}
        if self.options.write_report:
            reports = self._write_reports(payload)
            payload["summary"]["reports_written"] = True
            payload["summary"]["output_json"] = reports["json"]
            payload["summary"]["output_markdown"] = reports["markdown"]
        else:
            payload["summary"]["reports_written"] = False
            payload["summary"]["output_json"] = None
            payload["summary"]["output_markdown"] = None

        findings = _findings_from_report(payload)
        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        ok = not blocking
        return CommandResult(
            command="application cli-boundary integration",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Application CLI boundary integration passed." if ok else "Application CLI boundary integration has blocking gaps.",
            data={"summary": payload["summary"], "report": payload, "reports": reports},
            findings=findings,
        )

    def build_report(self) -> dict[str, Any]:
        cli_registry = DeclarativeCliRegistryBuilder(self.root).build_registry().to_dict()
        operation_catalog = ApplicationOperationCatalogBuilder(self.root).build_catalog().to_dict()
        operations = list(operation_catalog.get("operations", []))
        operation_ids = {str(operation.get("operation_id")) for operation in operations if isinstance(operation, dict)}

        operation_by_invocation: dict[str, dict[str, Any]] = {}
        for operation in operations:
            if not isinstance(operation, dict):
                continue
            for invocation in operation.get("cli_commands", []) or []:
                normalized = _normalize_invocation(str(invocation))
                if normalized:
                    operation_by_invocation[normalized] = operation

        groups = cli_registry.get("groups", []) if isinstance(cli_registry.get("groups"), list) else []
        command_links: list[dict[str, Any]] = []
        registered_total = 0
        registered_with_mapping = 0
        applicable_total = 0
        applicable_missing = 0
        stale_metadata_total = 0

        for group in groups:
            if not isinstance(group, dict):
                continue
            group_requires_application_service = bool(group.get("application_service_required"))
            for command in group.get("commands", []) or []:
                if not isinstance(command, dict):
                    continue
                metadata = command.get("metadata") if isinstance(command.get("metadata"), dict) else {}
                command_id = str(command.get("command_id") or "")
                public_invocation = str(command.get("public_invocation") or "")
                registered = bool(metadata.get("declarative_registered"))
                operation = operation_by_invocation.get(_normalize_invocation(public_invocation))
                metadata_operation_id = str(metadata.get("application_operation_id") or "").strip() or None
                operation_id = str(operation.get("operation_id")) if operation else metadata_operation_id
                maps_to_catalog = bool(operation_id and operation_id in operation_ids)
                mapping_source = "none"
                if operation is not None:
                    mapping_source = "application-operation-catalog.cli_commands"
                elif metadata_operation_id:
                    mapping_source = "cli-command-metadata.application_operation_id"
                applies_to_boundary = bool(group_requires_application_service or operation is not None or metadata_operation_id)
                missing_mapping = bool(applies_to_boundary and not maps_to_catalog)
                stale_metadata = bool(metadata_operation_id and metadata_operation_id not in operation_ids)

                if registered:
                    registered_total += 1
                    if maps_to_catalog:
                        registered_with_mapping += 1
                if applies_to_boundary:
                    applicable_total += 1
                    if missing_mapping:
                        applicable_missing += 1
                if stale_metadata:
                    stale_metadata_total += 1

                status = "mapped" if maps_to_catalog else "missing-operation-mapping" if missing_mapping else "not-applicable"
                command_links.append(
                    {
                        "command_id": command_id,
                        "public_invocation": public_invocation,
                        "group_id": str(group.get("group_id") or ""),
                        "registered": registered,
                        "registration_status": str(metadata.get("registration_status") or ""),
                        "application_service_required": group_requires_application_service,
                        "applies_to_boundary": applies_to_boundary,
                        "operation_id": operation_id,
                        "maps_to_catalog": maps_to_catalog,
                        "mapping_source": mapping_source,
                        "missing_mapping": missing_mapping,
                        "stale_metadata": stale_metadata,
                        "risk_level": str(command.get("risk_level") or ""),
                        "writes_files": bool(command.get("writes_files")),
                        "policy_check_required": bool(command.get("policy_check_required")),
                        "metadata_operation_id": metadata_operation_id,
                        "status": status,
                    }
                )

        api_ui_operations = [
            operation
            for operation in operations
            if isinstance(operation, dict) and (operation.get("api_routes") or operation.get("ui_surfaces"))
        ]
        api_ui_without_contract = [
            str(operation.get("operation_id"))
            for operation in api_ui_operations
            if not operation.get("test_contract_ids")
        ]

        warning_links = [link for link in command_links if link["missing_mapping"]]
        summary = {
            "report_id": APPLICATION_CLI_BOUNDARY_INTEGRATION_REPORT_ID,
            "created_by": POST_H_007_E_CREATED_BY,
            "status": "implemented-initial",
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "commands_total": len(command_links),
            "registered_commands_total": registered_total,
            "registered_commands_with_operation_mapping_total": registered_with_mapping,
            "registered_commands_missing_operation_mapping_total": max(registered_total - registered_with_mapping, 0),
            "applicable_commands_total": applicable_total,
            "applicable_commands_without_mapping_total": applicable_missing,
            "catalog_cli_mappings_total": len(operation_by_invocation),
            "catalog_operations_total": len(operations),
            "api_ui_operations_total": len(api_ui_operations),
            "api_ui_operations_with_contract_total": len(api_ui_operations) - len(api_ui_without_contract),
            "api_ui_operations_without_contract_total": len(api_ui_without_contract),
            "stale_metadata_total": stale_metadata_total,
            "warnings_total": len(warning_links),
            "blocking_findings_total": len(api_ui_without_contract) + stale_metadata_total,
            "quality_gate_hardening_bound": True,
            "test_contract_required": True,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "runtime_router_enabled": False,
            "dynamic_handler_loading_enabled": False,
            "preliminary": True,
        }
        return {
            "report_id": APPLICATION_CLI_BOUNDARY_INTEGRATION_REPORT_ID,
            "created_by": POST_H_007_E_CREATED_BY,
            "status": "implemented-initial",
            "schema_version": "1.0",
            "summary": summary,
            "command_operation_links": sorted(command_links, key=lambda item: item["command_id"]),
            "api_ui_operations_without_contract": sorted(api_ui_without_contract),
            "warnings": [
                {
                    "id": "CLI_APPLICATION_OPERATION_MAPPING_WARNING",
                    "message": "Registered or ApplicationService-required command has no catalog operation mapping yet.",
                    "command_id": link["command_id"],
                    "public_invocation": link["public_invocation"],
                    "group_id": link["group_id"],
                    "registration_status": link["registration_status"],
                }
                for link in sorted(warning_links, key=lambda item: item["command_id"])
            ],
            "safety": {
                "read_only": True,
                "dry_run": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "runtime_router_enabled": False,
                "dynamic_handler_loading_enabled": False,
            },
            "notes": [
                "POST-H-007-E is an initial CLI registry/ApplicationService integration; it is advisory plus quality-gate bound, not runtime routing.",
                "Warnings for missing command-operation mappings are non-blocking until an explicit migration sprint promotes them to enforcement.",
                "API/UI operations are blocking only if they lack explicit test_contract_ids in ApplicationOperationCatalog.",
            ],
        }

    def _write_reports(self, payload: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(render_cli_boundary_integration_markdown(payload), encoding="utf-8")
        return {"json": _display_path(json_path.relative_to(self.root)), "markdown": _display_path(markdown_path.relative_to(self.root))}


def application_cli_boundary_integration_report(root: Path) -> dict[str, Any]:
    return CliApplicationBoundaryIntegrationReportBuilder(root).build_report()


def render_cli_boundary_integration_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    warnings = payload.get("warnings", [])
    lines = [
        "# POST-H-007-E — Application CLI boundary integration report",
        "",
        f"Report ID: `{payload.get('report_id')}`",
        f"Status: `{payload.get('status')}`",
        "",
        "## Summary",
        "",
        f"- Commands total: `{summary.get('commands_total')}`",
        f"- Registered commands: `{summary.get('registered_commands_total')}`",
        f"- Registered commands with operation mapping: `{summary.get('registered_commands_with_operation_mapping_total')}`",
        f"- Applicable commands without mapping: `{summary.get('applicable_commands_without_mapping_total')}`",
        f"- API/UI operations without contract: `{summary.get('api_ui_operations_without_contract_total')}`",
        f"- Quality gate hardening bound: `{summary.get('quality_gate_hardening_bound')}`",
        "",
        "## Non-blocking mapping warnings",
        "",
    ]
    if warnings:
        for item in warnings[:50]:
            lines.append(f"- `{item.get('command_id')}` → {item.get('message')}")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local/read-only report.",
            "- No dynamic handler loading.",
            "- No runtime router activation.",
            "- No remote execution, connector write or plugin execution.",
            "",
        ]
    )
    return "\n".join(lines)


def _findings_from_report(payload: dict[str, Any]) -> list[Finding]:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    findings: list[Finding] = []
    for warning in payload.get("warnings", []) or []:
        findings.append(
            Finding(
                "CLI_APPLICATION_OPERATION_MAPPING_WARNING",
                "Registered or ApplicationService-required command has no catalog operation mapping yet.",
                Severity.WARNING,
                metadata={
                    "command_id": warning.get("command_id"),
                    "public_invocation": warning.get("public_invocation"),
                    "group_id": warning.get("group_id"),
                    "created_by": POST_H_007_E_CREATED_BY,
                },
            )
        )
    for operation_id in payload.get("api_ui_operations_without_contract", []) or []:
        findings.append(
            Finding(
                "APPLICATION_API_UI_OPERATION_CONTRACT_MISSING",
                "API/UI operation lacks explicit test_contract_ids in ApplicationOperationCatalog.",
                Severity.BLOCK,
                metadata={"operation_id": operation_id, "created_by": POST_H_007_E_CREATED_BY},
            )
        )
    if int(summary.get("stale_metadata_total") or 0) > 0:
        findings.append(
            Finding(
                "CLI_APPLICATION_OPERATION_STALE_METADATA",
                "One or more CLI command metadata mappings point to missing ApplicationOperationCatalog operations.",
                Severity.BLOCK,
                metadata={"stale_metadata_total": summary.get("stale_metadata_total")},
            )
        )
    if not findings:
        findings.append(
            Finding(
                "APPLICATION_CLI_BOUNDARY_INTEGRATION_PASS",
                "CLI registry and ApplicationOperationCatalog integration passed without blocking gaps.",
                Severity.INFO,
                metadata={
                    "registered_commands_with_operation_mapping_total": summary.get("registered_commands_with_operation_mapping_total"),
                    "api_ui_operations_with_contract_total": summary.get("api_ui_operations_with_contract_total"),
                },
            )
        )
    return findings


def _normalize_invocation(value: str) -> str:
    return " ".join(value.strip().split())


def _display_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")
