from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.application import ApplicationResponse
from devpilot_core.cli_models import ExitCode
from devpilot_core.interfaces.api import create_app
from devpilot_core.interfaces.api.dependencies import get_application_service
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, API_TOKEN_HEADER

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "gsdlc01e-test-token"


def j(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class _FakeProjectStatusService:
    def handle(self, request):
        assert request.operation == "guided_sdlc.project_status"
        payload = {
            "ui_state": "REVALIDATION_REQUIRED",
            "workspace_id": "ws-1",
            "project_status": {
                "workspace_id": "ws-1", "project_id": "p-1", "phase": "REQUIREMENTS", "current_step": "requirements",
                "lifecycle_status": "REVALIDATION_REQUIRED", "progress": {"percent": 25.0}, "mipsoftware": {"status": "ACTIVE"},
                "miasi": {"status": "UNKNOWN"}, "artifact_readiness": {"status": "ATTENTION_REQUIRED"}, "planning": {"status": "UNKNOWN"},
                "blockers": [], "pending_approvals": [], "quality": {"status": "UNKNOWN"}, "git": {"status": "DIRTY"},
                "revalidation": {"status": "REQUIRED"}, "model_budget": {"status": "NOT_AVAILABLE"}, "freshness": {"status": "FRESH"},
                "source_refs": [], "reason": None,
            },
            "next_action": {"action_id": "next.revalidate", "kind": "REVALIDATE", "reason_code": "REVALIDATION_REQUIRED", "explanation": "Revalidate", "navigation_target": "project-status/revalidation", "mutating": True, "available": False, "disabled_reason": "READ_ONLY_IN_GSDLC_01_E"},
            "read_only": True, "actor_neutral": True, "network_used": False, "external_api_used": False, "mutations_performed": False,
        }
        return ApplicationResponse(operation=request.operation, ok=True, exit_code=ExitCode.PASS, message="ok", data=payload, findings=[])


def test_01_e_predecessor_d_final_owner_authority_is_present() -> None:
    adjudication = j("docs/audits/DEVPL_GSDLC_01_D_FINAL_OWNER_ADJUDICATION_v1_0_0.json")
    assert adjudication["decision"] == "CLOSED/PASS"
    assert adjudication["successor_commit"] == "7c050d12d9641642aae971f0d32934f5af5a9557"
    assert adjudication["successor_sha256"] == "d5722222d1b0e9675f3c136df12df0310224450467332e13b9222ea2c4ade4f8"


def test_01_e_api_route_is_protected_read_only_and_uses_application_boundary() -> None:
    assert ("GET", "/api/v1/guided-sdlc/status") in API_ROUTE_POLICIES
    policy = API_ROUTE_POLICIES[("GET", "/api/v1/guided-sdlc/status")]
    assert policy.operation == "guided_sdlc.project_status"
    assert policy.action == "read"
    app = create_app(ROOT, api_token=TOKEN)
    app.dependency_overrides[get_application_service] = lambda: _FakeProjectStatusService()
    client = TestClient(app)
    unauthorized = client.get("/api/v1/guided-sdlc/status")
    assert unauthorized.status_code == 401
    response = client.get("/api/v1/guided-sdlc/status", headers={API_TOKEN_HEADER: TOKEN})
    assert response.status_code == 200
    body = response.json()
    assert body["operation"] == "guided_sdlc.project_status"
    assert body["data"]["ui_state"] == "REVALIDATION_REQUIRED"
    assert body["data"]["read_only"] is True
    assert body["data"]["mutations_performed"] is False


def test_01_e_route_registry_is_successor_10_and_uoc011_snapshot_stays_9() -> None:
    current = j(".devpilot/interfaces/ui_route_contract_registry.json")
    frozen = j(".devpilot/interfaces/ui_route_contract_registry_uoc011_at_close.json")
    matrix = j(".devpilot/interfaces/uoc011_browser_state_matrix.json")
    assert len(current["routes"]) >= 10
    assert current["summary"]["routes_total"] == len(current["routes"])
    assert len(frozen["routes"]) == 9
    assert len(matrix["routes"]) == 9 and matrix["summary"]["cases_total"] == 108
    assert {r["route_id"] for r in frozen["routes"]} == {r["route_id"] for r in matrix["routes"]}
    route = next(r for r in current["routes"] if r["route_id"] == "ui.project-status")
    assert route["path"] == "/project/status"
    assert route["allowed_api_routes"] == ["api.guided-sdlc.project-status"]
    assert route["shows_mutation_controls"] is False
    assert route["state_contract"]["revalidation_required"] is True


def test_01_e_project_status_view_uses_api_and_never_direct_core_or_innerhtml() -> None:
    source = (ROOT / "ui/web/src/pages/ProjectStatusView.ts").read_text(encoding="utf-8")
    main = (ROOT / "ui/web/src/main.ts").read_text(encoding="utf-8")
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    assert "ui.project-status" in source
    assert "textContent" in source and "innerHTML" not in source
    assert "action.mutating !== true" in source
    assert "globalThis.location.assign" in source
    for forbidden in ("devpilot_core", "child_process", "outputs/", ".devpilot/"):
        assert forbidden not in source
    assert "renderProjectStatusView" in main and "'/project/status'" in main
    assert "/guided-sdlc/status" in client


def test_01_e_package_preserves_historical_top_level_route_flag_and_declares_successor() -> None:
    package = j("ui/web/package.json")
    flags = package["devpilot"]
    assert flags["gsdlc01eTopLevelUiRoutesChanged"] is True
    assert flags["uoc011RoutesTotalAtClose"] == 9
    assert flags["currentTopLevelUiRoutesTotal"] >= 10
    assert flags["topLevelUiRoutesChanged"] is (flags["currentTopLevelUiRoutesTotal"] > flags["uoc011RoutesTotalAtClose"])
    assert flags["uoc011RoutesTotalAtClose"] == 9
    assert flags["gsdlc01eContinueMutatesState"] is False
