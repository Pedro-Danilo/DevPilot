from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.interfaces.api import create_app

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "test-token-settings"


_CLIENT = TestClient(create_app(ROOT, api_token=TOKEN))


def _client() -> TestClient:
    return _CLIENT


def _headers() -> dict[str, str]:
    return {"X-DevPilot-Token": TOKEN, "Origin": "http://127.0.0.1:5173"}


def test_settings_workspace_providers_and_policy_are_read_only() -> None:
    client = _client()

    for path in ["/api/v1/settings/workspace", "/api/v1/settings/providers", "/api/v1/settings/policy"]:
        response = client.get(path, headers=_headers())
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["contract"] == "DevPilotApplicationResponse"
        assert payload["ok"] is True
        assert payload["data"]["summary"]["write_enabled"] is False
        assert payload["data"]["summary"]["plan_only"] is True
        assert payload["data"]["summary"]["secrets_redacted"] is True


def test_settings_providers_do_not_expose_raw_secret_values() -> None:
    client = _client()
    response = client.get("/api/v1/settings/providers", headers=_headers())
    assert response.status_code == 200
    text = response.text
    assert "sk-proj-" not in text
    assert "github_pat_" not in text
    assert "Bearer " not in text
    assert "OPENAI_API_KEY" in text  # env var names are allowed; raw key values are not.
    payload = response.json()
    summary = payload["data"]["summary"]
    assert summary["external_api_enabled_total"] == 0


def test_provider_plan_is_plan_only_and_does_not_write_providers_file() -> None:
    client = _client()
    provider_file = ROOT / ".devpilot" / "providers.yaml"
    before = provider_file.read_text(encoding="utf-8") if provider_file.exists() else ""
    response = client.post(
        "/api/v1/settings/providers/plan",
        headers=_headers(),
        json={"provider_id": "ollama", "changes": {"enabled": True, "endpoint": "http://localhost:11434"}, "actor": "pytest", "reason": "settings plan test"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["summary"]["write_performed"] is False
    assert payload["data"]["summary"]["plan_only"] is True
    after = provider_file.read_text(encoding="utf-8") if provider_file.exists() else ""
    assert after == before


def test_provider_plan_blocks_external_api_enable() -> None:
    client = _client()
    response = client.post(
        "/api/v1/settings/providers/plan",
        headers=_headers(),
        json={"provider_id": "openai", "changes": {"enabled": True}, "actor": "pytest", "reason": "should block"},
    )
    assert response.status_code == 403
    payload = response.json()
    assert payload["ok"] is False
    assert any(finding["id"] == "SETTINGS_PROVIDER_EXTERNAL_ENABLE_BLOCK" for finding in payload["findings"])


def test_settings_routes_are_protected_by_token_and_policy() -> None:
    client = _client()
    response = client.get("/api/v1/settings/workspace", headers={"Origin": "http://127.0.0.1:5173"})
    assert response.status_code == 401
    assert response.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:5173"


def test_provider_plan_validates_synthetic_local_proposal_and_records_duration() -> None:
    client = _client()
    response = client.post(
        "/api/v1/settings/providers/plan",
        headers=_headers(),
        json={
            "provider_id": "ollama",
            "changes": {"enabled": True, "default_model": "qwen2.5:3b-instruct", "endpoint": "http://127.0.0.1:11434"},
            "actor": "pytest",
            "reason": "synthetic proposal",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    summary = payload["data"]["summary"]
    plan = payload["data"]["plan"]
    assert summary["validation_target"] == "synthetic-proposal"
    assert summary["duration_ms"] >= 0
    assert plan["proposed_preview"]["endpoint"] == "http://127.0.0.1:11434"
    assert "validate-synthetic-provider-configs" in plan["validation_steps"]
    assert plan["write_performed"] is False


def test_provider_plan_blocks_nonlocal_endpoint_in_synthetic_proposal() -> None:
    client = _client()
    response = client.post(
        "/api/v1/settings/providers/plan",
        headers=_headers(),
        json={"provider_id": "ollama", "changes": {"endpoint": "https://models.example.com"}},
    )
    assert response.status_code == 403, response.text
    payload = response.json()
    assert any(finding["id"] == "MODEL_PROVIDER_LOCAL_ENDPOINT_NOT_LOCAL_BLOCKED" for finding in payload["findings"])
    assert payload["data"]["summary"]["write_performed"] is False


def test_provider_plan_blocks_secret_like_proposal_and_redacts_response() -> None:
    client = _client()
    secret = "sk-" + "proj-" + "never-persist-this-value"
    response = client.post(
        "/api/v1/settings/providers/plan",
        headers=_headers(),
        json={"provider_id": "ollama", "changes": {"endpoint": f"http://localhost:11434?token={secret}"}},
    )
    assert response.status_code == 403, response.text
    assert secret not in response.text
    payload = response.json()
    assert any(finding["id"] in {"SETTINGS_PROVIDER_PLAN_SECRET_BLOCK", "MODEL_PROVIDER_RAW_SECRET_BLOCKED"} for finding in payload["findings"])


def test_provider_plan_warns_and_ignores_unsupported_fields() -> None:
    client = _client()
    response = client.post(
        "/api/v1/settings/providers/plan",
        headers=_headers(),
        json={"provider_id": "ollama", "changes": {"description": "not mutable"}},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert any(finding["id"] == "SETTINGS_PROVIDER_PLAN_UNSUPPORTED_FIELD_WARNING" for finding in payload["findings"])
    assert payload["data"]["plan"]["unsupported_fields"] == ["description"]


def test_provider_plan_blocks_unknown_provider_without_writing() -> None:
    client = _client()
    provider_file = ROOT / ".devpilot" / "providers.yaml"
    before = provider_file.read_bytes() if provider_file.exists() else b""
    response = client.post(
        "/api/v1/settings/providers/plan",
        headers=_headers(),
        json={"provider_id": "missing-provider", "changes": {"enabled": True}},
    )
    assert response.status_code == 403
    assert any(finding["id"] == "SETTINGS_PROVIDER_NOT_FOUND_BLOCK" for finding in response.json()["findings"])
    after = provider_file.read_bytes() if provider_file.exists() else b""
    assert after == before
