from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.schemas import SchemaValidator

POST_H_028_C_CREATED_BY = "POST-H-028-C"
UI_VISUAL_SMOKE_COMMAND = "api visual-smoke-report"
UI_VISUAL_SMOKE_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-UI-VISUAL-SMOKE-REPORT-V1"
UI_VISUAL_SMOKE_REPORT_CONTRACT = "UiVisualSmokeReport"
DEFAULT_UI_VISUAL_SMOKE_REPORT_JSON = Path("outputs/reports/ui_visual_smoke_report.json")
DEFAULT_UI_VISUAL_SMOKE_REPORT_MARKDOWN = Path("outputs/reports/ui_visual_smoke_report.md")
UI_ROUTE_CONTRACT_REGISTRY = Path(".devpilot/interfaces/ui_route_contract_registry.json")
API_ROUTE_CONTRACT_REGISTRY = Path(".devpilot/interfaces/api_route_contract_registry.json")
WEB_ROOT = Path("ui/web")


@dataclass(frozen=True)
class UiVisualSmokeOptions:
    """Options for the POST-H-028-C local UI visual smoke report.

    The runner is intentionally dependency-light for core pytest and quality gates:
    it performs static/contractual renderability checks over the Web UI source,
    route registries and npm smoke contract. Browser tooling remains optional and
    advisory until Playwright is installed explicitly by the operator.
    """

    output_json: str | Path = DEFAULT_UI_VISUAL_SMOKE_REPORT_JSON
    output_markdown: str | Path = DEFAULT_UI_VISUAL_SMOKE_REPORT_MARKDOWN
    write_report: bool = False
    require_browser_tooling: bool = False


