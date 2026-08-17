from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.approval.authenticated_binding import AuthenticatedApprovalAuthority
from devpilot_core.approval.models import ApprovalRecord, ApprovalStatus
from devpilot_core.application import AuthApplicationService
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.identity.session_service import LocalAuthService
from devpilot_core.interfaces.api.app import create_app

ROOT=Path(__file__).resolve().parents[1]
PASSWORD="A-very-long-local-password-123"


def _requested(*, action: str="filesystem.workspace_document_apply", tool_id: str="workspace.edit.apply", actor: str="local-owner", workspace: str="devpilot-local") -> ApprovalRecord:
    return ApprovalRecord(
        approval_id="apr-d-test",
        subject="plan-001",
        tool_id=tool_id,
        action=action,
        status=ApprovalStatus.REQUESTED.value,
        actor=actor,
        reason="request",
        scope={"tool_id":tool_id,"action":action,"subject":"plan-001","subject_hash":"abc","workspace_id":workspace},
        created_at="2026-08-17T12:00:00Z",
        updated_at="2026-08-17T12:00:00Z",
        expires_at="2099-01-01T00:00:00Z",
        metadata={},
    )


def test_authenticated_authority_uses_session_actor_and_bounded_high_self_approval(tmp_path: Path) -> None:
    auth=LocalAuthService(tmp_path)
    issue=auth.bootstrap_owner(username="owner",display_name="Owner",password=PASSWORD)
    authority=AuthenticatedApprovalAuthority(ROOT)
    allowed=authority.evaluate(_requested(),principal=issue.context.principal,session=issue.context,decision="approved")
    assert allowed.allowed is True
    assert allowed.actor_id=="local-owner"
    assert allowed.role_at_decision=="owner"
    assert allowed.separation_of_duties_exception=="bounded-local-single-owner"
    spoof=authority.evaluate(_requested(),principal=issue.context.principal,session=issue.context,decision="approved",caller_actor="attacker")
    assert spoof.allowed is False and spoof.reason_code=="APPROVAL_ACTOR_SPOOF_BLOCK"


def test_critical_self_approval_is_denied(tmp_path: Path) -> None:
    auth=LocalAuthService(tmp_path)
    issue=auth.bootstrap_owner(username="owner",display_name="Owner",password=PASSWORD)
    record=_requested(action="release.publish_deploy_tag",tool_id="release.deploy")
    decision=AuthenticatedApprovalAuthority(ROOT).evaluate(record,principal=issue.context.principal,session=issue.context,decision="approved")
    assert decision.allowed is False
    assert decision.reason_code=="APPROVAL_SOD_CRITICAL_SELF_APPROVAL_DENY"


def test_persisted_binding_revalidates_session_and_fails_after_revoke(tmp_path: Path) -> None:
    auth=LocalAuthService(tmp_path)
    issue=auth.bootstrap_owner(username="owner",display_name="Owner",password=PASSWORD)
    authority=AuthenticatedApprovalAuthority(ROOT)
    decision=authority.evaluate(_requested(),principal=issue.context.principal,session=issue.context,decision="approved")
    metadata=authority.decision_metadata(decision,issue.context)
    record=_requested()
    bound=ApprovalRecord(**{**record.__dict__,"status":"approved","metadata":metadata,"scope":{**record.scope,"role_at_decision":"owner"}})
    # Keep source-controlled policy under ROOT while injecting the isolated
    # runtime auth store explicitly.  Source policy and runtime session state
    # are separate authority roots after DEVPL-GSDLC-02-D.
    checker=AuthenticatedApprovalAuthority(ROOT, auth_store=auth.store)
    ok,reason=checker.revalidate_persisted_binding(bound)
    assert ok is True and reason=="APPROVAL_AUTHENTICATED_DECISION_BINDING_VALID"
    auth.store.revoke_session(auth._hash_secret(issue.token),revoked_at="2026-08-17T12:10:00Z",reason="test")
    ok,reason=checker.revalidate_persisted_binding(bound)
    assert ok is False and reason=="APPROVAL_DECISION_SESSION_REVOKED"


