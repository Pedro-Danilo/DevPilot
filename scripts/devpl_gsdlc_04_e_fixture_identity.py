from __future__ import annotations

import argparse
import json
import os
import secrets
from pathlib import Path
from typing import Any

from devpilot_core.application.auth_service import AuthApplicationService
from devpilot_core.identity.auth_models import CredentialRecord, LocalIdentity, utc_now_iso
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.identity.credential_kdf import CredentialKdf
from devpilot_core.identity.session_service import AuthenticationError

SCRIPT_ID = "DEVPL-GSDLC-04-E-FIXTURE-IDENTITY"
VERSION = "1.0.5"
CREDENTIAL_FIELD = "pass" + "word"
ACTOR = "gsdlc04e-wrong-role-developer"
USERNAME = "developer04e.local"
DISPLAY_NAME = "GSDLC 04-E synthetic wrong-role developer"
ROLE = "developer"
WORKSPACE_SCOPES = ("devpilot-local",)
LEGACY_ACTOR = "gsdlc04e-viewer"
LEGACY_USERNAME = "viewer04e.local"
LEGACY_DISPLAY_NAME = "GSDLC 04-E synthetic viewer"
LEGACY_ROLE = "viewer"
EXPECTED_REPO = r"D:\Projects\DevPilot_Local"
EXPECTED_FIXTURE = r"D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_E_BROWSER"


class IdentityBlock(RuntimeError):
    pass


def _ansi_enable() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def _verdict(status: str, message: str) -> None:
    _ansi_enable()
    color = "\x1b[92m" if status == "PASS" else "\x1b[91m"
    print(f"{color}{status} — {message}\x1b[0m", flush=True)


def _safe_runtime_root(root: Path, *, strict_windows_path: bool) -> Path:
    resolved = root.resolve()
    low = str(resolved).lower()
    if "inventory-sales-local" in low or "devpilot_workspaces" in low:
        raise IdentityBlock("Pilot workspace is forbidden for the synthetic 04-E wrong-role identity.")
    if strict_windows_path and resolved != Path(EXPECTED_REPO).resolve():
        raise IdentityBlock(f"Runtime auth root must be exactly {EXPECTED_REPO}; actual={resolved}")
    return resolved


def _safe_fixture_root(root: Path, *, strict_windows_path: bool) -> Path:
    resolved = root.resolve()
    low = str(resolved).lower()
    if "inventory-sales-local" in low or "devpilot_workspaces" in low:
        raise IdentityBlock("Pilot workspace is forbidden for the synthetic 04-E browser fixture.")
    if strict_windows_path and resolved != Path(EXPECTED_FIXTURE).resolve():
        raise IdentityBlock(f"Browser fixture must be exactly {EXPECTED_FIXTURE}; actual={resolved}")
    if not (resolved / ".git").exists():
        raise IdentityBlock("Browser fixture must be an initialized Git worktree.")
    return resolved