class UiVisualSmokeReporter:
    """POST-H-028-C visual smoke reporter for the local UI/API shell.

    This report verifies that critical operator surfaces are renderable and
    contract-visible without running a browser in the core Python gate. It keeps
    screenshots and browser execution opt-in to avoid making the >1100-test suite
    depend on Node/Playwright. The output clearly separates the PASS/BLOCK static
    visual contract from the advisory browser-tooling status.
    """

    def __init__(self, root: Path, options: UiVisualSmokeOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or UiVisualSmokeOptions()
        self.web_root = self.root / WEB_ROOT

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        ui_registry = self._load_json(UI_ROUTE_CONTRACT_REGISTRY, findings)
        api_registry = self._load_json(API_ROUTE_CONTRACT_REGISTRY, findings)
        package = self._load_json(WEB_ROOT / "package.json", findings)
        source_files = self._read_ui_source_files(findings)
        combined_source = "\n".join(source_files.values())

        route_checks = self._route_checks(ui_registry, api_registry, source_files, findings)
        view_checks = self._view_checks(source_files, combined_source, findings)
        state_checks = self._state_checks(combined_source, findings)
        safety_check = self._safety_check(package, source_files, findings)
        screenshot_check = self._screenshot_hygiene_check(findings)
        tooling_check = self._browser_tooling_check(package, findings)

        checks = {
            "route_contracts": route_checks,
            "critical_views": view_checks,
            "visual_states": state_checks,
            "ui_safety": safety_check,
            "screenshot_hygiene": screenshot_check,
            "browser_tooling": tooling_check,
        }
        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
        ok = not blocking
        summary = {
            "created_by": POST_H_028_C_CREATED_BY,
            "status": "implemented-initial",
            "decision": "PASS" if ok else "BLOCK",
            "visual_smoke_passed": ok,
            "critical_views_total": int(view_checks.get("critical_views_total", 0)),
            "critical_views_passed": int(view_checks.get("critical_views_passed", 0)),
            "operator_dashboard_embedded": bool(view_checks.get("operator_dashboard_embedded")),
            "states_checked_total": int(state_checks.get("states_checked_total", 0)),
            "states_visible_total": int(state_checks.get("states_visible_total", 0)),
            "empty_state_visible": bool(state_checks.get("empty_state_visible")),
            "error_state_visible": bool(state_checks.get("error_state_visible")),
            "block_state_visible": bool(state_checks.get("block_state_visible")),
            "unauthorized_state_visible": bool(state_checks.get("unauthorized_state_visible")),
            "api_down_state_visible": bool(state_checks.get("api_down_state_visible")),
            "screenshots_versioned": bool(screenshot_check.get("screenshots_versioned")),
            "screenshots_written": False,
            "screenshots_output_path": "outputs/ui-smoke/screenshots/",
            "browser_tooling_required_for_core": False,
            "browser_tooling_available": bool(tooling_check.get("browser_tooling_available")),
            "browser_smoke_status": tooling_check.get("browser_smoke_status"),
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
            "schema_id": UI_VISUAL_SMOKE_REPORT_SCHEMA_ID,
            "report_id": "devpilot-ui-visual-smoke-report",
            "created_by": POST_H_028_C_CREATED_BY,
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
                "screenshots_versioned": bool(screenshot_check.get("screenshots_versioned")),
            },
            "findings": [finding.to_dict() for finding in findings],
            "notes": [
                "POST-H-028-C adds a schema-backed UI visual smoke report for critical local operator surfaces.",
                "Core pytest remains dependency-light: browser/Playwright execution is optional and advisory unless explicitly installed by the operator.",
                "The report checks Dashboard, Report Viewer, Trace Viewer, Approval Center, Settings and embedded Operator Dashboard visual contracts.",
                "Screenshots, if generated by future browser tooling, must stay under outputs/ui-smoke or ui/web/test-results and must not be versioned.",
            ],
        }

        schema_result = SchemaValidator(self.root).validate_payload(
            schema=UI_VISUAL_SMOKE_REPORT_CONTRACT,
            payload=report,
            instance_label="in-memory:ui_visual_smoke_report",
        )
        if not schema_result.ok:
            findings.extend(_prefix_findings(schema_result.findings, "UI_VISUAL_SMOKE_REPORT_SCHEMA"))
            ok = False
            blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
            warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
            summary["decision"] = "BLOCK"
            summary["visual_smoke_passed"] = False
            summary["blocking_findings_total"] = len(blocking)
            summary["warnings_total"] = len(warnings)
            summary["findings_total"] = len(findings)
            summary["report_schema_valid"] = False
            report["status"] = "blocked"
            report["findings"] = [finding.to_dict() for finding in findings]
        else:
            summary["report_schema_valid"] = True
            report["summary"] = summary

        reports: dict[str, str] = {}
        if self.options.write_report:
            summary["reports_written"] = True
            report["summary"] = summary
            reports = self._write_reports(report)

        exit_code = ExitCode.PASS if ok else exit_code_for_findings(blocking, default_ok=False)
        return CommandResult(
            command=UI_VISUAL_SMOKE_COMMAND,
            ok=ok,
            exit_code=exit_code,
            message="UI visual smoke report passed." if ok else "UI visual smoke report blocked.",
            data={"summary": summary, "report": report, "reports": reports, "notes": report["notes"]},
            findings=findings or [Finding("UI_VISUAL_SMOKE_PASS", "UI visual smoke contract passed for critical local views.", Severity.INFO, metadata={"created_by": POST_H_028_C_CREATED_BY})],
        )

    def _load_json(self, relative: str | Path, findings: list[Finding]) -> dict[str, Any]:
        path = self.root / relative
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            findings.append(Finding("UI_VISUAL_SMOKE_JSON_MISSING", f"Required JSON file is missing: {relative}", Severity.BLOCK, path=str(relative).replace("\\", "/")))
        except json.JSONDecodeError as exc:
            findings.append(Finding("UI_VISUAL_SMOKE_JSON_INVALID", f"Required JSON file is invalid: {relative}: {exc}", Severity.ERROR, path=str(relative).replace("\\", "/")))
        return {}

    def _read_ui_source_files(self, findings: list[Finding]) -> dict[str, str]:
        files = sorted((self.web_root / "src").rglob("*.ts"))
        if not files:
            findings.append(Finding("UI_VISUAL_SMOKE_SOURCE_EMPTY", "No TypeScript source files were found under ui/web/src.", Severity.BLOCK, path="ui/web/src"))
            return {}
        sources: dict[str, str] = {}
        for path in files:
            rel = self._relative(path)
            try:
                sources[rel] = path.read_text(encoding="utf-8")
            except OSError as exc:
                findings.append(Finding("UI_VISUAL_SMOKE_SOURCE_READ_ERROR", f"Could not read UI source file {rel}: {exc}", Severity.ERROR, path=rel))
        return sources

    def _route_checks(self, ui_registry: dict[str, Any], api_registry: dict[str, Any], sources: dict[str, str], findings: list[Finding]) -> dict[str, Any]:
        routes = ui_registry.get("routes") if isinstance(ui_registry, dict) else []
        api_routes = api_registry.get("routes") if isinstance(api_registry, dict) else []
        api_ids = {route.get("route_id") for route in api_routes if isinstance(route, dict)}
        expected_routes = {"ui.dashboard", "ui.reports", "ui.traces", "ui.approvals", "ui.settings"}
        route_ids = {route.get("route_id") for route in routes if isinstance(route, dict)}
        missing_expected = sorted(expected_routes - route_ids)
        source_missing: list[str] = []
        bad_api_refs: list[str] = []
        safety_violations: list[str] = []
        state_contract_missing: list[str] = []
        for route in routes or []:
            if not isinstance(route, dict):
                continue
            route_id = str(route.get("route_id"))
            for source in route.get("source_files", []):
                if source not in sources and not (self.root / source).exists():
                    source_missing.append(f"{route_id}:{source}")
                else:
                    text = sources.get(source) or (self.root / source).read_text(encoding="utf-8")
                    if route_id not in text:
                        source_missing.append(f"{route_id}:{source}:missing-marker")
            for api_route in route.get("allowed_api_routes", []):
                if api_route not in api_ids:
                    bad_api_refs.append(f"{route_id}:{api_route}")
            if not route.get("local_only") or route.get("remote_execution_allowed") or route.get("connector_write_allowed") or route.get("plugin_execution_allowed") or route.get("external_api_allowed"):
                safety_violations.append(route_id)
            state_contract = route.get("state_contract") or {}
            if not all(state_contract.get(key) for key in ["loading", "empty", "error", "block_visible"]):
                state_contract_missing.append(route_id)
        for item in missing_expected:
            findings.append(Finding("UI_VISUAL_SMOKE_ROUTE_MISSING", "Expected critical UI route is missing from UiRouteContractRegistry.", Severity.BLOCK, metadata={"route_id": item}))
        for item in source_missing:
            findings.append(Finding("UI_VISUAL_SMOKE_ROUTE_SOURCE_MISSING", "UI route source file or route marker is missing.", Severity.BLOCK, metadata={"route_source": item}))
        for item in bad_api_refs:
            findings.append(Finding("UI_VISUAL_SMOKE_UNKNOWN_API_ROUTE", "UI route references an API route outside ApiRouteContractRegistry.", Severity.BLOCK, metadata={"api_ref": item}))
        for item in safety_violations:
            findings.append(Finding("UI_VISUAL_SMOKE_ROUTE_SAFETY_VIOLATION", "UI route violates local-only/no-go safety flags.", Severity.BLOCK, metadata={"route_id": item}))
        for item in state_contract_missing:
            findings.append(Finding("UI_VISUAL_SMOKE_STATE_CONTRACT_MISSING", "UI route state contract is incomplete.", Severity.BLOCK, metadata={"route_id": item}))
        ok = not missing_expected and not source_missing and not bad_api_refs and not safety_violations and not state_contract_missing and len(route_ids) >= 5
        return {
            "ok": ok,
            "ui_routes_total": len(route_ids),
            "expected_routes": sorted(expected_routes),
            "missing_expected_routes": missing_expected,
            "bad_api_refs": bad_api_refs,
            "source_or_marker_missing": source_missing,
            "safety_violations": safety_violations,
            "state_contract_missing": state_contract_missing,
        }

    def _view_checks(self, sources: dict[str, str], combined: str, findings: list[Finding]) -> dict[str, Any]:
        views = {
            "dashboard": ("ui/web/src/pages/Dashboard.ts", ["ui.dashboard", "renderProjectHomeEntryPanel", "dashboard-grid", "renderOperatorDashboard"]),
            "report_viewer": ("ui/web/src/pages/ReportTraceView.ts", ["Report Viewer", "ui.reports", "Sin reportes para mostrar"]),
            "trace_viewer": ("ui/web/src/pages/ReportTraceView.ts", ["Trace Viewer", "ui.traces", "Sin trazas para mostrar"]),
            "approval_center": ("ui/web/src/pages/ApprovalCenterView.ts", ["Approval Center", "ui.approvals", "Action Launcher", "Sin approvals"]),
            "settings": ("ui/web/src/pages/SettingsView.ts", ["Settings UI", "ui.settings", "Provider editor plan-only", "secretos redactados"]),
            "operator_dashboard": ("ui/web/src/pages/OperatorDashboard.ts", ["Operator Dashboard", "POST-H-015-D"]),
        }
        passed: list[str] = []
        failed: dict[str, list[str]] = {}
        for view_id, (source_path, markers) in views.items():
            text = sources.get(source_path)
            if text is None:
                failed[view_id] = [f"missing source {source_path}"]
                continue
            missing = [marker for marker in markers if marker not in text]
            if missing:
                failed[view_id] = missing
            else:
                passed.append(view_id)
        for view_id, missing in failed.items():
            findings.append(Finding("UI_VISUAL_SMOKE_CRITICAL_VIEW_NOT_RENDERABLE", "Critical UI view is missing visual smoke markers.", Severity.BLOCK, metadata={"view_id": view_id, "missing_markers": missing}))
        no_blank_dashboard = (("DevPilot Local Dashboard" in combined or "renderProjectHomeEntryPanel" in combined) and "dashboard-grid" in combined and "renderUiStateNotice" in combined)
        if not no_blank_dashboard:
            findings.append(Finding("UI_VISUAL_SMOKE_BLANK_DASHBOARD_RISK", "Dashboard lacks enough render markers to avoid a blank-screen false PASS.", Severity.BLOCK))
        return {
            "ok": not failed and no_blank_dashboard and len(passed) >= 6,
            "critical_views_total": len(views),
            "critical_views_passed": len(passed),
            "passed_views": passed,
            "failed_views": failed,
            "operator_dashboard_embedded": "renderOperatorDashboard" in sources.get("ui/web/src/pages/Dashboard.ts", ""),
            "blank_dashboard_guard": no_blank_dashboard,
        }

    def _state_checks(self, combined: str, findings: list[Finding]) -> dict[str, Any]:
        state_markers = {
            "loading_state_visible": ["loading state", "data-ui-state=\"loading\""],
            "empty_state_visible": ["empty state", "Sin reportes", "Sin trazas", "Sin approvals"],
            "error_state_visible": ["error state", "BLOCK/ERROR"],
            "block_state_visible": ["BLOCK", "ui-state--block", "block_visible"],
            "unauthorized_state_visible": ["401", "403", "Unauthorized", "Forbidden", "token local faltante", "Sesión/autenticación local no autorizada", "Credenciales inválidas"],
            "api_down_state_visible": ["API local down", "API local no disponible", "inaccesible"],
        }
        result: dict[str, Any] = {}
        missing: dict[str, list[str]] = {}
        for key, markers in state_markers.items():
            visible = any(marker in combined for marker in markers)
            result[key] = visible
            if not visible:
                missing[key] = markers
        for key, markers in missing.items():
            findings.append(Finding("UI_VISUAL_SMOKE_STATE_NOT_VISIBLE", "Required visual state marker is not visible in UI sources.", Severity.BLOCK, metadata={"state": key, "accepted_markers": markers}))
        result.update(
            {
                "ok": not missing,
                "states_checked_total": len(state_markers),
                "states_visible_total": len(state_markers) - len(missing),
                "missing_states": sorted(missing),
            }
        )
        return result

    def _safety_check(self, package: dict[str, Any], sources: dict[str, str], findings: list[Finding]) -> dict[str, Any]:
        combined = "\n".join(sources.values())
        forbidden = [
            "devpilot_core",
            "from 'fs'",
            'from "fs"',
            "fs.readFile",
            "writeFile",
            "child_process",
            "outputs/",
            ".devpilot/",
            "/patch/apply",
            "/rollback/execute",
            "/git/push",
        ]
        hits = [marker for marker in forbidden if marker in combined]
        devpilot = package.get("devpilot") if isinstance(package, dict) else {}
        flag_violations = []
        uoc005_active = bool(devpilot.get("uoc005ApprovalBinding"))
        expected_flags = {
            "apiOnly": True,
            "dryRunOnly": False if uoc005_active else True,
            "externalApiUsed": False,
            "remoteExecutionEnabled": False,
            "connectorWriteEnabled": False,
            "pluginExecutionEnabled": False,
        }
        if uoc005_active:
            expected_flags.update({
                "genericPatchApplyEnabled": False,
                "genericRollbackEnabled": False,
            })
            if devpilot.get("documentWriteMode") != "approval-gated-atomic-uoc005":
                flag_violations.append("documentWriteMode")
        for key, value in expected_flags.items():
            if devpilot.get(key) is not value:
                flag_violations.append(key)
        for marker in hits:
            findings.append(Finding("UI_VISUAL_SMOKE_UI_SAFETY_FORBIDDEN_MARKER", "UI source contains a forbidden local/runtime marker.", Severity.BLOCK, metadata={"marker": marker}))
        for flag in flag_violations:
            findings.append(Finding("UI_VISUAL_SMOKE_PACKAGE_SAFETY_FLAG_DRIFT", "ui/web/package.json devpilot safety flag drifted.", Severity.BLOCK, metadata={"flag": flag}))
        return {
            "ok": not hits and not flag_violations,
            "forbidden_markers_found": hits,
            "flag_violations": flag_violations,
            "post_h_028_c_flag": bool(devpilot.get("postH028C")),
            "ui_visual_smoke_script": devpilot.get("uiVisualSmokeScript"),
        }

    def _screenshot_hygiene_check(self, findings: list[Finding]) -> dict[str, Any]:
        gitignore = (self.root / ".gitignore").read_text(encoding="utf-8") if (self.root / ".gitignore").exists() else ""
        web_gitignore = (self.web_root / ".gitignore").read_text(encoding="utf-8") if (self.web_root / ".gitignore").exists() else ""
        ignored = "outputs/ui-smoke/" in gitignore and "ui/web/test-results/" in gitignore and "playwright-report/" in web_gitignore and "test-results/" in web_gitignore
        versioned_candidates = [
            path for path in [self.root / "outputs" / "ui-smoke", self.web_root / "test-results", self.web_root / "playwright-report"] if path.exists()
        ]
        screenshots_versioned = bool(versioned_candidates) and not ignored
        if not ignored:
            findings.append(Finding("UI_VISUAL_SMOKE_SCREENSHOT_IGNORE_MISSING", "Screenshot/browser output paths are not fully ignored.", Severity.BLOCK))
        if screenshots_versioned:
            findings.append(Finding("UI_VISUAL_SMOKE_SCREENSHOTS_VERSIONED", "Screenshot/browser output directory appears versionable.", Severity.BLOCK))
        return {
            "ok": ignored and not screenshots_versioned,
            "screenshots_output_path": "outputs/ui-smoke/screenshots/",
            "browser_test_results_path": "ui/web/test-results/",
            "playwright_report_path": "ui/web/playwright-report/",
            "ignored": ignored,
            "screenshots_versioned": screenshots_versioned,
            "versioned_candidates": [self._relative(path) for path in versioned_candidates],
        }

    def _browser_tooling_check(self, package: dict[str, Any], findings: list[Finding]) -> dict[str, Any]:
        scripts = package.get("scripts") if isinstance(package, dict) else {}
        test_visual = scripts.get("test:visual")
        playwright_config_exists = (self.web_root / "playwright.config.ts").exists()
        playwright_spec_exists = (self.web_root / "tests" / "visual-smoke.spec.ts").exists()
        package_text = (self.web_root / "package.json").read_text(encoding="utf-8") if (self.web_root / "package.json").exists() else ""
        browser_available = "@playwright/test" in package_text
        if self.options.require_browser_tooling and not browser_available:
            findings.append(Finding("UI_VISUAL_SMOKE_BROWSER_TOOLING_REQUIRED_MISSING", "Browser tooling was required but @playwright/test is not installed.", Severity.BLOCK))
        if not test_visual:
            findings.append(Finding("UI_VISUAL_SMOKE_VISUAL_SCRIPT_MISSING", "ui/web package.json must expose a local test:visual command.", Severity.BLOCK))
        if not playwright_config_exists or not playwright_spec_exists:
            findings.append(Finding("UI_VISUAL_SMOKE_PLAYWRIGHT_SCAFFOLD_MISSING", "Optional Playwright visual smoke scaffold is missing.", Severity.BLOCK))
        return {
            "ok": bool(test_visual) and playwright_config_exists and playwright_spec_exists and (browser_available or not self.options.require_browser_tooling),
            "browser_tooling_available": browser_available,
            "browser_smoke_status": "available" if browser_available else "advisory-optional-not-installed",
            "browser_tooling_required_for_core": False,
            "package_test_visual": test_visual,
            "playwright_config_exists": playwright_config_exists,
            "playwright_spec_exists": playwright_spec_exists,
            "core_pytest_browser_dependency": False,
        }

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = _resolve_under_root(self.root, self.options.output_json)
        md_path = _resolve_under_root(self.root, self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(self._markdown(report), encoding="utf-8")
        return {"json": self._relative(json_path), "markdown": self._relative(md_path)}

    def _markdown(self, report: dict[str, Any]) -> str:
        summary = report.get("summary", {})
        lines = [
            "# POST-H-028-C - UI visual smoke report",
            "",
            f"- Decision: `{summary.get('decision')}`",
            f"- Critical views passed: `{summary.get('critical_views_passed')}/{summary.get('critical_views_total')}`",
            f"- States visible: `{summary.get('states_visible_total')}/{summary.get('states_checked_total')}`",
            f"- Browser smoke status: `{summary.get('browser_smoke_status')}`",
            f"- Screenshots versioned: `{summary.get('screenshots_versioned')}`",
            f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
            "",
            "## Scope",
            "",
            "Dependency-light static visual contract plus optional browser scaffold. No server start, sockets, network, external APIs, source mutations, remote execution, connector write or plugin execution.",
            "",
            "## Findings",
            "",
        ]
        findings = report.get("findings", [])
        if not findings:
            lines.append("- No blocking findings.")
        for finding in findings:
            lines.append(f"- `{finding.get('severity')}` `{finding.get('id')}` - {finding.get('message')}")
        return "\n".join(lines) + "\n"

    def _relative(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")


def _resolve_under_root(root: Path, path: str | Path) -> Path:
    raw = Path(path)
    return raw if raw.is_absolute() else root / raw


def _prefix_findings(findings: list[Finding], prefix: str) -> list[Finding]:
    return [
        Finding(
            id=f"{prefix}_{finding.id}",
            message=finding.message,
            severity=finding.severity,
            path=finding.path,
            metadata=finding.metadata,
        )
        for finding in findings
    ]


def run_ui_visual_smoke_report(root: Path, *, write_report: bool = False) -> CommandResult:
    return UiVisualSmokeReporter(root, UiVisualSmokeOptions(write_report=write_report)).run()


__all__ = [
    "DEFAULT_UI_VISUAL_SMOKE_REPORT_JSON",
    "DEFAULT_UI_VISUAL_SMOKE_REPORT_MARKDOWN",
    "POST_H_028_C_CREATED_BY",
    "UI_VISUAL_SMOKE_COMMAND",
    "UI_VISUAL_SMOKE_REPORT_CONTRACT",
    "UI_VISUAL_SMOKE_REPORT_SCHEMA_ID",
    "UiVisualSmokeOptions",
    "UiVisualSmokeReporter",
    "run_ui_visual_smoke_report",
]
