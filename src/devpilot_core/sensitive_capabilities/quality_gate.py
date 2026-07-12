from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.sensitive_capabilities.models import SensitiveCapabilityOptions
from devpilot_core.sensitive_capabilities.validator import ConnectorWriteAdrValidator, PluginExecutionAdrValidator

_BLOCKING = {Severity.BLOCK, Severity.ERROR, Severity.FAIL}


class SensitiveCapabilityAdrGate:
    """Quality gate for POST-H-034 sensitive capability ADR boundaries.

    POST-H-034-A validates connector.write. POST-H-034-B extends the same gate
    to plugin.execution while preserving backward-compatible connector summary
    keys for historical tests and operator scripts. The gate remains read-only,
    local-first and no-execution.
    """

    def __init__(self, root: Path, *, options: SensitiveCapabilityOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SensitiveCapabilityOptions()

    def run(self) -> CommandResult:
        connector_result = ConnectorWriteAdrValidator(self.root, options=self.options).validate()
        plugin_result = PluginExecutionAdrValidator(self.root, options=self.options).validate()
        findings: list[Finding] = [*connector_result.findings, *plugin_result.findings]
        blocking = [finding for finding in findings if finding.severity in _BLOCKING]
        connector_summary = connector_result.data.get("summary", {}) if isinstance(connector_result.data, dict) else {}
        plugin_summary = plugin_result.data.get("summary", {}) if isinstance(plugin_result.data, dict) else {}
        summary = {
            **connector_summary,
            "subgates_total": 2,
            "subgates_passed": int(connector_result.ok) + int(plugin_result.ok),
            "connector_write_gate_ok": connector_result.ok,
            "plugin_execution_gate_ok": plugin_result.ok,
            "plugin_decision_state": plugin_summary.get("plugin_decision_state"),
            "plugin_execution_enabled": plugin_summary.get("plugin_execution_enabled"),
            "runtime_execution_enabled": plugin_summary.get("runtime_execution_enabled"),
            "plugin_code_loading_enabled": plugin_summary.get("plugin_code_loading_enabled"),
            "dynamic_import_allowed": plugin_summary.get("dynamic_import_allowed"),
            "subprocess_allowed": plugin_summary.get("subprocess_allowed"),
            "project_state_plugin_execution_enabled": plugin_summary.get("project_state_plugin_execution_enabled"),
            "blocking_findings_total": len(blocking),
            "findings_total": len(findings),
            "reports_written": False,
        }
        return CommandResult(
            command="sensitive-capability-adr-gate",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Sensitive capability ADR gate passed." if not blocking else "Sensitive capability ADR gate blocked.",
            data={
                "summary": summary,
                "subgates": {
                    "connector_write": connector_result.to_dict(),
                    "plugin_execution": plugin_result.to_dict(),
                },
                "notes": [
                    "POST-H-034-A/B gate validates ADR/no-go decisions only.",
                    "The gate does not enable connector write, plugin execution, remote execution, external APIs, network use or source mutations.",
                ],
            },
            findings=findings,
        )
