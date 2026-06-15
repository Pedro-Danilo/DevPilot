from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import ApplicationService

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = ROOT / "docs" / "07_interfaces" / "openapi_v1.json"
MAPPING_PATH = ROOT / "docs" / "07_interfaces" / "api_service_mapping.md"


def _openapi() -> dict:
    return json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))


def _app_contract() -> dict:
    return ApplicationService(ROOT).application_contract().to_dict()["data"]


def test_openapi_v1_is_static_local_contract_without_server() -> None:
    spec = _openapi()

    assert spec["openapi"] == "3.1.0"
    assert spec["info"]["version"] == "1.0.0-preliminary"
    assert spec["x-devpilot"]["sprint"] == "FUNC-SPRINT-66"
    assert spec["x-devpilot"]["status"] == "contract-only"
    assert spec["x-devpilot"]["api_implemented"] is False
    assert spec["x-devpilot"]["server_implemented"] is False
    assert spec["x-devpilot"]["ui_implemented"] is False
    assert spec["x-devpilot"]["desktop_deferred"] is True
    assert spec["servers"][0]["url"].startswith("http://127.0.0.1")
    assert not (ROOT / "src" / "devpilot_core" / "interfaces" / "api" / "app.py").exists()


def test_openapi_paths_match_application_service_route_contract() -> None:
    spec = _openapi()
    app_contract = _app_contract()

    openapi_routes = {
        (method.upper(), path, operation["x-devpilot-operation"])
        for path, methods in spec["paths"].items()
        for method, operation in methods.items()
    }
    app_routes = {
        (route["method"], route["path"], route["operation"])
        for route in app_contract["routes"]
    }

    assert openapi_routes == app_routes
    assert len(openapi_routes) == app_contract["summary"]["routes_total"] == 13
    assert all(path.startswith("/api/v1/") for _, path, _ in openapi_routes)


def test_openapi_uses_application_response_for_success_and_errors() -> None:
    spec = _openapi()
    schemas = spec["components"]["schemas"]

    assert "ApplicationRequest" in schemas
    assert "ApplicationResponse" in schemas
    assert "ErrorApplicationResponse" in schemas

    for path, methods in spec["paths"].items():
        for method, operation in methods.items():
            assert operation["x-devpilot-status"] == "contract-only"
            assert operation["x-devpilot-domain-service"].endswith(("Service", "application_contract")) or "ApplicationService" in operation["x-devpilot-domain-service"]
            assert "x-devpilot-side-effect" in operation
            assert "x-devpilot-dry-run-default" in operation
            assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ApplicationResponse"
            for status in ["400", "403", "422", "500"]:
                assert operation["responses"][status]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ErrorApplicationResponse"
            if method.upper() == "POST":
                assert "requestBody" in operation, path
                example = operation["requestBody"]["content"]["application/json"]["example"]
                assert example["operation"] == operation["x-devpilot-operation"]
                assert example["dry_run"] is True
            else:
                assert "requestBody" not in operation


def test_api_service_mapping_covers_every_endpoint_and_blocks_dangerous_routes() -> None:
    spec = _openapi()
    mapping = MAPPING_PATH.read_text(encoding="utf-8")
    forbidden_fragments = ["patch/apply", "rollback/execute", "refactor/execute", "/execute", "0.0.0.0"]

    for path, methods in spec["paths"].items():
        assert path in mapping
        assert all(fragment not in path for fragment in forbidden_fragments)
        for operation in methods.values():
            assert operation["x-devpilot-operation"] in mapping
            assert operation["x-devpilot-api-id"] in mapping
            assert "contract-only" in mapping

    assert "ApplicationService" in mapping
    assert "Policy/gate" in mapping
    assert "no patch execution" in mapping or "plan-only" in mapping


def test_api_contract_artifacts_are_synchronized_with_manifest() -> None:
    manifest = json.loads((ROOT / "docs" / "functional_sprint_66_manifest.json").read_text(encoding="utf-8"))
    contract = (ROOT / "docs" / "07_interfaces" / "api_contract_v1.md").read_text(encoding="utf-8")
    audit = (ROOT / "docs" / "audits" / "func_sprint_66_api_contract_audit.md").read_text(encoding="utf-8")

    assert manifest["sprint"] == "FUNC-SPRINT-66"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["api_contract_v1_defined"] is True
    assert manifest["summary"]["openapi_static_defined"] is True
    assert manifest["summary"]["api_implemented"] is False
    assert manifest["summary"]["ui_implemented"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-67")
    assert "server_implemented: false" in contract
    assert "Veredicto: `PASS`" in audit
