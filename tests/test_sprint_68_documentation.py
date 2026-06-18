from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import ApplicationService

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_68_artifacts_and_global_state_are_synchronized() -> None:
    readme = _read("README.md")
    backlog = _read("docs/devpilot_backlog_fase_F_producto_visual.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    runbook = _read("docs/05_operations/runbook.md")
    internal_contract = _read("docs/07_interfaces/internal_application_contract.md")
    threat_model = _read("docs/03_security/ui_api_threat_model.md")

    assert "Último hito: `FUNC-SPRINT-90" in readme
    assert "Siguiente hito: `FUNC-SPRINT-91" in readme
    assert "FUNC-SPRINT-68 — Seguridad API local" in readme
    assert 'source_repo: "repo_DevPilot_Local_92.zip"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-73"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-91"' in functional_backlog
    assert "FUNC-SPRINT-68 — Operación de seguridad API local" in runbook
    assert "Sprint 68 — Seguridad API local secured-initial" in internal_contract
    assert "Implementación Sprint 68" in threat_model

    for path in [
        "src/devpilot_core/interfaces/api/security.py",
        "docs/audits/func_sprint_68_api_security_audit.md",
        "docs/functional_sprint_68_manifest.json",
        "tests/test_api_security.py",
    ]:
        assert (ROOT / path).is_file(), path


def test_sprint_68_manifest_tracks_security_scope() -> None:
    manifest = _json("docs/functional_sprint_68_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-68"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["api_security_implemented"] is True
    assert manifest["summary"]["token_implemented"] is True
    assert manifest["summary"]["token_required"] is True
    assert manifest["summary"]["token_persisted"] is False
    assert manifest["summary"]["cors_restricted"] is True
    assert manifest["summary"]["cors_wildcard_enabled"] is False
    assert manifest["summary"]["policy_binding_enabled"] is True
    assert manifest["summary"]["ui_implemented"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-69")


def test_sprint_68_application_contract_reports_api_security() -> None:
    result = ApplicationService(ROOT).application_contract()
    summary = result.data["summary"]

    assert result.ok is True
    assert summary["api_implemented"] is True
    assert summary["api_local_mvp_implemented"] is True
    assert summary["api_security_implemented"] is True
    assert summary["api_token_required"] is True
    assert summary["api_cors_restricted"] is True
    assert summary["api_cors_wildcard_enabled"] is False
    assert summary["api_policy_binding_enabled"] is True
    assert summary["ui_implemented"] is True
    assert summary["desktop_deferred"] is True


def test_sprint_68_contract_and_openapi_declare_local_token_security() -> None:
    contract = _read("docs/07_interfaces/api_contract_v1.md")
    mapping = _read("docs/07_interfaces/api_service_mapping.md")
    openapi = _json("docs/07_interfaces/openapi_v1.json")
    audit = _read("docs/audits/func_sprint_68_api_security_audit.md")

    assert "token_required: true" in contract
    assert "cors_restricted: true" in contract
    assert "policy_binding_enabled: true" in contract
    assert "local-token-required" in mapping
    assert "API_ROUTE_POLICIES" in mapping
    assert openapi["info"]["version"] in {"1.0.0-web-ui-consumed", "1.0.0-report-trace-viewer", "1.0.0-approval-center", "1.0.0-settings-ui", "1.0.0-visual-mvp"}
    assert openapi["x-devpilot"]["sprint"] in {"FUNC-SPRINT-72", "FUNC-SPRINT-73"}
    assert openapi["x-devpilot"]["token_required"] is True
    assert openapi["x-devpilot"]["web_ui_mvp_implemented"] is True
    assert openapi["x-devpilot"]["cors_wildcard_enabled"] is False
    assert openapi["components"]["securitySchemes"]["LocalTokenAuth"]["name"] == "X-DevPilot-Token"
    assert "Veredicto: `PASS`" in audit
