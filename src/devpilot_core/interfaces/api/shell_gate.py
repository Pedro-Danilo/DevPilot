from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.interfaces.api.contracts import ApiRouteContractRegistryValidator
from devpilot_core.interfaces.api.ui_contracts import UiRouteContractRegistryValidator
from devpilot_core.schemas import SchemaValidator

POST_H_014_E_CREATED_BY = "POST-H-014-E"
UI_API_SHELL_GATE_COMMAND = "quality ui-api-industrial-shell"
UI_API_SHELL_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-UI-API-SHELL-REPORT-V1"
UI_API_SHELL_REPORT_CONTRACT = "UiApiShellReport"
DEFAULT_UI_API_SHELL_REPORT_JSON = Path("outputs/reports/ui_api_shell_report.json")
DEFAULT_UI_API_SHELL_REPORT_MARKDOWN = Path("outputs/reports/ui_api_shell_report.md")

_REQUIRED_DOC_MARKERS: dict[str, tuple[str, ...]] = {
    "README.md": ("POST-H-014-E", "ui-api-industrial-shell"),
    "docs/05_operations/runbook.md": ("POST-H-014-E", "quality-gate run --profile hardening"),
    "docs/05_operations/ui_api_local_runbook.md": ("POST-H-014-E", "ui-api-industrial-shell"),
    "docs/07_interfaces/ui_api_industrial_shell.md": ("POST-H-014-E", "quality gate"),
    "docs/backlogs/POST-H-014_ui_api_industrial_shell.md": ("POST-H-014-E", "Quality gate UI/API industrial shell"),
}


@dataclass(frozen=True)
class UiApiIndustrialShellGateOptions:
    """Options for the POST-H-014-E UI/API industrial shell quality gate.

    The default path is read-only and suitable for inclusion in the hardening
    and industrial quality-gate profiles. Report writing is explicit and limited
    to outputs/reports. The smoke test invokes the existing UI local smoke
    script; it does not start Vite, browsers, FastAPI servers, network calls,
    provider calls, connectors, plugins or remote execution.
    """

    write_report: bool = False
    output_json: str | Path = DEFAULT_UI_API_SHELL_REPORT_JSON
    output_markdown: str | Path = DEFAULT_UI_API_SHELL_REPORT_MARKDOWN
    run_ui_smoke: bool = True
    smoke_timeout_seconds: int = 45


