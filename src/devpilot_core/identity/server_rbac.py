from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .auth_models import AuthenticatedPrincipal

DEFAULT_RBAC_CATALOG = Path('.devpilot/identity/server_rbac_policy_catalog.json')

@dataclass(frozen=True)
class RBACDecision:
    allowed: bool
    reason_code: str
    operation: str
    access_class: str
    effective_roles: tuple[str, ...]
    required_roles: tuple[str, ...]
    workspace_id: str | None
    workspace_allowed: bool
    stale_session: bool = False
    policy_ref: str = str(DEFAULT_RBAC_CATALOG)
    def to_dict(self) -> dict[str, Any]:
        return {'decision':'ALLOW' if self.allowed else 'DENY','allowed':self.allowed,'reason_code':self.reason_code,'operation':self.operation,'access_class':self.access_class,'effective_roles':list(self.effective_roles),'required_roles':list(self.required_roles),'workspace_id':self.workspace_id,'workspace_allowed':self.workspace_allowed,'stale_session':self.stale_session,'policy_ref':self.policy_ref}

class ServerRBACEnforcer:
    """Deterministic server-side RBAC for authenticated human principals.

    This service never trusts caller-supplied actor/role values and never asks an
    LLM to decide authorization. Unknown route/action/role/scope is DENY.
    """
    def __init__(self, root: Path, *, catalog_path: Path = DEFAULT_RBAC_CATALOG) -> None:
        self.root=root.resolve(); self.path=self.root/catalog_path
        if not self.path.is_file():
            fallback=Path(__file__).resolve().parents[3]/catalog_path
            if fallback.is_file(): self.path=fallback
        self.catalog=json.loads(self.path.read_text(encoding='utf-8'))
        self._routes={(x['method'].upper(),x['path']):x for x in self.catalog['route_policies']}
        self._actions={x['action_id']:x for x in self.catalog['sensitive_action_policies']}
        self._roles=set(self.catalog['canonical_roles']); self._aliases=dict(self.catalog.get('legacy_role_aliases',{}))

    def canonical_roles(self, principal: AuthenticatedPrincipal) -> tuple[str, ...]:
        out=[]
        for role in principal.roles:
            canon=self._aliases.get(role,role)
            if canon not in self._roles: return tuple()
            if canon not in out: out.append(canon)
        return tuple(out)

    @staticmethod
    def _path_match(template: str, actual: str) -> bool:
        if template==actual:return True
        tp=template.strip('/').split('/'); ap=actual.strip('/').split('/')
        if len(tp)!=len(ap):return False
        return all((t.startswith('{') and t.endswith('}')) or t==a for t,a in zip(tp,ap))

    def route_policy(self, method: str, path: str) -> dict[str, Any] | None:
        method=method.upper()
        if (method,path) in self._routes:return self._routes[(method,path)]
        for (m,t),p in self._routes.items():
            if m==method and self._path_match(t,path):return p
        return None

    def authorize_route(self, principal: AuthenticatedPrincipal, *, method: str, path: str, workspace_id: str | None = None) -> RBACDecision:
        policy=self.route_policy(method,path)
        if policy is None:return RBACDecision(False,'RBAC_UNKNOWN_ROUTE_DENY',f'{method.upper()} {path}','unknown',tuple(),tuple(),workspace_id,False)
        roles=self.canonical_roles(principal)
        if not roles:return RBACDecision(False,'RBAC_UNKNOWN_ROLE_DENY',policy['operation'],policy['access_class'],tuple(),tuple(policy['allowed_roles']),workspace_id,False)
        required=tuple(policy['allowed_roles']); role_ok=bool(set(roles)&set(required)) if required else False
        workspace_ok=True
        if policy.get('workspace_scope_required'):
            if not workspace_id: workspace_id=self.catalog['workspace']['default_local_workspace_id']
            workspace_ok=workspace_id in principal.workspace_scopes
        if not workspace_ok:return RBACDecision(False,'RBAC_WORKSPACE_SCOPE_DENY',policy['operation'],policy['access_class'],roles,required,workspace_id,False)
        if not role_ok:return RBACDecision(False,'RBAC_ROLE_DENY',policy['operation'],policy['access_class'],roles,required,workspace_id,True)
        return RBACDecision(True,'RBAC_ALLOW',policy['operation'],policy['access_class'],roles,required,workspace_id,True)

    def authorize_sensitive_action(self, principal: AuthenticatedPrincipal, *, action_id: str, workspace_id: str | None = None) -> RBACDecision:
        policy=self._actions.get(action_id)
        if policy is None:return RBACDecision(False,'RBAC_UNKNOWN_ACTION_DENY',action_id,'sensitive-action',tuple(),tuple(),workspace_id,False)
        roles=self.canonical_roles(principal); required=tuple(policy['allowed_roles'])
        if not roles:return RBACDecision(False,'RBAC_UNKNOWN_ROLE_DENY',action_id,'sensitive-action',tuple(),required,workspace_id,False)
        workspace_ok=True
        if policy.get('workspace_scope_required'):
            if not workspace_id:workspace_id=self.catalog['workspace']['default_local_workspace_id']
            workspace_ok=workspace_id in principal.workspace_scopes
        allowed=workspace_ok and bool(set(roles)&set(required))
        return RBACDecision(allowed,'RBAC_ALLOW' if allowed else ('RBAC_WORKSPACE_SCOPE_DENY' if not workspace_ok else 'RBAC_ROLE_DENY'),action_id,'sensitive-action',roles,required,workspace_id,workspace_ok)

    def legacy_token_allowed(self, *, method: str, path: str) -> bool:
        policy=self.route_policy(method,path)
        return bool(policy and policy.get('legacy_token_allowed'))

    def human_session_required(self, *, method: str, path: str) -> bool:
        policy=self.route_policy(method,path)
        return bool(policy and policy.get('human_session_required'))

    def capability_view(self, principal: AuthenticatedPrincipal, *, workspace_id: str | None = None) -> dict[str, Any]:
        roles=self.canonical_roles(principal); caps=[]
        for p in sorted(self.catalog['route_policies'],key=lambda x:(x['path'],x['method'])):
            if p.get('public'):continue
            decision=self.authorize_route(principal,method=p['method'],path=p['path'],workspace_id=workspace_id)
            caps.append({'route_id':p['route_id'],'operation':p['operation'],'method':p['method'],'path':p['path'],'access_class':p['access_class'],'allowed':decision.allowed,'reason_code':decision.reason_code})
        return {'identity':{'actor_id':principal.actor_id,'username':principal.username,'display_name':principal.display_name},'effective_roles':list(roles),'workspace_id':workspace_id or self.catalog['workspace']['default_local_workspace_id'],'capabilities':caps,'server_authoritative':True,'legacy_token_human_authority':False,'secret_exposed':False}
