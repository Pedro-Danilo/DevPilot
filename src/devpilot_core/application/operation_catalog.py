from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

from .report import ApplicationServiceBoundaryReportBuilder

POST_H_007_B_CREATED_BY = "POST-H-007-B"
APPLICATION_OPERATION_CATALOG_ID = "devpilot-application-operation-catalog"
APPLICATION_OPERATION_CATALOG_SCHEMA_ID = "SCHEMA-DEVPL-APPLICATION-OPERATION-CATALOG-V1"

REQUIRED_INITIAL_DOMAINS = (
    "workspace",
    "validation",
    "reports",
    "approvals",
    "settings",
    "repo",
    "review",
    "refactor",
    "model",
    "observability",
)


@dataclass(frozen=True)
class ApplicationOperationDescriptor:
    """Declarative contract for one operation exposed at the ApplicationService boundary.

    POST-H-007-B promotes the advisory inventory produced by POST-H-007-A into
    a schema-valid operation catalog. The descriptor is intentionally declarative:
    it does not register runtime routes, does not execute handlers and does not
    modify CLI/API/UI behavior. Later POST-H-007 micro-sprints can use these
    descriptors to enforce boundary policy and DTO normalization incrementally.
    """

    operation_id: str
    domain: str
    service: str
    method: str
    request_contract: str = "ApplicationRequest"
    response_contract: str = "ApplicationResponse"
    cli_commands: list[str] = field(default_factory=list)
    api_routes: list[str] = field(default_factory=list)
    ui_surfaces: list[str] = field(default_factory=list)
    policy_required: bool = False
    dry_run_default: bool = True
    writes_files: bool = False
    risk_level: str = "medium"
    side_effects: list[str] = field(default_factory=list)
    test_contract_ids: list[str] = field(default_factory=list)
    source: str = "post-h-007-a-boundary-inventory"
    status: str = "declared-initial"
    preliminary: bool = True
    direct_core_bypass: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        exposed_to = []
        if self.cli_commands:
            exposed_to.append("cli")
        if self.api_routes:
            exposed_to.append("api")
        if self.ui_surfaces:
            exposed_to.append("ui")
        if not exposed_to:
            exposed_to.append("internal")
        test_contract_ids = sorted(set(self.test_contract_ids))
        return {
            "operation_id": self.operation_id,
            "domain": self.domain,
            "service": self.service,
            "method": self.method,
            "request_contract": self.request_contract,
            "response_contract": self.response_contract,
            "cli_commands": sorted(set(self.cli_commands)),
            "api_routes": sorted(set(self.api_routes)),
            "ui_surfaces": sorted(set(self.ui_surfaces)),
            "exposed_to": exposed_to,
            "policy_required": self.policy_required,
            "dry_run_default": self.dry_run_default,
            "writes_files": self.writes_files,
            "risk_level": self.risk_level,
            "side_effects": sorted(set(self.side_effects or _default_side_effects(self.writes_files))),
            "test_contract_ids": test_contract_ids,
            "test_coverage": {
                "covered": bool(test_contract_ids),
                "coverage_source": "test-contract-registry",
                "recommended_command": "python -m pytest tests/test_application_operation_catalog_schema.py -q",
            },
            "source": self.source,
            "status": self.status,
            "preliminary": self.preliminary,
            "direct_core_bypass": self.direct_core_bypass,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ApplicationOperationCatalog:
    """Schema-valid collection of ApplicationOperationDescriptor rows."""

    operations: list[ApplicationOperationDescriptor]
    generated_at_utc: str
    direct_core_bypass_total: int
    source_report_id: str = "devpilot-application-service-boundary-report"
    schema_version: str = "1.0"
    schema_id: str = APPLICATION_OPERATION_CATALOG_SCHEMA_ID
    catalog_id: str = APPLICATION_OPERATION_CATALOG_ID
    created_by: str = POST_H_007_B_CREATED_BY
    status: str = "implemented-initial"
    preliminary: bool = True

    def to_dict(self) -> dict[str, Any]:
        operation_dicts = [operation.to_dict() for operation in sorted(self.operations, key=lambda item: item.operation_id)]
        domains = sorted({operation["domain"] for operation in operation_dicts})
        required_missing = sorted(set(REQUIRED_INITIAL_DOMAINS) - set(domains))
        summary = {
            "catalog_id": self.catalog_id,
            "schema_version": self.schema_version,
            "schema_id": self.schema_id,
            "created_by": self.created_by,
            "status": self.status,
            "generated_at_utc": self.generated_at_utc,
            "source_report_id": self.source_report_id,
            "operations_total": len(operation_dicts),
            "domains_total": len(domains),
            "required_initial_domains_total": len(REQUIRED_INITIAL_DOMAINS),
            "required_initial_domains_covered_total": len(REQUIRED_INITIAL_DOMAINS) - len(required_missing),
            "cli_bound_total": sum(1 for operation in operation_dicts if operation["cli_commands"]),
            "api_bound_total": sum(1 for operation in operation_dicts if operation["api_routes"]),
            "ui_bound_total": sum(1 for operation in operation_dicts if operation["ui_surfaces"]),
            "policy_required_total": sum(1 for operation in operation_dicts if operation["policy_required"]),
            "writes_files_total": sum(1 for operation in operation_dicts if operation["writes_files"]),
            "high_or_critical_total": sum(1 for operation in operation_dicts if operation["risk_level"] in {"high", "critical"}),
            "operations_with_test_contracts_total": sum(1 for operation in operation_dicts if operation["test_contract_ids"]),
            "operations_without_test_contracts_total": sum(1 for operation in operation_dicts if not operation["test_contract_ids"]),
            "direct_core_bypass_total": self.direct_core_bypass_total,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "runtime_routes_added": False,
            "runtime_behavior_changed": False,
            "preliminary": self.preliminary,
        }
        return {
            "schema_version": self.schema_version,
            "schema_id": self.schema_id,
            "catalog_id": self.catalog_id,
            "created_by": self.created_by,
            "status": self.status,
            "generated_at_utc": self.generated_at_utc,
            "source_report_id": self.source_report_id,
            "required_initial_domains": list(REQUIRED_INITIAL_DOMAINS),
            "required_initial_domains_missing": required_missing,
            "domains": domains,
            "operations": operation_dicts,
            "summary": summary,
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
                "runtime_routes_added": False,
                "runtime_behavior_changed": False,
            },
            "notes": [
                "POST-H-007-B is a declarative/catalog sprint; it does not route runtime calls or enforce interface policy.",
                "CLI/API/UI mappings are explicit arrays and may be empty while operations remain internal-only.",
                "POST-H-007-C/D/E must normalize selected DTO paths, enforce boundary policy and connect CLI registry warnings incrementally.",
            ],
        }


