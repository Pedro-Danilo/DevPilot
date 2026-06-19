from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy.decisions import PolicyDecision, PolicyEffect
from devpilot_core.policy.path_guard import PathGuard
from devpilot_core.schemas import SchemaValidator

from .models import (
    DEFAULT_IDENTITY_REGISTRY_PATH,
    DEFAULT_IDENTITY_SCHEMA_PATH,
    ROLE_IDS,
    LocalActor,
    LocalRole,
    permission_for_action,
)


@dataclass(frozen=True)
class IdentityRegistryOptions:
    registry_path: str = DEFAULT_IDENTITY_REGISTRY_PATH
    schema_path: str = DEFAULT_IDENTITY_SCHEMA_PATH


@dataclass(frozen=True)
class RbacCheckInput:
    actor_id: str | None
    action: str
    permission: str | None = None
    tool_id: str | None = None
    subject: str | None = None
    workspace_id: str | None = None
    require_sensitive: bool = False


class IdentityRegistry:
    """Local identity and RBAC registry for FUNC-SPRINT-95.

    This registry is metadata-only: it stores local actors, roles and permissions
    used by PolicyEngine and ApprovalService. It deliberately does not implement
    passwords, sessions, remote auth, cloud identity or SaaS synchronization.
    """

    def __init__(self, root: Path, *, options: IdentityRegistryOptions | None = None) -> None:
        self.root = root.resolve()
        self.options = options or IdentityRegistryOptions()
        self.registry_path = (self.root / self.options.registry_path).resolve()
        self.schema_path = (self.root / self.options.schema_path).resolve()
        self.path_guard = PathGuard(self.root)

    def current(self) -> CommandResult:
        validation = self.validate()
        if not validation.ok:
            return validation
        payload = self._load()
        actor = self._current_actor(payload)
        roles = self._roles_for_actor(payload, actor)
        summary = {
            **validation.data["summary"],
            "current_actor_id": actor.actor_id,
            "current_roles": [role.role_id for role in roles],
            "permissions_total": len(self._permissions_for_roles(roles)),
            "auth_remote_enabled": False,
            "credentials_stored": False,
        }
        return CommandResult(
            command="identity current",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Current local identity loaded.",
            data={"summary": summary, "actor": actor.to_dict(), "roles": [role.to_dict() for role in roles]},
            findings=[Finding("IDENTITY_CURRENT_LOADED", "Current local identity is available and local-only.", Severity.INFO, metadata={"actor_id": actor.actor_id})],
        )

    def roles(self) -> CommandResult:
        validation = self.validate()
        if not validation.ok:
            return validation
        payload = self._load()
        roles = [LocalRole.from_dict(item) for item in payload.get("roles", [])]
        summary = {
            **validation.data["summary"],
            "roles": [role.role_id for role in roles],
            "required_roles_present": all(role_id in {role.role_id for role in roles} for role_id in ROLE_IDS),
        }
        return CommandResult(
            command="identity roles",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Local RBAC roles listed.",
            data={"summary": summary, "roles": [role.to_dict() for role in roles]},
            findings=[Finding("IDENTITY_ROLES_LISTED", "Local RBAC roles listed without remote authentication.", Severity.INFO, metadata={"roles_total": len(roles)})],
        )

    def check(self, data: RbacCheckInput) -> CommandResult:
        decision = self.evaluate(data)
        ok = decision.effect in {PolicyEffect.ALLOW, PolicyEffect.WARN}
        summary = {
            "allowed": ok,
            "actor_id": data.actor_id or self.default_actor_id(),
            "action": data.action,
            "permission": data.permission or permission_for_action(data.action, tool_id=data.tool_id),
            "tool_id": data.tool_id,
            "subject": data.subject,
            "workspace_id": data.workspace_id,
            "network_used": False,
            "external_api_used": False,
            "remote_auth_enabled": False,
            "credentials_stored": False,
            "preliminary": True,
        }
        return CommandResult(
            command="identity check",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="RBAC check passed." if ok else "RBAC check blocked the action.",
            data={"summary": summary, "decision": decision.to_dict()},
            findings=[decision.to_finding()] if not ok else [Finding("RBAC_PERMISSION_ALLOWED", "RBAC allowed the requested local action.", Severity.INFO, metadata=summary)],
        )

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        guard_decision = self.path_guard.evaluate(self.options.registry_path, action="read")
        if not guard_decision.ok:
            findings.append(guard_decision.to_finding())
        payload = self._load(missing_ok=True)
        if not payload:
            payload = _fallback_registry()
        if self.registry_path.exists() and self.schema_path.exists():
            schema_result = SchemaValidator(self.root).validate(schema=self.options.schema_path, instance=self.options.registry_path)
            if not schema_result.ok:
                findings.extend(schema_result.findings)
        roles = [LocalRole.from_dict(item) for item in payload.get("roles", []) if isinstance(item, dict)]
        actors = [LocalActor.from_dict(item) for item in payload.get("actors", []) if isinstance(item, dict)]
        role_ids = {role.role_id for role in roles}
        actor_ids = {actor.actor_id for actor in actors}
        for required in ROLE_IDS:
            if required not in role_ids:
                findings.append(Finding("IDENTITY_REQUIRED_ROLE_MISSING", "Identity Registry is missing a required local role.", Severity.BLOCK, metadata={"role_id": required}))
        active_actor_id = str(payload.get("active_actor_id") or "").strip()
        if active_actor_id and active_actor_id not in actor_ids:
            findings.append(Finding("IDENTITY_ACTIVE_ACTOR_MISSING", "Active actor is not declared in the local Identity Registry.", Severity.BLOCK, metadata={"active_actor_id": active_actor_id}))
        for actor in actors:
            if actor.credentials_stored:
                findings.append(Finding("IDENTITY_CREDENTIALS_STORED_BLOCK", "Identity Registry must not store local credentials in Sprint 95.", Severity.BLOCK, metadata={"actor_id": actor.actor_id}))
            if actor.remote_auth_enabled:
                findings.append(Finding("IDENTITY_REMOTE_AUTH_BLOCK", "Remote authentication is out of scope for Sprint 95.", Severity.BLOCK, metadata={"actor_id": actor.actor_id}))
            for role_id in actor.roles:
                if role_id not in role_ids:
                    findings.append(Finding("IDENTITY_ACTOR_ROLE_UNKNOWN", "Actor references a role that does not exist.", Severity.BLOCK, metadata={"actor_id": actor.actor_id, "role_id": role_id}))
        defaults = payload.get("defaults", {}) if isinstance(payload.get("defaults"), dict) else {}
        if defaults.get("auth_remote_enabled") is not False:
            findings.append(Finding("IDENTITY_REMOTE_AUTH_BLOCK", "Remote authentication must remain disabled.", Severity.BLOCK))
        if defaults.get("credentials_stored") is not False:
            findings.append(Finding("IDENTITY_CREDENTIALS_STORED_BLOCK", "Credentials must not be stored in the Identity Registry.", Severity.BLOCK))
        ok = not any(finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for finding in findings)
        summary = {
            "registry_path": self.options.registry_path,
            "schema_path": self.options.schema_path,
            "registry_exists": self.registry_path.exists(),
            "path_allowed": guard_decision.ok,
            "schema_valid": not self.registry_path.exists() or not self.schema_path.exists() or not any(f.id == "SCHEMA_VALIDATION_ERROR" for f in findings),
            "roles_total": len(roles),
            "actors_total": len(actors),
            "required_roles_total": len(ROLE_IDS),
            "required_roles_present": all(role_id in role_ids for role_id in ROLE_IDS),
            "active_actor_id": active_actor_id or None,
            "auth_remote_enabled": False,
            "credentials_stored": False,
            "network_used": False,
            "external_api_used": False,
            "remote_auth_used": False,
            "blocked_findings_total": sum(1 for f in findings if f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}),
            "preliminary": True,
        }
        return CommandResult(
            command="identity validate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Identity Registry validation passed." if ok else "Identity Registry validation failed.",
            data={"summary": summary},
            findings=findings or [Finding("IDENTITY_REGISTRY_VALIDATED", "Identity Registry is valid, local-only and role-bound.", Severity.INFO, metadata=summary)],
        )

    def evaluate(self, data: RbacCheckInput) -> PolicyDecision:
        validation = self.validate()
        payload = self._load(missing_ok=True) or _fallback_registry()
        actor_id = (data.actor_id or "").strip() or str(payload.get("active_actor_id") or "local-owner")
        permission = (data.permission or permission_for_action(data.action, tool_id=data.tool_id)).strip()
        metadata = {
            "actor_id": actor_id,
            "action": data.action,
            "permission": permission,
            "tool_id": data.tool_id,
            "subject": data.subject,
            "workspace_id": data.workspace_id,
            "identity_registry": self.options.registry_path if self.registry_path.exists() else None,
            "registry_valid": validation.ok,
            "auth_remote_enabled": False,
            "credentials_stored": False,
        }
        if not validation.ok:
            metadata["validation_findings"] = [finding.id for finding in validation.findings]
            return PolicyDecision(PolicyEffect.BLOCK, "Identity Registry is invalid; RBAC fails closed.", "RBAC", "RBAC_REGISTRY_INVALID", data.subject, metadata)
        actor = self._actor_by_id(payload, actor_id)
        if actor is None:
            return PolicyDecision(PolicyEffect.BLOCK, "RBAC actor is not registered in the local Identity Registry.", "RBAC", "RBAC_ACTOR_UNKNOWN", data.subject, metadata)
        if actor.status != "active":
            return PolicyDecision(PolicyEffect.BLOCK, "RBAC actor is not active.", "RBAC", "RBAC_ACTOR_INACTIVE", data.subject, metadata)
        roles = self._roles_for_actor(payload, actor)
        permissions = self._permissions_for_roles(roles)
        metadata["actor_roles"] = [role.role_id for role in roles]
        metadata["permissions_total"] = len(permissions)
        if "*" in permissions or permission in permissions:
            return PolicyDecision(PolicyEffect.ALLOW, "RBAC allowed the action for the local actor.", "RBAC", "RBAC_PERMISSION_ALLOWED", data.subject, metadata)
        if permission.startswith("action.") and not data.require_sensitive:
            return PolicyDecision(PolicyEffect.ALLOW, "RBAC action is non-sensitive and allowed by local default.", "RBAC", "RBAC_NON_SENSITIVE_ALLOWED", data.subject, metadata)
        return PolicyDecision(PolicyEffect.BLOCK, "RBAC denied the requested action for the local actor.", "RBAC", "RBAC_PERMISSION_DENIED", data.subject, metadata)

    def default_actor_id(self) -> str:
        payload = self._load(missing_ok=True) or _fallback_registry()
        return str(payload.get("active_actor_id") or "local-owner")

    def _load(self, *, missing_ok: bool = False) -> dict[str, Any]:
        if not self.registry_path.exists():
            return {} if missing_ok else _fallback_registry()
        try:
            loaded = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return loaded if isinstance(loaded, dict) else {}

    def _current_actor(self, payload: dict[str, Any]) -> LocalActor:
        actor_id = str(payload.get("active_actor_id") or "local-owner")
        actor = self._actor_by_id(payload, actor_id)
        return actor or LocalActor.from_dict(_fallback_registry()["actors"][0])

    def _actor_by_id(self, payload: dict[str, Any], actor_id: str) -> LocalActor | None:
        for item in payload.get("actors", []):
            if isinstance(item, dict) and str(item.get("actor_id", "")).strip() == actor_id:
                return LocalActor.from_dict(item)
        return None

    def _roles_for_actor(self, payload: dict[str, Any], actor: LocalActor) -> list[LocalRole]:
        role_map = {role.role_id: role for role in [LocalRole.from_dict(item) for item in payload.get("roles", []) if isinstance(item, dict)]}
        return [role_map[role_id] for role_id in actor.roles if role_id in role_map]

    def _permissions_for_roles(self, roles: list[LocalRole]) -> set[str]:
        permissions: set[str] = set()
        for role in roles:
            permissions.update(role.permissions)
        return permissions


