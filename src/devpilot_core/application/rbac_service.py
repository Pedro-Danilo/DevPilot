from __future__ import annotations
from pathlib import Path
from devpilot_core.identity.auth_models import AuthenticatedPrincipal
from devpilot_core.identity.server_rbac import RBACDecision, ServerRBACEnforcer

class RBACApplicationService:
    """Typed application facade for session-derived RBAC decisions."""
    def __init__(self, root: Path) -> None:self.enforcer=ServerRBACEnforcer(root)
    def canonical_roles(self, principal: AuthenticatedPrincipal) -> tuple[str, ...]:
        """Return canonical server-authoritative roles through the application boundary."""
        return self.enforcer.canonical_roles(principal)
    def authorize_route(self, principal: AuthenticatedPrincipal, *, method: str, path: str, workspace_id: str|None=None)->RBACDecision:return self.enforcer.authorize_route(principal,method=method,path=path,workspace_id=workspace_id)
    def authorize_sensitive_action(self, principal: AuthenticatedPrincipal, *, action_id: str, workspace_id: str|None=None)->RBACDecision:return self.enforcer.authorize_sensitive_action(principal,action_id=action_id,workspace_id=workspace_id)
    def capability_view(self, principal: AuthenticatedPrincipal, *, workspace_id: str|None=None)->dict:return self.enforcer.capability_view(principal,workspace_id=workspace_id)
    def legacy_token_allowed(self, *, method:str,path:str)->bool:return self.enforcer.legacy_token_allowed(method=method,path=path)
    def human_session_required(self, *, method:str,path:str)->bool:return self.enforcer.human_session_required(method=method,path=path)
