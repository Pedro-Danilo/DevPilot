from __future__ import annotations

from pathlib import Path
import json

from fastapi.testclient import TestClient

from devpilot_core.interfaces.api.app import create_app
from devpilot_core.identity.auth_models import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, SESSION_COOKIE_NAME


def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(tmp_path, api_token="legacy-test-token"), base_url="http://127.0.0.1:8787")


def bootstrap(c: TestClient):
    r=c.post("/api/v1/auth/bootstrap/owner",json={"username":"owner.local","display_name":"Local Owner","password":"correct horse battery staple"},headers={"Origin":"http://127.0.0.1:5173"})
    assert r.status_code==201, r.text
    assert SESSION_COOKIE_NAME in c.cookies
    assert CSRF_COOKIE_NAME in c.cookies
    assert "csrf_token" not in r.text and "correct horse" not in r.text
    return r


def test_bootstrap_status_and_duplicate_bootstrap(tmp_path: Path) -> None:
    c=client(tmp_path)
    assert c.get("/api/v1/auth/bootstrap/status").json()["first_run_required"] is True
    bootstrap(c)
    assert c.get("/api/v1/auth/bootstrap/status").json()["first_run_required"] is False
    r=c.post("/api/v1/auth/bootstrap/owner",json={"username":"other","display_name":"Other","password":"another correct local password"})
    assert r.status_code==409


def test_login_sets_httponly_strict_session_cookie_without_secret_body(tmp_path: Path) -> None:
    c=client(tmp_path); bootstrap(c)
    c.cookies.clear()
    r=c.post("/api/v1/auth/login",json={"username":"owner.local","password":"correct horse battery staple"})
    assert r.status_code==200
    cookie="\n".join(r.headers.get_list("set-cookie"))
    assert "devpilot_session=" in cookie and "HttpOnly" in cookie and "SameSite=strict" in cookie
    assert "correct horse" not in r.text and "csrf_token" not in r.text


def test_invalid_login_and_session_inspect(tmp_path: Path) -> None:
    c=client(tmp_path); bootstrap(c); c.cookies.clear()
    bad=c.post("/api/v1/auth/login",json={"username":"owner.local","password":"bad credentials x"})
    assert bad.status_code==401
    assert c.get("/api/v1/auth/session").status_code==401
    good=c.post("/api/v1/auth/login",json={"username":"owner.local","password":"correct horse battery staple"})
    assert good.status_code==200
    session=c.get("/api/v1/auth/session")
    assert session.status_code==200
    assert session.json()["session"]["principal"]["actor_id"]=="local-owner"
    assert session.json()["session"]["principal"]["auth_method"]=="human-session"


def test_session_mutation_requires_csrf_and_local_origin(tmp_path: Path) -> None:
    c=client(tmp_path); bootstrap(c)
    assert c.post("/api/v1/auth/session/rotate").status_code==403
    csrf=c.cookies.get(CSRF_COOKIE_NAME)
    assert c.post("/api/v1/auth/session/rotate",headers={CSRF_HEADER_NAME:csrf,"Origin":"https://evil.example"}).status_code==403
    ok=c.post("/api/v1/auth/session/rotate",headers={CSRF_HEADER_NAME:csrf,"Origin":"http://127.0.0.1:5173"})
    assert ok.status_code==200


def test_legacy_token_can_read_compatibility_route_but_cannot_approve(tmp_path: Path) -> None:
    c=client(tmp_path)
    # Legacy token remains bounded compatibility for protected reads.
    health=c.get("/api/v1/security/posture",headers={"X-DevPilot-Token":"legacy-test-token"})
    assert health.status_code==200
    # Human approval decision endpoints are already marked human-session-required.
    r=c.post("/api/v1/approvals/fake/approve",headers={"X-DevPilot-Token":"legacy-test-token"},json={"actor":"spoof","reason":"x"})
    assert r.status_code==401
    assert r.json()["findings"][0]["id"]=="AUTH_HUMAN_SESSION_REQUIRED_BLOCK"


def test_logout_revokes_and_clears_cookie(tmp_path: Path) -> None:
    c=client(tmp_path); bootstrap(c); csrf=c.cookies.get(CSRF_COOKIE_NAME)
    r=c.post("/api/v1/auth/logout",headers={CSRF_HEADER_NAME:csrf,"Origin":"http://127.0.0.1:5173"})
    assert r.status_code==200
    assert c.get("/api/v1/auth/session").status_code==401


def test_public_login_rejects_non_local_browser_origin(tmp_path: Path) -> None:
    c=client(tmp_path); bootstrap(c)
    r=c.post(
        "/api/v1/auth/login",
        json={"username":"owner.local","password":"correct horse battery staple"},
        headers={"Origin":"https://attacker.example"},
    )
    assert r.status_code==403
    assert "AUTH_PUBLIC_ORIGIN_BLOCK" in json.dumps(r.json())


def test_public_login_allows_local_browser_origin(tmp_path: Path) -> None:
    c=client(tmp_path); bootstrap(c)
    r=c.post(
        "/api/v1/auth/login",
        json={"username":"owner.local","password":"correct horse battery staple"},
        headers={"Origin":"http://127.0.0.1:5173"},
    )
    assert r.status_code==200
    assert r.json()["ok"] is True
