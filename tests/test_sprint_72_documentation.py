from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_sprint_72_artifacts_and_docs_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_F_producto_visual.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    internal_contract = _read("docs/07_interfaces/internal_application_contract.md")
    for path in [
        "src/devpilot_core/application/settings_service.py",
        "src/devpilot_core/interfaces/api/routers/settings.py",
        "ui/web/src/pages/SettingsView.ts",
        "ui/web/src/components/ProviderSettings.ts",
        "tests/test_api_settings.py",
        "tests/test_web_ui_settings.py",
        "docs/audits/func_sprint_72_settings_ui_audit.md",
        "docs/functional_sprint_72_manifest.json",
    ]:
        assert (ROOT / path).exists(), path
    assert "Último hito: `FUNC-SPRINT-82" in readme
    assert "Siguiente hito: `FUNC-SPRINT-83" in readme
    assert "FUNC-SPRINT-72 — Settings UI: workspace, providers y políticas locales" in readme
    assert "FUNC-SPRINT-72 — Operación de Settings UI" in runbook
    assert 'source_repo: "repo_DevPilot_Local_92.zip"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-73"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-83"' in functional_backlog
    assert "Settings UI" in internal_contract


def test_sprint_72_manifest_openapi_and_contract() -> None:
    manifest = _json("docs/functional_sprint_72_manifest.json")
    openapi = _json("docs/07_interfaces/openapi_v1.json")
    assert manifest["sprint"] == "FUNC-SPRINT-72"
    assert manifest["status"] == "implemented"
    summary = manifest["summary"]
    assert summary["settings_ui_implemented"] is True
    assert summary["providers_plan_only"] is True
    assert summary["secrets_redacted"] is True
    assert summary["writes_performed"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-73")
    assert openapi["x-devpilot"]["sprint"] in {"FUNC-SPRINT-72", "FUNC-SPRINT-73"}
    for path in ["/api/v1/settings/workspace", "/api/v1/settings/providers", "/api/v1/settings/policy", "/api/v1/settings/providers/plan"]:
        assert path in openapi["paths"]


def test_sprint_72_audit_validates_limits() -> None:
    audit = _read("docs/audits/func_sprint_72_settings_ui_audit.md")
    assert "Veredicto: `PASS`" in audit
    assert "plan-only" in audit
    assert "No escribe `.devpilot/providers.yaml`" in audit
    assert "No muestra secretos" in audit
