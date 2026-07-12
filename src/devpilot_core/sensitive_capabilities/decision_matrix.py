from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import Finding, Severity
from devpilot_core.schemas import SchemaValidator
from devpilot_core.sensitive_capabilities.models import (
    CONNECTOR_WRITE_DECISION_CONTRACT,
    DEFAULT_CONNECTOR_WRITE_CHECKLIST_PATH,
    DEFAULT_PLUGIN_EXECUTION_CHECKLIST_PATH,
    DEFAULT_REMOTE_EXECUTION_ADR3_CHECKLIST_PATH,
    DEFAULT_MULTIUSER_AUTH_CHECKLIST_PATH,
    DEFAULT_ENTERPRISE_SAAS_BOUNDARY_CHECKLIST_PATH,
    PLUGIN_EXECUTION_DECISION_CONTRACT,
    REMOTE_EXECUTION_ADR3_DECISION_CONTRACT,
    MULTIUSER_AUTH_DECISION_CONTRACT,
    ENTERPRISE_SAAS_BOUNDARY_DECISION_CONTRACT,
    DEFAULT_SENSITIVE_CAPABILITY_MATRIX_PATH,
    SENSITIVE_CAPABILITY_DECISION_MATRIX_CONTRACT,
    SensitiveCapabilityDecision,
)


