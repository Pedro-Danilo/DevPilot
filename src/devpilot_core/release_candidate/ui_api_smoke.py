from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import urlparse

from fastapi.testclient import TestClient

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.interfaces.api import API_TOKEN_HEADER, create_app, validate_api_bind_host
from devpilot_core.interfaces.api.security import is_local_api_host
from devpilot_core.policy import PolicyEngine, PolicyRequest

DEFAULT_UI_API_RC_SMOKE_REPORT_JSON = Path("outputs/reports/ui_api_rc_smoke_report.json")
DEFAULT_UI_API_RC_SMOKE_REPORT_MARKDOWN = Path("outputs/reports/ui_api_rc_smoke_report.md")
DEFAULT_BASE_URL = "http://127.0.0.1:8787"
DEFAULT_UI_ORIGIN = "http://127.0.0.1:5173"
_TEST_TOKEN = "post-h-026-c-local-rc-smoke-token-000000"
_REQUIRED_API_ROUTE_IDS = {
    "api.health",
    "api.security.posture",
    "api.operator.dashboard",
    "api.reports.list",
    "api.traces.list",
    "api.approvals.list",
    "api.settings.providers",
    "api.actions.dry_run",
}
_REQUIRED_UI_ROUTE_IDS = {"ui.dashboard", "ui.reports", "ui.traces", "ui.approvals", "ui.settings"}
_REQUIRED_UI_ENDPOINTS = (
    "/operator/dashboard",
    "/workspace/status",
    "/validation/readiness",
    "/standards/status",
    "/miasi/status",
    "/reports",
    "/traces",
    "/metrics/summary",
    "/approvals",
    "/actions/dry-run",
    "/settings/workspace",
    "/settings/providers",
    "/settings/policy",
    "/security/posture",
    "/settings/providers/plan",
)
_REQUIRED_UI_STATE_MARKERS = (
    'data-ui-state="loading"',
    'data-ui-state="empty"',
    'data-ui-state="error"',
    "BLOCK",
    "Security posture",
    "Action Launcher",
    "Provider editor plan-only",
)
_FORBIDDEN_UI_MARKERS = (
    "devpilot_core",
    "child_process",
    "fs.readFile",
    "writeFile",
    "/patch/apply",
    "/rollback/execute",
    "/git/push",
)


@dataclass(frozen=True)
class UiApiRcSmokeOptions:
    base_url: str = DEFAULT_BASE_URL
    ui_origin: str = DEFAULT_UI_ORIGIN
    output_json: str = str(DEFAULT_UI_API_RC_SMOKE_REPORT_JSON)
    output_markdown: str = str(DEFAULT_UI_API_RC_SMOKE_REPORT_MARKDOWN)
    write_report: bool = False


