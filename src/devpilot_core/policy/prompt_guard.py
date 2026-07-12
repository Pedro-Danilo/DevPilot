from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.policy.decisions import PolicyDecision, PolicyEffect
from devpilot_core.policy.guard_catalog import DEFAULT_GUARD_PATTERN_CATALOG_PATH, GuardPatternRule, catalog_block_decision_metadata, load_guard_pattern_catalog


@dataclass(frozen=True)
class PromptInjectionMatch:
    """One deterministic prompt-injection pattern match without raw payload."""

    category: str
    rule_id: str
    severity: str
    rule_source: str = "python:fallback:policy.prompt_guard"
    catalog_version: str = "fallback-compatible"
    built_in_mandatory: bool = True
    critical: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "rule_source": self.rule_source,
            "catalog_version": self.catalog_version,
            "built_in_mandatory": self.built_in_mandatory,
            "critical": self.critical,
        }


class PromptInjectionGuard:
    """Pattern-based local guard for prompt injection attempts.

    POST-H-033-E keeps built-in mandatory patterns non-removable in code while
    allowing schema-validated local extensions from `.devpilot/policy/guard_pattern_catalog.json`.
    The guard remains deterministic, dependency-light and does not use an LLM judge.
    """

    def __init__(self, root: Path | None = None, *, catalog_path: str | Path = DEFAULT_GUARD_PATTERN_CATALOG_PATH) -> None:
        self.root = Path(root).resolve() if root is not None else Path.cwd().resolve()
        self.catalog_path = Path(catalog_path)

    def scan_text(self, text: str | None, *, subject: str | None = None) -> PolicyDecision:
        catalog = load_guard_pattern_catalog(self.root, self.catalog_path)
        if catalog.has_blocking_catalog_findings:
            return PolicyDecision(
                effect=PolicyEffect.BLOCK,
                reason="PromptInjectionGuard failed closed because the policy guard pattern catalog is invalid.",
                guard="PromptInjectionGuard",
                rule_id="POLICY_GUARD_PATTERN_CATALOG_INVALID_BLOCKED",
                subject=subject,
                metadata=catalog_block_decision_metadata(catalog),
            )
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
                "guard_pattern_catalog": catalog.metadata(),
            },
        )

    def find_matches(self, text: str) -> list[PromptInjectionMatch]:
        catalog = load_guard_pattern_catalog(self.root, self.catalog_path)
        matches: list[PromptInjectionMatch] = []
        for rule in catalog.prompt_patterns:
            if rule.compiled.search(text):
                matches.append(_match_from_rule(rule))
        return matches


def _match_from_rule(rule: GuardPatternRule) -> PromptInjectionMatch:
    return PromptInjectionMatch(
        category=rule.category,
        rule_id=rule.rule_id,
        severity=rule.severity,
        rule_source=rule.source_catalog,
        catalog_version=rule.catalog_version,
        built_in_mandatory=rule.built_in_mandatory,
        critical=rule.critical,
    )
