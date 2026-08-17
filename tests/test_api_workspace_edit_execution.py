from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from devpilot_core.application.workspace_documents_service import WorkspaceDocumentsApplicationService
from devpilot_core.application import AuthApplicationService
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.identity.auth_models import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from devpilot_core.interfaces.api import create_app
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, API_TOKEN_HEADER
from uoc004_fixtures import create_uoc004_workspace, sha

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "uoc005-test-token"


def setup_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    platform = ROOT
    db = platform / ".devpilot/devpilot.db"
    if db.exists(): db.unlink()
    ws = create_uoc004_workspace(tmp_path / "inventory-sales-local")
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(["git", "config", "user.email", "uoc005@example.invalid"], cwd=ws, check=True)
    subprocess.run(["git", "config", "user.name", "UOC005 Fixture"], cwd=ws, check=True)
    subprocess.run(["git", "add", "."], cwd=ws, check=True); subprocess.run(["git", "commit", "-qm", "baseline"], cwd=ws, check=True)
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(ws)); monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(ws)); monkeypatch.setenv("DEVPILOT_UOC005_CONTROL_ROOT", str(tmp_path / "control"))
    auth_store=LocalAuthStore(platform, db_relative_path=f"outputs/tmp/gsdlc02c-edit-auth-{uuid.uuid4().hex}/auth.db")
    client = TestClient(create_app(platform, api_token=TOKEN, auth_service=AuthApplicationService(platform, store=auth_store))); client.headers.update({API_TOKEN_HEADER: TOKEN})
    docs = WorkspaceDocumentsApplicationService(platform); listing = docs.list_documents(limit=100)
    ids = {n["relative_path"]: n["document_id"] for n in listing.data["nodes"] if n.get("kind") == "document"}
    return client, ws, ids


def test_api_approval_apply_and_rollback_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    client, ws, ids = setup_client(tmp_path, monkeypatch); path = ws / "docs/00_product/product_vision.md"; base = sha(path)
    plan_res = client.post("/api/v1/workspace/edit-plans/plan", json={"operation":"workspace.edits.plan","payload":{"document_id":ids["docs/00_product/product_vision.md"],"document_sha_before":base,"proposed_content":path.read_text()+"\nUOC005 API change\n"},"dry_run":True})
    assert plan_res.status_code == 200, plan_res.text; plan = plan_res.json()["data"]["plan"]
    denied = client.post(f"/api/v1/workspace/edit-plans/{plan['plan_id']}/apply", json={"plan_hash":plan["plan_hash"],"approval_id":"missing","actor":"local-owner"})
    assert denied.status_code in {400,401,403}, denied.text; assert sha(path) == base
    boot=client.post("/api/v1/auth/bootstrap/owner",json={"username":"owner.local","display_name":"Local Owner","password":"correct horse battery staple"},headers={"Origin":"http://127.0.0.1:5173"}); assert boot.status_code==201,boot.text
    csrf=client.cookies.get(CSRF_COOKIE_NAME); secured={CSRF_HEADER_NAME:csrf,"Origin":"http://127.0.0.1:5173"}
    req = client.post(f"/api/v1/workspace/edit-plans/{plan['plan_id']}/approval-request", headers=secured, json={"plan_hash":plan["plan_hash"],"reason":"Review API apply","ttl_minutes":15})
    assert req.status_code == 200, req.text; approval = req.json()["data"]["approval"]["approval_id"]
    approve = client.post(f"/api/v1/approvals/{approval}/approve", headers=secured, json={"reason":"Approved in API fixture"}); assert approve.status_code == 200, approve.text
    applied = client.post(f"/api/v1/workspace/edit-plans/{plan['plan_id']}/apply", headers=secured, json={"plan_hash":plan["plan_hash"],"approval_id":approval})
    assert applied.status_code == 200, applied.text; execution = applied.json()["data"]["execution"]
    assert sha(path) == plan["document"]["proposed_sha256"]
    status = client.get(f"/api/v1/workspace/edit-executions/{execution['execution_id']}"); assert status.status_code == 200
    rr = client.post(f"/api/v1/workspace/edit-executions/{execution['execution_id']}/rollback-approval-request", headers=secured, json={"reason":"Restore API fixture","ttl_minutes":15})
    assert rr.status_code == 200, rr.text; rb_approval = rr.json()["data"]["approval"]["approval_id"]
    assert client.post(f"/api/v1/approvals/{rb_approval}/approve", headers=secured, json={"reason":"Approved rollback"}).status_code == 200
    rolled = client.post(f"/api/v1/workspace/edit-executions/{execution['execution_id']}/rollback", headers=secured, json={"approval_id":rb_approval})
    assert rolled.status_code == 200, rolled.text; assert sha(path) == base


def test_uoc005_routes_have_explicit_security_bindings():
    required = {
        ("POST","/api/v1/workspace/edit-plans/{plan_id}/approval-request"),
        ("POST","/api/v1/workspace/edit-plans/{plan_id}/apply"),
        ("GET","/api/v1/workspace/edit-executions/{execution_id}"),
        ("POST","/api/v1/workspace/edit-executions/{execution_id}/rollback-approval-request"),
        ("POST","/api/v1/workspace/edit-executions/{execution_id}/rollback"),
    }
    assert required <= set(API_ROUTE_POLICIES)
