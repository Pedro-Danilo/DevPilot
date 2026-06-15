from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.cli import main
from devpilot_core.interfaces.api import DEFAULT_ALLOWED_ORIGINS, create_app
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, API_TOKEN_ENV_VAR, API_TOKEN_HEADER

ROOT = Path(__file__).resolve().parents[1]
TEST_TOKEN = "devpilot-test-token"


def _client(*, token: str | None = TEST_TOKEN, origins: list[str] | None = None) -> TestClient:
    client = TestClient(create_app(ROOT, api_token=TEST_TOKEN, allowed_origins=origins))
    if token is not None:
        client.headers.update({API_TOKEN_HEADER: token})
    return client


def test_protected_endpoint_rejects_missing_token() -> None:
    client = _client(token=None)

    response = client.get("/api/v1/workspace/status")

    assert response.status_code == 401
    assert response.json()["contract"] == "DevPilotApplicationResponse"
    assert response.json()["ok"] is False
    assert response.json()["findings"][0]["id"] == "API_TOKEN_MISSING_BLOCK"


def test_protected_endpoint_rejects_invalid_token() -> None:
    client = _client(token="wrong-token")

    response = client.get("/api/v1/workspace/status")

    assert response.status_code == 401
    assert response.json()["findings"][0]["id"] == "API_TOKEN_INVALID_BLOCK"


def test_protected_endpoint_accepts_header_token_and_policy_binding() -> None:
    client = _client()

    response = client.get("/api/v1/workspace/status")

    assert response.status_code == 200
    assert response.headers["X-DevPilot-Policy"] == "allowed"
    assert response.headers["X-DevPilot-Api-Security"] == "token+cors+policy"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_public_health_does_not_require_token() -> None:
    client = _client(token=None)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["token_required"] is True
    assert response.json()["cors_wildcard_enabled"] is False


def test_bearer_token_is_accepted_for_protected_endpoint() -> None:
    client = TestClient(create_app(ROOT, api_token=TEST_TOKEN))

    response = client.get("/api/v1/workspace/status", headers={"Authorization": f"Bearer {TEST_TOKEN}"})

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_cors_is_restricted_and_never_wildcard_by_default() -> None:
    app = create_app(ROOT, api_token=TEST_TOKEN)
    security = app.state.api_security

    assert "*" not in security.allowed_origins
    assert security.allowed_origins == DEFAULT_ALLOWED_ORIGINS
    assert security.wildcard_cors_enabled is False

    client = _client()
    response = client.options(
        "/api/v1/workspace/status",
        headers={"Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "GET"},
    )
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert "*" not in response.headers["access-control-allow-origin"]


def test_policy_binding_covers_every_protected_route() -> None:
    app = create_app(ROOT, api_token=TEST_TOKEN)
    protected_paths = {
        (method.upper(), path)
        for path, methods in app.openapi()["paths"].items()
        for method in methods
        if path not in app.state.api_security.public_paths
    }

    assert protected_paths
    assert protected_paths.issubset(set(API_ROUTE_POLICIES))
    assert all(policy.operation for policy in API_ROUTE_POLICIES.values())


def test_api_token_command_generates_token_without_persisting_reports(capsys) -> None:
    exit_code = main(["api", "token", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "api token"
    assert payload["data"]["summary"]["token_generated"] is True
    assert payload["data"]["summary"]["persisted"] is False
    assert payload["data"]["summary"]["token_env_var"] == API_TOKEN_ENV_VAR
    assert payload["data"]["token"]
    assert payload["data"]["token"] not in payload["message"]
    assert "reports" not in payload["data"]


def test_api_serve_dry_run_reports_security_without_raw_token(monkeypatch, capsys) -> None:
    monkeypatch.setenv(API_TOKEN_ENV_VAR, TEST_TOKEN)

    exit_code = main(["api", "serve", "--host", "127.0.0.1", "--port", "8787", "--dry-run", "--json"])
    payload = json.loads(capsys.readouterr().out)
    rendered = json.dumps(payload, ensure_ascii=False)

    assert exit_code == 0
    assert payload["data"]["summary"]["api_security_implemented"] is True
    assert payload["data"]["summary"]["token_required"] is True
    assert payload["data"]["summary"]["cors_wildcard_enabled"] is False
    assert payload["data"]["summary"]["policy_binding_enabled"] is True
    assert TEST_TOKEN not in rendered


def test_api_serve_still_blocks_remote_host(capsys) -> None:
    exit_code = main(["api", "serve", "--host", "0.0.0.0", "--dry-run", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["findings"][0]["id"] == "API_HOST_NOT_LOCALHOST_BLOCK"


def test_api_serve_execute_requires_explicit_token(monkeypatch, capsys) -> None:
    monkeypatch.delenv(API_TOKEN_ENV_VAR, raising=False)

    exit_code = main(["api", "serve", "--host", "127.0.0.1", "--execute", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["findings"][0]["id"] == "API_EXECUTE_REQUIRES_EXPLICIT_TOKEN_BLOCK"
    assert payload["data"]["summary"]["server_started"] is False
