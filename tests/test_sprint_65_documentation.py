from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import ApplicationRequest, ApplicationService

ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_65_artifacts_and_global_state_are_synchronized() -> None:
    readme = read_text("README.md")
    backlog = read_text("docs/devpilot_backlog_fase_F_producto_visual.md")
    functional_backlog = read_text("docs/functional_backlog_after_precode.md")
    runbook = read_text("docs/05_operations/runbook.md")
    internal_contract = read_text("docs/07_interfaces/internal_application_contract.md")

    assert "Último hito: `FUNC-SPRINT-66" in readme
    assert "Siguiente hito: `FUNC-SPRINT-67" in readme
    assert "FUNC-SPRINT-65 — ApplicationService v2 por dominios" in readme
    assert 'source_repo: "repo_DevPilot_Local_80.zip"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-67"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-66"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-67"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-67"' in functional_backlog
    assert "FUNC-SPRINT-65 — Operación de ApplicationService v2 por dominios" in runbook
    assert "Sprint 65 — ApplicationService v2 por dominios" in internal_contract

    for path in [
        "docs/audits/func_sprint_65_application_service_v2_audit.md",
        "docs/functional_sprint_65_manifest.json",
        "tests/test_application_services_v2.py",
    ]:
        assert (ROOT / path).is_file(), path


def test_sprint_65_manifest_tracks_scope_and_next_sprint() -> None:
    manifest = json.loads(read_text("docs/functional_sprint_65_manifest.json"))

    assert manifest["sprint"] == "FUNC-SPRINT-65"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["application_service_v2"] is True
    assert manifest["summary"]["domain_facades_enabled"] is True
    assert manifest["summary"]["api_implemented"] is False
    assert manifest["summary"]["ui_implemented"] is False
    assert manifest["summary"]["desktop_deferred"] is True
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-66")
    assert set(manifest["domains"]) >= {
        "workspace",
        "validation",
        "miasi",
        "evals",
        "repo",
        "review",
        "refactor",
        "model",
        "history",
        "observability",
    }


def test_sprint_65_application_contract_exposes_domains_without_api_or_ui() -> None:
    payload = ApplicationService(ROOT).application_contract().to_dict()["data"]

    assert payload["summary"]["schema_version"] == "2.0"
    assert payload["summary"]["application_service_v2"] is True
    assert payload["summary"]["api_implemented"] is False
    assert payload["summary"]["ui_implemented"] is False
    assert payload["summary"]["desktop_deferred"] is True
    assert payload["summary"]["external_api_required"] is False

    routes = {route["path"] for route in payload["routes"]}
    assert "/api/v1/workspace/status" in routes
    assert "/api/v1/repo/inventory" in routes
    assert "/api/v1/observability/traces" in routes
    assert "/api/v1/application/contract" in routes

    operations = {capability["operation"] for capability in payload["capabilities"]}
    assert "workspace.status" in operations
    assert "validation.gateway" in operations
    assert "miasi.validate" in operations
    assert "model.providers" in operations
    assert "observability.agentops_status" in operations
    assert "validators.validate_artifact" in operations


def test_sprint_65_request_dispatcher_blocks_non_contract_actions() -> None:
    service = ApplicationService(ROOT)
    response = service.handle(ApplicationRequest(operation="workspace.status", client="test-suite"))
    blocked = service.execute(ApplicationRequest(operation="patch.apply", payload={"path": "unsafe.patch"}))

    assert response.ok is True
    assert response.operation == "workspace.status"
    assert blocked.ok is False
    assert blocked.findings[0].id == "APPLICATION_OPERATION_NOT_EXPOSED"
