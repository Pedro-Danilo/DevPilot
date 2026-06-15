from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import ApplicationService

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_67_artifacts_and_global_state_are_synchronized() -> None:
    readme = _read("README.md")
    backlog = _read("docs/devpilot_backlog_fase_F_producto_visual.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    runbook = _read("docs/05_operations/runbook.md")
    internal_contract = _read("docs/07_interfaces/internal_application_contract.md")

    assert "Último hito: `FUNC-SPRINT-68" in readme
    assert "Siguiente hito: `FUNC-SPRINT-69" in readme
    assert "FUNC-SPRINT-67 — API local MVP read-only/dry-run" in readme
    assert 'source_repo: "repo_DevPilot_Local_84.zip"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-69"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-68"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-69"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-69"' in functional_backlog
    assert "FUNC-SPRINT-67 — Operación de API local MVP read-only/dry-run" in runbook
    assert "Sprint 67 — API local MVP read-only/dry-run" in internal_contract

    for path in [
        "src/devpilot_core/interfaces/api/app.py",
        "src/devpilot_core/interfaces/api/routers/status.py",
        "src/devpilot_core/interfaces/api/routers/validation.py",
        "src/devpilot_core/interfaces/api/routers/actions.py",
        "docs/audits/func_sprint_67_api_local_mvp_audit.md",
        "docs/functional_sprint_67_manifest.json",
        "tests/test_api_local.py",
    ]:
        assert (ROOT / path).is_file(), path


def test_sprint_67_manifest_tracks_api_mvp_scope() -> None:
    manifest = _json("docs/functional_sprint_67_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-67"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["api_local_mvp_implemented"] is True
    assert manifest["summary"]["server_implemented"] is True
    assert manifest["summary"]["default_host"] == "127.0.0.1"
    assert manifest["summary"]["default_port"] == 8787
    assert manifest["summary"]["token_implemented"] is False
    assert manifest["summary"]["cors_implemented"] is False
    assert manifest["summary"]["ui_implemented"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-68")


def test_sprint_67_application_contract_reports_api_mvp() -> None:
    result = ApplicationService(ROOT).application_contract()
    summary = result.data["summary"]

    assert result.ok is True
    assert summary["api_implemented"] is True
    assert summary["api_local_mvp_implemented"] is True
    assert summary["api_default_host"] == "127.0.0.1"
    assert summary["api_default_port"] == 8787
    assert summary["ui_implemented"] is False
    assert summary["desktop_deferred"] is True
    assert summary["routes_total"] == 14


def test_sprint_67_pyproject_declares_api_dependencies() -> None:
    pyproject = _read("pyproject.toml")

    assert "fastapi" in pyproject
    assert "uvicorn" in pyproject
    assert "httpx" in pyproject
    assert "api =" in pyproject
    assert "dev =" in pyproject
