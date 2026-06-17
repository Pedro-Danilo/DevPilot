from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import ApplicationService

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_66_artifacts_and_global_state_are_synchronized() -> None:
    readme = _read("README.md")
    backlog = _read("docs/devpilot_backlog_fase_F_producto_visual.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    runbook = _read("docs/05_operations/runbook.md")
    internal_contract = _read("docs/07_interfaces/internal_application_contract.md")

    assert "Último hito: `FUNC-SPRINT-76" in readme
    assert "Siguiente hito: `FUNC-SPRINT-77" in readme
    assert "FUNC-SPRINT-66 — Contratos API y OpenAPI preliminar" in readme
    assert 'source_repo: "repo_DevPilot_Local_92.zip"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-73"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-77"' in functional_backlog
    assert "FUNC-SPRINT-66 — Operación de contratos API y OpenAPI preliminar" in runbook
    assert "Sprint 66 — Contrato API v1 y OpenAPI preliminar" in internal_contract

    for path in [
        "docs/07_interfaces/api_contract_v1.md",
        "docs/07_interfaces/openapi_v1.json",
        "docs/07_interfaces/api_service_mapping.md",
        "docs/audits/func_sprint_66_api_contract_audit.md",
        "docs/functional_sprint_66_manifest.json",
        "tests/test_api_contract.py",
    ]:
        assert (ROOT / path).is_file(), path


def test_sprint_66_manifest_tracks_contract_scope() -> None:
    manifest = _json("docs/functional_sprint_66_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-66"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["api_contract_v1_defined"] is True
    assert manifest["summary"]["openapi_static_defined"] is True
    assert manifest["summary"]["api_service_mapping_defined"] is True
    assert manifest["summary"]["api_namespace"] == "/api/v1"
    assert manifest["summary"]["server_implemented"] is False
    assert manifest["summary"]["api_implemented"] is False
    assert manifest["summary"]["ui_implemented"] is False
    assert manifest["summary"]["desktop_deferred"] is True
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-67")


def test_sprint_66_application_contract_reports_static_api_contract() -> None:
    result = ApplicationService(ROOT).application_contract()
    summary = result.data["summary"]

    assert result.ok is True
    assert summary["schema_version"] == "2.0"
    assert summary["api_contract_version"] == "v1"
    assert summary["api_contract_defined"] is True
    assert summary["openapi_contract_defined"] is True
    assert summary["api_implemented"] is True
    assert summary["ui_implemented"] is True
    assert summary["desktop_deferred"] is True
    assert summary["routes_total"] >= 14


def test_sprint_66_scope_does_not_implement_http_server_or_frontend() -> None:
    openapi = _json("docs/07_interfaces/openapi_v1.json")

    assert openapi["x-devpilot"]["server_implemented"] is True
    assert openapi["x-devpilot"]["api_implemented"] is True
    assert openapi["x-devpilot"]["ui_implemented"] is True
    assert openapi["x-devpilot"]["default_host"] == "127.0.0.1"
    assert (ROOT / "src" / "devpilot_core" / "interfaces" / "api" / "app.py").exists()
    # Historical Sprint 66 scope did not implement frontend, but FUNC-SPRINT-70 now adds ui/web.
    assert (ROOT / "ui" / "web" / "package.json").exists()
