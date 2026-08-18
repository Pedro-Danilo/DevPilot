from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.schemas import SchemaValidator

from .app import create_app
from .security import (
    API_REMOTE_BIND_OVERRIDE_ENV_VAR,
    API_TOKEN_HEADER,
    API_SECURITY_HEADER_VALUE,
    DEFAULT_ALLOWED_ORIGINS,
    SECURITY_HEADERS,
    is_allowed_local_origin,
    redact_token,
    sanitize_allowed_origins,
    validate_api_bind_host,
)

POST_H_028_B_CREATED_BY = "POST-H-028-B"
LOCAL_API_SECURITY_HARDENING_COMMAND = "api security-hardening"
LOCAL_API_SECURITY_HARDENING_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-LOCAL-API-SECURITY-HARDENING-REPORT-V1"
LOCAL_API_SECURITY_HARDENING_REPORT_CONTRACT = "LocalApiSecurityHardeningReport"
DEFAULT_LOCAL_API_SECURITY_HARDENING_REPORT_JSON = Path("outputs/reports/local_api_security_hardening_report.json")
DEFAULT_LOCAL_API_SECURITY_HARDENING_REPORT_MARKDOWN = Path("outputs/reports/local_api_security_hardening_report.md")
LOCAL_ALLOWED_ORIGIN = "http://127.0.0.1:5173"
NON_LOCAL_ORIGIN = "http://evil.example"
PROTECTED_SAMPLE_PATH = "/api/v1/security/posture"
SETTINGS_PROVIDERS_PATH = "/api/v1/settings/providers"


@dataclass(frozen=True)
class LocalApiSecurityHardeningOptions:
    """Options for POST-H-028-B local auth/CORS/security hardening.

    The runner uses FastAPI TestClient in-process only. It does not start a
    server, bind a socket, call the network, use external APIs or mutate source
    files. Report writing is explicit and limited to outputs/reports.
    """

    token: str = "post-h-028-b-local-hardening-token"
    local_origin: str = LOCAL_ALLOWED_ORIGIN
    non_local_origin: str = NON_LOCAL_ORIGIN
    protected_sample_path: str = PROTECTED_SAMPLE_PATH
    settings_providers_path: str = SETTINGS_PROVIDERS_PATH
    output_json: str | Path = DEFAULT_LOCAL_API_SECURITY_HARDENING_REPORT_JSON
    output_markdown: str | Path = DEFAULT_LOCAL_API_SECURITY_HARDENING_REPORT_MARKDOWN
    write_report: bool = False


