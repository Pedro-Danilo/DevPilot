from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from devpilot_core.cli_models import Finding


@dataclass(frozen=True)
class AgentMessage:
    """Input contract for local/mock DevPilot agents.

    FUNC-SPRINT-12 keeps agent execution deterministic and offline. The message
    explicitly separates the target/idea payload from execution mode so every
    agent can preserve dry-run by default and avoid implicit writes.
    """

    agent_id: str
    target: str | None = None
    idea: str | None = None
    dry_run: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "target": self.target,
            "idea_provided": self.idea is not None,
            "dry_run": self.dry_run,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class AgentToolCall:
    """Auditable representation of a planned or executed tool call."""

    tool_id: str
    action: str
    subject: str | None
    allowed: bool
    dry_run: bool
    policy_exit_code: int
    findings: list[Finding] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "tool_id": self.tool_id,
            "action": self.action,
            "subject": self.subject,
            "allowed": self.allowed,
            "dry_run": self.dry_run,
            "policy_exit_code": self.policy_exit_code,
            "findings": [finding.to_dict() for finding in self.findings],
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


@dataclass(frozen=True)
class AgentSuggestion:
    """Structured suggestion emitted by a mock/local document agent."""

    title: str
    body: str
    target: str | None = None
    severity: str = "info"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "title": self.title,
            "body": self.body,
            "severity": self.severity,
        }
        if self.target:
            payload["target"] = self.target
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


@dataclass(frozen=True)
class AgentRunResult:
    """Internal result contract for AgentRuntime before CLI adaptation."""

    agent_id: str
    agent_name: str
    ok: bool
    message: str
    dry_run: bool
    tool_calls: list[AgentToolCall] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    suggestions: list[AgentSuggestion] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "ok": self.ok,
            "message": self.message,
            "dry_run": self.dry_run,
            "tool_calls": [call.to_dict() for call in self.tool_calls],
            "findings": [finding.to_dict() for finding in self.findings],
            "suggestions": [suggestion.to_dict() for suggestion in self.suggestions],
            "artifacts": self.artifacts,
            "metadata": self.metadata,
        }
