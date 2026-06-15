from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.interfaces.api import DEFAULT_API_HOST, DEFAULT_API_PORT, api_route_paths, create_app

ROOT = Path(__file__).resolve().parents[1]
TEST_TOKEN = "devpilot-test-token"


def _client() -> TestClient:
    app = create_app(ROOT, api_token=TEST_TOKEN)
    client = TestClient(app)
    client.headers.update({"X-DevPilot-Token": TEST_TOKEN})
    return client


def test_api_local_health_and_workspace_status_are_available() -> None:
    client = _client()

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True
    assert health.json()["host_default"] == DEFAULT_API_HOST
    assert health.json()["token_required"] is True

    response = client.get("/api/v1/workspace/status")
    payload = response.json()

    assert response.status_code == 200
    assert response.headers["X-DevPilot-Api-Security"] == "token+cors+policy"
    assert response.headers["X-DevPilot-Policy"] == "allowed"
    assert payload["contract"] == "DevPilotApplicationResponse"
    assert payload["operation"] == "workspace.status"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["ready"] is True


def test_api_local_application_contract_and_standards_status() -> None:
    client = _client()

    contract = client.get("/api/v1/application/contract")
    assert contract.status_code == 200
    contract_payload = contract.json()
    assert contract_payload["operation"] == "app.contract"
    assert contract_payload["data"]["summary"]["api_implemented"] is True
    assert contract_payload["data"]["summary"]["api_local_mvp_implemented"] is True
    assert contract_payload["data"]["summary"]["api_security_implemented"] is True
    assert contract_payload["data"]["summary"]["api_token_required"] is True
    assert contract_payload["data"]["summary"]["api_cors_wildcard_enabled"] is False
    assert contract_payload["data"]["summary"]["api_default_host"] == DEFAULT_API_HOST
    assert contract_payload["data"]["summary"]["api_default_port"] == DEFAULT_API_PORT

    standards = client.get("/api/v1/standards/status")
    assert standards.status_code == 200
    assert standards.json()["operation"] == "standards.status"
    assert standards.json()["ok"] is True


def test_api_local_validation_and_miasi_endpoints_use_application_response() -> None:
    client = _client()

    readiness = client.post("/api/v1/validation/readiness", json={"operation": "validation.readiness", "payload": {"strict": True}, "dry_run": True})
    assert readiness.status_code == 200
    assert readiness.json()["contract"] == "DevPilotApplicationResponse"
    assert readiness.json()["operation"] == "validation.readiness"

    miasi = client.get("/api/v1/miasi/status")
    assert miasi.status_code == 200
    assert miasi.json()["operation"] == "miasi.validate"
    assert miasi.json()["ok"] is True


def test_api_local_blocks_operation_mismatch_and_nonexistent_critical_routes() -> None:
    client = _client()

    mismatch = client.post("/api/v1/refactor/plan", json={"operation": "repo.patch.apply", "payload": {"target": "."}})
    assert mismatch.status_code == 403
    assert mismatch.json()["ok"] is False
    assert mismatch.json()["findings"][0]["id"] == "API_OPERATION_MISMATCH_BLOCK"

    for path in ["/api/v1/patch/apply", "/api/v1/rollback/execute", "/api/v1/refactor/execute"]:
        response = client.post(path)
        assert response.status_code in {403, 404}
        if response.status_code == 403:
            assert response.json()["findings"][0]["id"] == "API_POLICY_BINDING_MISSING_BLOCK"


def test_api_route_paths_helper_ignores_non_http_route_like_objects() -> None:
    class _RouteWithoutPath:
        pass

    app = create_app(ROOT, api_token=TEST_TOKEN)
    app.routes.append(_RouteWithoutPath())  # type: ignore[arg-type]

    paths = api_route_paths(app)

    assert "/api/v1/workspace/status" in paths
    assert all(path.startswith("/api/v1/") for path in paths)


def test_api_route_paths_helper_includes_openapi_semantic_paths() -> None:
    app = create_app(ROOT, api_token=TEST_TOKEN)

    openapi_paths = {path for path in app.openapi()["paths"] if path.startswith("/api/v1/")}
    helper_paths = set(api_route_paths(app))

    assert "/api/v1/workspace/status" in openapi_paths
    assert openapi_paths.issubset(helper_paths)


def test_api_route_paths_helper_walks_nested_router_like_objects() -> None:
    class _NestedRoute:
        path = "/api/v1/nested/synthetic"

    class _IncludedRouterLike:
        routes = [_NestedRoute()]

    app = create_app(ROOT, api_token=TEST_TOKEN)
    app.routes.append(_IncludedRouterLike())  # type: ignore[arg-type]

    paths = api_route_paths(app)

    assert "/api/v1/nested/synthetic" in paths


def test_api_local_routes_are_limited_to_read_or_dry_run_mvp() -> None:
    app = create_app(ROOT, api_token=TEST_TOKEN)
    paths = set(api_route_paths(app))

    assert "/api/v1/workspace/status" in paths
    assert "/api/v1/application/contract" in paths
    assert "/api/v1/validation/readiness" in paths
    assert "/api/v1/miasi/status" in paths
    assert "/api/v1/standards/status" in paths
    assert all("0.0.0.0" not in path for path in paths)
    assert not any(fragment in path for path in paths for fragment in ["patch/apply", "rollback/execute", "refactor/execute"])