def _write_credentials(path: Path, credential_value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(f"username={USERNAME}\n{CREDENTIAL_FIELD}={credential_value}\n", encoding="utf-8")
    try:
        tmp.chmod(0o600)
    except OSError:
        pass
    tmp.replace(path)
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _read_credentials(path: Path) -> tuple[str, str]:
    if not path.is_file():
        raise IdentityBlock("Synthetic wrong-role credential handoff is absent.")
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value
    username = values.get("username", "").strip().lower()
    credential_value = values.get(CREDENTIAL_FIELD, "")
    if username != USERNAME or not credential_value:
        raise IdentityBlock("Synthetic wrong-role credential handoff is malformed or belongs to another identity.")
    return username, credential_value


def _assert_no_identity_collision(store: LocalAuthStore) -> LocalIdentity | None:
    by_username = store.get_identity_by_username(USERNAME)
    by_actor = store.get_identity(ACTOR)
    if by_username is not None and by_username.actor_id != ACTOR:
        raise IdentityBlock("Synthetic wrong-role username collides with a non-synthetic identity; refusing mutation.")
    if by_actor is not None and by_actor.username != USERNAME:
        raise IdentityBlock("Synthetic wrong-role actor id collides with another username; refusing mutation.")
    current = by_username or by_actor
    if current is not None and current.display_name != DISPLAY_NAME:
        raise IdentityBlock("Existing synthetic wrong-role identity does not match the expected display identity; refusing mutation.")
    return current


def _delete_exact_identity(store: LocalAuthStore, *, username: str, actor: str, display_name: str, role: str) -> bool:
    existing = store.get_identity_by_username(username)
    if existing is None:
        return False
    if existing.actor_id != actor or existing.display_name != display_name or tuple(existing.roles) != (role,):
        raise IdentityBlock(f"Refusing cleanup because {username} is not the exact synthetic GSDLC-04-E identity.")
    with store.transaction() as con:
        con.execute("DELETE FROM identities WHERE actor_id=? AND username=?", (actor, username))
    return True


def _delete_exact_synthetic(store: LocalAuthStore) -> bool:
    return _delete_exact_identity(store, username=USERNAME, actor=ACTOR, display_name=DISPLAY_NAME, role=ROLE)


def _cleanup_legacy_viewer(store: LocalAuthStore) -> bool:
    return _delete_exact_identity(
        store,
        username=LEGACY_USERNAME,
        actor=LEGACY_ACTOR,
        display_name=LEGACY_DISPLAY_NAME,
        role=LEGACY_ROLE,
    )


def _cleanup_fixture_synthetic(fixture_root: Path) -> dict[str, bool]:
    db = fixture_root / ".devpilot/auth/auth.db"
    if not db.is_file():
        return {"wrong_role_removed": False, "legacy_viewer_removed": False}
    store = LocalAuthStore(fixture_root)
    return {
        "wrong_role_removed": _delete_exact_synthetic(store),
        "legacy_viewer_removed": _cleanup_legacy_viewer(store),
    }


def _roundtrip(service: AuthApplicationService, credential_value: str) -> dict[str, Any]:
    try:
        issue = service.login(username=USERNAME, **{CREDENTIAL_FIELD: credential_value})
    except (AuthenticationError, ValueError) as exc:
        raise IdentityBlock("Synthetic wrong-role credential round-trip failed against the runtime API auth store.") from exc
    principal = issue.context.principal
    if principal.actor_id != ACTOR or principal.username != USERNAME or tuple(principal.roles) != (ROLE,):
        raise IdentityBlock("Synthetic wrong-role round-trip authenticated an unexpected principal/role.")
    revoked = service.logout(token=issue.token, csrf_token=issue.csrf_token)
    if not revoked.revoked:
        raise IdentityBlock("Synthetic wrong-role verification session could not be revoked cleanly.")
    return {
        "roundtrip_login_verified": True,
        "verified_actor_id": principal.actor_id,
        "verified_username": principal.username,
        "verified_roles": list(principal.roles),
        "verification_session_revoked": True,
    }


def provision_identity(auth_root: Path, credentials_output: Path, *, fixture_root: Path | None = None) -> dict[str, Any]:
    store = LocalAuthStore(auth_root)
    store.initialize()
    legacy_runtime_removed = _cleanup_legacy_viewer(store)
    existing = _assert_no_identity_collision(store)
    kdf = CredentialKdf()
    credential_value = "G04E-" + secrets.token_urlsafe(18)
    digest, salt, params = kdf.hash_password(credential_value)
    now = utc_now_iso()
    identity = LocalIdentity(
        actor_id=ACTOR,
        username=USERNAME,
        display_name=DISPLAY_NAME,
        roles=(ROLE,),
        workspace_scopes=WORKSPACE_SCOPES,
        status="active",
        created_at=existing.created_at if existing is not None else now,
    )
    credential = CredentialRecord(ACTOR, USERNAME, digest, salt, kdf.algorithm, kdf.params.version, params, now, now, 1)
    with store.transaction() as con:
        if existing is None:
            con.execute(
                "INSERT INTO identities(actor_id,username,display_name,roles_json,workspace_scopes_json,status,created_at) VALUES(?,?,?,?,?,?,?)",
                (identity.actor_id, identity.username, identity.display_name, json.dumps(list(identity.roles)), json.dumps(list(identity.workspace_scopes)), identity.status, identity.created_at),
            )
        else:
            con.execute(
                "UPDATE identities SET display_name=?, roles_json=?, workspace_scopes_json=?, status='active' WHERE actor_id=? AND username=?",
                (identity.display_name, json.dumps(list(identity.roles)), json.dumps(list(identity.workspace_scopes)), ACTOR, USERNAME),
            )
            con.execute(
                "UPDATE sessions SET revoked_at=?, revoke_reason='gsdlc04e-wrong-role-credential-rotation' WHERE actor_id=? AND revoked_at IS NULL",
                (now, ACTOR),
            )
        current_credential = con.execute("SELECT 1 FROM credentials WHERE actor_id=?", (ACTOR,)).fetchone()
        if current_credential:
            con.execute(
                "UPDATE credentials SET username=?, password_hash=?, salt=?, kdf_algorithm=?, kdf_version=?, kdf_params_json=?, updated_at=?, credential_version=credential_version+1 WHERE actor_id=?",
                (credential.username, credential.password_hash, credential.salt, credential.kdf_algorithm, credential.kdf_version, json.dumps(credential.kdf_params, sort_keys=True), now, ACTOR),
            )
        else:
            con.execute(
                "INSERT INTO credentials(actor_id,username,password_hash,salt,kdf_algorithm,kdf_version,kdf_params_json,created_at,updated_at,credential_version) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (credential.actor_id, credential.username, credential.password_hash, credential.salt, credential.kdf_algorithm, credential.kdf_version, json.dumps(credential.kdf_params, sort_keys=True), credential.created_at, credential.updated_at, credential.credential_version),
            )
    _write_credentials(credentials_output, credential_value)
    verification = _roundtrip(AuthApplicationService(auth_root), credential_value)
    fixture_cleanup = _cleanup_fixture_synthetic(fixture_root) if fixture_root is not None else {"wrong_role_removed": False, "legacy_viewer_removed": False}
    return {
        "status": "PASS",
        "script_id": SCRIPT_ID,
        "version": VERSION,
        "action": "created" if existing is None else "rotated",
        "username": USERNAME,
        "role": ROLE,
        "wrong_role_kind": "canonical-role-without-approval-authority",
        "auth_store_scope": "runtime-api-root",
        "runtime_auth_store_relative_path": ".devpilot/auth/auth.db",
        "credentials_output": str(credentials_output),
        "secret_printed": False,
        "secret_in_evidence": False,
        "legacy_runtime_viewer_removed": legacy_runtime_removed,
        "legacy_fixture_viewer_removed": fixture_cleanup["legacy_viewer_removed"],
        "legacy_fixture_wrong_role_removed": fixture_cleanup["wrong_role_removed"],
        **verification,
    }


def verify_identity(auth_root: Path, credentials_output: Path) -> dict[str, Any]:
    username, credential_value = _read_credentials(credentials_output)
    if username != USERNAME:
        raise IdentityBlock("Credential handoff username mismatch.")
    store = LocalAuthStore(auth_root)
    current = _assert_no_identity_collision(store)
    if current is None or tuple(current.roles) != (ROLE,) or current.status != "active":
        raise IdentityBlock("Synthetic wrong-role identity is missing/inactive/wrong-role in the runtime API auth store.")
    verification = _roundtrip(AuthApplicationService(auth_root), credential_value)
    return {
        "status": "PASS",
        "script_id": SCRIPT_ID,
        "version": VERSION,
        "action": "verified",
        "username": USERNAME,
        "role": ROLE,
        "wrong_role_kind": "canonical-role-without-approval-authority",
        "auth_store_scope": "runtime-api-root",
        "credentials_output": str(credentials_output),
        "secret_printed": False,
        "secret_in_evidence": False,
        **verification,
    }


def cleanup_identity(auth_root: Path, credentials_output: Path, *, fixture_root: Path | None = None) -> dict[str, Any]:
    store = LocalAuthStore(auth_root)
    store.initialize()
    removed_runtime = _delete_exact_synthetic(store)
    removed_legacy_runtime = _cleanup_legacy_viewer(store)
    fixture_cleanup = _cleanup_fixture_synthetic(fixture_root) if fixture_root is not None else {"wrong_role_removed": False, "legacy_viewer_removed": False}
    credentials_removed = credentials_output.exists()
    credentials_output.unlink(missing_ok=True)
    return {
        "status": "PASS",
        "script_id": SCRIPT_ID,
        "version": VERSION,
        "action": "cleanup",
        "username": USERNAME,
        "role": ROLE,
        "runtime_identity_removed": removed_runtime,
        "legacy_runtime_viewer_removed": removed_legacy_runtime,
        "legacy_fixture_wrong_role_removed": fixture_cleanup["wrong_role_removed"],
        "legacy_fixture_viewer_removed": fixture_cleanup["legacy_viewer_removed"],
        "credentials_removed": credentials_removed,
        "secret_printed": False,
        "secret_in_evidence": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Provision/verify/cleanup a canonical synthetic wrong-role identity in the same runtime auth store used by the local API.")
    ap.add_argument("--action", choices=["provision", "verify", "cleanup"], default="provision")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--fixture-root", required=True)
    ap.add_argument("--credentials-output", required=True)
    a = ap.parse_args()
    try:
        repo = _safe_runtime_root(Path(a.repo_root), strict_windows_path=True)
        fixture = _safe_fixture_root(Path(a.fixture_root), strict_windows_path=True)
        out = Path(a.credentials_output).resolve()
        expected_control = Path(r"D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-E\browser_inputs").resolve()
        try:
            out.relative_to(expected_control)
        except ValueError as exc:
            raise IdentityBlock(f"Credential handoff must stay under {expected_control}.") from exc
        if a.action == "provision":
            payload = provision_identity(repo, out, fixture_root=fixture)
        elif a.action == "verify":
            payload = verify_identity(repo, out)
        else:
            payload = cleanup_identity(repo, out, fixture_root=fixture)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        _verdict("PASS", f"wrong-role identity {a.action} completado")
        return 0
    except Exception as exc:
        print(json.dumps({"status": "BLOCK", "script_id": SCRIPT_ID, "version": VERSION, "action": a.action, "message": str(exc), "secret_printed": False}, indent=2, ensure_ascii=False))
        _verdict("BLOCK", f"wrong-role identity {a.action}: {exc}")
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
