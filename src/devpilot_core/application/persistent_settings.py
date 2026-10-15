"""R01-10: scoped, governed settings persistence; never changes runtime authority.

This store is intentionally NOT a provider enablement/kill switch.  The existing
ExternalProviderEnablementService retains exclusive ownership of runtime state.
"""
from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.identity.auth_models import AuthenticatedPrincipal, SessionContext
from devpilot_core.identity.server_rbac import ServerRBACEnforcer


class SettingsConflict(ValueError):
    """Revision or stale configuration conflict (no mutation performed)."""


class SettingsDenied(ValueError):
    """Unknown key/scope, unsafe value, or unauthorized operation."""


# Not a general-purpose YAML/JSON editor.  Plan-only, never a runtime grant.
_DEFAULTS = {
    "generation.default_route": "deterministic",
    "generation.max_output_tokens": 512,
    "ui.detail_level": "guided",
    "governance.external_network": "DENY",
    "governance.tool_execution": "DENY",
}
_FLOORS = {"governance.external_network", "governance.tool_execution"}
_KEY_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,79}$")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def _check_value(key: str, value: Any) -> None:
    if key not in _DEFAULTS or not _KEY_RE.fullmatch(key):
        raise SettingsDenied("UNKNOWN_KEY_DENY")
    if key in _FLOORS:
        if value != "DENY":
            raise SettingsDenied("POLICY_FLOOR_DENY")
    elif key == "generation.default_route":
        if type(value) is not str or value not in {"deterministic", "local"}:
            raise SettingsDenied("ROUTE_DENY")
    elif key == "generation.max_output_tokens":
        if type(value) is not int or not (1 <= value <= 8192):
            raise SettingsDenied("TOKEN_LIMIT_DENY")
    elif key == "ui.detail_level":
        if type(value) is not str or value not in {"guided", "expert"}:
            raise SettingsDenied("DETAIL_LEVEL_DENY")


def _scope(scope: str, scope_id: str) -> tuple[str, str]:
    if scope not in {"platform", "workspace", "project"}:
        raise SettingsDenied("UNKNOWN_SCOPE_DENY")
    if scope == "platform":
        if scope_id != "platform":
            raise SettingsDenied("PLATFORM_SCOPE_ID_DENY")
    elif not _ID_RE.fullmatch(scope_id):
        raise SettingsDenied("SCOPE_ID_DENY")
    return scope, scope_id


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class SettingsChangePlan:
    scope: str
    scope_id: str
    key: str
    value: Any
    expected_revision: int
    current_revision: int
    permitted: bool
    reason: str
    write_performed: bool = False
    runtime_modified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return vars(self).copy()


