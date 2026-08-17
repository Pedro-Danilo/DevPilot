from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.identity.auth_models import AuthenticatedPrincipal, SessionContext
from devpilot_core.identity.auth_store import LocalAuthStore
from .models import ApprovalRecord, ApprovalStatus

DEFAULT_AUTHORITY_MATRIX = Path(".devpilot/approval/approval_authority_matrix.json")


def safe_session_binding_id(actor_id: str, created_at: str, rotation_counter: int) -> str:
    raw=f"{actor_id}|{created_at}|{int(rotation_counter)}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class AuthenticatedApprovalDecision:
    allowed: bool
    reason_code: str
    actor_id: str
    role_at_decision: str | None
    risk_level: str
    domain: str
    workspace_id: str | None
    self_approval: bool
    separation_of_duties_exception: str | None
    policy_refs: tuple[str, ...]
    session_binding_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": "ALLOW" if self.allowed else "DENY",
            "allowed": self.allowed,
            "reason_code": self.reason_code,
            "actor_id": self.actor_id,
            "role_at_decision": self.role_at_decision,
            "risk_level": self.risk_level,
            "domain": self.domain,
            "workspace_id": self.workspace_id,
            "self_approval": self.self_approval,
            "separation_of_duties_exception": self.separation_of_duties_exception,
            "policy_refs": list(self.policy_refs),
            "session_binding_id": self.session_binding_id,
            "secret_exposed": False,
        }


