from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.approval.policy import ApprovalPolicyChecker, ApprovalPolicyInput
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy.cost_guard import CostGuard, CostPolicy
from devpilot_core.policy.decisions import PolicyDecision, PolicyEffect
from devpilot_core.policy.path_guard import PathGuard, PathPolicy
from devpilot_core.policy.prompt_guard import PromptInjectionGuard
from devpilot_core.policy.secrets import REDACTED, SecretGuard
from devpilot_core.policy.tool_injection_guard import ToolInjectionGuard
from devpilot_core.identity import IdentityRegistry, RbacCheckInput, permission_for_action

POST_H_012_D_CREATED_BY = "POST-H-012-D"


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
    approval_id: str | None = None
    tool_id: str | None = None
    subject: str | None = None
    actor: str | None = None
    role_at_decision: str | None = None
    command_id: str | None = None
    tool_call_id: str | None = None
    subject_hash: str | None = None
    interface: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "path": self.path,
            "text_provided": self.text is not None,
            "external_api": self.external_api,
            "provider": self.provider,
            "estimated_cost_usd": self.estimated_cost_usd,
            "dry_run": self.dry_run,
            "approval_id": self.approval_id,
            "tool_id": self.tool_id,
            "subject": self.subject,
            "metadata": self.metadata,
            "actor": self.actor,
            "role_at_decision": self.role_at_decision,
            "command_id": self.command_id,
            "tool_call_id": self.tool_call_id,
            "subject_hash": self.subject_hash,
            "interface": self.interface,
        }


