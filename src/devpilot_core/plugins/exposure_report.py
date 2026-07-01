from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.plugins.permission_model import PluginPermissionModel, PluginPermissionModelOptions
from devpilot_core.plugins.static_validator import PluginStaticValidator, PluginStaticValidatorOptions
from devpilot_core.schemas import SchemaValidator

DEFAULT_PLUGIN_EXPOSURE_REPORT_JSON = "outputs/reports/plugin_exposure_report.json"
DEFAULT_PLUGIN_EXPOSURE_REPORT_MD = "outputs/reports/plugin_exposure_report.md"
DEFAULT_PLUGIN_SANDBOX_DESIGN_REPORT_SCHEMA = "PluginSandboxDesignReport"
_BLOCKING_SEVERITIES = {Severity.BLOCK, Severity.ERROR, Severity.FAIL}


@dataclass(frozen=True)
class PluginExposureReportOptions:
    """Options for POST-H-019-C plugin exposure report generation."""

    registry_path: str = ".devpilot/plugins/plugin_registry.json"
    schema_path: str = "docs/schemas/plugin_manifest.schema.json"
    connector_registry_path: str = ".devpilot/connectors/connector_registry.json"
    permission_model_path: str = ".devpilot/plugins/plugin_permission_model.json"
    permission_model_schema_path: str = "docs/schemas/plugin_permission_model.schema.json"
    output_json: str = DEFAULT_PLUGIN_EXPOSURE_REPORT_JSON
    output_markdown: str = DEFAULT_PLUGIN_EXPOSURE_REPORT_MD


