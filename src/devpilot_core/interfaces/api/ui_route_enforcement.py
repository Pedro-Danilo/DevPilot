from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.schemas import SchemaValidator

from .contract_drift import ApiContractDriftGuard, ApiContractDriftOptions
from .security_hardening import LocalApiSecurityHardeningOptions, LocalApiSecurityHardeningRunner
from .shell_gate import UiApiIndustrialShellGate, UiApiIndustrialShellGateOptions
from .ui_contracts import DEFAULT_API_ROUTE_CONTRACT_REGISTRY, DEFAULT_UI_ROUTE_CONTRACT_REGISTRY, UiRouteContractRegistryValidator
from .visual_smoke_report import UiVisualSmokeOptions, UiVisualSmokeReporter
from .operator_flow_smoke import OperatorFlowSmokeOptions, OperatorFlowSmokeRunner

POST_H_028_E_CREATED_BY = "POST-H-028-E"
UI_ROUTE_ENFORCEMENT_COMMAND = "api ui-route-enforcement"
UI_ROUTE_ENFORCEMENT_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-UI-ROUTE-ENFORCEMENT-REPORT-V1"
UI_ROUTE_ENFORCEMENT_REPORT_CONTRACT = "UiRouteEnforcementReport"
DEFAULT_UI_ROUTE_ENFORCEMENT_REPORT_JSON = Path("outputs/reports/ui_route_enforcement_report.json")
DEFAULT_UI_ROUTE_ENFORCEMENT_REPORT_MARKDOWN = Path("outputs/reports/ui_route_enforcement_report.md")
UI_API_LOCAL_HARDENING_SUBGATE = "ui-api-local-hardening"

_EXPECTED_CRITICAL_ROUTES = {
    "ui.dashboard",
    "ui.reports",
    "ui.traces",
    "ui.approvals",
    "ui.settings",
    "ui.workspace-documents",
}

_EXPECTED_CRITICAL_VIEW_FILES = {
    "ui/web/src/pages/Dashboard.ts",
    "ui/web/src/pages/ReportsView.ts",
    "ui/web/src/pages/TracesView.ts",
    "ui/web/src/pages/ApprovalCenterView.ts",
    "ui/web/src/pages/SettingsView.ts",
    "ui/web/src/pages/OperatorDashboard.ts",
    "ui/web/src/pages/WorkspaceDocumentsView.ts",
    "ui/web/src/components/DocumentTree.ts",
    "ui/web/src/components/DocumentViewer.ts",
}

_REQUIRED_STATE_FLAGS = ("loading", "empty", "error", "block_visible")
_REQUIRED_STATUS_VISIBILITY = {"PASS", "BLOCK", "ERROR", "PENDING"}
_NO_GO_FLAGS = (
    "remote_execution_allowed",
    "connector_write_allowed",
    "plugin_execution_allowed",
    "external_api_allowed",
)
_FORBIDDEN_ACTION_MARKERS = (
    "/patch/apply",
    "patch-apply</option>",
    "patch_apply",
    "rollback-execute</option>",
    "/rollback/execute",
    "refactor-execute</option>",
    "/refactor/execute",
    "tests-run</option>",
    "/tests/run",
    "git-push</option>",
    "/git/push",
    "deploy</option>",
    "/deploy",
)
_FORBIDDEN_BOUNDARY_MARKERS = (
    "from 'devpilot_core",
    'from "devpilot_core',
    "import devpilot_core",
    "child_process",
    "node:fs",
    "fs.readFile",
    ".devpilot/",
    "outputs/",
)

