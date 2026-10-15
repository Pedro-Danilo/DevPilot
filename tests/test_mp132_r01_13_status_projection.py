from __future__ import annotations
from pathlib import Path
from devpilot_core.guided_sdlc.workflow_status_projection import project_workflow_status as status

ROOT = Path(__file__).resolve().parents[1]


def fixture(*, kind="ADVANCE_TRANSITION", available=True, mutating=False, terminal=False, lifecycle="IN_PROGRESS"):
    project = {"lifecycle_status": lifecycle, "progress": {"terminal": terminal}, "blockers": [], "freshness": {"status": "FRESH", "state_fingerprint": "abc"}}
    next_action = {"kind": kind, "action_id": "next.test", "available": available, "mutating": mutating, "reason_code": "TEST", "navigation_target": "project-status"}
    return project, next_action


def test_shared_gate_ready_and_pending_from_same_inputs():
    data, action = fixture()
    passed = status(data, action, "READY")
    assert passed["status"] == "READY" and passed["continue_cta_enabled"] is True
    action["available"] = False
    pending = status(data, action, "READY")
    assert pending["status"] == "PENDING" and not pending["continue_cta_enabled"]
    assert pending["next_action_id"] == passed["next_action_id"]


def test_never_adjudicate_terminal_on_panel_ready_alone():
    data, action = fixture(kind="COMPLETE", lifecycle="RELEASED")
    assert not status(data, action, "READY")["terminal_cta_enabled"]
    data["progress"]["terminal"] = True
    assert status(data, action, "READY")["terminal_cta_enabled"]
    data["blockers"] = [{"category": "release", "code": "NOT_READY"}]
    assert not status(data, action, "BLOCKED")["terminal_cta_enabled"]
    assert not status(data, action, "READY", {"authoritative_blocker_count": 1})["terminal_cta_enabled"]


def test_gate_denies_stale_unknown_block_and_mutating_navigation():
    data, action = fixture()
    for state in ("STALE", "BLOCKED", "EMPTY", "UNKNOWN", "REVALIDATION_REQUIRED"):
        assert not status(data, action, state)["continue_cta_enabled"]
    action["mutating"] = True
    assert status(data, action, "READY")["status"] == "READY"
    assert not status(data, action, "READY")["continue_cta_enabled"]


def test_stable_recompute_for_refresh_and_recovery():
    data, action = fixture()
    assert status(data, action, "READY") == status(data, action, "READY")
    data["freshness"]["status"] = "STALE"
    assert status(data, action, "READY")["status"] == "PENDING"
    data["freshness"]["status"] = "FRESH"
    assert status(data, action, "READY")["status"] == "READY"


def test_ui_header_panel_and_cta_share_server_projection():
    src = (ROOT / "ui/web/src/pages/ProjectStatusView.ts").read_text(encoding="utf-8")
    assert "data.workflow_status" in src
    assert "badge.dataset.workflowStatus = workflow?.status" in src
    assert "panel.dataset.workflowStatus = workflow?.status" in src
    assert "workflow?.terminal_cta_enabled === true" in src
    assert "workflow?.continue_cta_enabled === true" in src
    app = (ROOT / "src/devpilot_core/application/guided_sdlc_service.py").read_text(encoding="utf-8")
    assert '"workflow_status": project_workflow_status(status_payload, next_payload, ui_state, lifecycle_reconciliation)' in app
    assert '"workflow_status": project_workflow_status(unknown.status.to_payload(), unknown.next_action.to_payload(), "EMPTY")' in app