REDACTED_TEXT_PREVIEW = REDACTED


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
        observability_enabled: bool = True,
    ) -> None:
        self.root = root.resolve()
        self.observability_enabled = observability_enabled
        self.path_guard = PathGuard(self.root, policy=path_policy)
        self.secret_guard = SecretGuard()
        self.prompt_injection_guard = PromptInjectionGuard()
        self.tool_injection_guard = ToolInjectionGuard()
        self.cost_guard = CostGuard(policy=cost_policy)
        self.approval_checker = ApprovalPolicyChecker(self.root)
        self.sensitive_action_catalog_path = self.root / ".devpilot" / "approval" / "sensitive_action_catalog.json"
        self.identity_registry_path = self.root / ".devpilot" / "identity" / "identity_registry.json"

    def evaluate(self, request: PolicyRequest) -> CommandResult:
        """Evaluate a policy request and return a normalized CommandResult."""

        decisions: list[PolicyDecision] = []
        action = request.action.strip().lower() or "unknown"
        interface = _norm(request.interface or request.metadata.get("interface") or "cli")
        actor = request.actor or str(request.metadata.get("actor_id") or request.metadata.get("actor") or "") or None
        role_at_decision = request.role_at_decision or _norm(request.metadata.get("role_at_decision")) or None
        command_id = request.command_id or _norm(request.metadata.get("command_id")) or None
        tool_call_id = request.tool_call_id or _norm(request.metadata.get("tool_call_id")) or None
        subject_hash = request.subject_hash or _norm(request.metadata.get("subject_hash")) or None
        sensitive_action = self._resolve_sensitive_action(tool_id=request.tool_id, action=action)

        approval_decision = self.approval_checker.evaluate(
            ApprovalPolicyInput(
                action=action,
                approval_id=request.approval_id,
                tool_id=request.tool_id,
                subject=request.subject,
                path=request.path,
                metadata={**request.metadata, "interface": interface, "actor_id": actor, "role_at_decision": role_at_decision, "command_id": command_id, "tool_call_id": tool_call_id, "subject_hash": subject_hash},
                actor_id=actor,
                role_at_decision=role_at_decision,
                command_id=command_id,
                tool_call_id=tool_call_id,
                subject_hash=subject_hash,
            )
        )
        decisions.append(approval_decision)
        normalized_approval_decision = self._normalize_approval_decision(approval_decision, request=request, sensitive_action=sensitive_action)
        if normalized_approval_decision is not None:
            decisions.append(normalized_approval_decision)
        approval_valid = approval_decision.rule_id == "APPROVAL_VALID" and approval_decision.effect == PolicyEffect.ALLOW

        # FUNC-SPRINT-95 + POST-H-012-D: local RBAC is enforced for
        # approval-gated and catalog-sensitive requests. Missing actor falls
        # back to the active local identity so legacy CLI/tests remain
        # deterministic while new UI/API/agent paths can pass actor explicitly.
        rbac_required = approval_decision.metadata.get("approval_required", False) or action in self.dangerous_actions or sensitive_action is not None
        if rbac_required:
            rbac_decision = IdentityRegistry(self.root).evaluate(
                RbacCheckInput(
                    actor_id=actor,
                    action=action,
                    permission=permission_for_action(action, tool_id=request.tool_id),
                    tool_id=request.tool_id,
                    subject=request.subject or request.path,
                    workspace_id=str(request.metadata.get("workspace_id") or "") or None,
                    require_sensitive=True,
                )
            )
            decisions.append(rbac_decision)
            normalized_rbac_decision = self._normalize_rbac_decision(rbac_decision, request=request, sensitive_action=sensitive_action)
            if normalized_rbac_decision is not None:
                decisions.append(normalized_rbac_decision)

        if sensitive_action is not None:
            decisions.extend(
                self._sensitive_action_decisions(
                    sensitive_action,
                    request=request,
                    action=action,
                    actor_id=actor,
                    interface=interface,
                )
            )

        if action in self.dangerous_actions and request.dry_run and not approval_valid:
            decisions.append(
                PolicyDecision(
                    effect=PolicyEffect.BLOCK,
                    reason="PolicyEngine blocks dangerous actions by default, even in dry-run, until scoped human approval is valid.",
                    guard="PolicyEngine",
                    rule_id="POLICY_DANGEROUS_ACTION_BLOCKED",
                    subject=request.path or request.subject,
                    metadata={"action": action, "dry_run": request.dry_run, "approval_valid": approval_valid},
                )
            )

        decisions.append(self.path_guard.evaluate(request.path, action=action))
        decisions.append(self.secret_guard.scan_text(request.text, subject=request.path or request.subject))
        decisions.append(self.prompt_injection_guard.scan_text(request.text, subject=request.path or request.subject))
        decisions.append(self.tool_injection_guard.scan_text(request.text, subject=request.path or request.subject))
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
            "approval_required": approval_decision.metadata.get("approval_required", False),
            "approval_valid": approval_valid,
            "post_h_012_d_enforced": True,
            "policy_engine_enforcement_created_by": POST_H_012_D_CREATED_BY,
            "sensitive_action_matched": sensitive_action is not None,
            "sensitive_action_id": sensitive_action.get("action_id") if sensitive_action else None,
            "interface": interface,
            "actor_id": actor,
            "role_at_decision": role_at_decision,
            "command_id_bound": bool(command_id),
            "tool_call_id_bound": bool(tool_call_id),
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
        }
        request_payload = request.to_dict()
        if request.text is not None:
            injection_decisions = [
                decision
                for decision in decisions
                if decision.guard in {"PromptInjectionGuard", "ToolInjectionGuard"} and decision.effect != PolicyEffect.ALLOW
            ]
            request_payload["text_preview"] = REDACTED_TEXT_PREVIEW if injection_decisions else self.secret_guard.redact(request.text).value
        data = {
            "request": request_payload,
            "summary": summary,
            "decisions": [decision.to_dict() for decision in decisions],
        }
        result = CommandResult(
            command="policy check",
            ok=ok,
            exit_code=exit_code,
            message="Policy check passed." if ok else "Policy check blocked or denied the simulated request.",
            data=data,
            findings=findings,
        )
        self._record_policy_observability(result, request)
        return result

    def _resolve_sensitive_action(self, *, tool_id: str | None, action: str) -> dict[str, Any] | None:
        catalog = _load_json(self.sensitive_action_catalog_path)
        requested_action = _norm(action)
        requested_tool = _norm(tool_id)
        for entry in catalog.get("actions", []):
            if not isinstance(entry, dict):
                continue
            action_id = _norm(entry.get("action_id"))
            action_tail = action_id.split(".")[-1]
            tool_ids = {_norm(item) for item in entry.get("tool_ids", [])}
            if requested_action and requested_action in {action_id, action_tail}:
                return entry
            if requested_tool and requested_tool in tool_ids and requested_action in {action_id, action_tail}:
                return entry
        return None

    def _normalize_approval_decision(
        self,
        decision: PolicyDecision,
        *,
        request: PolicyRequest,
        sensitive_action: dict[str, Any] | None,
    ) -> PolicyDecision | None:
        if decision.rule_id == "APPROVAL_REQUIRED_MISSING":
            return PolicyDecision(
                effect=PolicyEffect.BLOCK,
                reason="APPROVAL_REQUIRED: sensitive or approval-gated action requires a valid scoped approval_id.",
                guard="PolicyEngine",
                rule_id="APPROVAL_REQUIRED",
                subject=request.subject or request.path,
                metadata={
                    "created_by": POST_H_012_D_CREATED_BY,
                    "original_rule_id": decision.rule_id,
                    "sensitive_action_id": sensitive_action.get("action_id") if sensitive_action else None,
                    "approval_required": True,
                    "actor_id": request.actor,
                    "tool_id": request.tool_id,
                    "action": request.action,
                    "interface": request.interface or request.metadata.get("interface") or "cli",
                },
            )
        if decision.rule_id == "APPROVAL_BINDING_MISMATCH":
            return PolicyDecision(
                effect=PolicyEffect.BLOCK,
                reason="APPROVAL_SCOPE_MISMATCH: approval_id does not match the exact actor/role/tool/action/subject/command/tool_call scope.",
                guard="PolicyEngine",
                rule_id="APPROVAL_SCOPE_MISMATCH",
                subject=request.subject or request.path,
                metadata={
                    "created_by": POST_H_012_D_CREATED_BY,
                    "original_rule_id": decision.rule_id,
                    "binding_findings": decision.metadata.get("binding_findings", []),
                    "sensitive_action_id": sensitive_action.get("action_id") if sensitive_action else None,
                    "actor_id": request.actor,
                    "tool_id": request.tool_id,
                    "action": request.action,
                },
            )
        return None

    def _normalize_rbac_decision(
        self,
        decision: PolicyDecision,
        *,
        request: PolicyRequest,
        sensitive_action: dict[str, Any] | None,
    ) -> PolicyDecision | None:
        if decision.effect != PolicyEffect.BLOCK or decision.guard != "RBAC":
            return None
        return PolicyDecision(
            effect=PolicyEffect.BLOCK,
            reason="RBAC_DENIED: local RBAC denied this sensitive or approval-gated policy request.",
            guard="PolicyEngine",
            rule_id="RBAC_DENIED",
            subject=request.subject or request.path,
            metadata={
                "created_by": POST_H_012_D_CREATED_BY,
                "original_rule_id": decision.rule_id,
                "sensitive_action_id": sensitive_action.get("action_id") if sensitive_action else None,
                "actor_id": decision.metadata.get("actor_id") or request.actor,
                "actor_roles": decision.metadata.get("actor_roles", []),
                "tool_id": request.tool_id,
                "action": request.action,
            },
        )

    def _sensitive_action_decisions(
        self,
        sensitive_action: dict[str, Any],
        *,
        request: PolicyRequest,
        action: str,
        actor_id: str | None,
        interface: str,
    ) -> list[PolicyDecision]:
        decisions: list[PolicyDecision] = []
        action_id = _norm(sensitive_action.get("action_id"))
        required_role = _norm(sensitive_action.get("requires_rbac_role"))
        blocked_interfaces = {_norm(item) for item in sensitive_action.get("blocked_interfaces", [])}
        allowed_interfaces = {_norm(item) for item in sensitive_action.get("allowed_interfaces", [])}
        executable = bool(sensitive_action.get("executable"))
        source_mutation_allowed = bool(sensitive_action.get("source_mutation_allowed"))
        default_effect = _norm(sensitive_action.get("default_effect")) or "block"
        status = _norm(sensitive_action.get("status"))

        if interface in blocked_interfaces:
            decisions.append(
                PolicyDecision(
                    effect=PolicyEffect.BLOCK,
                    reason="Sensitive action is blocked for the requested interface by SensitiveActionCatalog.",
                    guard="SensitiveActionCatalog",
                    rule_id="SENSITIVE_ACTION_INTERFACE_BLOCKED",
                    subject=request.subject or request.path,
                    metadata={
                        "created_by": POST_H_012_D_CREATED_BY,
                        "sensitive_action_id": action_id,
                        "interface": interface,
                        "blocked_interfaces": sorted(blocked_interfaces),
                        "allowed_interfaces": sorted(allowed_interfaces),
                    },
                )
            )
        elif allowed_interfaces and interface not in allowed_interfaces:
            decisions.append(
                PolicyDecision(
                    effect=PolicyEffect.BLOCK,
                    reason="Sensitive action interface is not explicitly allowed; deny-by-default applies.",
                    guard="SensitiveActionCatalog",
                    rule_id="SENSITIVE_ACTION_INTERFACE_DENIED",
                    subject=request.subject or request.path,
                    metadata={
                        "created_by": POST_H_012_D_CREATED_BY,
                        "sensitive_action_id": action_id,
                        "interface": interface,
                        "allowed_interfaces": sorted(allowed_interfaces),
                    },
                )
            )

        role_decision = self._required_role_decision(
            required_role=required_role,
            actor_id=actor_id,
            request=request,
            sensitive_action_id=action_id,
        )
        if role_decision is not None:
            decisions.append(role_decision)

        if status == "blocked" or default_effect in {"block", "deny"} or not executable or not source_mutation_allowed:
            decisions.append(
                PolicyDecision(
                    effect=PolicyEffect.BLOCK,
                    reason="Sensitive action remains non-executable or deny/block-by-default; POST-H-012-D does not enable side effects.",
                    guard="SensitiveActionCatalog",
                    rule_id="SENSITIVE_ACTION_NON_EXECUTABLE_BLOCKED",
                    subject=request.subject or request.path,
                    metadata={
                        "created_by": POST_H_012_D_CREATED_BY,
                        "sensitive_action_id": action_id,
                        "domain": sensitive_action.get("domain"),
                        "risk_level": sensitive_action.get("risk_level"),
                        "status": status,
                        "default_effect": default_effect,
                        "executable": executable,
                        "source_mutation_allowed": source_mutation_allowed,
                        "remote_execution_enabled": False,
                        "connector_write_enabled": False,
                        "plugin_execution_enabled": False,
                    },
                )
            )
        return decisions

    def _required_role_decision(
        self,
        *,
        required_role: str,
        actor_id: str | None,
        request: PolicyRequest,
        sensitive_action_id: str,
    ) -> PolicyDecision | None:
        if not required_role:
            return None
        registry = _load_json(self.identity_registry_path)
        roles = {str(role.get("role_id", "")).strip() for role in registry.get("roles", []) if isinstance(role, dict)}
        actor_roles: list[str] = []
        requested_actor = (actor_id or registry.get("active_actor_id") or "local-owner")
        for actor in registry.get("actors", []):
            if isinstance(actor, dict) and str(actor.get("actor_id", "")).strip() == str(requested_actor):
                actor_roles = [str(role).strip() for role in actor.get("roles", []) if str(role).strip()]
                break
        required_role_declared = required_role in roles
        actor_has_required_role = required_role in actor_roles
        if required_role_declared and actor_has_required_role:
            return PolicyDecision(
                effect=PolicyEffect.ALLOW,
                reason="Required RBAC role is declared and assigned to the local actor.",
                guard="RBAC",
                rule_id="RBAC_REQUIRED_ROLE_ALLOWED",
                subject=request.subject or request.path,
                metadata={
                    "created_by": POST_H_012_D_CREATED_BY,
                    "sensitive_action_id": sensitive_action_id,
                    "actor_id": requested_actor,
                    "actor_roles": actor_roles,
                    "requires_rbac_role": required_role,
                    "required_role_declared": required_role_declared,
                },
            )
        return PolicyDecision(
            effect=PolicyEffect.BLOCK,
            reason="RBAC_DENIED: actor does not hold the exact required role for this sensitive action.",
            guard="RBAC",
            rule_id="RBAC_DENIED",
            subject=request.subject or request.path,
            metadata={
                "created_by": POST_H_012_D_CREATED_BY,
                "sensitive_action_id": sensitive_action_id,
                "actor_id": requested_actor,
                "actor_roles": actor_roles,
                "requires_rbac_role": required_role,
                "required_role_declared": required_role_declared,
                "actor_has_required_role": actor_has_required_role,
            },
        )

    def _record_policy_observability(self, result: CommandResult, request: PolicyRequest) -> None:
        """Record Sprint 60 policy observability best-effort.

        Internal read-only engines can disable this projection to preserve the
        stronger invariant that repository inspection/preflight calls never
        create `.devpilot/` or any other worktree artifact in target repos.
        """

        if not self.observability_enabled:
            return

        try:
            from devpilot_core.observability.agentops import AgentOpsInstrumentor

            AgentOpsInstrumentor(self.root).record_policy_result(
                result=result,
                action=request.action,
                subject=request.subject or request.path,
                metadata={
                    "component": "PolicyEngine",
                    "tool_id": request.tool_id,
                    "approval_id": request.approval_id,
                    "actor_id": request.actor,
                    "interface": request.interface,
                    "post_h_012_d_enforced": True,
                    "payload_redacted": True,
                },
            )
        except Exception:
            return



def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()
