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
    assert "FUNC-SPRINT-72" in smoke
    assert '"sprint": "FUNC-SPRINT-72"' in package_json
    assert '"approvalCenter": true' in package_json
    assert '"dryRunOnly": true' in package_json
