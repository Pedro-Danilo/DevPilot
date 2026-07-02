from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator

_BLOCKING_SEVERITIES = {Severity.FAIL, Severity.BLOCK, Severity.ERROR}
_UNSAFE_FALSE_FLAGS = (
    "transport_implemented",
    "secure_transport_implemented",
    "network_allowed",
    "network_used",
    "sockets_opened",
    "certificates_generated",
    "certificate_authority_created",
    "private_key_material_present",
    "raw_secret_storage_allowed",
    "secrets_required",
    "secrets_stored",
    "secrets_read",
    "remote_execution_enabled",
    "remote_execution_used",
    "connector_write_enabled",
    "plugin_execution_enabled",
)
_REQUIRED_CONTROLS = {
    "identity_hardening",
    "approval_rbac_hardening",
    "remote_runner_adr2",
    "enterprise_threat_model",
    "observability_retention",
    "runtime_state_lifecycle",
    "key_certificate_lifecycle",
    "replay_protection",
    "revocation_rotation",
    "transport_quality_gate",
}
_FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "grpc",
    "http",
    "httpx",
    "paramiko",
    "requests",
    "socket",
    "ssl",
    "urllib",
    "websocket",
    "websockets",
}
_FORBIDDEN_CALLS = {
    "asyncio.open_connection",
    "http.client.HTTPConnection",
    "http.client.HTTPSConnection",
    "socket.create_connection",
    "socket.socket",
    "ssl.create_default_context",
    "ssl.wrap_socket",
}


@dataclass(frozen=True)
class SecureTransportDesignValidationOptions:
    """Paths for the POST-H-023-D secure transport design validator.

    The validator is deliberately read-only and local-only. It reads design
    artifacts, validates their JSON schemas, performs semantic no-go checks and
    statically verifies that the remote package does not introduce active network
    primitives. It does not open sockets, generate certificates, read secrets,
    call external services or write reports.
    """

    requirements_path: str = ".devpilot/remote/secure_transport_requirements.json"
    requirements_schema_path: str = "docs/schemas/secure_transport_requirements.schema.json"
    protocol_matrix_path: str = ".devpilot/remote/secure_transport_protocol_decision_matrix.json"
    protocol_matrix_schema_path: str = "docs/schemas/secure_transport_design.schema.json"
    key_lifecycle_path: str = ".devpilot/remote/secure_transport_key_lifecycle.json"
    key_lifecycle_schema_path: str = "docs/schemas/secure_transport_key_lifecycle.schema.json"
    validation_report_schema_path: str = "docs/schemas/secure_transport_validation_report.schema.json"
    static_scan_roots: tuple[str, ...] = ("src/devpilot_core/remote",)


@dataclass(frozen=True)
class SecureTransportDesignQualityGateOptions(SecureTransportDesignValidationOptions):
    """Quality gate options for POST-H-023-D."""


