from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".devpilot/project_state.json"


def _state() -> dict:
    return json.loads(STATE.read_text(encoding="utf-8"))


def test_08_activation_authority_is_repo397_and_successor_docs_are_materialized():
    state = _state()
    assert state["gsdlc_08_activation_source_repo"] == "repo_DevPilot_Local_397_FRX_V2_3_E_ONE_FULL_SAFE_PARALLEL_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip"
    assert state["gsdlc_08_activation_source_commit"] == "ba1a87adf7d7b17a2f41f1c5821b86a86b762877"
    assert state["gsdlc_08_activation_source_sha256"] == "109045dccb59fe235c60aac688dcee17e169dae174428df04fb3e1925dbff72a"
    for rel in [
        "DEVPL_FULL_REGRESSION_V2_3_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md",
        "DEVPL-GSDLC-08_planning_workbench_roadmap_backlog_sprints_v1_3_0_APPROVED_REBOUND.md",
        "00_PROMPT_DEVPL_GSDLC_08_ACTIVATION_REBIND_v1_0_0.md",
        "01_PROMPT_DEVPL_GSDLC_08_A_v1_0_0_APPROVED_REBOUND.md",
    ]:
        assert (ROOT / rel).is_file(), rel


def test_08_activation_preserves_historical_v23_backlog_and_uses_successor_closure():
    historical = (ROOT / "docs/backlogs/DEVPL_FULL_REGRESSION_V2_3_SAFE_PARALLELISM_BACKLOG_v1_4_0.md").read_text(encoding="utf-8")
    successor = (ROOT / "DEVPL_FULL_REGRESSION_V2_3_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md").read_text(encoding="utf-8")
    assert 'status: "approved"' in historical
    assert '`DEVPL-FULL-REGRESSION-V2-3 = CLOSED/PASS/WINDOWS-VALIDATED`' in successor
    sweep = json.loads((ROOT / "docs/audits/DEVPL_GSDLC_08_ACTIVATION_HISTORICAL_CONTRACT_SWEEP.json").read_text(encoding="utf-8"))
    assert sweep["status"] == "PASS"
    assert sweep["unclassified_total"] == 0


def test_08_activation_state_is_fail_closed_until_windows_pass():
    state = _state()
    status = state["gsdlc_08_activation_status"]
    assert status in {"IMPLEMENTED/PRE-WINDOWS", "CLOSED/PASS/WINDOWS-VALIDATED"}
    if status == "IMPLEMENTED/PRE-WINDOWS":
        assert state["current_repo"].startswith("repo_DevPilot_Local_397_")
        assert state["gsdlc_08_a_authorized"] is False
    else:
        assert state["current_repo"].startswith("repo_DevPilot_Local_398_")
        assert state["gsdlc_08_a_authorized"] is True


def test_08_activation_is_governance_only_and_consumes_no_full_or_browser():
    state = _state()
    report = json.loads((ROOT / "docs/audits/DEVPL_GSDLC_08_ACTIVATION_REBIND_REPORT.json").read_text(encoding="utf-8"))
    assert state["gsdlc_08_activation_functional_mutation"] is False
    assert state["gsdlc_08_activation_full_regression_runs"] == 0
    assert state["gsdlc_08_activation_browser_runs"] == 0
    assert report["src_changed_by_activation"] is False
    assert report["network_used"] is False
    assert report["external_api_used"] is False
