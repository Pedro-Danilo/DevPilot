from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application import ApplicationService

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_71_artifacts_and_global_state_are_synchronized() -> None:
    readme = _read("README.md")
    backlog = _read("docs/devpilot_backlog_fase_F_producto_visual.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    runbook = _read("docs/05_operations/runbook.md")

    assert "Último hito: `FUNC-SPRINT-86" in readme
    assert "Siguiente hito: `FUNC-SPRINT-87" in readme
    assert "FUNC-SPRINT-71 — Approval Center y acciones dry-run desde UI" in readme
    assert 'first_open_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-73"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-74"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-87"' in functional_backlog
    assert "FUNC-SPRINT-71 — Operación de Approval Center y Action Launcher" in runbook

    for path in [
        "src/devpilot_core/application/approval_service.py",
        "src/devpilot_core/interfaces/api/routers/approvals.py",
        "src/devpilot_core/interfaces/api/routers/actions.py",
        "ui/web/src/pages/ApprovalCenterView.ts",
        "ui/web/src/components/DryRunActionForm.ts",
        "tests/test_api_approvals_actions.py",
        "tests/test_web_ui_approval_center.py",
        "docs/audits/func_sprint_71_approval_center_audit.md",
        "docs/functional_sprint_71_manifest.json",
    ]:
        assert (ROOT / path).is_file(), path


def test_sprint_71_manifest_tracks_approval_and_dry_run_scope() -> None:
    manifest = _json("docs/functional_sprint_71_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-71"
    assert manifest["status"] == "implemented"
    assert manifest["summary"]["approval_center_implemented"] is True
    assert manifest["summary"]["dry_run_action_launcher_implemented"] is True
    assert manifest["summary"]["critical_actions_blocked_from_ui"] is True
    assert manifest["summary"]["ui_executes_destructive_actions"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-72")


def test_sprint_71_application_contract_reports_approval_center() -> None:
    result = ApplicationService(ROOT).application_contract()
    summary = result.data["summary"]

    assert result.ok is True
    assert summary["approval_center_implemented"] is True
    assert summary["dry_run_action_launcher_implemented"] is True
    assert summary["web_ui_actions_dry_run_only"] is True
    assert summary["web_ui_critical_actions_blocked"] is True
    assert summary["routes_total"] == 29


def test_sprint_71_audit_documents_limits() -> None:
    audit = _read("docs/audits/func_sprint_71_approval_center_audit.md")
    assert "Veredicto: `PASS`" in audit
    assert "acciones críticas" in audit.lower()
    assert "dry-run" in audit.lower()
