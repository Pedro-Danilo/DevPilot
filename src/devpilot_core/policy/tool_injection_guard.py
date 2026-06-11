from __future__ import annotations

import re
from dataclasses import dataclass

from devpilot_core.policy.decisions import PolicyDecision, PolicyEffect


@dataclass(frozen=True)
class ToolInjectionMatch:
    """One deterministic tool-injection signal without raw payload."""

    category: str
    rule_id: str
    severity: str

    def to_dict(self) -> dict[str, str]:
        return {"category": self.category, "rule_id": self.rule_id, "severity": self.severity}


_TOOL_PATTERNS: tuple[tuple[str, str, str, re.Pattern[str]], ...] = (
    (
        "force_tool_execution",
        "TOOL_INJECTION_FORCE_TOOL_EXECUTION",
        "block",
        re.compile(r"(?i)\b(force|must|directly|silently|without\s+asking)\b.{0,80}\b(use|call|run|execute|invoke)\b.{0,80}\b(tool|tests\.run|patch\.apply|git\.push|deploy|shell|subprocess)\b"),
    ),
    (
        "approval_bypass",
        "TOOL_INJECTION_APPROVAL_BYPASS",
        "block",
        re.compile(r"(?i)\b(without|skip|bypass|ignore)\b.{0,48}\b(approval|approval_id|policy|PolicyEngine|ApprovalPolicyChecker)\b"),
    ),
    (
        "destructive_tool_request",
        "TOOL_INJECTION_DESTRUCTIVE_TOOL_REQUEST",
        "block",
        re.compile(r"(?i)\b(run|execute|call|use)\b.{0,80}\b(rm\s+-rf|del\s+/f|format\s+|git\s+push|git\s+commit|patch\s+apply|deploy|overwrite\s+docs?)\b"),
    ),
    (
        "tool_selector_syntax",
        "TOOL_INJECTION_TOOL_SELECTOR_SYNTAX",
        "warn",
        re.compile(r"(?i)\b(tool|function|function_call|tool_call)\s*[:=]\s*['\"]?[a-zA-Z0-9_.-]{3,}"),
    ),
)


class ToolInjectionGuard:
    """Detect attempts to steer DevPilot into unauthorized tool execution.

    This guard is intentionally pattern-based and conservative. It does not
    authorize or deny real tool use by itself; PolicyEngine combines its decision
    with ApprovalPolicyChecker, PathGuard, SecretGuard and CostGuard.
    """

    def scan_text(self, text: str | None, *, subject: str | None = None) -> PolicyDecision:
        if not text:
            return PolicyDecision(
                effect=PolicyEffect.ALLOW,
                reason="No prompt payload was provided for tool-injection scanning.",
                guard="ToolInjectionGuard",
                rule_id="TOOL_INJECTION_NO_CONTENT",
                subject=subject,
            )

        matches = self.find_matches(text)
        if not matches:
            return PolicyDecision(
                effect=PolicyEffect.ALLOW,
                reason="ToolInjectionGuard did not detect tool-injection patterns.",
                guard="ToolInjectionGuard",
                rule_id="TOOL_INJECTION_PASS",
                subject=subject,
            )

        blocking = [match for match in matches if match.severity == "block"]
        effect = PolicyEffect.BLOCK if blocking else PolicyEffect.WARN
        rule_id = blocking[0].rule_id if blocking else matches[0].rule_id
        reason = (
            "ToolInjectionGuard detected an attempt to force or bypass controlled tool execution."
            if blocking
            else "ToolInjectionGuard detected suspicious tool-selector syntax."
        )
        return PolicyDecision(
            effect=effect,
            reason=reason,
            guard="ToolInjectionGuard",
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

    def find_matches(self, text: str) -> list[ToolInjectionMatch]:
        matches: list[ToolInjectionMatch] = []
        for category, rule_id, severity, pattern in _TOOL_PATTERNS:
            if pattern.search(text):
                matches.append(ToolInjectionMatch(category=category, rule_id=rule_id, severity=severity))
        return matches
