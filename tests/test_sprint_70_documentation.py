from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import ApplicationService

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_70_artifacts_and_global_state_are_synchronized() -> None:
    readme = _read("README.md")
    backlog = _read("docs/devpilot_backlog_fase_F_producto_visual.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    runbook = _read("docs/05_operations/runbook.md")

    assert "Último hito: `FUNC-SPRINT-83" in readme
    assert "Siguiente hito: `FUNC-SPRINT-84" in readme
    assert "FUNC-SPRINT-70 — Report Viewer y Trace Viewer" in readme
    assert 'first_open_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-73"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-84"' in functional_backlog
    assert "FUNC-SPRINT-70 — Operación de Report Viewer y Trace Viewer" in runbook

    for path in [
        "src/devpilot_core/interfaces/api/routers/reports.py",
        "src/devpilot_core/interfaces/api/routers/traces.py",
        "src/devpilot_core/application/reports_service.py",
        "ui/web/src/pages/ReportTraceView.ts",
        "ui/web/src/components/FindingTable.ts",
        "tests/test_api_reports_traces.py",
        "tests/test_web_ui_report_trace_viewer.py",
        "docs/audits/func_sprint_70_report_trace_viewer_audit.md",
        "docs/functional_sprint_70_manifest.json",
    ]:
        assert (ROOT / path).is_file(), path


def test_sprint_70_manifest_tracks_viewer_scope() -> None:
    manifest = _json("docs/functional_sprint_70_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-70"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["report_viewer_implemented"] is True
    assert manifest["summary"]["trace_viewer_implemented"] is True
    assert manifest["summary"]["ui_reads_outputs_directly"] is False
    assert manifest["summary"]["api_redaction_enabled"] is True
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-71")


def test_sprint_70_application_contract_reports_viewers() -> None:
    result = ApplicationService(ROOT).application_contract()
    summary = result.data["summary"]

    assert result.ok is True
    assert summary["report_viewer_implemented"] is True
    assert summary["trace_viewer_implemented"] is True
    assert summary["web_ui_reports_api_only"] is True
    assert summary["web_ui_traces_api_only"] is True
    assert summary["routes_total"] >= 19


def test_sprint_70_audit_documents_limits() -> None:
    audit = _read("docs/audits/func_sprint_70_report_trace_viewer_audit.md")
    assert "Veredicto: `PASS`" in audit
    assert "UI no lee `outputs/`" in audit
    assert "redacción" in audit.lower()
