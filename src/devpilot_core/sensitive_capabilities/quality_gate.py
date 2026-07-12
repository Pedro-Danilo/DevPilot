from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.sensitive_capabilities.models import SensitiveCapabilityOptions
from devpilot_core.sensitive_capabilities.validator import ConnectorWriteAdrValidator, PluginExecutionAdrValidator, RemoteExecutionAdr3Validator, MultiuserAuthAdrValidator, EnterpriseSaasBoundaryAdrValidator

_BLOCKING = {Severity.BLOCK, Severity.ERROR, Severity.FAIL}


class SensitiveCapabilityAdrGate:
    """Quality gate for POST-H-034 sensitive capability ADR boundaries.

    POST-H-034-A validates connector.write. POST-H-034-B extends the same gate
    to plugin.execution. POST-H-034-C adds remote.execution ADR-3, POST-H-034-D adds multiuser.auth,
    and POST-H-034-E adds enterprise.saas boundary. The gate remains read-only, local-first, no-execution and no-network.
    """

    def __init__(self, root: Path, *, options: SensitiveCapabilityOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SensitiveCapabilityOptions()

    def run(self) -> CommandResult:
        connector_result = ConnectorWriteAdrValidator(self.root, options=self.options).validate()
        plugin_result = PluginExecutionAdrValidator(self.root, options=self.options).validate()
        remote_result = RemoteExecutionAdr3Validator(self.root, options=self.options).validate()
        multiuser_result = MultiuserAuthAdrValidator(self.root, options=self.options).validate()
        enterprise_saas_result = EnterpriseSaasBoundaryAdrValidator(self.root, options=self.options).validate()
        findings: list[Finding] = [*connector_result.findings, *plugin_result.findings, *remote_result.findings, *multiuser_result.findings, *enterprise_saas_result.findings]
        blocking = [finding for finding in findings if finding.severity in _BLOCKING]
        connector_summary = connector_result.data.get("summary", {}) if isinstance(connector_result.data, dict) else {}
        plugin_summary = plugin_result.data.get("summary", {}) if isinstance(plugin_result.data, dict) else {}
        remote_summary = remote_result.data.get("summary", {}) if isinstance(remote_result.data, dict) else {}
        multiuser_summary = multiuser_result.data.get("summary", {}) if isinstance(multiuser_result.data, dict) else {}
        enterprise_saas_summary = enterprise_saas_result.data.get("summary", {}) if isinstance(enterprise_saas_result.data, dict) else {}
        summary = {
            **connector_summary,
            "subgates_total": 5,
            "subgates_passed": int(connector_result.ok) + int(plugin_result.ok) + int(remote_result.ok) + int(multiuser_result.ok) + int(enterprise_saas_result.ok),
            "connector_write_gate_ok": connector_result.ok,
            "plugin_execution_gate_ok": plugin_result.ok,
            "remote_execution_adr3_gate_ok": remote_result.ok,
            "multiuser_auth_gate_ok": multiuser_result.ok,
            "enterprise_saas_boundary_gate_ok": enterprise_saas_result.ok,
            "plugin_decision_state": plugin_summary.get("plugin_decision_state"),
            "plugin_execution_enabled": plugin_summary.get("plugin_execution_enabled"),
            "runtime_execution_enabled": plugin_summary.get("runtime_execution_enabled"),
            "plugin_code_loading_enabled": plugin_summary.get("plugin_code_loading_enabled"),
            "dynamic_import_allowed": plugin_summary.get("dynamic_import_allowed"),
            "subprocess_allowed": plugin_summary.get("subprocess_allowed"),
            "project_state_plugin_execution_enabled": plugin_summary.get("project_state_plugin_execution_enabled"),
            "remote_decision_state": remote_summary.get("remote_decision_state"),
            "remote_execution_enabled": remote_summary.get("remote_execution_enabled"),
            "remote_runner_enabled": remote_summary.get("remote_runner_enabled"),
            "runtime_remote_execution_enabled": remote_summary.get("runtime_execution_enabled"),
            "remote_transport_enabled": remote_summary.get("remote_transport_enabled"),
            "secure_transport_implemented": remote_summary.get("secure_transport_implemented"),
            "project_state_remote_execution_enabled": remote_summary.get("project_state_remote_execution_enabled"),
            "multiuser_decision_state": multiuser_summary.get("multiuser_decision_state"),
            "multiuser_auth_enabled": multiuser_summary.get("multiuser_auth_enabled"),
            "production_multiuser_enabled": multiuser_summary.get("production_multiuser_enabled"),
            "iam_enterprise_enabled": multiuser_summary.get("iam_enterprise_enabled"),
            "session_management_enabled": multiuser_summary.get("session_management_enabled"),
            "tenancy_enabled": multiuser_summary.get("tenancy_enabled"),
            "public_api_enabled": multiuser_summary.get("public_api_enabled"),
            "enterprise_saas_decision_state": enterprise_saas_summary.get("enterprise_saas_decision_state"),
            "enterprise_ready_claimed": enterprise_saas_summary.get("enterprise_ready_claimed"),
            "saas_ready_claimed": enterprise_saas_summary.get("saas_ready_claimed"),
            "control_plane_enabled": enterprise_saas_summary.get("control_plane_enabled"),
            "cloud_deployment_enabled": enterprise_saas_summary.get("cloud_deployment_enabled"),
            "enterprise_saas_tenancy_enabled": enterprise_saas_summary.get("tenancy_enabled"),
            "enterprise_saas_public_api_enabled": enterprise_saas_summary.get("public_api_enabled"),
            "compliance_certification_claim": enterprise_saas_summary.get("compliance_certification_claim"),
            "compliance_certified": enterprise_saas_summary.get("compliance_certified"),
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
                    "remote_execution_adr3": remote_result.to_dict(),
                    "multiuser_auth": multiuser_result.to_dict(),
                    "enterprise_saas_boundary": enterprise_saas_result.to_dict(),
                },
                "notes": [
                    "POST-H-034-A/B/C/D/E gate validates ADR/no-go decisions only.",
                    "The gate does not enable connector write, plugin execution, remote execution, multiuser auth, enterprise/SaaS, compliance certification, external APIs, network use or source mutations.",
                ],
            },
            findings=findings,
        )