def _api(tmp_path: Path):
    store=LocalAuthStore(tmp_path)
    auth=AuthApplicationService(tmp_path,store=store)
    return TestClient(create_app(ROOT,api_token="legacy-token-test",auth_service=auth)),store


def _bootstrap(client: TestClient) -> None:
    r=client.post("/api/v1/auth/bootstrap/owner",json={"username":"owner","display_name":"Owner","password":PASSWORD},headers={"origin":"http://127.0.0.1:5173"})
    assert r.status_code==201


def _csrf(client: TestClient) -> dict[str,str]:
    return {"origin":"http://127.0.0.1:5173","X-DevPilot-CSRF":str(client.cookies.get("devpilot_csrf") or "")}


def test_approval_request_and_decision_require_session_and_reject_actor_spoof(tmp_path: Path) -> None:
    client,_=_api(tmp_path)
    body={"tool_id":"tests.run","action":"execute","subject":"gsdlc02d","reason":"security test","ttl_minutes":30}
    token_only=client.post("/api/v1/approvals/request",json=body,headers={"X-DevPilot-Token":"legacy-token-test"})
    assert token_only.status_code in {401,403}
    _bootstrap(client)
    spoof=client.post("/api/v1/approvals/request",json={**body,"actor":"attacker"},headers=_csrf(client))
    assert spoof.status_code==403
    created=client.post("/api/v1/approvals/request",json=body,headers=_csrf(client))
    assert created.status_code==200
    approval=created.json()["data"]["approval"]
    assert approval["actor"]=="local-owner"
    approval_id=approval["approval_id"]
    spoof_decision=client.post(f"/api/v1/approvals/{approval_id}/approve",json={"actor":"attacker","reason":"spoof"},headers=_csrf(client))
    assert spoof_decision.status_code==403
    approved=client.post(f"/api/v1/approvals/{approval_id}/approve",json={"reason":"authenticated decision"},headers=_csrf(client))
    assert approved.status_code==200
    stored=approved.json()["data"]["approval"]
    assert stored["decided_by"]=="local-owner"
    binding=stored["metadata"]["authenticated_approval_binding"]
    assert binding["actor_id"]=="local-owner"
    assert binding["secret_exposed"] is False
    assert "token" not in str(binding).lower()


def test_role_change_revokes_session_before_approval_decision(tmp_path: Path) -> None:
    client,store=_api(tmp_path);_bootstrap(client)
    body={"tool_id":"tests.run","action":"execute","subject":"role-change","reason":"security test","ttl_minutes":30}
    created=client.post("/api/v1/approvals/request",json=body,headers=_csrf(client))
    assert created.status_code==200
    approval_id=created.json()["data"]["approval"]["approval_id"]
    store.update_identity_authority("local-owner",roles=("developer",),workspace_scopes=("devpilot-local",),changed_at="2026-08-17T12:20:00Z")
    denied=client.post(f"/api/v1/approvals/{approval_id}/approve",json={"reason":"must fail"},headers=_csrf(client))
    assert denied.status_code in {401,403}


def test_executable_sensitive_action_requires_authenticated_decision_binding() -> None:
    from devpilot_core.approval.binding import ApprovalBindingRequest, StrongApprovalBindingValidator, compute_subject_hash
    record=_requested(action="filesystem.workspace_document_apply",tool_id="workspace.edit.apply")
    approved=ApprovalRecord(**{
        **record.__dict__,
        "status":"approved",
        "scope":{
            **record.scope,
            "actor_id":"local-owner",
            "role_at_decision":"owner",
            "tool_id":"workspace.edit.apply",
            "action":"filesystem.workspace_document_apply",
            "subject":record.subject,
            "subject_hash":compute_subject_hash(record.subject),
        },
    })
    result=StrongApprovalBindingValidator(ROOT).evaluate(
        approved,
        ApprovalBindingRequest(
            approval_id=approved.approval_id,
            actor_id="local-owner",
            role_at_decision="owner",
            tool_id="workspace.edit.apply",
            action="filesystem.workspace_document_apply",
            subject=approved.subject,
            subject_hash=compute_subject_hash(approved.subject),
        ),
    )
    assert result.ok is False
    ids={f.id for f in result.findings}
    assert "APPROVAL_AUTHENTICATED_DECISION_BINDING_REQUIRED" in ids
