from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.sensitive_capabilities.decision_matrix import (
    connector_write_decision_from_matrix,
    load_connector_write_decision,
    load_decision_matrix,
    load_plugin_execution_decision,
    load_remote_execution_adr3_decision,
    load_multiuser_auth_decision,
    load_enterprise_saas_boundary_decision,
    plugin_execution_decision_from_matrix,
    remote_execution_decision_from_matrix,
    multiuser_auth_decision_from_matrix,
    enterprise_saas_decision_from_matrix,
)
from devpilot_core.sensitive_capabilities.models import (
    ALLOWED_CONNECTOR_WRITE_DECISIONS,
    ALLOWED_PLUGIN_EXECUTION_DECISIONS,
    ALLOWED_REMOTE_EXECUTION_ADR3_DECISIONS,
    ALLOWED_MULTIUSER_AUTH_DECISIONS,
    ALLOWED_ENTERPRISE_SAAS_BOUNDARY_DECISIONS,
    POST_H_034_A_CREATED_BY,
    POST_H_034_A_EXPECTED_DECISION,
    POST_H_034_B_CREATED_BY,
    POST_H_034_B_EXPECTED_DECISION,
    POST_H_034_C_CREATED_BY,
    POST_H_034_C_EXPECTED_DECISION,
    POST_H_034_D_CREATED_BY,
    POST_H_034_D_EXPECTED_DECISION,
    POST_H_034_E_CREATED_BY,
    POST_H_034_E_EXPECTED_DECISION,
    SensitiveCapabilityOptions,
)

_BLOCKING = {Severity.BLOCK, Severity.ERROR, Severity.FAIL}