class LocalApiSecurityHardeningRunner:
    """POST-H-028-B security hardening gate for the local API/UI shell.

    The gate verifies representative runtime auth behavior plus static local-only
    invariants: protected endpoints reject missing/invalid token, valid token
    works through PolicyEngine, CORS keeps wildcard and non-local origins out,
    non-local bind remains blocked even when the future override env var is set,
    security headers are applied to success/error responses, settings providers
    are redacted, and reports never contain the raw token.
    """

    def __init__(self, root: Path, options: LocalApiSecurityHardeningOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or LocalApiSecurityHardeningOptions()

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        options = self.options
        allowed_origins = sanitize_allowed_origins(["*", options.non_local_origin, options.local_origin, "http://localhost:5173"])
        app = create_app(self.root, api_token=options.token, allowed_origins=list(allowed_origins))
        client = TestClient(app)

        missing = client.get(options.protected_sample_path, headers={"Origin": options.local_origin})
        invalid = client.get(options.protected_sample_path, headers={API_TOKEN_HEADER: "invalid-token", "Origin": options.local_origin})
        valid = client.get(options.protected_sample_path, headers={API_TOKEN_HEADER: options.token, "Origin": options.local_origin})
        non_local_origin_response = client.get(options.protected_sample_path, headers={API_TOKEN_HEADER: "invalid-token", "Origin": options.non_local_origin})
        settings = client.get(options.settings_providers_path, headers={API_TOKEN_HEADER: options.token, "Origin": options.local_origin})
        bind = validate_api_bind_host(host="0.0.0.0", port=8787, env={API_REMOTE_BIND_OVERRIDE_ENV_VAR: "1"})

        auth_check = {
            "ok": missing.status_code in {401, 403} and invalid.status_code in {401, 403} and valid.status_code == 200,
            "protected_sample_path": options.protected_sample_path,
            "missing_token_status": missing.status_code,
            "invalid_token_status": invalid.status_code,
            "valid_token_status": valid.status_code,
            "missing_token_blocked": missing.status_code in {401, 403},
            "invalid_token_blocked": invalid.status_code in {401, 403},
            "valid_token_passed": valid.status_code == 200,
        }
        self._finding_if_false(findings, auth_check["missing_token_blocked"], "LOCAL_API_AUTH_MISSING_TOKEN_NOT_BLOCKED", "Protected local API route responded without a token.")
        self._finding_if_false(findings, auth_check["invalid_token_blocked"], "LOCAL_API_AUTH_INVALID_TOKEN_NOT_BLOCKED", "Protected local API route accepted an invalid token.")
        self._finding_if_false(findings, auth_check["valid_token_passed"], "LOCAL_API_AUTH_VALID_TOKEN_FAILED", "Protected local API route did not pass with a valid token.")

        local_origin_allowed = missing.headers.get("access-control-allow-origin") == options.local_origin
        non_local_origin_rejected = "access-control-allow-origin" not in {key.lower(): value for key, value in non_local_origin_response.headers.items()}
        cors_check = {
            "ok": "*" not in allowed_origins and options.non_local_origin not in allowed_origins and local_origin_allowed and non_local_origin_rejected,
            "requested_origins": ["*", options.non_local_origin, options.local_origin, "http://localhost:5173"],
            "effective_allowed_origins": list(allowed_origins),
            "wildcard_cors_enabled": "*" in allowed_origins,
            "local_origin_allowed": local_origin_allowed,
            "non_local_origin_rejected": non_local_origin_rejected,
            "origin_helper_accepts_local": is_allowed_local_origin(options.local_origin),
            "origin_helper_rejects_non_local": not is_allowed_local_origin(options.non_local_origin),
        }
        self._finding_if_false(findings, not cors_check["wildcard_cors_enabled"], "LOCAL_API_CORS_WILDCARD_ENABLED", "Wildcard CORS origin is enabled.")
        self._finding_if_false(findings, local_origin_allowed, "LOCAL_API_CORS_LOCAL_ORIGIN_NOT_ALLOWED", "Allowed localhost origin was not exposed on an early auth response.")
        self._finding_if_false(findings, non_local_origin_rejected, "LOCAL_API_CORS_NON_LOCAL_ORIGIN_ALLOWED", "Non-local origin received Access-Control-Allow-Origin.")

        bind_summary = dict((bind.data or {}).get("summary") or {})
        bind_check = {
            "ok": not bind.ok and int(bind.exit_code) == int(ExitCode.BLOCK) and bind_summary.get("remote_bind_override_enabled") is False and bind_summary.get("non_local_bind_allowed") is False,
            "host": "0.0.0.0",
            "exit_code": int(bind.exit_code),
            "non_local_bind_allowed": bool(bind_summary.get("non_local_bind_allowed")),
            "remote_bind_override_requested": bool(bind_summary.get("remote_bind_override_requested")),
            "remote_bind_override_enabled": bool(bind_summary.get("remote_bind_override_enabled")),
            "remote_bind_override_status": bind_summary.get("remote_bind_override_status"),
        }
        self._finding_if_false(findings, bind_check["ok"], "LOCAL_API_NON_LOCAL_BIND_NOT_BLOCKED", "Non-local API bind was not blocked or override was enabled.")

        security_headers_success = self._headers_present(valid)
        security_headers_error = self._headers_present(invalid)
        security_headers_check = {
            "ok": security_headers_success and security_headers_error,
            "required_headers": sorted(SECURITY_HEADERS),
            "success_headers_present": security_headers_success,
            "error_headers_present": security_headers_error,
            "api_security_header_success": valid.headers.get("X-DevPilot-Api-Security"),
            "api_security_header_error": invalid.headers.get("X-DevPilot-Api-Security"),
        }
        self._finding_if_false(findings, security_headers_check["ok"], "LOCAL_API_SECURITY_HEADERS_MISSING", "Required local API security headers are missing from success or error responses.")

        settings_text = settings.text
        raw_secret_markers = ["sk-proj-", "github_pat_", "Bearer ", options.token]
        raw_secret_markers_found = [marker for marker in raw_secret_markers if marker in settings_text]
        settings_payload = settings.json() if settings.status_code == 200 else {}
        settings_summary = ((settings_payload.get("data") or {}).get("summary") or {}) if isinstance(settings_payload, dict) else {}
        settings_check = {
            "ok": settings.status_code == 200 and not raw_secret_markers_found and settings_summary.get("secrets_redacted") is True and int(settings_summary.get("external_api_enabled_total", 0)) == 0,
            "settings_path": options.settings_providers_path,
            "status_code": settings.status_code,
            "raw_secret_markers_found": raw_secret_markers_found,
            "secrets_redacted": settings_summary.get("secrets_redacted"),
            "external_api_enabled_total": int(settings_summary.get("external_api_enabled_total", 0)) if settings_summary.get("external_api_enabled_total") is not None else 0,
        }
        self._finding_if_false(findings, settings_check["ok"], "LOCAL_API_SETTINGS_SECRET_REDACTION_BLOCK", "Settings providers API exposed raw secret markers or enabled external API providers.")

        token_redaction_check = {
            "ok": redact_token(options.token) != options.token,
            "token_redacted": redact_token(options.token),
            "raw_token_included": False,
        }
        self._finding_if_false(findings, token_redaction_check["ok"], "LOCAL_API_TOKEN_REDACTION_BLOCK", "Token redaction did not mask the local API token.")

        checks = {
            "auth": auth_check,
            "cors": cors_check,
            "bind_host": bind_check,
            "security_headers": security_headers_check,
            "settings_redaction": settings_check,
            "token_redaction": token_redaction_check,
            "no_go_gates": {
                "ok": True,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "external_api_used": False,
                "enterprise_auth_enabled": False,
                "sso_enabled": False,
                "oidc_enabled": False,
            },
        }

        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
        ok = not blocking
        summary = {
            "created_by": POST_H_028_B_CREATED_BY,
            "status": "implemented-initial",
            "decision": "PASS" if ok else "BLOCK",
            "local_api_security_hardening_passed": ok,
            "protected_without_token_blocked": bool(auth_check["missing_token_blocked"]),
            "protected_invalid_token_blocked": bool(auth_check["invalid_token_blocked"]),
            "protected_valid_token_passed": bool(auth_check["valid_token_passed"]),
            "cors_wildcard_enabled": bool(cors_check["wildcard_cors_enabled"]),
            "local_origin_allowed": bool(cors_check["local_origin_allowed"]),
            "non_local_origin_rejected": bool(cors_check["non_local_origin_rejected"]),
            "non_local_bind_allowed": bool(bind_check["non_local_bind_allowed"]),
            "remote_bind_override_enabled": bool(bind_check["remote_bind_override_enabled"]),
            "security_headers_present": bool(security_headers_check["ok"]),
            "settings_secrets_redacted": bool(settings_check["ok"]),
            "token_redacted_in_report": bool(token_redaction_check["ok"]),
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
            "schema_id": LOCAL_API_SECURITY_HARDENING_REPORT_SCHEMA_ID,
            "report_id": "devpilot-local-api-security-hardening-report",
            "created_by": POST_H_028_B_CREATED_BY,
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
                "enterprise_auth_enabled": False,
            },
            "findings": [finding.to_dict() for finding in findings],
            "notes": [
                "POST-H-028-B hardens the local API/UI security posture using in-process TestClient and static policy checks.",
                "The implementation does not introduce OIDC, SSO, multiuser IAM, rate limiting, public remote API exposure or persisted sessions.",
                "Non-local bind remains blocked even when DEVPILOT_API_ALLOW_NON_LOCALHOST is present; the override is future-disabled by design.",
                "Raw tokens and provider secret values are redacted from reports and settings responses.",
            ],
        }

        rendered_report = json.dumps(report, ensure_ascii=False)
        if options.token in rendered_report:
            findings.append(Finding("LOCAL_API_TOKEN_RAW_IN_REPORT_BLOCK", "Raw local API token appeared in LocalApiSecurityHardeningReport.", Severity.BLOCK))
            ok = False
            blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
            summary["decision"] = "BLOCK"
            summary["local_api_security_hardening_passed"] = False
            summary["token_redacted_in_report"] = False
            summary["blocking_findings_total"] = len(blocking)
            summary["findings_total"] = len(findings)
            report["status"] = "blocked"
            report["findings"] = [finding.to_dict() for finding in findings]
            report["summary"] = summary

        schema_result = SchemaValidator(self.root).validate_payload(
            schema=LOCAL_API_SECURITY_HARDENING_REPORT_CONTRACT,
            payload=report,
            instance_label="in-memory:local_api_security_hardening_report",
        )
        if not schema_result.ok:
            findings.extend(_prefix_findings(schema_result.findings, "LOCAL_API_SECURITY_HARDENING_REPORT_SCHEMA"))
            ok = False
            blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
            summary["decision"] = "BLOCK"
            summary["local_api_security_hardening_passed"] = False
            summary["blocking_findings_total"] = len(blocking)
            summary["findings_total"] = len(findings)
            summary["warnings_total"] = len([finding for finding in findings if finding.severity == Severity.WARNING])
            summary["report_schema_valid"] = False
            report["status"] = "blocked"
            report["findings"] = [finding.to_dict() for finding in findings]
        else:
            summary["report_schema_valid"] = True
            report["summary"] = summary

        reports: dict[str, str] = {}
        if options.write_report:
            summary["reports_written"] = True
            report["summary"] = summary
            reports = self._write_reports(report)

        exit_code = ExitCode.PASS if ok else exit_code_for_findings(blocking, default_ok=False)
        return CommandResult(
            command=LOCAL_API_SECURITY_HARDENING_COMMAND,
            ok=ok,
            exit_code=exit_code,
            message="Local API security hardening passed." if ok else "Local API security hardening blocked.",
            data={"summary": summary, "report": report, "reports": reports, "notes": report["notes"]},
            findings=findings or [Finding("LOCAL_API_SECURITY_HARDENING_PASS", "Local API auth/CORS/bind/security-header/redaction hardening passed.", Severity.INFO, metadata={"created_by": POST_H_028_B_CREATED_BY})],
        )

    def _headers_present(self, response: Any) -> bool:
        return all(response.headers.get(header) == value for header, value in SECURITY_HEADERS.items()) and response.headers.get("X-DevPilot-Api-Security") == API_SECURITY_HEADER_VALUE

    @staticmethod
    def _finding_if_false(findings: list[Finding], condition: bool, finding_id: str, message: str) -> None:
        if not condition:
            findings.append(Finding(finding_id, message, Severity.BLOCK))

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
            "# POST-H-028-B - Local API security hardening report",
            "",
            f"- Decision: `{summary.get('decision')}`",
            f"- Missing token blocked: `{summary.get('protected_without_token_blocked')}`",
            f"- Invalid token blocked: `{summary.get('protected_invalid_token_blocked')}`",
            f"- Valid token passed: `{summary.get('protected_valid_token_passed')}`",
            f"- CORS wildcard enabled: `{summary.get('cors_wildcard_enabled')}`",
            f"- Non-local bind allowed: `{summary.get('non_local_bind_allowed')}`",
            f"- Security headers present: `{summary.get('security_headers_present')}`",
            f"- Settings secrets redacted: `{summary.get('settings_secrets_redacted')}`",
            f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
            "",
            "## Safety",
            "",
            "Read-only, dry-run, local-first. No server start, sockets, network, external APIs, source mutations, remote execution, connector write or plugin execution.",
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


def run_local_api_security_hardening(root: Path, *, write_report: bool = False) -> CommandResult:
    return LocalApiSecurityHardeningRunner(root, LocalApiSecurityHardeningOptions(write_report=write_report)).run()


__all__ = [
    "DEFAULT_LOCAL_API_SECURITY_HARDENING_REPORT_JSON",
    "DEFAULT_LOCAL_API_SECURITY_HARDENING_REPORT_MARKDOWN",
    "LOCAL_API_SECURITY_HARDENING_COMMAND",
    "LOCAL_API_SECURITY_HARDENING_REPORT_CONTRACT",
    "LOCAL_API_SECURITY_HARDENING_REPORT_SCHEMA_ID",
    "POST_H_028_B_CREATED_BY",
    "LocalApiSecurityHardeningOptions",
    "LocalApiSecurityHardeningRunner",
    "run_local_api_security_hardening",
]
