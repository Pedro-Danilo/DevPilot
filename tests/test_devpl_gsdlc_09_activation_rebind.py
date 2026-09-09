from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".devpilot/project_state.json"
REPO406 = "repo_DevPilot_Local_406_FRX_V2_4_B_EXECUTION_PROFILE_LOCK_WINDOWS_VALIDATED_CANDIDATE.zip"
COMMIT406 = "6b8a9a5feef65860826904444f651421abad282a"
SHA406 = "59c40713182b84655315773654e49adf95419ceb517ec9496929252fba33b191"
PROFILE_ID = "frx-v2.4-current"
PROFILE_SHA = "2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219"


def j(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_09_activation_rebinds_repo406_and_current_frx_profile() -> None:
    state = j(".devpilot/project_state.json")
    assert state["gsdlc_09_activation_source_repo"] == REPO406
    assert state["gsdlc_09_activation_source_commit"] == COMMIT406
    assert state["gsdlc_09_activation_source_sha256"] == SHA406
    assert state["gsdlc_09_frx_execution_profile_id"] == PROFILE_ID
    assert state["gsdlc_09_frx_execution_profile_sha256"] == PROFILE_SHA
    pointer = j(".devpilot/testing/full_regression_execution_profile_current.json")
    assert pointer["current_profile_id"] == PROFILE_ID
    assert pointer["current_profile_sha256"] == PROFILE_SHA


def test_09_activation_preserves_gsdlc08_and_requires_closed_frx_v24() -> None:
    state = j(".devpilot/project_state.json")
    assert state["gsdlc_08_e_status"].startswith("CLOSED/PASS/WINDOWS-VALIDATED")
    assert state["frx_v2_4_status"] == "CLOSED/PASS/WINDOWS-VALIDATED"
    assert state["frx_v2_4_b_status"] == "CLOSED/PASS/WINDOWS-VALIDATED"
    report = j("docs/audits/DEVPL_GSDLC_09_ACTIVATION_REBIND_REPORT.json")
    assert report["ancestry"]["status"] == "PASS/WINDOWS-EVIDENCE"
    assert report["ancestry"]["base_repo404_commit"] == "c0347423b78c67ed93f9eb4a2af39e0411b1d22f"
    assert report["ancestry"]["frx_v2_4_b_close_commit"] == COMMIT406


def test_09_activation_current_pointers_are_rebound_and_functional_source_is_untouched() -> None:
    state = j(".devpilot/project_state.json")
    assert state["gsdlc_current_backlog"] == "DEVPL-GSDLC-09"
    # Activation intent is frozen in the activation report; mutable project state is expected to advance through 09-B..E.
    report = j("docs/audits/DEVPL_GSDLC_09_ACTIVATION_REBIND_REPORT.json")
    assert report["next_micro_sprint"] == "DEVPL-GSDLC-09-A"
    assert state["gsdlc_09_activation_functional_mutation"] is False
    assert state["gsdlc_09_activation_full_regression_runs"] == 0
    assert state["gsdlc_09_activation_browser_runs"] == 0
    status = state["gsdlc_09_activation_status"]
    assert status in {"IMPLEMENTED/PRE-WINDOWS", "CLOSED/PASS/WINDOWS-VALIDATED"}
    if status == "IMPLEMENTED/PRE-WINDOWS":
        assert state["current_repo"] == REPO406
        assert state["gsdlc_09_a_authorized"] is False
    else:
        report = j("docs/audits/DEVPL_GSDLC_09_ACTIVATION_REBIND_REPORT.json")
        assert report["successor_repo"].startswith("repo_DevPilot_Local_407_")
        current_number = int(state["current_repo"].split("_")[3])
        assert current_number >= 407
        assert state["gsdlc_09_a_authorized"] is True


def test_09_activation_rebound_artifacts_and_historical_sweep_are_materialized() -> None:
    for rel in [
        "DEVPL-GSDLC-09_story_and_coding_workbench_v1_4_1_APPROVED_REBOUND_REPO406.md",
        "00_PROMPT_DEVPL_GSDLC_09_ACTIVATION_REBIND_v1_0_1_REBOUND_REPO406.md",
        "01_PROMPT_DEVPL_GSDLC_09_A_v1_0_1_REBOUND_REPO406.md",
        "docs/audits/DEVPL_GSDLC_09_ACTIVATION_OWNER_ADJUDICATION_PROPOSAL.md",
    ]:
        assert (ROOT / rel).is_file(), rel
    sweep = j("docs/audits/DEVPL_GSDLC_09_ACTIVATION_HISTORICAL_CONTRACT_SWEEP.json")
    assert sweep["status"] == "PASS"
    assert sweep["unclassified_total"] == 0
    assert sweep["historical_current_leakage_total"] == 0
    assert {row["authority"] for row in sweep["classifications"]} >= {
        "historical-freeze", "current-active", "successor-needed", "runtime-ephemeral"
    }


def test_09_activation_report_is_governance_only_and_zero_cost_runtime() -> None:
    report = j("docs/audits/DEVPL_GSDLC_09_ACTIVATION_REBIND_REPORT.json")
    assert report["functional_mutation"] is False
    assert report["src_changed_by_activation"] is False
    assert report["full_regression_runs"] == 0
    assert report["browser_runs"] == 0
    assert report["network_used"] is False
    assert report["external_api_used"] is False
