from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.sensitive_capabilities.decision_matrix import (
    connector_write_decision_from_matrix,
    load_connector_write_decision,
    load_decision_matrix,
)
from devpilot_core.sensitive_capabilities.models import (
    ALLOWED_CONNECTOR_WRITE_DECISIONS,
    POST_H_034_A_CREATED_BY,
    POST_H_034_A_EXPECTED_DECISION,
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