@dataclass(frozen=True)
class ApplicationOperationCatalogOptions:
    """Options for generating the POST-H-007-B operation catalog."""

    write_report: bool = False
    output_json: Path = Path("outputs/reports/application_operation_catalog.json")
    output_markdown: Path = Path("outputs/reports/application_operation_catalog.md")


class ApplicationOperationCatalogBuilder:
    """Build a declarative ApplicationService operation catalog from local static evidence."""

    def __init__(self, root: Path, options: ApplicationOperationCatalogOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or ApplicationOperationCatalogOptions()

    def run(self) -> CommandResult:
        catalog = self.build_catalog()
        payload = catalog.to_dict()
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

        ok = not payload["required_initial_domains_missing"] and payload["summary"]["operations_without_test_contracts_total"] == 0
        findings = [
            Finding(
                id="APPLICATION_OPERATION_CATALOG_PASS" if ok else "APPLICATION_OPERATION_CATALOG_BLOCK",
                message="Application operation catalog was generated." if ok else "Application operation catalog has missing required coverage.",
                severity=Severity.INFO if ok else Severity.BLOCK,
                metadata={
                    "operations_total": payload["summary"]["operations_total"],
                    "required_initial_domains_missing": payload["required_initial_domains_missing"],
                    "operations_without_test_contracts_total": payload["summary"]["operations_without_test_contracts_total"],
                },
            )
        ]
        data: dict[str, Any] = {"summary": payload["summary"], "catalog": payload}
        if reports:
            data["reports"] = reports
        return CommandResult(
            command="application operation-catalog",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Application operation catalog passed." if ok else "Application operation catalog blocked.",
            data=data,
            findings=findings,
        )

    def build_catalog(self) -> ApplicationOperationCatalog:
        boundary_report = ApplicationServiceBoundaryReportBuilder(self.root).build_report()
        operations = self._merge_boundary_operations(boundary_report.get("operations", []))
        return ApplicationOperationCatalog(
            operations=operations,
            generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            direct_core_bypass_total=int(boundary_report.get("summary", {}).get("direct_core_bypass_total", 0)),
            source_report_id=str(boundary_report.get("summary", {}).get("report_id", "devpilot-application-service-boundary-report")),
        )

    def _merge_boundary_operations(self, raw_operations: list[dict[str, Any]]) -> list[ApplicationOperationDescriptor]:
        merged: dict[str, dict[str, Any]] = {}
        for raw in raw_operations:
            operation_id = str(raw.get("operation_id", "")).strip()
            if not operation_id:
                continue
            current = merged.setdefault(
                operation_id,
                {
                    "operation_id": operation_id,
                    "domain": str(raw.get("domain") or operation_id.split(".", 1)[0]),
                    "service": str(raw.get("service") or "ApplicationService"),
                    "method": str(raw.get("method") or operation_id.replace(".", "_")),
                    "request_contract": str(raw.get("request_contract") or "ApplicationRequest"),
                    "response_contract": str(raw.get("response_contract") or "ApplicationResponse"),
                    "cli_commands": set(),
                    "api_routes": set(),
                    "ui_surfaces": set(),
                    "policy_required": False,
                    "dry_run_default": True,
                    "writes_files": False,
                    "risk_level": str(raw.get("risk_level") or "medium"),
                    "side_effects": set(),
                    "direct_core_bypass": bool(raw.get("direct_core_bypass", False)),
                    "notes": set(),
                },
            )
            current["cli_commands"].update(str(item) for item in raw.get("cli_commands", []) if item)
            current["api_routes"].update(str(item) for item in raw.get("api_routes", []) if item)
            current["ui_surfaces"].update(str(item) for item in raw.get("ui_surfaces", []) if item)
            current["policy_required"] = bool(current["policy_required"] or raw.get("policy_required", False))
            current["dry_run_default"] = bool(current["dry_run_default"] and raw.get("dry_run_default", True))
            current["writes_files"] = bool(current["writes_files"] or raw.get("writes_files", False))
            current["risk_level"] = _max_risk(str(current["risk_level"]), str(raw.get("risk_level") or "medium"))
            current["side_effects"].update(_default_side_effects(bool(raw.get("writes_files", False))))
            current["direct_core_bypass"] = bool(current["direct_core_bypass"] or raw.get("direct_core_bypass", False))
        descriptors: list[ApplicationOperationDescriptor] = []
        for item in merged.values():
            notes = [
                "Initial descriptor derived from POST-H-007-A static boundary inventory.",
                "Runtime routing and DTO normalization are intentionally deferred to later POST-H-007 micro-sprints.",
            ]
            descriptors.append(
                ApplicationOperationDescriptor(
                    operation_id=item["operation_id"],
                    domain=item["domain"],
                    service=item["service"],
                    method=item["method"],
                    request_contract=item["request_contract"],
                    response_contract=item["response_contract"],
                    cli_commands=sorted(item["cli_commands"]),
                    api_routes=sorted(item["api_routes"]),
                    ui_surfaces=sorted(item["ui_surfaces"]),
                    policy_required=bool(item["policy_required"]),
                    dry_run_default=bool(item["dry_run_default"]),
                    writes_files=bool(item["writes_files"]),
                    risk_level=item["risk_level"],
                    side_effects=sorted(item["side_effects"] or _default_side_effects(bool(item["writes_files"]))),
                    test_contract_ids=_test_contract_ids_for_operation(item["operation_id"], item["domain"]),
                    direct_core_bypass=bool(item["direct_core_bypass"]),
                    notes=notes,
                )
            )
        if not any(descriptor.operation_id == "api.shell_gate" for descriptor in descriptors):
            descriptors.append(
                ApplicationOperationDescriptor(
                    operation_id="api.shell_gate",
                    domain="api",
                    service="UiApiIndustrialShellGate",
                    method="run",
                    cli_commands=["python -m devpilot_core api shell-gate"],
                    api_routes=[],
                    ui_surfaces=["ui-api-industrial-shell"],
                    policy_required=True,
                    dry_run_default=True,
                    writes_files=True,
                    risk_level="high",
                    side_effects=["execute-subprocess", "write-report"],
                    test_contract_ids=["post-h-014-ui-api-shell-quality-gate"],
                    source="post-h-014-e-ui-api-shell-quality-gate",
                    notes=[
                        "POST-H-014-E binds the UI/API shell quality subgate to CLI/API/UI contract evidence.",
                        "The command writes only optional reports under outputs/reports and runs a local npm smoke script without network or servers.",
                    ],
                )
            )
        return descriptors

    def _write_reports(self, payload: dict[str, Any]) -> dict[str, str]:
        self.options.output_json.parent.mkdir(parents=True, exist_ok=True)
        self.options.output_markdown.parent.mkdir(parents=True, exist_ok=True)
        self.options.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.options.output_markdown.write_text(render_application_operation_catalog_markdown(payload), encoding="utf-8")
        return {
            "json": str(self.options.output_json).replace("\\", "/"),
            "markdown": str(self.options.output_markdown).replace("\\", "/"),
        }


def render_application_operation_catalog_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines = [
        "# Application Operation Catalog — POST-H-007-B",
        "",
        "Generated read-only from local static evidence. This report is preliminary and does not change runtime routing.",
        "",
        "## Summary",
        "",
        f"- Operations: `{summary.get('operations_total')}`",
        f"- Domains: `{summary.get('domains_total')}`",
        f"- Required domains covered: `{summary.get('required_initial_domains_covered_total')}/{summary.get('required_initial_domains_total')}`",
        f"- CLI mapped operations: `{summary.get('cli_bound_total')}`",
        f"- API mapped operations: `{summary.get('api_bound_total')}`",
        f"- UI mapped operations: `{summary.get('ui_bound_total')}`",
        f"- Policy-required operations: `{summary.get('policy_required_total')}`",
        f"- Write-capable operations: `{summary.get('writes_files_total')}`",
        f"- Direct core bypasses inherited from boundary report: `{summary.get('direct_core_bypass_total')}`",
        "",
        "## Operations",
        "",
        "| Operation | Domain | Risk | Writes | Policy | CLI | API | UI |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for operation in payload.get("operations", []):
        lines.append(
            "| {operation_id} | {domain} | {risk_level} | {writes_files} | {policy_required} | {cli} | {api} | {ui} |".format(
                operation_id=operation.get("operation_id"),
                domain=operation.get("domain"),
                risk_level=operation.get("risk_level"),
                writes_files="yes" if operation.get("writes_files") else "no",
                policy_required="yes" if operation.get("policy_required") else "no",
                cli=len(operation.get("cli_commands", [])),
                api=len(operation.get("api_routes", [])),
                ui=len(operation.get("ui_surfaces", [])),
            )
        )
    lines.extend(
        [
            "",
            "## Limits",
            "",
            "- `POST-H-007-B` is catalog/schema only.",
            "- It does not normalize runtime DTO paths; that belongs to `POST-H-007-C`.",
            "- It does not enforce per-interface policy; that belongs to `POST-H-007-D`.",
            "- It does not connect CLI registry warnings to operation mappings; that belongs to `POST-H-007-E`.",
            "",
        ]
    )
    return "\n".join(lines)


def _default_side_effects(writes_files: bool) -> list[str]:
    return ["write-files", "write-report"] if writes_files else ["none"]


def _max_risk(left: str, right: str) -> str:
    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    return left if order.get(left, 1) >= order.get(right, 1) else right


def _test_contract_ids_for_operation(operation_id: str, domain: str) -> list[str]:
    ids = {"post-h-007-application-operation-catalog"}
    if domain in REQUIRED_INITIAL_DOMAINS or operation_id.startswith(("validation.", "reports.", "approvals.", "settings.", "repo.", "review.", "refactor.", "model.", "observability.", "workspace.")):
        ids.add("post-h-007-application-service-boundary-inventory")
    if operation_id.startswith("workspace."):
        ids.add("post-h-006-cli-handler-migration")
    if operation_id.startswith("validation."):
        ids.add("post-h-006-cli-handler-migration")
    if operation_id == "api.shell_gate" or operation_id.startswith("api."):
        ids.add("post-h-014-ui-api-shell-quality-gate")
    return sorted(ids)