class PluginExposureReporter:
    """Build POST-H-019-C plugin install dry-run exposure evidence.

    The report separates metadata declaration, static validation, install
    simulation and executable state. It never turns a manifest into executable
    authority and never performs network, dependency installation, filesystem
    mutation, shell execution or remote execution.
    """

    def __init__(self, root: Path, *, options: PluginExposureReportOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or PluginExposureReportOptions()

    def build(self, *, write_report: bool = False) -> CommandResult:
        static_options = PluginStaticValidatorOptions(
            registry_path=self.options.registry_path,
            schema_path=self.options.schema_path,
            connector_registry_path=self.options.connector_registry_path,
            permission_model_path=self.options.permission_model_path,
            permission_model_schema_path=self.options.permission_model_schema_path,
        )
        static_result = PluginStaticValidator(self.root, options=static_options).validate()
        permission_result = PluginPermissionModel(
            self.root,
            options=PluginPermissionModelOptions(
                model_path=self.options.permission_model_path,
                schema_path=self.options.permission_model_schema_path,
            ),
        ).validate()
        findings: list[Finding] = []
        if not static_result.ok:
            findings.extend(static_result.findings)
        if not permission_result.ok:
            findings.extend(permission_result.findings)

        report = self._report(static_result=static_result, permission_result=permission_result, findings=findings)
        schema_result = SchemaValidator(self.root).validate_payload(
            schema=DEFAULT_PLUGIN_SANDBOX_DESIGN_REPORT_SCHEMA,
            payload=report,
            instance_label=self.options.output_json,
        )
        if not schema_result.ok:
            findings.extend(schema_result.findings)
        blocking = _blocking(findings)

        reports: dict[str, str] = {}
        if write_report:
            reports = self.write(report)

        summary = dict(report["summary"])
        summary["schema_valid"] = schema_result.ok
        summary["reports_written"] = bool(write_report)
        summary["output_json"] = reports.get("json")
        summary["output_markdown"] = reports.get("markdown")
        summary["blocking_findings_total"] = len(blocking)
        report["summary"] = summary
        data: dict[str, Any] = {"summary": summary, "report": report}
        if reports:
            data["reports"] = reports

        ok = not blocking
        return CommandResult(
            command="plugin dry-run",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Plugin install dry-run and exposure report passed." if ok else "Plugin install dry-run exposure report blocked.",
            data=data,
            findings=findings or [Finding("PLUGIN_EXPOSURE_REPORT_PASS", "Plugin exposure report confirms metadata-only install dry-run and plugin execution blocked.", Severity.INFO, metadata=summary)],
        )

    def write(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self._resolve(self.options.output_json)
        markdown_path = self._resolve(self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(self._markdown(report), encoding="utf-8")
        return {"json": _rel(self.root, json_path), "markdown": _rel(self.root, markdown_path)}

    def _report(self, *, static_result: CommandResult, permission_result: CommandResult, findings: list[Finding]) -> dict[str, Any]:
        static_summary = static_result.data.get("summary", {}) if isinstance(static_result.data, dict) else {}
        permission_summary = permission_result.data.get("summary", {}) if isinstance(permission_result.data, dict) else {}
        plugins = static_result.data.get("plugins", []) if isinstance(static_result.data, dict) else []
        plugins = plugins if isinstance(plugins, list) else []
        model = self._read_json(self.options.permission_model_path)
        permissions = [item for item in model.get("permissions", []) if isinstance(item, dict)]
        allowed_permissions = [item for item in permissions if item.get("effect") == "allow"]
        blocked_permissions = [item for item in permissions if item.get("effect") == "deny"]
        manifest_critical_permissions = 0
        permission_index = {str(item.get("permission_id")): item for item in permissions if item.get("permission_id")}
        for plugin in plugins:
            for permission in plugin.get("permissions", []) or []:
                model_permission = permission_index.get(str(permission.get("canonical_permission_id")))
                if model_permission and model_permission.get("risk_level") in {"high", "critical"}:
                    manifest_critical_permissions += 1

        blocked = _blocking(findings)
        summary = {
            "created_by": "POST-H-019-C",
            "status": "implemented-initial",
            "preliminary": True,
            "registry_path": self.options.registry_path,
            "permission_model_path": self.options.permission_model_path,
            "plugins_total": int(static_summary.get("plugins_total", len(plugins)) or 0),
            "metadata_only_total": int(static_summary.get("metadata_only_total", 0) or 0),
            "install_simulated_total": int(static_summary.get("install_simulated_total", 0) or 0),
            "execution_allowed_total": int(static_summary.get("execution_allowed_total", 0) or 0),
            "critical_permissions_total": manifest_critical_permissions,
            "allowed_permissions_total": len(allowed_permissions),
            "blocked_permissions_total": len(blocked_permissions),
            "unknown_permissions_effect": permission_summary.get("unknown_permissions_effect"),
            "plugin_execution_allowed": model.get("plugin_execution_allowed") is True,
            "dynamic_import_allowed": model.get("dynamic_import_allowed") is True,
            "subprocess_allowed": model.get("subprocess_allowed") is True,
            "network_allowed": model.get("network_allowed") is True,
            "external_api_allowed": model.get("external_api_allowed") is True,
            "filesystem_write_allowed": model.get("filesystem_write_allowed") is True,
            "shell_allowed": model.get("shell_allowed") is True,
            "remote_execution_allowed": model.get("remote_execution_allowed") is True,
            "pip_install_allowed": model.get("pip_install_allowed") is True,
            "marketplace_enabled": model.get("marketplace_enabled") is True,
            "plugin_code_loaded": False,
            "arbitrary_code_execution_performed": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "shell_used": False,
            "remote_execution_used": False,
            "dependencies_installed": False,
            "marketplace_used": False,
            "arbitrary_files_read": False,
            "static_validation_passed": static_result.ok,
            "permission_model_valid": permission_result.ok,
            "blocking_findings_total": len(blocked),
        }
        return {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-PLUGIN-SANDBOX-DESIGN-REPORT-V1",
            "report_id": "devpilot-plugin-exposure-report",
            "created_by": "POST-H-019-C",
            "status": "implemented-initial",
            "generated_at_utc": _now_utc(),
            "preliminary": True,
            "plugins_total": summary["plugins_total"],
            "metadata_only_total": summary["metadata_only_total"],
            "execution_allowed_total": summary["execution_allowed_total"],
            "critical_permissions_total": summary["critical_permissions_total"],
            "blocked_permissions_total": summary["blocked_permissions_total"],
            "network_allowed": summary["network_allowed"],
            "dynamic_import_allowed": summary["dynamic_import_allowed"],
            "subprocess_allowed": summary["subprocess_allowed"],
            "blocking_findings_total": summary["blocking_findings_total"],
            "summary": summary,
            "plugins": plugins,
            "permission_model": {
                "model_path": self.options.permission_model_path,
                "permissions_total": len(permissions),
                "allowed_permissions_total": len(allowed_permissions),
                "blocked_permissions_total": len(blocked_permissions),
                "blocked_permission_ids": [str(item.get("permission_id")) for item in blocked_permissions],
            },
            "findings": [finding.to_dict() for finding in findings],
            "safety": {
                "local_first": True,
                "dry_run": True,
                "metadata_only": True,
                "plugin_execution_enabled": False,
                "dynamic_loading_enabled": False,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "shell_used": False,
                "remote_execution_used": False,
                "dependencies_installed": False,
                "marketplace_used": False,
            },
            "notes": [
                "POST-H-019-C install dry-run is metadata-only and not a plugin execution engine.",
                "Manifest validation, permission allowlists and exposure reports are not executable authorization.",
                "Future plugin execution requires ADR, sandbox isolation, RBAC, approvals, evals, observability and rollback.",
            ],
        }

    def _markdown(self, report: dict[str, Any]) -> str:
        summary = report["summary"]
        rows = [
            ("plugins_total", summary["plugins_total"]),
            ("metadata_only_total", summary["metadata_only_total"]),
            ("install_simulated_total", summary["install_simulated_total"]),
            ("execution_allowed_total", summary["execution_allowed_total"]),
            ("blocked_permissions_total", summary["blocked_permissions_total"]),
            ("network_used", summary["network_used"]),
            ("external_api_used", summary["external_api_used"]),
            ("mutations_performed", summary["mutations_performed"]),
            ("blocking_findings_total", summary["blocking_findings_total"]),
        ]
        body = [
            "---",
            'doc_id: "POST-H-019-C-PLUGIN-EXPOSURE-REPORT-RUNTIME"',
            'status: "generated"',
            'owner: "Ordóñez"',
            'created_by: "POST-H-019-C"',
            "---",
            "",
            "# Plugin exposure report",
            "",
            "Runtime evidence generated from metadata-only plugin install dry-run. This report is not execution authorization.",
            "",
            "| Metric | Value |",
            "|---|---:|",
        ]
        for key, value in rows:
            body.append(f"| `{key}` | `{value}` |")
        body.extend(["", "## Plugins", ""])
        for plugin in report.get("plugins", []):
            body.append(f"- `{plugin.get('plugin_id')}` — install_state=`{plugin.get('install_state')}`, metadata_only=`{plugin.get('metadata_only')}`, execution_allowed=`{plugin.get('execution_allowed')}`")
        body.extend(["", "## No-go gates", "", "PASS requiere execution_allowed_total=0, network_used=false, external_api_used=false, mutations_performed=false y dependencies_installed=false.", ""])
        return "\n".join(body)

    def _read_json(self, path: str) -> dict[str, Any]:
        payload = json.loads(self._resolve(path).read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}

    def _resolve(self, value: str | Path) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _blocking(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity in _BLOCKING_SEVERITIES]


def _exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
