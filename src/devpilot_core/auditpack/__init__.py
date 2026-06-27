from __future__ import annotations

__all__ = [
    "AuditPackBuildOptions",
    "AuditPackBuilder",
    "AuditPackVerifyOptions",
    "AuditPackV2BuildOptions",
    "AuditPackV2Builder",
    "AuditPackCryptoOptions",
    "AuditPackV2VerifyOptions",
    "AuditPackV2Verifier",
]


def __getattr__(name: str):
    if name in {"AuditPackBuildOptions", "AuditPackBuilder", "AuditPackVerifyOptions"}:
        from .builder import AuditPackBuildOptions, AuditPackBuilder, AuditPackVerifyOptions

        mapping = {
            "AuditPackBuildOptions": AuditPackBuildOptions,
            "AuditPackBuilder": AuditPackBuilder,
            "AuditPackVerifyOptions": AuditPackVerifyOptions,
        }
        return mapping[name]
    if name in {"AuditPackV2BuildOptions", "AuditPackV2Builder"}:
        from .manifest_v2 import AuditPackV2BuildOptions, AuditPackV2Builder

        mapping = {
            "AuditPackV2BuildOptions": AuditPackV2BuildOptions,
            "AuditPackV2Builder": AuditPackV2Builder,
        }
        return mapping[name]
    if name in {"AuditPackCryptoOptions"}:
        from .crypto import AuditPackCryptoOptions

        return AuditPackCryptoOptions
    if name in {"AuditPackV2VerifyOptions", "AuditPackV2Verifier"}:
        from .verify_v2 import AuditPackV2VerifyOptions, AuditPackV2Verifier

        mapping = {
            "AuditPackV2VerifyOptions": AuditPackV2VerifyOptions,
            "AuditPackV2Verifier": AuditPackV2Verifier,
        }
        return mapping[name]
    raise AttributeError(name)
