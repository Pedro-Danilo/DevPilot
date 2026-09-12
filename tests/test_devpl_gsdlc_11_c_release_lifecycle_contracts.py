from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_11c_api_ui_rbac_contracts_are_registered():
    api=json.loads((ROOT/'.devpilot/interfaces/api_route_contract_registry.json').read_text()); ids={r['route_id'] for r in api['routes']}
    expected={'api.release.lifecycle.status','api.release.lifecycle.install.plan','api.release.lifecycle.install.execute','api.release.lifecycle.upgrade.plan','api.release.lifecycle.upgrade.execute','api.release.lifecycle.rollback.plan','api.release.lifecycle.rollback.execute'};assert expected<=ids
    rbac=json.loads((ROOT/'.devpilot/identity/server_rbac_policy_catalog.json').read_text()); policies={r['route_id']:r for r in rbac['route_policies']}
    for rid in expected: assert policies[rid]['legacy_token_allowed'] is False and policies[rid]['workspace_scope_required'] is True
    ui=json.loads((ROOT/'.devpilot/interfaces/ui_route_contract_registry.json').read_text()); route=next(r for r in ui['routes'] if r['route_id']=='ui.release-lifecycle');assert set(route['allowed_api_routes'])==expected;assert route['mutation_controls']['source_write_enabled'] is False

def test_11c_closed_fact_survives_successor_without_reading_mutable_current_budget():
    s=json.loads((ROOT/'.devpilot/project_state.json').read_text()); assert s['gsdlc_11_c_status']=='CLOSED/PASS/WINDOWS-VALIDATED'; assert s['gsdlc_11_c_successor_repo'].startswith('repo_DevPilot_Local_423_'); assert s['gsdlc_11_c_full_regression_runs']==0; assert s['gsdlc_11_d_authorized'] is True

def test_11c_ui_and_docs_current_active_markers():
    main=(ROOT/'ui/web/src/main.ts').read_text();page=(ROOT/'ui/web/src/pages/ReleaseLifecycleView.ts').read_text();assert "'/release/lifecycle'" in main;assert 'backup-before-upgrade' in page;assert 'sandbox-only' in page
    backlog=(ROOT/'DEVPL-GSDLC-11_release_and_lifecycle_workbench_v1_3_2_APPROVED_REBOUND_REPO422.md').read_text();assert 'GSDLC-11-C' in backlog and 'repo_DevPilot_Local_422_' in backlog