def _fallback_registry() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "created_by": "FUNC-SPRINT-95",
        "updated_at": "2026-06-19T00:00:00Z",
        "active_actor_id": "local-owner",
        "defaults": {"auth_remote_enabled": False, "credentials_stored": False, "deny_unknown_actor": True, "rbac_enforced_for_sensitive_actions": True},
        "security": {"network_used": False, "external_api_used": False, "remote_auth_used": False, "credentials_read": False, "credentials_stored": False},
        "roles": [
            {"role_id": "owner", "name": "Owner", "risk_level": "high", "permissions": ["*"], "description": "Full local owner for controlled personal workspace operations."},
            {"role_id": "architect", "name": "Architect", "risk_level": "medium_high", "permissions": ["architecture.review", "policy.evaluate", "workspace.read", "report.read", "approval.request"], "description": "Architecture and policy reviewer."},
            {"role_id": "developer", "name": "Developer", "risk_level": "medium", "permissions": ["code.read", "tests.run", "workspace.read", "report.read", "approval.request"], "description": "Local implementation role without critical approvals."},
            {"role_id": "reviewer", "name": "Reviewer", "risk_level": "medium_high", "permissions": ["code.review", "policy.read", "report.read", "approval.request", "approval.decide.noncritical"], "description": "Review role for quality/security evidence."},
            {"role_id": "operator", "name": "Operator", "risk_level": "medium_high", "permissions": ["workspace.read", "portfolio.status", "state.read", "report.read", "approval.request"], "description": "Local operational and portfolio inspection role."},
            {"role_id": "agent-supervisor", "name": "Agent Supervisor", "risk_level": "high", "permissions": ["agent.supervise", "policy.evaluate", "approval.decide.critical", "tool.execute.approve", "external_api.approve", "patch.apply.approve", "release.deploy.approve", "git.write.approve", "filesystem.delete.approve", "filesystem.write.approve", "workspace.select", "portfolio.status"], "description": "Supervises agentic and approval-gated local operations."},
        ],
        "actors": [
            {"actor_id": "local-owner", "display_name": "Local Owner", "roles": ["owner", "agent-supervisor"], "status": "active", "workspace_scope": ["devpilot-local"], "credentials_stored": False, "remote_auth_enabled": False, "metadata": {"source": "default-local-registry"}},
            {"actor_id": "owner", "display_name": "Legacy Owner Alias", "roles": ["owner", "agent-supervisor"], "status": "active", "workspace_scope": ["devpilot-local"], "credentials_stored": False, "remote_auth_enabled": False, "metadata": {"source": "default-local-registry", "compatibility_alias": True}}
        ],
    }
