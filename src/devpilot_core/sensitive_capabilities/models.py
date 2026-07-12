from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_SENSITIVE_CAPABILITY_MATRIX_PATH = Path(".devpilot/sensitive_capabilities/capability_decision_matrix.json")
DEFAULT_CONNECTOR_WRITE_CHECKLIST_PATH = Path(".devpilot/sensitive_capabilities/connector_write_enablement_checklist.json")
DEFAULT_CONNECTOR_WRITE_ADR_PATH = Path("docs/adr/ADR-POSTH-034-A-connector-write-enable-or-continue-blocked.md")
DEFAULT_PLUGIN_EXECUTION_CHECKLIST_PATH = Path(".devpilot/sensitive_capabilities/plugin_execution_enablement_checklist.json")
DEFAULT_PLUGIN_EXECUTION_ADR_PATH = Path("docs/adr/ADR-POSTH-034-B-plugin-execution-enable-or-continue-blocked.md")
DEFAULT_REMOTE_EXECUTION_ADR3_CHECKLIST_PATH = Path(".devpilot/sensitive_capabilities/remote_execution_adr3_checklist.json")
DEFAULT_REMOTE_EXECUTION_ADR3_ADR_PATH = Path("docs/adr/ADR-POSTH-034-C-remote-execution-adr3.md")
DEFAULT_MULTIUSER_AUTH_CHECKLIST_PATH = Path(".devpilot/sensitive_capabilities/multiuser_auth_checklist.json")
DEFAULT_MULTIUSER_AUTH_ADR_PATH = Path("docs/adr/ADR-POSTH-034-D-multiuser-auth-boundary.md")
DEFAULT_CONNECTOR_SANDBOX_POLICY_PATH = Path(".devpilot/connectors/connector_sandbox_policy.json")
DEFAULT_PLUGIN_REGISTRY_PATH = Path(".devpilot/plugins/plugin_registry.json")
DEFAULT_PLUGIN_PERMISSION_MODEL_PATH = Path(".devpilot/plugins/plugin_permission_model.json")
DEFAULT_REMOTE_RUNNER_REGISTRY_PATH = Path(".devpilot/remote/runner_registry.json")
DEFAULT_REMOTE_READINESS_CRITERIA_PATH = Path(".devpilot/remote/remote_readiness_criteria.json")
DEFAULT_SECURE_TRANSPORT_DECISION_MATRIX_PATH = Path(".devpilot/remote/secure_transport_protocol_decision_matrix.json")
DEFAULT_PROJECT_STATE_PATH = Path(".devpilot/project_state.json")

SENSITIVE_CAPABILITY_DECISION_MATRIX_SCHEMA_ID = "SCHEMA-DEVPL-SENSITIVE-CAPABILITY-DECISION-MATRIX-V1"
SENSITIVE_CAPABILITY_DECISION_MATRIX_CONTRACT = "SensitiveCapabilityDecisionMatrix"
CONNECTOR_WRITE_DECISION_SCHEMA_ID = "SCHEMA-DEVPL-CONNECTOR-WRITE-DECISION-V1"
CONNECTOR_WRITE_DECISION_CONTRACT = "ConnectorWriteDecision"
PLUGIN_EXECUTION_DECISION_SCHEMA_ID = "SCHEMA-DEVPL-PLUGIN-EXECUTION-DECISION-V1"
PLUGIN_EXECUTION_DECISION_CONTRACT = "PluginExecutionDecision"
REMOTE_EXECUTION_ADR3_DECISION_SCHEMA_ID = "SCHEMA-DEVPL-REMOTE-EXECUTION-ADR3-DECISION-V1"
REMOTE_EXECUTION_ADR3_DECISION_CONTRACT = "RemoteExecutionAdr3Decision"
MULTIUSER_AUTH_DECISION_SCHEMA_ID = "SCHEMA-DEVPL-MULTIUSER-AUTH-DECISION-V1"
MULTIUSER_AUTH_DECISION_CONTRACT = "MultiuserAuthDecision"

