from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_approval_center_ui_is_api_only_and_dry_run_only() -> None:
    approval_view = _read("ui/web/src/pages/ApprovalCenterView.ts")
    action_form = _read("ui/web/src/components/DryRunActionForm.ts")
    client = _read("ui/web/src/api/client.ts")
    dashboard = _read("ui/web/src/pages/Dashboard.ts")

    for source in [approval_view, action_form, client, dashboard]:
        assert "devpilot_core" not in source
        assert "child_process" not in source
        assert "outputs/" not in source

    assert "Approval Center" in approval_view
    assert "Action Launcher" in approval_view
    assert "Solo acciones read-only/dry-run" in action_form
    assert "/approvals" in client
    assert "/actions/dry-run" in client
    assert "/patch/apply" not in client
    assert "/rollback/execute" not in client
    assert "/git/push" not in client


def test_web_smoke_knows_sprint71_contract() -> None:
    smoke = _read("ui/web/scripts/smoke-test.mjs")
    package_json = _read("ui/web/package.json")
    assert "FUNC-SPRINT-73" in smoke
    assert '"sprint": "FUNC-SPRINT-73"' in package_json
    assert '"approvalCenter": true' in package_json
    assert '"dryRunOnly": false' in package_json if '"uoc005ApprovalBinding": true' in package_json else '"dryRunOnly": true' in package_json


def test_browser_acceptance_corrective_325_exposes_dry_run_state_and_approval_detail() -> None:
    approval_view = _read("ui/web/src/pages/ApprovalCenterView.ts")
    action_form = _read("ui/web/src/components/DryRunActionForm.ts")
    client = _read("ui/web/src/api/client.ts")

    assert "ACTION_DRY_RUN_TIMEOUT_MS = 60000" in client
    assert "timeoutMs: ACTION_DRY_RUN_TIMEOUT_MS" in client
    assert "'idle' | 'loading' | 'pass' | 'block' | 'timeout' | 'error'" in action_form
    assert "No existe resultado PASS" in action_form
    assert "{ dry_run: true, critical_actions_blocked: true }" not in approval_view
    assert "state.selected = await client.showApproval(created.approval_id)" in approval_view
    for field in ["approval_id", "status", "tool_id", "action", "subject", "actor", "created_at", "expires_at"]:
        assert f"['{field}'" in approval_view
    assert "DETAIL LOADED" in approval_view
