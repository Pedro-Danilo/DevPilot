from __future__ import annotations

from pathlib import Path

from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.identity.credential_kdf import CredentialKdf
from devpilot_core.identity.session_service import LocalAuthService
from devpilot_core.identity.auth_models import utc_now_iso


class AuthApplicationService(LocalAuthService):
    """Application-layer facade for local human authentication.

    Secret-bearing SessionIssue objects never pass through CommandResult or the
    generic ApplicationResponse path, preventing accidental log/report capture.
    The FastAPI auth router consumes this facade directly and emits only safe
    response bodies while setting opaque cookies at the transport boundary.
    """

    def __init__(self, root: Path, *, store: LocalAuthStore | None = None, kdf: CredentialKdf | None = None) -> None:
        super().__init__(root, store=store, kdf=kdf)

    def reconcile_active_workspace_scope(self, workspace_id: str) -> dict[str, object]:
        """Bind the trusted server-active workspace to the local owner identity.

        The workspace id comes from the server-valid persisted project context, not
        from a browser parameter. Existing roles/scopes are preserved. If authority
        changes, LocalAuthStore revokes stale sessions atomically so the next login
        receives the updated scope. First-run installations without an owner remain
        a no-op.
        """
        active = str(workspace_id or "").strip()
        if not active:
            return {"status": "NOOP", "reason": "no-active-workspace", "workspace_id": None, "sessions_revoked": 0}
        identity = self.store.get_identity("local-owner")
        if identity is None or identity.status != "active":
            return {"status": "NOOP", "reason": "owner-not-bootstrapped", "workspace_id": active, "sessions_revoked": 0}
        scopes = tuple(dict.fromkeys((*identity.workspace_scopes, active)))
        if scopes == tuple(identity.workspace_scopes):
            return {"status": "PASS", "reason": "already-bound", "workspace_id": active, "workspace_scopes": list(scopes), "sessions_revoked": 0}
        changed_at = utc_now_iso()
        revoked = self.store.update_identity_authority(
            identity.actor_id, roles=tuple(identity.roles), workspace_scopes=scopes, changed_at=changed_at
        )
        self.store.audit(
            event_type="auth.workspace_scope.reconcile", actor_id=identity.actor_id, outcome="PASS",
            reason_code="ACTIVE_SERVER_WORKSPACE_SCOPE_BOUND", created_at=changed_at,
            metadata={"workspace_id": active, "workspace_scopes": list(scopes), "sessions_revoked": revoked},
        )
        return {"status": "PASS", "reason": "bound", "workspace_id": active, "workspace_scopes": list(scopes), "sessions_revoked": revoked}
