from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.interfaces.api import create_app
from devpilot_core.interfaces.api.security import API_TOKEN_HEADER, API_ROUTE_POLICIES
from devpilot_core.observability.trace_store import TraceStore

ROOT = Path(__file__).resolve().parents[1]
TEST_TOKEN = "devpilot-test-token"


def _client() -> TestClient:
    client = TestClient(create_app(ROOT, api_token=TEST_TOKEN))
    client.headers.update({API_TOKEN_HEADER: TEST_TOKEN})
    return client


def _write_sample_report(report_id: str = "sprint70-sample") -> None:
    reports = ROOT / "outputs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    payload = {
        "report_id": report_id,
        "command": "pytest sample",
        "status": "PASS",
        "ok": True,
        "exit_code": 0,
        "message": "sample report token should be redacted",
        "generated_at": "2026-06-16T00:00:00Z",
        "summary": {"token": "secret-token", "checks_total": 1},
        "findings": [{"id": "SAMPLE_WARNING", "message": "warn", "severity": "warning"}],
    }
    (reports / f"{report_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (reports / f"{report_id}.md").write_text("# sample\n\nsecret-token\n", encoding="utf-8")


def test_reports_endpoint_lists_reports_without_exposing_secrets() -> None:
    _write_sample_report()
    response = _client().get("/api/v1/reports?severity=warning")
    payload = response.json()
    rendered = json.dumps(payload, ensure_ascii=False)

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["operation"] == "reports.list"
    assert payload["data"]["summary"]["filesystem_access"] == "api_service_only_outputs_reports"
    assert payload["data"]["reports"]
    assert "secret-token" not in rendered


def test_report_detail_endpoint_blocks_path_traversal_and_reads_safe_report() -> None:
    _write_sample_report("sprint70-detail")
    client = _client()

    ok = client.get("/api/v1/reports/sprint70-detail?format=json")
    blocked = client.get("/api/v1/reports/..%2F.env?format=json")

    assert ok.status_code == 200
    assert ok.json()["data"]["summary"]["redacted"] is True
    assert blocked.status_code == 403
    assert blocked.json()["findings"][0]["id"] in {"REPORT_ID_INVALID_BLOCK", "API_POLICY_BINDING_MISSING_BLOCK"}


def test_trace_and_metrics_endpoints_handle_empty_or_present_data() -> None:
    TraceStore(ROOT).initialize()
    TraceStore(ROOT).record_smoke_trace(command="sprint70 api smoke")
    client = _client()

    traces = client.get("/api/v1/traces?limit=10")
    metrics = client.get("/api/v1/metrics/summary")

    assert traces.status_code == 200
    assert traces.json()["ok"] is True
    assert traces.json()["data"]["summary"]["limit"] == 10
    assert metrics.status_code == 200
    assert metrics.json()["ok"] is True


def test_trace_detail_endpoint_returns_tree_for_existing_trace() -> None:
    smoke = TraceStore(ROOT).record_smoke_trace(command="sprint70 inspect smoke")
    trace_id = smoke["trace_context"]["trace_id"]

    response = _client().get(f"/api/v1/traces/{trace_id}")
    payload = response.json()

    assert response.status_code == 200
    assert payload["operation"] == "observability.trace_inspect"
    assert payload["data"]["summary"]["found"] is True
    assert payload["data"]["tree"]


def test_policy_binding_covers_sprint70_routes() -> None:
    expected = {
        ("GET", "/api/v1/reports"),
        ("GET", "/api/v1/reports/{report_id}"),
        ("GET", "/api/v1/traces"),
        ("GET", "/api/v1/traces/{trace_id}"),
        ("GET", "/api/v1/metrics/summary"),
    }
    assert expected.issubset(set(API_ROUTE_POLICIES))
