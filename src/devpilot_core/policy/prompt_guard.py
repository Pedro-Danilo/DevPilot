from __future__ import annotations

import re
from dataclasses import dataclass

from devpilot_core.policy.decisions import PolicyDecision, PolicyEffect


@dataclass(frozen=True)
class PromptInjectionMatch:
    """One deterministic prompt-injection pattern match without raw payload."""

    category: str
    rule_id: str
    severity: str

    def to_dict(self) -> dict[str, str]:
        return {"category": self.category, "rule_id": self.rule_id, "severity": self.severity}


_PROMPT_PATTERNS: tuple[tuple[str, str, str, re.Pattern[str]], ...] = (
    (
        "instruction_override",
        "PROMPT_INJECTION_INSTRUCTION_OVERRIDE",
        "block",
        re.compile(r"(?i)\b(ignore|disregard|forget|override)\b.{0,48}\b(previous|prior|system|developer|policy|instruction|instructions|rules?)\b"),
    ),
    (
        "policy_bypass",
        "PROMPT_INJECTION_POLICY_BYPASS",
        "block",
        re.compile(r"(?i)\b(bypass|disable|turn\s*off|circumvent|skip)\b.{0,48}\b(policy|guard|approval|approval_id|safety|security|validation|validator)\b"),
    ),
    (
        "secret_exfiltration",
        "PROMPT_INJECTION_SECRET_EXFILTRATION",
        "block",
        re.compile(r"(?i)\b(print|show|reveal|dump|exfiltrate|leak|send)\b.{0,48}\b(secret|secrets|token|tokens|api[_ -]?key|password|credentials?|\.env|env vars?)\b"),
    ),
    (
        "role_hijack",
        "PROMPT_INJECTION_ROLE_HIJACK",
        "warn",
        re.compile(r"(?i)\b(you\s+are\s+now|act\s+as|pretend\s+to\s+be)\b.{0,48}\b(root|admin|developer|system|security auditor|owner)\b"),
    ),
    (
        "hidden_instruction",
        "PROMPT_INJECTION_HIDDEN_INSTRUCTION",
        "warn",
        re.compile(r"(?i)\b(hidden|invisible|secret)\b.{0,48}\b(instruction|prompt|message|command)\b"),
    ),
)


class PromptInjectionGuard:
    """Pattern-based local guard for prompt injection attempts.

    FUNC-SPRINT-33 intentionally keeps this deterministic and dependency-free.
    It does not use an LLM judge. It emits sanitized findings with categories and
    rule IDs only; the raw prompt remains outside decision metadata.
    """

    def scan_text(self, text: str | None, *, subject: str | None = None) -> PolicyDecision:
        if not text:
            return PolicyDecision(
                effect=PolicyEffect.ALLOW,
                reason="No prompt payload was provided for prompt-injection scanning.",
                guard="PromptInjectionGuard",
                rule_id="PROMPT_INJECTION_NO_CONTENT",
                subject=subject,
            )

        matches = self.find_matches(text)
        if not matches:
            return PolicyDecision(
                effect=PolicyEffect.ALLOW,
                reason="PromptInjectionGuard did not detect prompt-injection patterns.",
                guard="PromptInjectionGuard",
                rule_id="PROMPT_INJECTION_PASS",
                subject=subject,
            )

        blocking = [match for match in matches if match.severity == "block"]
        effect = PolicyEffect.BLOCK if blocking else PolicyEffect.WARN
        rule_id = blocking[0].rule_id if blocking else matches[0].rule_id
        reason = (
            "PromptInjectionGuard detected high-confidence prompt/policy bypass instructions."
            if blocking
            else "PromptInjectionGuard detected suspicious prompt-injection-like instructions."
        )
        return PolicyDecision(
            effect=effect,
            reason=reason,
            guard="PromptInjectionGuard",
            rule_id=rule_id,
            subject=subject,
            metadata={
                "matches_total": len(matches),
                "categories": sorted({match.category for match in matches}),
                "matches": [match.to_dict() for match in matches],
                "payload_redacted": True,
                "preliminary": True,
            },
        )

    def find_matches(self, text: str) -> list[PromptInjectionMatch]:
        matches: list[PromptInjectionMatch] = []
        for category, rule_id, severity, pattern in _PROMPT_PATTERNS:
            if pattern.search(text):
                matches.append(PromptInjectionMatch(category=category, rule_id=rule_id, severity=severity))
        return matches