POST_H_034_A_CREATED_BY = "POST-H-034-A"
ALLOWED_CONNECTOR_WRITE_DECISIONS = {
    "continue-blocked",
    "pilot-gated-future",
    "approved-for-future-implementation",
    "rejected",
}
POST_H_034_A_EXPECTED_DECISION = "continue-blocked"
POST_H_034_B_CREATED_BY = "POST-H-034-B"
ALLOWED_PLUGIN_EXECUTION_DECISIONS = {
    "continue-blocked",
    "pilot-gated-future",
    "approved-for-future-implementation",
    "rejected",
}
POST_H_034_B_EXPECTED_DECISION = "continue-blocked"
POST_H_034_C_CREATED_BY = "POST-H-034-C"
ALLOWED_REMOTE_EXECUTION_ADR3_DECISIONS = {
    "continue-blocked",
    "pilot-gated-future",
    "approved-for-future-implementation",
    "rejected",
}
POST_H_034_C_EXPECTED_DECISION = "continue-blocked"
POST_H_034_D_CREATED_BY = "POST-H-034-D"
ALLOWED_MULTIUSER_AUTH_DECISIONS = {
    "continue-blocked",
    "pilot-gated-future",
    "approved-for-future-implementation",
    "rejected",
    "out-of-scope",
}
POST_H_034_D_EXPECTED_DECISION = "continue-blocked"


@dataclass(frozen=True)
class SensitiveCapabilityOptions:
    matrix_path: Path | str = DEFAULT_SENSITIVE_CAPABILITY_MATRIX_PATH
    connector_write_checklist_path: Path | str = DEFAULT_CONNECTOR_WRITE_CHECKLIST_PATH
    connector_write_adr_path: Path | str = DEFAULT_CONNECTOR_WRITE_ADR_PATH
    plugin_execution_checklist_path: Path | str = DEFAULT_PLUGIN_EXECUTION_CHECKLIST_PATH
    plugin_execution_adr_path: Path | str = DEFAULT_PLUGIN_EXECUTION_ADR_PATH
    remote_execution_adr3_checklist_path: Path | str = DEFAULT_REMOTE_EXECUTION_ADR3_CHECKLIST_PATH
    remote_execution_adr3_adr_path: Path | str = DEFAULT_REMOTE_EXECUTION_ADR3_ADR_PATH
    multiuser_auth_checklist_path: Path | str = DEFAULT_MULTIUSER_AUTH_CHECKLIST_PATH
    multiuser_auth_adr_path: Path | str = DEFAULT_MULTIUSER_AUTH_ADR_PATH
    connector_sandbox_policy_path: Path | str = DEFAULT_CONNECTOR_SANDBOX_POLICY_PATH
    plugin_registry_path: Path | str = DEFAULT_PLUGIN_REGISTRY_PATH
    plugin_permission_model_path: Path | str = DEFAULT_PLUGIN_PERMISSION_MODEL_PATH
    remote_runner_registry_path: Path | str = DEFAULT_REMOTE_RUNNER_REGISTRY_PATH
    remote_readiness_criteria_path: Path | str = DEFAULT_REMOTE_READINESS_CRITERIA_PATH
    secure_transport_decision_matrix_path: Path | str = DEFAULT_SECURE_TRANSPORT_DECISION_MATRIX_PATH
    project_state_path: Path | str = DEFAULT_PROJECT_STATE_PATH


@dataclass(frozen=True)
class SensitiveCapabilityDecision:
    capability_id: str
    decision_state: str
    runtime_enabled: bool
    requires_future_adr: bool
    adr_path: str | None = None
    checklist_path: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "SensitiveCapabilityDecision":
        return cls(
            capability_id=str(payload.get("capability_id", "")),
            decision_state=str(payload.get("decision_state", "")),
            runtime_enabled=bool(payload.get("runtime_enabled", False)),
            requires_future_adr=bool(payload.get("requires_future_adr", False)),
            adr_path=payload.get("adr_path") if isinstance(payload.get("adr_path"), str) else None,
            checklist_path=payload.get("checklist_path") if isinstance(payload.get("checklist_path"), str) else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "decision_state": self.decision_state,
            "runtime_enabled": self.runtime_enabled,
            "requires_future_adr": self.requires_future_adr,
            "adr_path": self.adr_path,
            "checklist_path": self.checklist_path,
        }
