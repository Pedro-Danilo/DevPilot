from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "repo_DevPilot_Local_325_POST_H_EVAL_002_01_D_BROWSER_ACCEPTANCE_CORRECTIVE.zip"
CURRENT_REPO = "repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip"


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def data(path: str) -> dict:
    return json.loads(text(path))


def test_repo_325_history_is_preserved_after_01_d_closure() -> None:
    state = data(".devpilot/project_state.json")
    assert state["post_h_eval_002_01_d_governance_repo"] == CURRENT_REPO
    assert state["current_repo"].startswith("repo_DevPilot_Local_")
    assert state["post_h_eval_002_01_d_source_repo"] == REPO
    assert state["post_h_eval_002_current_micro_sprint"] in {"POST-H-EVAL-002-02-A", "POST-H-EVAL-002-02-B"}
    assert state["post_h_eval_002_01_d_closed"] is True
    assert state["post_h_eval_002_01_d_required_retest_run_id"] == "PILOT-E2E-001-RUN-05B-RERUN-03"
    assert state["post_h_eval_002_01_d_next_authorized"] is True
    assert state["post_h_eval_002_01_d_browser_acceptance_executed"] is True


def test_operation_specific_timeouts_keep_default_bounded() -> None:
    source = text("ui/web/src/api/client.ts")
    assert "DEFAULT_REQUEST_TIMEOUT_MS = 8000" in source
    assert "PROTECTED_WARMUP_TIMEOUT_MS = 15000" in source
    assert "READINESS_REQUEST_TIMEOUT_MS = 30000" in source
    assert "PROVIDER_SETTINGS_READ_TIMEOUT_MS = 45000" in source
    assert "ACTION_DRY_RUN_TIMEOUT_MS = 60000" in source
    assert "PROVIDER_PLAN_TIMEOUT_MS = 60000" in source
    assert "timeoutMs: ACTION_DRY_RUN_TIMEOUT_MS" in source
    assert "timeoutMs: PROVIDER_PLAN_TIMEOUT_MS" in source
    assert "client_request:" in source


def test_ui_state_machines_do_not_render_false_success() -> None:
    approvals = text("ui/web/src/pages/ApprovalCenterView.ts")
    dry_run = text("ui/web/src/components/DryRunActionForm.ts")
    settings = text("ui/web/src/pages/SettingsView.ts")
    states = "'idle' | 'loading' | 'pass' | 'block' | 'timeout' | 'error'"
    assert states in dry_run
    assert states in settings
    assert "No existe resultado PASS" in dry_run
    assert "No existe un plan válido" in settings
    assert "{ dry_run: true, critical_actions_blocked: true }" not in approvals
    assert "Plan-only listo." not in settings


def test_provider_plan_validates_synthetic_payload_and_never_writes() -> None:
    service = text("src/devpilot_core/application/settings_service.py")
    providers = text("src/devpilot_core/modeling/providers.py")
    assert "def parse_provider_config_payload" in providers
    assert "synthetic_payload" in service
    assert "parse_provider_config_payload(" in service
    assert "validate_provider_configs(synthetic_configs" in service
    assert '"validation_target": "synthetic-proposal"' in service
    assert "write_text(" not in service
    assert "write_bytes(" not in service


def test_approval_show_has_explicit_browser_evidence_surface() -> None:
    source = text("ui/web/src/pages/ApprovalCenterView.ts")
    assert "state.selected = await client.showApproval(created.approval_id)" in source
    assert "DETAIL LOADED" in source
    for field in ["approval_id", "status", "tool_id", "action", "subject", "actor", "created_at", "expires_at"]:
        assert f"['{field}'" in source


def test_corrective_manifest_preserves_safety_and_pending_closure() -> None:
    manifest = data("docs/post_h_eval_002_01_d_browser_acceptance_corrective_325_manifest.json")
    assert manifest["target_repo"] == REPO
    assert manifest["run_03_forensic"]["decision"] == "BLOCK-WITH-PROGRESS"
    assert manifest["closure_state"]["closed"] is False
    assert manifest["closure_state"]["required_retest_run_id"] == "PILOT-E2E-001-RUN-04"
    assert manifest["closure_state"]["next_authorized"] is False
    assert manifest["safety"]["external_api_used"] is False
    assert manifest["safety"]["provider_write_enabled"] is False
