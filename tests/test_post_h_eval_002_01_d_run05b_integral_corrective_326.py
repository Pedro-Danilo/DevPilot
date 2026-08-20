from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_326 = "repo_DevPilot_Local_326_POST_H_EVAL_002_01_D_RUN05B_INTEGRAL_CORRECTIVE.zip"
REPO_327 = "repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip"
RERUN_03 = "PILOT-E2E-001-RUN-05B-RERUN-03"


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def data(path: str) -> dict:
    return json.loads(text(path))


def test_repo_326_product_history_is_preserved_after_repo_327_closure() -> None:
    state = data(".devpilot/project_state.json")
    assert state["post_h_eval_002_01_d_governance_repo"] == REPO_327
    assert state["current_repo"].startswith("repo_DevPilot_Local_")
    assert state["post_h_eval_002_01_d_target_repo"] == REPO_326
    assert state["current_micro_sprint"] in {"POST-H-EVAL-002-02-A", "POST-H-EVAL-002-02-B"}
    assert state["post_h_eval_002_01_d_closed"] is True
    assert state["post_h_eval_002_01_d_next_authorized"] is True
    assert state["post_h_eval_002_01_d_required_retest_run_id"] == RERUN_03
    assert state["post_h_eval_002_01_d_run05b_rerun02_result"] == "BLOCK/product-contract-evidence"


def test_dashboard_consumes_health_before_protected_requests() -> None:
    source = text("ui/web/src/pages/Dashboard.ts")
    health = source.index("await client.health()")
    warmup = source.index("await client.protectedWarmup()")
    assert health < warmup
    assert "panel.dataset.apiOperation = 'api.health'" in source
    assert "Operaciones contractuales:" in source
    # The original RUN05B copy remains a historical UI message. GSDLC-03-E successor replaces that presentation with a guided pre-project shell while preserving health-before-warmup semantics.
    assert ("El fan-out autenticado no se ejecutó" in source) or ("renderProjectHomeEntryPanel(session)" in source and "readProjectJourneyContext()?.phase === 'project'" in source)


def test_approval_states_are_truthful_and_conditional() -> None:
    source = text("ui/web/src/pages/ApprovalCenterView.ts")
    assert "if (state.actionOutcome.phase === 'block')" in source
    assert "approvalItems(state).some((approval) => approval.status === 'requested')" in source
    assert "Consulta inicial pendiente. Este estado no acredita una lista vacía." in source
    assert "section.append(renderUiStateNotice('block', 'POST-H-028-D ui.approvals block state: acciones críticas" not in source


def test_settings_never_renders_token_derived_characters() -> None:
    source = text("ui/web/src/pages/SettingsView.ts")
    assert "import { redactSecrets, safeJsonForHtml }" in source
    assert "JSON.stringify(redactSecrets(" in source
    sanitize = text("ui/web/src/utils/sanitize.ts")
    assert "return '<redacted>'" in sanitize


def test_ui_state_notices_have_accessible_semantics() -> None:
    source = text("ui/web/src/components/ContractBadges.ts")
    assert "'pending'" in source
    assert "notice.setAttribute('role'" in source
    assert "notice.setAttribute('aria-live'" in source
    assert "notice.setAttribute('aria-atomic', 'true')" in source


def test_integral_manifest_records_evidence_truth_without_promoting_it() -> None:
    manifest = data("docs/post_h_eval_002_01_d_run05b_integral_corrective_326_manifest.json")
    assert manifest["source_repo"].endswith("_325_POST_H_EVAL_002_01_D_BROWSER_ACCEPTANCE_CORRECTIVE.zip")
    assert manifest["target_repo"] == REPO_326
    assert manifest["rerun_02"]["decision"] == "BLOCK/product-contract-evidence"
    assert manifest["rerun_02"]["observed_ui_operations"] == 21
    assert manifest["rerun_02"]["required_ui_operations"] == 23
    assert manifest["rerun_02"]["valid_negative_screenshots"] == 4
    assert manifest["closure_state"]["required_retest_run_id"] == RERUN_03
    assert manifest["closure_state"]["closed"] is False
    assert manifest["safety"]["secrets_included"] is False


def test_package_metadata_matches_integral_corrective() -> None:
    package = data("ui/web/package.json")
    assert package["version"].startswith("0.") and "-post-h-" in package["version"]
    assert package["devpilot"]["sprint"] == "FUNC-SPRINT-73"
    assert package["devpilot"]["run05bIntegralCorrective326"] is True
    assert package["devpilot"]["postHEvolution"] is True
    assert package["devpilot"]["run05bIntegralCorrective326"] is True
    assert package["devpilot"]["dashboardHealthConsumed"] is True
    assert package["devpilot"]["browserRetestRunId"] == RERUN_03


def test_node_gate_is_independent_of_caller_working_directory() -> None:
    source = text("ui/web/scripts/run05b-integral-corrective-326.mjs")
    assert "fileURLToPath(import.meta.url)" in source
    assert "path.resolve(scriptDirectory, '..')" in source
    assert "path.resolve(process.cwd())" not in source
