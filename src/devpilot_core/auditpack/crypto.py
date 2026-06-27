from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import Finding, Severity

POST_H_013_D_CREATED_BY = "POST-H-013-D"
HMAC_SHA256_ALGORITHM = "hmac-sha256-local-keyfile-or-env"
FERNET_ALGORITHM = "fernet-sha256-derived-local-key"

try:  # optional dependency: the repo must still work when it is absent.
    from cryptography.fernet import Fernet, InvalidToken  # type: ignore

    _FERNET_AVAILABLE = True
except Exception:  # pragma: no cover - exercised only on envs without cryptography.
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore
    _FERNET_AVAILABLE = False


@dataclass(frozen=True)
class AuditPackCryptoOptions:
    """Local optional crypto options for POST-H-013-D.

    ``sign_mode`` and ``encrypt_mode`` are explicit feature switches. Supported
    values are ``none``, ``optional`` and ``required``. Key material must come
    from a local keyfile outside the repository or from an environment variable;
    direct passphrase CLI arguments are intentionally unsupported to avoid shell
    history/process-list leakage.
    """

    sign_mode: str = "none"
    encrypt_mode: str = "none"
    keyfile: str | None = None
    passphrase_env: str | None = None


@dataclass(frozen=True)
class LocalKeyMaterial:
    source: str | None
    fingerprint: str | None
    value: bytes | None
    findings: list[Finding]

    @property
    def available(self) -> bool:
        return bool(self.value)


def crypto_capabilities() -> dict[str, Any]:
    return {
        "created_by": POST_H_013_D_CREATED_BY,
        "status": "implemented-initial",
        "preliminary": True,
        "signing_backend": "stdlib-hmac-sha256",
        "signing_available": True,
        "encryption_backend": "cryptography-fernet" if _FERNET_AVAILABLE else None,
        "encryption_available": _FERNET_AVAILABLE,
        "network_used": False,
        "external_api_used": False,
        "remote_kms_used": False,
        "keys_in_repo_allowed": False,
    }


def load_local_key_material(root: Path, options: AuditPackCryptoOptions) -> LocalKeyMaterial:
    findings: list[Finding] = []
    root = Path(root).resolve()
    if options.keyfile and options.passphrase_env:
        findings.append(
            Finding(
                "AUDIT_PACK_CRYPTO_MULTIPLE_KEY_SOURCES_BLOCKED",
                "Audit pack local crypto accepts exactly one key source per command.",
                Severity.BLOCK,
                metadata={"keyfile_declared": True, "passphrase_env_declared": True},
            )
        )
        return LocalKeyMaterial(source=None, fingerprint=None, value=None, findings=findings)
    if options.keyfile:
        key_path = Path(options.keyfile)
        absolute = key_path if key_path.is_absolute() else root / key_path
        absolute = absolute.resolve()
        try:
            absolute.relative_to(root)
            findings.append(
                Finding(
                    "AUDIT_PACK_CRYPTO_KEY_IN_REPO_BLOCKED",
                    "Audit pack local crypto key material must not be stored inside the repository workspace.",
                    Severity.BLOCK,
                    path=str(key_path),
                    metadata={"keys_in_repo_allowed": False},
                )
            )
            return LocalKeyMaterial(source="repo-keyfile-blocked", fingerprint=None, value=None, findings=findings)
        except ValueError:
            pass
        if not absolute.exists() or not absolute.is_file():
            findings.append(
                Finding(
                    "AUDIT_PACK_CRYPTO_KEYFILE_MISSING",
                    "Audit pack local crypto keyfile does not exist.",
                    Severity.BLOCK,
                    path=str(key_path),
                )
            )
            return LocalKeyMaterial(source="external-keyfile", fingerprint=None, value=None, findings=findings)
        try:
            value = absolute.read_bytes().strip()
        except OSError as exc:
            findings.append(
                Finding(
                    "AUDIT_PACK_CRYPTO_KEYFILE_READ_ERROR",
                    "Audit pack local crypto keyfile could not be read.",
                    Severity.BLOCK,
                    path=str(key_path),
                    metadata={"error": str(exc)},
                )
            )
            return LocalKeyMaterial(source="external-keyfile", fingerprint=None, value=None, findings=findings)
        return _material_from_bytes(value, source="external-keyfile", findings=findings)
    if options.passphrase_env:
        raw = os.environ.get(options.passphrase_env)
        if not raw:
            findings.append(
                Finding(
                    "AUDIT_PACK_CRYPTO_PASSPHRASE_ENV_MISSING",
                    "Audit pack local crypto passphrase environment variable is not set.",
                    Severity.BLOCK,
                    metadata={"env_var": options.passphrase_env},
                )
            )
            return LocalKeyMaterial(source="environment", fingerprint=None, value=None, findings=findings)
        return _material_from_bytes(raw.encode("utf-8"), source=f"env:{options.passphrase_env}", findings=findings)
    return LocalKeyMaterial(source=None, fingerprint=None, value=None, findings=findings)


