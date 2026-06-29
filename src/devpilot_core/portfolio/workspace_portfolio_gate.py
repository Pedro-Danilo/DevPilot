from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.workspace import MultiworkspaceRegistryV2, WorkspaceIsolationOptions, WorkspaceIsolationValidator, WorkspaceRegistryV2Options

POST_H_016_E_CREATED_BY = "POST-H-016-E"
WORKSPACE_PORTFOLIO_HARDENING_SUBGATE = "workspace-portfolio-hardening"
DEFAULT_WORKSPACE_PORTFOLIO_GATE_REPORT_JSON = Path("outputs/reports/workspace_portfolio_hardening_report.json")
DEFAULT_WORKSPACE_PORTFOLIO_GATE_REPORT_MD = Path("outputs/reports/workspace_portfolio_hardening_report.md")


@dataclass(frozen=True)
class WorkspacePortfolioHardeningGateOptions:
    """Options for the POST-H-016-E local workspace portfolio quality gate."""

    registry_path: str = ".devpilot/workspaces/workspace_registry.json"
    write_report: bool = False
    output_json: Path = DEFAULT_WORKSPACE_PORTFOLIO_GATE_REPORT_JSON
    output_markdown: Path = DEFAULT_WORKSPACE_PORTFOLIO_GATE_REPORT_MD


