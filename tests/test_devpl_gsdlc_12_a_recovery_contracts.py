from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_12_a_recovery_ui_is_project_scoped_and_server_authoritative() -> None:
    main = (ROOT / "ui/web/src/main.ts").read_text(encoding="utf-8")
    view = (ROOT / "ui/web/src/pages/RecoveryView.ts").read_text(encoding="utf-8")
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    assert "path: '/recovery'" in main
    assert "routeId: 'ui.recovery'" in main
    assert "scope: 'project'" in main
    assert "RecoveryView" in main
    for marker in [
        "browser_storage_authority",
        "REVALIDATION_REQUIRED",
        "SAFE_TO_RESUME",
        "Guardar checkpoint seguro",
        "Adquirir lock sensible",
        "Project Status coherence",
    ]:
        assert marker in view
    for marker in ["recoveryStatus", "recoveryCheckpoint", "recoveryLockAcquire", "recoveryLockRelease", "recoveryLockRecover"]:
        assert marker in client
    assert "sessionStorage" not in view
    assert "localStorage" not in view


def test_12_a_project_status_released_reconciliation_preserves_gaps_without_contradictory_blocked() -> None:
    source = (ROOT / "src/devpilot_core/application/guided_sdlc_service.py").read_text(encoding="utf-8")
    assert 'lifecycle == "RELEASED"' in source
    assert 'current_step == "local-release-closed"' in source
    assert '"RELEASED_WITH_NON_AUTHORITATIVE_GAPS"' in source
    assert '"display_state": "BLOCKED" if authoritative_blockers else "RELEASED"' in source
    assert '"blockers_preserved": True' in source
    assert '"hidden_blockers": False' in source
    assert "authoritative_categories" in source


def test_12_a_recovery_durable_store_excludes_runtime_db_and_managed_source_writes() -> None:
    source = (ROOT / "src/devpilot_core/recovery/service.py").read_text(encoding="utf-8")
    assert '"outputs" / "workspaces" / workspace_id / "recovery"' in source
    assert '"runtime_db_snapshot_used": False' in source
    assert '"source_mutations_performed": False' in source
    assert '"auto_execute"] = False' in source
    assert "auth.db" not in source
    assert "devpilot.db" not in source
    assert "reset --hard" not in source
    assert "git clean" not in source


def test_12_a_current_active_contract_registries_include_recovery_without_full_regression() -> None:
    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    rbac = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    ui = json.loads((ROOT / ".devpilot/interfaces/ui_route_contract_registry.json").read_text(encoding="utf-8"))
    api_ops = {row["operation"] for row in api["routes"]}
    rbac_ops = {row["operation"] for row in rbac["route_policies"]}
    required = {"recovery.status", "recovery.checkpoint", "recovery.lock.acquire", "recovery.lock.release", "recovery.lock.recover"}
    assert required <= api_ops
    assert required <= rbac_ops
    recovery_ui = next(row for row in ui["routes"] if row["route_id"] == "ui.recovery")
    assert recovery_ui["path"] == "/recovery"
    assert recovery_ui["local_only"] is True
    assert recovery_ui["remote_execution_allowed"] is False
    assert set(recovery_ui["allowed_api_routes"]) == {
        "api.recovery.status",
        "api.recovery.checkpoint",
        "api.recovery.lock.acquire",
        "api.recovery.lock.release",
        "api.recovery.lock.recover",
    }
    project = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    assert project["current_phase"] == "DEVPL-GSDLC-12"
    # Successor-safe historical contract: 12-A remains CLOSED/PASS while the current pointer may advance within GSDLC-12.
    assert project["gsdlc_12_a_status"] == "CLOSED/PASS/WINDOWS-VALIDATED"
    assert project["current_micro_sprint"] in {"DEVPL-GSDLC-12-A", "DEVPL-GSDLC-12-B", "DEVPL-GSDLC-12-C", "DEVPL-GSDLC-12-D", "DEVPL-GSDLC-12-E"}
    assert project["gsdlc_12_a_full_regression_runs"] == 0
    assert project["gsdlc_12_full_regression_budget_consumed"] == 0
    assert project["gsdlc_12_full_regression_budget_total"] == 1


def test_12_a_activation_sources_are_bound_to_repo425() -> None:
    backlog = (ROOT / "DEVPL-GSDLC-12_ux_resumability_reconciliation_and_industrial_hardening_v1_3_1_APPROVED_REBOUND_REPO425.md").read_text(encoding="utf-8")
    activation = (ROOT / "00_PROMPT_DEVPL_GSDLC_12_ACTIVATION_REBIND_v1_0_0_REPO425.md").read_text(encoding="utf-8")
    prompt = (ROOT / "01_PROMPT_DEVPL_GSDLC_12_A_v1_0_0_REPO425.md").read_text(encoding="utf-8")
    expected_repo = "repo_DevPilot_Local_425_DEVPL_GSDLC_11_E_CLEAN_INSTALL_BROWSER_RELEASE_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip"
    expected_commit = "b341370633e66355add6bb2611879b32f277ad0f"
    expected_sha = "d4a9cf4b3b8d544b71ee9b568e7ba3388cf39e74ce8d213d3b0e9f9d2946695d"
    for source in [backlog, activation]:
        assert expected_repo in source
    assert 'repo425' in prompt
    assert expected_commit in backlog and expected_commit in activation
    assert expected_sha in backlog and expected_sha in activation
    assert "Full Regression = 0" in prompt


def test_12_a_new_human_session_restores_project_route_from_durable_recovery_before_guarding_home() -> None:
    main = (ROOT / "ui/web/src/main.ts").read_text(encoding="utf-8")
    client = (ROOT / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    segment = main.split("async function recoverSessionBoundProjectRouteContext", 1)[1].split("function renderRouteHeader", 1)[0]
    assert "client.projectStatusSessionRecovery(expectedWorkspaceId)" in segment
    assert "client.settingsWorkspace()" in segment
    assert "client.recoveryStatus()" in segment
    assert "restoreProjectJourneyContextFromDurableRecovery(recovery, expectedWorkspaceId)" in segment
    assert segment.index("projectStatusSessionRecovery") < segment.index("settingsWorkspace") < segment.index("recoveryStatus")
    helper = client.split("export function restoreProjectJourneyContextFromDurableRecovery", 1)[1].split("export function beginProjectEntryJourney", 1)[0]
    for required in [
        "response.ok === true",
        "authority?.server_side === true",
        "authority?.browser_storage_authority === false",
        "authority?.runtime_db_snapshot_used === false",
        "recovery?.browser_storage_authority === false",
        "recovery?.runtime_db_snapshot_used === false",
        "recovery?.auto_resume_mutation === false",
        "workspaceId === expectedWorkspaceId",
        "checkpointRecord !== null",
        "String(checkpointRecord.schema_version ?? '') === '1.0'",
        "String(checkpointRecord.workspace_id ?? '') === workspaceId",
        "checkpointRecord.source_mutations_performed === false",
        "phase: 'project'",
        "globalThis.sessionStorage?.setItem(PROJECT_JOURNEY_CONTEXT_KEY",
    ]:
        assert required in helper
    assert "projectEntry" not in helper
