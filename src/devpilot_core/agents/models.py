from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from devpilot_core.cli_models import Finding


@dataclass(frozen=True)
class AgentMessage:
    """Input contract for local/mock DevPilot agents.

    FUNC-SPRINT-51 keeps the original deterministic agent contract and adds an
    optional model-runtime envelope in ``metadata``. Model use is never implicit:
    callers must opt in through AgentRuntime/CLI provider or prompt arguments.
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
class AgentModelCall:
    """Redacted metadata for one AgentRuntime v2 model call.

    The object deliberately stores references, counts and digests only. Raw
    rendered prompts, completions, input values and secrets must not be stored in
    agent results, cost events or reports.
    """

    provider: str
    model: str | None
    task: str
    ok: bool
    exit_code: int
    prompt_id: str | None = None
    prompt_version: str | None = None
    prompt_inputs_used: list[str] = field(default_factory=list)
    prompt_payload_redacted: bool = True
    tokens_estimated: int = 0
    cost_estimate_usd: float = 0.0
    external_api_used: bool = False
    fallback_applied: bool = False
    fallback_from_provider: str | None = None
    fallback_to_provider: str | None = None
    result_digest: dict[str, Any] = field(default_factory=dict)
    raw_prompt_stored: bool = False
    raw_output_stored: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "provider": self.provider,
            "model": self.model,
            "task": self.task,
            "ok": self.ok,
            "exit_code": self.exit_code,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "prompt_inputs_used": list(self.prompt_inputs_used),
            "prompt_payload_redacted": self.prompt_payload_redacted,
            "tokens_estimated": self.tokens_estimated,
            "cost_estimate_usd": self.cost_estimate_usd,
            "external_api_used": self.external_api_used,
            "fallback_applied": self.fallback_applied,
            "fallback_from_provider": self.fallback_from_provider,
            "fallback_to_provider": self.fallback_to_provider,
            "result_digest": self.result_digest,
            "raw_prompt_stored": self.raw_prompt_stored,
            "raw_output_stored": self.raw_output_stored,
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
    model_calls: list[AgentModelCall] = field(default_factory=list)
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
            "model_calls": [call.to_dict() for call in self.model_calls],
            "findings": [finding.to_dict() for finding in self.findings],
            "suggestions": [suggestion.to_dict() for suggestion in self.suggestions],
            "artifacts": self.artifacts,
            "metadata": self.metadata,
        }
