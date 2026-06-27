from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

from .manifest_v2 import AuditPackV2BuildOptions, AuditPackV2Builder

POST_H_013_E_CREATED_BY = "POST-H-013-E"
AUDIT_PACK_INTEGRITY_GATE_COMMAND = "quality audit-pack-integrity"
_POLICY_PATH = ".devpilot/auditpack/audit_pack_policy.json"


@dataclass(frozen=True)
class AuditPackIntegrityGateOptions:
    """Options for the POST-H-013-E Audit Pack integrity subgate.

    The gate is intentionally read-only. It validates policy/no-go invariants,
    contract registration, runbook/disclaimer coverage and a dry-run build-v2
    execution path without creating audit pack ZIPs, writing source files,
    calling network services, using external APIs, signing remotely or using KMS.
    """

    require_runbook: bool = True
    require_crypto_docs: bool = True
    require_disclaimers: bool = True


class AuditPackIntegrityGate:
    """POST-H-013-E quality-gate subgate for audit pack integrity.

    This gate converts POST-H-013 A-D controls into a deterministic hardening
    signal. It does not build real packs, does not verify external evidence and
    does not read key material. Instead, it checks the local policy, dry-run
    builder behavior, documentation disclaimers and Test Contract Registry
    coverage needed to operate audit packs safely.
    """

    def __init__(self, root: Path, *, options: AuditPackIntegrityGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or AuditPackIntegrityGateOptions()

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        file_summary = self._check_required_files(findings)
        policy_summary = self._check_policy(findings)
        build_summary = self._dry_run_build_v2(findings)
        docs_summary = self._documentation_checks(findings)
        contract_summary = self._test_contract_checks(findings)

        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        summary = {
            "created_by": POST_H_013_E_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "quality_gate_ready": not blocking,
            "required_files_total": file_summary["required_files_total"],
            "required_files_existing_total": file_summary["required_files_existing_total"],
            "policy_path": _POLICY_PATH,
            "policy_ok": policy_summary["policy_ok"],
            "policy_no_go_gates_ok": policy_summary["no_go_gates_ok"],
            "policy_exclusions_ok": policy_summary["exclusions_ok"],
            "dry_run_builder_ok": build_summary["ok"],
            "dry_run_files_included": build_summary["files_included"],
            "dry_run_redaction_report_present": build_summary["redaction_report_present"],
            "dry_run_no_go_gates_ok": build_summary["no_go_gates_ok"],
            "docs_runbook_present": docs_summary["runbook_present"],
            "docs_build_verify_crypto_documented": docs_summary["build_verify_crypto_documented"],
            "docs_no_certification_disclaimer_present": docs_summary["no_certification_disclaimer_present"],
            "docs_received_pack_verification_documented": docs_summary["received_pack_verification_documented"],
            "test_contract_registered": contract_summary["v1_registered"],
            "test_contract_v2_registered": contract_summary["v2_registered"],
            "blocking_findings_total": len(blocking),
            "findings_total": len(findings),
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "remote_kms_used": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
        }
        ok = not blocking
        return CommandResult(
            command=AUDIT_PACK_INTEGRITY_GATE_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else self._exit_code(findings),
            message="Audit pack integrity gate passed." if ok else "Audit pack integrity gate blocked.",
            data={
                "summary": summary,
                "required_files": file_summary["files"],
                "policy_summary": policy_summary,
                "dry_run_summary": build_summary,
                "documentation_summary": docs_summary,
                "contract_summary": contract_summary,
                "notes": [
                    "POST-H-013-E binds audit-pack-integrity to hardening/industrial quality-gate profiles.",
                    "The subgate validates policy/no-go invariants and build-v2 dry-run behavior without writing audit packs.",
                    "Audit packs are local evidence artifacts, not compliance certification or enterprise assurance claims.",
                ],
            },
            findings=findings or [Finding("AUDIT_PACK_INTEGRITY_GATE_PASS", "Audit pack integrity checks passed.", Severity.INFO, metadata=summary)],
        )

    def _check_required_files(self, findings: list[Finding]) -> dict[str, Any]:
        required = [
            _POLICY_PATH,
            "docs/schemas/audit_pack_manifest_v2.schema.json",
            "docs/schemas/audit_pack_integrity_report.schema.json",
            "src/devpilot_core/auditpack/manifest_v2.py",
            "src/devpilot_core/auditpack/redaction.py",
            "src/devpilot_core/auditpack/verify_v2.py",
            "src/devpilot_core/auditpack/crypto.py",
            "src/devpilot_core/auditpack/gate.py",
            "docs/05_operations/audit_pack_runbook.md",
            "docs/05_operations/runbook.md",
            "docs/backlogs/POST-H-013_audit_pack_integrity.md",
            "docs/POST-H-013_audit_pack_integrity.md",
            "docs/post_h_013_e_manifest.json",
            "docs/audits/post_h_013_e_quality_gate_runbook_disclaimers_report.md",
            "tests/test_post_h_013_audit_pack_integrity.py",
        ]
        records: list[dict[str, Any]] = []
        for rel in required:
            exists = (self.root / rel).exists()
            records.append({"path": rel, "exists": exists})
            if not exists:
                findings.append(Finding("AUDIT_PACK_INTEGRITY_REQUIRED_FILE_MISSING", "Audit pack integrity required file is missing.", Severity.BLOCK, path=rel))
        return {"required_files_total": len(records), "required_files_existing_total": sum(1 for item in records if item["exists"]), "files": records}

    def _check_policy(self, findings: list[Finding]) -> dict[str, Any]:
        path = self.root / _POLICY_PATH
        payload: dict[str, Any] = {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            findings.append(Finding("AUDIT_PACK_INTEGRITY_POLICY_MISSING", "Audit pack policy is missing.", Severity.BLOCK, path=_POLICY_PATH))
            return {"policy_ok": False, "no_go_gates_ok": False, "exclusions_ok": False, "missing_policy_keys": [], "missing_exclusions": []}
        except json.JSONDecodeError as exc:
            findings.append(Finding("AUDIT_PACK_INTEGRITY_POLICY_JSON_INVALID", "Audit pack policy JSON is invalid.", Severity.ERROR, path=_POLICY_PATH, metadata={"error": str(exc)}))
            return {"policy_ok": False, "no_go_gates_ok": False, "exclusions_ok": False, "missing_policy_keys": [], "missing_exclusions": []}

        expected_flags = {
            "local_first": True,
            "dry_run_default": True,
            "optional_crypto": True,
            "compliance_certification_claimed": False,
            "remote_export_allowed": False,
            "network_required": False,
            "external_api_required": False,
        }
        missing_policy_keys: list[str] = []
        for key, expected in expected_flags.items():
            if payload.get(key) is not expected:
                missing_policy_keys.append(key)
                findings.append(Finding("AUDIT_PACK_INTEGRITY_POLICY_FLAG_INVALID", "Audit pack policy safety flag is invalid.", Severity.BLOCK, path=_POLICY_PATH, metadata={"key": key, "expected": expected, "actual": payload.get(key)}))

        safety = payload.get("safety") if isinstance(payload.get("safety"), dict) else {}
        expected_safety = {
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "remote_signing_enabled": False,
            "remote_kms_enabled": False,
        }
        for key, expected in expected_safety.items():
            if safety.get(key) is not expected:
                missing_policy_keys.append(f"safety.{key}")
                findings.append(Finding("AUDIT_PACK_INTEGRITY_POLICY_NO_GO_INVALID", "Audit pack policy no-go gate flag is invalid.", Severity.BLOCK, path=_POLICY_PATH, metadata={"key": key, "expected": expected, "actual": safety.get(key)}))

        redaction = payload.get("redaction") if isinstance(payload.get("redaction"), dict) else {}
        if redaction.get("redaction_report_required") is not True or redaction.get("raw_secret_export_policy") != "block":
            findings.append(Finding("AUDIT_PACK_INTEGRITY_POLICY_REDACTION_INVALID", "Audit pack policy must require redaction report and block raw secret export.", Severity.BLOCK, path=_POLICY_PATH, metadata={"redaction": redaction}))

        crypto = payload.get("crypto") if isinstance(payload.get("crypto"), dict) else {}
        if crypto.get("remote_kms_allowed") is not False or crypto.get("keys_in_repo_allowed") is not False:
            findings.append(Finding("AUDIT_PACK_INTEGRITY_POLICY_CRYPTO_INVALID", "Audit pack policy must deny remote KMS and repo-stored keys.", Severity.BLOCK, path=_POLICY_PATH, metadata={"crypto": crypto}))

        exclusions = {str(item) for item in payload.get("exclude_patterns", [])}
        required_exclusions = {
            "outputs/**",
            ".devpilot/devpilot.db",
            ".devpilot/agent_sessions/**",
            ".env",
            ".env.*",
            "**/*.pem",
            "**/*.key",
            ".git/**",
        }
        missing_exclusions = sorted(required_exclusions - exclusions)
        for item in missing_exclusions:
            findings.append(Finding("AUDIT_PACK_INTEGRITY_POLICY_EXCLUSION_MISSING", "Audit pack policy is missing a required exclusion.", Severity.BLOCK, path=_POLICY_PATH, metadata={"missing_exclusion": item}))

        return {
            "policy_ok": not missing_policy_keys and not missing_exclusions,
            "no_go_gates_ok": all(safety.get(key) is value for key, value in expected_safety.items()),
            "exclusions_ok": not missing_exclusions,
            "missing_policy_keys": missing_policy_keys,
            "missing_exclusions": missing_exclusions,
        }

    def _dry_run_build_v2(self, findings: list[Finding]) -> dict[str, Any]:
        result = AuditPackV2Builder(self.root).build(AuditPackV2BuildOptions(dry_run=True, execute=False))
        findings.extend(self._prefixed_findings(result, prefix="AUDIT_PACK_INTEGRITY_BUILD_V2"))
        summary = result.data.get("summary", {}) if isinstance(result.data, dict) else {}
        checks = {
            "dry_run": summary.get("dry_run") is True,
            "execute": summary.get("execute") is False,
            "pack_path_absent": summary.get("pack_path") is None,
            "redaction_report_present": summary.get("redaction_report_present") is True,
            "redaction_passed": summary.get("redaction_passed") is True,
            "secrets_detected_zero": summary.get("secrets_detected") == 0,
            "compliance_certification_claimed_false": summary.get("compliance_certification_claimed") is False,
            "network_used_false": summary.get("network_used") is False,
            "external_api_used_false": summary.get("external_api_used") is False,
            "remote_export_used_false": summary.get("remote_export_used") is False,
            "runtime_db_exported_false": summary.get("runtime_db_exported") is False,
            "agent_sessions_exported_false": summary.get("agent_sessions_exported") is False,
            "env_files_exported_false": summary.get("env_files_exported") is False,
            "remote_execution_enabled_false": summary.get("remote_execution_enabled") is False,
            "connector_write_enabled_false": summary.get("connector_write_enabled") is False,
            "plugin_execution_enabled_false": summary.get("plugin_execution_enabled") is False,
        }
        for check, ok in checks.items():
            if not ok:
                findings.append(Finding("AUDIT_PACK_INTEGRITY_DRY_RUN_NO_GO_FAILED", "Audit pack dry-run build-v2 no-go check failed.", Severity.BLOCK, metadata={"check": check, "summary_value": summary.get(check)}))
        return {
            "ok": bool(result.ok) and all(checks.values()),
            "exit_code": int(result.exit_code),
            "files_included": summary.get("files_included", 0),
            "redaction_report_present": bool(summary.get("redaction_report_present")),
            "no_go_gates_ok": all(checks.values()),
            "checks": checks,
        }

    def _documentation_checks(self, findings: list[Finding]) -> dict[str, Any]:
        paths = [
            "docs/05_operations/audit_pack_runbook.md",
            "docs/05_operations/runbook.md",
            "docs/backlogs/POST-H-013_audit_pack_integrity.md",
            "docs/POST-H-013_audit_pack_integrity.md",
            "docs/03_security/post_h_security_risk_register.md",
        ]
        contents = {rel: (self.root / rel).read_text(encoding="utf-8") if (self.root / rel).exists() else "" for rel in paths}
        combined = "\n".join(contents.values()).lower()
        required_terms = {
            "build_v2": "audit-pack build-v2",
            "verify_v2": "audit-pack verify-v2",
            "sign_optional": "--sign optional",
            "encrypt_optional": "--encrypt optional",
            "redaction_report": "redaction_report",
            "integrity_report": "integrity report",
            "compliance_false": "compliance_certification_claimed=false",
            "no_certification": "no-certificación",
            "no_third_party_default": "no se recomienda subir packs a terceros por defecto",
            "received_pack": "pack recibido",
            "quality_gate": "audit-pack-integrity",
        }
        missing = [key for key, term in required_terms.items() if term not in combined]
        for key in missing:
            findings.append(Finding("AUDIT_PACK_INTEGRITY_DOCUMENTATION_TERM_MISSING", "Audit pack operational documentation is missing a required term.", Severity.BLOCK, metadata={"term_key": key, "expected": required_terms[key]}))
        return {
            "runbook_present": bool(contents["docs/05_operations/audit_pack_runbook.md"]),
            "build_verify_crypto_documented": all(key not in missing for key in ["build_v2", "verify_v2", "sign_optional", "encrypt_optional"]),
            "no_certification_disclaimer_present": all(key not in missing for key in ["compliance_false", "no_certification"]),
            "received_pack_verification_documented": "received_pack" not in missing,
            "missing_terms": missing,
        }

    def _test_contract_checks(self, findings: list[Finding]) -> dict[str, Any]:
        v1 = self._load_json(".devpilot/testing/test_contract_registry.json")
        v2 = self._load_json(".devpilot/testing/test_contract_registry_v2.json")
        v1_contract = self._find_contract(v1, "post-h-013-audit-pack-integrity-gate")
        v2_contract = self._find_contract(v2, "post-h-013-audit-pack-integrity-gate")
        if not v1_contract:
            findings.append(Finding("AUDIT_PACK_INTEGRITY_TCR_CONTRACT_MISSING", "TCR v1 does not register POST-H-013-E audit-pack-integrity gate.", Severity.BLOCK, path=".devpilot/testing/test_contract_registry.json"))
        if not v2_contract:
            findings.append(Finding("AUDIT_PACK_INTEGRITY_TCR_V2_CONTRACT_MISSING", "TCR v2 does not register POST-H-013-E audit-pack-integrity gate.", Severity.BLOCK, path=".devpilot/testing/test_contract_registry_v2.json"))
        return {"v1_registered": bool(v1_contract), "v2_registered": bool(v2_contract)}

    def _load_json(self, rel: str) -> dict[str, Any]:
        try:
            payload = json.loads((self.root / rel).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _find_contract(payload: dict[str, Any], contract_id: str) -> dict[str, Any] | None:
        for item in payload.get("contracts", []):
            if isinstance(item, dict) and item.get("contract_id") == contract_id:
                return item
        return None

    @staticmethod
    def _prefixed_findings(result: CommandResult, *, prefix: str) -> list[Finding]:
        prefixed: list[Finding] = []
        for finding in result.findings:
            severity = finding.severity
            if severity == Severity.INFO:
                continue
            prefixed.append(
                Finding(
                    id=f"{prefix}_{finding.id}",
                    message=finding.message,
                    severity=severity,
                    path=finding.path,
                    metadata={"source_command": result.command, "source_finding_id": finding.id, **(finding.metadata or {})},
                )
            )
        return prefixed

    @staticmethod
    def _exit_code(findings: list[Finding]) -> ExitCode:
        severities = {finding.severity for finding in findings}
        if Severity.ERROR in severities:
            return ExitCode.ERROR
        if Severity.BLOCK in severities:
            return ExitCode.BLOCK
        if Severity.FAIL in severities:
            return ExitCode.FAIL
        return ExitCode.PASS
