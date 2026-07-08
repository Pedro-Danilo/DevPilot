from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.interfaces.api import API_TOKEN_HEADER, create_app, sanitize_allowed_origins, validate_api_bind_host
from devpilot_core.interfaces.api.security import API_REMOTE_BIND_OVERRIDE_ENV_VAR, SECURITY_HEADERS
from devpilot_core.interfaces.api.security_hardening import LocalApiSecurityHardeningOptions, LocalApiSecurityHardeningRunner
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "post-h-028-b-test-token"
LOCAL_ORIGIN = "http://127.0.0.1:5173"
NON_LOCAL_ORIGIN = "http://evil.example"


def _client(*, token: str | None = TOKEN, origins: list[str] | None = None) -> TestClient:
    client = TestClient(create_app(ROOT, api_token=TOKEN, allowed_origins=origins or [LOCAL_ORIGIN]))
    if token is not None:
        client.headers.update({API_TOKEN_HEADER: token})
    return client


def test_local_api_security_hardening_runner_passes_and_redacts_token() -> None:
    result = LocalApiSecurityHardeningRunner(ROOT, LocalApiSecurityHardeningOptions(token=TOKEN)).run()

    rendered = json.dumps(result.to_dict(), ensure_ascii=False)
    summary = result.data["summary"]
    report = result.data["report"]

    assert result.ok is True
    assert int(result.exit_code) == 0
    assert summary["decision"] == "PASS"
    assert summary["local_api_security_hardening_passed"] is True
    assert summary["protected_without_token_blocked"] is True
    assert summary["protected_invalid_token_blocked"] is True
    assert summary["protected_valid_token_passed"] is True
    assert summary["cors_wildcard_enabled"] is False
    assert summary["local_origin_allowed"] is True
    assert summary["non_local_origin_rejected"] is True
    assert summary["non_local_bind_allowed"] is False
    assert summary["remote_bind_override_enabled"] is False
    assert summary["security_headers_present"] is True
    assert summary["settings_secrets_redacted"] is True
    assert summary["token_redacted_in_report"] is True
    assert summary["report_schema_valid"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["source_mutations_performed"] is False
    assert TOKEN not in rendered
    assert report["schema_id"] == "SCHEMA-DEVPL-LOCAL-API-SECURITY-HARDENING-REPORT-V1"


def test_local_api_security_hardening_writes_schema_valid_report(tmp_path: Path) -> None:
    json_path = tmp_path / "local_api_security_hardening_report.json"
    md_path = tmp_path / "local_api_security_hardening_report.md"
    result = LocalApiSecurityHardeningRunner(
        ROOT,
        LocalApiSecurityHardeningOptions(token=TOKEN, write_report=True, output_json=json_path, output_markdown=md_path),
    ).run()

    assert result.ok is True
    assert json_path.exists()
    assert md_path.exists()
    assert TOKEN not in json_path.read_text(encoding="utf-8")
    schema = SchemaValidator(ROOT).validate(schema="LocalApiSecurityHardeningReport", instance=json_path)
    assert schema.ok is True, schema.to_dict()


def test_protected_route_rejects_missing_and_invalid_token_but_accepts_valid_token() -> None:
    missing = _client(token=None).get("/api/v1/security/posture", headers={"Origin": LOCAL_ORIGIN})
    invalid = _client(token="wrong").get("/api/v1/security/posture", headers={"Origin": LOCAL_ORIGIN})
    valid = _client().get("/api/v1/security/posture", headers={"Origin": LOCAL_ORIGIN})

    assert missing.status_code == 401
    assert missing.json()["findings"][0]["id"] == "API_TOKEN_MISSING_BLOCK"
    assert invalid.status_code == 401
    assert invalid.json()["findings"][0]["id"] == "API_TOKEN_INVALID_BLOCK"
    assert valid.status_code == 200
    assert valid.json()["ok"] is True
    assert TOKEN not in valid.text


def test_cors_local_origin_allowed_and_non_local_origin_rejected() -> None:
    sanitized = sanitize_allowed_origins(["*", NON_LOCAL_ORIGIN, LOCAL_ORIGIN, "http://localhost:8787"])

    assert "*" not in sanitized
    assert NON_LOCAL_ORIGIN not in sanitized
    assert LOCAL_ORIGIN in sanitized

    local_error = _client(token="wrong", origins=list(sanitized)).get("/api/v1/security/posture", headers={"Origin": LOCAL_ORIGIN})
    evil_error = _client(token="wrong", origins=list(sanitized)).get("/api/v1/security/posture", headers={"Origin": NON_LOCAL_ORIGIN})
    evil_headers = {key.lower(): value for key, value in evil_error.headers.items()}

    assert local_error.headers.get("Access-Control-Allow-Origin") == LOCAL_ORIGIN
    assert "access-control-allow-origin" not in evil_headers


def test_non_local_bind_remains_blocked_even_when_future_override_is_present() -> None:
    result = validate_api_bind_host(host="0.0.0.0", port=8787, env={API_REMOTE_BIND_OVERRIDE_ENV_VAR: "1"})

    assert result.ok is False
    assert int(result.exit_code) == 2
    summary = result.data["summary"]
    assert summary["remote_bind_override_requested"] is True
    assert summary["remote_bind_override_enabled"] is False
    assert summary["remote_bind_override_status"] == "future_disabled_by_design"
    assert summary["non_local_bind_allowed"] is False


def test_security_headers_present_on_success_and_auth_error() -> None:
    success = _client().get("/api/v1/security/posture", headers={"Origin": LOCAL_ORIGIN})
    error = _client(token="wrong").get("/api/v1/security/posture", headers={"Origin": LOCAL_ORIGIN})

    for response in [success, error]:
        for header, value in SECURITY_HEADERS.items():
            assert response.headers.get(header) == value
        assert response.headers["X-DevPilot-Api-Security"] == "token+cors+policy"


def test_settings_providers_response_remains_redacted_and_plan_only() -> None:
    response = _client().get("/api/v1/settings/providers", headers={"Origin": LOCAL_ORIGIN})

    assert response.status_code == 200, response.text
    text = response.text
    assert TOKEN not in text
    assert "sk-proj-" not in text
    assert "github_pat_" not in text
    assert "Bearer " not in text
    payload = response.json()
    summary = payload["data"]["summary"]
    assert summary["secrets_redacted"] is True
    assert summary["write_enabled"] is False
    assert summary["plan_only"] is True
    assert summary["external_api_enabled_total"] == 0


def test_post_h_028_b_docs_and_tcr_are_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-028_ui_api_local_hardening.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    interface_doc = (ROOT / "docs/07_interfaces/ui_api_industrial_shell.md").read_text(encoding="utf-8")
    schema_catalog = (ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8")
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")

    assert 'current_micro_sprint: "POST-H-028-B"' in backlog
    assert 'next_micro_sprint: "POST-H-028-C"' in backlog
    assert "POST-H-028-B" in readme
    assert "api security-hardening" in runbook
    assert "Local auth and CORS hardening" in interface_doc
    assert "SCHEMA-DEVPL-LOCAL-API-SECURITY-HARDENING-REPORT-V1" in schema_catalog
    assert "post-h-028-local-auth-cors-hardening" in tcr_v1
    assert "post-h-028-local-auth-cors-hardening" in tcr_v2
