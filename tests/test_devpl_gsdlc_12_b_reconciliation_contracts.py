from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_12_b_ui_route_is_project_scoped_and_project_status_exposes_conflict() -> None:
    main = (ROOT / "ui/web/src/main.ts").read_text(encoding="utf-8")
    view = (ROOT / "ui/web/src/pages/ConflictResolutionView.ts").read_text(encoding="utf-8")
    status = (ROOT / "ui/web/src/pages/ProjectStatusView.ts").read_text(encoding="utf-8")
    assert "path: '/reconciliation'" in main
    assert "routeId: 'ui.reconciliation'" in main
    assert "scope: 'project'" in main
    assert "renderConflictResolutionView" in main
    assert "renderReconciliationSummary" in status
    for marker in ["NO_CONFLICT", "REVALIDATE", "REPLAN_REQUIRED", "MANUAL_RECONCILIATION_REQUIRED", "READ_ONLY_BLOCK", "Cambios observados", "Drafts preservados", "Plan seguro"]:
        assert marker in view
    assert "localStorage" not in view and "sessionStorage" not in view


def test_12_b_registries_include_reconciliation_and_live_ui_route_counts_match() -> None:
    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    ui = json.loads((ROOT / ".devpilot/interfaces/ui_route_contract_registry.json").read_text(encoding="utf-8"))
    caps = json.loads((ROOT / ".devpilot/interfaces/ui_capability_registry.json").read_text(encoding="utf-8"))
    assert {row["operation"] for row in api["routes"]} >= {"reconciliation.status", "reconciliation.baseline", "reconciliation.adopt"}
    route = next(row for row in ui["routes"] if row["route_id"] == "ui.reconciliation")
    assert route["path"] == "/reconciliation"
    assert route["local_only"] is True and route["remote_execution_allowed"] is False
    assert route["mutation_controls"]["destructive_action_allowed"] is False
    assert set(route["allowed_api_routes"]) == {"api.reconciliation.status", "api.reconciliation.baseline", "api.reconciliation.adopt"}
    assert len(caps["ui_routes"]) == caps["summary"]["ui_routes_total"] == caps["summary"]["ui_routes_mapped_total"]
    assert {row["route_id"] for row in caps["ui_routes"]} >= {"ui.recovery", "ui.reconciliation"}
    assert caps["summary"]["api_routes_total"] == len(api["routes"])


def test_12_b_schema_contracts_require_explicit_state_and_integrity_hashes() -> None:
    drift = json.loads((ROOT / "docs/schemas/gsdlc12b_workspace_drift_snapshot.schema.json").read_text(encoding="utf-8"))
    report = json.loads((ROOT / "docs/schemas/gsdlc12b_reconciliation_report.schema.json").read_text(encoding="utf-8"))
    assert drift["properties"]["snapshot_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert set(report["properties"]["classification"]["enum"]) == {"NO_CONFLICT", "REVALIDATE", "REPLAN_REQUIRED", "MANUAL_RECONCILIATION_REQUIRED", "READ_ONLY_BLOCK"}
    assert "report_sha256" in report["required"]


def test_12_b_product_service_contains_no_destructive_git_execution_path() -> None:
    source = (ROOT / "src/devpilot_core/reconciliation/service.py").read_text(encoding="utf-8")
    assert "subprocess.run" in source
    # Product implementation is observation-only. Forbidden destructive command spellings are absent.
    assert "reset --hard" not in source
    assert "git clean" not in source
    assert "rebase --" not in source
    assert "force push" not in source
    assert '"source_mutations_performed": False' in source
    assert '"git_mutations_performed": False' in source


def test_12_b_full_regression_budget_remains_unconsumed() -> None:
    project = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    assert project["gsdlc_12_full_regression_budget_consumed"] == 0
    assert project["gsdlc_12_full_regression_budget_total"] == 1
