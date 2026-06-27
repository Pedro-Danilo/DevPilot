from __future__ import annotations

import copy
import hashlib
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy.path_guard import PathGuard
from devpilot_core.schemas import SchemaValidator

from .crypto import AuditPackCryptoOptions, decrypt_bytes, json_bytes as crypto_json_bytes, load_local_key_material, verify_signature

MANIFEST_V2_NAME = "audit-pack-manifest-v2.json"
REDACTION_REPORT_NAME = "redaction_report.json"
POST_H_013_C_CREATED_BY = "POST-H-013-C"
_DEFAULT_OUTPUT_DIR = "outputs/auditpacks"
_DEFAULT_MANIFEST_HASH_PLACEHOLDER = "0" * 64


@dataclass(frozen=True)
class AuditPackV2VerifyOptions:
    """Options for POST-H-013-C audit pack v2 verification.

    The verifier is local-first and read-only against repository source files. It
    may write an integrity report under ``outputs/auditpacks`` as runtime
    evidence; it never mutates source artifacts, does not call network services
    and does not require external APIs.
    """

    pack: str
    output_dir: str = _DEFAULT_OUTPUT_DIR
    write_integrity_report: bool = True
    signature: str | None = None
    encrypted_pack: str | None = None
    crypto_keyfile: str | None = None
    crypto_passphrase_env: str | None = None