_CLIENT_METHOD_TO_API_ROUTES: dict[str, tuple[str, ...]] = {
    "workspaceStatus": ("api.workspace.status",),
    "applicationContract": ("api.application.contract",),
    "standardsStatus": ("api.standards.status",),
    "miasiStatus": ("api.miasi.status",),
    "readiness": ("api.validation.readiness",),
    "listReports": ("api.reports.list",),
    "readReport": ("api.reports.read",),
    "listTraces": ("api.traces.list",),
    "inspectTrace": ("api.traces.inspect",),
    "metricsSummary": ("api.metrics.summary",),
    "listApprovals": ("api.approvals.list",),
    "showApproval": ("api.approvals.show",),
    "requestApproval": ("api.approvals.request",),
    "decideApproval": ("api.approvals.approve", "api.approvals.deny"),
    "runDryRunAction": ("api.actions.dry_run",),
    "settingsWorkspace": ("api.settings.workspace",),
    "settingsProviders": ("api.settings.providers",),
    "settingsPolicy": ("api.settings.policy",),
    "securityPosture": ("api.security.posture",),
    "operatorDashboard": ("api.operator.dashboard",),
    "planProviderChange": ("api.settings.providers.plan",),
    "listWorkspaceDocuments": ("api.workspace.documents.list",),
    "readWorkspaceDocument": ("api.workspace.documents.read",),
    "workspaceDocumentMetadata": ("api.workspace.documents.metadata",),
}


@dataclass(frozen=True)
class UiRouteEnforcementOptions:
    registry_path: str | Path = DEFAULT_UI_ROUTE_CONTRACT_REGISTRY
    api_registry_path: str | Path = DEFAULT_API_ROUTE_CONTRACT_REGISTRY
    output_json: str | Path = DEFAULT_UI_ROUTE_ENFORCEMENT_REPORT_JSON
    output_markdown: str | Path = DEFAULT_UI_ROUTE_ENFORCEMENT_REPORT_MARKDOWN
    write_report: bool = False
    run_npm_smoke: bool = False
    npm_timeout_seconds: int = 45


