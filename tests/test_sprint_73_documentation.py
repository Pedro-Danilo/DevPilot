from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import ApplicationService

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_sprint_73_artifacts_and_docs_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_F_producto_visual.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    internal_contract = _read("docs/07_interfaces/internal_application_contract.md")
    for path in [
        "scripts/visual_product_smoke.py",
        "docs/audits/phase_f_visual_product_closure_report.md",
        "docs/release/release_manifest_visual_mvp.json",
        "docs/functional_sprint_73_manifest.json",
        "tests/test_visual_product_smoke.py",
        "tests/test_sprint_73_documentation.py",
    ]:
        assert (ROOT / path).exists(), path
    assert "Último hito: `FUNC-SPRINT-93" in readme
    assert "Siguiente hito: `FUNC-SPRINT-94" in readme
    assert "FUNC-SPRINT-73 — Cierre Fase F web-first y decisión de evolución" in readme
    assert "FUNC-SPRINT-73 — Operación de cierre Fase F" in runbook
    assert 'source_repo: "repo_DevPilot_Local_92.zip"' in backlog
    assert 'phase_f_status: "closed_visual_mvp_web_first"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-73"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-94"' in functional_backlog
    assert "Visual Product Quality Gate" in internal_contract


def test_sprint_73_manifest_release_and_closure_report() -> None:
    manifest = _json("docs/functional_sprint_73_manifest.json")
    release = _json("docs/release/release_manifest_visual_mvp.json")
    closure = _read("docs/audits/phase_f_visual_product_closure_report.md")
    assert manifest["sprint"] == "FUNC-SPRINT-73"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["phase_f_closed"] is True
    assert manifest["summary"]["desktop_deferred"] is True
    assert manifest["summary"]["web_real_evolution_planned"] is True
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-74")
    assert release["sprint"] == "FUNC-SPRINT-73"
    assert release["summary"]["phase_f_closed"] is True
    assert release["summary"]["desktop_deferred"] is True
    assert release["summary"]["web_real_evolution_planned"] is True
    assert "Veredicto: `PASS`" in closure
    assert "Desktop queda diferido" in closure


def test_sprint_73_openapi_ui_and_application_contract_are_closed() -> None:
    openapi = _json("docs/07_interfaces/openapi_v1.json")
    package_json = _json("ui/web/package.json")
    contract = ApplicationService(ROOT).application_contract().to_dict()["data"]
    assert openapi["x-devpilot"]["sprint"] == "FUNC-SPRINT-73"
    assert openapi["x-devpilot"]["status"] == "visual-mvp-closed"
    assert openapi["x-devpilot"]["desktop_deferred"] is True
    assert package_json["devpilot"]["sprint"] == "FUNC-SPRINT-73"
    assert package_json["devpilot"]["phaseFClosed"] is True
    assert package_json["devpilot"]["desktopDeferred"] is True
    assert package_json["devpilot"]["webRealEvolutionPlanned"] is True
    assert contract["summary"]["phase_f_closed"] is True
    assert contract["summary"]["visual_product_mvp_release"] is True
    assert contract["summary"]["next_sprint"] == "FUNC-SPRINT-74"


def test_sprint_73_no_desktop_shell_and_no_runtime_frontend_artifacts() -> None:
    assert not (ROOT / "desktop").exists()
    assert not (ROOT / "ui" / "web" / "node_modules").exists()
    assert not (ROOT / "package-lock.json").exists()
    assert (ROOT / "ui" / "web" / "package-lock.json").exists()
