from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.policy.decisions import PolicyDecision, PolicyEffect
from devpilot_core.policy.guard_catalog import DEFAULT_GUARD_PATTERN_CATALOG_PATH, catalog_block_decision_metadata, load_guard_pattern_catalog

REDACTED = "[REDACTED]"

_SECRET_KEY_PATTERN = re.compile(
    r"(api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|auth[_-]?token|token|secret|password|passwd|pwd|authorization|bearer|private[_-]?key|client[_-]?secret|database[_-]?url|connection[_-]?string|webhook)",
    re.IGNORECASE,
)

# Ordered from most specific to broadest. Patterns intentionally target common
# synthetic/dev tokens and well-known token shapes. They do not try to be a full
# industrial secret scanner.
_SECRET_VALUE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"sk-proj-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"sk-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{12,}"),
    re.compile(r"github_pat_[A-Za-z0-9_\-]{12,}"),
    re.compile(r"glpat-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"hf_[A-Za-z0-9_\-]{12,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ASIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"(?i)-----BEGIN\s+(RSA\s+|EC\s+|OPENSSH\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(RSA\s+|EC\s+|OPENSSH\s+)?PRIVATE\s+KEY-----"),
    re.compile(r"(?i)(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s'\"<>]+:[^\s'\"<>]+@[^\s'\"<>]+"),
    re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9_/\-]{20,}"),
    re.compile(r"https://discord(?:app)?\.com/api/webhooks/\d+/[A-Za-z0-9_\-]{20,}"),
    re.compile(r"(?i)(bearer)\s+([A-Za-z0-9._\-]{12,})"),
    re.compile(r"(?i)(basic)\s+([A-Za-z0-9+/=]{12,})"),
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|auth[_-]?token|token|secret|password|passwd|pwd|authorization|client[_-]?secret|database[_-]?url|connection[_-]?string)\s*[:=]\s*['\"]?([^'\"\s,;]+)"),
]


@dataclass(frozen=True)
class RedactionResult:
    """Result returned by SecretGuard after recursive redaction."""

    value: Any
    redactions: int
    catalog_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def changed(self) -> bool:
        return self.redactions > 0

    def to_dict(self) -> dict[str, Any]:
        return {"redactions": self.redactions, "changed": self.changed, "guard_pattern_catalog": self.catalog_metadata}


class SecretGuard:
    """Dependency-free secret scanner/redactor for synthetic and common token patterns.

    FUNC-SPRINT-33 hardens the initial scanner with additional common token
    shapes, private-key blocks and environment/connection-string leaks. It
    remains deterministic and local-only. It is not a replacement for a full
    industrial secret-scanning engine, but it prevents obvious leakage in
    reports, traces, stdout/stderr and policy evidence.
    """

    def __init__(self, root: Path | None = None, *, catalog_path: str | Path = DEFAULT_GUARD_PATTERN_CATALOG_PATH) -> None:
        self.root = Path(root).resolve() if root is not None else Path.cwd().resolve()
        self.catalog_path = Path(catalog_path)

    def redact(self, value: Any) -> RedactionResult:
        """Recursively redact sensitive keys and known token-like values."""

        catalog = load_guard_pattern_catalog(self.root, self.catalog_path)
        redacted, count = self._redact_value(value, catalog=catalog)
        return RedactionResult(value=redacted, redactions=count, catalog_metadata=catalog.metadata())

    def scan_text(self, text: str | None, *, subject: str | None = None) -> PolicyDecision:
        """Return BLOCK when text contains a secret-like value."""

        catalog = load_guard_pattern_catalog(self.root, self.catalog_path)
        if catalog.has_blocking_catalog_findings:
            return PolicyDecision(
                effect=PolicyEffect.BLOCK,
                reason="SecretGuard failed closed because the policy guard pattern catalog is invalid.",
                guard="SecretGuard",
                rule_id="POLICY_GUARD_PATTERN_CATALOG_INVALID_BLOCKED",
                subject=subject,
                metadata=catalog_block_decision_metadata(catalog),
            )
        if not text:
            return PolicyDecision(
                effect=PolicyEffect.ALLOW,
                reason="No secret-like content was provided.",
                guard="SecretGuard",
                rule_id="SECRETGUARD_NO_CONTENT",
                subject=subject,
            )
        result = self.redact(text)
        if result.changed:
            return PolicyDecision(
                effect=PolicyEffect.BLOCK,
                reason="SecretGuard detected and redacted secret-like content.",
                guard="SecretGuard",
                rule_id="SECRETGUARD_SECRET_DETECTED",
                subject=subject,
                metadata={"redactions": result.redactions, "payload_redacted": True, "preliminary": True, "guard_pattern_catalog": result.catalog_metadata},
            )
        return PolicyDecision(
            effect=PolicyEffect.ALLOW,
            reason="SecretGuard did not detect secret-like content.",
            guard="SecretGuard",
            rule_id="SECRETGUARD_PASS",
            subject=subject,
        )

    def _redact_value(self, value: Any, *, catalog=None) -> tuple[Any, int]:
        catalog = catalog or load_guard_pattern_catalog(self.root, self.catalog_path)
        if isinstance(value, dict):
            redacted: dict[Any, Any] = {}
            count = 0
            for key, item in value.items():
                if _is_sensitive_key(str(key), catalog=catalog):
                    redacted[key] = REDACTED
                    count += 1
                else:
                    item_value, item_count = self._redact_value(item, catalog=catalog)
                    redacted[key] = item_value
                    count += item_count
            return redacted, count
        if isinstance(value, list):
            result = []
            count = 0
            for item in value:
                item_value, item_count = self._redact_value(item, catalog=catalog)
                result.append(item_value)
                count += item_count
            return result, count
        if isinstance(value, tuple):
            value_list, count = self._redact_value(list(value), catalog=catalog)
            return value_list, count
        if isinstance(value, str):
            return _redact_sensitive_string_with_catalog(value, catalog=catalog)
        return value, 0


def redact_sensitive_data(value: Any) -> Any:
    """Compatibility helper used by reports/events to redact nested payloads."""

    return SecretGuard().redact(value).value


def redact_sensitive_string(value: str, *, root: Path | None = None, catalog_path: str | Path = DEFAULT_GUARD_PATTERN_CATALOG_PATH) -> tuple[str, int]:
    """Redact known token patterns in a string and return redaction count."""

    catalog = load_guard_pattern_catalog(root, catalog_path)
    redacted = value
    count = 0
    return _redact_sensitive_string_with_catalog(value, catalog=catalog)


def _redact_sensitive_string_with_catalog(value: str, *, catalog) -> tuple[str, int]:
    redacted = value
    count = 0
    patterns = [rule.compiled for rule in catalog.secret_value_patterns] if not catalog.has_blocking_catalog_findings else _SECRET_VALUE_PATTERNS
    for pattern in patterns:
        def _replace(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            groups = match.groups()
            first_group = groups[0].lower() if groups and isinstance(groups[0], str) else ""
            if first_group in {"bearer", "basic"}:
                return f"{match.group(1)} {REDACTED}"
            if pattern.groups >= 2 and first_group:
                return f"{match.group(1)}={REDACTED}"
            return REDACTED

        redacted = pattern.sub(_replace, redacted)
    return redacted, count


def redact_string(value: str) -> str:
    """Return only the redacted string for callers that do not need counts."""

    return redact_sensitive_string(value)[0]


def _is_sensitive_key(key: str, *, catalog=None) -> bool:
    if catalog is not None and not catalog.has_blocking_catalog_findings:
        return bool(catalog.secret_key_pattern.search(key))
    return bool(_SECRET_KEY_PATTERN.search(key))