class UiApiRcSmokeRunner:
    """POST-H-026-C local UI/API RC smoke verifier.

    The runner is deterministic and local-first. It uses FastAPI TestClient for
    in-process API checks instead of opening sockets, and it performs static UI
    contract checks over the Web UI source tree. This intentionally avoids new
    browser/test dependencies while still validating localhost, token, CORS,
    route contracts, visible UI states and no-go invariants for the RC flow.
    """

    def __init__(self, root: Path, options: UiApiRcSmokeOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or UiApiRcSmokeOptions()

    def run(self) -> CommandResult:
        started = perf_counter()
        findings: list[Finding] = []
        checks: list[dict[str, Any]] = []

        parsed_url = urlparse(self.options.base_url)
        host = (parsed_url.hostname or "").strip()
        port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
        base_url_local = self._record(
            checks,
            "base-url-localhost",
            bool(host and is_local_api_host(host) and parsed_url.scheme in {"http", "https"}),
            f"base_url={self.options.base_url}",
            critical=True,
            metadata={"scheme": parsed_url.scheme, "host": host, "port": port},
        )
        if not base_url_local:
            findings.append(Finding("UI_API_RC_BASE_URL_NOT_LOCALHOST_BLOCK", "UI/API RC smoke only accepts localhost/loopback base URLs.", Severity.BLOCK, metadata={"base_url": self.options.base_url}))

        bind_result = validate_api_bind_host(host=host or "", port=port)
        self._record(
            checks,
            "api-bind-host-localhost",
            bind_result.ok,
            bind_result.message,
            critical=True,
            metadata={"host": host, "port": port},
        )
        if not bind_result.ok:
            findings.extend(bind_result.findings)

        non_local_result = validate_api_bind_host(host="0.0.0.0", port=port)
        self._record(
            checks,
            "api-non-local-bind-blocked",
            not non_local_result.ok and int(non_local_result.exit_code) == int(ExitCode.BLOCK),
            "0.0.0.0 remains blocked for RC smoke.",
            critical=True,
        )
        if non_local_result.ok:
            findings.append(Finding("UI_API_RC_NON_LOCAL_BIND_ALLOWED_BLOCK", "API accepted 0.0.0.0 during RC smoke.", Severity.BLOCK))

        client = TestClient(
            create_app(self.root, api_token=_TEST_TOKEN, allowed_origins=["*", "http://evil.example", self.options.ui_origin]),
            base_url=self.options.base_url if base_url_local else DEFAULT_BASE_URL,
        )
        security_summary = client.app.state.api_security.to_safe_summary()
        cors_ok = security_summary.get("cors_wildcard_enabled") is False and "*" not in security_summary.get("allowed_origins", []) and "http://evil.example" not in security_summary.get("allowed_origins", [])
        self._record(checks, "cors-wildcard-blocked", cors_ok, "Wildcard/non-local origins are sanitized from API CORS config.", critical=True, metadata={"allowed_origins": security_summary.get("allowed_origins")})
        if not cors_ok:
            findings.append(Finding("UI_API_RC_CORS_WILDCARD_BLOCK", "CORS wildcard or non-local origin was accepted during RC smoke.", Severity.BLOCK, metadata={"allowed_origins": security_summary.get("allowed_origins")}))

        self._api_checks(client, checks, findings)
        self._registry_checks(checks, findings)
        self._ui_static_checks(checks, findings)
        self._policy_no_go_check(checks, findings)

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        decision = "PASS" if not blocking else "BLOCK"
        duration_ms = round((perf_counter() - started) * 1000, 3)
        checks_passed = sum(1 for check in checks if check["status"] == "pass")
        report = {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-UI-API-RC-SMOKE-REPORT-V1",
            "report_id": "ui-api-rc-smoke-post_h_026_c",
            "created_by": "POST-H-026-C",
            "created_at": self._now(),
            "scope": "local-release-candidate",
            "decision": decision,
            "implemented_status": "implemented-initial",
            "base_url": self.options.base_url,
            "ui_origin": self.options.ui_origin,
            "execution_mode": "in-process-api-and-static-ui-contract-smoke",
            "checks_total": len(checks),
            "checks_passed_total": checks_passed,
            "checks_failed_total": len(checks) - checks_passed,
            "critical_checks_total": sum(1 for check in checks if check.get("critical") is True),
            "critical_checks_failed_total": sum(1 for check in checks if check.get("critical") is True and check["status"] != "pass"),
            "api_checks_total": sum(1 for check in checks if check.get("category") == "api"),
            "ui_checks_total": sum(1 for check in checks if check.get("category") == "ui"),
            "security_checks_total": sum(1 for check in checks if check.get("category") == "security"),
            "route_contract_checks_total": sum(1 for check in checks if check.get("category") == "route-contract"),
            "checks": checks,
            "duration_ms": duration_ms,
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "in_process_api_client": True,
                "socket_opened": False,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "mutations_performed": False,
                "source_mutations": False,
                "reports_written": self.options.write_report,
                "raw_token_persisted": False,
            },
            "summary": {
                "decision": decision,
                "created_by": "POST-H-026-C",
                "preliminary": True,
                "api_localhost_only": True,
                "api_token_required": True,
                "cors_wildcard_enabled": False,
                "ui_api_shell_static_smoke": True,
                "browser_automation_used": False,
                "playwright_required": False,
                "ui_reads_filesystem_directly": False,
                "no_go_action_blocked": True,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "external_apis_required": False,
                "reports_written": self.options.write_report,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations": False,
            },
            "limitations": [
                "POST-H-026-C uses FastAPI TestClient and static Web UI contract checks; it does not open sockets or run a real browser by default.",
                "npm/Playwright visual browser execution remains optional/future hardening; npm --prefix ui/web test can be run manually as the existing local smoke.",
                "Install smoke and final RC PASS/BLOCK remain planned for POST-H-026-D/E.",
            ],
        }
        if self.options.write_report:
            self._write_report(report)
        if decision == "PASS":
            findings.append(Finding("UI_API_RC_SMOKE_PASS", "UI/API local RC smoke passed without network, external APIs or source mutations.", Severity.INFO, metadata={"checks_total": len(checks), "checks_passed_total": checks_passed}))
        return CommandResult(
            command="release-candidate ui-api-smoke",
            ok=decision == "PASS",
            exit_code=ExitCode.PASS if decision == "PASS" else ExitCode.BLOCK,
            message="UI/API RC smoke passed." if decision == "PASS" else "UI/API RC smoke blocked.",
            data={
                "summary": report["summary"] | {"checks_total": len(checks), "checks_passed_total": checks_passed, "checks_failed_total": len(checks) - checks_passed},
                "report": report,
                "reports": self._report_paths() if self.options.write_report else {},
            },
            findings=findings,
        )

    def _api_checks(self, client: TestClient, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        origin_headers = {"Origin": self.options.ui_origin}
        token_headers = {**origin_headers, API_TOKEN_HEADER: _TEST_TOKEN}

        health = client.get("/api/v1/health", headers=origin_headers)
        self._record(checks, "api-health-public", health.status_code == 200 and health.json().get("ok") is True, "Health route is public and local.", category="api", critical=True, metadata={"status_code": health.status_code})

        missing_token = client.get("/api/v1/security/posture", headers=origin_headers)
        missing_payload = self._json_payload(missing_token)
        missing_token_ok = missing_token.status_code == 401 and self._has_finding(missing_payload, "API_TOKEN_MISSING_BLOCK")
        self._record(checks, "api-protected-route-requires-token", missing_token_ok, "Security posture route blocks missing token.", category="security", critical=True, metadata={"status_code": missing_token.status_code})
        if not missing_token_ok:
            findings.append(Finding("UI_API_RC_PROTECTED_ROUTE_WITHOUT_TOKEN_BLOCK", "A protected API route did not block missing token.", Severity.BLOCK, metadata={"status_code": missing_token.status_code}))

        posture = client.get("/api/v1/security/posture", headers=token_headers)
        posture_payload = self._json_payload(posture)
        rendered_posture = json.dumps(posture_payload, ensure_ascii=False)
        posture_summary = (posture_payload.get("data") or {}).get("summary") if isinstance(posture_payload, dict) else {}
        posture_ok = (
            posture.status_code == 200
            and posture_payload.get("ok") is True
            and _TEST_TOKEN not in rendered_posture
            and posture_summary.get("token_required") is True
            and posture_summary.get("cors_wildcard_enabled") is False
            and posture_summary.get("remote_execution_enabled") is False
            and posture_summary.get("connector_write_enabled") is False
            and posture_summary.get("plugin_execution_enabled") is False
        )
        self._record(checks, "api-security-posture-redacted-local-only", posture_ok, "Security posture is token-protected, redacted and local-only.", category="security", critical=True, metadata={"status_code": posture.status_code})
        if not posture_ok:
            findings.append(Finding("UI_API_RC_SECURITY_POSTURE_BLOCK", "Security posture did not satisfy RC local-only/redaction invariants.", Severity.BLOCK, metadata={"status_code": posture.status_code}))

        operator = client.get("/api/v1/operator/dashboard", headers=token_headers)
        operator_payload = self._json_payload(operator)
        operator_ok = operator.status_code == 200 and operator_payload.get("ok") is True and "operator.dashboard" in json.dumps(operator_payload, ensure_ascii=False)
        self._record(checks, "api-operator-dashboard-protected", operator_ok, "Operator dashboard is protected and returns ApplicationResponse.", category="api", critical=True, metadata={"status_code": operator.status_code})
        if not operator_ok:
            findings.append(Finding("UI_API_RC_OPERATOR_DASHBOARD_BLOCK", "Operator dashboard route failed RC protected smoke.", Severity.BLOCK, metadata={"status_code": operator.status_code}))

        evil_options = client.options(
            "/api/v1/security/posture",
            headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"},
        )
        evil_cors_ok = "access-control-allow-origin" not in {key.lower(): value for key, value in evil_options.headers.items()}
        self._record(checks, "api-cors-non-local-origin-denied", evil_cors_ok, "Non-local browser origin does not receive CORS allow header.", category="security", critical=True, metadata={"status_code": evil_options.status_code})
        if not evil_cors_ok:
            findings.append(Finding("UI_API_RC_CORS_NON_LOCAL_ORIGIN_BLOCK", "Non-local UI origin received CORS allow headers.", Severity.BLOCK))

    def _registry_checks(self, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        api_registry = self._load_json(".devpilot/interfaces/api_route_contract_registry.json")
        ui_registry = self._load_json(".devpilot/interfaces/ui_route_contract_registry.json")
        api_routes = api_registry.get("routes", []) if isinstance(api_registry, dict) else []
        ui_routes = ui_registry.get("routes", []) if isinstance(ui_registry, dict) else []
        api_by_id = {str(route.get("route_id")): route for route in api_routes if isinstance(route, dict)}
        ui_by_id = {str(route.get("route_id")): route for route in ui_routes if isinstance(route, dict)}
        missing_api = sorted(_REQUIRED_API_ROUTE_IDS - set(api_by_id))
        missing_ui = sorted(_REQUIRED_UI_ROUTE_IDS - set(ui_by_id))
        self._record(checks, "api-route-contracts-required-routes", not missing_api, "Required API route contracts are present.", category="route-contract", critical=True, metadata={"missing": missing_api})
        self._record(checks, "ui-route-contracts-required-routes", not missing_ui, "Required UI route contracts are present.", category="route-contract", critical=True, metadata={"missing": missing_ui})
        if missing_api:
            findings.append(Finding("UI_API_RC_API_ROUTE_CONTRACT_MISSING_BLOCK", "Required API route contract IDs are missing.", Severity.BLOCK, path=".devpilot/interfaces/api_route_contract_registry.json", metadata={"missing": missing_api}))
        if missing_ui:
            findings.append(Finding("UI_API_RC_UI_ROUTE_CONTRACT_MISSING_BLOCK", "Required UI route contract IDs are missing.", Severity.BLOCK, path=".devpilot/interfaces/ui_route_contract_registry.json", metadata={"missing": missing_ui}))

        unsafe_api = [route.get("route_id") for route in api_routes if isinstance(route, dict) and (route.get("remote_execution_allowed") is not False or route.get("connector_write_allowed") is not False or route.get("plugin_execution_allowed") is not False or route.get("external_api_allowed") is not False)]
        unsafe_ui = [route.get("route_id") for route in ui_routes if isinstance(route, dict) and (route.get("local_only") is not True or route.get("remote_execution_allowed") is not False or route.get("connector_write_allowed") is not False or route.get("plugin_execution_allowed") is not False or route.get("external_api_allowed") is not False)]
        self._record(checks, "api-route-contract-no-go-flags", not unsafe_api, "API route contracts keep no-go flags disabled.", category="route-contract", critical=True, metadata={"unsafe_route_ids": unsafe_api})
        self._record(checks, "ui-route-contract-no-go-flags", not unsafe_ui, "UI route contracts keep local-only/no-go flags enforced.", category="route-contract", critical=True, metadata={"unsafe_route_ids": unsafe_ui})
        if unsafe_api or unsafe_ui:
            findings.append(Finding("UI_API_RC_ROUTE_NO_GO_FLAGS_BLOCK", "API/UI route contracts contain unsafe no-go flag values.", Severity.BLOCK, metadata={"unsafe_api": unsafe_api, "unsafe_ui": unsafe_ui}))

        incomplete_state = []
        known_api_ids = set(api_by_id)
        unknown_refs: list[str] = []
        for route in ui_routes:
            if not isinstance(route, dict):
                continue
            state = route.get("state_contract") if isinstance(route.get("state_contract"), dict) else {}
            if not all(state.get(key) is True for key in ("loading", "empty", "error", "block_visible")):
                incomplete_state.append(route.get("route_id"))
            for api_id in route.get("allowed_api_routes", []) if isinstance(route.get("allowed_api_routes"), list) else []:
                if str(api_id) not in known_api_ids:
                    unknown_refs.append(f"{route.get('route_id')}->{api_id}")
        self._record(checks, "ui-route-state-contracts", not incomplete_state, "UI routes declare loading/empty/error/BLOCK states.", category="ui", critical=True, metadata={"incomplete": incomplete_state})
        self._record(checks, "ui-api-route-references-valid", not unknown_refs, "UI route allowed API references point to registered API routes.", category="route-contract", critical=True, metadata={"unknown_refs": unknown_refs})
        if incomplete_state or unknown_refs:
            findings.append(Finding("UI_API_RC_UI_ROUTE_STATE_OR_REF_BLOCK", "UI route contracts are missing state coverage or reference unknown API routes.", Severity.BLOCK, metadata={"incomplete_state": incomplete_state, "unknown_refs": unknown_refs}))

    def _ui_static_checks(self, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        web_root = self.root / "ui" / "web"
        source_files = sorted((web_root / "src").rglob("*.ts"))
        smoke_script = web_root / "scripts" / "smoke-test.mjs"
        package_path = web_root / "package.json"
        combined = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in source_files)
        smoke = smoke_script.read_text(encoding="utf-8") if smoke_script.exists() else ""
        package = json.loads(package_path.read_text(encoding="utf-8")) if package_path.exists() else {}
        source_bundle = combined + "\n" + smoke

        package_ok = package.get("scripts", {}).get("test") == "node scripts/smoke-test.mjs" and package.get("devpilot", {}).get("apiOnly") is True and package.get("devpilot", {}).get("dryRunOnly") is True
        self._record(checks, "ui-package-local-smoke-script", package_ok, "Web UI exposes deterministic local npm smoke script.", category="ui", critical=True)
        if not package_ok:
            findings.append(Finding("UI_API_RC_UI_PACKAGE_SMOKE_BLOCK", "Web UI package metadata does not expose the local smoke script/API-only flags.", Severity.BLOCK, path="ui/web/package.json"))

        missing_endpoints = [endpoint for endpoint in _REQUIRED_UI_ENDPOINTS if endpoint not in combined]
        missing_state_markers = [marker for marker in _REQUIRED_UI_STATE_MARKERS if marker not in source_bundle]
        forbidden = [marker for marker in _FORBIDDEN_UI_MARKERS if marker in combined]
        direct_runtime_reads = [marker for marker in ("outputs/", ".devpilot/") if marker in combined]
        self._record(checks, "ui-client-required-local-api-endpoints", not missing_endpoints, "Web UI client covers required local API endpoints.", category="ui", critical=True, metadata={"missing": missing_endpoints})
        self._record(checks, "ui-visible-states-and-block-markers", not missing_state_markers, "Web UI source exposes loading/empty/error/BLOCK/security/dry-run states.", category="ui", critical=True, metadata={"missing": missing_state_markers})
        self._record(checks, "ui-no-forbidden-runtime-or-destructive-calls", not forbidden and not direct_runtime_reads, "Web UI does not import core, execute processes, read outputs directly or call destructive endpoints.", category="ui", critical=True, metadata={"forbidden": forbidden, "direct_runtime_reads": direct_runtime_reads})
        if missing_endpoints or missing_state_markers or forbidden or direct_runtime_reads:
            findings.append(Finding("UI_API_RC_STATIC_UI_CONTRACT_BLOCK", "Static Web UI RC contract checks failed.", Severity.BLOCK, metadata={"missing_endpoints": missing_endpoints, "missing_state_markers": missing_state_markers, "forbidden": forbidden, "direct_runtime_reads": direct_runtime_reads}))

    def _policy_no_go_check(self, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
        result = PolicyEngine(self.root, observability_enabled=False).evaluate(
            PolicyRequest(
                action="execute",
                tool_id="tests.run",
                subject="pytest",
                dry_run=True,
                metadata={"component": "UiApiRcSmokeRunner", "interface": "api", "api_operation": "ui.actions.dry_run"},
            )
        )
        ok = not result.ok and int(result.exit_code) == int(ExitCode.BLOCK) and any(finding.severity == Severity.BLOCK for finding in result.findings)
        self._record(checks, "ui-api-no-go-action-blocked", ok, "PolicyEngine blocks no-go execute action attempted from UI/API dry-run context.", category="security", critical=True, metadata={"policy_exit_code": int(result.exit_code), "finding_ids": [finding.id for finding in result.findings[:8]]})
        if not ok:
            findings.append(Finding("UI_API_RC_NO_GO_ACTION_NOT_BLOCKED", "No-go action simulation was not blocked during UI/API RC smoke.", Severity.BLOCK))

    def _record(self, checks: list[dict[str, Any]], check_id: str, passed: bool, reason: str, *, category: str = "security", critical: bool = False, metadata: dict[str, Any] | None = None) -> bool:
        checks.append(
            {
                "check_id": check_id,
                "category": category,
                "status": "pass" if passed else "block",
                "critical": critical,
                "reason": reason,
                "metadata": metadata or {},
            }
        )
        return passed

    def _load_json(self, relative_path: str) -> dict[str, Any]:
        path = self.root / relative_path
        return json.loads(path.read_text(encoding="utf-8"))

    def _json_payload(self, response: Any) -> dict[str, Any]:
        try:
            payload = response.json()
            return payload if isinstance(payload, dict) else {"raw": payload}
        except Exception:
            return {"raw_text": getattr(response, "text", "")}

    def _has_finding(self, payload: dict[str, Any], finding_id: str) -> bool:
        findings = payload.get("findings") if isinstance(payload, dict) else []
        return any(isinstance(finding, dict) and finding.get("id") == finding_id for finding in findings)

    def _write_report(self, report: dict[str, Any]) -> None:
        json_path = self._resolve(self.options.output_json)
        markdown_path = self._resolve(self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(self._markdown(report), encoding="utf-8")

    def _markdown(self, report: dict[str, Any]) -> str:
        lines = [
            "# UI/API RC smoke report",
            "",
            f"- Decision: `{report['decision']}`",
            f"- Scope: `{report['scope']}`",
            f"- Base URL: `{report['base_url']}`",
            f"- UI origin: `{report['ui_origin']}`",
            f"- Execution mode: `{report['execution_mode']}`",
            f"- Checks: `{report['checks_passed_total']}/{report['checks_total']}`",
            f"- Network used: `{report['safety']['network_used']}`",
            f"- Browser automation used: `{report['summary']['browser_automation_used']}`",
            "",
            "## Checks",
        ]
        lines.extend(f"- `{check['status']}` · `{check['check_id']}` · {check['reason']}" for check in report["checks"])
        lines.extend(["", "## Limitations"])
        lines.extend(f"- {item}" for item in report["limitations"])
        return "\n".join(lines) + "\n"

    def _report_paths(self) -> dict[str, str]:
        return {"json": self._relative(self._resolve(self.options.output_json)), "markdown": self._relative(self._resolve(self.options.output_markdown))}

    def _resolve(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Path escapes project root: {path}") from exc
        return resolved

    def _relative(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    def _now(self) -> str:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
