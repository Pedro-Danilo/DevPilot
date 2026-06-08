from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy.cost_guard import CostGuard, CostPolicy
from devpilot_core.policy.decisions import PolicyDecision, PolicyEffect
from devpilot_core.policy.path_guard import PathGuard, PathPolicy
from devpilot_core.policy.secrets import SecretGuard


@dataclass(frozen=True)
class PolicyRequest:
    """Input contract for deterministic policy evaluation."""

    action: str
    path: str | None = None
    text: str | None = None
    external_api: bool = False
    provider: str | None = None
    estimated_cost_usd: float = 0.0
    dry_run: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "path": self.path,
            "text_provided": self.text is not None,
            "external_api": self.external_api,
            "provider": self.provider,
            "estimated_cost_usd": self.estimated_cost_usd,
            "dry_run": self.dry_run,
            "metadata": self.metadata,
        }


class PolicyEngine:
    """Deterministic policy orchestrator for DevPilot safe execution.

    The engine coordinates PathGuard, SecretGuard and CostGuard. It is the first
    executable MIASI policy layer in DevPilot and intentionally fails closed for
    dangerous actions, external APIs and detected secrets. It evaluates requests;
    it does not execute the requested operation.
    """

    dangerous_actions = {"delete", "remove", "rm", "rmdir", "overwrite", "execute", "shell", "network-call", "external-api"}

    def __init__(
        self,
        root: Path,
        *,
        path_policy: PathPolicy | None = None,
        cost_policy: CostPolicy | None = None,
    ) -> None:
        self.root = root.resolve()
        self.path_guard = PathGuard(self.root, policy=path_policy)
        self.secret_guard = SecretGuard()
        self.cost_guard = CostGuard(policy=cost_policy)

    def evaluate(self, request: PolicyRequest) -> CommandResult:
        """Evaluate a policy request and return a normalized CommandResult."""

        decisions: list[PolicyDecision] = []
        action = request.action.strip().lower() or "unknown"

        if action in self.dangerous_actions and request.dry_run:
            decisions.append(
                PolicyDecision(
                    effect=PolicyEffect.BLOCK,
                    reason="PolicyEngine blocks dangerous actions by default, even in dry-run, until human approval exists.",
                    guard="PolicyEngine",
                    rule_id="POLICY_DANGEROUS_ACTION_BLOCKED",
                    subject=request.path,
                    metadata={"action": action, "dry_run": request.dry_run},
                )
            )

        decisions.append(self.path_guard.evaluate(request.path, action=action))
        decisions.append(self.secret_guard.scan_text(request.text, subject=request.path))
        decisions.append(
            self.cost_guard.evaluate(
                external_api=request.external_api,
                provider=request.provider,
                estimated_cost_usd=request.estimated_cost_usd,
            )
        )

        # Remove informational no-op decisions from findings, but keep them in data.
        blocking = [decision for decision in decisions if decision.effect == PolicyEffect.BLOCK]
        denying = [decision for decision in decisions if decision.effect == PolicyEffect.DENY]
        warnings = [decision for decision in decisions if decision.effect == PolicyEffect.WARN]
        ok = not blocking and not denying
        exit_code = ExitCode.BLOCK if blocking else (ExitCode.FAIL if denying else ExitCode.PASS)
        findings = [decision.to_finding() for decision in decisions if decision.effect != PolicyEffect.ALLOW]
        if not findings and ok:
            findings = [Finding(id="POLICY_PASS", message="PolicyEngine allowed the simulated request.", severity=Severity.INFO)]

        summary = {
            "allowed": ok,
            "blocked": bool(blocking),
            "denied": bool(denying),
            "warnings": len(warnings),
            "decisions_total": len(decisions),
            "guards": sorted({decision.guard for decision in decisions}),
        }
        request_payload = request.to_dict()
        if request.text is not None:
            request_payload["text_preview"] = self.secret_guard.redact(request.text).value
        data = {
            "request": request_payload,
            "summary": summary,
            "decisions": [decision.to_dict() for decision in decisions],
        }
        return CommandResult(
            command="policy check",
            ok=ok,
            exit_code=exit_code,
            message="Policy check passed." if ok else "Policy check blocked or denied the simulated request.",
            data=data,
            findings=findings,
        )
