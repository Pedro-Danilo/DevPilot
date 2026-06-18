from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import ApplicationService

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_64_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_F_producto_visual.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    manifest = _json("docs/functional_sprint_64_manifest.json")

    expected_paths = [
        "docs/02_architecture/adrs/ADR-0013-web-ui-first.md",
        "docs/03_security/ui_api_threat_model.md",
        "docs/audits/func_sprint_64_ui_api_adr_audit.md",
        "docs/functional_sprint_64_manifest.json",
        "tests/test_sprint_64_documentation.py",
    ]
    for path in expected_paths:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-85" in readme
    assert "Siguiente hito: `FUNC-SPRINT-86" in readme
    assert "## FUNC-SPRINT-64 — ADR UI/API local y threat model de interfaz" in readme
    assert "## FUNC-SPRINT-64 — Operación de ADR UI/API local y threat model de interfaz" in runbook
    assert 'source_repo: "repo_DevPilot_Local_92.zip"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-73"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-74"' in backlog
    assert "## Estado de implementación Sprint 64" in backlog
    assert 'next_sprint: "FUNC-SPRINT-86"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-64" in functional_backlog
    assert manifest["sprint"] == "FUNC-SPRINT-64"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is True
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-65")


def test_sprint_64_decision_and_threat_model_are_explicit() -> None:
    adr = _read("docs/02_architecture/adrs/ADR-0013-web-ui-first.md")
    threat = _read("docs/03_security/ui_api_threat_model.md")
    c4 = _read("docs/02_architecture/c4_container.md")
    contract = _read("docs/07_interfaces/internal_application_contract.md")
    audit = _read("docs/audits/func_sprint_64_ui_api_adr_audit.md")

    for term in ["FastAPI", "Web UI local", "Web UI real", "Desktop", "deferred", "127.0.0.1", "CORS", "token"]:
        assert term in adr
    for term in ["localhost", "CORS", "token", "CSRF", "secret", "path traversal", "Approval Workflow", "0.0.0.0"]:
        assert term.lower() in threat.lower()
    assert "planned-fase-f" in c4
    assert "future-post-fase-f" in c4
    assert "deferred" in c4
    assert "visual_strategy=web_ui_first" in contract
    assert "Veredicto: `PASS`" in audit
    assert "implemented-initial" in audit


def test_sprint_64_application_contract_reports_web_first_strategy() -> None:
    result = ApplicationService(ROOT).application_contract()
    summary = result.data["summary"]

    assert result.ok is True
    assert summary["ui_implemented"] is True
    assert summary["visual_strategy"] == "web_ui_first"
    assert summary["api_local_planned"] is True
    assert summary["web_ui_local_planned"] is True
    assert summary["web_ui_real_future"] is True
    assert summary["desktop_deferred"] is True
    assert summary["desktop_ready_for_shell"] is False
    assert summary["web_ready_for_shell"] is True


def test_sprint_64_scope_does_not_implement_server_frontend_or_desktop() -> None:
    manifest = _json("docs/functional_sprint_64_manifest.json")
    combined = "\n".join(
        _read(path)
        for path in [
            "docs/02_architecture/adrs/ADR-0013-web-ui-first.md",
            "docs/03_security/ui_api_threat_model.md",
            "docs/audits/func_sprint_64_ui_api_adr_audit.md",
        ]
    ).lower()

    assert manifest["summary"]["server_implemented"] is False
    assert manifest["summary"]["frontend_implemented"] is False
    assert manifest["summary"]["desktop_implemented"] is False
    assert manifest["summary"]["external_dependencies_added"] is False
    assert "no implementa servidor" in combined
    assert "no implementa api http" in combined or "sin servidor activo" in combined
    assert "desktop queda diferido" in combined or "desktop is deferred" in combined
    assert (ROOT / "src" / "devpilot_core" / "interfaces" / "api").exists()  # Implemented later by FUNC-SPRINT-67
    assert (ROOT / "ui" / "web" / "package.json").exists()  # Implemented later by FUNC-SPRINT-70