class PersistentSettingsStore:
    """Versioned SQLite settings, optimistic CAS, canonical scoped precedence.

    Instantiation and preview never write.  Writes use a transaction with a
    compare-and-swap revision; rollback creates a new revision (no history rewrite).
    """
    def __init__(self, root: Path, *, database: Path | None = None) -> None:
        self.root = Path(root).resolve()
        self.database = database or self.root / ".devpilot" / "runtime" / "settings" / "settings.sqlite3"
        self.database = Path(self.database).absolute()
        # The explicit database path supports isolated tests; never accept paths from HTTP.

    def _connect(self, *, writable: bool) -> sqlite3.Connection | None:
        if not writable and not self.database.is_file():
            return None
        if writable:
            self.database.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.database, timeout=15, isolation_level=None)
            conn.execute("PRAGMA busy_timeout=15000")
            conn.execute("CREATE TABLE IF NOT EXISTS setting_versions (scope TEXT NOT NULL, scope_id TEXT NOT NULL, key TEXT NOT NULL, revision INTEGER NOT NULL, value_json TEXT NOT NULL, actor_id TEXT NOT NULL, event TEXT NOT NULL, PRIMARY KEY(scope,scope_id,key,revision))")
            return conn
        return sqlite3.connect(f"file:{self.database.as_posix()}?mode=ro", uri=True, timeout=15)

    @staticmethod
    def _latest(conn: sqlite3.Connection | None, scope: str, scope_id: str, key: str) -> tuple[int, Any | None]:
        if conn is None:
            return 0, None
        try:
            row = conn.execute("SELECT revision,value_json FROM setting_versions WHERE scope=? AND scope_id=? AND key=? ORDER BY revision DESC LIMIT 1", (scope, scope_id, key)).fetchone()
        except sqlite3.OperationalError as exc:
            raise SettingsDenied("SETTINGS_SCHEMA_UNAVAILABLE") from exc
        return (int(row[0]), json.loads(row[1])) if row else (0, None)

    def effective(self, *, key: str, workspace_id: str | None = None, project_id: str | None = None) -> dict[str, Any]:
        if key not in _DEFAULTS:
            raise SettingsDenied("UNKNOWN_KEY_DENY")
        if workspace_id is not None:
            _scope("workspace", workspace_id)
        if project_id is not None:
            _scope("project", project_id)
        if project_id and not workspace_id:
            raise SettingsDenied("PROJECT_REQUIRES_WORKSPACE")
        conn = self._connect(writable=False)
        try:
            value, origin, rev = _DEFAULTS[key], "builtin", 0
            if key not in _FLOORS:
                for scope, sid in [("platform", "platform"), ("workspace", workspace_id), ("project", project_id)]:
                    if sid is None:
                        continue
                    cur, found = self._latest(conn, scope, sid, key)
                    if cur:
                        _check_value(key, found)
                        value, origin, rev = found, f"{scope}:{sid}", cur
            return {"key": key, "effective_value": value, "origin": origin, "revision": rev, "plan_only": True, "runtime_modified": False, "policy_floor": key in _FLOORS}
        finally:
            if conn is not None:
                conn.close()

    def plan(self, *, scope: str, scope_id: str, key: str, value: Any, expected_revision: int) -> SettingsChangePlan:
        _scope(scope, scope_id)
        _check_value(key, value)
        if type(expected_revision) is not int or expected_revision < 0:
            raise SettingsDenied("INVALID_REVISION")
        conn = self._connect(writable=False)
        try:
            revision, _ = self._latest(conn, scope, scope_id, key)
        finally:
            if conn is not None:
                conn.close()
        return SettingsChangePlan(scope, scope_id, key, value, expected_revision, revision, expected_revision == revision, "READY_PLAN_ONLY" if expected_revision == revision else "REVISION_CONFLICT")

    def _owner(self, *, principal: AuthenticatedPrincipal, session: SessionContext, scope: str, scope_id: str, workspace_id: str | None) -> None:
        if not isinstance(principal, AuthenticatedPrincipal) or not isinstance(session, SessionContext) or session.principal != principal:
            raise SettingsDenied("AUTHENTICATED_SESSION_REQUIRED")
        roles = ServerRBACEnforcer(self.root).canonical_roles(principal)
        if "owner" not in roles or not principal.actor_id:
            raise SettingsDenied("OWNER_RBAC_DENY")
        if scope != "platform":
            target = workspace_id if scope == "project" else scope_id
            if scope == "project" and not target:
                raise SettingsDenied("PROJECT_WORKSPACE_REQUIRED")
            if target not in principal.workspace_scopes:
                raise SettingsDenied("WORKSPACE_RBAC_DENY")

    def apply(self, *, scope: str, scope_id: str, key: str, value: Any, expected_revision: int,
              principal: AuthenticatedPrincipal, session: SessionContext, approve_write: bool = False, workspace_id: str | None = None) -> dict[str, Any]:
        _scope(scope, scope_id)
        _check_value(key, value)
        self._owner(principal=principal, session=session, scope=scope, scope_id=scope_id, workspace_id=workspace_id)
        if not approve_write:
            raise SettingsDenied("EXPLICIT_WRITE_APPROVAL_REQUIRED")
        if type(expected_revision) is not int or expected_revision < 0:
            raise SettingsDenied("INVALID_REVISION")
        conn = self._connect(writable=True)
        assert conn is not None
        try:
            conn.execute("BEGIN IMMEDIATE")
            current, prior = self._latest(conn, scope, scope_id, key)
            if current != expected_revision:
                raise SettingsConflict("REVISION_CONFLICT")
            if current and prior == value:
                conn.execute("COMMIT")
                return {"status": "NO_OP", "revision": current, "runtime_modified": False, "value": value}
            new_revision = current + 1
            conn.execute("INSERT INTO setting_versions VALUES (?,?,?,?,?,?,?)", (scope, scope_id, key, new_revision, _json(value), principal.actor_id, "set"))
            conn.execute("COMMIT")
            return {"status": "PERSISTED_PLAN_ONLY", "revision": new_revision, "runtime_modified": False, "value": value}
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def rollback(self, *, scope: str, scope_id: str, key: str, target_revision: int, expected_revision: int,
                 principal: AuthenticatedPrincipal, session: SessionContext, approve_write: bool = False, workspace_id: str | None = None) -> dict[str, Any]:
        _scope(scope, scope_id)
        if key not in _DEFAULTS or type(target_revision) is not int or target_revision < 1 or type(expected_revision) is not int or expected_revision < 1:
            raise SettingsDenied("ROLLBACK_REVISION_DENY")
        self._owner(principal=principal, session=session, scope=scope, scope_id=scope_id, workspace_id=workspace_id)
        if not approve_write:
            raise SettingsDenied("EXPLICIT_WRITE_APPROVAL_REQUIRED")
        conn = self._connect(writable=True)
        assert conn is not None
        try:
            conn.execute("BEGIN IMMEDIATE")
            current, _ = self._latest(conn, scope, scope_id, key)
            if current != expected_revision:
                raise SettingsConflict("REVISION_CONFLICT")
            row = conn.execute("SELECT value_json FROM setting_versions WHERE scope=? AND scope_id=? AND key=? AND revision=?", (scope, scope_id, key, target_revision)).fetchone()
            if row is None:
                raise SettingsDenied("UNKNOWN_TARGET_REVISION")
            restored = json.loads(row[0])
            _check_value(key, restored)
            new_revision = current + 1
            conn.execute("INSERT INTO setting_versions VALUES (?,?,?,?,?,?,?)", (scope, scope_id, key, new_revision, _json(restored), principal.actor_id, "rollback"))
            conn.execute("COMMIT")
            return {"status": "ROLLBACK_VERSION_CREATED", "revision": new_revision, "target_revision": target_revision, "runtime_modified": False, "value": restored}
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()
