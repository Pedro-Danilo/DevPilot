from __future__ import annotations

__all__ = [
    "AuditPackBuildOptions",
    "AuditPackBuilder",
    "AuditPackVerifyOptions",
    "AuditPackV2BuildOptions",
    "AuditPackV2Builder",
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
    raise AttributeError(name)
