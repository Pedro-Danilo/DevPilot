from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


_ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")


class CredentialReferenceType(str, Enum):
    NONE = "none"
    ENV = "env"
    PROVIDER_NATIVE = "provider-native"
    CONSUMER_SESSION = "consumer-session"


@dataclass(frozen=True)
class ProviderCredentialReference:
    """Reference-only provider credential contract.

    The raw credential value is deliberately absent from this model.  Only the
    execution-boundary auth adapter may resolve a reference into ephemeral
    credential material.
    """

    provider_id: str
    auth_adapter_id: str
    reference_type: CredentialReferenceType
    reference_name: str | None = None
    required: bool = True
    source: str = "explicit-config"

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.provider_id.strip():
            errors.append("provider-id-required")
        if not self.auth_adapter_id.strip():
            errors.append("auth-adapter-id-required")
        if self.reference_type is CredentialReferenceType.ENV:
            if not self.reference_name or not _ENV_NAME_RE.fullmatch(self.reference_name):
                errors.append("env-reference-name-invalid")
        elif self.reference_type is CredentialReferenceType.NONE:
            if self.reference_name:
                errors.append("no-secret-reference-must-not-name-secret")
        elif self.reference_type is CredentialReferenceType.CONSUMER_SESSION:
            errors.append("consumer-session-reference-blocked")
        elif self.reference_type is CredentialReferenceType.PROVIDER_NATIVE:
            if not self.reference_name:
                errors.append("provider-native-reference-name-required")
        return tuple(errors)

    def to_dict(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "auth_adapter_id": self.auth_adapter_id,
            "reference_type": self.reference_type.value,
            "reference_name": self.reference_name,
            "required": self.required,
            "source": self.source,
            "raw_secret_present": False,
        }


@dataclass(frozen=True)
class CredentialMaterial:
    """Ephemeral execution-boundary credential material.

    ``secret`` is intentionally excluded from repr/equality-oriented evidence.
    Callers must never serialize ``__dict__``; use :meth:`safe_dict` instead.
    """

    provider_id: str
    auth_adapter_id: str
    reference_type: str
    reference_name: str | None
    available: bool
    secret: str | None = field(default=None, repr=False, compare=False)
    reason: str = "available"

    def safe_dict(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "auth_adapter_id": self.auth_adapter_id,
            "reference_type": self.reference_type,
            "reference_name": self.reference_name,
            "available": self.available,
            "reason": self.reason,
            "secret_exposed": False,
        }


class CredentialResolutionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class LocalLoopbackNoSecretAdapter:
    adapter_id = "no-secret-local"

    def resolve(self, reference: ProviderCredentialReference, *, environ: Mapping[str, str] | None = None) -> CredentialMaterial:
        del environ
        errors = reference.validate()
        if reference.reference_type is not CredentialReferenceType.NONE or errors:
            raise CredentialResolutionError("local-no-secret-reference-invalid", "Local loopback auth does not accept credential material.")
        return CredentialMaterial(
            provider_id=reference.provider_id,
            auth_adapter_id=reference.auth_adapter_id,
            reference_type=reference.reference_type.value,
            reference_name=None,
            available=True,
            secret=None,
            reason="no-secret-required",
        )


class EnvApiKeyAdapter:
    adapter_id = "env-api-key-future"

    def resolve(self, reference: ProviderCredentialReference, *, environ: Mapping[str, str] | None = None) -> CredentialMaterial:
        errors = reference.validate()
        if reference.reference_type is not CredentialReferenceType.ENV or errors:
            raise CredentialResolutionError("env-credential-reference-invalid", "Environment API-key reference is invalid.")
        env = environ if environ is not None else os.environ
        assert reference.reference_name is not None
        value = env.get(reference.reference_name)
        if value is None or not value.strip():
            raise CredentialResolutionError("credential-missing", "Required provider credential reference is not available in the execution environment.")
        if len(value.strip()) < 8 or any(ch in value for ch in "\r\n\x00"):
            raise CredentialResolutionError("credential-invalid", "Provider credential value failed bounded structural validation.")
        return CredentialMaterial(
            provider_id=reference.provider_id,
            auth_adapter_id=reference.auth_adapter_id,
            reference_type=reference.reference_type.value,
            reference_name=reference.reference_name,
            available=True,
            secret=value,
            reason="resolved-at-execution-boundary",
        )


class ProviderNativeIdentityAdapter:
    adapter_id = "provider-native-identity-future"

    def resolve(self, reference: ProviderCredentialReference, *, environ: Mapping[str, str] | None = None) -> CredentialMaterial:
        del environ
        errors = reference.validate()
        if reference.reference_type is not CredentialReferenceType.PROVIDER_NATIVE or errors:
            raise CredentialResolutionError("provider-native-reference-invalid", "Provider-native identity reference is invalid.")
        return CredentialMaterial(
            provider_id=reference.provider_id,
            auth_adapter_id=reference.auth_adapter_id,
            reference_type=reference.reference_type.value,
            reference_name=reference.reference_name,
            available=True,
            secret=None,
            reason="provider-native-identity-reference-only",
        )


class ConsumerSessionAdapter:
    adapter_id = "consumer-session-adapter"

    def resolve(self, reference: ProviderCredentialReference, *, environ: Mapping[str, str] | None = None) -> CredentialMaterial:
        del reference, environ
        raise CredentialResolutionError(
            "consumer-session-blocked",
            "Consumer browser sessions, cookies and subscription piggyback are not supported provider credentials.",
        )


def auth_adapter_for(reference: ProviderCredentialReference):
    mapping = {
        "no-secret-local": LocalLoopbackNoSecretAdapter,
        "env-api-key-future": EnvApiKeyAdapter,
        "provider-native-identity-future": ProviderNativeIdentityAdapter,
        "consumer-session-adapter": ConsumerSessionAdapter,
    }
    adapter_type = mapping.get(reference.auth_adapter_id)
    if adapter_type is None:
        raise CredentialResolutionError("auth-adapter-unknown", "Credential reference names an unknown auth adapter.")
    return adapter_type()
