from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import ApplicationService

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_69_artifacts_and_global_state_are_synchronized() -> None:
    readme = _read("README.md")
    backlog = _read("docs/devpilot_backlog_fase_F_producto_visual.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    runbook = _read("docs/05_operations/runbook.md")
    internal_contract = _read("docs/07_interfaces/internal_application_contract.md")

    assert "Último hito: `FUNC-SPRINT-79" in readme
    assert "Siguiente hito: `FUNC-SPRINT-80" in readme
    assert "FUNC-SPRINT-69 — Web UI MVP" in readme
    assert 'source_repo: "repo_DevPilot_Local_92.zip"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-73"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-80"' in functional_backlog
    assert "FUNC-SPRINT-69 — Operación de Web UI MVP" in runbook
    assert "Sprint 69 — Web UI local MVP" in internal_contract

    for path in [
        "ui/web/package.json",
        "ui/web/src/main.ts",
        "ui/web/src/api/client.ts",
        "ui/web/src/pages/Dashboard.ts",
        "ui/web/src/components/StatusCard.ts",
        "docs/audits/func_sprint_69_web_ui_dashboard_audit.md",
        "docs/functional_sprint_69_manifest.json",
        "tests/test_web_ui_mvp.py",
    ]:
        assert (ROOT / path).is_file(), path


def test_sprint_69_manifest_tracks_web_ui_scope() -> None:
    manifest = _json("docs/functional_sprint_69_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-69"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["web_ui_implemented"] is True
    assert manifest["summary"]["web_ui_stack"] == "vite-typescript-dom-mvp"
    assert manifest["summary"]["ui_api_only"] is True
    assert manifest["summary"]["ui_imports_core"] is False
    assert manifest["summary"]["ui_read_only"] is True
    assert manifest["summary"]["token_storage"] == "browser_session_storage"
    assert manifest["summary"]["external_api_used"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-70")


def test_sprint_69_application_contract_reports_web_ui() -> None:
    result = ApplicationService(ROOT).application_contract()
    summary = result.data["summary"]

    assert result.ok is True
    assert summary["api_implemented"] is True
    assert summary["api_security_implemented"] is True
    assert summary["ui_implemented"] is True
    assert summary["web_ui_local_implemented"] is True
    assert summary["web_ui_status"] == "implemented-initial"
    assert summary["web_ui_path"] == "ui/web"
    assert summary["desktop_deferred"] is True


def test_sprint_69_pyproject_uses_httpx2_for_starlette_testclient() -> None:
    pyproject = _read("pyproject.toml")

    assert "httpx2>=2.4" in pyproject
    assert "httpx>=0.27" not in pyproject


def test_sprint_69_audit_and_web_readme_document_limits() -> None:
    audit = _read("docs/audits/func_sprint_69_web_ui_dashboard_audit.md")
    web_readme = _read("ui/web/README.md")

    assert "Veredicto: `PASS`" in audit
    assert "API-only" in audit
    # Historical Sprint 69 scope remains preserved in the Sprint 69 audit, while
    # the current Web UI README legitimately evolves after Sprint 70/71.
    assert "Report Viewer y Trace Viewer no están implementados todavía" in audit
    assert "Report Viewer y Trace Viewer" in web_readme
    assert "Approval Center" in web_readme
    assert "npm test" in web_readme
    assert "DEVPILOT_API_TOKEN" in web_readme
