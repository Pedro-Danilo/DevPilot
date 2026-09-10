from __future__ import annotations

import os
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _fixture_root() -> Path:
    configured = str(os.environ.get("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT") or "").strip()
    return Path(configured).resolve() if configured else ROOT


def test_gsdlc10e_browser_story_value_is_ready() -> None:
    fixture = _fixture_root() / "tests" / "fixtures" / "gsdlc10e_story_value.py"
    assert fixture.is_file(), f"controlled GSDLC-10-E fixture missing: {fixture}"
    value = runpy.run_path(str(fixture))["CYCLE_VALUE"]
    assert value == "ready", f"controlled GSDLC-10-E story failure: expected ready, got {value}"


def test_gsdlc10e_project_route_recovery_is_server_session_bound() -> None:
    main = (ROOT / "ui" / "web" / "src" / "main.ts").read_text(encoding="utf-8")
    assert "recoverSessionBoundProjectRouteContext(client, envelope.session, path)" in main
    assert "route.scope !== 'project'" in main
    assert "scopes.length !== 1" in main
    assert "projectStatusSessionRecovery(expectedWorkspaceId)" in main
    assert "restoreProjectJourneyContextFromProjectStatusRecovery(response, expectedWorkspaceId)" in main
    assert "recovery=session-bound-project-failed" in main


def test_gsdlc10e_project_route_recovery_preserves_browser_storage_as_ux_only() -> None:
    main = (ROOT / "ui" / "web" / "src" / "main.ts").read_text(encoding="utf-8")
    assert "readProjectJourneyContext()?.phase === 'project'" in main
    assert "session.principal.workspace_scopes" in main
    assert "routeAllowed(route, journey)" in main
    assert "sessionStorage" not in main
