from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ = ROOT / "docs/01_requirements/requirements_specification.md"
TRACE = ROOT / "docs/01_requirements/traceability_matrix.md"
VISION = ROOT / "docs/00_product/product_vision.md"
STATE = ROOT / ".devpilot/project_state.json"

EXPECTED_IDS = ['GSDLC-FR-001', 'GSDLC-FR-002', 'GSDLC-FR-003', 'GSDLC-SEC-001', 'GSDLC-SEC-002', 'GSDLC-FR-004', 'GSDLC-FR-005', 'GSDLC-SEC-003', 'GSDLC-FR-006', 'GSDLC-FR-007', 'GSDLC-FR-008', 'GSDLC-GOV-001', 'GSDLC-GOV-002', 'GSDLC-FR-009', 'GSDLC-NFR-001', 'GSDLC-FR-010', 'GSDLC-NFR-002', 'GSDLC-FR-011', 'GSDLC-FR-012', 'GSDLC-GOV-003', 'GSDLC-FR-013', 'GSDLC-FR-014', 'GSDLC-FR-015', 'GSDLC-FR-016', 'GSDLC-FR-017', 'GSDLC-GOV-004', 'GSDLC-FR-018', 'GSDLC-NFR-003', 'GSDLC-UX-001', 'GSDLC-GOV-005', 'GSDLC-GOV-006']


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_gsdlc_00_b_product_vision_declares_ui_complete_successor_without_runtime_claim() -> None:
    text = _text(VISION)
    assert "UI-complete normal journey" in text
    assert "PowerShell required by normal user = 0" in text
    assert "External operator project writes = 0" in text
    assert "runtime correspondiente permanece `planned`" in text
    assert "CLI/API = expert automation / CI / diagnostics" in text


def test_gsdlc_00_b_requirements_are_all_stable_planned_owned_and_testable() -> None:
    text = _text(REQ)
    for rid in EXPECTED_IDS:
        rows = [line for line in text.splitlines() if line.startswith(f"| {rid} |") ]
        assert len(rows) == 1, rid
        cells = [cell.strip() for cell in rows[0].strip("|").split("|")]
        assert len(cells) == 11, (rid, len(cells))
        assert cells[6].startswith("DEVPL-GSDLC-"), rid
        assert cells[7].startswith("M"), rid
        assert cells[8], rid
        assert cells[9], rid
        assert cells[10] == "planned", rid
    assert "gsdlc_orphan_requirements: 0" in text


def test_gsdlc_00_b_traceability_covers_every_successor_requirement_once() -> None:
    text = _text(TRACE)
    for rid in EXPECTED_IDS:
        assert len([line for line in text.splitlines() if line.startswith(f"| {rid} |")]) == 1, rid
    assert f"gsdlc_requirements_total: {len(EXPECTED_IDS)}" in text
    assert f"gsdlc_requirements_traced: {len(EXPECTED_IDS)}" in text
    assert "gsdlc_traceability_coverage: 100%" in text
    assert "gsdlc_orphan_requirements: 0" in text


def test_gsdlc_00_b_preserves_local_first_and_historical_boundaries() -> None:
    req = _text(REQ)
    assert "sin LLM, sin API key y sin red externa" in req
    assert "enterprise IAM, tenancy, SSO" in req
    assert "arbitrary shell" in req
    assert "LLM/agentes nunca deben decidir PASS/BLOCK" in req


def test_gsdlc_00_b_project_state_advances_program_only_and_preserves_pilot_pause() -> None:
    state = json.loads(_text(STATE))
    assert state["gsdlc_00_b_status"] == "closed/PASS"
    assert state["gsdlc_00_b_program_status_at_close"] == "active/00-b"
    assert state["gsdlc_00_b_current_micro_sprint_at_close"] == "DEVPL-GSDLC-00-B"
    assert state["gsdlc_00_b_next_micro_sprint_at_close"] == "DEVPL-GSDLC-00-C"
    assert state["gsdlc_program_status"] in {"active/00-b", "active/00-c"}
    assert state["gsdlc_00_a_status"] == "closed/PASS"
    assert state["post_h_eval_002_execution_status"] == "paused-before-02-b"
    assert state["post_h_eval_002_02_b_executed"] is False
    assert state["gsdlc_runtime_implemented"] is False
    assert state["gsdlc_auth_runtime_enabled"] is False
    assert state["gsdlc_provider_runtime_enabled"] is False
    assert state["gsdlc_filesystem_write_enabled"] is False
    assert state["gsdlc_00_b_requirements_total"] == len(EXPECTED_IDS)
    assert state["gsdlc_00_b_orphan_requirements"] == 0


def test_gsdlc_00_b_machine_readable_delta_is_complete_and_no_orphans() -> None:
    delta = json.loads(_text(ROOT / "docs/audits/devpl_gsdlc_00_b_traceability_delta.json"))
    assert delta["requirements_total"] == len(EXPECTED_IDS)
    assert delta["requirements_traced"] == len(EXPECTED_IDS)
    assert delta["coverage_percent"] == 100
    assert delta["orphans"] == []
    assert {e["requirement_id"] for e in delta["entries"]} == set(EXPECTED_IDS)


def test_gsdlc_00_b_historical_sweep_scopes_instead_of_rewriting_history() -> None:
    sweep = json.loads(_text(ROOT / "docs/audits/devpl_gsdlc_00_b_historical_contract_sweep.json"))
    classes = {item["classification"] for item in sweep["classifications"]}
    assert "historical-freeze" in classes
    assert "current-active" in classes
    assert "successor-needed" in classes
    assert sweep["runtime_source_changed"] is False
    assert sweep["network_used"] is False
    assert sweep["external_api_used"] is False
