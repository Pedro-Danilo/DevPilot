from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DEFAULT_IDENTITY_REGISTRY_PATH = ".devpilot/identity/identity_registry.json"
DEFAULT_IDENTITY_SCHEMA_PATH = "docs/schemas/identity_registry.schema.json"

ROLE_IDS = ("owner", "architect", "developer", "reviewer", "operator", "agent-supervisor")
SENSITIVE_ACTIONS = {
    "execute",
    "shell",
    "external-api",
    "network-call",
    "deploy",
    "commit",
    "push",
    "apply",
    "delete",
    "remove",
    "rm",
    "rmdir",
    "overwrite",
}

ACTION_PERMISSION_MAP = {
    "approval.request": "approval.request",
    "approval.approve": "approval.decide.critical",
    "approval.deny": "approval.decide.critical",
    "approval.revoke": "approval.decide.critical",
    "execute": "tool.execute.approve",
    "shell": "tool.execute.approve",
    "external-api": "external_api.approve",
    "network-call": "external_api.approve",
    "deploy": "release.deploy.approve",
    "commit": "git.write.approve",
    "push": "git.write.approve",
    "apply": "patch.apply.approve",
    "delete": "filesystem.delete.approve",
    "remove": "filesystem.delete.approve",
    "rm": "filesystem.delete.approve",
    "rmdir": "filesystem.delete.approve",
    "overwrite": "filesystem.write.approve",
}


@dataclass(frozen=True)
class LocalRole:
    role_id: str
    name: str
    permissions: tuple[str, ...]
    risk_level: str = "medium"
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LocalRole":
        return cls(
            role_id=str(data.get("role_id", "")).strip(),
            name=str(data.get("name", "")).strip(),
            permissions=tuple(str(item).strip() for item in data.get("permissions", []) if str(item).strip()),
            risk_level=str(data.get("risk_level", "medium")).strip(),
            description=str(data.get("description", "")).strip(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "name": self.name,
            "permissions": list(self.permissions),
            "risk_level": self.risk_level,
            "description": self.description,
        }


@dataclass(frozen=True)
class LocalActor:
    actor_id: str
    display_name: str
    roles: tuple[str, ...]
    status: str = "active"
    workspace_scope: tuple[str, ...] = field(default_factory=tuple)
    credentials_stored: bool = False
    remote_auth_enabled: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LocalActor":
        return cls(
            actor_id=str(data.get("actor_id", "")).strip(),
            display_name=str(data.get("display_name", "")).strip(),
            roles=tuple(str(item).strip() for item in data.get("roles", []) if str(item).strip()),
            status=str(data.get("status", "active")).strip(),
            workspace_scope=tuple(str(item).strip() for item in data.get("workspace_scope", []) if str(item).strip()),
            credentials_stored=bool(data.get("credentials_stored", False)),
            remote_auth_enabled=bool(data.get("remote_auth_enabled", False)),
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "display_name": self.display_name,
            "roles": list(self.roles),
            "status": self.status,
            "workspace_scope": list(self.workspace_scope),
            "credentials_stored": self.credentials_stored,
            "remote_auth_enabled": self.remote_auth_enabled,
            "metadata": dict(self.metadata),
        }


def permission_for_action(action: str, *, tool_id: str | None = None) -> str:
    normalized = (action or "").strip().lower()
    if tool_id and normalized in {"execute", "shell"}:
        return "tool.execute.approve"
    return ACTION_PERMISSION_MAP.get(normalized, f"action.{normalized or 'unknown'}")