class SecureTransportDesignValidator:
    """Validate secure transport design artifacts without enabling transport.

    POST-H-023-D converts the design-only artifacts produced by POST-H-023-A/B/C
    into an executable invariant. The validator is a guardrail for the future: a
    PASS means the current repository still declares local-only-no-transport and
    no implementation side effect was introduced; it is not an authorization to
    add network, TLS, SSH, certificates, secrets or remote execution.
    """

    def __init__(self, root: Path, *, options: SecureTransportDesignValidationOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SecureTransportDesignValidationOptions()
        self.schema_validator = SchemaValidator(self.root)

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        sources = {
            "requirements": (self.options.requirements_path, self.options.requirements_schema_path),
            "protocol_matrix": (self.options.protocol_matrix_path, self.options.protocol_matrix_schema_path),
            "key_lifecycle": (self.options.key_lifecycle_path, self.options.key_lifecycle_schema_path),
        }
        payloads: dict[str, dict[str, Any]] = {}
        artifact_checks: list[dict[str, Any]] = []
        schema_results: list[CommandResult] = []

        for artifact_id, (path, schema) in sources.items():
            payload = self._read_json(path, findings, required=True)
            payloads[artifact_id] = payload
            schema_result = self.schema_validator.validate(schema=schema, instance=path)
            schema_results.append(schema_result)
            if not schema_result.ok:
                findings.extend(schema_result.findings)
            artifact_checks.append(
                {
                    "artifact_id": artifact_id,
                    "path": path,
                    "schema": schema,
                    "loaded": bool(payload),
                    "schema_valid": schema_result.ok,
                    "decision_status": payload.get("decision_status") if isinstance(payload, dict) else None,
                }
            )

        static_scan = self._static_no_network_scan()
        findings.extend(static_scan["findings"])
        semantic_checks = self._semantic_checks(payloads)
        findings.extend(semantic_checks["findings"])

        report = self._build_report(
            payloads=payloads,
            artifact_checks=artifact_checks,
            semantic_checks=semantic_checks["checks"],
            no_network_static_scan=static_scan["summary"],
            findings=findings,
        )
        report_schema = self.schema_validator.validate_payload(
            schema=self.options.validation_report_schema_path,
            payload=report,
            instance_label="secure_transport_validation_report",
        )
        if not report_schema.ok:
            findings.extend(report_schema.findings)

        blocking = _blocking(findings)
        report["blocking_findings_total"] = len(blocking)
        report["summary"]["blocking_findings_total"] = len(blocking)
        report["summary"]["report_schema_valid"] = report_schema.ok
        report["ok"] = not blocking
        report["findings"] = [finding.to_dict() for finding in findings]

        ok = not blocking
        return CommandResult(
            command="secure transport design validate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Secure transport design validator passed with no-network invariant." if ok else "Secure transport design validator blocked unsafe design drift.",
            data={
                "summary": report["summary"],
                "report": report,
                "artifact_checks": artifact_checks,
                "semantic_checks": semantic_checks["checks"],
                "no_network_static_scan": static_scan["summary"],
                "notes": [
                    "POST-H-023-D validates design artifacts only; it does not implement secure transport.",
                    "PASS means local-only-no-transport remains selected and no network primitive is introduced in src/devpilot_core/remote.",
                    "Future transport still requires a future enablement ADR, identity/RBAC/approval controls, secret lifecycle, replay protection and a dedicated implementation gate.",
                ],
            },
            findings=findings
            or [
                Finding(
                    "SECURE_TRANSPORT_DESIGN_VALIDATOR_PASS",
                    "Secure transport design remains design-only, local-only and no-network.",
                    Severity.INFO,
                    metadata=report["summary"],
                )
            ],
        )

    def _semantic_checks(self, payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
        findings: list[Finding] = []
        checks: list[dict[str, Any]] = []
        requirements = payloads.get("requirements", {})
        protocol = payloads.get("protocol_matrix", {})
        lifecycle = payloads.get("key_lifecycle", {})

        for artifact_id, payload in payloads.items():
            checks.append({"check_id": f"{artifact_id}.loaded", "ok": bool(payload)})
            if not payload:
                continue
            if payload.get("decision_status") != "design-only":
                findings.append(
                    Finding(
                        "SECURE_TRANSPORT_NOT_DESIGN_ONLY",
                        "Secure transport artifact must keep decision_status=design-only.",
                        Severity.BLOCK,
                        path=self._path_for_artifact(artifact_id),
                        metadata={"artifact_id": artifact_id, "decision_status": payload.get("decision_status")},
                    )
                )
            checks.append({"check_id": f"{artifact_id}.decision_status", "ok": payload.get("decision_status") == "design-only"})
            findings.extend(self._unsafe_flag_findings(artifact_id, payload))

        selected_requirements = requirements.get("selected_for_now")
        selected_protocol = protocol.get("selected_for_now")
        selected_ok = selected_requirements == "local-only-no-transport" and selected_protocol == "local-only-no-transport"
        checks.append({"check_id": "selected_for_now.local_only_no_transport", "ok": selected_ok})
        if not selected_ok:
            findings.append(
                Finding(
                    "SECURE_TRANSPORT_SELECTED_PROTOCOL_DRIFT",
                    "Secure transport design must keep selected_for_now=local-only-no-transport.",
                    Severity.BLOCK,
                    metadata={"requirements_selected": selected_requirements, "protocol_selected": selected_protocol},
                )
            )

        future_adr_ok = protocol.get("requires_future_enablement_adr") is True and lifecycle.get("requires_future_enablement_adr") is True
        checks.append({"check_id": "future_enablement_adr.required", "ok": future_adr_ok})
        if not future_adr_ok:
            findings.append(
                Finding(
                    "SECURE_TRANSPORT_FUTURE_ADR_REQUIRED",
                    "Future transport enablement must remain blocked by an explicit future ADR requirement.",
                    Severity.BLOCK,
                )
            )

        lifecycle_ok = lifecycle.get("lifecycle_status") == "design-only-no-material"
        checks.append({"check_id": "key_lifecycle.design_only_no_material", "ok": lifecycle_ok})
        if not lifecycle_ok:
            findings.append(
                Finding(
                    "SECURE_TRANSPORT_LIFECYCLE_MATERIAL_DRIFT",
                    "Key/certificate lifecycle must remain design-only-no-material.",
                    Severity.BLOCK,
                    path=self.options.key_lifecycle_path,
                    metadata={"lifecycle_status": lifecycle.get("lifecycle_status")},
                )
            )

        required_controls = set(requirements.get("required_controls_before_implementation", [])) if isinstance(requirements, dict) else set()
        controls_ok = _REQUIRED_CONTROLS.issubset(required_controls)
        checks.append(
            {
                "check_id": "required_controls.coverage",
                "ok": controls_ok,
                "required_total": len(_REQUIRED_CONTROLS),
                "present_total": len(_REQUIRED_CONTROLS.intersection(required_controls)),
            }
        )
        if not controls_ok:
            findings.append(
                Finding(
                    "SECURE_TRANSPORT_REQUIRED_CONTROLS_MISSING",
                    "Secure transport requirements are missing mandatory pre-implementation controls.",
                    Severity.BLOCK,
                    path=self.options.requirements_path,
                    metadata={"missing_controls": sorted(_REQUIRED_CONTROLS - required_controls)},
                )
            )

        matrix = protocol.get("decision_matrix") if isinstance(protocol, dict) else None
        matrix_items = matrix if isinstance(matrix, list) else []
        matrix_ok = bool(matrix_items) and all(item.get("implementation_allowed_now") is False for item in matrix_items if isinstance(item, dict))
        checks.append({"check_id": "protocol_matrix.no_current_implementation", "ok": matrix_ok, "protocols_total": len(matrix_items)})
        if not matrix_ok:
            findings.append(
                Finding(
                    "SECURE_TRANSPORT_PROTOCOL_IMPLEMENTATION_ALLOWED",
                    "Protocol decision matrix must not allow current implementation of any transport candidate.",
                    Severity.BLOCK,
                    path=self.options.protocol_matrix_path,
                )
            )

        phases = lifecycle.get("lifecycle_phases") if isinstance(lifecycle, dict) else None
        phase_items = phases if isinstance(phases, list) else []
        phases_ok = len(phase_items) >= 5 and all(item.get("implementation_allowed_now") is False and item.get("material_generated_now") is False for item in phase_items if isinstance(item, dict))
        checks.append({"check_id": "key_lifecycle.no_material_generation", "ok": phases_ok, "phases_total": len(phase_items)})
        if not phases_ok:
            findings.append(
                Finding(
                    "SECURE_TRANSPORT_KEY_LIFECYCLE_GENERATION_ALLOWED",
                    "Key lifecycle phases must not allow implementation or material generation now.",
                    Severity.BLOCK,
                    path=self.options.key_lifecycle_path,
                )
            )

        return {"checks": checks, "findings": findings}

    def _unsafe_flag_findings(self, artifact_id: str, payload: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        contexts: list[tuple[str, Any]] = [("top_level", payload)]
        for key in ("no_go_gates", "safety"):
            value = payload.get(key)
            if isinstance(value, dict):
                contexts.append((key, value))
        for context, values in contexts:
            if not isinstance(values, dict):
                continue
            for flag in _UNSAFE_FALSE_FLAGS:
                if flag in values and values.get(flag) is not False:
                    findings.append(
                        Finding(
                            "SECURE_TRANSPORT_UNSAFE_FLAG_BLOCKED",
                            "Secure transport design no-go flag must remain false.",
                            Severity.BLOCK,
                            path=self._path_for_artifact(artifact_id),
                            metadata={"artifact_id": artifact_id, "context": context, "flag": flag, "value": values.get(flag)},
                        )
                    )
        return findings

    def _static_no_network_scan(self) -> dict[str, Any]:
        findings: list[Finding] = []
        scanned_files: list[str] = []
        forbidden_hits: list[dict[str, str]] = []
        for raw_root in self.options.static_scan_roots:
            root = self._resolve(raw_root)
            if not root.exists():
                findings.append(Finding("SECURE_TRANSPORT_STATIC_SCAN_ROOT_MISSING", "Static no-network scan root is missing.", Severity.BLOCK, path=raw_root))
                continue
            paths = [root] if root.is_file() else sorted(root.rglob("*.py"))
            for path in paths:
                if "__pycache__" in path.parts:
                    continue
                rel = _relative(path, self.root)
                scanned_files.append(rel)
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
                except SyntaxError as exc:
                    findings.append(Finding("SECURE_TRANSPORT_STATIC_SCAN_SYNTAX_ERROR", "Python source could not be parsed for no-network invariant.", Severity.ERROR, path=rel, metadata={"error": str(exc)}))
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            root_name = alias.name.split(".", 1)[0]
                            if root_name in _FORBIDDEN_IMPORT_ROOTS:
                                forbidden_hits.append({"path": rel, "type": "import", "symbol": alias.name})
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        root_name = module.split(".", 1)[0]
                        if root_name in _FORBIDDEN_IMPORT_ROOTS:
                            forbidden_hits.append({"path": rel, "type": "import_from", "symbol": module})
                    elif isinstance(node, ast.Call):
                        name = _qualified_name(node.func)
                        if name in _FORBIDDEN_CALLS:
                            forbidden_hits.append({"path": rel, "type": "call", "symbol": name})
        for hit in forbidden_hits:
            findings.append(
                Finding(
                    "SECURE_TRANSPORT_FORBIDDEN_NETWORK_PRIMITIVE",
                    "Secure transport design package must not import or call active network primitives in POST-H-023-D.",
                    Severity.BLOCK,
                    path=hit["path"],
                    metadata={"type": hit["type"], "symbol": hit["symbol"]},
                )
            )
        return {
            "summary": {
                "scan_id": "secure-transport-no-network-static-scan",
                "scanned_roots": list(self.options.static_scan_roots),
                "scanned_files_total": len(scanned_files),
                "scanned_files": scanned_files,
                "forbidden_network_primitives_total": len(forbidden_hits),
                "forbidden_hits": forbidden_hits,
                "network_used": False,
                "external_api_used": False,
                "sockets_opened": False,
                "ok": not forbidden_hits and not _blocking(findings),
            },
            "findings": findings,
        }

    def _build_report(
        self,
        *,
        payloads: dict[str, dict[str, Any]],
        artifact_checks: list[dict[str, Any]],
        semantic_checks: list[dict[str, Any]],
        no_network_static_scan: dict[str, Any],
        findings: list[Finding],
    ) -> dict[str, Any]:
        requirements = payloads.get("requirements", {})
        protocol = payloads.get("protocol_matrix", {})
        lifecycle = payloads.get("key_lifecycle", {})
        no_go = _merged_no_go(requirements, protocol, lifecycle)
        blocking = _blocking(findings)
        summary = {
            "created_by": "POST-H-023-D",
            "status": "implemented-initial",
            "preliminary": True,
            "validator_status": "design-only-validator",
            "decision_status": "design-only",
            "selected_for_now": protocol.get("selected_for_now") or requirements.get("selected_for_now"),
            "lifecycle_status": lifecycle.get("lifecycle_status"),
            "schema_validations_total": len(artifact_checks),
            "schema_validations_passed": sum(1 for item in artifact_checks if item.get("schema_valid") is True),
            "artifact_checks_total": len(artifact_checks),
            "artifact_checks_passed": sum(1 for item in artifact_checks if item.get("loaded") and item.get("schema_valid")),
            "semantic_checks_total": len(semantic_checks),
            "semantic_checks_passed": sum(1 for item in semantic_checks if item.get("ok") is True),
            "no_network_static_scan_passed": no_network_static_scan.get("ok") is True,
            "forbidden_network_primitives_total": int(no_network_static_scan.get("forbidden_network_primitives_total", 0) or 0),
            "future_enablement_adr_required": protocol.get("requires_future_enablement_adr") is True and lifecycle.get("requires_future_enablement_adr") is True,
            "report_schema_valid": False,
            "blocking_findings_total": len(blocking),
            "reports_written": False,
            "read_only": True,
            "dry_run": True,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "external_api_used": False,
            "network_used": False,
            "sockets_opened": False,
            "transport_implemented": bool(no_go.get("transport_implemented", False)),
            "secure_transport_implemented": bool(no_go.get("secure_transport_implemented", False)),
            "network_allowed": bool(no_go.get("network_allowed", False)),
            "certificates_generated": bool(no_go.get("certificates_generated", False)),
            "certificate_authority_created": bool(no_go.get("certificate_authority_created", False)),
            "private_key_material_present": bool(no_go.get("private_key_material_present", False)),
            "raw_secret_storage_allowed": bool(no_go.get("raw_secret_storage_allowed", False)),
            "secrets_required": bool(no_go.get("secrets_required", False)),
            "secrets_stored": bool(no_go.get("secrets_stored", False)),
            "secrets_read": bool(no_go.get("secrets_read", False)),
            "remote_execution_enabled": bool(no_go.get("remote_execution_enabled", False)),
            "connector_write_enabled": bool(no_go.get("connector_write_enabled", False)),
            "plugin_execution_enabled": bool(no_go.get("plugin_execution_enabled", False)),
        }
        return {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-SECURE-TRANSPORT-VALIDATION-REPORT-V1",
            "report_id": "devpilot-secure-transport-validation-report",
            "created_by": "POST-H-023-D",
            "status": "implemented-initial",
            "generated_at_utc": _now_utc(),
            "ok": len(blocking) == 0,
            "decision_status": "design-only",
            "selected_for_now": summary["selected_for_now"],
            "lifecycle_status": summary["lifecycle_status"],
            "transport_implemented": summary["transport_implemented"],
            "secure_transport_implemented": summary["secure_transport_implemented"],
            "network_allowed": summary["network_allowed"],
            "network_used": summary["network_used"],
            "sockets_opened": summary["sockets_opened"],
            "certificates_generated": summary["certificates_generated"],
            "certificate_authority_created": summary["certificate_authority_created"],
            "private_key_material_present": summary["private_key_material_present"],
            "raw_secret_storage_allowed": summary["raw_secret_storage_allowed"],
            "secrets_required": summary["secrets_required"],
            "secrets_stored": summary["secrets_stored"],
            "secrets_read": summary["secrets_read"],
            "remote_execution_enabled": summary["remote_execution_enabled"],
            "connector_write_enabled": summary["connector_write_enabled"],
            "plugin_execution_enabled": summary["plugin_execution_enabled"],
            "blocking_findings_total": summary["blocking_findings_total"],
            "summary": summary,
            "artifacts": artifact_checks,
            "cross_checks": semantic_checks,
            "no_network_static_scan": no_network_static_scan,
            "findings": [finding.to_dict() for finding in findings],
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "secrets_read": False,
                "reports_written": False,
            },
            "notes": [
                "POST-H-023-D validator report is in-memory evidence unless a caller explicitly writes it under outputs/reports.",
                "Secure transport remains design-only and local-only; active transport remains blocked.",
            ],
        }

    def _read_json(self, path: str | Path, findings: list[Finding], *, required: bool) -> dict[str, Any]:
        resolved = self._resolve(path)
        if not resolved.exists():
            if required:
                findings.append(Finding("SECURE_TRANSPORT_SOURCE_MISSING", "Secure transport design source is missing.", Severity.BLOCK, path=_relative(resolved, self.root)))
            return {}
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("SECURE_TRANSPORT_SOURCE_INVALID_JSON", "Secure transport design source is invalid JSON.", Severity.ERROR, path=_relative(resolved, self.root), metadata={"error": str(exc)}))
            return {}
        if not isinstance(payload, dict):
            findings.append(Finding("SECURE_TRANSPORT_SOURCE_NOT_OBJECT", "Secure transport design source must be a JSON object.", Severity.ERROR, path=_relative(resolved, self.root)))
            return {}
        return payload

    def _path_for_artifact(self, artifact_id: str) -> str:
        return {
            "requirements": self.options.requirements_path,
            "protocol_matrix": self.options.protocol_matrix_path,
            "key_lifecycle": self.options.key_lifecycle_path,
        }.get(artifact_id, artifact_id)

    def _resolve(self, value: str | Path) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.root / path


class SecureTransportDesignQualityGate:
    """Hardening/industrial quality subgate for POST-H-023-D."""

    def __init__(self, root: Path, *, options: SecureTransportDesignQualityGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SecureTransportDesignQualityGateOptions()

    def run(self) -> CommandResult:
        validator_result = SecureTransportDesignValidator(self.root, options=self.options).validate()
        summary = dict(validator_result.data.get("summary", {})) if isinstance(validator_result.data, dict) else {}
        summary.update(
            {
                "created_by": "POST-H-023-D",
                "quality_gate_subgate": "secure-transport-design-only",
                "validator_ok": validator_result.ok,
                "reports_written": False,
            }
        )
        findings: list[Finding] = list(validator_result.findings)
        findings.extend(self._invariant_findings(summary))
        blocking = _blocking(findings)
        summary["blocking_findings_total"] = len(blocking)
        ok = not blocking
        return CommandResult(
            command="quality secure-transport-design-only",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Secure transport design-only quality gate passed." if ok else "Secure transport design-only quality gate blocked.",
            data={
                "summary": summary,
                "validator": validator_result.data,
                "notes": [
                    "POST-H-023-D integrates secure transport design validation into hardening/industrial quality gates.",
                    "The subgate is read-only and does not write reports, open network connections, generate certificates or read secrets.",
                    "The next micro-sprint POST-H-023-E remains responsible for the dedicated runbook and hito closure.",
                ],
            },
            findings=findings
            or [
                Finding(
                    "SECURE_TRANSPORT_QUALITY_GATE_PASS",
                    "Secure transport design-only quality gate confirms local-only no-network baseline.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _invariant_findings(self, summary: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        if summary.get("quality_gate_subgate") != "secure-transport-design-only":
            findings.append(Finding("SECURE_TRANSPORT_SUBGATE_ID_DRIFT", "Secure transport quality subgate id drifted from POST-H-023-D contract.", Severity.BLOCK))
        if summary.get("validator_ok") is not True:
            findings.append(Finding("SECURE_TRANSPORT_VALIDATOR_BLOCKED", "Secure transport quality gate requires validator_ok=true.", Severity.BLOCK))
        if summary.get("decision_status") != "design-only" or summary.get("selected_for_now") != "local-only-no-transport":
            findings.append(Finding("SECURE_TRANSPORT_GATE_DESIGN_ONLY_BLOCKED", "Secure transport quality gate requires design-only local-only-no-transport state.", Severity.BLOCK, metadata={"decision_status": summary.get("decision_status"), "selected_for_now": summary.get("selected_for_now")}))
        if summary.get("lifecycle_status") != "design-only-no-material":
            findings.append(Finding("SECURE_TRANSPORT_GATE_LIFECYCLE_BLOCKED", "Secure transport quality gate requires lifecycle_status=design-only-no-material.", Severity.BLOCK, metadata={"lifecycle_status": summary.get("lifecycle_status")}))
        if summary.get("report_schema_valid") is not True:
            findings.append(Finding("SECURE_TRANSPORT_REPORT_SCHEMA_BLOCKED", "Secure transport validation report schema must pass.", Severity.BLOCK))
        if summary.get("no_network_static_scan_passed") is not True:
            findings.append(Finding("SECURE_TRANSPORT_STATIC_NO_NETWORK_BLOCKED", "Secure transport no-network static scan must pass.", Severity.BLOCK))
        for flag in _UNSAFE_FALSE_FLAGS:
            if summary.get(flag) is True:
                findings.append(Finding("SECURE_TRANSPORT_GATE_UNSAFE_FLAG_BLOCKED", "Secure transport quality gate blocks unsafe flags.", Severity.BLOCK, metadata={"flag": flag}))
        for flag in ("reports_written", "mutations_performed", "source_mutations_performed", "external_api_used"):
            if summary.get(flag) is True:
                findings.append(Finding("SECURE_TRANSPORT_GATE_SIDE_EFFECT_BLOCKED", "Secure transport quality gate must remain read-only/local-only.", Severity.BLOCK, metadata={"flag": flag}))
        return findings


def _merged_no_go(*payloads: dict[str, Any]) -> dict[str, Any]:
    merged = {flag: False for flag in _UNSAFE_FALSE_FLAGS}
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        sources = [payload]
        for key in ("no_go_gates", "safety"):
            value = payload.get(key)
            if isinstance(value, dict):
                sources.append(value)
        for source in sources:
            for flag in _UNSAFE_FALSE_FLAGS:
                if source.get(flag) is True:
                    merged[flag] = True
    return merged


def _qualified_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


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


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
