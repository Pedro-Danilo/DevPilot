from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_REPO = "repo_DevPilot_Local_322_POST_H_EVAL_002_01_D_ACCEPTANCE_READY.zip"


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_01_d_remains_open_and_next_not_authorized() -> None:
    state = _json(".devpilot/project_state.json")
    assert state["current_repo"] == TARGET_REPO
    assert state["current_micro_sprint"] == "POST-H-EVAL-002-01-D"
    assert state["next_micro_sprint"] == "POST-H-EVAL-002-02-A"
    assert state["post_h_eval_002_01_d_closed"] is False
    assert state["post_h_eval_002_01_d_browser_acceptance_executed"] is False
    assert state["post_h_eval_002_01_d_next_authorized"] is False


def test_five_registered_routes_have_runtime_dispatch() -> None:
    registry = _json(".devpilot/interfaces/ui_route_contract_registry.json")
    main = (ROOT / "ui/web/src/main.ts").read_text(encoding="utf-8")
    expected = {
        "ui.dashboard": "/",
        "ui.reports": "/reports",
        "ui.traces": "/traces",
        "ui.approvals": "/approvals",
        "ui.settings": "/settings",
    }
    assert {item["route_id"]: item["path"] for item in registry["routes"]} == expected
    for route_id, path in expected.items():
        assert f"path: '{path}'" in main
        assert f"routeId: '{route_id}'" in main


def test_route_navigation_and_controlled_unknown_route_exist() -> None:
    main = (ROOT / "ui/web/src/main.ts").read_text(encoding="utf-8")
    assert "renderPrimaryNavigation" in main
    assert "aria-current" in main
    assert "renderNotFound" in main
    assert "Ruta UI no registrada" in main


def test_browser_requests_have_bounded_timeout() -> None:
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    assert "DEFAULT_REQUEST_TIMEOUT_MS = 8000" in client
    assert "AbortController" in client
    assert "controller.abort()" in client
    assert "state: 'timeout'" in client
    assert "Tiempo de espera agotado" in client


def test_token_remains_session_only_and_not_in_url() -> None:
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    main = (ROOT / "ui/web/src/main.ts").read_text(encoding="utf-8")
    assert "sessionStorage" in client
    assert "localStorage" not in client
    assert "?token=" not in main
    assert "token=" not in client


def test_acceptance_baseline_npm_contract_is_registered() -> None:
    package = _json("ui/web/package.json")
    assert package["scripts"]["test:acceptance-baseline"] == "node scripts/acceptance-baseline.mjs"
    assert package["devpilot"]["routeAwareRuntimeDispatch"] is True
    assert package["devpilot"]["requestTimeoutMs"] == 8000
    assert package["devpilot"]["browserAcceptanceExecuted"] is False


def test_preparation_manifest_is_open_and_bounded() -> None:
    manifest = _json("docs/post_h_eval_002_01_d_preparation_manifest.json")
    assert manifest["status"] == "active"
    assert manifest["decision"] == "IMPLEMENTED-PENDING-WINDOWS-BROWSER-EVIDENCE"
    assert manifest["micro_sprint_state"]["closed"] is False
    assert manifest["micro_sprint_state"]["next_authorized"] is False
    assert len(manifest["blockers_corrected"]) == 2


def test_backlog_and_readme_do_not_claim_01_d_closed() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-EVAL-002-01_baseline_ui_acceptance.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert 'current_micro_sprint: "POST-H-EVAL-002-01-D"' in backlog
    assert "active/01-d-acceptance-ready" in backlog
    assert "01-D permanece abierto" in readme


def test_no_pilot_workspace_or_browser_evidence_is_versioned() -> None:
    assert not (ROOT / "workspaces/inventory-sales-local").exists()
    assert not (ROOT / "evidence/PILOT-E2E-001/03_ui_baseline_acceptance").exists()
    assert not list(ROOT.rglob("*.png"))
