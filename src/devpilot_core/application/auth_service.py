from __future__ import annotations

from pathlib import Path

from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.identity.credential_kdf import CredentialKdf
from devpilot_core.identity.session_service import LocalAuthService


class AuthApplicationService(LocalAuthService):
    """Application-layer facade for local human authentication.

    Secret-bearing SessionIssue objects never pass through CommandResult or the
    generic ApplicationResponse path, preventing accidental log/report capture.
    The FastAPI auth router consumes this facade directly and emits only safe
    response bodies while setting opaque cookies at the transport boundary.
    """

    def __init__(self, root: Path, *, store: LocalAuthStore | None = None, kdf: CredentialKdf | None = None) -> None:
        super().__init__(root, store=store, kdf=kdf)
