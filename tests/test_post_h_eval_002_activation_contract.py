from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.testing.project_state_progress import post_h_progress_rank

ROOT = Path(__file__).resolve().parents[1]

SOURCE_REPO = "repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip"
TARGET_REPO = "repo_DevPilot_Local_319_POST_H_EVAL_002_01_A.zip"
CURRENT_MICRO = "POST-H-EVAL-002-01-B"
NEXT_MICRO = "POST-H-EVAL-002-01-C"
CONTRACT_ID = "post-h-eval-002-activation-governance"

CANONICAL_DOCS = {
    "DEVPL-POST-H-EVAL-002-E2E-PILOT-UI-FIRST-RUNBOOK": "docs/05_operations/DevPilot_POST_H_EVAL_002_Piloto_Real_End_to_End_UI_First_Runbook.md",
    "DEVPL-POST-H-EVAL-002-PILOT-ROADMAP": "docs/00_product/POST-H-EVAL-002_end_to_end_product_pilot_roadmap.md",
    "DEVPL-POST-H-EVAL-002-01-BACKLOG": "docs/backlogs/POST-H-EVAL-002-01_baseline_ui_acceptance.md",
    "DEVPL-POST-H-EVAL-002-02-BACKLOG": "docs/backlogs/POST-H-EVAL-002-02_sdlc_execution_traceability.md",
    "DEVPL-POST-H-EVAL-002-03-BACKLOG": "docs/backlogs/POST-H-EVAL-002-03_release_assessment_roadmap.md",
}


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")



def test_project_state_progress_rank_supports_evaluation_namespace() -> None:
    assert post_h_progress_rank("POST-H-034") == 34
    assert post_h_progress_rank("POST-H-034-CLOSURE") == 34
    assert post_h_progress_rank("POST-H-EVAL-002") > post_h_progress_rank("POST-H-034")
    assert post_h_progress_rank("POST-H-EVAL-002-01-A") == post_h_progress_rank("POST-H-EVAL-002")


def test_post_h_eval_002_documents_are_approved_and_cross_linked() -> None:
    for doc_id, path in CANONICAL_DOCS.items():
        text = _text(path)
        assert f'doc_id: "{doc_id}"' in text
        assert 'status: "approved"' in text
        assert 'approval: "approved_by_owner"' in text
        assert "POST-H-EVAL-002" in text

    roadmap = _text(CANONICAL_DOCS["DEVPL-POST-H-EVAL-002-PILOT-ROADMAP"])
    assert "POST-H-EVAL-002-01-A" in roadmap
    for path in list(CANONICAL_DOCS.values())[2:]:
        assert Path(path).name in roadmap

    # Every active source identifies current governance repo and frozen executable baseline.
    for path in CANONICAL_DOCS.values():
        text = _text(path)
        assert TARGET_REPO in text
        assert "repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip" in text


def test_post_h_eval_002_backlog_01_has_no_historical_operational_baseline_drift() -> None:
    backlog = _text(CANONICAL_DOCS["DEVPL-POST-H-EVAL-002-01-BACKLOG"])
    forbidden = (
        "calcular SHA-256 del ZIP 315",
        "instalar DevPilot desde el ZIP 315",
        "registrar commit fuente `665fa37`",
    )
    for phrase in forbidden:
        assert phrase not in backlog
    assert "calcular SHA-256 del ZIP 318" in backlog
    assert "git rev-parse HEAD" in backlog
    assert "instalar DevPilot desde el ZIP 318" in backlog


def test_post_h_eval_002_sources_are_canonical_in_documentation_registry() -> None:
    registry = _json(".devpilot/docs_governance/source_registry.json")
    by_id = {item["doc_id"]: item for item in registry["documents"]}
    for doc_id, path in CANONICAL_DOCS.items():
        item = by_id[doc_id]
        assert item["path"] == path
        assert item["classification"] == "source-of-truth"
        assert item["status_required"] == "approved"
        assert item["criticality"] == "P0"
        assert "tests/test_post_h_eval_002_activation_contract.py" in item["required_tests"]
        assert item["lifecycle"] == "active"
    assert registry["last_registered_sprint"] in {"POST-H-EVAL-002", "POST-H-EVAL-002-01-A"}


def test_post_h_eval_002_test_contract_is_registered_in_v1_and_v2() -> None:
    v1 = _json(".devpilot/testing/test_contract_registry.json")
    v2 = _json(".devpilot/testing/test_contract_registry_v2.json")
    v1_contract = next(item for item in v1["contracts"] if item["contract_id"] == CONTRACT_ID)
    v2_contract = next(item for item in v2["contracts"] if item["contract_id"] == CONTRACT_ID)
    assert v1_contract["critical"] is True
    assert v1_contract["mutable_global_state_allowed"] is False
    assert v2_contract["domain"] == "governance.project_state"
    assert v2_contract["execution_profile"] == "release"
    assert v2_contract["network_allowed"] is False
    assert v2_contract["external_api_allowed"] is False
    assert v2_contract["mutations_allowed"] is False


def test_project_state_activates_eval_without_reopening_post_h_034() -> None:
    state = _json(".devpilot/project_state.json")
    assert state["last_completed_sprint"] == "POST-H-034"
    assert state["post_h_034_closed"] is True
    assert state["post_h_034_closure_status"] == "closed/full-regression-pass"
    assert state["current_phase"] == "POST-H-EVAL-002"
    assert state["next_sprint"] == "POST-H-EVAL-002"
    assert state["source_repo"] == SOURCE_REPO
    assert state["current_repo"] == TARGET_REPO
    assert state["current_micro_sprint"] == CURRENT_MICRO
    assert state["next_micro_sprint"] == NEXT_MICRO
    assert state["next_backlog_planned"] is True
    assert state["post_h_eval_002_activated"] is True
    assert state["post_h_eval_002_status"] == "approved/active-evaluation"


def test_rc_criteria_and_operator_docs_follow_activation_state() -> None:
    state = _json(".devpilot/project_state.json")
    criteria = _json(".devpilot/release/local_release_candidate_criteria.json")
    assert criteria["expected_source_repo"] == state["source_repo"]
    assert criteria["expected_current_repo"] == state["current_repo"]
    assert criteria["expected_current_micro_sprint"] == state["current_micro_sprint"]
    assert criteria["expected_next_micro_sprint"] == state["next_micro_sprint"]

    readme = _text("README.md")
    runbook = _text("docs/05_operations/runbook.md")
    changelog = _text("docs/release/CHANGELOG.md")
    for text in (readme, runbook, changelog):
        assert "POST-H-EVAL-002" in text
        assert TARGET_REPO in text


def test_sensitive_capability_no_go_flags_remain_disabled() -> None:
    state = _json(".devpilot/project_state.json")
    for key in (
        "connector_write_enabled",
        "plugin_execution_enabled",
        "remote_execution_enabled",
        "production_multiuser_enabled",
        "enterprise_ready_claimed",
        "saas_ready_claimed",
        "external_api_allowed",
    ):
        assert state[key] is False
