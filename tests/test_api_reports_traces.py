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


def _external_workspace_registry(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    workspace = (tmp_path / "DevPilot_Workspaces" / "inventory-sales-local").resolve()
    registry_path = workspace / ".devpilot" / "onboarding" / "workspace_registry.local.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    (workspace / "outputs" / "reports" / "post_h_eval_002_02_a").mkdir(parents=True, exist_ok=True)
    (workspace / "outputs" / "traces").mkdir(parents=True, exist_ok=True)
    (workspace / ".devpilot" / "project.yaml").write_text(
        '\n'.join(
            [
                'schema_version: "1.0"',
                'project:',
                '  id: "inventory-sales-local"',
                '  name: "Sistema local de ventas e inventario"',
                '  type: "agent-assisted-sdlc"',
                '  owner: "local-owner"',
                'standards:',
                '  - "MIPSoftware"',
                '  - "MIASI"',
                'miasi:',
                '  required: true',
                'paths:',
                '  docs: "docs"',
                '  reports: "outputs/reports"',
                '  traces: "outputs/traces"',
                '  state: ".devpilot/devpilot.db"',
                'runtime:',
                '  dry_run_default: true',
                '  created_by: "POST-H-EVAL-002-02-A"',
                '  overwrite_policy: "refuse_by_default"',
                '',
            ]
        ),
        encoding="utf-8",
    )
    payload = {
        "schema_version": "1.0",
        "created_by": "FUNC-SPRINT-94",
        "updated_at": "2026-08-03T10:06:45-05:00",
        "active_workspace_id": "inventory-sales-local",
        "defaults": {
            "deny_unregistered_workspaces": True,
            "cross_workspace_state_reads": False,
            "secret_sharing_allowed": False,
            "portfolio_status_read_only": True,
        },
        "security": {
            "network_used": False,
            "external_api_used": False,
            "shell_used": False,
            "remote_execution_used": False,
            "mutations_performed": False,
            "secrets_read": False,
        },
        "workspaces": [
            {
                "workspace_id": "inventory-sales-local",
                "project_id": "inventory-sales-local",
                "name": "Sistema local de ventas e inventario",
                "path": workspace.as_posix(),
                "path_mode": "absolute-local",
                "status": "active",
                "risk_level": "medium_high",
                "default_effect": "deny",
                "state_path": ".devpilot/devpilot.db",
                "reports_path": "outputs/reports",
                "traces_path": "outputs/traces",
                "secrets_path": ".devpilot/providers.yaml",
                "secret_policy": "reference-only",
                "network_allowed": False,
                "external_api_allowed": False,
                "observability_required": True,
                "eval_required": True,
                "registered_at": "2026-08-03T10:06:45-05:00",
                "updated_at": "2026-08-03T10:06:45-05:00",
            }
        ],
    }
    registry_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(workspace))
    monkeypatch.setenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", str(registry_path))
    return workspace, registry_path