class UiApiIndustrialShellGate:
    """POST-H-014-E deterministic gate for the local UI/API product shell.

    This gate composes POST-H-014-A/C/D validators and the Web UI smoke test into
    a single hardening signal. It intentionally validates the local shell as an
    implemented-initial product surface, not as production SaaS readiness.
    """

    def __init__(self, root: Path, options: UiApiIndustrialShellGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or UiApiIndustrialShellGateOptions()

    def run(self) -> CommandResult:
        findings: list[Finding] = []

        api_result = ApiRouteContractRegistryValidator(self.root).validate()
        ui_result = UiRouteContractRegistryValidator(self.root).validate()
        smoke_summary = self._run_smoke(findings)
        docs_summary = self._check_docs(findings)
        registry_summary = self._registry_summary(findings)

        for result in (api_result, ui_result):
            findings.extend(self._prefixed_findings(result))

        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        ok = not blocking and api_result.ok and ui_result.ok and bool(smoke_summary.get("ok")) and bool(docs_summary.get("ok")) and bool(registry_summary.get("ok"))

        report = self._build_report(
            api_result=api_result,
            ui_result=ui_result,
            smoke_summary=smoke_summary,
            docs_summary=docs_summary,
            registry_summary=registry_summary,
            findings=findings,
            ok=ok,
        )
        schema_result = SchemaValidator(self.root).validate_payload(
            schema=UI_API_SHELL_REPORT_CONTRACT,
            payload=report,
            instance_label="in-memory:ui_api_shell_report",
        )
        if not schema_result.ok:
            findings.extend(self._prefixed_findings(schema_result, prefix="UI_API_SHELL_REPORT_SCHEMA"))
            ok = False
            blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
            report["summary"]["report_schema_valid"] = False
            report["summary"]["blocking_findings_total"] = len(blocking)
        else:
            report["summary"]["report_schema_valid"] = True

        reports: dict[str, str] = {}
        if self.options.write_report:
            reports = self._write_reports(report)
            report["summary"]["reports_written"] = True
        else:
            report["summary"]["reports_written"] = False

        exit_code = ExitCode.PASS if ok else exit_code_for_findings(blocking, default_ok=False)
        data: dict[str, Any] = {
            "summary": report["summary"],
            "report": report,
            "api_contract_summary": (api_result.data or {}).get("summary", {}),
            "ui_contract_summary": (ui_result.data or {}).get("summary", {}),
            "smoke_summary": smoke_summary,
            "documentation_summary": docs_summary,
            "registry_summary": registry_summary,
            "reports": reports,
            "notes": report["notes"],
        }
        return CommandResult(
            command=UI_API_SHELL_GATE_COMMAND,
            ok=ok,
            exit_code=exit_code,
            message="UI/API industrial shell quality gate passed." if ok else "UI/API industrial shell quality gate found blocking issues.",
            data=data,
            findings=findings or [Finding("UI_API_SHELL_GATE_PASS", "UI/API industrial shell contract, smoke and documentation checks passed.", Severity.INFO, metadata=report["summary"])],
        )

    def _run_smoke(self, findings: list[Finding]) -> dict[str, Any]:
        if not self.options.run_ui_smoke:
            findings.append(Finding("UI_API_SHELL_SMOKE_SKIPPED_WARNING", "UI smoke execution was skipped by options.", Severity.WARNING))
            return {"ok": True, "skipped": True, "command": None, "returncode": 0, "stdout_tail": "", "stderr_tail": "", "network_used": False, "external_api_used": False}

        npm = shutil.which("npm")
        if npm is None:
            findings.append(Finding("UI_API_SHELL_NPM_MISSING", "npm is required to run the local Web UI smoke test.", Severity.BLOCK, path="ui/web/package.json"))
            return {"ok": False, "skipped": False, "command": "npm --prefix ui/web test", "returncode": None, "stdout_tail": "", "stderr_tail": "npm not found", "network_used": False, "external_api_used": False}

        completed = subprocess.run(
            [npm, "--prefix", "ui/web", "test"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=self.options.smoke_timeout_seconds,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        ok = completed.returncode == 0 and "DEVPL WEB UI SMOKE TEST: PASS" in stdout
        if not ok:
            findings.append(
                Finding(
                    "UI_API_SHELL_SMOKE_BLOCK",
                    "Web UI smoke test failed or did not emit the expected PASS marker.",
                    Severity.BLOCK,
                    path="ui/web/scripts/smoke-test.mjs",
                    metadata={"returncode": completed.returncode, "stdout_tail": stdout[-500:], "stderr_tail": stderr[-500:]},
                )
            )
        return {
            "ok": ok,
            "skipped": False,
            "command": "npm --prefix ui/web test",
            "returncode": completed.returncode,
            "stdout_tail": stdout[-1000:],
            "stderr_tail": stderr[-1000:],
            "pass_marker_detected": "DEVPL WEB UI SMOKE TEST: PASS" in stdout,
            "network_used": False,
            "external_api_used": False,
        }

    def _check_docs(self, findings: list[Finding]) -> dict[str, Any]:
        records: list[dict[str, Any]] = []
        for relative_path, markers in _REQUIRED_DOC_MARKERS.items():
            path = self.root / relative_path
            exists = path.exists()
            content = path.read_text(encoding="utf-8") if exists else ""
            missing = [marker for marker in markers if marker.lower() not in content.lower()]
            if not exists:
                findings.append(Finding("UI_API_SHELL_DOC_MISSING", f"Required UI/API shell document is missing: {relative_path}", Severity.BLOCK, path=relative_path))
            elif missing:
                findings.append(Finding("UI_API_SHELL_DOC_MARKER_MISSING", f"Required UI/API shell document lacks POST-H-014-E markers: {relative_path}", Severity.BLOCK, path=relative_path, metadata={"missing_markers": missing}))
            records.append({"path": relative_path, "exists": exists, "required_markers": list(markers), "missing_markers": missing, "ok": exists and not missing})
        ok = all(record["ok"] for record in records)
        return {"ok": ok, "documents_total": len(records), "documents_passed": sum(1 for record in records if record["ok"]), "documents": records}

    def _registry_summary(self, findings: list[Finding]) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        required_markers = {
            ".devpilot/testing/test_contract_registry.json": "post-h-014-ui-api-shell-quality-gate",
            ".devpilot/testing/test_contract_registry_v2.json": "post-h-014-ui-api-shell-quality-gate",
            ".devpilot/docs_governance/source_registry.json": "tests/test_post_h_014_ui_api_shell_gate.py",
            "docs/schemas/schema_catalog.json": UI_API_SHELL_REPORT_SCHEMA_ID,
        }
        for relative_path, marker in required_markers.items():
            path = self.root / relative_path
            exists = path.exists()
            content = path.read_text(encoding="utf-8") if exists else ""
            marker_present = marker in content
            if not exists:
                findings.append(Finding("UI_API_SHELL_REGISTRY_FILE_MISSING", f"Required registry file is missing: {relative_path}", Severity.BLOCK, path=relative_path))
            elif not marker_present:
                findings.append(Finding("UI_API_SHELL_REGISTRY_MARKER_MISSING", f"Required registry marker is missing from {relative_path}: {marker}", Severity.BLOCK, path=relative_path, metadata={"marker": marker}))
            checks.append({"path": relative_path, "marker": marker, "exists": exists, "marker_present": marker_present, "ok": exists and marker_present})
        return {"ok": all(item["ok"] for item in checks), "checks_total": len(checks), "checks_passed": sum(1 for item in checks if item["ok"]), "checks": checks}

    def _build_report(
        self,
        *,
        api_result: CommandResult,
        ui_result: CommandResult,
        smoke_summary: dict[str, Any],
        docs_summary: dict[str, Any],
        registry_summary: dict[str, Any],
        findings: list[Finding],
        ok: bool,
    ) -> dict[str, Any]:
        api_summary = dict((api_result.data or {}).get("summary") or {})
        ui_summary = dict((ui_result.data or {}).get("summary") or {})
        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
        summary = {
            "created_by": POST_H_014_E_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "quality_gate_subgate": "ui-api-industrial-shell",
            "quality_gate_ready": ok,
            "api_registry_ok": api_result.ok,
            "ui_registry_ok": ui_result.ok,
            "ui_smoke_ok": bool(smoke_summary.get("ok")),
            "documentation_ok": bool(docs_summary.get("ok")),
            "registries_synchronized": bool(registry_summary.get("ok")),
            "api_routes_total": int(api_summary.get("routes_total") or 0),
            "api_protected_routes_total": int(api_summary.get("routes_total") or 0) - int(api_summary.get("public_routes_total") or 0),
            "ui_routes_total": int(ui_summary.get("routes_total") or 0),
            "no_go_violations_total": int(api_summary.get("remote_execution_allowed_total") or 0)
            + int(api_summary.get("connector_write_allowed_total") or 0)
            + int(api_summary.get("plugin_execution_allowed_total") or 0)
            + int(ui_summary.get("no_go_violations_total") or 0),
            "findings_total": len(findings),
            "warnings_total": len(warnings),
            "blocking_findings_total": len(blocking),
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "llm_judge_used": False,
            "reports_written": False,
            "report_schema_valid": False,
        }
        return {
            "schema_version": "1.0",
            "schema_id": UI_API_SHELL_REPORT_SCHEMA_ID,
            "report_id": "devpilot-ui-api-shell-report",
            "created_by": POST_H_014_E_CREATED_BY,
            "status": "implemented-initial",
            "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "summary": summary,
            "checks": {
                "api_contract": {"ok": api_result.ok, "summary": api_summary},
                "ui_contract": {"ok": ui_result.ok, "summary": ui_summary},
                "ui_smoke": smoke_summary,
                "documentation": docs_summary,
                "registries": registry_summary,
            },
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
            },
            "findings": [finding.to_dict() for finding in findings],
            "notes": [
                "POST-H-014-E integrates the UI/API shell into hardening/industrial quality-gate profiles.",
                "This report validates implemented-initial local product-shell readiness; it is not production SaaS, cloud or enterprise-auth certification.",
                "The smoke test is local and deterministic; it does not start browsers, servers, connectors, plugins, LLMs, web search or external APIs.",
            ],
        }

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        output_json = Path(self.options.output_json)
        output_markdown = Path(self.options.output_markdown)
        json_path = output_json if output_json.is_absolute() else self.root / output_json
        md_path = output_markdown if output_markdown.is_absolute() else self.root / output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(self._markdown(report), encoding="utf-8")
        return {"json": _relative(json_path, self.root), "markdown": _relative(md_path, self.root)}

    def _markdown(self, report: dict[str, Any]) -> str:
        summary = report.get("summary", {})
        lines = [
            "# UI/API shell quality gate report",
            "",
            f"- Created by: `{report.get('created_by')}`",
            f"- Status: `{report.get('status')}`",
            f"- Quality gate ready: `{summary.get('quality_gate_ready')}`",
            f"- API registry OK: `{summary.get('api_registry_ok')}`",
            f"- UI registry OK: `{summary.get('ui_registry_ok')}`",
            f"- UI smoke OK: `{summary.get('ui_smoke_ok')}`",
            f"- Documentation OK: `{summary.get('documentation_ok')}`",
            f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
            "",
            "This is local-first, dry-run evidence for POST-H-014-E. It does not certify production, SaaS, cloud, OIDC, remote execution, connector write or plugin execution readiness.",
            "",
        ]
        return "\n".join(lines)

    def _prefixed_findings(self, result: CommandResult, *, prefix: str | None = None) -> list[Finding]:
        findings: list[Finding] = []
        for finding in result.findings:
            if finding.severity == Severity.INFO:
                continue
            metadata = dict(finding.metadata or {})
            metadata.setdefault("source_command", result.command)
            findings.append(
                Finding(
                    id=f"{prefix}_{finding.id}" if prefix else finding.id,
                    message=finding.message,
                    severity=finding.severity,
                    path=finding.path,
                    metadata=metadata,
                )
            )
        return findings


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")
