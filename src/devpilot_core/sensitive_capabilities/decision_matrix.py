from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import Finding, Severity
from devpilot_core.schemas import SchemaValidator
from devpilot_core.sensitive_capabilities.models import (
    CONNECTOR_WRITE_DECISION_CONTRACT,
    DEFAULT_CONNECTOR_WRITE_CHECKLIST_PATH,
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


def connector_write_decision_from_matrix(matrix: dict[str, Any]) -> SensitiveCapabilityDecision | None:
    for item in matrix.get("capabilities", []):
        if isinstance(item, dict) and item.get("capability_id") == "connector.write":
            return SensitiveCapabilityDecision.from_payload(item)
    return None
