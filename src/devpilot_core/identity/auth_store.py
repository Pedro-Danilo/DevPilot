from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .auth_models import AUTH_DB_RELATIVE_PATH, AUTH_SCHEMA_VERSION, CredentialRecord, LocalIdentity, SessionRecord


class AuthStoreError(RuntimeError):
    pass


class LocalAuthStore:
    """SQLite runtime store for human identities, credentials and opaque sessions.

    The database is runtime-only under `.devpilot/auth/`, excluded from Git and
    release archives. Passwords and raw session/CSRF tokens are never persisted.
    """

    def __init__(self, root: Path, *, db_relative_path: str = AUTH_DB_RELATIVE_PATH) -> None:
        self.root = root.resolve()
        self.db_relative_path = db_relative_path
        self.db_path = self._resolve_runtime_path(db_relative_path)

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.db_path.parent, 0o700)
        except OSError:
            pass
        try:
            with self._connect() as con:
                con.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS auth_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                    CREATE TABLE IF NOT EXISTS identities (
                        actor_id TEXT PRIMARY KEY,
                        username TEXT NOT NULL UNIQUE,
                        display_name TEXT NOT NULL,
                        roles_json TEXT NOT NULL,
                        workspace_scopes_json TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS credentials (
                        actor_id TEXT PRIMARY KEY REFERENCES identities(actor_id) ON DELETE CASCADE,
                        username TEXT NOT NULL UNIQUE,
                        password_hash BLOB NOT NULL,
                        salt BLOB NOT NULL,
                        kdf_algorithm TEXT NOT NULL,
                        kdf_version INTEGER NOT NULL,
                        kdf_params_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        credential_version INTEGER NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS sessions (
                        token_hash TEXT PRIMARY KEY,
                        csrf_hash TEXT NOT NULL,
                        actor_id TEXT NOT NULL REFERENCES identities(actor_id) ON DELETE CASCADE,
                        roles_json TEXT NOT NULL,
                        workspace_scopes_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_seen_at TEXT NOT NULL,
                        absolute_expires_at TEXT NOT NULL,
                        idle_timeout_seconds INTEGER NOT NULL,
                        revoked_at TEXT,
                        revoke_reason TEXT,
                        rotation_counter INTEGER NOT NULL DEFAULT 0
                    );
                    CREATE INDEX IF NOT EXISTS idx_sessions_actor ON sessions(actor_id);
                    CREATE TABLE IF NOT EXISTS auth_events (
                        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        actor_id TEXT,
                        outcome TEXT NOT NULL,
                        reason_code TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        metadata_json TEXT NOT NULL
                    );
                    """
                )
                row = con.execute("SELECT value FROM auth_meta WHERE key='schema_version'").fetchone()
                if row is None:
                    con.execute("INSERT INTO auth_meta(key,value) VALUES('schema_version',?)", (str(AUTH_SCHEMA_VERSION),))
                elif int(row[0]) != AUTH_SCHEMA_VERSION:
                    raise AuthStoreError(f"unsupported auth store schema version: {row[0]}")
                con.commit()
            try:
                os.chmod(self.db_path, 0o600)
            except OSError:
                pass
        except (sqlite3.DatabaseError, ValueError) as exc:
            raise AuthStoreError("local auth store is corrupt or incompatible") from exc

    def owner_exists(self) -> bool:
        self.initialize()
        with self._connect() as con:
            row = con.execute("SELECT 1 FROM identities WHERE roles_json LIKE '%\"owner\"%' AND status='active' LIMIT 1").fetchone()
            return row is not None

    def get_identity_by_username(self, username: str) -> LocalIdentity | None:
        self.initialize()
        with self._connect() as con:
            row = con.execute("SELECT actor_id,username,display_name,roles_json,workspace_scopes_json,status,created_at FROM identities WHERE username=?", (username,)).fetchone()
            return self._identity(row) if row else None

    def get_identity(self, actor_id: str) -> LocalIdentity | None:
        self.initialize()
        with self._connect() as con:
            row = con.execute("SELECT actor_id,username,display_name,roles_json,workspace_scopes_json,status,created_at FROM identities WHERE actor_id=?", (actor_id,)).fetchone()
            return self._identity(row) if row else None

    def update_identity_authority(self, actor_id: str, *, roles: tuple[str, ...], workspace_scopes: tuple[str, ...], changed_at: str) -> int:
        """Internal governed authority update; no HTTP self-service endpoint exists in 02-C.

        Role/scope changes revoke all active sessions atomically so stale privilege
        snapshots cannot survive an authority mutation.
        """
        self.initialize()
        if not roles:
            raise AuthStoreError("identity must retain at least one role")
        with self.transaction() as con:
            cur=con.execute("UPDATE identities SET roles_json=?, workspace_scopes_json=? WHERE actor_id=? AND status='active'", (json.dumps(list(roles)), json.dumps(list(workspace_scopes)), actor_id))
            if cur.rowcount != 1:
                raise AuthStoreError("identity authority update target not found")
            revoked=con.execute("UPDATE sessions SET revoked_at=?, revoke_reason='authority-changed' WHERE actor_id=? AND revoked_at IS NULL", (changed_at, actor_id)).rowcount
        return int(revoked)

    def get_credential(self, actor_id: str) -> CredentialRecord | None:
        self.initialize()
        with self._connect() as con:
            row = con.execute("SELECT actor_id,username,password_hash,salt,kdf_algorithm,kdf_version,kdf_params_json,created_at,updated_at,credential_version FROM credentials WHERE actor_id=?", (actor_id,)).fetchone()
            if row is None:
                return None
            return CredentialRecord(row[0], row[1], bytes(row[2]), bytes(row[3]), row[4], int(row[5]), json.loads(row[6]), row[7], row[8], int(row[9]))

    def bootstrap_owner(self, identity: LocalIdentity, credential: CredentialRecord) -> None:
        self.initialize()
        try:
            with self.transaction() as con:
                existing = con.execute("SELECT 1 FROM identities WHERE roles_json LIKE '%\"owner\"%' LIMIT 1").fetchone()
                if existing:
                    raise AuthStoreError("first-run owner is already bootstrapped")
                con.execute("INSERT INTO identities(actor_id,username,display_name,roles_json,workspace_scopes_json,status,created_at) VALUES(?,?,?,?,?,?,?)", (identity.actor_id, identity.username, identity.display_name, json.dumps(list(identity.roles)), json.dumps(list(identity.workspace_scopes)), identity.status, identity.created_at))
                con.execute("INSERT INTO credentials(actor_id,username,password_hash,salt,kdf_algorithm,kdf_version,kdf_params_json,created_at,updated_at,credential_version) VALUES(?,?,?,?,?,?,?,?,?,?)", (credential.actor_id, credential.username, credential.password_hash, credential.salt, credential.kdf_algorithm, credential.kdf_version, json.dumps(credential.kdf_params, sort_keys=True), credential.created_at, credential.updated_at, credential.credential_version))
        except sqlite3.IntegrityError as exc:
            raise AuthStoreError("first-run owner bootstrap conflict") from exc

    def insert_session(self, record: SessionRecord, *, con: sqlite3.Connection | None = None) -> None:
        target = con or self._open_initialized_connection()
        own = con is None
        try:
            target.execute("INSERT INTO sessions(token_hash,csrf_hash,actor_id,roles_json,workspace_scopes_json,created_at,last_seen_at,absolute_expires_at,idle_timeout_seconds,revoked_at,revoke_reason,rotation_counter) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (record.token_hash, record.csrf_hash, record.actor_id, json.dumps(list(record.roles)), json.dumps(list(record.workspace_scopes)), record.created_at, record.last_seen_at, record.absolute_expires_at, record.idle_timeout_seconds, record.revoked_at, record.revoke_reason, record.rotation_counter))
            if own: target.commit()
        finally:
            if own: target.close()

    def get_session(self, token_hash: str) -> SessionRecord | None:
        self.initialize()
        with self._connect() as con:
            row = con.execute("SELECT token_hash,csrf_hash,actor_id,roles_json,workspace_scopes_json,created_at,last_seen_at,absolute_expires_at,idle_timeout_seconds,revoked_at,revoke_reason,rotation_counter FROM sessions WHERE token_hash=?", (token_hash,)).fetchone()
            if row is None: return None
            return SessionRecord(row[0], row[1], row[2], tuple(json.loads(row[3])), tuple(json.loads(row[4])), row[5], row[6], row[7], int(row[8]), row[9], row[10], int(row[11]))

    def find_session_by_authority(self, *, actor_id: str, created_at: str, rotation_counter: int) -> SessionRecord | None:
        """Resolve one session by non-secret authority coordinates for approval revalidation."""
        self.initialize()
        with self._connect() as con:
            row = con.execute(
                "SELECT token_hash,csrf_hash,actor_id,roles_json,workspace_scopes_json,created_at,last_seen_at,absolute_expires_at,idle_timeout_seconds,revoked_at,revoke_reason,rotation_counter "
                "FROM sessions WHERE actor_id=? AND created_at=? AND rotation_counter=? ORDER BY rowid DESC LIMIT 1",
                (actor_id, created_at, int(rotation_counter)),
            ).fetchone()
            if row is None:
                return None
            return SessionRecord(row[0], row[1], row[2], tuple(json.loads(row[3])), tuple(json.loads(row[4])), row[5], row[6], row[7], int(row[8]), row[9], row[10], int(row[11]))

    def touch_session(self, token_hash: str, last_seen_at: str) -> None:
        self.initialize()
        with self._connect() as con:
            con.execute("UPDATE sessions SET last_seen_at=? WHERE token_hash=? AND revoked_at IS NULL", (last_seen_at, token_hash)); con.commit()

    def revoke_session(self, token_hash: str, *, revoked_at: str, reason: str, con: sqlite3.Connection | None = None) -> bool:
        target = con or self._open_initialized_connection(); own = con is None
        try:
            cur = target.execute("UPDATE sessions SET revoked_at=?, revoke_reason=? WHERE token_hash=? AND revoked_at IS NULL", (revoked_at, reason, token_hash))
            if own: target.commit()
            return cur.rowcount == 1
        finally:
            if own: target.close()

    def audit(self, *, event_type: str, actor_id: str | None, outcome: str, reason_code: str, created_at: str, metadata: dict[str, object] | None = None) -> None:
        safe = {k:v for k,v in (metadata or {}).items() if k not in {"password","token","session","cookie","csrf","password_hash","salt"}}
        self.initialize()
        with self._connect() as con:
            con.execute("INSERT INTO auth_events(event_type,actor_id,outcome,reason_code,created_at,metadata_json) VALUES(?,?,?,?,?,?)", (event_type, actor_id, outcome, reason_code, created_at, json.dumps(safe, sort_keys=True))); con.commit()

    def audit_summary(self) -> dict[str, int]:
        self.initialize()
        with self._connect() as con:
            rows = con.execute("SELECT event_type,COUNT(*) FROM auth_events GROUP BY event_type ORDER BY event_type").fetchall()
            return {str(k): int(v) for k,v in rows}

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        self.initialize()
        con = self._connect_raw()
        try:
            con.execute("BEGIN IMMEDIATE")
            yield con
            con.commit()
        except Exception:
            con.rollback(); raise
        finally:
            con.close()

    def _open_initialized_connection(self) -> sqlite3.Connection:
        self.initialize(); return self._connect_raw()

    def _connect(self) -> sqlite3.Connection:
        return self._connect_raw()

    def _connect_raw(self) -> sqlite3.Connection:
        try:
            con = sqlite3.connect(self.db_path, timeout=5.0)
            con.execute("PRAGMA foreign_keys=ON")
            con.execute("PRAGMA journal_mode=WAL")
            return con
        except sqlite3.DatabaseError as exc:
            raise AuthStoreError("local auth store cannot be opened safely") from exc

    def _resolve_runtime_path(self, relative: str) -> Path:
        rel = Path(relative)
        if rel.is_absolute() or ".." in rel.parts:
            raise AuthStoreError("auth store path must be repository-relative")
        current = self.root
        for part in rel.parts[:-1]:
            current = current / part
            if current.exists() and current.is_symlink():
                raise AuthStoreError("auth store path cannot traverse symlinks")
        target = (self.root / rel).resolve(strict=False)
        try: target.relative_to(self.root)
        except ValueError as exc: raise AuthStoreError("auth store escaped repository root") from exc
        return target

    @staticmethod
    def _identity(row: sqlite3.Row | tuple[object, ...]) -> LocalIdentity:
        return LocalIdentity(str(row[0]), str(row[1]), str(row[2]), tuple(json.loads(str(row[3]))), tuple(json.loads(str(row[4]))), str(row[5]), str(row[6]))