class AuthenticatedApprovalAuthority:
    """Deterministic D-wave approval authority derived only from human session.

    Caller-provided actor/role values are compatibility hints at most; they can
    only match the authenticated principal and can never replace it.
    """

    def __init__(self, root: Path, *, matrix_path: Path = DEFAULT_AUTHORITY_MATRIX, auth_store: LocalAuthStore | None = None) -> None:
        self.root=root.resolve()
        self.path=self.root/matrix_path
        self.auth_store=auth_store or LocalAuthStore(self.root)
        self.matrix=json.loads(self.path.read_text(encoding="utf-8"))
        cat=self.root/".devpilot/approval/sensitive_action_catalog.json"
        self.sensitive=json.loads(cat.read_text(encoding="utf-8")) if cat.is_file() else {"actions":[]}
        self.actions={str(x.get("action_id")):x for x in self.sensitive.get("actions",[]) if isinstance(x,dict)}

    def evaluate(
        self,
        record: ApprovalRecord,
        *,
        principal: AuthenticatedPrincipal,
        session: SessionContext,
        decision: str,
        caller_actor: str | None = None,
    ) -> AuthenticatedApprovalDecision:
        sid=safe_session_binding_id(principal.actor_id,session.created_at,session.rotation_counter)
        if principal.auth_method!="human-session":
            return self._deny("APPROVAL_HUMAN_SESSION_REQUIRED",record,principal,session,sid)
        if caller_actor and caller_actor.strip() and caller_actor.strip()!=principal.actor_id:
            return self._deny("APPROVAL_ACTOR_SPOOF_BLOCK",record,principal,session,sid)
        if record.status!=ApprovalStatus.REQUESTED.value and not (record.status==ApprovalStatus.APPROVED.value and decision==ApprovalStatus.REVOKED.value):
            return self._deny("APPROVAL_STATE_NOT_DECIDABLE",record,principal,session,sid)
        if record.expired:
            return self._deny("APPROVAL_EXPIRED",record,principal,session,sid)
        risk,domain=self._risk_domain(record)
        workspace=self._workspace(record)
        if workspace and not self._workspace_allowed(principal,workspace):
            return self._deny("APPROVAL_WORKSPACE_SCOPE_DENY",record,principal,session,sid,risk=risk,domain=domain,workspace=workspace)
        role=self._select_role(principal,risk=risk,domain=domain)
        if role is None:
            return self._deny("APPROVAL_ROLE_DENY",record,principal,session,sid,risk=risk,domain=domain,workspace=workspace)

        self_approval=(record.actor==principal.actor_id)
        exception=None
        if decision==ApprovalStatus.APPROVED.value and self_approval:
            if risk=="critical":
                return self._deny("APPROVAL_SOD_CRITICAL_SELF_APPROVAL_DENY",record,principal,session,sid,risk=risk,domain=domain,workspace=workspace,role=role)
            if risk=="high":
                bounded=(role=="owner" and domain in {"workspace","filesystem","git"})
                if not bounded:
                    return self._deny("APPROVAL_SOD_HIGH_SELF_APPROVAL_DENY",record,principal,session,sid,risk=risk,domain=domain,workspace=workspace,role=role)
                exception="bounded-local-single-owner"

        return AuthenticatedApprovalDecision(
            True,"APPROVAL_AUTHORITY_ALLOW",principal.actor_id,role,risk,domain,workspace,
            self_approval,exception,
            (str(DEFAULT_AUTHORITY_MATRIX),".devpilot/identity/server_rbac_policy_catalog.json"),
            sid,
        )

    def decision_metadata(self, decision: AuthenticatedApprovalDecision, session: SessionContext) -> dict[str, Any]:
        return {
            "authenticated_approval_binding": {
                **decision.to_dict(),
                "session_created_at": session.created_at,
                "session_rotation_counter": session.rotation_counter,
                "session_absolute_expires_at": session.absolute_expires_at,
                "binding_version": "DEVPL-GSDLC-02-D/v1",
            }
        }

    def request_metadata(self, principal: AuthenticatedPrincipal, session: SessionContext, *, workspace_id: str | None) -> dict[str, Any]:
        return {
            "authenticated_request_binding": {
                "actor_id": principal.actor_id,
                "effective_roles": list(principal.roles),
                "workspace_id": workspace_id,
                "session_binding_id": safe_session_binding_id(principal.actor_id,session.created_at,session.rotation_counter),
                "session_created_at": session.created_at,
                "session_rotation_counter": session.rotation_counter,
                "binding_version": "DEVPL-GSDLC-02-D/v1",
                "secret_exposed": False,
            }
        }

    def revalidate_persisted_binding(self, record: ApprovalRecord) -> tuple[bool,str]:
        binding=dict(record.metadata.get("authenticated_approval_binding") or {})
        if not binding:
            return False,"APPROVAL_AUTHENTICATED_DECISION_BINDING_REQUIRED"
        actor=str(binding.get("actor_id") or "")
        created=str(binding.get("session_created_at") or "")
        rotation=int(binding.get("session_rotation_counter", -1))
        role=str(binding.get("role_at_decision") or "")
        if not actor or not created or rotation<0 or not role:
            return False,"APPROVAL_AUTHENTICATED_DECISION_BINDING_INVALID"
        session=self.auth_store.find_session_by_authority(actor_id=actor,created_at=created,rotation_counter=rotation)
        if session is None:
            return False,"APPROVAL_DECISION_SESSION_NOT_FOUND"
        if session.revoked_at:
            return False,"APPROVAL_DECISION_SESSION_REVOKED"
        now=datetime.now(timezone.utc)
        try:
            expires=datetime.fromisoformat(session.absolute_expires_at.replace("Z","+00:00")).astimezone(timezone.utc)
        except ValueError:
            return False,"APPROVAL_DECISION_SESSION_INVALID"
        if now>=expires:
            return False,"APPROVAL_DECISION_SESSION_EXPIRED"
        identity=self.auth_store.get_identity(actor)
        if identity is None or identity.status!="active":
            return False,"APPROVAL_DECISION_PRINCIPAL_INACTIVE"
        if tuple(identity.roles)!=tuple(session.roles) or tuple(identity.workspace_scopes)!=tuple(session.workspace_scopes):
            return False,"APPROVAL_DECISION_AUTHORITY_STALE"
        if role not in identity.roles:
            return False,"APPROVAL_DECISION_ROLE_STALE"
        expected=safe_session_binding_id(actor,created,rotation)
        if binding.get("session_binding_id")!=expected:
            return False,"APPROVAL_DECISION_SESSION_BINDING_MISMATCH"
        return True,"APPROVAL_AUTHENTICATED_DECISION_BINDING_VALID"

    def _risk_domain(self, record: ApprovalRecord) -> tuple[str,str]:
        entry=self.actions.get(record.action)
        if entry is None:
            # Tool/action aliases used by current workspace flows.
            for item in self.actions.values():
                if record.tool_id in set(item.get("tool_ids") or []):
                    entry=item;break
        risk=str((entry or {}).get("risk_level") or record.scope.get("risk_level") or "medium").lower()
        domain=str((entry or {}).get("domain") or record.scope.get("domain") or self._infer_domain(record.action)).lower()
        return risk if risk in {"low","medium","high","critical"} else "critical",domain

    def _select_role(self, principal: AuthenticatedPrincipal, *, risk: str, domain: str) -> str | None:
        risk_roles=set(self.matrix["risk_levels"][risk]["roles"])
        domain_roles=set(self.matrix["domain_roles"].get(domain,self.matrix["domain_roles"]["general"]))
        allowed=risk_roles & domain_roles
        for role in principal.roles:
            if role in allowed:return role
        return None

    @staticmethod
    def _infer_domain(action: str) -> str:
        prefix=(action or "").split(".",1)[0].lower()
        return prefix if prefix in {"workspace","filesystem","git","product","architecture","security","release","agent"} else "general"

    @staticmethod
    def _workspace(record: ApprovalRecord) -> str | None:
        return str(record.scope.get("workspace_id") or record.metadata.get("workspace_id") or "").strip() or None

    @staticmethod
    def _workspace_allowed(principal: AuthenticatedPrincipal, workspace: str) -> bool:
        scopes=set(principal.workspace_scopes)
        return workspace in scopes or "devpilot-local" in scopes

    def _deny(self,reason: str,record: ApprovalRecord,principal: AuthenticatedPrincipal,session: SessionContext,sid: str,*,risk: str="critical",domain: str="general",workspace: str|None=None,role: str|None=None) -> AuthenticatedApprovalDecision:
        return AuthenticatedApprovalDecision(False,reason,principal.actor_id,role,risk,domain,workspace,record.actor==principal.actor_id,None,(str(DEFAULT_AUTHORITY_MATRIX),),sid)
