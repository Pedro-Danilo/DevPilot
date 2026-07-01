from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.plugins.exposure_report import PluginExposureReporter, PluginExposureReportOptions
from devpilot_core.plugins.permission_model import PluginPermissionModel, PluginPermissionModelOptions
from devpilot_core.plugins.registry import PluginRegistry, PluginRegistryOptions

_BLOCKING_SEVERITIES = {Severity.BLOCK, Severity.ERROR, Severity.FAIL}


@dataclass(frozen=True)
class PluginSandboxQualityGateOptions:
    """Paths used by the POST-H-019-D plugin sandbox design quality gate."""

    registry_path: str = ".devpilot/plugins/plugin_registry.json"
    schema_path: str = "docs/schemas/plugin_manifest.schema.json"
    connector_registry_path: str = ".devpilot/connectors/connector_registry.json"
    permission_model_path: str = ".devpilot/plugins/plugin_permission_model.json"
    permission_model_schema_path: str = "docs/schemas/plugin_permission_model.schema.json"
    plugin_ecosystem_fixture_path: str = "evals/fixtures/plugin_ecosystem_eval_cases.json"


class PluginSandboxQualityGate:
    """Validate metadata-only plugin safety as a hardening quality subgate.

    POST-H-019-D composes existing validators instead of introducing a plugin
    runtime. The gate validates registry metadata, the deny-by-default permission
    model, exposure report invariants and the existing plugin-ecosystem eval
    fixture signal without importing plugin code, installing dependencies,
    starting subprocesses, opening network connections or writing reports.
    """

    def __init__(self, root: Path, *, options: PluginSandboxQualityGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or PluginSandboxQualityGateOptions()

    def run(self) -> CommandResult:
        registry_result = PluginRegistry(
            self.root,
            options=PluginRegistryOptions(
                registry_path=self.options.registry_path,
                schema_path=self.options.schema_path,
                connector_registry_path=self.options.connector_registry_path,
                permission_model_path=self.options.permission_model_path,
                permission_model_schema_path=self.options.permission_model_schema_path,
            ),
        ).validate()
        permission_result = PluginPermissionModel(
            self.root,
            options=PluginPermissionModelOptions(
                model_path=self.options.permission_model_path,
                schema_path=self.options.permission_model_schema_path,
            ),
        ).validate()
        exposure_result = PluginExposureReporter(
            self.root,
            options=PluginExposureReportOptions(
                registry_path=self.options.registry_path,
                schema_path=self.options.schema_path,
                connector_registry_path=self.options.connector_registry_path,
                permission_model_path=self.options.permission_model_path,
                permission_model_schema_path=self.options.permission_model_schema_path,
            ),
        ).build(write_report=False)
        eval_signal, eval_findings = self._plugin_ecosystem_eval_signal()

        findings: list[Finding] = []
        for result in (registry_result, permission_result, exposure_result):
            if not result.ok:
                findings.extend(result.findings)
        findings.extend(eval_findings)

        registry_summary = _summary(registry_result)
        permission_summary = _summary(permission_result)
        exposure_summary = _summary(exposure_result)
        model = self._read_json(self.options.permission_model_path)

        summary = {
            "created_by": "POST-H-019-D",
            "status": "implemented-initial",
            "preliminary": True,
            "quality_gate_subgate": "plugin-sandbox-design",
            "registry_valid": registry_result.ok,
            "permission_model_valid": permission_result.ok,
            "exposure_report_valid": exposure_result.ok,
            "quality_gate_evaluates_plugin_registry": True,
            "quality_gate_evaluates_permission_model": True,
            "quality_gate_evaluates_exposure_report": True,
            "plugin_ecosystem_eval_signal_present": eval_signal["ok"],
            "plugin_ecosystem_suite_id": eval_signal.get("suite_id"),
            "plugin_ecosystem_cases_total": eval_signal.get("cases_total"),
            "plugin_ecosystem_minimum_safety_score": eval_signal.get("minimum_safety_score"),
            "plugins_total": exposure_summary.get("plugins_total", registry_summary.get("plugins_total", 0)),
            "metadata_only_total": exposure_summary.get("metadata_only_total", 0),
            "install_simulated_total": exposure_summary.get("install_simulated_total", 0),
            "execution_allowed_total": exposure_summary.get("execution_allowed_total", 0),
            "critical_permissions_total": exposure_summary.get("critical_permissions_total", 0),
            "all_plugin_manifests_metadata_only": exposure_summary.get("plugins_total") == exposure_summary.get("metadata_only_total"),
            "all_plugins_install_simulated": exposure_summary.get("plugins_total") == exposure_summary.get("install_simulated_total"),
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
            "source_mutations_performed": False,
            "shell_used": False,
            "remote_execution_used": False,
            "dependencies_installed": False,
            "marketplace_used": False,
        }

        findings.extend(self._invariant_findings(summary))
        blocking = _blocking(findings)
        summary["blocking_findings_total"] = len(blocking)
        ok = not blocking
        return CommandResult(
            command="quality plugin-sandbox-design",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Plugin sandbox design quality gate passed." if ok else "Plugin sandbox design quality gate blocked.",
            data={
                "summary": summary,
                "registry": registry_result.data,
                "permission_model": permission_result.data,
                "exposure_report": exposure_result.data,
                "plugin_ecosystem_eval_signal": eval_signal,
            },
            findings=findings
            or [
                Finding(
                    "PLUGIN_SANDBOX_QUALITY_GATE_PASS",
                    "Plugin sandbox design quality gate confirms metadata-only plugins and blocked execution.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _plugin_ecosystem_eval_signal(self) -> tuple[dict[str, Any], list[Finding]]:
        path = self._resolve(self.options.plugin_ecosystem_fixture_path)
        summary: dict[str, Any] = {
            "ok": False,
            "fixture_path": self.options.plugin_ecosystem_fixture_path,
            "fixture_exists": path.exists(),
            "suite_id": None,
            "cases_total": 0,
            "minimum_safety_score": None,
            "network_used": False,
            "external_api_used": False,
            "llm_judge_used": False,
        }
        findings: list[Finding] = []
        if not path.exists():
            findings.append(Finding("PLUGIN_ECOSYSTEM_EVAL_FIXTURE_MISSING", "Plugin ecosystem eval fixture is missing.", Severity.BLOCK, path=self.options.plugin_ecosystem_fixture_path))
            return summary, findings
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("PLUGIN_ECOSYSTEM_EVAL_FIXTURE_INVALID_JSON", "Plugin ecosystem eval fixture is not valid JSON.", Severity.ERROR, path=self.options.plugin_ecosystem_fixture_path, metadata={"error": str(exc)}))
            return summary, findings

        cases = payload.get("cases") if isinstance(payload, dict) else None
        case_ids = {str(item.get("id")) for item in cases if isinstance(item, dict)} if isinstance(cases, list) else set()
        required_case_ids = {
            "plugin-clean-metadata-pass",
            "plugin-code-loading-block",
            "plugin-external-access-block",
            "plugin-policy-observability-block",
        }
        summary.update(
            {
                "suite_id": payload.get("suite_id") if isinstance(payload, dict) else None,
                "cases_total": len(cases) if isinstance(cases, list) else 0,
                "minimum_safety_score": payload.get("minimum_safety_score") if isinstance(payload, dict) else None,
                "network_used": payload.get("network_used") is True if isinstance(payload, dict) else False,
                "external_api_used": payload.get("external_api_used") is True if isinstance(payload, dict) else False,
                "llm_judge_used": payload.get("llm_judge_used") is True if isinstance(payload, dict) else False,
                "required_case_ids_present": sorted(required_case_ids.intersection(case_ids)),
            }
        )
        if summary["suite_id"] != "plugin-ecosystem":
            findings.append(Finding("PLUGIN_ECOSYSTEM_EVAL_SUITE_UNEXPECTED", "Plugin ecosystem eval fixture suite_id is not plugin-ecosystem.", Severity.FAIL, path=self.options.plugin_ecosystem_fixture_path, metadata={"suite_id": summary["suite_id"]}))
        if not isinstance(cases, list) or len(cases) < 4:
            findings.append(Finding("PLUGIN_ECOSYSTEM_EVAL_CASES_INSUFFICIENT", "Plugin ecosystem eval fixture must include at least four safety cases.", Severity.BLOCK, path=self.options.plugin_ecosystem_fixture_path, metadata={"cases_total": summary["cases_total"]}))
        missing = sorted(required_case_ids - case_ids)
        if missing:
            findings.append(Finding("PLUGIN_ECOSYSTEM_EVAL_CASES_MISSING", "Plugin ecosystem eval fixture is missing required safety cases.", Severity.BLOCK, path=self.options.plugin_ecosystem_fixture_path, metadata={"missing_case_ids": missing}))
        for blocked_flag in ("network_used", "external_api_used", "llm_judge_used"):
            if summary[blocked_flag] is True:
                findings.append(Finding("PLUGIN_ECOSYSTEM_EVAL_UNSAFE_FLAG", "Plugin ecosystem eval signal must remain local, deterministic and non-LLM-judged.", Severity.BLOCK, path=self.options.plugin_ecosystem_fixture_path, metadata={"flag": blocked_flag}))
        summary["ok"] = not _blocking(findings)
        return summary, findings

    def _invariant_findings(self, summary: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        if summary["plugin_execution_allowed"] is True or summary["execution_allowed_total"]:
            findings.append(Finding("PLUGIN_SANDBOX_EXECUTION_ENABLED_BLOCKED", "Plugin execution must remain blocked for POST-H-019-D.", Severity.BLOCK, metadata={"execution_allowed_total": summary["execution_allowed_total"]}))
        for flag in (
            "dynamic_import_allowed",
            "subprocess_allowed",
            "network_allowed",
            "external_api_allowed",
            "filesystem_write_allowed",
            "shell_allowed",
            "remote_execution_allowed",
            "pip_install_allowed",
            "marketplace_enabled",
            "plugin_code_loaded",
            "arbitrary_code_execution_performed",
            "network_used",
            "external_api_used",
            "mutations_performed",
            "source_mutations_performed",
            "dependencies_installed",
            "marketplace_used",
        ):
            if summary.get(flag) is True:
                findings.append(Finding("PLUGIN_SANDBOX_UNSAFE_FLAG_BLOCKED", "Plugin sandbox quality gate blocks unsafe safety flags.", Severity.BLOCK, metadata={"flag": flag}))
        if summary["all_plugin_manifests_metadata_only"] is not True:
            findings.append(Finding("PLUGIN_SANDBOX_METADATA_ONLY_BLOCKED", "All plugin manifests must validate as metadata-only.", Severity.BLOCK, metadata={"plugins_total": summary["plugins_total"], "metadata_only_total": summary["metadata_only_total"]}))
        if summary["plugin_ecosystem_eval_signal_present"] is not True:
            findings.append(Finding("PLUGIN_SANDBOX_EVAL_SIGNAL_BLOCKED", "Plugin ecosystem eval safety signal is required for POST-H-019-D.", Severity.BLOCK, metadata={"suite_id": summary.get("plugin_ecosystem_suite_id")}))
        return findings

    def _read_json(self, path: str) -> dict[str, Any]:
        payload = json.loads(self._resolve(path).read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}

    def _resolve(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()


def _summary(result: CommandResult) -> dict[str, Any]:
    data = result.data if isinstance(result.data, dict) else {}
    summary = data.get("summary")
    return summary if isinstance(summary, dict) else {}


def _blocking(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity in _BLOCKING_SEVERITIES]


def _exit_code(findings: list[Finding]) -> ExitCode:
    if any(finding.severity == Severity.ERROR for finding in findings):
        return ExitCode.ERROR
    if any(finding.severity == Severity.BLOCK for finding in findings):
        return ExitCode.BLOCK
    if any(finding.severity == Severity.FAIL for finding in findings):
        return ExitCode.FAIL
    return ExitCode.PASS