def _resolve(root: Path, path: Path | str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _rel(path: Path | str) -> str:
    return str(path).replace("\\", "/")


class ConnectorWriteAdrValidator:
    """POST-H-034-A validator for connector write ADR/no-go invariants.

    The validator reads only source-controlled policy and decision artifacts. It does
    not execute connectors, use network, call external APIs, read credentials or
    mutate the workspace. Its purpose is to prove that connector write remains
    explicitly blocked until a future ADR/backlog introduces stronger controls.
    """

    def __init__(self, root: Path, *, options: SensitiveCapabilityOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SensitiveCapabilityOptions()

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        matrix, matrix_findings = load_decision_matrix(self.root, self.options.matrix_path)
        decision, decision_findings = load_connector_write_decision(self.root, self.options.connector_write_checklist_path)
        findings.extend(matrix_findings)
        findings.extend(decision_findings)

        sandbox_policy = self._read_json(self.options.connector_sandbox_policy_path, "CONNECTOR_SANDBOX_POLICY")
        project_state = self._read_json(self.options.project_state_path, "PROJECT_STATE")
        adr_path = _resolve(self.root, self.options.connector_write_adr_path)
        adr_text = ""
        if not adr_path.exists():
            findings.append(Finding("CONNECTOR_WRITE_ADR_MISSING", "Connector write ADR is missing.", Severity.BLOCK, path=_rel(self.options.connector_write_adr_path)))
        else:
            adr_text = adr_path.read_text(encoding="utf-8")

        if decision is not None:
            findings.extend(self._validate_decision(decision, adr_text))
        if matrix is not None:
            findings.extend(self._validate_matrix(matrix))
        if isinstance(sandbox_policy, dict):
            findings.extend(self._validate_sandbox_policy(sandbox_policy))
        if isinstance(project_state, dict):
            findings.extend(self._validate_project_state(project_state))

        blocking = [finding for finding in findings if finding.severity in _BLOCKING]
        summary = self._summary(decision, matrix, sandbox_policy, project_state, blocking)
        if not blocking:
            findings.append(
                Finding(
                    "CONNECTOR_WRITE_ADR_GATE_PASS",
                    "Connector write ADR gate passed: connector.write remains continue-blocked with runtime write disabled and no claims broadened.",
                    Severity.INFO,
                    metadata={"decision_state": summary["decision_state"], "connector_write_enabled": summary["connector_write_enabled"]},
                )
            )
            summary["findings_total"] = len(findings)
        return CommandResult(
            command="sensitive-capability connector-write-adr validate",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Connector write ADR gate passed." if not blocking else "Connector write ADR gate blocked.",
            data={
                "summary": summary,
                "decision": decision or {},
                "matrix_summary": (matrix or {}).get("summary", {}) if isinstance(matrix, dict) else {},
                "notes": [
                    "POST-H-034-A is an ADR/no-go validation only; it does not enable connector write.",
                    "Any future connector write pilot requires separate backlog, threat model, fake write tests, rollback/compensation and approval/RBAC hardening.",
                ],
            },
            findings=findings,
        )

    def _read_json(self, path: Path | str, label: str) -> dict[str, Any] | None:
        resolved = _resolve(self.root, path)
        if not resolved.exists():
            return None
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def _validate_decision(self, decision: dict[str, Any], adr_text: str) -> list[Finding]:
        findings: list[Finding] = []
        if decision.get("created_by") != POST_H_034_A_CREATED_BY:
            findings.append(Finding("CONNECTOR_WRITE_DECISION_CREATED_BY_BLOCK", "Connector write decision must be owned by POST-H-034-A.", Severity.BLOCK, path=_rel(self.options.connector_write_checklist_path)))
        if decision.get("capability_id") != "connector.write":
            findings.append(Finding("CONNECTOR_WRITE_DECISION_CAPABILITY_BLOCK", "Connector write decision must target capability_id connector.write.", Severity.BLOCK, path=_rel(self.options.connector_write_checklist_path)))
        state = decision.get("decision_state")
        if state not in ALLOWED_CONNECTOR_WRITE_DECISIONS:
            findings.append(Finding("CONNECTOR_WRITE_DECISION_STATE_BLOCK", "Connector write decision_state is not allowed.", Severity.BLOCK, path=_rel(self.options.connector_write_checklist_path), metadata={"decision_state": state}))
        if state != POST_H_034_A_EXPECTED_DECISION:
            findings.append(Finding("CONNECTOR_WRITE_DECISION_NOT_CONTINUE_BLOCKED", "POST-H-034-A must keep connector.write in continue-blocked state for the current repo baseline.", Severity.BLOCK, path=_rel(self.options.connector_write_checklist_path), metadata={"decision_state": state}))
        for key in ("connector_write_enabled", "runtime_write_enabled", "external_api_allowed", "network_allowed", "credentials_required"):
            if decision.get(key) is not False:
                findings.append(Finding("CONNECTOR_WRITE_DECISION_FLAG_BLOCK", f"{key} must remain false.", Severity.BLOCK, path=_rel(self.options.connector_write_checklist_path), metadata={"flag": key, "actual": decision.get(key)}))
        for key in ("requires_future_backlog", "requires_future_enablement_adr", "requires_human_approval", "rollback_required_before_pilot", "kill_switch_required_before_pilot"):
            if decision.get(key) is not True:
                findings.append(Finding("CONNECTOR_WRITE_DECISION_PREREQUISITE_FLAG_BLOCK", f"{key} must be true.", Severity.BLOCK, path=_rel(self.options.connector_write_checklist_path), metadata={"flag": key, "actual": decision.get(key)}))
        safety = decision.get("safety") if isinstance(decision.get("safety"), dict) else {}
        for key in ("network_used", "external_api_used", "connector_write_enabled", "connector_write_used", "remote_execution_enabled", "plugin_execution_enabled", "source_mutations_performed", "secrets_versioned"):
            if safety.get(key) is not False:
                findings.append(Finding("CONNECTOR_WRITE_SAFETY_FLAG_BLOCK", f"safety.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.connector_write_checklist_path), metadata={"flag": key, "actual": safety.get(key)}))
        if "decision_status: \"continue-blocked\"" not in adr_text and "decision_status: 'continue-blocked'" not in adr_text:
            findings.append(Finding("CONNECTOR_WRITE_ADR_STATUS_BLOCK", "Connector write ADR frontmatter must declare decision_status continue-blocked.", Severity.BLOCK, path=_rel(self.options.connector_write_adr_path)))
        forbidden_terms = ["enabled-now", "production-enabled", "connector_write_enabled: true", "runtime_write_enabled: true"]
        lowered = adr_text.lower()
        for term in forbidden_terms:
            if term in lowered:
                findings.append(Finding("CONNECTOR_WRITE_ADR_FORBIDDEN_ENABLEMENT_TERM", "Connector write ADR contains a forbidden runtime enablement term.", Severity.BLOCK, path=_rel(self.options.connector_write_adr_path), metadata={"term": term}))
        return findings

    def _validate_matrix(self, matrix: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        decision = connector_write_decision_from_matrix(matrix)
        if decision is None:
            findings.append(Finding("SENSITIVE_CAPABILITY_MATRIX_CONNECTOR_WRITE_MISSING", "Decision matrix must include connector.write.", Severity.BLOCK, path=_rel(self.options.matrix_path)))
            return findings
        if decision.runtime_enabled is not False:
            findings.append(Finding("SENSITIVE_CAPABILITY_MATRIX_RUNTIME_ENABLEMENT_BLOCK", "connector.write runtime_enabled must remain false in decision matrix.", Severity.BLOCK, path=_rel(self.options.matrix_path)))
        if decision.decision_state != POST_H_034_A_EXPECTED_DECISION:
            findings.append(Finding("SENSITIVE_CAPABILITY_MATRIX_CONNECTOR_WRITE_DECISION_BLOCK", "Decision matrix must keep connector.write continue-blocked in POST-H-034-A.", Severity.BLOCK, path=_rel(self.options.matrix_path), metadata=decision.to_dict()))
        gates = matrix.get("global_no_go_gates") if isinstance(matrix.get("global_no_go_gates"), dict) else {}
        for key in ("connector_write_enabled", "plugin_execution_enabled", "remote_execution_enabled", "production_multiuser", "enterprise_ready", "saas_ready", "compliance_certified"):
            if gates.get(key) is not False:
                findings.append(Finding("SENSITIVE_CAPABILITY_MATRIX_NO_GO_BLOCK", f"global_no_go_gates.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.matrix_path), metadata={"flag": key, "actual": gates.get(key)}))
        return findings

    def _validate_sandbox_policy(self, policy: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        if policy.get("connector_write_enabled") is not False:
            findings.append(Finding("CONNECTOR_WRITE_SANDBOX_POLICY_ENABLEMENT_BLOCK", "Connector sandbox policy must keep connector_write_enabled=false.", Severity.BLOCK, path=_rel(self.options.connector_sandbox_policy_path)))
        for connector in policy.get("connectors", []):
            if isinstance(connector, dict) and connector.get("write_allowed") is not False:
                findings.append(Finding("CONNECTOR_WRITE_SANDBOX_CONNECTOR_WRITE_BLOCK", "Every connector sandbox policy entry must keep write_allowed=false.", Severity.BLOCK, path=_rel(self.options.connector_sandbox_policy_path), metadata={"connector_id": connector.get("connector_id")}))
        return findings

    def _validate_project_state(self, state: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        for key in ("connector_write_enabled", "plugin_execution_enabled", "remote_execution_enabled", "enterprise_ready_claimed", "compliance_certification_claim"):
            if state.get(key) is not False:
                findings.append(Finding("SENSITIVE_CAPABILITY_PROJECT_STATE_NO_GO_BLOCK", f"project_state.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.project_state_path), metadata={"flag": key, "actual": state.get(key)}))
        return findings

    def _summary(self, decision: dict[str, Any] | None, matrix: dict[str, Any] | None, sandbox_policy: dict[str, Any] | None, project_state: dict[str, Any] | None, blocking: list[Finding]) -> dict[str, Any]:
        decision = decision or {}
        safety = decision.get("safety") if isinstance(decision.get("safety"), dict) else {}
        return {
            "created_by": POST_H_034_A_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "capability_id": "connector.write",
            "decision_state": decision.get("decision_state"),
            "decision_status": decision.get("decision_status"),
            "connector_write_enabled": decision.get("connector_write_enabled"),
            "runtime_write_enabled": decision.get("runtime_write_enabled"),
            "network_used": safety.get("network_used", False),
            "external_api_used": safety.get("external_api_used", False),
            "sandbox_policy_connector_write_enabled": sandbox_policy.get("connector_write_enabled") if isinstance(sandbox_policy, dict) else None,
            "project_state_connector_write_enabled": project_state.get("connector_write_enabled") if isinstance(project_state, dict) else None,
            "matrix_loaded": matrix is not None,
            "decision_loaded": bool(decision),
            "blocking_findings_total": len(blocking),
            "findings_total": len(blocking),
            "claims_changed": False,
            "reports_written": False,
        }


class PluginExecutionAdrValidator:
    """POST-H-034-B validator for plugin execution ADR/no-go invariants.

    The validator reads source-controlled plugin policy, registry and decision
    artifacts only. It never imports plugin code, starts subprocesses, opens
    network connections, uses external APIs, reads secrets or mutates the
    workspace. Its purpose is to prove that plugin execution remains explicitly
    blocked until a future ADR/backlog introduces a real sandbox and supply-chain
    controls.
    """

    def __init__(self, root: Path, *, options: SensitiveCapabilityOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SensitiveCapabilityOptions()

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        matrix, matrix_findings = load_decision_matrix(self.root, self.options.matrix_path)
        decision, decision_findings = load_plugin_execution_decision(self.root, self.options.plugin_execution_checklist_path)
        findings.extend(matrix_findings)
        findings.extend(decision_findings)

        plugin_registry = self._read_json(self.options.plugin_registry_path)
        permission_model = self._read_json(self.options.plugin_permission_model_path)
        project_state = self._read_json(self.options.project_state_path)
        adr_path = _resolve(self.root, self.options.plugin_execution_adr_path)
        adr_text = ""
        if not adr_path.exists():
            findings.append(Finding("PLUGIN_EXECUTION_ADR_MISSING", "Plugin execution ADR is missing.", Severity.BLOCK, path=_rel(self.options.plugin_execution_adr_path)))
        else:
            adr_text = adr_path.read_text(encoding="utf-8")

        if decision is not None:
            findings.extend(self._validate_decision(decision, adr_text))
        if matrix is not None:
            findings.extend(self._validate_matrix(matrix))
        if isinstance(plugin_registry, dict):
            findings.extend(self._validate_plugin_registry(plugin_registry))
        else:
            findings.append(Finding("PLUGIN_REGISTRY_MISSING", "Plugin registry is missing or invalid JSON.", Severity.BLOCK, path=_rel(self.options.plugin_registry_path)))
        if isinstance(permission_model, dict):
            findings.extend(self._validate_permission_model(permission_model))
        else:
            findings.append(Finding("PLUGIN_PERMISSION_MODEL_MISSING", "Plugin permission model is missing or invalid JSON.", Severity.BLOCK, path=_rel(self.options.plugin_permission_model_path)))
        if isinstance(project_state, dict):
            findings.extend(self._validate_project_state(project_state))

        blocking = [finding for finding in findings if finding.severity in _BLOCKING]
        summary = self._summary(decision, matrix, plugin_registry, permission_model, project_state, blocking)
        if not blocking:
            findings.append(
                Finding(
                    "PLUGIN_EXECUTION_ADR_GATE_PASS",
                    "Plugin execution ADR gate passed: plugin.execution remains continue-blocked with plugin code loading and runtime execution disabled.",
                    Severity.INFO,
                    metadata={"decision_state": summary["plugin_decision_state"], "plugin_execution_enabled": summary["plugin_execution_enabled"]},
                )
            )
            summary["findings_total"] = len(findings)
        return CommandResult(
            command="sensitive-capability plugin-execution-adr validate",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Plugin execution ADR gate passed." if not blocking else "Plugin execution ADR gate blocked.",
            data={
                "summary": summary,
                "decision": decision or {},
                "matrix_summary": (matrix or {}).get("summary", {}) if isinstance(matrix, dict) else {},
                "notes": [
                    "POST-H-034-B is an ADR/no-go validation only; it does not execute, import or load plugin code.",
                    "Any future plugin execution pilot requires separate backlog, threat model, signing, runtime sandbox, resource limits, Approval/RBAC and malicious fake plugin tests.",
                ],
            },
            findings=findings,
        )

    def _read_json(self, path: Path | str) -> dict[str, Any] | None:
        resolved = _resolve(self.root, path)
        if not resolved.exists():
            return None
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def _validate_decision(self, decision: dict[str, Any], adr_text: str) -> list[Finding]:
        findings: list[Finding] = []
        if decision.get("created_by") != POST_H_034_B_CREATED_BY:
            findings.append(Finding("PLUGIN_EXECUTION_DECISION_CREATED_BY_BLOCK", "Plugin execution decision must be owned by POST-H-034-B.", Severity.BLOCK, path=_rel(self.options.plugin_execution_checklist_path)))
        if decision.get("capability_id") != "plugin.execution":
            findings.append(Finding("PLUGIN_EXECUTION_DECISION_CAPABILITY_BLOCK", "Plugin execution decision must target capability_id plugin.execution.", Severity.BLOCK, path=_rel(self.options.plugin_execution_checklist_path)))
        state = decision.get("decision_state")
        if state not in ALLOWED_PLUGIN_EXECUTION_DECISIONS:
            findings.append(Finding("PLUGIN_EXECUTION_DECISION_STATE_BLOCK", "Plugin execution decision_state is not allowed.", Severity.BLOCK, path=_rel(self.options.plugin_execution_checklist_path), metadata={"decision_state": state}))
        if state != POST_H_034_B_EXPECTED_DECISION:
            findings.append(Finding("PLUGIN_EXECUTION_DECISION_NOT_CONTINUE_BLOCKED", "POST-H-034-B must keep plugin.execution in continue-blocked state for the current repo baseline.", Severity.BLOCK, path=_rel(self.options.plugin_execution_checklist_path), metadata={"decision_state": state}))
        for key in ("plugin_execution_enabled", "runtime_execution_enabled", "plugin_code_loading_enabled", "dynamic_import_allowed", "subprocess_allowed", "external_api_allowed", "network_allowed", "filesystem_write_allowed", "shell_allowed", "credentials_required"):
            if decision.get(key) is not False:
                findings.append(Finding("PLUGIN_EXECUTION_DECISION_FLAG_BLOCK", f"{key} must remain false.", Severity.BLOCK, path=_rel(self.options.plugin_execution_checklist_path), metadata={"flag": key, "actual": decision.get(key)}))
        for key in ("requires_future_backlog", "requires_future_enablement_adr", "requires_human_approval", "sandbox_required_before_pilot", "kill_switch_required_before_pilot", "signing_required_before_pilot", "supply_chain_policy_required_before_pilot"):
            if decision.get(key) is not True:
                findings.append(Finding("PLUGIN_EXECUTION_DECISION_PREREQUISITE_FLAG_BLOCK", f"{key} must be true.", Severity.BLOCK, path=_rel(self.options.plugin_execution_checklist_path), metadata={"flag": key, "actual": decision.get(key)}))
        safety = decision.get("safety") if isinstance(decision.get("safety"), dict) else {}
        for key in ("network_used", "external_api_used", "plugin_execution_enabled", "plugin_code_loaded", "dynamic_import_used", "subprocess_used", "shell_used", "filesystem_write_used", "secrets_versioned", "source_mutations_performed"):
            if safety.get(key) is not False:
                findings.append(Finding("PLUGIN_EXECUTION_SAFETY_FLAG_BLOCK", f"safety.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.plugin_execution_checklist_path), metadata={"flag": key, "actual": safety.get(key)}))
        if "decision_status: \"continue-blocked\"" not in adr_text and "decision_status: 'continue-blocked'" not in adr_text:
            findings.append(Finding("PLUGIN_EXECUTION_ADR_STATUS_BLOCK", "Plugin execution ADR frontmatter must declare decision_status continue-blocked.", Severity.BLOCK, path=_rel(self.options.plugin_execution_adr_path)))
        lowered = adr_text.lower()
        forbidden_terms = ["enabled-now", "production-enabled", "plugin_execution_enabled: true", "runtime_execution_enabled: true", "dynamic_import_allowed: true", "subprocess_allowed: true"]
        for term in forbidden_terms:
            if term in lowered:
                findings.append(Finding("PLUGIN_EXECUTION_ADR_FORBIDDEN_ENABLEMENT_TERM", "Plugin execution ADR contains a forbidden runtime enablement term.", Severity.BLOCK, path=_rel(self.options.plugin_execution_adr_path), metadata={"term": term}))
        return findings

    def _validate_matrix(self, matrix: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        plugin_decision = plugin_execution_decision_from_matrix(matrix)
        if plugin_decision is None:
            findings.append(Finding("SENSITIVE_CAPABILITY_MATRIX_PLUGIN_EXECUTION_MISSING", "Decision matrix must include plugin.execution.", Severity.BLOCK, path=_rel(self.options.matrix_path)))
        else:
            if plugin_decision.runtime_enabled is not False:
                findings.append(Finding("SENSITIVE_CAPABILITY_MATRIX_PLUGIN_RUNTIME_ENABLEMENT_BLOCK", "plugin.execution runtime_enabled must remain false in decision matrix.", Severity.BLOCK, path=_rel(self.options.matrix_path)))
            if plugin_decision.decision_state != POST_H_034_B_EXPECTED_DECISION:
                findings.append(Finding("SENSITIVE_CAPABILITY_MATRIX_PLUGIN_EXECUTION_DECISION_BLOCK", "Decision matrix must keep plugin.execution continue-blocked in POST-H-034-B.", Severity.BLOCK, path=_rel(self.options.matrix_path), metadata=plugin_decision.to_dict()))
        connector_decision = connector_write_decision_from_matrix(matrix)
        if connector_decision is None or connector_decision.decision_state != POST_H_034_A_EXPECTED_DECISION or connector_decision.runtime_enabled is not False:
            findings.append(Finding("SENSITIVE_CAPABILITY_MATRIX_CONNECTOR_WRITE_REGRESSION_BLOCK", "POST-H-034-B must preserve connector.write continue-blocked and runtime_enabled=false.", Severity.BLOCK, path=_rel(self.options.matrix_path)))
        gates = matrix.get("global_no_go_gates") if isinstance(matrix.get("global_no_go_gates"), dict) else {}
        for key in ("connector_write_enabled", "plugin_execution_enabled", "remote_execution_enabled", "production_multiuser", "enterprise_ready", "saas_ready", "compliance_certified"):
            if gates.get(key) is not False:
                findings.append(Finding("SENSITIVE_CAPABILITY_MATRIX_NO_GO_BLOCK", f"global_no_go_gates.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.matrix_path), metadata={"flag": key, "actual": gates.get(key)}))
        return findings

    def _validate_plugin_registry(self, registry: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        defaults = registry.get("defaults") if isinstance(registry.get("defaults"), dict) else {}
        security = registry.get("security") if isinstance(registry.get("security"), dict) else {}
        default_checks = {
            "executable_loading_default": False,
            "deny_unregistered_plugins": True,
            "permission_model_required": True,
            "critical_permissions_require_future_adr": True,
        }
        for key, expected in default_checks.items():
            if defaults.get(key) is not expected:
                findings.append(Finding("PLUGIN_REGISTRY_DEFAULT_BLOCK", f"defaults.{key} must be {expected!r}.", Severity.BLOCK, path=_rel(self.options.plugin_registry_path), metadata={"flag": key, "actual": defaults.get(key)}))
        for key in ("plugin_code_loaded", "arbitrary_code_execution_performed", "network_used", "external_api_used", "shell_used", "remote_execution_used", "secrets_allowed", "dynamic_import_allowed", "subprocess_allowed", "filesystem_write_allowed", "pip_install_allowed", "marketplace_enabled"):
            if security.get(key) is not False:
                findings.append(Finding("PLUGIN_REGISTRY_SECURITY_FLAG_BLOCK", f"security.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.plugin_registry_path), metadata={"flag": key, "actual": security.get(key)}))
        for plugin in registry.get("plugins", []):
            if not isinstance(plugin, dict):
                continue
            plugin_id = plugin.get("plugin_id")
            if plugin.get("loading_mode") != "metadata-only":
                findings.append(Finding("PLUGIN_REGISTRY_LOADING_MODE_BLOCK", "Every plugin must remain metadata-only.", Severity.BLOCK, path=_rel(self.options.plugin_registry_path), metadata={"plugin_id": plugin_id, "loading_mode": plugin.get("loading_mode")}))
            if plugin.get("execution_enabled") is not False:
                findings.append(Finding("PLUGIN_REGISTRY_EXECUTION_BLOCK", "Every plugin must keep execution_enabled=false.", Severity.BLOCK, path=_rel(self.options.plugin_registry_path), metadata={"plugin_id": plugin_id}))
            if not str(plugin.get("entrypoint", "")).startswith("disabled://"):
                findings.append(Finding("PLUGIN_REGISTRY_ENTRYPOINT_BLOCK", "Every plugin entrypoint must remain disabled:// in POST-H-034-B.", Severity.BLOCK, path=_rel(self.options.plugin_registry_path), metadata={"plugin_id": plugin_id, "entrypoint": plugin.get("entrypoint")}))
            for key in ("network_allowed", "external_api_allowed", "shell_allowed", "remote_execution_allowed"):
                if plugin.get(key) is not False:
                    findings.append(Finding("PLUGIN_REGISTRY_PLUGIN_FLAG_BLOCK", f"plugin.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.plugin_registry_path), metadata={"plugin_id": plugin_id, "flag": key, "actual": plugin.get(key)}))
        return findings

    def _validate_permission_model(self, model: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        for key in ("plugin_execution_allowed", "dynamic_import_allowed", "subprocess_allowed", "network_allowed", "external_api_allowed", "filesystem_write_allowed", "shell_allowed", "remote_execution_allowed", "pip_install_allowed", "marketplace_enabled"):
            if model.get(key) is not False:
                findings.append(Finding("PLUGIN_PERMISSION_MODEL_FLAG_BLOCK", f"{key} must remain false.", Severity.BLOCK, path=_rel(self.options.plugin_permission_model_path), metadata={"flag": key, "actual": model.get(key)}))
        if model.get("default_effect") != "deny" or model.get("unknown_permissions_effect") != "deny":
            findings.append(Finding("PLUGIN_PERMISSION_MODEL_DEFAULT_DENY_BLOCK", "Plugin permission model must remain deny-by-default and deny unknown permissions.", Severity.BLOCK, path=_rel(self.options.plugin_permission_model_path)))
        denied_ids = {"plugin.code.execute", "plugin.dynamic_import", "plugin.subprocess.run", "plugin.network.access", "plugin.filesystem.write", "plugin.dependency.install"}
        seen: set[str] = set()
        for permission in model.get("permissions", []):
            if not isinstance(permission, dict):
                continue
            pid = str(permission.get("permission_id", ""))
            if pid in denied_ids:
                seen.add(pid)
                if permission.get("effect") != "deny":
                    findings.append(Finding("PLUGIN_PERMISSION_MODEL_CRITICAL_PERMISSION_BLOCK", "Critical plugin execution permissions must be denied.", Severity.BLOCK, path=_rel(self.options.plugin_permission_model_path), metadata={"permission_id": pid, "effect": permission.get("effect")}))
                if permission.get("blocked_until") != "future-adr":
                    findings.append(Finding("PLUGIN_PERMISSION_MODEL_FUTURE_ADR_BLOCK", "Critical plugin execution permissions must be blocked until a future ADR.", Severity.BLOCK, path=_rel(self.options.plugin_permission_model_path), metadata={"permission_id": pid}))
        missing = denied_ids - seen
        if missing:
            findings.append(Finding("PLUGIN_PERMISSION_MODEL_CRITICAL_PERMISSION_MISSING", "Permission model must explicitly deny critical plugin execution permissions.", Severity.BLOCK, path=_rel(self.options.plugin_permission_model_path), metadata={"missing": sorted(missing)}))
        return findings

    def _validate_project_state(self, state: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        for key in ("connector_write_enabled", "plugin_execution_enabled", "remote_execution_enabled", "enterprise_ready_claimed", "compliance_certification_claim"):
            if state.get(key) is not False:
                findings.append(Finding("SENSITIVE_CAPABILITY_PROJECT_STATE_NO_GO_BLOCK", f"project_state.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.project_state_path), metadata={"flag": key, "actual": state.get(key)}))
        return findings

    def _summary(self, decision: dict[str, Any] | None, matrix: dict[str, Any] | None, plugin_registry: dict[str, Any] | None, permission_model: dict[str, Any] | None, project_state: dict[str, Any] | None, blocking: list[Finding]) -> dict[str, Any]:
        decision = decision or {}
        safety = decision.get("safety") if isinstance(decision.get("safety"), dict) else {}
        security = plugin_registry.get("security") if isinstance(plugin_registry, dict) and isinstance(plugin_registry.get("security"), dict) else {}
        return {
            "created_by": POST_H_034_B_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "capability_id": "plugin.execution",
            "plugin_decision_state": decision.get("decision_state"),
            "plugin_decision_status": decision.get("decision_status"),
            "plugin_execution_enabled": decision.get("plugin_execution_enabled"),
            "runtime_execution_enabled": decision.get("runtime_execution_enabled"),
            "plugin_code_loading_enabled": decision.get("plugin_code_loading_enabled"),
            "dynamic_import_allowed": decision.get("dynamic_import_allowed"),
            "subprocess_allowed": decision.get("subprocess_allowed"),
            "network_used": safety.get("network_used", False),
            "external_api_used": safety.get("external_api_used", False),
            "registry_plugin_code_loaded": security.get("plugin_code_loaded") if security else None,
            "permission_model_plugin_execution_allowed": permission_model.get("plugin_execution_allowed") if isinstance(permission_model, dict) else None,
            "project_state_plugin_execution_enabled": project_state.get("plugin_execution_enabled") if isinstance(project_state, dict) else None,
            "matrix_loaded": matrix is not None,
            "decision_loaded": bool(decision),
            "blocking_findings_total": len(blocking),
            "findings_total": len(blocking),
            "claims_changed": False,
            "reports_written": False,
        }


class RemoteExecutionAdr3Validator:
    """POST-H-034-C validator for remote execution ADR-3/no-go invariants.

    The validator reads only source-controlled decision, remote runner and secure
    transport design artifacts. It does not execute remote commands, open network
    connections, read credentials, call external APIs, start workers or mutate the
    workspace. Its purpose is to prove that remote execution remains explicitly
    blocked until a future backlog introduces a complete secure transport/runtime
    architecture.
    """

    def __init__(self, root: Path, *, options: SensitiveCapabilityOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SensitiveCapabilityOptions()

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        matrix, matrix_findings = load_decision_matrix(self.root, self.options.matrix_path)
        decision, decision_findings = load_remote_execution_adr3_decision(self.root, self.options.remote_execution_adr3_checklist_path)
        findings.extend(matrix_findings)
        findings.extend(decision_findings)

        remote_registry = self._read_json(self.options.remote_runner_registry_path, "REMOTE_RUNNER_REGISTRY")
        readiness = self._read_json(self.options.remote_readiness_criteria_path, "REMOTE_READINESS_CRITERIA")
        transport = self._read_json(self.options.secure_transport_decision_matrix_path, "SECURE_TRANSPORT_DECISION_MATRIX")
        project_state = self._read_json(self.options.project_state_path, "PROJECT_STATE")
        adr_path = _resolve(self.root, self.options.remote_execution_adr3_adr_path)
        adr_text = ""
        if not adr_path.exists():
            findings.append(Finding("REMOTE_EXECUTION_ADR3_MISSING", "Remote execution ADR-3 is missing.", Severity.BLOCK, path=_rel(self.options.remote_execution_adr3_adr_path)))
        else:
            adr_text = adr_path.read_text(encoding="utf-8")
            if 'status: "approved"' not in adr_text:
                findings.append(Finding("REMOTE_EXECUTION_ADR3_NOT_APPROVED", "Remote execution ADR-3 must be approved.", Severity.BLOCK, path=_rel(self.options.remote_execution_adr3_adr_path)))
            if 'decision_status: "continue-blocked"' not in adr_text:
                findings.append(Finding("REMOTE_EXECUTION_ADR3_NOT_CONTINUE_BLOCKED", "Remote execution ADR-3 must declare continue-blocked.", Severity.BLOCK, path=_rel(self.options.remote_execution_adr3_adr_path)))

        if decision:
            findings.extend(self._validate_decision(decision, adr_text))
        if matrix:
            findings.extend(self._validate_matrix(matrix))
        if remote_registry:
            findings.extend(self._validate_remote_registry(remote_registry))
        if readiness:
            findings.extend(self._validate_readiness(readiness))
        if transport:
            findings.extend(self._validate_transport(transport))
        if project_state:
            findings.extend(self._validate_project_state(project_state))

        blocking = [finding for finding in findings if finding.severity in _BLOCKING]
        if not blocking:
            findings.append(Finding("REMOTE_EXECUTION_ADR3_GATE_PASS", "Remote execution ADR-3 remains continue-blocked; remote runner, transport, shell, network, external API and credentials are disabled.", Severity.INFO))
        return CommandResult(
            command="sensitive-capability remote-execution-adr3 validate",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Remote execution ADR-3 gate passed." if not blocking else "Remote execution ADR-3 gate blocked.",
            data={
                "summary": self._summary(decision, matrix, remote_registry, readiness, transport, project_state, blocking),
                "notes": [
                    "POST-H-034-C validates ADR/no-go decisions only.",
                    "The validator does not enable remote runner, transport, network, shell, external APIs or credentials.",
                ],
            },
            findings=findings,
        )

    def _read_json(self, path: Path | str, label: str) -> dict[str, Any] | None:
        resolved = _resolve(self.root, path)
        if not resolved.exists():
            return None
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def _validate_decision(self, decision: dict[str, Any], adr_text: str) -> list[Finding]:
        findings: list[Finding] = []
        if decision.get("created_by") != POST_H_034_C_CREATED_BY:
            findings.append(Finding("REMOTE_EXECUTION_ADR3_WRONG_OWNER", "Remote execution ADR-3 decision must be created by POST-H-034-C.", Severity.BLOCK, metadata={"actual": decision.get("created_by")}))
        if decision.get("decision_state") not in ALLOWED_REMOTE_EXECUTION_ADR3_DECISIONS:
            findings.append(Finding("REMOTE_EXECUTION_ADR3_UNKNOWN_DECISION", "Remote execution ADR-3 decision_state is not allowed.", Severity.BLOCK, metadata={"actual": decision.get("decision_state")}))
        if decision.get("decision_state") != POST_H_034_C_EXPECTED_DECISION:
            findings.append(Finding("REMOTE_EXECUTION_ADR3_NOT_CONTINUE_BLOCKED", "Remote execution ADR-3 must remain continue-blocked in POST-H-034-C.", Severity.BLOCK, metadata={"actual": decision.get("decision_state")}))
        for key in (
            "remote_execution_enabled",
            "remote_runner_enabled",
            "runtime_execution_enabled",
            "remote_transport_enabled",
            "secure_transport_implemented",
            "transport_implemented",
            "shell_allowed",
            "arbitrary_command_execution_allowed",
            "network_allowed",
            "external_api_allowed",
            "credentials_required",
        ):
            if decision.get(key) is not False:
                findings.append(Finding("REMOTE_EXECUTION_ADR3_DECISION_FLAG_BLOCK", f"{key} must remain false.", Severity.BLOCK, metadata={"flag": key, "actual": decision.get(key)}))
        for key in ("requires_future_backlog", "requires_future_enablement_adr", "requires_human_approval", "remote_sandbox_required_before_pilot", "kill_switch_required_before_pilot"):
            if decision.get(key) is not True:
                findings.append(Finding("REMOTE_EXECUTION_ADR3_REQUIRED_CONTROL_BLOCK", f"{key} must remain true.", Severity.BLOCK, metadata={"flag": key, "actual": decision.get(key)}))
        if "remote runner registry exists != remote execution enabled" not in adr_text.lower():
            findings.append(Finding("REMOTE_EXECUTION_ADR3_MISSING_INTERPRETATION_RULE", "ADR must separate remote runner registry from remote execution enablement.", Severity.BLOCK))
        return findings

    def _validate_matrix(self, matrix: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        remote = remote_execution_decision_from_matrix(matrix)
        if remote is None:
            findings.append(Finding("REMOTE_EXECUTION_MATRIX_ENTRY_MISSING", "Sensitive capability matrix must include remote.execution.", Severity.BLOCK, path=_rel(self.options.matrix_path)))
            return findings
        if remote.decision_state != POST_H_034_C_EXPECTED_DECISION:
            findings.append(Finding("REMOTE_EXECUTION_MATRIX_DECISION_BLOCK", "Matrix remote.execution decision must remain continue-blocked.", Severity.BLOCK, path=_rel(self.options.matrix_path), metadata=remote.to_dict()))
        if remote.runtime_enabled is not False:
            findings.append(Finding("REMOTE_EXECUTION_MATRIX_RUNTIME_BLOCK", "Matrix remote.execution runtime_enabled must remain false.", Severity.BLOCK, path=_rel(self.options.matrix_path), metadata=remote.to_dict()))
        gates = matrix.get("global_no_go_gates", {}) if isinstance(matrix.get("global_no_go_gates"), dict) else {}
        if gates.get("remote_execution_enabled") is not False:
            findings.append(Finding("REMOTE_EXECUTION_MATRIX_NO_GO_BLOCK", "global_no_go_gates.remote_execution_enabled must remain false.", Severity.BLOCK, path=_rel(self.options.matrix_path), metadata={"actual": gates.get("remote_execution_enabled")}))
        return findings

    def _validate_remote_registry(self, registry: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        security = registry.get("security") if isinstance(registry.get("security"), dict) else {}
        for key in ("remote_runner_enabled", "execution_allowed", "remote_execution_used", "cloud_control_plane_enabled", "network_used", "external_api_used", "shell_allowed", "arbitrary_command_execution_allowed", "credentials_required", "secrets_read", "source_mutations_performed", "mutations_performed"):
            if security.get(key) is not False:
                findings.append(Finding("REMOTE_RUNNER_REGISTRY_FLAG_BLOCK", f"Remote runner registry security.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.remote_runner_registry_path), metadata={"flag": key, "actual": security.get(key)}))
        for runner in registry.get("runners", []):
            if not isinstance(runner, dict):
                continue
            if runner.get("status") != "disabled" or runner.get("execution_allowed") is not False or runner.get("network_allowed") is not False or runner.get("requires_credentials") is not False:
                findings.append(Finding("REMOTE_RUNNER_PROFILE_ENABLEMENT_BLOCK", "All remote runner profiles must remain disabled and non-executable.", Severity.BLOCK, path=_rel(self.options.remote_runner_registry_path), metadata={"runner_id": runner.get("runner_id")}))
        return findings

    def _validate_readiness(self, readiness: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        if readiness.get("decision_status") != "design-only":
            findings.append(Finding("REMOTE_READINESS_STATUS_BLOCK", "Remote readiness criteria must remain design-only.", Severity.BLOCK, path=_rel(self.options.remote_readiness_criteria_path), metadata={"actual": readiness.get("decision_status")}))
        if readiness.get("remote_execution_allowed") is not False or readiness.get("remote_runner_enabled") is not False:
            findings.append(Finding("REMOTE_READINESS_ENABLEMENT_BLOCK", "Remote readiness criteria must not allow remote execution or runner enablement.", Severity.BLOCK, path=_rel(self.options.remote_readiness_criteria_path)))
        no_go = readiness.get("no_go_gates") if isinstance(readiness.get("no_go_gates"), dict) else {}
        for key in ("remote_runner_enabled", "remote_execution_used", "network_required", "external_api_required", "credentials_required", "secrets_required", "mutations_performed", "source_mutations_performed"):
            if no_go.get(key) is not False:
                findings.append(Finding("REMOTE_READINESS_NO_GO_BLOCK", f"Remote readiness no_go_gates.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.remote_readiness_criteria_path), metadata={"flag": key, "actual": no_go.get(key)}))
        return findings

    def _validate_transport(self, transport: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        expected = {
            "decision_status": "design-only",
            "selected_for_now": "local-only-no-transport",
            "transport_implemented": False,
            "network_allowed": False,
            "remote_execution_enabled": False,
            "secrets_required": False,
            "requires_future_enablement_adr": True,
        }
        for key, value in expected.items():
            if transport.get(key) != value:
                findings.append(Finding("SECURE_TRANSPORT_REMOTE_ADR3_BLOCK", f"Secure transport decision matrix {key} must remain {value!r}.", Severity.BLOCK, path=_rel(self.options.secure_transport_decision_matrix_path), metadata={"flag": key, "actual": transport.get(key)}))
        return findings

    def _validate_project_state(self, state: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        for key in ("remote_execution_enabled", "remote_runner_enabled", "network_allowed", "network_used", "external_api_used", "credentials_required", "connector_write_enabled", "plugin_execution_enabled", "enterprise_ready_claimed", "compliance_certification_claim"):
            if state.get(key) is not False:
                findings.append(Finding("REMOTE_EXECUTION_PROJECT_STATE_NO_GO_BLOCK", f"project_state.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.project_state_path), metadata={"flag": key, "actual": state.get(key)}))
        return findings

    def _summary(self, decision: dict[str, Any] | None, matrix: dict[str, Any] | None, remote_registry: dict[str, Any] | None, readiness: dict[str, Any] | None, transport: dict[str, Any] | None, project_state: dict[str, Any] | None, blocking: list[Finding]) -> dict[str, Any]:
        decision = decision or {}
        security = remote_registry.get("security") if isinstance(remote_registry, dict) and isinstance(remote_registry.get("security"), dict) else {}
        return {
            "created_by": POST_H_034_C_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "capability_id": "remote.execution",
            "remote_decision_state": decision.get("decision_state"),
            "remote_decision_status": decision.get("decision_status"),
            "remote_execution_enabled": decision.get("remote_execution_enabled"),
            "remote_runner_enabled": decision.get("remote_runner_enabled"),
            "runtime_execution_enabled": decision.get("runtime_execution_enabled"),
            "remote_transport_enabled": decision.get("remote_transport_enabled"),
            "secure_transport_implemented": decision.get("secure_transport_implemented"),
            "transport_implemented": decision.get("transport_implemented"),
            "shell_allowed": decision.get("shell_allowed"),
            "network_allowed": decision.get("network_allowed"),
            "external_api_allowed": decision.get("external_api_allowed"),
            "credentials_required": decision.get("credentials_required"),
            "registry_remote_runner_enabled": security.get("remote_runner_enabled") if security else None,
            "registry_execution_allowed": security.get("execution_allowed") if security else None,
            "readiness_decision_status": readiness.get("decision_status") if isinstance(readiness, dict) else None,
            "transport_decision_status": transport.get("decision_status") if isinstance(transport, dict) else None,
            "project_state_remote_execution_enabled": project_state.get("remote_execution_enabled") if isinstance(project_state, dict) else None,
            "matrix_loaded": matrix is not None,
            "decision_loaded": bool(decision),
            "blocking_findings_total": len(blocking),
            "findings_total": len(blocking),
            "claims_changed": False,
            "reports_written": False,
        }


class MultiuserAuthAdrValidator:
    """POST-H-034-D validator for multiuser/auth boundary invariants.

    The validator reads local source-controlled decision, identity and project
    metadata only. It does not authenticate users, create sessions, read real
    credentials, open network connections, call external identity providers,
    start servers or mutate the workspace.
    """

    def __init__(self, root: Path, *, options: SensitiveCapabilityOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SensitiveCapabilityOptions()

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        matrix, matrix_findings = load_decision_matrix(self.root, self.options.matrix_path)
        decision, decision_findings = load_multiuser_auth_decision(self.root, self.options.multiuser_auth_checklist_path)
        findings.extend(matrix_findings)
        findings.extend(decision_findings)

        identity_registry = self._read_json(Path(".devpilot/identity/identity_registry.json"))
        project_state = self._read_json(self.options.project_state_path)
        api_security_report = _resolve(self.root, Path("docs/audits/post_h_028_b_local_auth_cors_hardening_report.md"))
        adr_path = _resolve(self.root, self.options.multiuser_auth_adr_path)
        adr_text = ""
        if not adr_path.exists():
            findings.append(Finding("MULTIUSER_AUTH_ADR_MISSING", "Multiuser/auth ADR is missing.", Severity.BLOCK, path=_rel(self.options.multiuser_auth_adr_path)))
        else:
            adr_text = adr_path.read_text(encoding="utf-8")
            if 'status: "approved"' not in adr_text:
                findings.append(Finding("MULTIUSER_AUTH_ADR_NOT_APPROVED", "Multiuser/auth ADR must be approved.", Severity.BLOCK, path=_rel(self.options.multiuser_auth_adr_path)))
            if 'decision_status: "continue-blocked"' not in adr_text:
                findings.append(Finding("MULTIUSER_AUTH_ADR_NOT_CONTINUE_BLOCKED", "Multiuser/auth ADR must declare continue-blocked.", Severity.BLOCK, path=_rel(self.options.multiuser_auth_adr_path)))
        api_text = api_security_report.read_text(encoding="utf-8") if api_security_report.exists() else ""

        if decision:
            findings.extend(self._validate_decision(decision, adr_text))
        if matrix:
            findings.extend(self._validate_matrix(matrix))
        if identity_registry:
            findings.extend(self._validate_identity_registry(identity_registry))
        else:
            findings.append(Finding("MULTIUSER_AUTH_IDENTITY_REGISTRY_MISSING", "Identity registry must remain available as local preliminary RBAC source.", Severity.BLOCK, path=".devpilot/identity/identity_registry.json"))
        findings.extend(self._validate_api_security_report(api_text))
        if project_state:
            findings.extend(self._validate_project_state(project_state))

        blocking = [finding for finding in findings if finding.severity in _BLOCKING]
        if not blocking:
            findings.append(Finding("MULTIUSER_AUTH_ADR_GATE_PASS", "Multiuser/auth ADR gate passed: production multiuser, enterprise IAM, sessions, tenancy, public API, network, external APIs and credentials remain disabled.", Severity.INFO))
        return CommandResult(
            command="sensitive-capability multiuser-auth validate",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Multiuser/auth ADR gate passed." if not blocking else "Multiuser/auth ADR gate blocked.",
            data={
                "summary": self._summary(decision, matrix, identity_registry, project_state, blocking),
                "notes": [
                    "POST-H-034-D validates ADR/no-go decisions only.",
                    "The validator does not enable multiuser auth, sessions, IAM, tenancy, public API, network, external APIs or credentials.",
                ],
            },
            findings=findings,
        )

    def _read_json(self, path: Path | str) -> dict[str, Any] | None:
        resolved = _resolve(self.root, path)
        if not resolved.exists():
            return None
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def _validate_decision(self, decision: dict[str, Any], adr_text: str) -> list[Finding]:
        findings: list[Finding] = []
        if decision.get("created_by") != POST_H_034_D_CREATED_BY:
            findings.append(Finding("MULTIUSER_AUTH_WRONG_OWNER", "Multiuser/auth decision must be created by POST-H-034-D.", Severity.BLOCK, metadata={"actual": decision.get("created_by")}))
        if decision.get("decision_state") not in ALLOWED_MULTIUSER_AUTH_DECISIONS:
            findings.append(Finding("MULTIUSER_AUTH_UNKNOWN_DECISION", "Multiuser/auth decision_state is not allowed.", Severity.BLOCK, metadata={"actual": decision.get("decision_state")}))
        if decision.get("decision_state") != POST_H_034_D_EXPECTED_DECISION:
            findings.append(Finding("MULTIUSER_AUTH_NOT_CONTINUE_BLOCKED", "Multiuser/auth must remain continue-blocked in POST-H-034-D.", Severity.BLOCK, metadata={"actual": decision.get("decision_state")}))
        for key in (
            "multiuser_auth_enabled", "production_multiuser_enabled", "multiuser_runtime_enabled", "iam_enterprise_enabled", "oidc_enabled", "sso_enabled", "session_management_enabled", "tenancy_enabled", "tenant_isolation_implemented", "public_api_enabled", "network_allowed", "external_api_allowed", "credentials_required", "password_storage_enabled",
        ):
            if decision.get(key) is not False:
                findings.append(Finding("MULTIUSER_AUTH_DECISION_FLAG_BLOCK", f"{key} must remain false.", Severity.BLOCK, path=_rel(self.options.multiuser_auth_checklist_path), metadata={"flag": key, "actual": decision.get(key)}))
        for key in ("local_api_token_control", "local_rbac_initial", "local_approval_binding_initial", "requires_future_backlog", "requires_future_enablement_adr", "requires_human_approval", "auth_threat_model_required_before_pilot", "session_management_required_before_pilot", "tenant_isolation_required_before_pilot", "approval_actor_binding_required_before_pilot"):
            if decision.get(key) is not True:
                findings.append(Finding("MULTIUSER_AUTH_REQUIRED_CONTROL_BLOCK", f"{key} must remain true.", Severity.BLOCK, path=_rel(self.options.multiuser_auth_checklist_path), metadata={"flag": key, "actual": decision.get(key)}))
        lowered = adr_text.lower()
        required_rules = [
            "local api token exists != production multiuser enabled",
            "identity registry exists != real user identity provider",
            "auth/rbac initial exists != enterprise iam",
            "post-h-034-d adr exists != runtime enablement",
        ]
        for rule in required_rules:
            if rule not in lowered:
                findings.append(Finding("MULTIUSER_AUTH_ADR_MISSING_INTERPRETATION_RULE", "ADR must separate local auth/RBAC from production multiuser enablement.", Severity.BLOCK, path=_rel(self.options.multiuser_auth_adr_path), metadata={"rule": rule}))
        return findings

    def _validate_matrix(self, matrix: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        decision = multiuser_auth_decision_from_matrix(matrix)
        if decision is None:
            findings.append(Finding("MULTIUSER_AUTH_MATRIX_ENTRY_MISSING", "Sensitive capability matrix must include multiuser.auth.", Severity.BLOCK, path=_rel(self.options.matrix_path)))
            return findings
        if decision.decision_state != POST_H_034_D_EXPECTED_DECISION:
            findings.append(Finding("MULTIUSER_AUTH_MATRIX_DECISION_BLOCK", "Matrix multiuser.auth decision must remain continue-blocked.", Severity.BLOCK, path=_rel(self.options.matrix_path), metadata=decision.to_dict()))
        if decision.runtime_enabled is not False:
            findings.append(Finding("MULTIUSER_AUTH_MATRIX_RUNTIME_BLOCK", "Matrix multiuser.auth runtime_enabled must remain false.", Severity.BLOCK, path=_rel(self.options.matrix_path), metadata=decision.to_dict()))
        gates = matrix.get("global_no_go_gates", {}) if isinstance(matrix.get("global_no_go_gates"), dict) else {}
        if gates.get("production_multiuser") is not False:
            findings.append(Finding("MULTIUSER_AUTH_MATRIX_NO_GO_BLOCK", "global_no_go_gates.production_multiuser must remain false.", Severity.BLOCK, path=_rel(self.options.matrix_path), metadata={"actual": gates.get("production_multiuser")}))
        return findings

    def _validate_identity_registry(self, registry: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        defaults = registry.get("defaults") if isinstance(registry.get("defaults"), dict) else {}
        security = registry.get("security") if isinstance(registry.get("security"), dict) else {}
        if defaults.get("auth_remote_enabled") is not False:
            findings.append(Finding("MULTIUSER_AUTH_IDENTITY_REMOTE_AUTH_BLOCK", "identity.defaults.auth_remote_enabled must remain false.", Severity.BLOCK, path=".devpilot/identity/identity_registry.json"))
        if defaults.get("credentials_stored") is not False:
            findings.append(Finding("MULTIUSER_AUTH_IDENTITY_CREDENTIALS_BLOCK", "identity.defaults.credentials_stored must remain false.", Severity.BLOCK, path=".devpilot/identity/identity_registry.json"))
        if defaults.get("deny_unknown_actor") is not True:
            findings.append(Finding("MULTIUSER_AUTH_IDENTITY_UNKNOWN_ACTOR_BLOCK", "identity.defaults.deny_unknown_actor must remain true.", Severity.BLOCK, path=".devpilot/identity/identity_registry.json"))
        for key in ("network_used", "external_api_used", "remote_auth_used", "credentials_read", "credentials_stored"):
            if security.get(key) is not False:
                findings.append(Finding("MULTIUSER_AUTH_IDENTITY_SECURITY_FLAG_BLOCK", f"identity.security.{key} must remain false.", Severity.BLOCK, path=".devpilot/identity/identity_registry.json", metadata={"flag": key, "actual": security.get(key)}))
        actors = registry.get("actors") if isinstance(registry.get("actors"), list) else []
        for actor in actors:
            if isinstance(actor, dict) and (actor.get("credentials_stored") is not False or actor.get("remote_auth_enabled") is not False):
                findings.append(Finding("MULTIUSER_AUTH_IDENTITY_ACTOR_ENABLEMENT_BLOCK", "Identity actor credentials_stored and remote_auth_enabled must remain false.", Severity.BLOCK, path=".devpilot/identity/identity_registry.json", metadata={"actor_id": actor.get("actor_id")}))
        return findings

    def _validate_api_security_report(self, text: str) -> list[Finding]:
        findings: list[Finding] = []
        lowered = text.lower()
        if "no es iam enterprise" not in lowered and "no es iam" not in lowered:
            findings.append(Finding("MULTIUSER_AUTH_API_SECURITY_BOUNDARY_MISSING", "API security report/runbook must state the local token is not IAM enterprise.", Severity.WARN, path="docs/audits/post_h_028_b_local_auth_cors_hardening_report.md"))
        return findings

    def _validate_project_state(self, state: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        for key in (
            "production_multiuser", "production_multiuser_enabled", "multiuser_auth_enabled", "multiuser_runtime_enabled", "iam_enterprise_enabled", "session_management_enabled", "tenancy_enabled", "public_api_enabled", "network_allowed", "network_used", "external_api_used", "credentials_required", "connector_write_enabled", "plugin_execution_enabled", "remote_execution_enabled", "enterprise_ready_claimed", "compliance_certification_claim",
        ):
            if state.get(key) is not False:
                findings.append(Finding("MULTIUSER_AUTH_PROJECT_STATE_NO_GO_BLOCK", f"project_state.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.project_state_path), metadata={"flag": key, "actual": state.get(key)}))
        return findings

    def _summary(self, decision: dict[str, Any] | None, matrix: dict[str, Any] | None, identity_registry: dict[str, Any] | None, project_state: dict[str, Any] | None, blocking: list[Finding]) -> dict[str, Any]:
        decision = decision or {}
        defaults = identity_registry.get("defaults") if isinstance(identity_registry, dict) and isinstance(identity_registry.get("defaults"), dict) else {}
        return {
            "created_by": POST_H_034_D_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "capability_id": "multiuser.auth",
            "multiuser_decision_state": decision.get("decision_state"),
            "multiuser_decision_status": decision.get("decision_status"),
            "multiuser_auth_enabled": decision.get("multiuser_auth_enabled"),
            "production_multiuser_enabled": decision.get("production_multiuser_enabled"),
            "multiuser_runtime_enabled": decision.get("multiuser_runtime_enabled"),
            "iam_enterprise_enabled": decision.get("iam_enterprise_enabled"),
            "session_management_enabled": decision.get("session_management_enabled"),
            "tenancy_enabled": decision.get("tenancy_enabled"),
            "public_api_enabled": decision.get("public_api_enabled"),
            "network_allowed": decision.get("network_allowed"),
            "external_api_allowed": decision.get("external_api_allowed"),
            "credentials_required": decision.get("credentials_required"),
            "identity_remote_auth_enabled": defaults.get("auth_remote_enabled") if defaults else None,
            "identity_credentials_stored": defaults.get("credentials_stored") if defaults else None,
            "project_state_production_multiuser": project_state.get("production_multiuser") if isinstance(project_state, dict) else None,
            "matrix_loaded": matrix is not None,
            "decision_loaded": bool(decision),
            "blocking_findings_total": len(blocking),
            "findings_total": len(blocking),
            "claims_changed": False,
            "reports_written": False,
        }


class EnterpriseSaasBoundaryAdrValidator:
    """POST-H-034-E validator for enterprise/SaaS/compliance boundary invariants.

    The validator reads local source-controlled decision, enterprise threat model,
    compliance mapping and project metadata only. It does not open network
    connections, call cloud providers, create tenants, authenticate users, read
    credentials, start control planes or mutate the workspace.
    """

    def __init__(self, root: Path, *, options: SensitiveCapabilityOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SensitiveCapabilityOptions()

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        matrix, matrix_findings = load_decision_matrix(self.root, self.options.matrix_path)
        decision, decision_findings = load_enterprise_saas_boundary_decision(self.root, self.options.enterprise_saas_boundary_checklist_path)
        findings.extend(matrix_findings)
        findings.extend(decision_findings)

        enterprise_threat_model = self._read_json(self.options.enterprise_threat_model_path)
        enterprise_control_matrix = self._read_json(self.options.enterprise_control_matrix_path)
        compliance_control_mappings = self._read_json(self.options.compliance_control_mappings_path)
        compliance_evidence_mappings = self._read_json(self.options.compliance_evidence_mappings_path)
        project_state = self._read_json(self.options.project_state_path)
        adr_path = _resolve(self.root, self.options.enterprise_saas_boundary_adr_path)
        adr_text = ""
        if not adr_path.exists():
            findings.append(Finding("ENTERPRISE_SAAS_ADR_MISSING", "Enterprise/SaaS boundary ADR is missing.", Severity.BLOCK, path=_rel(self.options.enterprise_saas_boundary_adr_path)))
        else:
            adr_text = adr_path.read_text(encoding="utf-8")
            if 'status: "approved"' not in adr_text:
                findings.append(Finding("ENTERPRISE_SAAS_ADR_NOT_APPROVED", "Enterprise/SaaS boundary ADR must be approved.", Severity.BLOCK, path=_rel(self.options.enterprise_saas_boundary_adr_path)))
            if 'decision_status: "continue-blocked"' not in adr_text:
                findings.append(Finding("ENTERPRISE_SAAS_ADR_NOT_CONTINUE_BLOCKED", "Enterprise/SaaS boundary ADR must declare continue-blocked.", Severity.BLOCK, path=_rel(self.options.enterprise_saas_boundary_adr_path)))

        if decision:
            findings.extend(self._validate_decision(decision, adr_text))
        if matrix:
            findings.extend(self._validate_matrix(matrix))
        if enterprise_threat_model:
            findings.extend(self._validate_enterprise_threat_model(enterprise_threat_model))
        else:
            findings.append(Finding("ENTERPRISE_SAAS_THREAT_MODEL_MISSING", "Enterprise threat model must remain available as design-only evidence.", Severity.BLOCK, path=_rel(self.options.enterprise_threat_model_path)))
        if enterprise_control_matrix:
            findings.extend(self._validate_enterprise_control_matrix(enterprise_control_matrix))
        else:
            findings.append(Finding("ENTERPRISE_SAAS_CONTROL_MATRIX_MISSING", "Enterprise control matrix must remain available as design-only evidence.", Severity.BLOCK, path=_rel(self.options.enterprise_control_matrix_path)))
        if compliance_control_mappings:
            findings.extend(self._validate_compliance_mapping(compliance_control_mappings, self.options.compliance_control_mappings_path))
        else:
            findings.append(Finding("ENTERPRISE_SAAS_COMPLIANCE_CONTROLS_MISSING", "Compliance control mappings must remain available as non-certifying evidence.", Severity.BLOCK, path=_rel(self.options.compliance_control_mappings_path)))
        if compliance_evidence_mappings:
            findings.extend(self._validate_compliance_mapping(compliance_evidence_mappings, self.options.compliance_evidence_mappings_path))
        else:
            findings.append(Finding("ENTERPRISE_SAAS_COMPLIANCE_EVIDENCE_MISSING", "Compliance evidence mappings must remain available as non-certifying evidence.", Severity.BLOCK, path=_rel(self.options.compliance_evidence_mappings_path)))
        if project_state:
            findings.extend(self._validate_project_state(project_state))

        blocking = [finding for finding in findings if finding.severity in _BLOCKING]
        if not blocking:
            findings.append(Finding("ENTERPRISE_SAAS_BOUNDARY_ADR_GATE_PASS", "Enterprise/SaaS boundary ADR gate passed: enterprise-ready, SaaS-ready, compliance-certified, control plane, tenancy, public API, network, external APIs and credentials remain disabled.", Severity.INFO))
        return CommandResult(
            command="sensitive-capability enterprise-saas-boundary validate",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Enterprise/SaaS boundary ADR gate passed." if not blocking else "Enterprise/SaaS boundary ADR gate blocked.",
            data={
                "summary": self._summary(decision, matrix, enterprise_threat_model, enterprise_control_matrix, compliance_control_mappings, project_state, blocking),
                "notes": [
                    "POST-H-034-E validates ADR/no-go decisions only.",
                    "The validator does not enable enterprise, SaaS, compliance certification, control plane, cloud deployment, tenancy, public API, network, external APIs or credentials.",
                ],
            },
            findings=findings,
        )

    def _read_json(self, path: Path | str) -> dict[str, Any] | None:
        resolved = _resolve(self.root, path)
        if not resolved.exists():
            return None
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def _validate_decision(self, decision: dict[str, Any], adr_text: str) -> list[Finding]:
        findings: list[Finding] = []
        if decision.get("created_by") != POST_H_034_E_CREATED_BY:
            findings.append(Finding("ENTERPRISE_SAAS_WRONG_OWNER", "Enterprise/SaaS boundary decision must be created by POST-H-034-E.", Severity.BLOCK, metadata={"actual": decision.get("created_by")}))
        if decision.get("decision_state") not in ALLOWED_ENTERPRISE_SAAS_BOUNDARY_DECISIONS:
            findings.append(Finding("ENTERPRISE_SAAS_UNKNOWN_DECISION", "Enterprise/SaaS boundary decision_state is not allowed.", Severity.BLOCK, metadata={"actual": decision.get("decision_state")}))
        if decision.get("decision_state") != POST_H_034_E_EXPECTED_DECISION:
            findings.append(Finding("ENTERPRISE_SAAS_NOT_CONTINUE_BLOCKED", "Enterprise/SaaS boundary must remain continue-blocked in POST-H-034-E.", Severity.BLOCK, metadata={"actual": decision.get("decision_state")}))
        false_flags = (
            "enterprise_ready_claimed", "enterprise_ready_enabled", "enterprise_runtime_enabled", "saas_ready_claimed", "saas_runtime_enabled", "control_plane_enabled", "cloud_deployment_enabled", "tenancy_enabled", "tenant_isolation_implemented", "public_api_enabled", "compliance_certified", "compliance_certification_claim", "external_audit_claimed", "legal_advice_claimed", "network_allowed", "external_api_allowed", "credentials_required",
        )
        for key in false_flags:
            if decision.get(key) is not False:
                findings.append(Finding("ENTERPRISE_SAAS_DECISION_FLAG_BLOCK", f"{key} must remain false.", Severity.BLOCK, path=_rel(self.options.enterprise_saas_boundary_checklist_path), metadata={"flag": key, "actual": decision.get(key)}))
        true_flags = (
            "production_ready_local_scope_preserved", "enterprise_threat_model_design_only", "compliance_mapping_non_certifying", "requires_future_backlog", "requires_future_enablement_adr", "requires_human_approval", "enterprise_architecture_required_before_pilot", "tenancy_required_before_saas", "external_audit_required_before_certification", "migration_plan_required_before_enterprise",
        )
        for key in true_flags:
            if decision.get(key) is not True:
                findings.append(Finding("ENTERPRISE_SAAS_REQUIRED_CONTROL_BLOCK", f"{key} must remain true.", Severity.BLOCK, path=_rel(self.options.enterprise_saas_boundary_checklist_path), metadata={"flag": key, "actual": decision.get(key)}))
        lowered = adr_text.lower()
        required_rules = [
            "enterprise threat model exists != enterprise-ready",
            "enterprise control matrix exists != production enterprise authorization",
            "compliance mapping exists != compliance-certified",
            "production-ready-local exists != saas-ready",
            "post-h-034-e adr exists != runtime enablement",
        ]
        for rule in required_rules:
            if rule not in lowered:
                findings.append(Finding("ENTERPRISE_SAAS_ADR_MISSING_INTERPRETATION_RULE", "ADR must separate design/compliance evidence from enterprise/SaaS enablement.", Severity.BLOCK, path=_rel(self.options.enterprise_saas_boundary_adr_path), metadata={"rule": rule}))
        return findings

    def _validate_matrix(self, matrix: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        decision = enterprise_saas_decision_from_matrix(matrix)
        if decision is None:
            findings.append(Finding("ENTERPRISE_SAAS_MATRIX_ENTRY_MISSING", "Sensitive capability matrix must include enterprise.saas.", Severity.BLOCK, path=_rel(self.options.matrix_path)))
            return findings
        if decision.decision_state != POST_H_034_E_EXPECTED_DECISION:
            findings.append(Finding("ENTERPRISE_SAAS_MATRIX_DECISION_BLOCK", "Matrix enterprise.saas decision must remain continue-blocked.", Severity.BLOCK, path=_rel(self.options.matrix_path), metadata=decision.to_dict()))
        if decision.runtime_enabled is not False:
            findings.append(Finding("ENTERPRISE_SAAS_MATRIX_RUNTIME_BLOCK", "Matrix enterprise.saas runtime_enabled must remain false.", Severity.BLOCK, path=_rel(self.options.matrix_path), metadata=decision.to_dict()))
        gates = matrix.get("global_no_go_gates", {}) if isinstance(matrix.get("global_no_go_gates"), dict) else {}
        for key in ("enterprise_ready", "saas_ready", "compliance_certified", "production_multiuser"):
            if gates.get(key) is not False:
                findings.append(Finding("ENTERPRISE_SAAS_MATRIX_NO_GO_BLOCK", f"global_no_go_gates.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.matrix_path), metadata={"flag": key, "actual": gates.get(key)}))
        return findings

    def _validate_enterprise_threat_model(self, model: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        expected = {
            "decision_status": "design-only",
            "enterprise_deployment_enabled": False,
            "production_multiuser_enabled": False,
            "control_plane_enabled": False,
            "remote_execution_enabled": False,
            "secure_transport_implemented": False,
            "compliance_certification_claim": False,
        }
        for key, value in expected.items():
            if model.get(key) != value:
                findings.append(Finding("ENTERPRISE_SAAS_THREAT_MODEL_FLAG_BLOCK", f"Enterprise threat model {key} must remain {value!r}.", Severity.BLOCK, path=_rel(self.options.enterprise_threat_model_path), metadata={"flag": key, "actual": model.get(key)}))
        safety = model.get("safety") if isinstance(model.get("safety"), dict) else {}
        for key in ("network_used", "external_api_used", "mutations_performed", "source_mutations_performed", "secrets_read"):
            if safety.get(key) is not False:
                findings.append(Finding("ENTERPRISE_SAAS_THREAT_MODEL_SAFETY_BLOCK", f"Enterprise threat model safety.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.enterprise_threat_model_path), metadata={"flag": key, "actual": safety.get(key)}))
        return findings

    def _validate_enterprise_control_matrix(self, matrix: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        expected = {
            "decision_status": "design-only",
            "enterprise_ready_claimed": False,
            "enterprise_deployment_enabled": False,
            "remote_execution_enabled": False,
            "secure_transport_implemented": False,
            "compliance_certification_claim": False,
        }
        for key, value in expected.items():
            if matrix.get(key) != value:
                findings.append(Finding("ENTERPRISE_SAAS_CONTROL_MATRIX_FLAG_BLOCK", f"Enterprise control matrix {key} must remain {value!r}.", Severity.BLOCK, path=_rel(self.options.enterprise_control_matrix_path), metadata={"flag": key, "actual": matrix.get(key)}))
        summary = matrix.get("summary") if isinstance(matrix.get("summary"), dict) else {}
        if int(summary.get("required_not_implemented_total", 0)) <= 0:
            findings.append(Finding("ENTERPRISE_SAAS_CONTROL_MATRIX_NO_BLOCKERS", "Enterprise control matrix must keep explicit blockers before enterprise-ready claims.", Severity.BLOCK, path=_rel(self.options.enterprise_control_matrix_path)))
        return findings

    def _validate_compliance_mapping(self, payload: dict[str, Any], path: Path | str) -> list[Finding]:
        findings: list[Finding] = []
        if payload.get("certification_claimed") is not False:
            findings.append(Finding("ENTERPRISE_SAAS_COMPLIANCE_CERTIFICATION_BLOCK", "Compliance mapping certification_claimed must remain false.", Severity.BLOCK, path=_rel(path)))
        if payload.get("legal_advice_claimed") is not False:
            findings.append(Finding("ENTERPRISE_SAAS_COMPLIANCE_LEGAL_ADVICE_BLOCK", "Compliance mapping legal_advice_claimed must remain false.", Severity.BLOCK, path=_rel(path)))
        safety = payload.get("safety") if isinstance(payload.get("safety"), dict) else {}
        for key in ("network_used", "external_api_used", "mutations_performed"):
            if safety.get(key) is not False:
                findings.append(Finding("ENTERPRISE_SAAS_COMPLIANCE_SAFETY_BLOCK", f"Compliance mapping safety.{key} must remain false.", Severity.BLOCK, path=_rel(path), metadata={"flag": key, "actual": safety.get(key)}))
        disclaimer = str(payload.get("disclaimer", "")).lower()
        if "not" not in disclaimer or ("certification" not in disclaimer and "certified" not in disclaimer):
            findings.append(Finding("ENTERPRISE_SAAS_COMPLIANCE_DISCLAIMER_WEAK", "Compliance mapping must keep a non-certification disclaimer.", Severity.BLOCK, path=_rel(path)))
        return findings

    def _validate_project_state(self, state: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        for key in (
            "enterprise_ready_claimed", "enterprise_ready_enabled", "enterprise_runtime_enabled", "enterprise_deployment_enabled", "saas_ready_claimed", "saas_runtime_enabled", "control_plane_enabled", "cloud_deployment_enabled", "tenancy_enabled", "tenant_isolation_implemented", "public_api_enabled", "compliance_certification_claim", "compliance_certified_claimed", "external_audit_claimed", "legal_advice_claimed", "network_allowed", "network_used", "external_api_used", "credentials_required", "connector_write_enabled", "plugin_execution_enabled", "remote_execution_enabled", "production_multiuser",
        ):
            if state.get(key) is not False:
                findings.append(Finding("ENTERPRISE_SAAS_PROJECT_STATE_NO_GO_BLOCK", f"project_state.{key} must remain false.", Severity.BLOCK, path=_rel(self.options.project_state_path), metadata={"flag": key, "actual": state.get(key)}))
        return findings

    def _summary(self, decision: dict[str, Any] | None, matrix: dict[str, Any] | None, enterprise_threat_model: dict[str, Any] | None, enterprise_control_matrix: dict[str, Any] | None, compliance_mapping: dict[str, Any] | None, project_state: dict[str, Any] | None, blocking: list[Finding]) -> dict[str, Any]:
        decision = decision or {}
        return {
            "created_by": POST_H_034_E_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "capability_id": "enterprise.saas",
            "enterprise_saas_decision_state": decision.get("decision_state"),
            "enterprise_saas_decision_status": decision.get("decision_status"),
            "enterprise_ready_claimed": decision.get("enterprise_ready_claimed"),
            "enterprise_ready_enabled": decision.get("enterprise_ready_enabled"),
            "saas_ready_claimed": decision.get("saas_ready_claimed"),
            "control_plane_enabled": decision.get("control_plane_enabled"),
            "cloud_deployment_enabled": decision.get("cloud_deployment_enabled"),
            "tenancy_enabled": decision.get("tenancy_enabled"),
            "public_api_enabled": decision.get("public_api_enabled"),
            "compliance_certification_claim": decision.get("compliance_certification_claim"),
            "compliance_certified": decision.get("compliance_certified"),
            "network_allowed": decision.get("network_allowed"),
            "external_api_allowed": decision.get("external_api_allowed"),
            "credentials_required": decision.get("credentials_required"),
            "enterprise_threat_model_decision_status": enterprise_threat_model.get("decision_status") if isinstance(enterprise_threat_model, dict) else None,
            "enterprise_control_matrix_decision_status": enterprise_control_matrix.get("decision_status") if isinstance(enterprise_control_matrix, dict) else None,
            "compliance_certification_claimed": compliance_mapping.get("certification_claimed") if isinstance(compliance_mapping, dict) else None,
            "project_state_enterprise_ready_claimed": project_state.get("enterprise_ready_claimed") if isinstance(project_state, dict) else None,
            "matrix_loaded": matrix is not None,
            "decision_loaded": bool(decision),
            "blocking_findings_total": len(blocking),
            "findings_total": len(blocking),
            "claims_changed": False,
            "reports_written": False,
        }
