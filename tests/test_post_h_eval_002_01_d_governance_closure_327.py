from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO_326 = "repo_DevPilot_Local_326_POST_H_EVAL_002_01_D_RUN05B_INTEGRAL_CORRECTIVE.zip"
REPO_327 = "repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip"
RUN_02 = "PILOT-E2E-001-RUN-05B-RERUN-02"
RUN_03 = "PILOT-E2E-001-RUN-05B-RERUN-03"
CONTRACT_ID = "post-h-eval-002-01-d-governance-closure-327"


def data(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_project_state_closes_01_d_and_authorizes_02_a() -> None:
    state = data(".devpilot/project_state.json")
    assert state["post_h_eval_002_01_d_governance_repo"] == REPO_327
    assert state["post_h_eval_002_02_b_platform_baseline"].startswith("repo_DevPilot_Local_")
    assert state["post_h_eval_002_current_micro_sprint"] in {"POST-H-EVAL-002-02-A", "POST-H-EVAL-002-02-B"}
    if state["post_h_eval_002_current_micro_sprint"] == "POST-H-EVAL-002-02-B":
        assert state["post_h_eval_002_next_micro_sprint"] == "POST-H-EVAL-002-02-C"
    else:
        assert state["post_h_eval_002_next_micro_sprint"] == "POST-H-EVAL-002-02-B"
    assert state["post_h_eval_002_01_d_closed"] is True
    assert state["post_h_eval_002_01_d_status"] == "closed/PASS-authoritative-rerun03"
    assert state["post_h_eval_002_01_d_browser_acceptance_executed"] is True
    assert state["post_h_eval_002_01_d_next_authorized"] is True
    assert state["post_h_eval_002_01_d_run05b_rerun03_result"] == "CLOSED/PASS"
    assert state["post_h_eval_002_01_d_s0_open"] == 0
    assert state["post_h_eval_002_01_d_s1_open"] == 0


def test_manifest_preserves_forensic_run_and_authoritative_run() -> None:
    manifest = data("docs/post_h_eval_002_01_d_governance_closure_327_manifest.json")
    assert manifest["source_repo"] == REPO_326
    assert manifest["target_repo"] == REPO_327
    assert manifest["functional_code_changed"] is False
    strategy = manifest["implementation_strategy"]
    assert strategy["version"] == "2.1.1"
    assert strategy["strategy"] == "direct-transactional-governance-overlay-git-canonical"
    assert strategy["corrected_scope"] == "integration"
    assert strategy["canonical_global_state_owner"] == "project-global-state"
    assert strategy["required_marker"] == "closed/PASS-authoritative-rerun03"
    assert strategy["patch_files_total"] == 30
    assert strategy["modified_files_total"] == 25
    assert strategy["added_files_total"] == 5
    assert strategy["deleted_files_total"] == 0
    assert strategy["transactional_apply"] is True
    assert strategy["dry_run_first"] is True
    assert strategy["source_files_frozen_by_sha256"] is True
    assert strategy["repo_327_built_only_from_frozen_source_manifest"] is True
    assert strategy["official_repo_runtime_mutation_allowed"] is False
    assert strategy["expected_collection_total"] == 1986
    assert strategy["compatibility_tests_expected"] == 21
    assert strategy["functional_code_changed"] is False
    assert strategy["source_identity_gate"] == "git-canonical-blob-plus-physical-sha256-diagnostics"
    assert strategy["legacy_run06_root_allowed"] is False
    assert strategy["canonical_evaluation_root"] == r"D:\Projects\DevPilot_E2E_Evaluation"
    assert [item["version"] for item in strategy["history"]] == [
        "1.0.1",
        "1.0.2",
        "1.0.3",
        "1.0.4",
        "1.0.5",
        "2.0.0",
        "2.1.0",
        "2.1.1",
    ]
    assert strategy["runtime_allowlist"] == [
        ".devpilot/devpilot.db*",
        ".devpilot/agent_sessions/**",
        "outputs/**",
    ]
    assert manifest["historical_run"]["run_id"] == RUN_02
    assert manifest["historical_run"]["decision"] == "BLOCK/product-contract-evidence"
    assert manifest["historical_run"]["evidence_use"] == "FORENSIC-ONLY"
    assert manifest["authoritative_run"]["run_id"] == RUN_03
    assert manifest["authoritative_run"]["status"] == "CLOSED/PASS"
    assert manifest["authoritative_run"]["finalize_count"] == 1
    assert manifest["authoritative_run"]["s0"] == 0
    assert manifest["authoritative_run"]["s1"] == 0


def test_final_package_hashes_are_frozen() -> None:
    final = data("docs/post_h_eval_002_01_d_governance_closure_327_manifest.json")["final_evidence"]
    assert final["browser_acceptance_package"]["sha256"] == "1453fb9a10ba87908ebf77a36324054d6946da07fd28bade7399af5ef67b0d88"
    assert final["finalization_control_package"]["sha256"] == "e04a8c754cb8112a28ce79fe0135886690e7522b5642a54b65316c4ea4ed7cfb"
    assert final["independent_audit"]["sha256"] == "73f2a425af41725cbb26ecf5463c8b4a6b3d1d570f75d191d6e246e2775538df"
    assert final["independent_audit"]["decision"] == "PASS"
    assert final["independent_audit"]["sprint7_authorized"] is True


def test_canonical_documents_are_synchronized() -> None:
    # 01-D is a historical closure contract.  Freeze repo327/RERUN-03 only in
    # the artifacts that own that closure; do not force future active backlogs
    # to keep repo327 as their operational baseline after a governed successor.
    historical_paths = (
        "docs/backlogs/POST-H-EVAL-002-01_baseline_ui_acceptance.md",
        "docs/01_requirements/traceability_matrix.md",
    )
    for path in historical_paths:
        content = text(path)
        assert REPO_327 in content, path
        assert RUN_03 in content, path

    state = data(".devpilot/project_state.json")
    current_repo = state["post_h_eval_002_02_b_platform_baseline"]
    active_paths = (
        "README.md",
        "docs/00_product/POST-H-EVAL-002_end_to_end_product_pilot_roadmap.md",
        "docs/backlogs/POST-H-EVAL-002-02_sdlc_execution_traceability.md",
        "docs/backlogs/POST-H-EVAL-002-03_release_assessment_roadmap.md",
        "docs/05_operations/DevPilot_POST_H_EVAL_002_Piloto_Real_End_to_End_UI_First_Runbook.md",
        "docs/05_operations/runbook.md",
        "docs/release/CHANGELOG.md",
    )
    for path in active_paths:
        assert current_repo in text(path), path

    backlog = text("docs/backlogs/POST-H-EVAL-002-01_baseline_ui_acceptance.md")
    assert "closed/PASS-authoritative-rerun03" in backlog
    assert 'current_micro_sprint: "POST-H-EVAL-002-02-A"' in backlog


def test_source_registry_and_snapshot_include_closure_sources() -> None:
    registry = data(".devpilot/docs_governance/source_registry.json")
    ids = {item["doc_id"] for item in registry["documents"]}
    assert {
        "POST-H-EVAL-002-01-D-GOVERNANCE-CLOSURE-327-REPORT",
        "POST-H-EVAL-002-01-D-GOVERNANCE-CLOSURE-327-MANIFEST",
        "POST-H-EVAL-002-01-D-SPRINT7-IMPLEMENTATION-GUIDE",
        "POST-H-EVAL-002-01-D-GOVERNANCE-CLOSURE-327-TEST",
    } <= ids
    snapshot = registry["project_state_snapshot"]
    # The registry snapshot is intentionally refreshed as the program advances.
    # Freeze 01-D through its dedicated historical fields, not through mutable
    # current_repo/current_micro_sprint pointers.
    assert snapshot["post_h_eval_002_01_d_governance_repo"] == REPO_327
    assert snapshot["post_h_eval_002_01_d_closed"] is True
    assert snapshot["post_h_eval_002_01_d_run05b_rerun03_result"] == "CLOSED/PASS"


def test_tcr_v1_and_v2_register_closure_contract() -> None:
    v1 = data(".devpilot/testing/test_contract_registry.json")
    v2 = data(".devpilot/testing/test_contract_registry_v2.json")
    c1 = next(item for item in v1["contracts"] if item["contract_id"] == CONTRACT_ID)
    c2 = next(item for item in v2["contracts"] if item["contract_id"] == CONTRACT_ID)
    global_state_owners = [
        item for item in v1["contracts"] if item["scope"] == "global-state"
    ]
    assert [item["contract_id"] for item in global_state_owners] == [
        "project-global-state"
    ]
    assert c1["scope"] == "integration"
    assert c1["mutable_global_state_allowed"] is True
    assert c1["critical"] is True
    assert c1["network_allowed"] is False
    assert c1["external_api_allowed"] is False
    assert c2["domain"] == "governance.project_state"
    assert c2["test_type"] == "integration"
    assert c2["execution_profile"] == "release"
    assert c2["required_for_release"] is True
    assert c2["network_allowed"] is False
    assert c2["mutations_allowed"] is False
    assert "tests/test_post_h_034_closure_regression_reconciliation.py" in c1["test_files"]
    assert "tests/test_post_h_034_closure_regression_reconciliation.py" in c2["test_files"]
    assert "tests/test_post_h_034_closure_regression_reconciliation.py" in c1["watched_paths"]
    assert "tests/test_post_h_034_closure_regression_reconciliation.py" in c2["watched_paths"]


def test_release_candidate_snapshot_matches_project_state() -> None:
    state = data(".devpilot/project_state.json")
    criteria = data(".devpilot/release/local_release_candidate_criteria.json")
    # Release-candidate freshness follows the canonical platform successor, not the
    # immutable POST-H-EVAL-002 pilot checkpoint retained in post_h_eval_002_02_b_platform_baseline.
    assert criteria["expected_current_repo"] == state["current_repo"]
    assert state["post_h_eval_002_02_b_platform_baseline"].startswith("repo_DevPilot_Local_341_")
    assert state["post_h_eval_002_01_d_governance_repo"] == REPO_327
    assert criteria["expected_current_micro_sprint"] == state["current_micro_sprint"]
    assert criteria["expected_next_micro_sprint"] == state["next_micro_sprint"]



def test_closure_report_satisfies_registered_freshness_markers() -> None:
    criteria = data(".devpilot/release/local_release_candidate_criteria.json")
    item = next(
        evidence
        for evidence in criteria["evidence"]
        if evidence["evidence_id"]
        == "post-h-eval-002-01-d-governance-closure-327-report"
    )
    report = text(item["path"])
    missing = [
        marker for marker in item["required_markers"] if marker not in report
    ]
    assert missing == []


def test_all_release_candidate_evidence_contracts_pass_stdlib_preflight() -> None:
    script = ROOT / "tests/preflight_release_candidate_evidence_stdlib.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--root", str(ROOT), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert completed.returncode == 0, payload
    assert payload["decision"] == "PASS"
    criteria = data(".devpilot/release/local_release_candidate_criteria.json")
    assert payload["evidence_total"] == len(criteria["evidence"])
    assert payload["evidence_total"] >= 47
    assert payload["critical_stale_total"] == 0
    assert payload["critical_missing_total"] == 0
    assert payload["critical_invalid_total"] == 0
    assert payload["no_go_gates_passed"] is True


def test_sensitive_capabilities_remain_disabled() -> None:
    state = data(".devpilot/project_state.json")
    for key in (
        "network_used",
        "external_api_used",
        "connector_write_enabled",
        "plugin_execution_enabled",
        "remote_execution_enabled",
        "production_multiuser_enabled",
        "enterprise_ready_claimed",
        "saas_ready_claimed",
    ):
        assert state[key] is False
