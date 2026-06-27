from __future__ import annotations

import fnmatch
import hashlib
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy.path_guard import PathGuard

from .crypto import (
    AuditPackCryptoOptions,
    build_encryption_report,
    crypto_capabilities,
    encrypt_bytes,
    json_bytes as crypto_json_bytes,
    load_local_key_material,
    sha256_bytes as crypto_sha256_bytes,
    sign_bytes,
)
from .redaction import AuditPackRedactionEntry, AuditPackRedactionScanner, build_redaction_report

POST_H_013_B_CREATED_BY = "POST-H-013-B"
MANIFEST_V2_NAME = "audit-pack-manifest-v2.json"
REDACTION_REPORT_NAME = "redaction_report.json"
_DEFAULT_POLICY_PATH = ".devpilot/auditpack/audit_pack_policy.json"
_DEFAULT_OUTPUT_DIR = "outputs/auditpacks"
_DEFAULT_ACTOR = "local-owner"
_DEFAULT_MANIFEST_HASH_PLACEHOLDER = "0" * 64


@dataclass(frozen=True)
class AuditPackV2BuildOptions:
    """Options for POST-H-013-B audit pack v2 creation.

    Dry-run is the default and performs the complete selection, exclusion,
    redaction and checksum plan without writing ZIPs or reports. Execute mode is
    explicit and writes only under outputs/auditpacks.
    """

    actor: str | None = _DEFAULT_ACTOR
    output_dir: str = _DEFAULT_OUTPUT_DIR
    policy_path: str = _DEFAULT_POLICY_PATH
    dry_run: bool = True
    execute: bool = False
    sign_mode: str = "none"
    encrypt_mode: str = "none"
    crypto_keyfile: str | None = None
    crypto_passphrase_env: str | None = None


