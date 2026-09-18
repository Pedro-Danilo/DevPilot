from __future__ import annotations

import json
import re
from pathlib import Path

from devpilot_core.testing.project_state_progress import post_h_progress_rank

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_ux_p0_a_rebind_preserves_gsdlc_closure_and_defers_gsdlc13() -> None:
    state = load_json(".devpilot/project_state.json")
    assert state["gsdlc_status"] == "CLOSED/PASS/WINDOWS-VALIDATED"
    assert state["gsdlc_12_status"] == "CLOSED/PASS/WINDOWS-VALIDATED"
    assert state["gsdlc_13_authorized"] is True
    assert state["gsdlc_13_execution_deferred_by"] == "DEVPL-UX-P0/PRE-PILOT-PRODUCTIZATION"
    assert state["current_phase"] == "DEVPL-UX-P0"
    assert state["current_micro_sprint"] in {"DEVPL-UX-P0-A","DEVPL-UX-P0-B","DEVPL-UX-P0-C","DEVPL-UX-P0-D","DEVPL-UX-P0-E"}
    assert state["ux_p0_a_full_regression_runs"] == 0
    assert state["ux_p0_full_regression_budget"] in {"0/1-RESERVED-FOR-UX-P0-E", "1/1-CONSUMED-BY-UX-P0-E"}
    assert post_h_progress_rank("DEVPL-UX-P0-A") > post_h_progress_rank("FRX-v2.4-B")
    assert post_h_progress_rank("DEVPL-UX-P0-B") > post_h_progress_rank("DEVPL-UX-P0-A")


def test_frontend_identity_and_design_tokens_are_current_without_route_authority_change() -> None:
    package = load_json("ui/web/package.json")
    assert re.fullmatch(r"0\.\d+\.0-ux-p0-[a-e](?:-rc)?", package["version"])
    state = load_json(".devpilot/project_state.json")
    assert package["devpilot"]["currentSprint"] == state["current_micro_sprint"]
    assert package["devpilot"]["uxP0RoutePathsChanged"] is False
    assert package["devpilot"]["uxP0ServerAuthorityChanged"] is False
    tokens = (ROOT / "ui/web/src/design-tokens.css").read_text(encoding="utf-8")
    styles = (ROOT / "ui/web/src/styles.css").read_text(encoding="utf-8")
    assert "--dp-state-block-bg:" in tokens
    assert "--dp-color-focus:" in tokens
    assert styles.startswith('@import "./design-tokens.css";')
    assert "var(--dp-color-action-primary)" in styles


def test_owner_approved_transition_and_strategy_are_materialized() -> None:
    for relative in (
        "docs/00_product/DEVPL_POST_GSDLC_TRANSITION_DECISION_v1_0_0_APPROVED.md",
        "docs/00_product/DEVPL_UI_UX_PRODUCTIZATION_STRATEGY_v1_0_0_APPROVED.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert 'status: "approved"' in text
        assert 'approval: "approved_by_owner"' in text


def test_ux_p0_a_current_contract_and_rc_schema_are_successor_aware() -> None:
    state = load_json(".devpilot/project_state.json")
    criteria = load_json(".devpilot/release/local_release_candidate_criteria.json")
    assert criteria["expected_current_micro_sprint"] == state["current_micro_sprint"]
    if state["current_micro_sprint"] == "DEVPL-UX-P0-A":
        assert criteria["expected_next_micro_sprint"] == "DEVPL-UX-P0-B"
    else:
        assert criteria["expected_next_micro_sprint"] in {"DEVPL-UX-P0-C","DEVPL-UX-P0-D","DEVPL-UX-P0-E","DEVPL-GSDLC-13"}
    for registry in (
        ".devpilot/testing/test_contract_registry.json",
        ".devpilot/testing/test_contract_registry_v2.json",
    ):
        payload = load_json(registry)
        ids = {item["contract_id"] for item in payload["contracts"]}
        assert "devpl-ux-p0-a-authority-design-system-foundation" in ids
        assert payload["contracts_total"] == len(payload["contracts"])
    schema = load_json("docs/schemas/local_release_candidate_criteria.schema.json")
    pattern = schema["properties"]["expected_current_micro_sprint"]["pattern"]
    assert "DEVPL-UX-P" in pattern
