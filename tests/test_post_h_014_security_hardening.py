from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.cli import main
from devpilot_core.interfaces.api import API_TOKEN_HEADER, DEFAULT_ALLOWED_ORIGINS, create_app, sanitize_allowed_origins, validate_api_bind_host
from devpilot_core.interfaces.api.security import API_REMOTE_BIND_OVERRIDE_ENV_VAR, SECURITY_HEADERS

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "post-h-014-d-test-token"


def _client(*, token: str | None = TOKEN, origins: list[str] | None = None) -> TestClient:
    client = TestClient(create_app(ROOT, api_token=TOKEN, allowed_origins=origins))
    if token is not None:
        client.headers.update({API_TOKEN_HEADER: token})
    return client


def test_post_h_014_d_security_posture_endpoint_requires_token() -> None:
    response = _client(token=None).get("/api/v1/security/posture", headers={"Origin": "http://127.0.0.1:5173"})

    assert response.status_code == 401
    assert response.json()["contract"] == "DevPilotApplicationResponse"
    assert response.json()["findings"][0]["id"] == "API_TOKEN_MISSING_BLOCK"
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_post_h_014_d_security_posture_is_redacted_and_local_only() -> None:
    response = _client().get("/api/v1/security/posture", headers={"Origin": "http://127.0.0.1:5173"})

    assert response.status_code == 200, response.text
    payload = response.json()
    rendered = json.dumps(payload, ensure_ascii=False)
    summary = payload["data"]["summary"]
    assert payload["contract"] == "DevPilotApplicationResponse"
    assert payload["operation"] == "api.security.posture"
    assert summary["created_by"] == "POST-H-014-D"
    assert summary["token_required"] is True
    assert summary["token_redacted"] != TOKEN
    assert TOKEN not in rendered
    assert summary["cors_wildcard_enabled"] is False
    assert summary["non_local_bind_allowed"] is False
    assert summary["remote_bind_override_status"] == "future_disabled_by_design"
    assert summary["settings_secrets_redacted"] is True
    assert summary["secrets_in_api_responses_allowed"] is False
    assert summary["remote_execution_enabled"] is False
    assert summary["connector_write_enabled"] is False
    assert summary["plugin_execution_enabled"] is False
    assert "X-Content-Type-Options" in summary["security_headers"]


def test_post_h_014_d_cors_sanitizer_rejects_wildcard_and_non_local_origins() -> None:
    sanitized = sanitize_allowed_origins(["*", "http://evil.example", "http://127.0.0.1:5173", "http://localhost:8787"])

    assert sanitized == ("http://127.0.0.1:5173", "http://localhost:8787")
    assert "*" not in sanitized

    fallback = sanitize_allowed_origins(["*", "https://evil.example"])
    assert fallback == DEFAULT_ALLOWED_ORIGINS


def test_post_h_014_d_create_app_does_not_enable_wildcard_cors_even_if_requested() -> None:
    app = create_app(ROOT, api_token=TOKEN, allowed_origins=["*", "http://evil.example", "http://127.0.0.1:5173"])
    summary = app.state.api_security.to_safe_summary()

    assert summary["allowed_origins"] == ["http://127.0.0.1:5173"]
    assert summary["cors_wildcard_enabled"] is False

    response = TestClient(app).options(
        "/api/v1/security/posture",
        headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in {key.lower(): value for key, value in response.headers.items()}


def test_post_h_014_d_security_headers_are_applied_to_success_and_error_responses() -> None:
    client = _client()
    success = client.get("/api/v1/security/posture", headers={"Origin": "http://127.0.0.1:5173"})
    error = _client(token="wrong").get("/api/v1/security/posture", headers={"Origin": "http://127.0.0.1:5173"})

    for response in [success, error]:
        for header in SECURITY_HEADERS:
            assert response.headers.get(header) == SECURITY_HEADERS[header]
        assert response.headers["X-DevPilot-Api-Security"] == "token+cors+policy"


def test_post_h_014_d_non_local_bind_remains_blocked_even_with_future_override(monkeypatch) -> None:
    monkeypatch.setenv(API_REMOTE_BIND_OVERRIDE_ENV_VAR, "1")

    result = validate_api_bind_host(host="0.0.0.0", port=8787)

    assert result.ok is False
    assert int(result.exit_code) == 2
    summary = result.data["summary"]
    assert summary["remote_bind_override_requested"] is True
    assert summary["remote_bind_override_enabled"] is False
    assert summary["remote_bind_override_status"] == "future_disabled_by_design"
    assert result.findings[0].id == "API_HOST_NOT_LOCALHOST_BLOCK"


def test_post_h_014_d_api_serve_dry_run_reports_posture_without_raw_token(monkeypatch, capsys) -> None:
    monkeypatch.setenv("DEVPILOT_API_TOKEN", TOKEN)

    exit_code = main(["api", "serve", "--host", "127.0.0.1", "--port", "8787", "--dry-run", "--json"])
    payload = json.loads(capsys.readouterr().out)
    rendered = json.dumps(payload, ensure_ascii=False)

    assert exit_code == 0
    assert TOKEN not in rendered
    summary = payload["data"]["summary"]
    assert summary["api_security_implemented"] is True
    assert summary["security_posture_endpoint"] == "/api/v1/security/posture"
    assert summary["non_local_bind_allowed"] is False
    assert summary["cors_wildcard_enabled"] is False
    assert summary["settings_secrets_redacted"] is True


def test_post_h_014_d_contract_docs_and_tcr_are_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-014_ui_api_industrial_shell.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    interface_doc = (ROOT / "docs/07_interfaces/ui_api_industrial_shell.md").read_text(encoding="utf-8")
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")

    assert 'current_micro_sprint: "POST-H-014-E"' in backlog
    assert 'next_micro_sprint: "POST-H-015"' in backlog
    assert "POST-H-014-D — Security hardening local de API/UI" in readme
    assert "POST-H-014-D — Security hardening local de API/UI" in runbook
    assert "security posture" in interface_doc.lower()
    assert "post-h-014-security-hardening" in tcr_v1
    assert "post-h-014-security-hardening" in tcr_v2