class AuditPackV2Verifier:
    """Verify Audit Pack Manifest v2 evidence locally.

    POST-H-013-C validates the embedded manifest against the registered schema,
    checks the manifest self-hash, verifies SHA-256 for every declared included
    file, detects missing members, detects extra undeclared ZIP members and
    fails closed on forbidden compliance/security flags. Signing and encryption
    remain explicit later-sprint concerns.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.path_guard = PathGuard(self.root)
        self.schema_validator = SchemaValidator(self.root)

    def verify(self, options: AuditPackV2VerifyOptions) -> CommandResult:
        findings: list[Finding] = []
        crypto_options = AuditPackCryptoOptions(
            sign_mode="optional" if options.signature else "none",
            encrypt_mode="optional" if options.encrypted_pack else "none",
            keyfile=options.crypto_keyfile,
            passphrase_env=options.crypto_passphrase_env,
        )
        key_material = load_local_key_material(self.root, crypto_options)
        if (options.signature or options.encrypted_pack) and not key_material.available:
            findings.extend(key_material.findings)
        input_path = Path(options.pack)
        absolute = input_path if input_path.is_absolute() else self.root / input_path
        absolute = absolute.resolve()
        rel = _relative_or_none(absolute, self.root)
        if rel is None:
            finding = Finding(
                "AUDIT_PACK_V2_VERIFY_PATH_OUTSIDE_ROOT_BLOCKED",
                "Audit pack v2 verification path is outside the governed workspace root.",
                Severity.BLOCK,
                path=str(input_path),
            )
            report = _integrity_report(pack_id="unknown", status="blocked", findings=[finding])
            return CommandResult(
                "audit-pack verify-v2",
                False,
                ExitCode.BLOCK,
                "Audit pack v2 verification blocked by PathGuard.",
                data={"summary": _summary(options, rel=str(input_path), report=report, report_path=None), "integrity_report": report},
                findings=[finding],
            )

        decision = self.path_guard.evaluate(rel, action="read")
        if decision.effect.value == "block":
            finding = decision.to_finding()
            report = _integrity_report(pack_id="unknown", status="blocked", findings=[finding])
            return CommandResult(
                "audit-pack verify-v2",
                False,
                ExitCode.BLOCK,
                "Audit pack v2 verification blocked by PathGuard.",
                data={"summary": _summary(options, rel=rel, report=report, report_path=None), "integrity_report": report},
                findings=[finding],
            )

        manifest: dict[str, Any] | None = None
        redaction_report: dict[str, Any] | None = None
        pack_id = "unknown"
        zip_valid = False
        manifest_present = False
        redaction_report_present = False
        files_total = 0
        files_verified = 0
        missing_files: list[str] = []
        hash_mismatches: list[dict[str, str]] = []
        extra_files: list[str] = []
        schema_valid = False
        manifest_hash_valid = False
        pack_bytes: bytes | None = None

        if not absolute.exists() or not absolute.is_file():
            findings.append(Finding("AUDIT_PACK_V2_MISSING", "Audit pack v2 ZIP does not exist.", Severity.BLOCK, path=rel))
            report = _integrity_report(pack_id=pack_id, status="blocked", findings=findings, missing_files=missing_files, hash_mismatches=hash_mismatches)
            report_path = self._write_report(options, report)
            return self._result(options, rel, report, report_path, zip_valid, manifest_present, redaction_report_present, schema_valid, manifest_hash_valid, findings)

        try:
            pack_bytes = absolute.read_bytes()
            with zipfile.ZipFile(absolute, "r") as archive:
                names = set(archive.namelist())
                zip_valid = True
                if MANIFEST_V2_NAME not in names:
                    findings.append(Finding("AUDIT_PACK_V2_MANIFEST_MISSING", "Audit pack manifest v2 is missing from ZIP.", Severity.BLOCK, path=MANIFEST_V2_NAME))
                else:
                    manifest_present = True
                    manifest = json.loads(archive.read(MANIFEST_V2_NAME).decode("utf-8"))
                    if isinstance(manifest, dict):
                        pack_id = str(manifest.get("pack_id") or "unknown")
                        schema_result = self.schema_validator.validate_payload(
                            schema="AuditPackManifestV2",
                            payload=manifest,
                            instance_label=f"{rel}:{MANIFEST_V2_NAME}",
                        )
                        schema_valid = schema_result.ok
                        if not schema_result.ok:
                            findings.append(
                                Finding(
                                    "AUDIT_PACK_V2_MANIFEST_SCHEMA_INVALID",
                                    "Audit pack manifest v2 does not validate against AuditPackManifestV2 schema.",
                                    Severity.BLOCK,
                                    path=MANIFEST_V2_NAME,
                                    metadata={"schema_findings": [item.to_dict() for item in schema_result.findings]},
                                )
                            )
                        manifest_hash_valid = _verify_manifest_hash(manifest)
                        if not manifest_hash_valid:
                            findings.append(
                                Finding(
                                    "AUDIT_PACK_V2_MANIFEST_HASH_MISMATCH",
                                    "Audit pack manifest self-hash does not match canonical manifest content.",
                                    Severity.BLOCK,
                                    path=MANIFEST_V2_NAME,
                                    metadata={"expected_sha256": manifest.get("integrity", {}).get("manifest_hash")},
                                )
                            )
                        findings.extend(_safety_findings(manifest))
                        files = manifest.get("files")
                        if not isinstance(files, list):
                            files = []
                            findings.append(Finding("AUDIT_PACK_V2_MANIFEST_FILES_INVALID", "Audit pack manifest files section is invalid.", Severity.BLOCK, path=MANIFEST_V2_NAME))
                        files_total = len(files)
                        declared_paths = {str(item.get("path", "")) for item in files if isinstance(item, dict)}
                        extra_files = sorted(names - declared_paths - {MANIFEST_V2_NAME})
                        for extra in extra_files:
                            findings.append(
                                Finding(
                                    "AUDIT_PACK_V2_EXTRA_MEMBER_BLOCKED",
                                    "Audit pack v2 ZIP contains an undeclared member not listed in manifest v2.",
                                    Severity.BLOCK,
                                    path=extra,
                                )
                            )
                        for item in files:
                            if not isinstance(item, dict):
                                findings.append(Finding("AUDIT_PACK_V2_FILE_ENTRY_INVALID", "Audit pack manifest contains an invalid file entry.", Severity.BLOCK, path=MANIFEST_V2_NAME))
                                continue
                            entry_path = str(item.get("path") or "")
                            expected_sha = str(item.get("sha256") or "")
                            invalid_reason = _invalid_member_reason(entry_path)
                            if invalid_reason:
                                findings.append(
                                    Finding(
                                        "AUDIT_PACK_V2_FORBIDDEN_MEMBER_BLOCKED",
                                        "Audit pack v2 manifest declares a forbidden member path.",
                                        Severity.BLOCK,
                                        path=entry_path or MANIFEST_V2_NAME,
                                        metadata={"reason": invalid_reason},
                                    )
                                )
                            if not entry_path or entry_path not in names:
                                missing_files.append(entry_path or "<empty-path>")
                                findings.append(
                                    Finding(
                                        "AUDIT_PACK_V2_ENTRY_MISSING",
                                        "Audit pack v2 declared file is missing from ZIP.",
                                        Severity.BLOCK,
                                        path=entry_path or MANIFEST_V2_NAME,
                                    )
                                )
                                continue
                            raw = archive.read(entry_path)
                            actual_sha = _sha256_bytes(raw)
                            if actual_sha != expected_sha:
                                mismatch = {"path": entry_path, "expected_sha256": expected_sha, "actual_sha256": actual_sha}
                                hash_mismatches.append(mismatch)
                                findings.append(
                                    Finding(
                                        "AUDIT_PACK_V2_HASH_MISMATCH",
                                        "Audit pack v2 file hash does not match manifest v2.",
                                        Severity.BLOCK,
                                        path=entry_path,
                                        metadata=mismatch,
                                    )
                                )
                            else:
                                files_verified += 1
                        if REDACTION_REPORT_NAME in names:
                            redaction_report_present = True
                            try:
                                payload = json.loads(archive.read(REDACTION_REPORT_NAME).decode("utf-8"))
                                redaction_report = payload if isinstance(payload, dict) else None
                            except json.JSONDecodeError as exc:
                                findings.append(Finding("AUDIT_PACK_V2_REDACTION_REPORT_JSON_INVALID", "Audit pack v2 redaction report JSON is invalid.", Severity.BLOCK, path=REDACTION_REPORT_NAME, metadata={"error": str(exc)}))
                        else:
                            findings.append(Finding("AUDIT_PACK_V2_REDACTION_REPORT_MISSING", "Audit pack v2 redaction report is missing from ZIP.", Severity.BLOCK, path=REDACTION_REPORT_NAME))
                    else:
                        findings.append(Finding("AUDIT_PACK_V2_MANIFEST_INVALID", "Audit pack manifest v2 root must be an object.", Severity.BLOCK, path=MANIFEST_V2_NAME))
        except zipfile.BadZipFile:
            findings.append(Finding("AUDIT_PACK_V2_ZIP_INVALID", "Audit pack v2 path is not a valid ZIP file.", Severity.BLOCK, path=rel))
        except json.JSONDecodeError as exc:
            findings.append(Finding("AUDIT_PACK_V2_MANIFEST_JSON_INVALID", "Audit pack manifest v2 JSON is invalid.", Severity.ERROR, path=MANIFEST_V2_NAME, metadata={"error": str(exc)}))
        except OSError as exc:
            findings.append(Finding("AUDIT_PACK_V2_VERIFY_IO_ERROR", "Audit pack v2 verification could not read ZIP content.", Severity.ERROR, path=rel, metadata={"error": str(exc)}))

        redaction_passed = bool(manifest.get("redaction", {}).get("redaction_passed", False)) if isinstance(manifest, dict) else False
        secrets_detected = int(manifest.get("redaction", {}).get("secrets_detected", 0)) if isinstance(manifest, dict) else 0
        if isinstance(redaction_report, dict):
            redaction_passed = redaction_passed and bool(redaction_report.get("redaction_passed", False))
            secrets_detected = max(secrets_detected, int(redaction_report.get("secrets_detected", 0)))
        if not redaction_passed:
            findings.append(Finding("AUDIT_PACK_V2_REDACTION_NOT_PASSED", "Audit pack v2 redaction status is not passed.", Severity.BLOCK, path=REDACTION_REPORT_NAME))
        if secrets_detected > 0:
            findings.append(Finding("AUDIT_PACK_V2_SECRETS_DETECTED_BLOCKED", "Audit pack v2 declares detected secrets and must not pass verification.", Severity.BLOCK, path=REDACTION_REPORT_NAME, metadata={"secrets_detected": secrets_detected}))

        crypto_status = self._verify_optional_crypto(
            options=options,
            pack_bytes=pack_bytes,
            pack_rel=rel,
            key=key_material.value,
            key_fingerprint=key_material.fingerprint,
        )
        findings.extend(crypto_status["findings"])

        status = "passed" if _verification_ok(findings, zip_valid, manifest_present, schema_valid, manifest_hash_valid, files_total, files_verified) else "blocked"
        report = _integrity_report(
            pack_id=pack_id,
            status=status,
            files_total=files_total,
            files_verified=files_verified,
            missing_files=missing_files,
            hash_mismatches=hash_mismatches,
            redaction_passed=redaction_passed,
            secrets_detected=secrets_detected,
            encryption_used=bool(manifest.get("integrity", {}).get("encrypted", False)) or bool(crypto_status["encryption_used"]) if isinstance(manifest, dict) else bool(crypto_status["encryption_used"]),
            signature_verified=crypto_status["signature_verified"],
            crypto_status=crypto_status,
            findings=findings,
            extra_files=extra_files,
            schema_valid=schema_valid,
            manifest_hash_valid=manifest_hash_valid,
        )
        report_path = self._write_report(options, report)
        return self._result(options, rel, report, report_path, zip_valid, manifest_present, redaction_report_present, schema_valid, manifest_hash_valid, findings)


    def _verify_optional_crypto(
        self,
        *,
        options: AuditPackV2VerifyOptions,
        pack_bytes: bytes | None,
        pack_rel: str,
        key: bytes | None,
        key_fingerprint: str | None,
    ) -> dict[str, Any]:
        findings: list[Finding] = []
        status: dict[str, Any] = {
            "created_by": "POST-H-013-D",
            "status": "implemented-initial",
            "signature_provided": bool(options.signature),
            "signature_verified": None,
            "encryption_artifact_provided": bool(options.encrypted_pack),
            "encryption_used": bool(options.encrypted_pack),
            "encryption_verified": None,
            "key_fingerprint_sha256_16": key_fingerprint,
            "network_used": False,
            "external_api_used": False,
            "remote_kms_used": False,
            "findings": findings,
        }
        if pack_bytes is None:
            return status
        if options.signature:
            if not key:
                findings.append(
                    Finding(
                        "AUDIT_PACK_CRYPTO_SIGNATURE_KEY_MISSING",
                        "Audit pack signature verification requires explicit local key material.",
                        Severity.BLOCK,
                        path=options.signature,
                    )
                )
            else:
                signature_payload, signature_finding = self._read_json_sidecar(options.signature, label="signature")
                if signature_finding is not None:
                    findings.append(signature_finding)
                elif signature_payload is not None:
                    verified = verify_signature(pack_bytes, key=key, signature_report=signature_payload)
                    status["signature_verified"] = verified
                    if not verified:
                        findings.append(
                            Finding(
                                "AUDIT_PACK_CRYPTO_SIGNATURE_INVALID",
                                "Audit pack local signature sidecar does not match the provided pack and key material.",
                                Severity.BLOCK,
                                path=options.signature,
                            )
                        )
        if options.encrypted_pack:
            if not key:
                findings.append(
                    Finding(
                        "AUDIT_PACK_CRYPTO_DECRYPT_KEY_MISSING",
                        "Audit pack encrypted artifact verification requires explicit local key material.",
                        Severity.BLOCK,
                        path=options.encrypted_pack,
                    )
                )
            else:
                encrypted_bytes, encrypted_finding = self._read_binary_sidecar(options.encrypted_pack, label="encrypted-pack")
                if encrypted_finding is not None:
                    findings.append(encrypted_finding)
                elif encrypted_bytes is not None:
                    decrypted, decrypt_finding = decrypt_bytes(encrypted_bytes, key=key)
                    if decrypt_finding is not None:
                        findings.append(decrypt_finding)
                    if decrypted is not None:
                        verified = decrypted == pack_bytes
                        status["encryption_verified"] = verified
                        if not verified:
                            findings.append(
                                Finding(
                                    "AUDIT_PACK_CRYPTO_ENCRYPTION_MISMATCH",
                                    "Audit pack encrypted artifact decrypts but does not match the plain pack bytes.",
                                    Severity.BLOCK,
                                    path=options.encrypted_pack,
                                    metadata={"pack_path": pack_rel},
                                )
                            )
        return status

    def _read_json_sidecar(self, path_value: str, *, label: str) -> tuple[dict[str, Any] | None, Finding | None]:
        raw, finding = self._read_binary_sidecar(path_value, label=label)
        if finding is not None or raw is None:
            return None, finding
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            return None, Finding(
                "AUDIT_PACK_CRYPTO_SIDECAR_JSON_INVALID",
                "Audit pack crypto sidecar JSON is invalid.",
                Severity.BLOCK,
                path=path_value,
                metadata={"label": label, "error": str(exc)},
            )
        if not isinstance(payload, dict):
            return None, Finding(
                "AUDIT_PACK_CRYPTO_SIDECAR_INVALID",
                "Audit pack crypto sidecar root must be an object.",
                Severity.BLOCK,
                path=path_value,
                metadata={"label": label},
            )
        return payload, None

    def _read_binary_sidecar(self, path_value: str, *, label: str) -> tuple[bytes | None, Finding | None]:
        input_path = Path(path_value)
        absolute = input_path if input_path.is_absolute() else self.root / input_path
        absolute = absolute.resolve()
        rel = _relative_or_none(absolute, self.root)
        if rel is None:
            return None, Finding(
                "AUDIT_PACK_CRYPTO_SIDECAR_OUTSIDE_ROOT_BLOCKED",
                "Audit pack crypto sidecar must be inside the governed workspace root.",
                Severity.BLOCK,
                path=path_value,
                metadata={"label": label},
            )
        decision = self.path_guard.evaluate(rel, action="read")
        if decision.effect.value == "block":
            return None, decision.to_finding()
        if not absolute.exists() or not absolute.is_file():
            return None, Finding(
                "AUDIT_PACK_CRYPTO_SIDECAR_MISSING",
                "Audit pack crypto sidecar does not exist.",
                Severity.BLOCK,
                path=rel,
                metadata={"label": label},
            )
        try:
            return absolute.read_bytes(), None
        except OSError as exc:
            return None, Finding(
                "AUDIT_PACK_CRYPTO_SIDECAR_READ_ERROR",
                "Audit pack crypto sidecar could not be read.",
                Severity.BLOCK,
                path=rel,
                metadata={"label": label, "error": str(exc)},
            )

    def _write_report(self, options: AuditPackV2VerifyOptions, report: dict[str, Any]) -> str | None:
        if not options.write_integrity_report:
            return None
        output_dir = (self.root / options.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_pack_id = _safe_filename(str(report.get("pack_id") or "unknown"))
        path = output_dir / f"{safe_pack_id}_integrity_report.json"
        path.write_bytes(_json_bytes(report))
        return path.relative_to(self.root).as_posix()

    def _result(
        self,
        options: AuditPackV2VerifyOptions,
        rel: str,
        report: dict[str, Any],
        report_path: str | None,
        zip_valid: bool,
        manifest_present: bool,
        redaction_report_present: bool,
        schema_valid: bool,
        manifest_hash_valid: bool,
        findings: list[Finding],
    ) -> CommandResult:
        ok = report["status"] == "passed"
        summary = _summary(
            options,
            rel=rel,
            report=report,
            report_path=report_path,
            zip_valid=zip_valid,
            manifest_present=manifest_present,
            redaction_report_present=redaction_report_present,
            schema_valid=schema_valid,
            manifest_hash_valid=manifest_hash_valid,
        )
        if ok and not findings:
            findings = [
                Finding(
                    "AUDIT_PACK_V2_VERIFY_PASS",
                    "Audit pack v2 manifest schema, checksums, declared files and redaction evidence verified locally.",
                    Severity.INFO,
                    path=rel,
                    metadata={"files_verified": report["files_verified"], "report_path": report_path},
                )
            ]
        return CommandResult(
            "audit-pack verify-v2",
            ok,
            ExitCode.PASS if ok else _exit_code_from_findings(findings),
            "Audit pack v2 verification passed." if ok else "Audit pack v2 verification failed or blocked.",
            data={"summary": summary, "integrity_report": report},
            findings=findings,
        )


def _summary(
    options: AuditPackV2VerifyOptions,
    *,
    rel: str,
    report: dict[str, Any],
    report_path: str | None,
    zip_valid: bool = False,
    manifest_present: bool = False,
    redaction_report_present: bool = False,
    schema_valid: bool = False,
    manifest_hash_valid: bool = False,
    crypto_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "created_by": POST_H_013_C_CREATED_BY,
        "status": report.get("status", "blocked"),
        "preliminary": True,
        "pack_path": rel,
        "pack_id": report.get("pack_id"),
        "zip_valid": zip_valid,
        "manifest_present": manifest_present,
        "manifest_schema_valid": schema_valid,
        "manifest_hash_valid": manifest_hash_valid,
        "redaction_report_present": redaction_report_present,
        "files_total": report.get("files_total", 0),
        "files_verified": report.get("files_verified", 0),
        "files_failed": report.get("files_failed", 0),
        "missing_files_total": len(report.get("missing_files", [])),
        "hash_mismatches_total": len(report.get("hash_mismatches", [])),
        "extra_files_total": len(report.get("extra_files", [])),
        "integrity_report_path": report_path,
        "integrity_report_written": report_path is not None,
        "network_used": False,
        "external_api_used": False,
        "remote_export_used": False,
        "compliance_certification_claimed": False,
        "mutations_performed": report_path is not None,
        "source_mutations_performed": False,
        "remote_execution_enabled": False,
        "connector_write_enabled": False,
        "plugin_execution_enabled": False,
        "blocking_findings_total": _blocking_count([_finding_from_dict(item) for item in report.get("findings", [])]),
        "crypto_available": report.get("crypto", {}).get("crypto_available"),
        "signed": report.get("crypto", {}).get("signed"),
        "signature_provided": report.get("crypto", {}).get("signature_provided"),
        "signature_verified": report.get("signature_verified"),
        "encrypted": report.get("crypto", {}).get("encrypted"),
        "encryption_used": report.get("encryption_used"),
        "encryption_verified": report.get("crypto", {}).get("encryption_verified"),
        "remote_kms_used": False,
        "output_dir": options.output_dir,
    }


def _integrity_report(
    *,
    pack_id: str,
    status: str,
    files_total: int = 0,
    files_verified: int = 0,
    missing_files: list[str] | None = None,
    hash_mismatches: list[dict[str, str]] | None = None,
    redaction_passed: bool = False,
    secrets_detected: int = 0,
    signature_verified: bool | None = None,
    encryption_used: bool = False,
    findings: list[Finding] | None = None,
    extra_files: list[str] | None = None,
    schema_valid: bool = False,
    manifest_hash_valid: bool = False,
    crypto_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    missing_files = missing_files or []
    hash_mismatches = hash_mismatches or []
    extra_files = extra_files or []
    findings = findings or []
    crypto_status = crypto_status or {}
    files_failed = len(missing_files) + len(hash_mismatches) + len(extra_files)
    return {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-AUDIT-PACK-INTEGRITY-REPORT-V1",
        "report_id": f"audit-pack-integrity-{_safe_filename(pack_id)}",
        "pack_id": pack_id,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "created_by": POST_H_013_C_CREATED_BY,
        "status": status,
        "files_total": files_total,
        "files_verified": files_verified,
        "files_failed": files_failed,
        "missing_files": missing_files,
        "hash_mismatches": hash_mismatches,
        "extra_files": extra_files,
        "manifest_schema_valid": schema_valid,
        "manifest_hash_valid": manifest_hash_valid,
        "redaction_passed": redaction_passed,
        "secrets_detected": secrets_detected,
        "signature_verified": signature_verified,
        "encryption_used": encryption_used,
        "crypto": {
            "created_by": "POST-H-013-D",
            "status": "implemented-initial",
            "preliminary": True,
            "crypto_available": True,
            "signed": signature_verified is not None or bool(crypto_status.get("signature_provided", False)),
            "encrypted": encryption_used,
            "signature_provided": bool(crypto_status.get("signature_provided", False)),
            "signature_verified": signature_verified,
            "encryption_artifact_provided": bool(crypto_status.get("encryption_artifact_provided", False)),
            "encryption_verified": crypto_status.get("encryption_verified"),
            "remote_kms_used": False,
            "network_used": False,
            "external_api_used": False,
        },
        "network_used": False,
        "external_api_used": False,
        "remote_export_used": False,
        "compliance_certification_claimed": False,
        "findings": [finding.to_dict() for finding in findings],
        "safety": {
            "local_first": True,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "runtime_db_exported": False,
            "agent_sessions_exported": False,
            "env_files_exported": False,
            "secrets_exported": False,
        },
        "notes": [
            "POST-H-013-C verifies audit pack v2 integrity locally without network or external APIs.",
            "POST-H-013-D reports optional local signature/encryption status without remote KMS.",
            "This report is evidence integrity metadata only and does not claim compliance certification.",
        ],
    }


def _safety_findings(manifest: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    flag_expectations = {
        "local_first": True,
        "remote_export_used": False,
        "network_used": False,
        "external_api_used": False,
        "compliance_certification_claimed": False,
    }
    for key, expected in flag_expectations.items():
        if manifest.get(key) is not expected:
            findings.append(Finding("AUDIT_PACK_V2_SAFETY_FLAG_INVALID", "Audit pack v2 manifest safety flag is invalid.", Severity.BLOCK, path=MANIFEST_V2_NAME, metadata={"key": key, "expected": expected, "actual": manifest.get(key)}))
    safety = manifest.get("safety", {}) if isinstance(manifest.get("safety"), dict) else {}
    for key in ["runtime_db_exported", "agent_sessions_exported", "env_files_exported", "secrets_exported", "remote_execution_enabled", "connector_write_enabled", "plugin_execution_enabled"]:
        if safety.get(key) is not False:
            findings.append(Finding("AUDIT_PACK_V2_SAFETY_INVARIANT_INVALID", "Audit pack v2 safety invariant is invalid.", Severity.BLOCK, path=MANIFEST_V2_NAME, metadata={"key": key, "expected": False, "actual": safety.get(key)}))
    return findings


def _verify_manifest_hash(manifest: dict[str, Any]) -> bool:
    expected = manifest.get("integrity", {}).get("manifest_hash") if isinstance(manifest.get("integrity"), dict) else None
    if not isinstance(expected, str) or len(expected) != 64:
        return False
    clone = copy.deepcopy(manifest)
    clone.setdefault("integrity", {})["manifest_hash"] = _DEFAULT_MANIFEST_HASH_PLACEHOLDER
    return _sha256_bytes(_json_bytes(clone)) == expected


def _invalid_member_reason(path: str) -> str | None:
    rel = path.replace("\\", "/").strip("/")
    if not rel:
        return "empty-path"
    if path.startswith("/") or "\\" in path:
        return "unsafe-path-syntax"
    parts = PurePosixPath(rel).parts
    if ".." in parts:
        return "path-traversal"
    if rel in {".devpilot/devpilot.db", ".env", ".devpilot/providers.yaml"}:
        return "forbidden-exact"
    if rel.startswith((".devpilot/agent_sessions/", ".devpilot/backups/", "outputs/")):
        return "forbidden-prefix"
    if any(part in {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "dist"} for part in parts):
        return "forbidden-runtime-build-part"
    name = PurePosixPath(rel).name.lower()
    if name == ".env" or (name.startswith(".env.") and not name.endswith(".example")):
        return "env-secret"
    if name.endswith((".pem", ".key", ".p12", ".pfx")):
        return "secret-key-file"
    if any(part.lower() in {"secrets", ".secrets"} for part in parts):
        return "secrets-directory"
    return None


def _verification_ok(
    findings: list[Finding],
    zip_valid: bool,
    manifest_present: bool,
    schema_valid: bool,
    manifest_hash_valid: bool,
    files_total: int,
    files_verified: int,
) -> bool:
    return (
        zip_valid
        and manifest_present
        and schema_valid
        and manifest_hash_valid
        and files_total > 0
        and files_total == files_verified
        and not any(finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for finding in findings)
    )


def _relative_or_none(path: Path, root: Path) -> str | None:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return None


def _json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_filename(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "-" for ch in value)
    return cleaned[:120] or "unknown"


def _exit_code_from_findings(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS


def _blocking_count(findings: list[Finding]) -> int:
    return sum(1 for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR})


def _finding_from_dict(item: dict[str, Any]) -> Finding:
    severity = Severity(item.get("severity", "info"))
    return Finding(str(item.get("id", "UNKNOWN")), str(item.get("message", "")), severity, path=item.get("path"), metadata=item.get("metadata", {}))
