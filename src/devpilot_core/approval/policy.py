from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from devpilot_core.policy.decisions import PolicyDecision, PolicyEffect

from .binding import ApprovalBindingRequest, StrongApprovalBindingValidator
from .models import ApprovalStatus

if TYPE_CHECKING:
    from .store import ApprovalStore


@dataclass(frozen=True)
class ApprovalPolicyInput:
    """Input required to verify an approval against a policy-scoped request."""

    action: str
    approval_id: str | None = None
    tool_id: str | None = None
    subject: str | None = None
    path: str | None = None
    metadata: dict[str, Any] | None = None
    actor_id: str | None = None
    role_at_decision: str | None = None
    command_id: str | None = None
    tool_call_id: str | None = None
    subject_hash: str | None = None


class ApprovalPolicyChecker:
    """Verify approval_id against ApprovalStore and MIASI approval metadata.

    FUNC-SPRINT-30 deliberately makes approvals narrow: a valid approval can
    satisfy only the tool/action/subject scope it declares. It never bypasses
    PathGuard, SecretGuard, CostGuard or other PolicyEngine decisions.
    """

    critical_actions = {"execute", "shell", "external-api", "network-call", "deploy", "commit", "push", "apply"}

    def __init__(self, root: Path, *, store: "ApprovalStore | None" = None) -> None:
        self.root = root.resolve()
        if store is None:
            from .store import ApprovalStore

            self.store = ApprovalStore(self.root)
        else:
            self.store = store
        self.tool_registry_path = self.root / ".devpilot" / "miasi" / "tool_registry.json"
        self.policy_matrix_path = self.root / ".devpilot" / "miasi" / "policy_matrix.json"
        self.sensitive_catalog_path = self.root / ".devpilot" / "approval" / "sensitive_action_catalog.json"

    def evaluate(self, data: ApprovalPolicyInput) -> PolicyDecision:
        action = data.action.strip().lower() or "unknown"
        tool_id = (data.tool_id or "").strip() or None
        subject = (data.subject or "").strip() or None
        approval_id = (data.approval_id or "").strip() or None
        approval_required = self.approval_required(action=action, tool_id=tool_id)

        metadata: dict[str, Any] = {
            "action": action,
            "tool_id": tool_id,
            "subject": subject,
            "path": data.path,
            "approval_required": approval_required,
            "tool_registry": str(self.tool_registry_path.relative_to(self.root)) if self.tool_registry_path.exists() else None,
            "policy_matrix": str(self.policy_matrix_path.relative_to(self.root)) if self.policy_matrix_path.exists() else None,
            "sensitive_action_catalog": str(self.sensitive_catalog_path.relative_to(self.root)) if self.sensitive_catalog_path.exists() else None,
        }
        if data.metadata:
            metadata.update(data.metadata)

        if not approval_required and not approval_id:
            return PolicyDecision(
                effect=PolicyEffect.ALLOW,
                reason="Approval is not required for this policy request.",
                guard="ApprovalPolicyChecker",
                rule_id="APPROVAL_NOT_REQUIRED",
                subject=subject or data.path,
                metadata=metadata,
            )

        if approval_required and not approval_id:
            return PolicyDecision(
                effect=PolicyEffect.BLOCK,
                reason="Approval-gated action requires a valid approval_id.",
                guard="ApprovalPolicyChecker",
                rule_id="APPROVAL_REQUIRED_MISSING",
                subject=subject or data.path,
                metadata=metadata,
            )

        if not approval_id:
            return PolicyDecision(
                effect=PolicyEffect.ALLOW,
                reason="Approval was not provided and is not required.",
                guard="ApprovalPolicyChecker",
                rule_id="APPROVAL_NOT_REQUIRED",
                subject=subject or data.path,
                metadata=metadata,
            )

        record = self.store.get(approval_id)
        metadata["approval_id"] = approval_id
        if record is None:
            return PolicyDecision(
                effect=PolicyEffect.BLOCK,
                reason="Provided approval_id does not exist in the local approval store.",
                guard="ApprovalPolicyChecker",
                rule_id="APPROVAL_NOT_FOUND",
                subject=subject or data.path,
                metadata=metadata,
            )

        metadata.update(
            {
                "approval_status": record.status,
                "approval_tool_id": record.tool_id,
                "approval_action": record.action,
                "approval_subject": record.subject,
                "approval_expires_at": record.expires_at,
            }
        )

        if record.expired:
            return PolicyDecision(
                effect=PolicyEffect.BLOCK,
                reason="Provided approval_id is expired.",
                guard="ApprovalPolicyChecker",
                rule_id="APPROVAL_EXPIRED",
                subject=subject or record.subject,
                metadata=metadata,
            )

        if record.status != ApprovalStatus.APPROVED.value:
            return PolicyDecision(
                effect=PolicyEffect.BLOCK,
                reason="Provided approval_id is not approved.",
                guard="ApprovalPolicyChecker",
                rule_id="APPROVAL_NOT_APPROVED",
                subject=subject or record.subject,
                metadata=metadata,
            )

        binding_validator = StrongApprovalBindingValidator(self.root)
        sensitive_action = binding_validator._resolve_sensitive_action(tool_id or record.tool_id, action)
        if sensitive_action is not None:
            binding_result = binding_validator.evaluate(
                record,
                ApprovalBindingRequest(
                    approval_id=approval_id,
                    actor_id=data.actor_id or str(metadata.get("actor_id") or metadata.get("actor") or ""),
                    role_at_decision=data.role_at_decision or metadata.get("role_at_decision"),
                    tool_id=tool_id or record.tool_id,
                    action=action,
                    subject=subject or record.subject,
                    command_id=data.command_id or metadata.get("command_id"),
                    tool_call_id=data.tool_call_id or metadata.get("tool_call_id"),
                    subject_hash=data.subject_hash or metadata.get("subject_hash"),
                    interface=metadata.get("interface"),
                ),
            )
            metadata["approval_scope"] = record.scope
            metadata["strong_binding_required"] = True
            metadata["binding_summary"] = binding_result.data.get("summary", {})
            if not binding_result.ok:
                metadata["binding_findings"] = [finding.id for finding in binding_result.findings]
                return PolicyDecision(
                    effect=PolicyEffect.BLOCK,
                    reason="Provided approval_id failed strong approval binding checks.",
                    guard="ApprovalPolicyChecker",
                    rule_id="APPROVAL_BINDING_MISMATCH",
                    subject=subject or record.subject,
                    metadata=metadata,
                )
            return PolicyDecision(
                effect=PolicyEffect.ALLOW,
                reason="Provided approval_id is approved, unexpired and strongly bound to this sensitive request.",
                guard="ApprovalPolicyChecker",
                rule_id="APPROVAL_VALID",
                subject=subject or record.subject,
                metadata=metadata,
            )

        scope_findings = self._scope_mismatches(record_scope=record.scope, record_tool=record.tool_id, record_action=record.action, record_subject=record.subject, tool_id=tool_id, action=action, subject=subject)
        if scope_findings:
            metadata["scope_mismatches"] = scope_findings
            metadata["approval_scope"] = record.scope
            return PolicyDecision(
                effect=PolicyEffect.BLOCK,
                reason="Provided approval_id does not cover the requested tool/action/subject scope.",
                guard="ApprovalPolicyChecker",
                rule_id="APPROVAL_SCOPE_MISMATCH",
                subject=subject or record.subject,
                metadata=metadata,
            )

        metadata["approval_scope"] = record.scope
        metadata["strong_binding_required"] = False
        return PolicyDecision(
            effect=PolicyEffect.ALLOW,
            reason="Provided approval_id is approved, unexpired and scoped to this request.",
            guard="ApprovalPolicyChecker",
            rule_id="APPROVAL_VALID",
            subject=subject or record.subject,
            metadata=metadata,
        )

    def approval_required(self, *, action: str, tool_id: str | None) -> bool:
        action = action.strip().lower()
        if self._sensitive_action_requires_approval(action=action, tool_id=tool_id):
            return True
        if tool_id and self._tool_requires_approval(tool_id):
            return True
        if action in self.critical_actions:
            return True
        return self._policy_action_requires_approval(action)


    def _sensitive_action_requires_approval(self, *, action: str, tool_id: str | None) -> bool:
        entry = self._resolve_sensitive_action(action=action, tool_id=tool_id)
        return bool(entry and entry.get("requires_approval"))

    def _resolve_sensitive_action(self, *, action: str, tool_id: str | None) -> dict[str, Any] | None:
        payload = self._load_json(self.sensitive_catalog_path)
        requested_action = str(action or "").strip().lower()
        requested_tool = str(tool_id or "").strip().lower()
        for entry in payload.get("actions", []):
            if not isinstance(entry, dict):
                continue
            action_id = str(entry.get("action_id", "")).strip().lower()
            action_tail = action_id.split(".")[-1]
            tool_ids = {str(item).strip().lower() for item in entry.get("tool_ids", [])}
            if requested_action and requested_action in {action_id, action_tail}:
                return entry
            if requested_tool and requested_tool in tool_ids and requested_action in {action_id, action_tail}:
                return entry
        return None

    def _tool_requires_approval(self, tool_id: str) -> bool:
        data = self._load_json(self.tool_registry_path)
        for tool in data.get("tools", []):
            if isinstance(tool, dict) and tool.get("tool_id") == tool_id:
                return bool(tool.get("requires_approval"))
        return False

    def _policy_action_requires_approval(self, action: str) -> bool:
        data = self._load_json(self.policy_matrix_path)
        for rule in data.get("rules", []):
            if not isinstance(rule, dict):
                continue
            rule_action = str(rule.get("action", "")).strip().lower()
            if rule_action == action and bool(rule.get("approval_required")):
                return True
        return False

    def _load_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return loaded if isinstance(loaded, dict) else {}

    def _scope_mismatches(
        self,
        *,
        record_scope: dict[str, Any],
        record_tool: str,
        record_action: str,
        record_subject: str,
        tool_id: str | None,
        action: str,
        subject: str | None,
    ) -> list[str]:
        mismatches: list[str] = []
        requested_tool = tool_id or str(record_scope.get("tool_id") or record_tool or "")
        requested_subject = subject or str(record_scope.get("subject") or record_subject or "")
        requested_action = action
        if str(record_scope.get("tool_id") or record_tool).strip() != requested_tool:
            mismatches.append("tool_id")
        if str(record_scope.get("action") or record_action).strip().lower() != requested_action:
            mismatches.append("action")
        if str(record_scope.get("subject") or record_subject).strip() != requested_subject:
            mismatches.append("subject")
        return mismatches
