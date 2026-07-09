from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from shutil import copytree, ignore_patterns
from typing import Any

from fastapi.testclient import TestClient

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.schemas import SchemaValidator

from .app import create_app
from .security import API_TOKEN_HEADER, redact_token

POST_H_028_D_CREATED_BY = "POST-H-028-D"
OPERATOR_FLOW_SMOKE_COMMAND = "api operator-flow-smoke"
OPERATOR_FLOW_SMOKE_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-OPERATOR-FLOW-SMOKE-REPORT-V1"
OPERATOR_FLOW_SMOKE_REPORT_CONTRACT = "OperatorFlowSmokeReport"
DEFAULT_OPERATOR_FLOW_SMOKE_REPORT_JSON = Path("outputs/reports/operator_flow_smoke_report.json")
DEFAULT_OPERATOR_FLOW_SMOKE_REPORT_MARKDOWN = Path("outputs/reports/operator_flow_smoke_report.md")
LOCAL_ORIGIN = "http://127.0.0.1:5173"
WEB_ROOT = Path("ui/web")


@dataclass(frozen=True)
class OperatorFlowSmokeOptions:
    """Options for the POST-H-028-D local operator-flow smoke report."""

    token: str = "post-h-028-d-operator-flow-token"
    local_origin: str = LOCAL_ORIGIN
    output_json: str | Path = DEFAULT_OPERATOR_FLOW_SMOKE_REPORT_JSON
    output_markdown: str | Path = DEFAULT_OPERATOR_FLOW_SMOKE_REPORT_MARKDOWN
    write_report: bool = False


