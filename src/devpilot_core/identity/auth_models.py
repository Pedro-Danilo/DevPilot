from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

AUTH_DB_RELATIVE_PATH = ".devpilot/auth/auth.db"
AUTH_SCHEMA_VERSION = 1
SESSION_COOKIE_NAME = "devpilot_session"
CSRF_COOKIE_NAME = "devpilot_csrf"
CSRF_HEADER_NAME = "X-DevPilot-CSRF"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class LocalIdentity:
    actor_id: str
    username: str
    display_name: str
    roles: tuple[str, ...]
    workspace_scopes: tuple[str, ...] = field(default_factory=tuple)
    status: str = "active"
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class CredentialRecord:
    actor_id: str
    username: str
    password_hash: bytes
    salt: bytes
    kdf_algorithm: str
    kdf_version: int
    kdf_params: dict[str, int]
    created_at: str
    updated_at: str
    credential_version: int = 1


@dataclass(frozen=True)
class SessionRecord:
    token_hash: str
    csrf_hash: str
    actor_id: str
    roles: tuple[str, ...]
    workspace_scopes: tuple[str, ...]
    created_at: str
    last_seen_at: str
    absolute_expires_at: str
    idle_timeout_seconds: int
    revoked_at: str | None = None
    revoke_reason: str | None = None
    rotation_counter: int = 0


@dataclass(frozen=True)
class SessionContext:
    principal: "AuthenticatedPrincipal"
    created_at: str
    last_seen_at: str
    absolute_expires_at: str
    idle_timeout_seconds: int
    rotation_counter: int

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "authenticated": True,
            "principal": self.principal.to_safe_dict(),
            "created_at": self.created_at,
            "last_seen_at": self.last_seen_at,
            "absolute_expires_at": self.absolute_expires_at,
            "idle_timeout_seconds": self.idle_timeout_seconds,
            "rotation_counter": self.rotation_counter,
            "session_secret_exposed": False,
        }


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    actor_id: str
    username: str
    display_name: str
    roles: tuple[str, ...]
    workspace_scopes: tuple[str, ...]
    auth_method: str = "human-session"

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "username": self.username,
            "display_name": self.display_name,
            "roles": list(self.roles),
            "workspace_scopes": list(self.workspace_scopes),
            "auth_method": self.auth_method,
        }


@dataclass(frozen=True)
class SessionIssue:
    token: str
    csrf_token: str
    context: SessionContext


@dataclass(frozen=True)
class SessionRevocation:
    actor_id: str
    revoked: bool
    reason: str
    revoked_at: str
