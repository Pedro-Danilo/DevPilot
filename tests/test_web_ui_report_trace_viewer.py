from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "ui" / "web"


def _read(rel: str) -> str:
    return (WEB / rel).read_text(encoding="utf-8")


def test_web_ui_report_trace_viewer_is_api_only() -> None:
    sources = "\n".join(path.read_text(encoding="utf-8") for path in (WEB / "src").rglob("*.ts"))

    assert "Report Viewer" in sources
    assert "Trace Viewer" in sources
    assert "/reports" in sources
    assert "/traces" in sources
    assert "/metrics/summary" in sources
    assert "outputs/" not in sources
    assert ".devpilot/" not in sources
    assert "devpilot_core" not in sources
    assert "child_process" not in sources
    assert "X-DevPilot-Token" in sources


def test_web_ui_smoke_script_tracks_sprint70_scope() -> None:
    package = json.loads(_read("package.json"))
    smoke = _read("scripts/smoke-test.mjs")

    assert package["devpilot"]["sprint"] == "FUNC-SPRINT-71"
    assert package["devpilot"]["reportViewer"] is True
    assert package["devpilot"]["traceViewer"] is True
    assert "Report Viewer" in smoke
    assert "Trace Viewer" in smoke
    assert "Sin trazas para mostrar" in smoke