class WorkspacePortfolioHardeningGate:
    """Validate local workspace portfolio hardening without mutating source or runtime state."""

    def __init__(self, root: Path, options: WorkspacePortfolioHardeningGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or WorkspacePortfolioHardeningGateOptions()

    def run(self) -> CommandResult:
        from devpilot_core.application import ApplicationOperationCatalogBuilder, ApplicationService

        registry_result = MultiworkspaceRegistryV2(
            self.root,
            options=WorkspaceRegistryV2Options(registry_path=self.options.registry_path),
        ).validate()
        isolation_result = WorkspaceIsolationValidator(
            self.root,
            options=WorkspaceIsolationOptions(registry_path=self.options.registry_path, write_report=False),
        ).run()
        portfolio_result = ApplicationService(self.root).portfolio_status(registry_path=self.options.registry_path)
        operation_catalog_result = ApplicationOperationCatalogBuilder(self.root).run()

        findings: list[Finding] = []
        findings.extend(self._prefixed_findings(registry_result, prefix="registry"))
        findings.extend(self._prefixed_findings(isolation_result, prefix="isolation"))
        findings.extend(self._prefixed_findings(portfolio_result, prefix="portfolio"))
        findings.extend(self._prefixed_findings(operation_catalog_result, prefix="operation-catalog"))
        findings.extend(self._api_route_contract_findings())
        findings.extend(self._portfolio_status_findings(portfolio_result))
        findings.extend(self._operation_catalog_findings(operation_catalog_result))
        findings.extend(self._documentation_findings())

        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        summary = self._summary(
            registry_result=registry_result,
            isolation_result=isolation_result,
            portfolio_result=portfolio_result,
            operation_catalog_result=operation_catalog_result,
            blocking_total=len(blocking),
        )
        report = {
            "schema_version": "1.0",
            "report_id": "workspace-portfolio-hardening-report",
            "created_by": POST_H_016_E_CREATED_BY,
            "status": "implemented-initial",
            "generated_at_utc": _utc_now(),
            "summary": summary,
            "checks": {
                "registry": _result_projection(registry_result),
                "isolation": _result_projection(isolation_result),
                "portfolio": _result_projection(portfolio_result),
                "operation_catalog": _result_projection(operation_catalog_result),
            },
            "findings": [finding.to_dict() for finding in findings],
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "source_mutations_performed": False,
            },
        }
        reports = self._write_reports(report) if self.options.write_report else {}
        if reports:
            summary["reports_written"] = True
            summary["output_json"] = reports["json"]
            summary["output_markdown"] = reports["markdown"]

        ok = registry_result.ok and isolation_result.ok and portfolio_result.ok and operation_catalog_result.ok and not blocking
        return CommandResult(
            command=f"quality {WORKSPACE_PORTFOLIO_HARDENING_SUBGATE}",
            ok=ok,
            exit_code=ExitCode.PASS if ok else exit_code_for_findings(blocking, default_ok=False),
            message="Workspace portfolio hardening gate passed." if ok else "Workspace portfolio hardening gate blocked.",
            data={"summary": summary, "report": report, "reports": reports},
            findings=findings
            or [
                Finding(
                    "WORKSPACE_PORTFOLIO_HARDENING_PASS",
                    "Workspace registry, isolation, portfolio status, API boundary and runbook are hardened.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _summary(
        self,
        *,
        registry_result: CommandResult,
        isolation_result: CommandResult,
        portfolio_result: CommandResult,
        operation_catalog_result: CommandResult,
        blocking_total: int,
    ) -> dict[str, Any]:
        portfolio_summary = portfolio_result.data.get("summary", {}) if isinstance(portfolio_result.data, dict) else {}
        isolation_summary = isolation_result.data.get("summary", {}) if isinstance(isolation_result.data, dict) else {}
        return {
            "created_by": POST_H_016_E_CREATED_BY,
            "quality_gate_subgate": WORKSPACE_PORTFOLIO_HARDENING_SUBGATE,
            "workspace_portfolio_hardening_ready": all(
                [registry_result.ok, isolation_result.ok, portfolio_result.ok, operation_catalog_result.ok]
            )
            and blocking_total == 0,
            "registry_ok": registry_result.ok,
            "isolation_ok": isolation_result.ok,
            "portfolio_status_ok": portfolio_result.ok,
            "operation_catalog_ok": operation_catalog_result.ok,
            "registry_path": self.options.registry_path,
            "workspaces_total": portfolio_summary.get("workspaces_total"),
            "active_workspace_id": portfolio_summary.get("active_workspace_id"),
            "registered_workspaces_only": portfolio_summary.get("registered_workspaces_only") is True,
            "unregistered_workspace_policy": portfolio_summary.get("unregistered_workspace_policy"),
            "portfolio_status_read_only": portfolio_summary.get("portfolio_status_read_only") is True,
            "path_isolation_passed": portfolio_summary.get("path_isolation_passed") is True,
            "state_isolation_passed": portfolio_summary.get("state_isolation_passed") is True,
            "outputs_isolation_passed": portfolio_summary.get("outputs_isolation_passed") is True,
            "traces_isolation_passed": portfolio_summary.get("traces_isolation_passed") is True,
            "isolation_blocking_findings_total": isolation_summary.get("blocking_findings_total"),
            "blocking_findings_total": blocking_total,
            "reports_written": False,
            "output_json": None,
            "output_markdown": None,
            "local_first": True,
            "read_only": True,
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

    def _api_route_contract_findings(self) -> list[Finding]:
        path = self.root / ".devpilot/interfaces/api_route_contract_registry.json"
        if not path.exists():
            return [Finding("WORKSPACE_PORTFOLIO_API_REGISTRY_MISSING", "API route contract registry is missing.", Severity.BLOCK, path=".devpilot/interfaces/api_route_contract_registry.json")]
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return [Finding("WORKSPACE_PORTFOLIO_API_REGISTRY_INVALID_JSON", str(exc), Severity.ERROR, path=".devpilot/interfaces/api_route_contract_registry.json")]
        routes = {item.get("route_id"): item for item in payload.get("routes", []) if isinstance(item, dict)}
        route = routes.get("api.portfolio.status")
        if not isinstance(route, dict):
            return [Finding("WORKSPACE_PORTFOLIO_API_ROUTE_MISSING", "api.portfolio.status must be registered.", Severity.BLOCK, path=".devpilot/interfaces/api_route_contract_registry.json")]
        findings: list[Finding] = []
        expected = {
            "method": "GET",
            "path": "/api/v1/portfolio/status",
            "operation": "portfolio.status",
            "application_service_required": True,
            "policy_check_required": True,
            "auth_required": True,
            "dry_run_only": True,
            "mutations_allowed": False,
            "external_api_allowed": False,
            "remote_execution_allowed": False,
            "connector_write_allowed": False,
            "plugin_execution_allowed": False,
        }
        for key, value in expected.items():
            actual = route.get(key)
            invalid = actual is not value if isinstance(value, bool) else actual != value
            if invalid:
                findings.append(
                    Finding(
                        "WORKSPACE_PORTFOLIO_API_ROUTE_CONTRACT_INVALID",
                        "api.portfolio.status route contract has an invalid field.",
                        Severity.BLOCK,
                        path=f".devpilot/interfaces/api_route_contract_registry.json:{key}",
                        metadata={"expected": value, "actual": actual},
                    )
                )
        return findings

    def _portfolio_status_findings(self, portfolio_result: CommandResult) -> list[Finding]:
        summary = portfolio_result.data.get("summary", {}) if isinstance(portfolio_result.data, dict) else {}
        expected = {
            "portfolio_status_read_only": True,
            "registered_workspaces_only": True,
            "path_isolation_passed": True,
            "state_isolation_passed": True,
            "outputs_isolation_passed": True,
            "traces_isolation_passed": True,
            "cross_workspace_refs_detected": False,
            "state_files_read": False,
            "secrets_read": False,
            "network_used": False,
            "external_api_used": False,
            "remote_execution_used": False,
            "connector_write_used": False,
            "plugin_execution_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "cross_workspace_writes": False,
        }
        findings: list[Finding] = []
        for key, value in expected.items():
            if summary.get(key) is not value:
                findings.append(
                    Finding(
                        "WORKSPACE_PORTFOLIO_STATUS_NO_GO_INVALID",
                        "Portfolio status violates a workspace portfolio no-go flag.",
                        Severity.BLOCK,
                        path=key,
                        metadata={"expected": value, "actual": summary.get(key)},
                    )
                )
        if summary.get("unregistered_workspace_policy") != "denied":
            findings.append(
                Finding(
                    "WORKSPACE_PORTFOLIO_UNREGISTERED_POLICY_INVALID",
                    "Portfolio status must deny unregistered workspaces.",
                    Severity.BLOCK,
                    path="unregistered_workspace_policy",
                    metadata={"actual": summary.get("unregistered_workspace_policy")},
                )
            )
        return findings

    def _operation_catalog_findings(self, operation_catalog_result: CommandResult) -> list[Finding]:
        catalog = operation_catalog_result.data.get("catalog", {}) if isinstance(operation_catalog_result.data, dict) else {}
        operations = catalog.get("operations", []) if isinstance(catalog, dict) else []
        operation = next((item for item in operations if isinstance(item, dict) and item.get("operation_id") == "portfolio.status"), None)
        if not isinstance(operation, dict):
            return [Finding("WORKSPACE_PORTFOLIO_OPERATION_MISSING", "ApplicationOperationCatalog must expose portfolio.status.", Severity.BLOCK)]
        findings: list[Finding] = []
        if operation.get("service") != "PortfolioApplicationService":
            findings.append(Finding("WORKSPACE_PORTFOLIO_OPERATION_SERVICE_INVALID", "portfolio.status must be served by PortfolioApplicationService.", Severity.BLOCK, metadata={"service": operation.get("service")}))
        if "GET /api/v1/portfolio/status" not in operation.get("api_routes", []):
            findings.append(Finding("WORKSPACE_PORTFOLIO_OPERATION_API_ROUTE_MISSING", "portfolio.status must be bound to GET /api/v1/portfolio/status.", Severity.BLOCK))
        if operation.get("writes_files") is not False:
            findings.append(Finding("WORKSPACE_PORTFOLIO_OPERATION_WRITES_FILES", "portfolio.status must stay read-only.", Severity.BLOCK))
        return findings

    def _documentation_findings(self) -> list[Finding]:
        required = {
            "README.md": ["POST-H-016-E", WORKSPACE_PORTFOLIO_HARDENING_SUBGATE],
            "docs/05_operations/runbook.md": ["POST-H-016-E", WORKSPACE_PORTFOLIO_HARDENING_SUBGATE],
            "docs/05_operations/workspace_portfolio_runbook.md": ["POST-H-016-E", WORKSPACE_PORTFOLIO_HARDENING_SUBGATE],
            "docs/05_operations/workspace_onboarding_checklist.md": ["Workspace onboarding checklist", "workspace registry-validate", "workspace isolation-check"],
            "docs/POST-H-016_workspace_portfolio_hardening.md": ["POST-H-016-E", WORKSPACE_PORTFOLIO_HARDENING_SUBGATE],
            "docs/backlogs/POST-H-016_workspace_portfolio_hardening.md": ['implementation_status: "closed"', 'current_micro_sprint: "POST-H-016-E"'],
        }
        findings: list[Finding] = []
        for relative, markers in required.items():
            path = self.root / relative
            if not path.exists():
                findings.append(Finding("WORKSPACE_PORTFOLIO_DOC_MISSING", "Required workspace portfolio document is missing.", Severity.BLOCK, path=relative))
                continue
            text = path.read_text(encoding="utf-8")
            for marker in markers:
                if marker not in text:
                    findings.append(
                        Finding(
                            "WORKSPACE_PORTFOLIO_DOC_MARKER_MISSING",
                            "Required workspace portfolio documentation marker is missing.",
                            Severity.BLOCK,
                            path=relative,
                            metadata={"marker": marker},
                        )
                    )
        return findings

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(render_workspace_portfolio_hardening_markdown(report), encoding="utf-8")
        return {"json": _rel(json_path, self.root), "markdown": _rel(markdown_path, self.root)}

    def _prefixed_findings(self, result: CommandResult, *, prefix: str) -> list[Finding]:
        return [
            Finding(
                id=f"WORKSPACE_PORTFOLIO_{prefix.upper().replace('-', '_')}_{finding.id}",
                message=finding.message,
                severity=finding.severity,
                path=finding.path,
                metadata={"source": prefix, **(finding.metadata or {})},
            )
            for finding in result.findings
            if finding.severity in {Severity.WARNING, Severity.FAIL, Severity.BLOCK, Severity.ERROR}
        ]


def render_workspace_portfolio_hardening_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# POST-H-016-E — Workspace portfolio hardening report",
        "",
        f"Status: `{'PASS' if summary.get('workspace_portfolio_hardening_ready') else 'BLOCK'}`",
        "",
        "## Summary",
        "",
        f"- Subgate: `{summary.get('quality_gate_subgate')}`",
        f"- Registry OK: `{summary.get('registry_ok')}`",
        f"- Isolation OK: `{summary.get('isolation_ok')}`",
        f"- Portfolio status OK: `{summary.get('portfolio_status_ok')}`",
        f"- Operation catalog OK: `{summary.get('operation_catalog_ok')}`",
        f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
        "",
        "## Safety",
        "",
        "```text",
        "local_first=true",
        "read_only=true",
        "dry_run=true",
        "network_used=false",
        "external_api_used=false",
        "remote_execution_enabled=false",
        "connector_write_enabled=false",
        "plugin_execution_enabled=false",
        "source_mutations_performed=false",
        "```",
        "",
    ]
    return "\n".join(lines)


def _result_projection(result: CommandResult) -> dict[str, Any]:
    return {
        "command": result.command,
        "ok": result.ok,
        "exit_code": int(result.exit_code),
        "summary": (result.data or {}).get("summary", {}),
        "findings_total": len(result.findings),
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