class UiRouteEnforcementRunner:
    """POST-H-028-E blocking enforcement for the local UI route registry.

    This runner upgrades the POST-H-014-C UI route contract registry from an
    advisory/static contract into a blocking local hardening signal. It verifies
    that critical UI surfaces are registered, source files are present, API
    calls made by each route are allowed by that route contract, state contracts
    are complete, no-go capability flags remain disabled and forbidden UI action
    controls/boundary breaks are absent. It never starts a server, opens sockets,
    reads runtime outputs from the browser, calls external APIs or mutates source.
    """

    def __init__(self, root: Path, options: UiRouteEnforcementOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or UiRouteEnforcementOptions()
        self.registry_path = Path(self.options.registry_path)
        self.api_registry_path = Path(self.options.api_registry_path)

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        registry = self._load_json(self.registry_path, findings, "UI_ROUTE_ENFORCEMENT_REGISTRY_LOAD_ERROR")
        api_registry = self._load_json(self.api_registry_path, findings, "UI_ROUTE_ENFORCEMENT_API_REGISTRY_LOAD_ERROR")

        base_contract_result = UiRouteContractRegistryValidator(
            self.root,
            registry_path=self.registry_path,
            api_registry_path=self.api_registry_path,
        ).validate()
        findings.extend(self._prefixed_findings(base_contract_result, "UI_ROUTE_BASE_CONTRACT"))

        routes = [item for item in (registry or {}).get("routes", []) if isinstance(item, dict)]
        api_routes = [item for item in (api_registry or {}).get("routes", []) if isinstance(item, dict)]
        api_route_ids = {str(route.get("route_id")) for route in api_routes}
        checks = {
            "registry_contract": self._registry_contract_check(base_contract_result),
            "critical_routes": self._critical_routes_check(routes, findings),
            "allowed_api_routes": self._allowed_api_routes_check(routes, api_route_ids, findings),
            "state_contracts": self._state_contracts_check(routes, findings),
            "route_source_calls": self._route_source_api_call_check(routes, findings),
            "ui_boundary": self._ui_boundary_check(routes, findings),
            "action_allowlist": self._action_allowlist_check(findings),
            "npm_smoke": self._npm_smoke_check(findings),
        }

        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
        ok = not blocking and all(bool(item.get("ok")) for item in checks.values())
        summary = {
            "created_by": POST_H_028_E_CREATED_BY,
            "status": "implemented-initial",
            "decision": "PASS" if ok else "BLOCK",
            "ui_route_registry_enforcement_passed": ok,
            "critical_routes_total": len(_EXPECTED_CRITICAL_ROUTES),
            "critical_routes_registered_total": int(checks["critical_routes"].get("critical_routes_registered_total", 0)),
            "critical_view_files_total": len(_EXPECTED_CRITICAL_VIEW_FILES),
            "critical_view_files_registered_total": int(checks["critical_routes"].get("critical_view_files_registered_total", 0)),
            "routes_total": len(routes),
            "allowed_api_routes_total": int(checks["allowed_api_routes"].get("allowed_api_routes_total", 0)),
            "unregistered_api_refs_total": int(checks["allowed_api_routes"].get("unregistered_api_refs_total", 0)) + int(checks["route_source_calls"].get("missing_allowed_api_calls_total", 0)),
            "missing_state_contracts_total": int(checks["state_contracts"].get("missing_state_contracts_total", 0)),
            "no_go_violations_total": int(checks["state_contracts"].get("no_go_violations_total", 0)),
            "forbidden_ui_actions_total": int(checks["action_allowlist"].get("forbidden_ui_actions_total", 0)),
            "filesystem_core_imports_total": int(checks["ui_boundary"].get("filesystem_core_imports_total", 0)),
            "npm_smoke_required": bool(self.options.run_npm_smoke),
            "npm_smoke_passed": bool(checks["npm_smoke"].get("ok")),
            "checks_total": len(checks),
            "checks_passed": sum(1 for item in checks.values() if bool(item.get("ok"))),
            "findings_total": len(findings),
            "warnings_total": len(warnings),
            "blocking_findings_total": len(blocking),
            "report_schema_valid": False,
            "reports_written": False,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        report = {
            "schema_version": "1.0",
            "schema_id": UI_ROUTE_ENFORCEMENT_REPORT_SCHEMA_ID,
            "report_id": "devpilot-ui-route-enforcement-report",
            "created_by": POST_H_028_E_CREATED_BY,
            "status": "pass" if ok else "blocked",
            "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "summary": summary,
            "checks": checks,
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
                "llm_judge_used": False,
                "server_started": False,
                "sockets_opened": False,
                "browser_required_for_core": False,
                "filesystem_read_from_ui": False,
                "core_python_import_from_ui": False,
            },
            "findings": [finding.to_dict() for finding in findings],
            "notes": [
                "POST-H-028-E enforces UiRouteContractRegistry as a blocking local UI/API boundary guard.",
                "Critical UI routes must be registered, local-only, state-complete and mapped only to known ApiRouteContractRegistry routes.",
                "Forbidden UI actions, filesystem reads, core Python imports, remote execution, connector write and plugin execution remain blocked.",
                "This is implemented-initial local route enforcement; browser E2E and enterprise UI routing remain future evolution.",
            ],
        }

        schema_result = SchemaValidator(self.root).validate_payload(
            schema=UI_ROUTE_ENFORCEMENT_REPORT_CONTRACT,
            payload=report,
            instance_label="in-memory:ui_route_enforcement_report",
        )
        if not schema_result.ok:
            findings.extend(self._prefixed_findings(schema_result, "UI_ROUTE_ENFORCEMENT_SCHEMA"))
            ok = False
            blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
            report["summary"]["decision"] = "BLOCK"
            report["summary"]["ui_route_registry_enforcement_passed"] = False
            report["summary"]["report_schema_valid"] = False
            report["summary"]["blocking_findings_total"] = len(blocking)
            report["findings"] = [finding.to_dict() for finding in findings]
        else:
            report["summary"]["report_schema_valid"] = True

        reports: dict[str, str] = {}
        if self.options.write_report:
            report["summary"]["reports_written"] = True
            reports = self._write_reports(report)
        exit_code = ExitCode.PASS if ok else exit_code_for_findings(blocking, default_ok=False)
        return CommandResult(
            command=UI_ROUTE_ENFORCEMENT_COMMAND,
            ok=ok,
            exit_code=exit_code,
            message="UI route registry enforcement passed." if ok else "UI route registry enforcement found blocking issues.",
            data={"summary": report["summary"], "report": report, "reports": reports, "notes": report["notes"]},
            findings=findings or [Finding("UI_ROUTE_ENFORCEMENT_PASS", "UI route registry enforcement passed.", Severity.INFO, metadata=report["summary"])],
        )

    def _load_json(self, path: Path, findings: list[Finding], finding_id: str) -> dict[str, Any]:
        try:
            return json.loads((self.root / path).read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(Finding(finding_id, f"Could not load {path}: {exc}", Severity.ERROR, path=str(path)))
            return {}

    def _registry_contract_check(self, result: CommandResult) -> dict[str, Any]:
        summary = dict((result.data or {}).get("summary") or {})
        return {
            "ok": result.ok,
            "command": result.command,
            "exit_code": int(result.exit_code),
            "schema_valid": bool(summary.get("schema_valid")),
            "routes_total": int(summary.get("routes_total", 0)),
            "blocking_findings_total": sum(1 for item in result.findings if item.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}),
        }

    def _critical_routes_check(self, routes: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        route_ids = {str(route.get("route_id")) for route in routes}
        registered_sources = {str(path) for route in routes for path in (route.get("source_files") or [])}
        missing_routes = sorted(_EXPECTED_CRITICAL_ROUTES - route_ids)
        missing_files = sorted(_EXPECTED_CRITICAL_VIEW_FILES - registered_sources)
        for route_id in missing_routes:
            findings.append(Finding("UI_ROUTE_ENFORCEMENT_CRITICAL_ROUTE_MISSING", f"Critical UI route is not registered: {route_id}", Severity.BLOCK, path=str(self.registry_path), metadata={"route_id": route_id}))
        for source_file in missing_files:
            findings.append(Finding("UI_ROUTE_ENFORCEMENT_CRITICAL_VIEW_FILE_UNREGISTERED", f"Critical UI view source is not registered: {source_file}", Severity.BLOCK, path=source_file))
        return {
            "ok": not missing_routes and not missing_files,
            "expected_critical_routes": sorted(_EXPECTED_CRITICAL_ROUTES),
            "missing_critical_routes": missing_routes,
            "critical_routes_registered_total": len(_EXPECTED_CRITICAL_ROUTES) - len(missing_routes),
            "expected_critical_view_files": sorted(_EXPECTED_CRITICAL_VIEW_FILES),
            "missing_critical_view_files": missing_files,
            "critical_view_files_registered_total": len(_EXPECTED_CRITICAL_VIEW_FILES) - len(missing_files),
        }

    def _allowed_api_routes_check(self, routes: list[dict[str, Any]], api_route_ids: set[str], findings: list[Finding]) -> dict[str, Any]:
        unknown: list[dict[str, str]] = []
        total = 0
        for route in routes:
            route_id = str(route.get("route_id"))
            for api_route in route.get("allowed_api_routes", []) or []:
                total += 1
                if str(api_route) not in api_route_ids:
                    item = {"route_id": route_id, "api_route_id": str(api_route)}
                    unknown.append(item)
                    findings.append(Finding("UI_ROUTE_ENFORCEMENT_UNKNOWN_API_ROUTE", f"UI route {route_id} references unknown API route {api_route}.", Severity.BLOCK, path=str(self.registry_path), metadata=item))
        return {"ok": not unknown, "allowed_api_routes_total": total, "unregistered_api_refs_total": len(unknown), "unknown_api_routes": unknown}

    def _state_contracts_check(self, routes: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        missing_state: list[str] = []
        missing_status: list[str] = []
        no_go: list[dict[str, Any]] = []
        mutation_control_violations: list[str] = []
        for route in routes:
            route_id = str(route.get("route_id"))
            state = route.get("state_contract") or {}
            if not all(state.get(flag) is True for flag in _REQUIRED_STATE_FLAGS):
                missing_state.append(route_id)
                findings.append(Finding("UI_ROUTE_ENFORCEMENT_REQUIRED_STATE_MISSING", f"UI route {route_id} lacks a required state contract.", Severity.BLOCK, path=str(self.registry_path), metadata={"route_id": route_id, "required": list(_REQUIRED_STATE_FLAGS)}))
            statuses = set(route.get("status_visibility") or [])
            if not _REQUIRED_STATUS_VISIBILITY.issubset(statuses):
                missing_status.append(route_id)
                findings.append(Finding("UI_ROUTE_ENFORCEMENT_STATUS_VISIBILITY_MISSING", f"UI route {route_id} lacks required status visibility.", Severity.BLOCK, path=str(self.registry_path), metadata={"route_id": route_id, "required": sorted(_REQUIRED_STATUS_VISIBILITY)}))
            for flag in _NO_GO_FLAGS:
                if route.get(flag) is not False:
                    item = {"route_id": route_id, "flag": flag, "value": route.get(flag)}
                    no_go.append(item)
                    findings.append(Finding("UI_ROUTE_ENFORCEMENT_NO_GO_FLAG_ENABLED", f"UI route {route_id} enables no-go flag {flag}.", Severity.BLOCK, path=str(self.registry_path), metadata=item))
            if route.get("shows_mutation_controls") is True:
                mutation = route.get("mutation_controls") or {}
                if mutation.get("destructive_action_allowed") is not False or not str(mutation.get("justification", "")).strip():
                    mutation_control_violations.append(route_id)
                    findings.append(Finding("UI_ROUTE_ENFORCEMENT_MUTATION_CONTROL_UNSAFE", f"UI route {route_id} mutation controls are not explicitly safe.", Severity.BLOCK, path=str(self.registry_path), metadata={"route_id": route_id}))
        return {
            "ok": not missing_state and not missing_status and not no_go and not mutation_control_violations,
            "missing_state_contracts_total": len(missing_state),
            "missing_status_visibility_total": len(missing_status),
            "no_go_violations_total": len(no_go),
            "mutation_control_violations_total": len(mutation_control_violations),
            "missing_state_routes": missing_state,
            "missing_status_routes": missing_status,
            "no_go_violations": no_go,
        }

    def _route_source_api_call_check(self, routes: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        missing: list[dict[str, str]] = []
        calls_total = 0
        for route in routes:
            route_id = str(route.get("route_id"))
            allowed = set(route.get("allowed_api_routes") or [])
            sources = self._route_sources(route)
            combined = "\n".join(sources.values())
            called_methods = sorted(set(re.findall(r"\bclient\.([A-Za-z_][A-Za-z0-9_]*)\s*\(", combined)))
            for method in called_methods:
                expected_routes = _CLIENT_METHOD_TO_API_ROUTES.get(method)
                if not expected_routes:
                    continue
                calls_total += 1
                for api_route_id in expected_routes:
                    if api_route_id not in allowed:
                        item = {"route_id": route_id, "client_method": method, "api_route_id": api_route_id}
                        missing.append(item)
                        findings.append(Finding("UI_ROUTE_ENFORCEMENT_CLIENT_CALL_NOT_ALLOWED", f"UI route {route_id} calls client.{method} but does not allow {api_route_id}.", Severity.BLOCK, path=str(self.registry_path), metadata=item))
        return {"ok": not missing, "client_calls_checked_total": calls_total, "missing_allowed_api_calls_total": len(missing), "missing_allowed_api_calls": missing}

    def _ui_boundary_check(self, routes: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        source_paths = {"ui/web/src/main.ts", "ui/web/src/api/client.ts"}
        for route in routes:
            for source in route.get("source_files", []) or []:
                source_paths.add(str(source))
        violations: list[dict[str, str]] = []
        checked = 0
        for source_path in sorted(source_paths):
            path = self.root / source_path
            if not path.exists():
                continue
            checked += 1
            content = path.read_text(encoding="utf-8")
            for marker in _FORBIDDEN_BOUNDARY_MARKERS:
                if marker in content:
                    item = {"source_file": source_path, "marker": marker}
                    violations.append(item)
                    findings.append(Finding("UI_ROUTE_ENFORCEMENT_UI_BOUNDARY_BREAK", f"UI source file contains forbidden boundary marker {marker}: {source_path}", Severity.BLOCK, path=source_path, metadata=item))
        return {"ok": not violations, "source_files_checked_total": checked, "filesystem_core_imports_total": len(violations), "violations": violations}

    def _action_allowlist_check(self, findings: list[Finding]) -> dict[str, Any]:
        source_paths = ["ui/web/src/components/DryRunActionForm.ts", "ui/web/src/pages/ApprovalCenterView.ts"]
        violations: list[dict[str, str]] = []
        combined = ""
        for source_path in source_paths:
            path = self.root / source_path
            if path.exists():
                combined += path.read_text(encoding="utf-8") + "\n"
        for marker in _FORBIDDEN_ACTION_MARKERS:
            if marker in combined:
                item = {"marker": marker}
                violations.append(item)
                findings.append(Finding("UI_ROUTE_ENFORCEMENT_FORBIDDEN_UI_ACTION", f"Forbidden UI action/control marker found: {marker}", Severity.BLOCK, path="ui/web/src", metadata=item))
        return {"ok": not violations, "forbidden_ui_actions_total": len(violations), "forbidden_markers_found": violations}

    def _npm_smoke_check(self, findings: list[Finding]) -> dict[str, Any]:
        if not self.options.run_npm_smoke:
            return {"ok": True, "skipped": True, "command": "npm --prefix ui/web test", "returncode": None, "stdout_tail": "", "stderr_tail": ""}
        npm = shutil.which("npm.cmd") or shutil.which("npm.exe") or shutil.which("npm")
        if npm is None:
            findings.append(Finding("UI_ROUTE_ENFORCEMENT_NPM_MISSING", "npm is required for the explicit UI route enforcement npm smoke.", Severity.BLOCK, path="ui/web/package.json"))
            return {"ok": False, "skipped": False, "command": "npm --prefix ui/web test", "returncode": None, "stdout_tail": "", "stderr_tail": "npm not found"}
        completed = subprocess.run([npm, "--prefix", "ui/web", "test"], cwd=self.root, text=True, capture_output=True, check=False, timeout=self.options.npm_timeout_seconds)
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        ok = completed.returncode == 0 and "DEVPL WEB UI SMOKE TEST: PASS" in stdout
        if not ok:
            findings.append(Finding("UI_ROUTE_ENFORCEMENT_NPM_SMOKE_BLOCK", "npm --prefix ui/web test failed or did not emit the expected PASS marker.", Severity.BLOCK, path="ui/web/scripts/smoke-test.mjs", metadata={"returncode": completed.returncode, "stdout_tail": stdout[-500:], "stderr_tail": stderr[-500:]}))
        return {"ok": ok, "skipped": False, "command": "npm --prefix ui/web test", "returncode": completed.returncode, "stdout_tail": stdout[-1000:], "stderr_tail": stderr[-1000:], "pass_marker_detected": "DEVPL WEB UI SMOKE TEST: PASS" in stdout}

    def _route_sources(self, route: dict[str, Any]) -> dict[str, str]:
        out: dict[str, str] = {}
        for source_file in route.get("source_files", []) or []:
            path = self.root / str(source_file)
            if path.exists():
                out[str(source_file)] = path.read_text(encoding="utf-8")
        return out

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        md_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(self._render_markdown(report), encoding="utf-8")
        return {"json": str(self.options.output_json).replace("\\", "/"), "markdown": str(self.options.output_markdown).replace("\\", "/")}

    def _render_markdown(self, report: dict[str, Any]) -> str:
        summary = report["summary"]
        lines = [
            "# POST-H-028-E — UI route registry enforcement report",
            "",
            f"Decision: **{summary['decision']}**",
            "",
            "## Summary",
            "",
        ]
        for key in sorted(summary):
            lines.append(f"- `{key}`: `{summary[key]}`")
        lines.extend(["", "## Notes", ""])
        for note in report.get("notes", []):
            lines.append(f"- {note}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _prefixed_findings(result: CommandResult, prefix: str) -> list[Finding]:
        prefixed: list[Finding] = []
        for finding in result.findings:
            if finding.severity == Severity.INFO:
                continue
            prefixed.append(Finding(id=f"{prefix}_{finding.id}", message=finding.message, severity=finding.severity, path=finding.path, metadata={"source_command": result.command, "source_finding_id": finding.id, **(finding.metadata or {})}))
        return prefixed


class UiApiLocalHardeningGate:
    """POST-H-028-E aggregate gate for the completed UI/API local hardening wave."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()

    def run(self) -> CommandResult:
        subresults = [
            ("api-contract-drift-guard", ApiContractDriftGuard(self.root, ApiContractDriftOptions(write_report=False)).run()),
            ("local-api-security-hardening", LocalApiSecurityHardeningRunner(self.root, LocalApiSecurityHardeningOptions(write_report=False)).run()),
            ("ui-visual-smoke", UiVisualSmokeReporter(self.root, UiVisualSmokeOptions(write_report=False)).run()),
            ("operator-flow-smoke", OperatorFlowSmokeRunner(self.root, OperatorFlowSmokeOptions(write_report=False)).run()),
            ("ui-route-enforcement", UiRouteEnforcementRunner(self.root, UiRouteEnforcementOptions(write_report=False, run_npm_smoke=False)).run()),
            ("ui-api-industrial-shell", UiApiIndustrialShellGate(self.root, UiApiIndustrialShellGateOptions(write_report=False, run_ui_smoke=True)).run()),
        ]
        findings: list[Finding] = []
        records: list[dict[str, Any]] = []
        for subgate_id, result in subresults:
            records.append({"id": subgate_id, "command": result.command, "ok": result.ok, "exit_code": int(result.exit_code), "summary": (result.data or {}).get("summary", {})})
            for finding in result.findings:
                if finding.severity == Severity.INFO:
                    continue
                findings.append(Finding(id=f"UI_API_LOCAL_HARDENING_{subgate_id.upper().replace('-', '_')}_{finding.id}", message=finding.message, severity=finding.severity, path=finding.path, metadata={"subgate": subgate_id, "source_command": result.command, **(finding.metadata or {})}))
        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        ok = all(record["ok"] for record in records) and not blocking
        summary = {
            "quality_gate_subgate": UI_API_LOCAL_HARDENING_SUBGATE,
            "created_by": POST_H_028_E_CREATED_BY,
            "decision": "PASS" if ok else "BLOCK",
            "ui_api_local_hardening_passed": ok,
            "subgates_total": len(records),
            "subgates_passed": sum(1 for record in records if record["ok"]),
            "blocking_findings_total": len(blocking),
            "cors_wildcard_enabled": False,
            "non_local_bind_allowed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "external_api_required": False,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        return CommandResult(
            command=f"quality subgate {UI_API_LOCAL_HARDENING_SUBGATE}",
            ok=ok,
            exit_code=ExitCode.PASS if ok else exit_code_for_findings(blocking, default_ok=False),
            message="UI/API local hardening aggregate gate passed." if ok else "UI/API local hardening aggregate gate blocked.",
            data={"summary": summary, "subgates": records, "notes": ["POST-H-028-E closes the UI/API local hardening wave as implemented-initial/local-first."]},
            findings=findings or [Finding("UI_API_LOCAL_HARDENING_PASS", "UI/API local hardening aggregate gate passed.", Severity.INFO, metadata=summary)],
        )


def run_ui_route_enforcement(root: Path, options: UiRouteEnforcementOptions | None = None) -> CommandResult:
    return UiRouteEnforcementRunner(root, options).run()
