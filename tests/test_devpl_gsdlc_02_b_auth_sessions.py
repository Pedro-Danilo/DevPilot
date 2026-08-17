from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from devpilot_core.identity.credential_kdf import CredentialKdf
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.identity.auth_store import AuthStoreError
from devpilot_core.identity.session_service import AuthenticationError, BootstrapUnavailable, CsrfInvalid, LocalAuthService, SessionInvalid


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 16, 20, 0, tzinfo=timezone.utc)
    def __call__(self) -> datetime:
        return self.value
    def advance(self, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)


def service(tmp_path: Path, *, clock: Clock | None = None, idle: int = 30, absolute: int = 120) -> LocalAuthService:
    return LocalAuthService(tmp_path, now=clock, idle_timeout_seconds=idle, absolute_timeout_seconds=absolute)


def bootstrap(svc: LocalAuthService):
    return svc.bootstrap_owner(username="owner.local", display_name="Local Owner", password="correct horse battery staple")


def test_first_run_bootstrap_exactly_once_and_runtime_store_is_not_source(tmp_path: Path) -> None:
    svc = service(tmp_path)
    assert svc.bootstrap_status()["first_run_required"] is True
    issue = bootstrap(svc)
    assert issue.context.principal.actor_id == "local-owner"
    assert issue.context.principal.roles == ("owner",)
    assert svc.bootstrap_status()["first_run_required"] is False
    with pytest.raises(BootstrapUnavailable):
        bootstrap(svc)
    db = tmp_path / ".devpilot/auth/auth.db"
    assert db.is_file()
    assert "password" not in json.dumps(svc.store.audit_summary()).lower()


def test_scrypt_kdf_is_versioned_and_password_is_never_persisted_plaintext(tmp_path: Path) -> None:
    svc = service(tmp_path)
    bootstrap(svc)
    cred = svc.store.get_credential("local-owner")
    assert cred is not None
    assert cred.kdf_algorithm == "scrypt"
    assert cred.kdf_version == 1
    assert cred.kdf_params["n"] >= 16384
    assert CredentialKdf().verify("correct horse battery staple", expected_hash=cred.password_hash, salt=cred.salt, params=cred.kdf_params)
    raw = (tmp_path / ".devpilot/auth/auth.db").read_bytes()
    assert b"correct horse battery staple" not in raw


def test_valid_invalid_login_and_restart_recovery(tmp_path: Path) -> None:
    svc = service(tmp_path)
    bootstrap(svc)
    with pytest.raises(AuthenticationError):
        svc.login(username="owner.local", password="wrong-password-value")
    issue = svc.login(username="owner.local", password="correct horse battery staple")
    restarted = service(tmp_path)
    ctx = restarted.resolve(issue.token)
    assert ctx.principal.actor_id == "local-owner"
    assert ctx.principal.auth_method == "human-session"


def test_session_rotation_revokes_old_and_new_session_survives_restart(tmp_path: Path) -> None:
    svc = service(tmp_path)
    issue = bootstrap(svc)
    rotated = svc.rotate(token=issue.token, csrf_token=issue.csrf_token)
    assert rotated.token != issue.token
    assert rotated.csrf_token != issue.csrf_token
    assert rotated.context.rotation_counter == 1
    with pytest.raises(SessionInvalid):
        svc.resolve(issue.token)
    assert service(tmp_path).resolve(rotated.token).principal.actor_id == "local-owner"


def test_logout_and_revoke_invalidate_immediately(tmp_path: Path) -> None:
    svc = service(tmp_path)
    issue = bootstrap(svc)
    rev = svc.logout(token=issue.token, csrf_token=issue.csrf_token)
    assert rev.revoked is True
    with pytest.raises(SessionInvalid):
        svc.resolve(issue.token)
    issue2 = svc.login(username="owner.local", password="correct horse battery staple")
    assert svc.revoke_current(token=issue2.token, csrf_token=issue2.csrf_token).revoked is True
    with pytest.raises(SessionInvalid):
        svc.resolve(issue2.token)


def test_idle_and_absolute_timeout_fail_closed(tmp_path: Path) -> None:
    clock = Clock(); svc = service(tmp_path, clock=clock, idle=10, absolute=30)
    issue = bootstrap(svc)
    clock.advance(11)
    with pytest.raises(SessionInvalid):
        svc.resolve(issue.token)
    issue2 = svc.login(username="owner.local", password="correct horse battery staple")
    clock.advance(5); svc.resolve(issue2.token)
    clock.advance(26)
    with pytest.raises(SessionInvalid):
        svc.resolve(issue2.token)


def test_csrf_mismatch_is_denied(tmp_path: Path) -> None:
    svc=service(tmp_path); issue=bootstrap(svc)
    with pytest.raises(CsrfInvalid):
        svc.require_csrf(issue.token, "not-the-csrf-token")


def test_corrupt_existing_store_fails_closed(tmp_path: Path) -> None:
    db=tmp_path/".devpilot/auth/auth.db"; db.parent.mkdir(parents=True); db.write_bytes(b"not a sqlite database")
    with pytest.raises(AuthStoreError):
        service(tmp_path).bootstrap_status()


def test_auth_audit_contains_no_password_session_or_csrf_secrets(tmp_path: Path) -> None:
    svc=service(tmp_path); issue=bootstrap(svc); svc.logout(token=issue.token,csrf_token=issue.csrf_token)
    con=sqlite3.connect(tmp_path/".devpilot/auth/auth.db")
    values="\n".join(str(x) for row in con.execute("SELECT event_type,actor_id,outcome,reason_code,metadata_json FROM auth_events") for x in row)
    con.close()
    assert issue.token not in values
    assert issue.csrf_token not in values
    assert "correct horse battery staple" not in values


def test_store_path_escape_is_blocked(tmp_path: Path) -> None:
    with pytest.raises(AuthStoreError):
        LocalAuthStore(tmp_path, db_relative_path="../auth.db")


def test_store_symlink_traversal_is_blocked_when_platform_can_create_symlink(tmp_path: Path) -> None:
    real=tmp_path/"real"; real.mkdir(); link=tmp_path/".devpilot"
    try:
        link.symlink_to(real, target_is_directory=True)
    except OSError as exc:
        if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
            pytest.skip("Windows symlink creation privilege unavailable; path-escape protection is tested separately.")
        raise
    with pytest.raises(AuthStoreError):
        LocalAuthStore(tmp_path).initialize()
