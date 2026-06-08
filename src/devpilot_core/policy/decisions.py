from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from devpilot_core.cli_models import Finding, Severity


class PolicyEffect(str, Enum):
    """Deterministic policy effects emitted by DevPilot guards.

    FUNC-SPRINT-09 intentionally uses a small vocabulary that maps cleanly to
    CLI exit codes, evidence reports and future MIASI policy matrices.
    """

    ALLOW = "allow"
    WARN = "warn"
    DENY = "deny"
    BLOCK = "block"


@dataclass(frozen=True)
class PolicyDecision:
    """Auditable decision produced by PolicyEngine, PathGuard, SecretGuard or CostGuard.

    A decision is not an exception. It is a structured security/control result
    that can be rendered in JSON, converted to a `Finding`, persisted as an
    evidence report and emitted as EventLog JSONL. The first version is
    deterministic and local-only: no external policy service, no API call and no
    dependency on LLM judgment.
    """

    effect: PolicyEffect
    reason: str
    guard: str
    rule_id: str
    subject: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """Return True when the decision does not block execution."""

        return self.effect in (PolicyEffect.ALLOW, PolicyEffect.WARN)

    @property
    def severity(self) -> Severity:
        """Map policy effect to DevPilot finding severity."""

        if self.effect == PolicyEffect.BLOCK:
            return Severity.BLOCK
        if self.effect == PolicyEffect.DENY:
            return Severity.FAIL
        if self.effect == PolicyEffect.WARN:
            return Severity.WARNING
        return Severity.INFO

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable policy decision."""

        payload: dict[str, Any] = {
            "effect": self.effect.value,
            "ok": self.ok,
            "reason": self.reason,
            "guard": self.guard,
            "rule_id": self.rule_id,
        }
        if self.subject is not None:
            payload["subject"] = self.subject
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload

    def to_finding(self) -> Finding:
        """Convert the decision into the common CLI finding contract."""

        return Finding(
            id=self.rule_id,
            message=self.reason,
            severity=self.severity,
            path=self.subject,
            metadata={"guard": self.guard, "effect": self.effect.value, **self.metadata},
        )