def _display(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def _resolve(root: Path, path: Path | str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def load_json(root: Path, path: Path | str) -> tuple[dict[str, Any] | None, list[Finding]]:
    resolved = _resolve(root, path)
    rel = _display(Path(path))
    if not resolved.exists():
        return None, [Finding("SENSITIVE_CAPABILITY_ARTIFACT_MISSING", "Sensitive capability artifact is missing.", Severity.BLOCK, path=rel)]
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [Finding("SENSITIVE_CAPABILITY_ARTIFACT_INVALID_JSON", f"Sensitive capability artifact is not valid JSON: {exc}", Severity.ERROR, path=rel)]
    if not isinstance(payload, dict):
        return None, [Finding("SENSITIVE_CAPABILITY_ARTIFACT_NOT_OBJECT", "Sensitive capability artifact must be a JSON object.", Severity.BLOCK, path=rel)]
    return payload, []


def load_decision_matrix(root: Path, path: Path | str = DEFAULT_SENSITIVE_CAPABILITY_MATRIX_PATH) -> tuple[dict[str, Any] | None, list[Finding]]:
    payload, findings = load_json(root, path)
    if payload is None:
        return None, findings
    schema_result = SchemaValidator(root).validate(schema=SENSITIVE_CAPABILITY_DECISION_MATRIX_CONTRACT, instance=path)
    if not schema_result.ok:
        findings.extend(schema_result.findings)
        findings.append(Finding("SENSITIVE_CAPABILITY_MATRIX_SCHEMA_BLOCK", "Sensitive capability decision matrix does not conform to schema.", Severity.BLOCK, path=_display(path)))
    return payload, findings


def load_connector_write_decision(root: Path, path: Path | str = DEFAULT_CONNECTOR_WRITE_CHECKLIST_PATH) -> tuple[dict[str, Any] | None, list[Finding]]:
    payload, findings = load_json(root, path)
    if payload is None:
        return None, findings
    schema_result = SchemaValidator(root).validate(schema=CONNECTOR_WRITE_DECISION_CONTRACT, instance=path)
    if not schema_result.ok:
        findings.extend(schema_result.findings)
        findings.append(Finding("CONNECTOR_WRITE_DECISION_SCHEMA_BLOCK", "Connector write decision checklist does not conform to schema.", Severity.BLOCK, path=_display(path)))
    return payload, findings


def load_plugin_execution_decision(root: Path, path: Path | str = DEFAULT_PLUGIN_EXECUTION_CHECKLIST_PATH) -> tuple[dict[str, Any] | None, list[Finding]]:
    payload, findings = load_json(root, path)
    if payload is None:
        return None, findings
    schema_result = SchemaValidator(root).validate(schema=PLUGIN_EXECUTION_DECISION_CONTRACT, instance=path)
    if not schema_result.ok:
        findings.extend(schema_result.findings)
        findings.append(Finding("PLUGIN_EXECUTION_DECISION_SCHEMA_BLOCK", "Plugin execution decision checklist does not conform to schema.", Severity.BLOCK, path=_display(path)))
    return payload, findings


def load_remote_execution_adr3_decision(root: Path, path: Path | str = DEFAULT_REMOTE_EXECUTION_ADR3_CHECKLIST_PATH) -> tuple[dict[str, Any] | None, list[Finding]]:
    payload, findings = load_json(root, path)
    if payload is None:
        return None, findings
    schema_result = SchemaValidator(root).validate(schema=REMOTE_EXECUTION_ADR3_DECISION_CONTRACT, instance=path)
    if not schema_result.ok:
        findings.extend(schema_result.findings)
        findings.append(Finding("REMOTE_EXECUTION_ADR3_DECISION_SCHEMA_BLOCK", "Remote execution ADR-3 checklist does not conform to schema.", Severity.BLOCK, path=_display(path)))
    return payload, findings

def load_multiuser_auth_decision(root: Path, path: Path | str = DEFAULT_MULTIUSER_AUTH_CHECKLIST_PATH) -> tuple[dict[str, Any] | None, list[Finding]]:
    payload, findings = load_json(root, path)
    if payload is None:
        return None, findings
    schema_result = SchemaValidator(root).validate(schema=MULTIUSER_AUTH_DECISION_CONTRACT, instance=path)
    if not schema_result.ok:
        findings.extend(schema_result.findings)
        findings.append(Finding("MULTIUSER_AUTH_DECISION_SCHEMA_BLOCK", "Multiuser/auth decision checklist does not conform to schema.", Severity.BLOCK, path=_display(path)))
    return payload, findings


def load_enterprise_saas_boundary_decision(root: Path, path: Path | str = DEFAULT_ENTERPRISE_SAAS_BOUNDARY_CHECKLIST_PATH) -> tuple[dict[str, Any] | None, list[Finding]]:
    payload, findings = load_json(root, path)
    if payload is None:
        return None, findings
    schema_result = SchemaValidator(root).validate(schema=ENTERPRISE_SAAS_BOUNDARY_DECISION_CONTRACT, instance=path)
    if not schema_result.ok:
        findings.extend(schema_result.findings)
        findings.append(Finding("ENTERPRISE_SAAS_BOUNDARY_DECISION_SCHEMA_BLOCK", "Enterprise/SaaS boundary decision checklist does not conform to schema.", Severity.BLOCK, path=_display(path)))
    return payload, findings


def _decision_from_matrix(matrix: dict[str, Any], capability_id: str) -> SensitiveCapabilityDecision | None:
    for item in matrix.get("capabilities", []):
        if isinstance(item, dict) and item.get("capability_id") == capability_id:
            return SensitiveCapabilityDecision.from_payload(item)
    return None


def connector_write_decision_from_matrix(matrix: dict[str, Any]) -> SensitiveCapabilityDecision | None:
    return _decision_from_matrix(matrix, "connector.write")


def plugin_execution_decision_from_matrix(matrix: dict[str, Any]) -> SensitiveCapabilityDecision | None:
    return _decision_from_matrix(matrix, "plugin.execution")


def remote_execution_decision_from_matrix(matrix: dict[str, Any]) -> SensitiveCapabilityDecision | None:
    return _decision_from_matrix(matrix, "remote.execution")


def multiuser_auth_decision_from_matrix(matrix: dict[str, Any]) -> SensitiveCapabilityDecision | None:
    return _decision_from_matrix(matrix, "multiuser.auth")


def enterprise_saas_decision_from_matrix(matrix: dict[str, Any]) -> SensitiveCapabilityDecision | None:
    return _decision_from_matrix(matrix, "enterprise.saas")
