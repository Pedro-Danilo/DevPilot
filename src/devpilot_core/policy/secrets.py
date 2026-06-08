from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from devpilot_core.policy.decisions import PolicyDecision, PolicyEffect

REDACTED = "[REDACTED]"

_SECRET_KEY_PATTERN = re.compile(
    r"(api[_-]?key|access[_-]?token|refresh[_-]?token|token|secret|password|authorization|bearer)",
    re.IGNORECASE,
)
_SECRET_VALUE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{12,}"),
    re.compile(r"github_pat_[A-Za-z0-9_\-]{12,}"),
    re.compile(r"hf_[A-Za-z0-9_\-]{12,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"(?i)(bearer)\s+([A-Za-z0-9._\-]{12,})"),
    re.compile(
        r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|token|secret|password|authorization)\s*[:=]\s*['\"]?([^'\"\s,;]+)"
    ),
]


@dataclass(frozen=True)
class RedactionResult:
    """Result returned by SecretGuard after recursive redaction."""

    value: Any
    redactions: int

    @property
    def changed(self) -> bool:
        return self.redactions > 0

    def to_dict(self) -> dict[str, Any]:
        return {"redactions": self.redactions, "changed": self.changed}


class SecretGuard:
    """Dependency-free secret scanner/redactor for synthetic and common token patterns.

    This first production-oriented version is conservative and deterministic. It
    redacts values in nested dict/list payloads and blocks policy checks when a
    secret-like pattern is detected. It is not a replacement for an industrial
    secret scanner, but it prevents obvious leakage in reports, traces and CLI
    policy decisions.
    """

    def redact(self, value: Any) -> RedactionResult:
        """Recursively redact sensitive keys and known token-like values."""

        redacted, count = self._redact_value(value)
        return RedactionResult(value=redacted, redactions=count)

    def scan_text(self, text: str | None, *, subject: str | None = None) -> PolicyDecision:
        """Return BLOCK when text contains a secret-like value."""

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
                metadata={"redactions": result.redactions},
            )
        return PolicyDecision(
            effect=PolicyEffect.ALLOW,
            reason="SecretGuard did not detect secret-like content.",
            guard="SecretGuard",
            rule_id="SECRETGUARD_PASS",
            subject=subject,
        )

    def _redact_value(self, value: Any) -> tuple[Any, int]:
        if isinstance(value, dict):
            redacted: dict[Any, Any] = {}
            count = 0
            for key, item in value.items():
                if _is_sensitive_key(str(key)):
                    redacted[key] = REDACTED
                    count += 1
                else:
                    item_value, item_count = self._redact_value(item)
                    redacted[key] = item_value
                    count += item_count
            return redacted, count
        if isinstance(value, list):
            result = []
            count = 0
            for item in value:
                item_value, item_count = self._redact_value(item)
                result.append(item_value)
                count += item_count
            return result, count
        if isinstance(value, tuple):
            value_list, count = self._redact_value(list(value))
            return value_list, count
        if isinstance(value, str):
            return redact_sensitive_string(value)
        return value, 0


def redact_sensitive_data(value: Any) -> Any:
    """Compatibility helper used by reports/events to redact nested payloads."""

    return SecretGuard().redact(value).value


def redact_sensitive_string(value: str) -> tuple[str, int]:
    """Redact known token patterns in a string and return redaction count."""

    redacted = value
    count = 0
    for pattern in _SECRET_VALUE_PATTERNS:
        def _replace(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            if pattern.groups >= 2:
                return f"{match.group(1)}={REDACTED}" if match.group(1).lower() != "bearer" else f"{match.group(1)} {REDACTED}"
            return REDACTED

        redacted = pattern.sub(_replace, redacted)
    return redacted, count


def redact_string(value: str) -> str:
    """Return only the redacted string for callers that do not need counts."""

    return redact_sensitive_string(value)[0]


def _is_sensitive_key(key: str) -> bool:
    return bool(_SECRET_KEY_PATTERN.search(key))