def test_reports_endpoint_discovers_and_reads_nested_report() -> None:
    reports = ROOT / "outputs" / "reports" / "post_h_eval_002_02_a"
    reports.mkdir(parents=True, exist_ok=True)
    report_json = reports / "bootstrap_dry_run.json"
    report_md = reports / "bootstrap_dry_run.md"
    report_json.write_text(
        json.dumps(
            {
                "operation": "workspace.bootstrap",
                "status": "PASS",
                "ok": True,
                "summary": {"mode": "dry-run", "mutations_performed": False},
                "findings": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report_md.write_text("# Bootstrap dry-run\n\nmutations_performed=false\n", encoding="utf-8")

    client = _client()
    listed = client.get("/api/v1/reports?scope=platform&query=bootstrap_dry_run")
    payload = listed.json()

    assert listed.status_code == 200
    assert payload["ok"] is True
    item = next(report for report in payload["data"]["reports"] if report["relative_path"] == "post_h_eval_002_02_a/bootstrap_dry_run")
    assert item["nested"] is True
    assert set(item["formats"]) == {"json", "markdown"}
    assert item["report_id"].startswith("rpt_")

    detail = client.get(f"/api/v1/reports/{item['report_id']}?format=json")
    assert detail.status_code == 200
    assert detail.json()["data"]["report"]["summary"]["mutations_performed"] is False


def test_reports_default_page_parses_only_returned_json_summaries(tmp_path: Path) -> None:
    from devpilot_core.application.reports_service import ReportsApplicationService

    reports = tmp_path / "outputs" / "reports"
    reports.mkdir(parents=True)
    for index in range(120):
        (reports / f"report-{index:03d}.json").write_text(
            json.dumps({"status": "PASS", "ok": True, "summary": {"index": index}}),
            encoding="utf-8",
        )

    result = ReportsApplicationService(tmp_path).list_reports(limit=7)

    assert result.ok is True
    assert result.data["summary"]["reports_total"] == 120
    assert result.data["summary"]["returned_total"] == 7
    assert result.data["summary"]["json_summaries_parsed_total"] == 7
    assert result.data["summary"]["recursive_discovery"] is True


def test_ui_context_surfaces_external_workspace_reports_settings_portfolio_and_traces(tmp_path: Path, monkeypatch) -> None:
    workspace, _ = _external_workspace_registry(tmp_path, monkeypatch)
    report = workspace / "outputs" / "reports" / "post_h_eval_002_02_a" / "bootstrap_dry_run.json"
    report.write_text(json.dumps({"status": "PASS", "ok": True, "summary": {"mutations_performed": False}}), encoding="utf-8")
    TraceStore(workspace).initialize()
    TraceStore(workspace).record_smoke_trace(command="inventory workspace smoke")

    client = _client()
    reports = client.get("/api/v1/reports?scope=workspace&query=bootstrap_dry_run")
    settings = client.get("/api/v1/settings/workspace")
    portfolio = client.get("/api/v1/portfolio/status")
    traces = client.get("/api/v1/traces?scope=workspace&limit=10")

    assert reports.status_code == 200
    assert reports.json()["data"]["reports"][0]["scope"] == "workspace"
    assert reports.json()["data"]["summary"]["workspace_context"]["active_workspace_id"] == "inventory-sales-local"
    assert settings.status_code == 200
    assert settings.json()["data"]["summary"]["project_id"] == "inventory-sales-local"
    assert settings.json()["data"]["summary"]["scope"] == "active-workspace"
    assert portfolio.status_code == 200
    assert portfolio.json()["data"]["summary"]["active_workspace_id"] == "inventory-sales-local"
    assert traces.status_code == 200
    assert traces.json()["data"]["summary"]["ui_scope"] == "workspace"
    assert traces.json()["data"]["summary"]["workspace_context"]["active_workspace_id"] == "inventory-sales-local"


def test_invalid_external_ui_context_is_rejected_without_accessing_unallowed_root(tmp_path: Path, monkeypatch) -> None:
    from devpilot_core.application.reports_service import ReportsApplicationService

    platform = tmp_path / "platform"
    (platform / "outputs" / "reports").mkdir(parents=True)
    (platform / "outputs" / "reports" / "platform.json").write_text(json.dumps({"status": "PASS", "ok": True}), encoding="utf-8")
    outside = tmp_path / "outside-workspace"
    outside.mkdir()
    (outside / "secret.json").write_text('{"secret":"not-read"}', encoding="utf-8")
    monkeypatch.delenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", raising=False)
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(outside))

    result = ReportsApplicationService(platform).list_reports(scope="all")

    assert result.ok is True
    assert result.data["summary"]["workspace_context"]["configured"] is True
    assert result.data["summary"]["workspace_context"]["valid"] is False
    assert result.data["summary"]["reports_total"] == 1
    assert all(item["scope"] == "platform" for item in result.data["reports"])
    assert any(finding.id == "UI_ACTIVE_WORKSPACE_ROOT_REJECTED" for finding in result.findings)
    assert all(finding.severity.value != "block" for finding in result.findings)
