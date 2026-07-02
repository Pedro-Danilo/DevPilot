from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

_BLOCKING_SEVERITIES = {Severity.FAIL, Severity.BLOCK, Severity.ERROR}


@dataclass(frozen=True)
class EnterpriseThreatModelValidationOptions:
    """Paths used by the POST-H-022-D enterprise design-only validator."""

    threat_model_path: str = ".devpilot/enterprise/enterprise_threat_model.json"
    control_matrix_path: str = ".devpilot/enterprise/enterprise_control_matrix.json"


class EnterpriseThreatModelValidator:
    """Validate enterprise deployment design artifacts without enabling runtime.

    POST-H-022-D is a read-only semantic validator. It reads the enterprise
    threat model and control matrix, checks design-only no-go gates, and reports
    readiness blockers. It does not deploy, contact a network service, read
    secrets, execute remote work or mutate source files.
    """

    def __init__(self, root: Path, options: EnterpriseThreatModelValidationOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or EnterpriseThreatModelValidationOptions()

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        threat_model = self._load_json(self.options.threat_model_path, findings)
        control_matrix = self._load_json(self.options.control_matrix_path, findings)

        summary = self._summary(threat_model, control_matrix)
        if not findings:
            findings.extend(self._validate_threat_model(threat_model))
            findings.extend(self._validate_control_matrix(control_matrix))
            findings.extend(self._validate_cross_artifact_consistency(threat_model, control_matrix))

        blocking = _blocking(findings)
        summary["blocking_findings_total"] = len(blocking)
        ok = not blocking
        return CommandResult(
            command="enterprise threat-model validate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Enterprise threat model design-only validation passed." if ok else "Enterprise threat model design-only validation blocked.",
            data={
                "summary": summary,
                "source_paths": {
                    "threat_model": self.options.threat_model_path,
                    "control_matrix": self.options.control_matrix_path,
                },
                "notes": [
                    "POST-H-022-D validates enterprise design artifacts in read-only mode.",
                    "The validator is not an enterprise readiness claim and does not enable deployment, remote execution, network, secure transport or compliance certification.",
                ],
            },
            findings=findings
            or [
                Finding(
                    "ENTERPRISE_THREAT_MODEL_DESIGN_ONLY_PASS",
                    "Enterprise threat model remains design-only with explicit readiness blockers.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _load_json(self, relative_path: str, findings: list[Finding]) -> dict[str, Any]:
        path = self._resolve(relative_path)
        if not path.exists():
            findings.append(Finding("ENTERPRISE_ARTIFACT_MISSING", "Required enterprise design artifact is missing.", Severity.BLOCK, path=relative_path))
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("ENTERPRISE_ARTIFACT_INVALID_JSON", "Required enterprise design artifact is not valid JSON.", Severity.ERROR, path=relative_path, metadata={"error": str(exc)}))
            return {}
        if not isinstance(payload, dict):
            findings.append(Finding("ENTERPRISE_ARTIFACT_NOT_OBJECT", "Enterprise design artifact must be a JSON object.", Severity.ERROR, path=relative_path))
            return {}
        return payload

    def _summary(self, threat_model: dict[str, Any], control_matrix: dict[str, Any]) -> dict[str, Any]:
        matrix_summary = control_matrix.get("summary", {}) if isinstance(control_matrix.get("summary"), dict) else {}
        controls = control_matrix.get("controls", []) if isinstance(control_matrix.get("controls"), list) else []
        required_not_implemented = [
            item for item in controls if isinstance(item, dict) and item.get("status") == "required-not-implemented"
        ]
        partial = [item for item in controls if isinstance(item, dict) and item.get("status") == "partial"]
        implemented = [item for item in controls if isinstance(item, dict) and item.get("status") == "implemented"]
        return {
            "created_by": "POST-H-022-D",
            "status": "implemented-initial",
            "preliminary": True,
            "decision_status": "design-only",
            "threat_model_loaded": bool(threat_model),
            "control_matrix_loaded": bool(control_matrix),
            "enterprise_deployment_enabled": bool(threat_model.get("enterprise_deployment_enabled") or control_matrix.get("enterprise_deployment_enabled")),
            "remote_execution_enabled": bool(threat_model.get("remote_execution_enabled") or control_matrix.get("remote_execution_enabled")),
            "secure_transport_implemented": bool(threat_model.get("secure_transport_implemented") or control_matrix.get("secure_transport_implemented")),
            "compliance_certification_claim": bool(threat_model.get("compliance_certification_claim") or control_matrix.get("compliance_certification_claim")),
            "enterprise_ready_claimed": bool(control_matrix.get("enterprise_ready_claimed")),
            "assets_total": len(threat_model.get("assets", [])) if isinstance(threat_model.get("assets"), list) else 0,
            "actors_total": len(threat_model.get("actors", [])) if isinstance(threat_model.get("actors"), list) else 0,
            "trust_boundaries_total": len(threat_model.get("trust_boundaries", [])) if isinstance(threat_model.get("trust_boundaries"), list) else 0,
            "threats_total": len(threat_model.get("threat_catalog", [])) if isinstance(threat_model.get("threat_catalog"), list) else 0,
            "controls_total": len(controls),
            "implemented_controls_total": len(implemented),
            "partial_controls_total": len(partial),
            "required_not_implemented_total": len(required_not_implemented),
            "matrix_required_not_implemented_total": int(matrix_summary.get("required_not_implemented_total", 0) or 0),
            "enterprise_ready": bool((control_matrix.get("go_no_go") or {}).get("enterprise_ready")) if isinstance(control_matrix.get("go_no_go"), dict) else False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "secrets_read": False,
            "remote_execution_used": False,
        }

    def _validate_threat_model(self, threat_model: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        if threat_model.get("decision_status") != "design-only":
            findings.append(Finding("ENTERPRISE_THREAT_MODEL_NOT_DESIGN_ONLY", "Enterprise threat model must remain design-only.", Severity.BLOCK, path=self.options.threat_model_path, metadata={"decision_status": threat_model.get("decision_status")}))
        for flag in (
            "enterprise_deployment_enabled",
            "production_multiuser_enabled",
            "control_plane_enabled",
            "remote_execution_enabled",
            "secure_transport_implemented",
            "compliance_certification_claim",
        ):
            if threat_model.get(flag) is not False:
                findings.append(Finding("ENTERPRISE_THREAT_MODEL_UNSAFE_FLAG", "Enterprise threat model no-go flag must remain false.", Severity.BLOCK, path=self.options.threat_model_path, metadata={"flag": flag, "value": threat_model.get(flag)}))
        summary = threat_model.get("threat_catalog_summary")
        if not isinstance(summary, dict):
            findings.append(Finding("ENTERPRISE_THREAT_CATALOG_SUMMARY_MISSING", "Enterprise threat model must include threat_catalog_summary from POST-H-022-B.", Severity.BLOCK, path=self.options.threat_model_path))
        else:
            for flag in ("all_boundaries_have_threats", "critical_threats_have_controls"):
                if summary.get(flag) is not True:
                    findings.append(Finding("ENTERPRISE_THREAT_CATALOG_COVERAGE_BLOCKED", "Enterprise threat catalog coverage flag is not satisfied.", Severity.BLOCK, path=self.options.threat_model_path, metadata={"flag": flag, "value": summary.get(flag)}))
        return findings

    def _validate_control_matrix(self, control_matrix: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        if control_matrix.get("decision_status") != "design-only":
            findings.append(Finding("ENTERPRISE_CONTROL_MATRIX_NOT_DESIGN_ONLY", "Enterprise control matrix must remain design-only.", Severity.BLOCK, path=self.options.control_matrix_path, metadata={"decision_status": control_matrix.get("decision_status")}))
        for flag in (
            "enterprise_ready_claimed",
            "enterprise_deployment_enabled",
            "remote_execution_enabled",
            "secure_transport_implemented",
            "compliance_certification_claim",
        ):
            if control_matrix.get(flag) is not False:
                findings.append(Finding("ENTERPRISE_CONTROL_MATRIX_UNSAFE_FLAG", "Enterprise control matrix no-go flag must remain false.", Severity.BLOCK, path=self.options.control_matrix_path, metadata={"flag": flag, "value": control_matrix.get(flag)}))

        controls = control_matrix.get("controls")
        if not isinstance(controls, list) or not controls:
            findings.append(Finding("ENTERPRISE_CONTROL_MATRIX_EMPTY", "Enterprise control matrix must define controls.", Severity.BLOCK, path=self.options.control_matrix_path))
            return findings
        statuses = {item.get("status") for item in controls if isinstance(item, dict)}
        if not {"implemented", "partial", "required-not-implemented"}.issubset(statuses):
            findings.append(Finding("ENTERPRISE_CONTROL_MATRIX_STATUS_COVERAGE_BLOCKED", "Enterprise control matrix must distinguish implemented, partial and required-not-implemented controls.", Severity.BLOCK, path=self.options.control_matrix_path, metadata={"statuses": sorted(str(item) for item in statuses)}))
        required_not_implemented = [
            item for item in controls if isinstance(item, dict) and item.get("status") == "required-not-implemented"
        ]
        if not required_not_implemented:
            findings.append(Finding("ENTERPRISE_READINESS_OVERCLAIM_BLOCKED", "Enterprise control matrix must keep explicit required-not-implemented blockers.", Severity.BLOCK, path=self.options.control_matrix_path))
        for item in required_not_implemented:
            if item.get("blocks_enterprise_readiness") is not True:
                findings.append(Finding("ENTERPRISE_CONTROL_BLOCKER_DRIFT", "Required-not-implemented controls must block enterprise readiness.", Severity.BLOCK, path=self.options.control_matrix_path, metadata={"control_id": item.get("control_id")}))
        if isinstance(control_matrix.get("go_no_go"), dict) and control_matrix["go_no_go"].get("enterprise_ready") is not False:
            findings.append(Finding("ENTERPRISE_GO_NO_GO_READY_BLOCKED", "Enterprise go/no-go checklist must not mark enterprise_ready=true.", Severity.BLOCK, path=self.options.control_matrix_path))
        return findings

    def _validate_cross_artifact_consistency(self, threat_model: dict[str, Any], control_matrix: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        threat_ids = {item.get("threat_id") for item in threat_model.get("threat_catalog", []) if isinstance(item, dict)}
        risk_ids = {item.get("risk_id") for item in threat_model.get("residual_risks", []) if isinstance(item, dict)}
        boundary_ids = {item.get("boundary_id") for item in threat_model.get("trust_boundaries", []) if isinstance(item, dict)}
        for control in control_matrix.get("controls", []) if isinstance(control_matrix.get("controls"), list) else []:
            if not isinstance(control, dict):
                continue
            missing_threats = sorted(set(control.get("mapped_threat_ids", [])) - threat_ids)
            missing_risks = sorted(set(control.get("mapped_residual_risk_ids", [])) - risk_ids)
            missing_boundaries = sorted(set(control.get("mapped_boundary_ids", [])) - boundary_ids)
            if missing_threats or missing_risks or missing_boundaries:
                findings.append(
                    Finding(
                        "ENTERPRISE_CONTROL_MAPPING_DRIFT",
                        "Enterprise control references unknown threat, risk or boundary ids.",
                        Severity.BLOCK,
                        path=self.options.control_matrix_path,
                        metadata={
                            "control_id": control.get("control_id"),
                            "missing_threat_ids": missing_threats,
                            "missing_residual_risk_ids": missing_risks,
                            "missing_boundary_ids": missing_boundaries,
                        },
                    )
                )
        return findings

    def _resolve(self, value: str | Path) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.root / path


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
