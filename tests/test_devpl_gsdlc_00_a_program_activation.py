from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO341 = "repo_DevPilot_Local_341_POST_H_EVAL_002_PILOT_TRANSITION_REBIND.zip"
SHA341 = "e28cd2bae08d099a2b62c4869c83b6e5a647f3f780ca1572727b7c80f6eeea3b"
COMMIT341 = "cff43e8d992ff6139bd13bb1809ce4d497ae0952"

def j(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def t(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

def test_gsdlc_00_a_program_is_active_without_overclaiming_runtime() -> None:
    state=j(".devpilot/project_state.json")
    assert state["gsdlc_program_id"] == "DEVPL-GSDLC"
    assert state["gsdlc_00_a_program_status_at_close"] == "active/00-a"
    assert state["gsdlc_00_a_current_micro_sprint_at_close"] == "DEVPL-GSDLC-00-A"
    assert state["gsdlc_program_status"] in {"active/00-a", "active/00-b"}
    assert state["gsdlc_00_a_next_micro_sprint_candidate_at_close"] == "DEVPL-GSDLC-00-B"
    assert state["gsdlc_current_micro_sprint"] in {"DEVPL-GSDLC-00-A", "DEVPL-GSDLC-00-B"}
    assert state["gsdlc_next_micro_sprint"] in {"DEVPL-GSDLC-00-B", "DEVPL-GSDLC-00-C"}
    assert state["gsdlc_r01_a_authorized"] is True
    assert state["gsdlc_runtime_implemented"] is False
    assert state["gsdlc_auth_runtime_enabled"] is False
    assert state["gsdlc_provider_runtime_enabled"] is False
    assert state["gsdlc_filesystem_write_enabled"] is False

def test_repo341_is_immutable_parent_and_pilot_is_paused_before_02_b() -> None:
    state=j(".devpilot/project_state.json")
    parent=j(".devpilot/gsdlc/repo341_parent_manifest.json")
    assert parent["artifact_name"] == REPO341
    assert parent["sha256"] == SHA341
    assert parent["git_commit"] == COMMIT341
    assert parent["source_rewrite_allowed"] is False
    assert parent["historical_evidence_rewrite_allowed"] is False
    assert state["gsdlc_parent_immutable"] is True
    assert state["post_h_eval_002_status"] == "approved/active-evaluation"
    assert state["post_h_eval_002_execution_status"] == "paused-before-02-b"
    assert state["post_h_eval_002_02_b_execution_status"] == "PAUSED_BEFORE_EXECUTION"
    assert state["post_h_eval_002_02_b_executed"] is False
    assert state["post_h_eval_002_02_b_reference_oracle_only"] is True
    assert state["post_h_eval_002_resume_authority"] == "DEVPL-GSDLC-13"
    assert state["post_h_eval_002_02_a_closed"] is True
    assert state["post_h_eval_002_02_a_workspace_commit"] == "a10d97f425c31300860de7ef5a3c9fd82d6d6f59"
    assert state["gsdlc_00_a_pilot_workspace_mutated"] is False

def test_gsdlc_canonical_sources_are_registered_and_owner_approved_scope_is_preserved() -> None:
    registry=j(".devpilot/docs_governance/source_registry.json")
    ids={d["doc_id"]: d for d in registry["documents"]}
    expected={
        "DEVPL-GSDLC-PRODUCT-EVOLUTION-ROADMAP",
        "DEVPL-GSDLC-00",
        "DEVPL-GSDLC-PROGRAM-CHARTER",
        "DEVPL-POST-H-EVAL-002-PILOT-PAUSE-DECISION",
        "DEVPL-GSDLC-REPO341-PARENT-MANIFEST",
        "DEVPL-GSDLC-LEGACY-PRESERVATION-MATRIX",
        "DEVPL-GSDLC-00-A-HISTORICAL-CONTRACT-SWEEP",
    }
    assert expected <= set(ids)
    assert registry["last_registered_sprint"] == "POST-H-EVAL-002-UI-OPERATIONAL-CONSOLE-FINAL-CLOSURE"
    assert registry["gsdlc_00_a_last_registered_micro_sprint_at_close"] == "DEVPL-GSDLC-00-A"
    assert registry["gsdlc_00_a_program_status_at_close"] == "active/00-a"
    assert registry["gsdlc_last_registered_micro_sprint"] in {"DEVPL-GSDLC-00-A", "DEVPL-GSDLC-00-B"}
    assert 'status: "approved"' in t("docs/00_product/DEVPL_GSDLC_product_evolution_roadmap.md")
    assert 'approval: "approved_by_owner"' in t("docs/00_product/DEVPL_GSDLC_product_evolution_roadmap.md")
    assert 'status: "approved"' in t("docs/backlogs/DEVPL-GSDLC-00_program_activation_rebaseline_and_pilot_pause.md")

def test_active_pilot_docs_expose_pause_and_preserve_repo341() -> None:
    for rel in (
        "README.md",
        "docs/00_product/POST-H-EVAL-002_end_to_end_product_pilot_roadmap.md",
        "docs/backlogs/POST-H-EVAL-002-02_sdlc_execution_traceability.md",
        "docs/05_operations/DevPilot_POST_H_EVAL_002_Piloto_Real_End_to_End_UI_First_Runbook.md",
        "docs/05_operations/runbook.md",
        "docs/release/CHANGELOG.md",
    ):
        text=t(rel)
        assert "DEVPL-GSDLC" in text, rel
        assert REPO341 in text, rel
    assert "PAUSED_BEFORE_02_B" in t("docs/05_operations/runbook.md")

def test_no_go_and_network_flags_remain_false() -> None:
    state=j(".devpilot/project_state.json")
    for key in (
        "network_used", "external_api_used", "connector_write_enabled",
        "plugin_execution_enabled", "remote_execution_enabled",
        "multiuser_auth_enabled", "multiuser_runtime_enabled",
        "filesystem_write_allowed", "cloud_deployment_enabled",
    ):
        assert state[key] is False, key
    assert state["gsdlc_00_a_network_used"] is False
    assert state["gsdlc_00_a_external_api_used"] is False

def test_historical_contract_sweep_has_no_test_rewrite_to_pass() -> None:
    sweep=j("docs/audits/devpl_gsdlc_00_a_historical_contract_sweep.json")
    assert sweep["summary"]["tests_rewritten_only_to_pass"] == 0
    assert {i["classification"] for i in sweep["items"]} <= {"historical-freeze","current-active","successor-needed","deprecated-after-proof"}
    assert any(i["classification"] == "successor-needed" for i in sweep["items"])