def _material_from_bytes(value: bytes, *, source: str, findings: list[Finding]) -> LocalKeyMaterial:
    if len(value) < 16:
        findings.append(
            Finding(
                "AUDIT_PACK_CRYPTO_KEY_TOO_SHORT_BLOCKED",
                "Audit pack local crypto key material must be at least 16 bytes.",
                Severity.BLOCK,
                metadata={"minimum_bytes": 16, "actual_bytes": len(value)},
            )
        )
        return LocalKeyMaterial(source=source, fingerprint=None, value=None, findings=findings)
    fingerprint = hashlib.sha256(value).hexdigest()[:16]
    return LocalKeyMaterial(source=source, fingerprint=fingerprint, value=value, findings=findings)


def sign_bytes(payload: bytes, *, key: bytes, pack_id: str, signed_artifact: str) -> dict[str, Any]:
    signature = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-AUDIT-PACK-LOCAL-SIGNATURE-V1",
        "signature_id": f"audit-pack-local-signature-{_safe_filename(pack_id)}",
        "pack_id": pack_id,
        "created_at_utc": _now_utc(),
        "created_by": POST_H_013_D_CREATED_BY,
        "status": "signed",
        "preliminary": True,
        "algorithm": HMAC_SHA256_ALGORITHM,
        "signed_artifact": signed_artifact,
        "signature_hex": signature,
        "key_fingerprint_sha256_16": hashlib.sha256(key).hexdigest()[:16],
        "local_first": True,
        "network_used": False,
        "external_api_used": False,
        "remote_kms_used": False,
        "compliance_certification_claimed": False,
        "notes": [
            "POST-H-013-D uses local HMAC-SHA256 as an implemented-initial authenticity check, not enterprise PKI.",
            "The signing key material is never embedded in this signature artifact.",
        ],
    }


def verify_signature(payload: bytes, *, key: bytes, signature_report: dict[str, Any]) -> bool:
    expected = str(signature_report.get("signature_hex") or "")
    actual = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return bool(expected) and hmac.compare_digest(expected, actual)


def encrypt_bytes(payload: bytes, *, key: bytes) -> tuple[bytes | None, Finding | None]:
    if not _FERNET_AVAILABLE or Fernet is None:
        return None, Finding(
            "AUDIT_PACK_CRYPTO_ENCRYPTION_BACKEND_UNAVAILABLE",
            "Audit pack local encryption requires optional cryptography support; no remote KMS fallback is allowed.",
            Severity.WARNING,
            metadata={"remote_kms_used": False, "backend": "cryptography-fernet"},
        )
    fernet = Fernet(_fernet_key(key))
    return fernet.encrypt(payload), None


def decrypt_bytes(payload: bytes, *, key: bytes) -> tuple[bytes | None, Finding | None]:
    if not _FERNET_AVAILABLE or Fernet is None:
        return None, Finding(
            "AUDIT_PACK_CRYPTO_ENCRYPTION_BACKEND_UNAVAILABLE",
            "Audit pack local decryption requires optional cryptography support; no remote KMS fallback is allowed.",
            Severity.WARNING,
            metadata={"remote_kms_used": False, "backend": "cryptography-fernet"},
        )
    try:
        return Fernet(_fernet_key(key)).decrypt(payload), None
    except InvalidToken:
        return None, Finding(
            "AUDIT_PACK_CRYPTO_DECRYPT_FAILED",
            "Audit pack encrypted artifact could not be decrypted with the provided local key material.",
            Severity.BLOCK,
        )


def build_encryption_report(*, pack_id: str, source_pack: str, encrypted_artifact: str, plaintext_sha256: str, encrypted_sha256: str, key_fingerprint: str | None) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-AUDIT-PACK-LOCAL-ENCRYPTION-V1",
        "encryption_id": f"audit-pack-local-encryption-{_safe_filename(pack_id)}",
        "pack_id": pack_id,
        "created_at_utc": _now_utc(),
        "created_by": POST_H_013_D_CREATED_BY,
        "status": "encrypted",
        "preliminary": True,
        "algorithm": FERNET_ALGORITHM,
        "source_pack": source_pack,
        "encrypted_artifact": encrypted_artifact,
        "plaintext_sha256": plaintext_sha256,
        "encrypted_sha256": encrypted_sha256,
        "key_fingerprint_sha256_16": key_fingerprint,
        "local_first": True,
        "network_used": False,
        "external_api_used": False,
        "remote_kms_used": False,
        "compliance_certification_claimed": False,
        "notes": [
            "POST-H-013-D encryption is local optional protection at rest, performed after redaction and integrity checks.",
            "The encryption key material is never embedded in this report.",
        ],
    }


def json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fernet_key(key: bytes) -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(key).digest())


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_filename(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "-" for ch in value)
    return cleaned[:120] or "unknown"
