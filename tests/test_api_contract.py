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


def test_openapi_v1_tracks_local_api_mvp_contract() -> None:
    spec = _openapi()

    assert spec["openapi"] == "3.1.0"
    assert spec["info"]["version"] == "1.0.0-visual-mvp"
    assert spec["x-devpilot"]["sprint"] == "FUNC-SPRINT-73"
    assert spec["x-devpilot"]["status"] == "visual-mvp-closed"
    assert spec["x-devpilot"]["api_implemented"] is True
    assert spec["x-devpilot"]["server_implemented"] is True
    assert spec["x-devpilot"]["ui_implemented"] is True
    assert spec["x-devpilot"]["desktop_deferred"] is True
    assert spec["x-devpilot"]["api_security_implemented"] is True
    assert spec["x-devpilot"]["token_required"] is True
    assert spec["x-devpilot"]["cors_wildcard_enabled"] is False
    assert spec["x-devpilot"]["policy_binding_enabled"] is True
    assert spec["x-devpilot"]["web_ui_mvp_implemented"] is True
    assert spec["x-devpilot"]["web_ui_consumer"] == "ui/web"
    assert spec["servers"][0]["url"].startswith("http://127.0.0.1")
    assert (ROOT / "src" / "devpilot_core" / "interfaces" / "api" / "app.py").exists()


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
    assert len(openapi_routes) == app_contract["summary"]["routes_total"]
    assert len(openapi_routes) >= 30
    assert ("GET", "/api/v1/portfolio/status", "portfolio.status") in openapi_routes
    assert all(path.startswith("/api/v1/") for _, path, _ in openapi_routes)


def test_openapi_uses_application_response_for_success_and_errors() -> None:
    spec = _openapi()
    schemas = spec["components"]["schemas"]

    assert "ApplicationRequest" in schemas
    assert "ApplicationResponse" in schemas
    assert "ErrorApplicationResponse" in schemas

    for path, methods in spec["paths"].items():
        for method, operation in methods.items():
            assert operation["x-devpilot-status"] in {"secured-initial", "report-trace-viewer-initial", "approval-center-initial", "settings-ui-initial", "visual-mvp-closed"}
            assert operation["security"] == [{"LocalTokenAuth": []}]
            assert operation["x-devpilot-auth"] == "local-token-required"
            assert operation["x-devpilot-cors"] == "restricted-local-allowlist"
            assert operation["x-devpilot-security-headers"] is True
            assert operation["x-devpilot-domain-service"].endswith(("Service", "application_contract")) or "ApplicationService" in operation["x-devpilot-domain-service"]
            assert "x-devpilot-side-effect" in operation
            assert "x-devpilot-dry-run-default" in operation
            assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ApplicationResponse"
            for status in ["400", "401", "403", "422", "500"]:
                assert operation["responses"][status]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ErrorApplicationResponse"
            if method.upper() == "POST":
                assert "requestBody" in operation, path
                example = operation["requestBody"]["content"]["application/json"]["example"]
                document_source_mutation_ids = {"API-UOC005-EDIT-APPLY", "API-UOC005-EDIT-ROLLBACK"}
                governed_git_mutation_ids = {"API-UOC006-STAGE", "API-UOC006-COMMIT", "API-UOC006-BRANCH-CREATE"}
                governed_job_control_ids = {"API-UOC008-JOBS-CANCEL", "API-UOC008-JOBS-RETRY"}
                quality_typed_ids = {
                    "API-UOC009-QUALITY-TEST-IMPACT-PLAN",
                    "API-UOC009-QUALITY-JOBS-PLAN",
                    "API-UOC009-QUALITY-JOBS-EXECUTE",
                    "API-UOC009-QUALITY-EVIDENCE-PACKAGE",
                }
                if operation["x-devpilot-api-id"] in governed_job_control_ids:
                    assert set(example) == {"actor", "reason"}
                    assert operation["x-devpilot-source-mutation"] is False
                    assert operation["x-devpilot-arbitrary-shell"] is False
                    assert operation["x-devpilot-remote-execution"] is False
                elif operation["x-devpilot-api-id"] in quality_typed_ids:
                    assert operation["x-devpilot-source-mutation"] is False
                    assert operation["x-devpilot-arbitrary-shell"] is False
                    assert operation["x-devpilot-remote-execution"] is False
                    assert "command" not in example and "executable" not in example and "pytest_args" not in example
                else:
                    assert example["operation"] == operation["x-devpilot-operation"]
                if operation["x-devpilot-api-id"] in document_source_mutation_ids:
                    assert example["dry_run"] is False
                    assert operation["x-devpilot-approval-required"] is True
                    assert operation["x-devpilot-atomic-write"] is True
                elif operation["x-devpilot-api-id"] in governed_git_mutation_ids:
                    assert example["dry_run"] is False
                    assert operation["x-devpilot-approval-required"] is True
                    assert operation["x-devpilot-git-arbitrary-args"] is False
                    assert operation["x-devpilot-push-enabled"] is False
                elif operation["x-devpilot-api-id"] in governed_job_control_ids:
                    assert operation["x-devpilot-side-effect"] == "local_runtime_job_control"
                elif operation["x-devpilot-api-id"] in quality_typed_ids:
                    assert operation["x-devpilot-side-effect"] in {"read_only", "local_runtime_plan", "local_runtime_job_execution", "local_evidence_output"}
                else:
                    assert example["dry_run"] is True
            else:
                assert "requestBody" not in operation


def test_api_service_mapping_covers_every_endpoint_and_blocks_dangerous_routes() -> None:
    spec = _openapi()
    mapping = MAPPING_PATH.read_text(encoding="utf-8")
    forbidden_fragments = ["patch/apply", "rollback/execute", "refactor/execute", "0.0.0.0"]
    allowed_typed_execute_paths = {"/api/v1/workspace/validations/execute", "/api/v1/quality/jobs/{job_id}/execute"}

    for path, methods in spec["paths"].items():
        assert path in mapping
        assert all(fragment not in path for fragment in forbidden_fragments)
        if path.endswith("/execute"):
            assert path in allowed_typed_execute_paths, path
        for operation in methods.values():
            assert operation["x-devpilot-operation"] in mapping
            assert operation["x-devpilot-api-id"] in mapping
            assert "Policy/gate" in mapping

    assert "ApplicationService" in mapping
    assert "Policy/gate" in mapping
    assert "no patch execution" in mapping or "plan-only" in mapping


def test_api_contract_artifacts_are_synchronized_with_manifest() -> None:
    manifest = json.loads((ROOT / "docs" / "functional_sprint_68_manifest.json").read_text(encoding="utf-8"))
    contract = (ROOT / "docs" / "07_interfaces" / "api_contract_v1.md").read_text(encoding="utf-8")
    audit = (ROOT / "docs" / "audits" / "func_sprint_68_api_security_audit.md").read_text(encoding="utf-8")

    assert manifest["sprint"] == "FUNC-SPRINT-68"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["api_local_mvp_implemented"] is True
    assert manifest["summary"]["server_implemented"] is True
    assert manifest["summary"]["api_security_implemented"] is True
    assert manifest["summary"]["token_implemented"] is True
    assert manifest["summary"]["cors_restricted"] is True
    assert manifest["summary"]["ui_implemented"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-69")
    assert "server_implemented: true" in contract
    assert "token_required: true" in contract
    assert "Veredicto: `PASS`" in audit
