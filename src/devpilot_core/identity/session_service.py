from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from .auth_models import AuthenticatedPrincipal, CredentialRecord, LocalIdentity, SessionContext, SessionIssue, SessionRecord, SessionRevocation, utc_now_iso
from .auth_store import AuthStoreError, LocalAuthStore
from .credential_kdf import CredentialKdf

USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")


class AuthenticationError(RuntimeError): pass
class SessionInvalid(AuthenticationError): pass
class CsrfInvalid(AuthenticationError): pass
class BootstrapUnavailable(AuthenticationError): pass


class LocalAuthService:
    def __init__(self, root: Path, *, store: LocalAuthStore | None = None, kdf: CredentialKdf | None = None, now: Callable[[], datetime] | None = None, idle_timeout_seconds: int = 1800, absolute_timeout_seconds: int = 28800) -> None:
        self.root = root.resolve(); self.store = store or LocalAuthStore(self.root); self.kdf = kdf or CredentialKdf(); self._now = now or (lambda: datetime.now(timezone.utc)); self.idle_timeout_seconds = idle_timeout_seconds; self.absolute_timeout_seconds = absolute_timeout_seconds

    def bootstrap_status(self) -> dict[str, object]:
        return {"first_run_required": not self.store.owner_exists(), "runtime_auth_store": ".devpilot/auth/auth.db", "runtime_store_version": 1, "remote_login_enabled": False, "public_api_enabled": False}

    def bootstrap_owner(self, *, username: str, display_name: str, password: str) -> SessionIssue:
        if self.store.owner_exists(): raise BootstrapUnavailable("first-run owner already exists")
        username = self._normalize_username(username); display_name = self._validate_display_name(display_name)
        digest,salt,params = self.kdf.hash_password(password); now = self._iso(self._now())
        identity = LocalIdentity(actor_id="local-owner", username=username, display_name=display_name, roles=("owner",), workspace_scopes=("devpilot-local",), created_at=now)
        credential = CredentialRecord(identity.actor_id, username, digest, salt, self.kdf.algorithm, self.kdf.params.version, params, now, now, 1)
        try: self.store.bootstrap_owner(identity, credential)
        except AuthStoreError as exc: raise BootstrapUnavailable(str(exc)) from exc
        self.store.audit(event_type="auth.bootstrap_owner", actor_id=identity.actor_id, outcome="PASS", reason_code="FIRST_RUN_OWNER_CREATED", created_at=now, metadata={"roles":["owner"]})
        return self._issue(identity, rotation_counter=0)

    def login(self, *, username: str, password: str) -> SessionIssue:
        normalized = self._normalize_username(username, strict=False); identity = self.store.get_identity_by_username(normalized) if normalized else None; now = self._iso(self._now())
        if identity is None or identity.status != "active":
            self.store.audit(event_type="auth.login", actor_id=None, outcome="BLOCK", reason_code="INVALID_CREDENTIALS", created_at=now); raise AuthenticationError("invalid credentials")
        credential = self.store.get_credential(identity.actor_id)
        if credential is None or not self.kdf.verify(password, expected_hash=credential.password_hash, salt=credential.salt, params=credential.kdf_params):
            self.store.audit(event_type="auth.login", actor_id=identity.actor_id, outcome="BLOCK", reason_code="INVALID_CREDENTIALS", created_at=now); raise AuthenticationError("invalid credentials")
        self.store.audit(event_type="auth.login", actor_id=identity.actor_id, outcome="PASS", reason_code="CREDENTIAL_VERIFIED", created_at=now, metadata={"kdf":credential.kdf_algorithm,"kdf_version":credential.kdf_version,"needs_rehash":self.kdf.needs_rehash(algorithm=credential.kdf_algorithm, version=credential.kdf_version, params=credential.kdf_params)})
        return self._issue(identity, rotation_counter=0)

    def resolve(self, token: str, *, touch: bool = True) -> SessionContext:
        token_hash=self._hash_secret(token); record=self.store.get_session(token_hash)
        if record is None: raise SessionInvalid("session not found")
        now=self._now(); now_iso=self._iso(now)
        if record.revoked_at: raise SessionInvalid("session revoked")
        if now >= self._parse(record.absolute_expires_at): self.store.revoke_session(token_hash,revoked_at=now_iso,reason="absolute-timeout"); raise SessionInvalid("session expired")
        if now - self._parse(record.last_seen_at) > timedelta(seconds=record.idle_timeout_seconds): self.store.revoke_session(token_hash,revoked_at=now_iso,reason="idle-timeout"); raise SessionInvalid("session idle timeout")
        identity=self.store.get_identity(record.actor_id)
        if identity is None or identity.status!="active": raise SessionInvalid("session principal inactive")
        if touch: self.store.touch_session(token_hash,now_iso)
        principal=AuthenticatedPrincipal(identity.actor_id,identity.username,identity.display_name,record.roles,record.workspace_scopes)
        return SessionContext(principal,record.created_at,now_iso if touch else record.last_seen_at,record.absolute_expires_at,record.idle_timeout_seconds,record.rotation_counter)

    def require_csrf(self, token: str, csrf_token: str) -> None:
        record=self.store.get_session(self._hash_secret(token))
        if record is None or record.revoked_at: raise SessionInvalid("session invalid")
        if not csrf_token or not hmac.compare_digest(record.csrf_hash,self._hash_secret(csrf_token)): raise CsrfInvalid("csrf validation failed")

    def rotate(self, *, token: str, csrf_token: str) -> SessionIssue:
        ctx=self.resolve(token,touch=False); self.require_csrf(token,csrf_token); old_hash=self._hash_secret(token); now=self._iso(self._now()); identity=self.store.get_identity(ctx.principal.actor_id)
        if identity is None: raise SessionInvalid("session principal missing")
        with self.store.transaction() as con:
            if not self.store.revoke_session(old_hash,revoked_at=now,reason="rotation",con=con): raise SessionInvalid("session already invalid")
            issue=self._issue(identity,rotation_counter=ctx.rotation_counter+1,con=con)
        self.store.audit(event_type="auth.session.rotate",actor_id=identity.actor_id,outcome="PASS",reason_code="SESSION_ROTATED",created_at=now)
        return issue

    def logout(self, *, token: str, csrf_token: str) -> SessionRevocation:
        ctx=self.resolve(token,touch=False); self.require_csrf(token,csrf_token); now=self._iso(self._now()); revoked=self.store.revoke_session(self._hash_secret(token),revoked_at=now,reason="logout")
        self.store.audit(event_type="auth.logout",actor_id=ctx.principal.actor_id,outcome="PASS" if revoked else "BLOCK",reason_code="SESSION_REVOKED" if revoked else "SESSION_ALREADY_INVALID",created_at=now)
        return SessionRevocation(ctx.principal.actor_id,revoked,"logout",now)

    def revoke_current(self, *, token: str, csrf_token: str, reason: str = "self-revoke") -> SessionRevocation:
        ctx=self.resolve(token,touch=False); self.require_csrf(token,csrf_token); now=self._iso(self._now()); revoked=self.store.revoke_session(self._hash_secret(token),revoked_at=now,reason=reason)
        self.store.audit(event_type="auth.session.revoke",actor_id=ctx.principal.actor_id,outcome="PASS" if revoked else "BLOCK",reason_code="SESSION_REVOKED" if revoked else "SESSION_ALREADY_INVALID",created_at=now)
        return SessionRevocation(ctx.principal.actor_id,revoked,reason,now)

    def _issue(self, identity: LocalIdentity, *, rotation_counter: int, con=None) -> SessionIssue:
        token=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(24); now=self._now(); created=self._iso(now); absolute=self._iso(now+timedelta(seconds=self.absolute_timeout_seconds))
        record=SessionRecord(self._hash_secret(token),self._hash_secret(csrf),identity.actor_id,identity.roles,identity.workspace_scopes,created,created,absolute,self.idle_timeout_seconds,None,None,rotation_counter)
        self.store.insert_session(record,con=con); principal=AuthenticatedPrincipal(identity.actor_id,identity.username,identity.display_name,identity.roles,identity.workspace_scopes); return SessionIssue(token,csrf,SessionContext(principal,created,created,absolute,self.idle_timeout_seconds,rotation_counter))

    @staticmethod
    def _hash_secret(value: str) -> str: return hashlib.sha256(value.encode("utf-8")).hexdigest()
    @staticmethod
    def _iso(value: datetime) -> str: return value.astimezone(timezone.utc).isoformat().replace("+00:00","Z")
    @staticmethod
    def _parse(value: str) -> datetime: return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)
    @staticmethod
    def _normalize_username(value: str, *, strict: bool = True) -> str:
        normalized=(value or "").strip().lower()
        if strict and not USERNAME_RE.fullmatch(normalized): raise ValueError("username must be 3-64 lowercase local characters")
        return normalized if USERNAME_RE.fullmatch(normalized) else ""
    @staticmethod
    def _validate_display_name(value: str) -> str:
        display=(value or "").strip()
        if not 1<=len(display)<=128: raise ValueError("display name must be 1-128 characters")
        return display
