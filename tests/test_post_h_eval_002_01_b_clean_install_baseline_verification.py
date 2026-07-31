from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

def test_01_b_state_closes_and_authorizes_01_c() -> None:
    state = _json(".devpilot/project_state.json")
    assert state["current_repo"] in {
        "repo_DevPilot_Local_320_POST_H_EVAL_002_01_B.zip",
        "repo_DevPilot_Local_321_POST_H_EVAL_002_01_C.zip",
        "repo_DevPilot_Local_322_POST_H_EVAL_002_01_D_ACCEPTANCE_READY.zip",
        "repo_DevPilot_Local_323_POST_H_EVAL_002_01_D_UI_ACCEPTANCE_FIX.zip",
        "repo_DevPilot_Local_324_POST_H_EVAL_002_01_D_RUNTIME_CORRECTIVE.zip", "repo_DevPilot_Local_325_POST_H_EVAL_002_01_D_BROWSER_ACCEPTANCE_CORRECTIVE.zip", "repo_DevPilot_Local_326_POST_H_EVAL_002_01_D_RUN05B_INTEGRAL_CORRECTIVE.zip", "repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip",
    }
    assert state["current_micro_sprint"] in {
        "POST-H-EVAL-002-01-C",
        "POST-H-EVAL-002-01-D",
        "POST-H-EVAL-002-02-A",
    }
    assert state["next_micro_sprint"] in {
        "POST-H-EVAL-002-01-D",
        "POST-H-EVAL-002-02-A",
        "POST-H-EVAL-002-02-B",
    }
    assert state["post_h_eval_002_01_b_closed"] is True
    assert state["post_h_eval_002_01_b_status"] == "closed/PASS-WITH-GAPS"
    assert state["post_h_eval_002_01_b_s0_open"] == 0
    assert state["post_h_eval_002_01_b_s1_open"] == 0
    assert state["post_h_eval_002_01_b_next_authorized"] == "POST-H-EVAL-002-01-C"

def test_01_b_evidence_hashes_and_results_are_frozen() -> None:
    manifest = _json("docs/post_h_eval_002_01_b_manifest.json")
    assert manifest["decision"] == "PASS-WITH-GAPS"
    assert manifest["evidence"]["final_package"]["sha256"] == "83174a229e93bff2590e19896ea0ba9c0848827e0d37e7b5243580888e6f173f"
    assert manifest["evidence"]["priority_package"]["sha256"] == "ac41871b57ec681146fa501ef57083de955d9ffb1dda1ffb8fb7edd9893080dd"
    assert manifest["results"]["commands_passed"] == manifest["results"]["commands_total"] == 17
    assert manifest["results"]["secret_findings"] == 0
    assert manifest["results"]["path_overlaps"] == 0

def test_01_b_preserves_freeze_and_does_not_claim_api_ui_startup() -> None:
    state = _json(".devpilot/project_state.json")
    assert state["source_repo"] == "repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip"
    assert state["post_h_eval_002_01_b_platform_installed"] is True
    assert state["post_h_eval_002_01_b_api_started"] is False
    assert state["post_h_eval_002_01_b_ui_started"] is False
    assert state["post_h_eval_002_01_b_workspace_created"] is False
    for key in ("connector_write_enabled", "plugin_execution_enabled", "remote_execution_enabled", "production_multiuser_enabled", "enterprise_ready_claimed", "saas_ready_claimed", "external_api_allowed"):
        assert state[key] is False

def test_01_b_governance_docs_are_synchronized() -> None:
    roadmap = _text("docs/00_product/POST-H-EVAL-002_end_to_end_product_pilot_roadmap.md")
    backlog = _text("docs/backlogs/POST-H-EVAL-002-01_baseline_ui_acceptance.md")
    audit = _text("docs/audits/post_h_eval_002_01_b_clean_install_baseline_verification_report.md")
    assert "POST-H-EVAL-002-01-A/B" in roadmap or "01-B" in backlog
    assert 'current_micro_sprint: "POST-H-EVAL-002-02-A"' in backlog
    assert "`PASS-WITH-GAPS`" in audit
    registry = _json(".devpilot/docs_governance/source_registry.json")
    assert registry["project_state_snapshot"]["post_h_eval_002_01_b_evidence_package_sha256"] == "83174a229e93bff2590e19896ea0ba9c0848827e0d37e7b5243580888e6f173f"