class OperatorFlowSmokeRunner:
    """POST-H-028-D operator flow and error-state smoke runner.

    The runner combines in-process FastAPI checks with static UI source checks.
    It never starts uvicorn, opens sockets, uses network/external APIs or writes
    source files. The approval lifecycle is exercised inside a temporary local
    runtime sandbox so the real repository's operational SQLite store is not
    mutated.
    """

    def __init__(self, root: Path, options: OperatorFlowSmokeOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or OperatorFlowSmokeOptions()
        self.web_root = self.root / WEB_ROOT

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        source_files = self._read_ui_source_files(findings)
        combined_source = "\n".join(source_files.values())
        client = TestClient(create_app(self.root, api_token=self.options.token, allowed_origins=[self.options.local_origin]))
        headers = {API_TOKEN_HEADER: self.options.token, "Origin": self.options.local_origin}

        auth = self._auth_error_flows(client, headers, combined_source, findings)
        reports_traces = self._reports_traces_flows(client, headers, combined_source, findings)
        settings_security = self._settings_security_flows(client, headers, combined_source, findings)
        actions = self._action_flows(client, headers, combined_source, findings)
        operator_dashboard = self._operator_dashboard_flow(client, headers, combined_source, findings)
        approvals = self._approval_flow(findings)
        ui_error_states = self._ui_error_state_contract(source_files, combined_source, findings)
        troubleshooting = self._troubleshooting_contract(combined_source, findings)

        checks = {
            "auth_error_flows": auth,
            "reports_traces_empty_states": reports_traces,
            "settings_security_redaction": settings_security,
            "action_launcher": actions,
            "operator_dashboard": operator_dashboard,
            "approval_center": approvals,
            "ui_error_states": ui_error_states,
            "troubleshooting": troubleshooting,
        }
        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
        ok = not blocking
        minimal_flow_names = [
            "api_down",
            "token_missing",
            "token_invalid",
            "dashboard_ready",
            "reports_empty",
            "traces_empty",
            "approval_create_list_decide",
            "dry_run_allowed_actions",
            "forbidden_action_block",
            "settings_redacted",
        ]
        minimal_passed = sum(
            1
            for name in minimal_flow_names
            if {
                "api_down": ui_error_states.get("api_down_visible"),
                "token_missing": auth.get("token_missing_visible"),
                "token_invalid": auth.get("token_invalid_visible"),
                "dashboard_ready": operator_dashboard.get("ready"),
                "reports_empty": reports_traces.get("reports_empty_visible"),
                "traces_empty": reports_traces.get("traces_empty_visible"),
                "approval_create_list_decide": approvals.get("approval_lifecycle_passed"),
                "dry_run_allowed_actions": actions.get("allowed_dry_run_actions_passed"),
                "forbidden_action_block": actions.get("forbidden_action_blocked"),
                "settings_redacted": settings_security.get("settings_redacted"),
            }.get(name)
        )
        summary = {
            "created_by": POST_H_028_D_CREATED_BY,
            "status": "implemented-initial",
            "decision": "PASS" if ok else "BLOCK",
            "operator_flow_smoke_passed": ok,
            "minimal_flows_total": len(minimal_flow_names),
            "minimal_flows_passed": minimal_passed,
            "api_down_visible": bool(ui_error_states.get("api_down_visible")),
            "token_missing_blocked": bool(auth.get("missing_token_blocked")),
            "token_invalid_blocked": bool(auth.get("invalid_token_blocked")),
            "token_missing_visible": bool(auth.get("token_missing_visible")),
            "token_invalid_visible": bool(auth.get("token_invalid_visible")),
            "raw_stack_traces_visible": bool(ui_error_states.get("raw_stack_traces_visible")),
            "reports_empty_state_visible": bool(reports_traces.get("reports_empty_visible")),
            "traces_empty_state_visible": bool(reports_traces.get("traces_empty_visible")),
            "approval_lifecycle_passed": bool(approvals.get("approval_lifecycle_passed")),
            "approval_runtime_sandbox_used": bool(approvals.get("runtime_sandbox_used")),
            "dry_run_actions_allowed_total": int(actions.get("allowed_actions_passed", 0)),
            "forbidden_action_blocked": bool(actions.get("forbidden_action_blocked")),
            "block_state_visible": bool(ui_error_states.get("block_state_visible")),
            "settings_redacted": bool(settings_security.get("settings_redacted")),
            "settings_plan_only": bool(settings_security.get("settings_plan_only")),
            "operator_dashboard_no_go_visible": bool(operator_dashboard.get("no_go_visible")),
            "operator_dashboard_next_actions_visible": bool(operator_dashboard.get("next_actions_visible")),
            "troubleshooting_messages_aligned": bool(troubleshooting.get("ok")),
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
            "schema_id": OPERATOR_FLOW_SMOKE_REPORT_SCHEMA_ID,
            "report_id": "devpilot-operator-flow-smoke-report",
            "created_by": POST_H_028_D_CREATED_BY,
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
                "approval_runtime_sandbox_used": bool(approvals.get("runtime_sandbox_used")),
                "raw_token_included": False,
                "raw_secret_values_included": False,
            },
            "findings": [finding.to_dict() for finding in findings],
            "notes": [
                "POST-H-028-D validates operator flows and user-facing error states for the local UI/API shell.",
                "The report checks API down, missing/invalid token, empty reports/traces, approvals, dry-run actions, forbidden action BLOCK, settings redaction and operator dashboard next actions.",
                "Approval create/list/decision is exercised in a temporary runtime sandbox so the source repository and real operational store are not mutated.",
                "This is an implemented-initial local operator flow smoke, not a full browser E2E suite or enterprise UI workflow.",
            ],
        }

        schema_result = SchemaValidator(self.root).validate_payload(
            schema=OPERATOR_FLOW_SMOKE_REPORT_CONTRACT,
            payload=report,
            instance_label="in-memory:operator_flow_smoke_report",
        )
        if not schema_result.ok:
            findings.extend(_prefix_findings(schema_result.findings, "OPERATOR_FLOW_SMOKE_REPORT_SCHEMA"))
            ok = False
            blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
            warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
            summary["decision"] = "BLOCK"
            summary["operator_flow_smoke_passed"] = False
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
            command=OPERATOR_FLOW_SMOKE_COMMAND,
            ok=ok,
            exit_code=exit_code,
            message="Operator flow smoke report passed." if ok else "Operator flow smoke report blocked.",
            data={"summary": summary, "report": report, "reports": reports, "notes": report["notes"]},
            findings=findings or [Finding("OPERATOR_FLOW_SMOKE_PASS", "Operator flow and error-state smoke passed for local UI/API.", Severity.INFO, metadata={"created_by": POST_H_028_D_CREATED_BY})],
        )

    def _auth_error_flows(self, client: TestClient, headers: dict[str, str], combined_source: str, findings: list[Finding]) -> dict[str, Any]:
        missing = client.get("/api/v1/operator/dashboard", headers={"Origin": self.options.local_origin})
        invalid = client.get("/api/v1/operator/dashboard", headers={API_TOKEN_HEADER: "invalid-token", "Origin": self.options.local_origin})
        valid = client.get("/api/v1/operator/dashboard", headers=headers)
        token_missing_visible = _contains_all(combined_source, ["token local faltante", "Unauthorized/Forbidden"])
        token_invalid_visible = "token local faltante o inválido" in combined_source and "401/403" in combined_source
        ok = missing.status_code in {401, 403} and invalid.status_code in {401, 403} and valid.status_code == 200 and token_missing_visible and token_invalid_visible
        _finding_if_false(findings, missing.status_code in {401, 403}, "OPERATOR_FLOW_TOKEN_MISSING_NOT_BLOCKED", "Missing local token was not blocked.")
        _finding_if_false(findings, invalid.status_code in {401, 403}, "OPERATOR_FLOW_INVALID_TOKEN_NOT_BLOCKED", "Invalid local token was not blocked.")
        _finding_if_false(findings, token_missing_visible, "OPERATOR_FLOW_TOKEN_MISSING_MESSAGE_NOT_VISIBLE", "UI source does not expose missing-token troubleshooting text.")
        _finding_if_false(findings, token_invalid_visible, "OPERATOR_FLOW_TOKEN_INVALID_MESSAGE_NOT_VISIBLE", "UI source does not expose invalid-token 401/403 text.")
        return {
            "ok": ok,
            "missing_token_status": missing.status_code,
            "invalid_token_status": invalid.status_code,
            "valid_token_status": valid.status_code,
            "missing_token_blocked": missing.status_code in {401, 403},
            "invalid_token_blocked": invalid.status_code in {401, 403},
            "token_missing_visible": token_missing_visible,
            "token_invalid_visible": token_invalid_visible,
            "raw_token_included": self.options.token in json.dumps([missing.text, invalid.text, combined_source]),
            "token_redacted": redact_token(self.options.token),
        }

    def _reports_traces_flows(self, client: TestClient, headers: dict[str, str], combined_source: str, findings: list[Finding]) -> dict[str, Any]:
        reports = client.get("/api/v1/reports?limit=50", headers=headers)
        traces = client.get("/api/v1/traces?limit=20", headers=headers)
        reports_empty_visible = "Sin reportes para mostrar" in combined_source and "ui.reports empty state" in combined_source
        traces_empty_visible = "Sin trazas para mostrar" in combined_source and "ui.traces empty state" in combined_source
        ok = reports.status_code == 200 and traces.status_code == 200 and reports_empty_visible and traces_empty_visible
        _finding_if_false(findings, reports.status_code == 200, "OPERATOR_FLOW_REPORTS_LIST_FAILED", "Reports list API did not respond with 200.")
        _finding_if_false(findings, traces.status_code == 200, "OPERATOR_FLOW_TRACES_LIST_FAILED", "Traces list API did not respond with 200.")
        _finding_if_false(findings, reports_empty_visible, "OPERATOR_FLOW_REPORTS_EMPTY_STATE_MISSING", "Reports empty state is not visible in UI source.")
        _finding_if_false(findings, traces_empty_visible, "OPERATOR_FLOW_TRACES_EMPTY_STATE_MISSING", "Traces empty state is not visible in UI source.")
        reports_summary = ((reports.json().get("data") or {}).get("summary") or {}) if reports.status_code == 200 else {}
        traces_summary = ((traces.json().get("data") or {}).get("summary") or {}) if traces.status_code == 200 else {}
        return {
            "ok": ok,
            "reports_status": reports.status_code,
            "traces_status": traces.status_code,
            "reports_empty_visible": reports_empty_visible,
            "traces_empty_visible": traces_empty_visible,
            "reports_returned_total": int(reports_summary.get("returned_total", 0) or 0),
            "traces_total": int(traces_summary.get("traces_total", 0) or 0),
        }

    def _settings_security_flows(self, client: TestClient, headers: dict[str, str], combined_source: str, findings: list[Finding]) -> dict[str, Any]:
        providers = client.get("/api/v1/settings/providers", headers=headers)
        posture = client.get("/api/v1/security/posture", headers=headers)
        plan = client.post(
            "/api/v1/settings/providers/plan",
            headers=headers,
            json={"provider_id": "ollama", "changes": {"enabled": True, "endpoint": "http://localhost:11434"}, "actor": "local-owner", "reason": "operator flow smoke plan-only"},
        )
        combined_payload = "\n".join([providers.text, posture.text, plan.text, combined_source])
        forbidden = [marker for marker in [self.options.token, "sk-proj-", "github_pat_", "Bearer "] if marker and marker in combined_payload]
        providers_summary = ((providers.json().get("data") or {}).get("summary") or {}) if providers.status_code == 200 else {}
        posture_summary = ((posture.json().get("data") or {}).get("summary") or {}) if posture.status_code == 200 else {}
        plan_summary = ((plan.json().get("data") or {}).get("summary") or {}) if plan.status_code == 200 else {}
        settings_redacted = providers.status_code == 200 and providers_summary.get("secrets_redacted") is True and posture_summary.get("settings_secrets_redacted") is True and not forbidden
        settings_plan_only = plan.status_code == 200 and plan_summary.get("plan_only") is True and plan_summary.get("write_performed") is False and "plan-only" in combined_source
        ok = settings_redacted and settings_plan_only
        _finding_if_false(findings, settings_redacted, "OPERATOR_FLOW_SETTINGS_REDACTION_BLOCK", "Settings/security posture exposed raw secret markers or lacked redaction evidence.")
        _finding_if_false(findings, settings_plan_only, "OPERATOR_FLOW_SETTINGS_PLAN_ONLY_MISSING", "Settings provider flow is not plan-only or is not visibly documented in UI source.")
        return {
            "ok": ok,
            "settings_status": providers.status_code,
            "security_posture_status": posture.status_code,
            "provider_plan_status": plan.status_code,
            "settings_redacted": settings_redacted,
            "settings_plan_only": settings_plan_only,
            "raw_secret_markers_found": forbidden,
            "external_api_enabled_total": int(providers_summary.get("external_api_enabled_total", 0) or 0),
        }

    def _action_flows(self, client: TestClient, headers: dict[str, str], combined_source: str, findings: list[Finding]) -> dict[str, Any]:
        allowed_payloads = [
            {"action_id": "readiness", "target": ".", "strict": True},
            {"action_id": "code-review", "target": "docs/01_requirements/use_cases.md"},
            {"action_id": "refactor-plan", "target": "docs/01_requirements/use_cases.md", "goal": "improve docs"},
        ]
        responses = [client.post("/api/v1/actions/dry-run", headers=headers, json=payload) for payload in allowed_payloads]
        blocked = client.post("/api/v1/actions/dry-run", headers=headers, json={"action_id": "patch-apply", "target": "."})
        allowed_passed = sum(1 for response in responses if response.status_code == 200 and response.json().get("ok") is True)
        forbidden_action_blocked = blocked.status_code in {403, 422} and blocked.json().get("ok") is False
        ui_allowlist_visible = all(marker in combined_source for marker in ["readiness", "code-review", "refactor-plan"])
        critical_hidden = all(marker not in combined_source for marker in ["patch-apply</option>", "rollback-execute</option>", "git-push</option>"])
        block_visible = "critical_actions_blocked" in combined_source and "patch apply" in combined_source.lower()
        ok = allowed_passed == len(allowed_payloads) and forbidden_action_blocked and ui_allowlist_visible and critical_hidden and block_visible
        _finding_if_false(findings, allowed_passed == len(allowed_payloads), "OPERATOR_FLOW_DRY_RUN_ACTIONS_FAILED", "One or more allowed dry-run actions failed.")
        _finding_if_false(findings, forbidden_action_blocked, "OPERATOR_FLOW_FORBIDDEN_ACTION_NOT_BLOCKED", "Forbidden UI action was not blocked.")
        _finding_if_false(findings, ui_allowlist_visible and critical_hidden, "OPERATOR_FLOW_ACTION_ALLOWLIST_DRIFT", "UI action launcher allowlist is missing safe actions or exposes critical actions.")
        _finding_if_false(findings, block_visible, "OPERATOR_FLOW_ACTION_BLOCK_NOT_VISIBLE", "UI does not visibly document critical action blocking.")
        return {
            "ok": ok,
            "allowed_actions_total": len(allowed_payloads),
            "allowed_actions_passed": allowed_passed,
            "allowed_dry_run_actions_passed": allowed_passed == len(allowed_payloads),
            "forbidden_action_status": blocked.status_code,
            "forbidden_action_blocked": forbidden_action_blocked,
            "ui_allowlist_visible": ui_allowlist_visible,
            "critical_actions_hidden": critical_hidden,
            "block_state_visible": block_visible,
        }

    def _operator_dashboard_flow(self, client: TestClient, headers: dict[str, str], combined_source: str, findings: list[Finding]) -> dict[str, Any]:
        response = client.get("/api/v1/operator/dashboard", headers=headers)
        data = response.json().get("data", {}) if response.status_code == 200 else {}
        snapshot = data.get("snapshot") or {}
        summary = data.get("summary") or {}
        no_go_visible = "no-go visible" in combined_source or "no-go gates" in combined_source.lower()
        next_actions_visible = "recommended_next_actions" in combined_source or "next actions" in combined_source.lower()
        ready = response.status_code == 200 and summary.get("read_only") is True and summary.get("dry_run") is True and int(summary.get("recommended_next_actions_total", 0) or 0) >= 0
        ok = ready and no_go_visible and next_actions_visible
        _finding_if_false(findings, ready, "OPERATOR_FLOW_DASHBOARD_NOT_READY", "Operator dashboard API did not return local read-only/dry-run evidence.")
        _finding_if_false(findings, no_go_visible, "OPERATOR_FLOW_DASHBOARD_NO_GO_NOT_VISIBLE", "Operator dashboard no-go gates are not visible in UI source.")
        _finding_if_false(findings, next_actions_visible, "OPERATOR_FLOW_DASHBOARD_NEXT_ACTIONS_NOT_VISIBLE", "Operator dashboard next actions are not visible in UI source.")
        return {
            "ok": ok,
            "status_code": response.status_code,
            "ready": ready,
            "snapshot_status": snapshot.get("status"),
            "sections_total": int(summary.get("sections_total", 0) or 0),
            "recommended_next_actions_total": int(summary.get("recommended_next_actions_total", 0) or 0),
            "no_go_visible": no_go_visible,
            "next_actions_visible": next_actions_visible,
            "remote_execution_enabled": bool(summary.get("remote_execution_enabled")),
            "connector_write_enabled": bool(summary.get("connector_write_enabled")),
            "plugin_execution_enabled": bool(summary.get("plugin_execution_enabled")),
        }

    def _approval_flow(self, findings: list[Finding]) -> dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix="devpilot-operator-flow-") as tmp:
            temp_root = Path(tmp) / "repo"
            copytree(
                self.root,
                temp_root,
                ignore=ignore_patterns(
                    ".git",
                    ".venv",
                    "outputs",
                    "dist",
                    "node_modules",
                    "__pycache__",
                    ".pytest_cache",
                    "devpilot.db",
                ),
            )
            client = TestClient(create_app(temp_root, api_token=self.options.token, allowed_origins=[self.options.local_origin]))
            headers = {API_TOKEN_HEADER: self.options.token, "Origin": self.options.local_origin}
            request = client.post(
                "/api/v1/approvals/request",
                headers=headers,
                json={
                    "tool_id": "tests.run",
                    "action": "execute",
                    "subject": "pytest-post-h-028-d",
                    "actor": "local-owner",
                    "reason": "operator flow smoke",
                    "ttl_minutes": 30,
                },
            )
            approval_id = None
            if request.status_code == 200:
                approval_id = ((request.json().get("data") or {}).get("approval") or {}).get("approval_id")
            listed = client.get("/api/v1/approvals?status=requested&limit=20", headers=headers)
            shown = client.get(f"/api/v1/approvals/{approval_id}", headers=headers) if approval_id else None
            decided = client.post(f"/api/v1/approvals/{approval_id}/deny", headers=headers, json={"actor": "local-owner", "reason": "operator flow denial"}) if approval_id else None
        lifecycle_passed = (
            request.status_code == 200
            and listed.status_code == 200
            and shown is not None
            and shown.status_code == 200
            and decided is not None
            and decided.status_code == 200
            and ((decided.json().get("data") or {}).get("approval") or {}).get("status") == "denied"
        )
        _finding_if_false(findings, lifecycle_passed, "OPERATOR_FLOW_APPROVAL_LIFECYCLE_FAILED", "Approval Center create/list/show/decision flow failed in the runtime sandbox.")
        return {
            "ok": lifecycle_passed,
            "approval_lifecycle_passed": lifecycle_passed,
            "runtime_sandbox_used": True,
            "request_status": request.status_code,
            "list_status": listed.status_code,
            "show_status": shown.status_code if shown is not None else None,
            "decision_status": decided.status_code if decided is not None else None,
            "final_status": ((decided.json().get("data") or {}).get("approval") or {}).get("status") if decided is not None and decided.status_code == 200 else None,
        }

    def _ui_error_state_contract(self, source_files: dict[str, str], combined_source: str, findings: list[Finding]) -> dict[str, Any]:
        raw_stack_markers = ["Traceback (most recent call last)", "stack:", "error.stack", "console.trace"]
        raw_stack_visible = any(marker in combined_source for marker in raw_stack_markers)
        api_down_visible = "API local down" in combined_source and "localhost" in combined_source
        unauthorized_visible = "Unauthorized/Forbidden" in combined_source and "401/403" in combined_source
        block_state_visible = "ui-state--block" in combined_source or "BLOCK" in combined_source
        empty_state_visible = "ui-state--empty" in combined_source
        error_state_visible = "ui-state--error" in combined_source
        loading_state_visible = "ui-state--loading" in combined_source
        ok = api_down_visible and unauthorized_visible and block_state_visible and empty_state_visible and error_state_visible and loading_state_visible and not raw_stack_visible
        _finding_if_false(findings, api_down_visible, "OPERATOR_FLOW_API_DOWN_MESSAGE_MISSING", "UI source does not expose API-down troubleshooting text.")
        _finding_if_false(findings, unauthorized_visible, "OPERATOR_FLOW_UNAUTHORIZED_MESSAGE_MISSING", "UI source does not expose Unauthorized/Forbidden 401/403 text.")
        _finding_if_false(findings, block_state_visible, "OPERATOR_FLOW_BLOCK_STATE_MISSING", "UI source does not expose BLOCK state.")
        _finding_if_false(findings, not raw_stack_visible, "OPERATOR_FLOW_RAW_STACK_TRACE_VISIBLE", "UI source contains raw stack trace markers.")
        return {
            "ok": ok,
            "api_down_visible": api_down_visible,
            "unauthorized_visible": unauthorized_visible,
            "block_state_visible": block_state_visible,
            "empty_state_visible": empty_state_visible,
            "error_state_visible": error_state_visible,
            "loading_state_visible": loading_state_visible,
            "raw_stack_traces_visible": raw_stack_visible,
            "source_files_checked_total": len(source_files),
        }

    def _troubleshooting_contract(self, combined_source: str, findings: list[Finding]) -> dict[str, Any]:
        expected = [
            "verifica que DevPilot API esté levantada en localhost",
            "token local faltante o inválido",
            "no habilita patch apply",
            "No remote",
        ]
        present = [item for item in expected if item in combined_source]
        forbidden = ["0.0.0.0 como solución", "exponer API", "desactivar CORS"]
        forbidden_found = [item for item in forbidden if item.lower() in combined_source.lower()]
        ok = len(present) == len(expected) and not forbidden_found
        _finding_if_false(findings, ok, "OPERATOR_FLOW_TROUBLESHOOTING_DRIFT", "Troubleshooting messages are missing or suggest unsafe remediation.")
        return {"ok": ok, "expected_messages_total": len(expected), "messages_present_total": len(present), "missing_messages": sorted(set(expected) - set(present)), "forbidden_messages_found": forbidden_found}

    def _read_ui_source_files(self, findings: list[Finding]) -> dict[str, str]:
        paths = [
            "src/api/client.ts",
            "src/pages/Dashboard.ts",
            "src/pages/ReportTraceView.ts",
            "src/pages/ApprovalCenterView.ts",
            "src/pages/SettingsView.ts",
            "src/pages/OperatorDashboard.ts",
            "src/components/DryRunActionForm.ts",
            "src/components/ContractBadges.ts",
            "src/components/OperatorGatePanel.ts",
            "src/components/OperatorNextActions.ts",
        ]
        out: dict[str, str] = {}
        for rel in paths:
            path = self.web_root / rel
            if not path.exists():
                findings.append(Finding("OPERATOR_FLOW_UI_SOURCE_MISSING", f"UI source file missing: {path}", Severity.BLOCK, path=str(path)))
                continue
            out[rel] = path.read_text(encoding="utf-8")
        return out

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / Path(self.options.output_json)
        md_path = self.root / Path(self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        summary = report["summary"]
        md = [
            "# POST-H-028-D — Operator flows and error states",
            "",
            f"- Decision: `{summary['decision']}`",
            f"- Minimal flows: `{summary['minimal_flows_passed']}/{summary['minimal_flows_total']}`",
            f"- Blocking findings: `{summary['blocking_findings_total']}`",
            f"- Approval runtime sandbox used: `{summary['approval_runtime_sandbox_used']}`",
            f"- Network used: `{summary['network_used']}`",
            f"- Source mutations: `{summary['source_mutations_performed']}`",
            "",
            "Este reporte es evidence local implemented-initial. No equivale a una suite E2E browser industrial completa.",
        ]
        md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
        return {"json": _rel(json_path, self.root), "markdown": _rel(md_path, self.root)}


def _contains_all(text: str, markers: list[str]) -> bool:
    return all(marker in text for marker in markers)


def _finding_if_false(findings: list[Finding], condition: bool, finding_id: str, message: str) -> None:
    if not condition:
        findings.append(Finding(finding_id, message, Severity.BLOCK))


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


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def run_operator_flow_smoke(root: Path, *, write_report: bool = False) -> CommandResult:
    return OperatorFlowSmokeRunner(root, OperatorFlowSmokeOptions(write_report=write_report)).run()