class AuditPackV2Builder:
    """Build local Audit Pack Manifest v2 evidence with checksums and redaction.

    POST-H-013-B is intentionally local-first and conservative: it reads only
    allowlisted source/governance paths, excludes runtime/secret artifacts, uses
    SecretGuard for text scanning and blocks the build when secret-like material
    is detected. It does not sign, encrypt or verify received packs; those are
    reserved for later POST-H-013 micro-sprints.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.path_guard = PathGuard(self.root)
        self.redaction_scanner = AuditPackRedactionScanner()

    def build(self, options: AuditPackV2BuildOptions | None = None) -> CommandResult:
        options = options or AuditPackV2BuildOptions()
        mode_result = _resolve_mode(options)
        if mode_result is not None:
            return mode_result

        rbac_result = self._rbac_check(options.actor, action="audit-pack.build-v2", subject="audit-pack-v2")
        if not rbac_result.ok:
            return rbac_result

        crypto_options = AuditPackCryptoOptions(
            sign_mode=options.sign_mode,
            encrypt_mode=options.encrypt_mode,
            keyfile=options.crypto_keyfile,
            passphrase_env=options.crypto_passphrase_env,
        )
        crypto_findings, crypto_plan = self._plan_crypto(crypto_options)

        findings: list[Finding] = [*crypto_findings]
        policy_result = self._load_policy(options.policy_path)
        if not policy_result.ok:
            return policy_result
        policy = policy_result.data["policy"]

        if _has_blocking(crypto_findings):
            pack_id = _pack_id([], execute=options.execute)
            summary = _blocked_crypto_summary(options, pack_id, crypto_plan, findings)
            return CommandResult(
                "audit-pack build-v2",
                False,
                _exit_code_from_findings(findings),
                "Audit pack v2 build blocked by local crypto findings before file collection.",
                data={"summary": summary, "crypto": _public_crypto_plan(crypto_plan)},
                findings=findings,
            )

        selected, excluded = self._collect_candidates(policy)
        files: list[dict[str, Any]] = []
        payloads: list[tuple[str, bytes]] = []
        redaction_entries: list[AuditPackRedactionEntry] = []
        read_errors = 0

        for rel in selected:
            absolute = self.root / rel
            decision = self.path_guard.evaluate(rel, action="read")
            if decision.effect.value == "block":
                findings.append(decision.to_finding())
                continue
            try:
                content = absolute.read_bytes()
            except OSError as exc:
                read_errors += 1
                findings.append(
                    Finding(
                        "AUDIT_PACK_V2_FILE_READ_ERROR",
                        "Audit pack v2 could not read an allowlisted evidence file.",
                        Severity.FAIL,
                        path=rel,
                        metadata={"error": str(exc)},
                    )
                )
                continue
            redaction = self.redaction_scanner.scan(path=absolute, rel_path=rel, content=content)
            redaction_entries.append(redaction.entry)
            if redaction.entry.redactions > 0:
                findings.append(
                    Finding(
                        "AUDIT_PACK_V2_SECRET_DETECTED_BLOCKED",
                        "SecretGuard detected secret-like content; audit pack v2 build is blocked and no raw secret is exported.",
                        Severity.BLOCK,
                        path=rel,
                        metadata={"redactions": redaction.entry.redactions, "raw_secret_exported": False},
                    )
                )
                continue
            sha = _sha256_bytes(redaction.content)
            files.append(
                {
                    "path": rel,
                    "kind": _entry_kind(rel),
                    "sha256": sha,
                    "size_bytes": len(redaction.content),
                    "redaction_applied": redaction.entry.redaction_applied,
                    "included": True,
                    "source": "repo",
                }
            )
            payloads.append((rel, redaction.content))

        pack_id = _pack_id(files, execute=options.execute)
        blocked = _has_blocking(findings)
        redaction_report = build_redaction_report(pack_id=pack_id, entries=redaction_entries, blocked=blocked)
        redaction_report_bytes = _json_bytes(redaction_report)
        redaction_entry = {
            "path": REDACTION_REPORT_NAME,
            "kind": "redaction-report",
            "sha256": _sha256_bytes(redaction_report_bytes),
            "size_bytes": len(redaction_report_bytes),
            "redaction_applied": False,
            "included": True,
            "source": "generated",
        }

        manifest_files = files if blocked else [*files, redaction_entry]
        manifest = self._manifest(
            pack_id=pack_id,
            actor=options.actor or _DEFAULT_ACTOR,
            files=manifest_files,
            excluded=excluded,
            redaction_report=redaction_report,
            status="blocked" if blocked else ("built" if options.execute else "implemented-initial"),
            crypto_plan=crypto_plan,
        )
        manifest_bytes = _json_bytes(manifest)

        summary: dict[str, Any] = {
            "created_by": POST_H_013_B_CREATED_BY,
            "status": "blocked" if blocked else "implemented-initial",
            "preliminary": True,
            "pack_id": pack_id,
            "mode": "execute" if options.execute else "dry-run",
            "dry_run": bool(options.dry_run and not options.execute),
            "execute": bool(options.execute),
            "policy_path": options.policy_path,
            "output_dir": options.output_dir,
            "candidates_total": len(selected),
            "files_included": len(files),
            "files_with_sha256": len([item for item in files if item.get("sha256")]),
            "excluded_total": len(excluded),
            "read_errors_total": read_errors,
            "redaction_report_present": True,
            "redaction_report_written": False,
            "redaction_report_embedded": False,
            "redaction_report_path": None,
            "secrets_detected": redaction_report["secrets_detected"],
            "redaction_passed": redaction_report["redaction_passed"],
            "raw_secrets_exported": False,
            "manifest_schema_id": "SCHEMA-DEVPL-AUDIT-PACK-MANIFEST-V2",
            "manifest_hash": manifest["integrity"]["manifest_hash"],
            "manifest_embedded": False,
            "manifest_path": None,
            "pack_path": None,
            "pack_sha256": None,
            "local_first": True,
            "network_used": False,
            "external_api_used": False,
            "remote_export_used": False,
            "compliance_certification_claimed": False,
            "runtime_db_exported": False,
            "agent_sessions_exported": False,
            "env_files_exported": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "crypto_available": crypto_plan["crypto_available"],
            "sign_requested": crypto_plan["sign_requested"],
            "encrypt_requested": crypto_plan["encrypt_requested"],
            "signed": False,
            "encrypted": False,
            "signature_path": None,
            "encrypted_pack_path": None,
            "crypto_report_path": None,
            "crypto_key_source": crypto_plan["key_source"],
            "crypto_key_fingerprint": crypto_plan["key_fingerprint"],
            "signing_backend": crypto_plan["signing_backend"],
            "encryption_backend": crypto_plan["encryption_backend"],
            "remote_kms_used": False,
            "keys_in_repo_used": False,
            "blocking_findings_total": _blocking_count(findings),
        }

        if blocked:
            return CommandResult(
                "audit-pack build-v2",
                False,
                _exit_code_from_findings(findings),
                "Audit pack v2 build blocked by redaction or safety findings.",
                data={"summary": summary, "manifest": manifest, "redaction_report": redaction_report, "crypto": _public_crypto_plan(crypto_plan)},
                findings=findings,
            )

        if options.execute:
            output_dir = (self.root / options.output_dir).resolve()
            output_dir.mkdir(parents=True, exist_ok=True)
            pack_path = output_dir / f"{pack_id}.zip"
            manifest_path = output_dir / f"{pack_id}_manifest_v2.json"
            redaction_report_path = output_dir / f"{pack_id}_redaction_report.json"
            with zipfile.ZipFile(pack_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for arcname, content in sorted(payloads, key=lambda item: item[0]):
                    archive.writestr(arcname, content)
                archive.writestr(REDACTION_REPORT_NAME, redaction_report_bytes)
                archive.writestr(MANIFEST_V2_NAME, manifest_bytes)
            manifest_path.write_bytes(manifest_bytes)
            redaction_report_path.write_bytes(redaction_report_bytes)
            pack_rel = _to_posix(pack_path.relative_to(self.root))
            pack_sha256 = _sha256_file(pack_path)
            crypto_result = self._write_optional_crypto_artifacts(
                pack_path=pack_path,
                pack_rel=pack_rel,
                pack_id=pack_id,
                pack_sha256=pack_sha256,
                crypto_plan=crypto_plan,
                output_dir=output_dir,
            )
            findings.extend(crypto_result["findings"])
            if _has_blocking(crypto_result["findings"]):
                summary.update({"blocking_findings_total": _blocking_count(findings)})
                return CommandResult(
                    "audit-pack build-v2",
                    False,
                    _exit_code_from_findings(findings),
                    "Audit pack v2 build blocked by local crypto findings.",
                    data={"summary": summary, "manifest": manifest, "redaction_report": redaction_report, "crypto": crypto_result},
                    findings=findings,
                )
            summary.update(
                {
                    "status": "built",
                    "pack_path": pack_rel,
                    "pack_sha256": pack_sha256,
                    "manifest_embedded": True,
                    "manifest_path": _to_posix(manifest_path.relative_to(self.root)),
                    "redaction_report_written": True,
                    "redaction_report_embedded": True,
                    "redaction_report_path": _to_posix(redaction_report_path.relative_to(self.root)),
                    "mutations_performed": True,
                    "signed": crypto_result["signed"],
                    "encrypted": crypto_result["encrypted"],
                    "signature_path": crypto_result["signature_path"],
                    "encrypted_pack_path": crypto_result["encrypted_pack_path"],
                    "crypto_report_path": crypto_result["crypto_report_path"],
                }
            )
            message = "Audit pack v2 built successfully under outputs/auditpacks."
        else:
            message = "Audit pack v2 dry-run completed without writing pack artifacts."

        findings.append(
            Finding(
                "AUDIT_PACK_V2_BUILD_READY",
                message,
                Severity.INFO,
                path=summary["pack_path"],
                metadata={
                    "pack_id": pack_id,
                    "files_included": len(files),
                    "dry_run": summary["dry_run"],
                    "execute": summary["execute"],
                },
            )
        )
        return CommandResult(
            "audit-pack build-v2",
            True,
            ExitCode.PASS,
            message,
            data={"summary": summary, "manifest": manifest, "redaction_report": redaction_report, "crypto": _public_crypto_plan(crypto_plan)},
            findings=findings,
        )

    def _load_policy(self, policy_path: str) -> CommandResult:
        path = self.root / policy_path
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            finding = Finding("AUDIT_PACK_V2_POLICY_MISSING", "Audit pack v2 policy file is missing.", Severity.BLOCK, path=policy_path)
            return CommandResult("audit-pack build-v2", False, ExitCode.BLOCK, "Audit pack v2 policy is missing.", data={"policy_path": policy_path}, findings=[finding])
        except json.JSONDecodeError as exc:
            finding = Finding("AUDIT_PACK_V2_POLICY_JSON_INVALID", "Audit pack v2 policy JSON is invalid.", Severity.ERROR, path=policy_path, metadata={"error": str(exc)})
            return CommandResult("audit-pack build-v2", False, ExitCode.ERROR, "Audit pack v2 policy is invalid.", data={"policy_path": policy_path}, findings=[finding])
        required_flags = {
            "local_first": True,
            "compliance_certification_claimed": False,
            "remote_export_allowed": False,
            "network_required": False,
            "external_api_required": False,
        }
        findings: list[Finding] = []
        for key, expected in required_flags.items():
            if payload.get(key) is not expected:
                findings.append(Finding("AUDIT_PACK_V2_POLICY_SAFETY_FLAG_INVALID", "Audit pack v2 policy safety flag is invalid.", Severity.BLOCK, path=policy_path, metadata={"key": key, "expected": expected, "actual": payload.get(key)}))
        if findings:
            return CommandResult("audit-pack build-v2", False, ExitCode.BLOCK, "Audit pack v2 policy failed safety validation.", data={"policy": payload}, findings=findings)
        return CommandResult("audit-pack build-v2 policy", True, ExitCode.PASS, "Audit pack v2 policy loaded.", data={"policy": payload}, findings=[])

    def _collect_candidates(self, policy: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
        include_patterns = [str(item) for item in policy.get("include_patterns", [])]
        exclude_patterns = [str(item) for item in policy.get("exclude_patterns", [])]
        forbidden_exact = {str(item).replace("\\", "/").strip("/") for item in policy.get("forbidden_exact_paths", [])}
        forbidden_prefixes = tuple(str(item).replace("\\", "/").strip("/") for item in policy.get("forbidden_prefixes", []))
        selected: set[str] = set()
        excluded: dict[str, dict[str, Any]] = {}

        for pattern in include_patterns:
            for path in _glob_pattern(self.root, pattern):
                if not path.is_file():
                    continue
                rel = _to_posix(path.relative_to(self.root))
                reason = _excluded_reason(rel, exclude_patterns=exclude_patterns, forbidden_exact=forbidden_exact, forbidden_prefixes=forbidden_prefixes)
                if reason:
                    excluded.setdefault(rel, {"path": rel, "reason": reason, "policy_rule_id": "AUDIT_PACK_POLICY_EXCLUDE"})
                    continue
                selected.add(rel)

        for exact in sorted(forbidden_exact):
            excluded.setdefault(exact, {"path": exact, "reason": "forbidden-exact-policy", "policy_rule_id": "AUDIT_PACK_POLICY_FORBIDDEN_EXACT"})
        for prefix in sorted(forbidden_prefixes):
            excluded.setdefault(prefix.rstrip("/") + "/**", {"path": prefix.rstrip("/") + "/**", "reason": "forbidden-prefix-policy", "policy_rule_id": "AUDIT_PACK_POLICY_FORBIDDEN_PREFIX"})

        return sorted(selected), sorted(excluded.values(), key=lambda item: item["path"])


    def _plan_crypto(self, options: AuditPackCryptoOptions) -> tuple[list[Finding], dict[str, Any]]:
        findings: list[Finding] = []
        sign_mode = _normalize_crypto_mode(options.sign_mode, field="sign")
        encrypt_mode = _normalize_crypto_mode(options.encrypt_mode, field="encrypt")
        capabilities = crypto_capabilities()
        normalized_options = AuditPackCryptoOptions(
            sign_mode=sign_mode,
            encrypt_mode=encrypt_mode,
            keyfile=options.keyfile,
            passphrase_env=options.passphrase_env,
        )
        if sign_mode == "invalid" or encrypt_mode == "invalid":
            findings.append(
                Finding(
                    "AUDIT_PACK_CRYPTO_MODE_INVALID",
                    "Audit pack local crypto mode must be one of none, optional or required.",
                    Severity.BLOCK,
                    metadata={"sign_mode": options.sign_mode, "encrypt_mode": options.encrypt_mode},
                )
            )
        key_material = load_local_key_material(self.root, normalized_options)
        findings.extend(key_material.findings)
        sign_requested = sign_mode in {"optional", "required"}
        encrypt_requested = encrypt_mode in {"optional", "required"}
        sign_planned = sign_requested and key_material.available and sign_mode != "invalid"
        encrypt_planned = encrypt_requested and key_material.available and bool(capabilities["encryption_available"]) and encrypt_mode != "invalid"
        if sign_mode == "required" and not sign_planned:
            findings.append(
                Finding(
                    "AUDIT_PACK_CRYPTO_SIGN_REQUIRED_UNAVAILABLE",
                    "Audit pack local signing was required but no usable local key material was available.",
                    Severity.BLOCK,
                    metadata={"key_source": key_material.source},
                )
            )
        if encrypt_mode == "required" and not encrypt_planned:
            findings.append(
                Finding(
                    "AUDIT_PACK_CRYPTO_ENCRYPT_REQUIRED_UNAVAILABLE",
                    "Audit pack local encryption was required but the optional backend or key material was unavailable.",
                    Severity.BLOCK,
                    metadata={"encryption_available": capabilities["encryption_available"], "key_source": key_material.source},
                )
            )
        if encrypt_mode == "optional" and encrypt_requested and key_material.available and not capabilities["encryption_available"]:
            findings.append(
                Finding(
                    "AUDIT_PACK_CRYPTO_ENCRYPT_OPTIONAL_UNAVAILABLE",
                    "Audit pack local encryption optional backend is unavailable; build continues without encryption.",
                    Severity.WARNING,
                    metadata={"remote_kms_used": False},
                )
            )
        return findings, {
            **capabilities,
            "sign_mode": sign_mode,
            "encrypt_mode": encrypt_mode,
            "sign_requested": sign_requested,
            "encrypt_requested": encrypt_requested,
            "sign_planned": sign_planned,
            "encrypt_planned": encrypt_planned,
            "crypto_available": bool(capabilities["signing_available"] or capabilities["encryption_available"]),
            "signature_algorithm": "hmac-sha256-local-keyfile-or-env" if sign_planned else None,
            "encryption_algorithm": "fernet-sha256-derived-local-key" if encrypt_planned else None,
            "key_source": key_material.source,
            "key_fingerprint": key_material.fingerprint,
            "key_material": key_material.value,
            "findings": [finding.to_dict() for finding in findings],
        }

    def _write_optional_crypto_artifacts(
        self,
        *,
        pack_path: Path,
        pack_rel: str,
        pack_id: str,
        pack_sha256: str,
        crypto_plan: dict[str, Any],
        output_dir: Path,
    ) -> dict[str, Any]:
        findings: list[Finding] = []
        key = crypto_plan.get("key_material")
        result: dict[str, Any] = {
            "created_by": "POST-H-013-D",
            "status": "implemented-initial",
            "signed": False,
            "encrypted": False,
            "signature_path": None,
            "encrypted_pack_path": None,
            "crypto_report_path": None,
            "findings": findings,
            "network_used": False,
            "external_api_used": False,
            "remote_kms_used": False,
            "keys_in_repo_used": False,
        }
        if not key:
            return result
        pack_bytes = pack_path.read_bytes()
        crypto_report: dict[str, Any] = {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-AUDIT-PACK-LOCAL-CRYPTO-REPORT-V1",
            "report_id": f"audit-pack-local-crypto-{pack_id}",
            "pack_id": pack_id,
            "created_by": "POST-H-013-D",
            "status": "implemented-initial",
            "preliminary": True,
            "pack_path": pack_rel,
            "pack_sha256": pack_sha256,
            "signed": False,
            "encrypted": False,
            "signature_path": None,
            "encrypted_pack_path": None,
            "network_used": False,
            "external_api_used": False,
            "remote_kms_used": False,
            "compliance_certification_claimed": False,
        }
        if crypto_plan.get("sign_planned"):
            signature = sign_bytes(pack_bytes, key=key, pack_id=pack_id, signed_artifact=pack_rel)
            signature_path = output_dir / f"{pack_id}.sig.json"
            signature_path.write_bytes(crypto_json_bytes(signature))
            result["signed"] = True
            result["signature_path"] = _to_posix(signature_path.relative_to(self.root))
            crypto_report.update({"signed": True, "signature_path": result["signature_path"], "signature_algorithm": signature["algorithm"]})
        if crypto_plan.get("encrypt_planned"):
            encrypted_bytes, finding = encrypt_bytes(pack_bytes, key=key)
            if finding is not None:
                findings.append(finding)
            if encrypted_bytes is not None:
                encrypted_path = output_dir / f"{pack_id}.zip.fernet"
                encrypted_path.write_bytes(encrypted_bytes)
                encrypted_report = build_encryption_report(
                    pack_id=pack_id,
                    source_pack=pack_rel,
                    encrypted_artifact=_to_posix(encrypted_path.relative_to(self.root)),
                    plaintext_sha256=pack_sha256,
                    encrypted_sha256=crypto_sha256_bytes(encrypted_bytes),
                    key_fingerprint=crypto_plan.get("key_fingerprint"),
                )
                encryption_report_path = output_dir / f"{pack_id}_encryption_report.json"
                encryption_report_path.write_bytes(crypto_json_bytes(encrypted_report))
                result["encrypted"] = True
                result["encrypted_pack_path"] = _to_posix(encrypted_path.relative_to(self.root))
                crypto_report.update({
                    "encrypted": True,
                    "encrypted_pack_path": result["encrypted_pack_path"],
                    "encryption_report_path": _to_posix(encryption_report_path.relative_to(self.root)),
                    "encryption_algorithm": encrypted_report["algorithm"],
                })
        if result["signed"] or result["encrypted"]:
            crypto_report_path = output_dir / f"{pack_id}_crypto_report.json"
            crypto_report_path.write_bytes(crypto_json_bytes(crypto_report))
            result["crypto_report_path"] = _to_posix(crypto_report_path.relative_to(self.root))
        return result

    def _manifest(
        self,
        *,
        pack_id: str,
        actor: str,
        files: list[dict[str, Any]],
        excluded: list[dict[str, Any]],
        redaction_report: dict[str, Any],
        status: str,
        crypto_plan: dict[str, Any],
    ) -> dict[str, Any]:
        base = {
            "schema_version": "2.0",
            "schema_id": "SCHEMA-DEVPL-AUDIT-PACK-MANIFEST-V2",
            "pack_id": pack_id,
            "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "created_by": POST_H_013_B_CREATED_BY,
            "generated_by_actor": actor,
            "status": status,
            "local_first": True,
            "remote_export_used": False,
            "network_used": False,
            "external_api_used": False,
            "compliance_certification_claimed": False,
            "files": files,
            "excluded": excluded,
            "redaction": {
                "redaction_report_required": True,
                "redaction_report_present": True,
                "redaction_passed": bool(redaction_report["redaction_passed"]),
                "secrets_detected": int(redaction_report["secrets_detected"]),
                "raw_secrets_exported": False,
                "redacted_files_total": int(redaction_report["files_redacted_total"]),
            },
            "integrity": {
                "algorithm": "sha256",
                "manifest_hash": _DEFAULT_MANIFEST_HASH_PLACEHOLDER,
                "signed": bool(crypto_plan.get("sign_planned", False)),
                "encrypted": bool(crypto_plan.get("encrypt_planned", False)),
                "signature_algorithm": crypto_plan.get("signature_algorithm"),
                "encryption_algorithm": crypto_plan.get("encryption_algorithm"),
                "manifest_hash_source": "canonical-json-before-final-hash-injection",
            },
            "safety": {
                "runtime_db_exported": False,
                "agent_sessions_exported": False,
                "env_files_exported": False,
                "secrets_exported": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
            },
            "crypto": {
                "created_by": "POST-H-013-D",
                "status": "implemented-initial",
                "preliminary": True,
                "crypto_available": bool(crypto_plan.get("crypto_available", False)),
                "sign_requested": bool(crypto_plan.get("sign_requested", False)),
                "encrypt_requested": bool(crypto_plan.get("encrypt_requested", False)),
                "sign_planned": bool(crypto_plan.get("sign_planned", False)),
                "encrypt_planned": bool(crypto_plan.get("encrypt_planned", False)),
                "key_source": crypto_plan.get("key_source"),
                "key_fingerprint_sha256_16": crypto_plan.get("key_fingerprint"),
                "remote_kms_used": False,
                "keys_in_repo_used": False,
            },
            "notes": [
                "POST-H-013-B implements the first audit pack v2 builder with dry-run default and execute flag.",
                "POST-H-013-D adds optional local signing/encryption planning and sidecar artifacts without remote KMS.",
                "This artifact is local evidence only and does not claim SOC2, ISO or enterprise compliance certification.",
            ],
        }
        base["integrity"]["manifest_hash"] = _sha256_bytes(_json_bytes(base))
        return base

    def _rbac_check(self, actor: str | None, *, action: str, subject: str) -> CommandResult:
        from devpilot_core.identity import IdentityRegistry, IdentityRegistryOptions, RbacCheckInput

        registry = IdentityRegistry(self.root, options=IdentityRegistryOptions(registry_path=".devpilot/identity/identity_registry.json"))
        result = registry.check(RbacCheckInput(actor_id=actor, action=action, permission="audit.pack.build", subject=subject, require_sensitive=False))
        if result.ok:
            return CommandResult("audit-pack build-v2 rbac", True, ExitCode.PASS, "Audit pack v2 actor is authorized.", data=result.data, findings=[])
        return CommandResult("audit-pack build-v2", False, result.exit_code, "Audit pack v2 actor is not authorized.", data=result.data, findings=result.findings)


def _public_crypto_plan(plan: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in plan.items() if key != "key_material"}


def _normalize_crypto_mode(value: str, *, field: str) -> str:
    normalized = (value or "none").strip().lower()
    return normalized if normalized in {"none", "optional", "required"} else "invalid"


def _resolve_mode(options: AuditPackV2BuildOptions) -> CommandResult | None:
    if options.execute and options.dry_run:
        # CLI defaults dry_run=True internally; execute is authoritative for user-facing mode.
        return None
    if not options.execute and not options.dry_run:
        finding = Finding("AUDIT_PACK_V2_MODE_UNSPECIFIED", "Audit pack v2 requires explicit dry-run or execute mode.", Severity.BLOCK)
        return CommandResult("audit-pack build-v2", False, ExitCode.BLOCK, "Audit pack v2 mode is invalid.", data={"summary": {"dry_run": options.dry_run, "execute": options.execute}}, findings=[finding])
    return None



def _blocked_crypto_summary(options: AuditPackV2BuildOptions, pack_id: str, crypto_plan: dict[str, Any], findings: list[Finding]) -> dict[str, Any]:
    return {
        "created_by": POST_H_013_B_CREATED_BY,
        "status": "blocked",
        "preliminary": True,
        "pack_id": pack_id,
        "mode": "execute" if options.execute else "dry-run",
        "dry_run": bool(options.dry_run and not options.execute),
        "execute": bool(options.execute),
        "policy_path": options.policy_path,
        "output_dir": options.output_dir,
        "candidates_total": 0,
        "files_included": 0,
        "files_with_sha256": 0,
        "excluded_total": 0,
        "read_errors_total": 0,
        "redaction_report_present": False,
        "redaction_report_written": False,
        "redaction_report_embedded": False,
        "redaction_report_path": None,
        "secrets_detected": 0,
        "redaction_passed": False,
        "raw_secrets_exported": False,
        "manifest_schema_id": "SCHEMA-DEVPL-AUDIT-PACK-MANIFEST-V2",
        "manifest_hash": None,
        "manifest_embedded": False,
        "manifest_path": None,
        "pack_path": None,
        "pack_sha256": None,
        "local_first": True,
        "network_used": False,
        "external_api_used": False,
        "remote_export_used": False,
        "compliance_certification_claimed": False,
        "runtime_db_exported": False,
        "agent_sessions_exported": False,
        "env_files_exported": False,
        "mutations_performed": False,
        "source_mutations_performed": False,
        "remote_execution_enabled": False,
        "connector_write_enabled": False,
        "plugin_execution_enabled": False,
        "crypto_available": crypto_plan["crypto_available"],
        "sign_requested": crypto_plan["sign_requested"],
        "encrypt_requested": crypto_plan["encrypt_requested"],
        "signed": False,
        "encrypted": False,
        "signature_path": None,
        "encrypted_pack_path": None,
        "crypto_report_path": None,
        "crypto_key_source": crypto_plan["key_source"],
        "crypto_key_fingerprint": crypto_plan["key_fingerprint"],
        "signing_backend": crypto_plan["signing_backend"],
        "encryption_backend": crypto_plan["encryption_backend"],
        "remote_kms_used": False,
        "keys_in_repo_used": False,
        "blocking_findings_total": _blocking_count(findings),
    }

def _glob_pattern(root: Path, pattern: str) -> list[Path]:
    pattern = pattern.replace("\\", "/").strip("/")
    if pattern == "**":
        return _files_under(root)
    if pattern.endswith("/**"):
        base_pattern = pattern[:-3].rstrip("/")
        bases = list(root.glob(base_pattern)) if any(ch in base_pattern for ch in "*?[") else [root / base_pattern]
        files: list[Path] = []
        for base in bases:
            if base.is_file():
                files.append(base)
            elif base.is_dir():
                files.extend(_files_under(base))
        return files
    if any(ch in pattern for ch in "*?["):
        return [item for item in root.glob(pattern) if item.is_file()]
    path = root / pattern
    if path.is_dir():
        return _files_under(path)
    return [path] if path.exists() else []


def _files_under(path: Path) -> list[Path]:
    return [item for item in path.rglob("*") if item.is_file()]


def _excluded_reason(rel: str, *, exclude_patterns: list[str], forbidden_exact: set[str], forbidden_prefixes: tuple[str, ...]) -> str | None:
    rel = rel.replace("\\", "/").strip("/")
    if rel in forbidden_exact:
        return "forbidden-exact-policy"
    if any(rel.startswith(prefix) for prefix in forbidden_prefixes):
        return "forbidden-prefix-policy"
    if any(_match_pattern(rel, pattern) for pattern in exclude_patterns):
        return "exclude-pattern-policy"
    path = PurePosixPath(rel)
    if any(part in {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "dist"} for part in path.parts):
        return "forbidden-runtime-build-part"
    filename = path.name.lower()
    if filename == ".env" or (filename.startswith(".env.") and not filename.endswith(".example")):
        return "env-secret-policy"
    if filename.endswith((".pem", ".key", ".p12", ".pfx")):
        return "secret-key-file-policy"
    return None


def _match_pattern(rel: str, pattern: str) -> bool:
    pattern = pattern.replace("\\", "/").strip("/")
    if pattern.endswith("/**"):
        return rel == pattern[:-3].rstrip("/") or rel.startswith(pattern[:-3].rstrip("/") + "/")
    return fnmatch.fnmatch(rel, pattern)


def _entry_kind(path: str) -> str:
    if path == REDACTION_REPORT_NAME:
        return "redaction-report"
    if path.startswith("docs/schemas/"):
        return "schema"
    if path.startswith("docs/audits/"):
        return "audit-document"
    if path.startswith("docs/backlogs/"):
        return "backlog"
    if path.startswith("docs/"):
        return "documentation"
    if path.startswith(".devpilot/"):
        return "governance-registry"
    return "source-document"


def _pack_id(files: list[dict[str, Any]], *, execute: bool) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dt%H%M%Sz")
    seed = "|".join(f"{item['path']}:{item['sha256']}" for item in sorted(files, key=lambda item: item["path"]))
    digest = hashlib.sha256(f"{seed}|{execute}".encode("utf-8")).hexdigest()[:10]
    return f"audit-pack-v2-{now}-{digest}"


def _json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _to_posix(path: Path) -> str:
    return path.as_posix()


def _has_blocking(findings: list[Finding]) -> bool:
    return any(finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for finding in findings)


def _blocking_count(findings: list[Finding]) -> int:
    return sum(1 for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR})


def _exit_code_from_findings(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS
