from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _read_json(path: str) -> dict:
    return json.loads(_read(path))


def test_post_h_020_e_runbook_and_disclaimers_exist_and_define_statuses() -> None:
    runbook = _read("docs/05_operations/compliance_mapping_runbook.md").lower()
    disclaimers = _read("docs/03_security/compliance_mapping_disclaimers.md").lower()

    for text in (runbook, disclaimers):
        assert "certification_claimed=false" in text
        assert "legal_advice_claimed=false" in text
        assert "no constituyen certificación compliance" in text or "no certificación" in text
        assert "no constituyen" in text or "no asesoría legal" in text

    for status in ("mapped", "partial", "gap", "not-applicable"):
        assert status in runbook
        assert status in disclaimers

    assert "missing evidence" in runbook
    assert "no se deben borrar gaps" in runbook


def test_post_h_020_e_documents_do_not_overclaim_certification() -> None:
    paths = [
        "docs/05_operations/compliance_mapping_runbook.md",
        "docs/audits/post_h_020_e_compliance_mapping_closure_report.md",
        "docs/backlogs/POST-H-020_compliance_mapping_packs.md",
        "docs/POST-H-020_compliance_mapping_packs.md",
    ]
    forbidden = [
        "certified compliant",
        "compliance certified",
        "legally compliant",
        "external audit completed",
        "guaranteed compliance",
        "regulatory approval",
        "third-party attestation completed",
    ]
    for path in paths:
        lowered = _read(path).lower()
        for phrase in forbidden:
            assert phrase not in lowered, f"{phrase!r} must not appear in {path}"

    disclaimers = _read("docs/03_security/compliance_mapping_disclaimers.md").lower()
    assert "lenguaje prohibido" in disclaimers
    for phrase in forbidden:
        assert phrase in disclaimers


def test_post_h_020_e_backlog_is_closed_and_project_state_advances() -> None:
    backlog = _read("docs/backlogs/POST-H-020_compliance_mapping_packs.md")
    implementation = _read("docs/POST-H-020_compliance_mapping_packs.md")
    state = _read_json(".devpilot/project_state.json")

    assert 'implementation_status: "closed"' in backlog
    assert 'implementation_status: "closed"' in implementation
    assert 'current_micro_sprint: "POST-H-020-E"' in backlog
    assert state["last_completed_sprint"] == "POST-H-020"
    assert state["next_sprint"] == "POST-H-021"
    assert state["current_micro_sprint"] == "POST-H-020-E"
    assert state["next_micro_sprint"] == "POST-H-021"
    assert any("POST-H-020 closes Compliance mapping packs" in note for note in state["notes"])


def test_post_h_020_e_tcr_v2_contracts_have_schema_valid_classification_status() -> None:
    registry = _read_json(".devpilot/testing/test_contract_registry_v2.json")
    allowed = {"explicit", "inferred", "needs-review"}
    contracts = registry["contracts"]
    by_id = {item["contract_id"]: item for item in contracts}

    assert all(item.get("classification_status") in allowed for item in contracts)
    assert by_id["post-h-020-compliance-evidence-report"]["classification_status"] == "explicit"
    assert by_id["post-h-020-compliance-mapping-quality-gate"]["classification_status"] == "explicit"
    assert "post-h-020-compliance-runbook-disclaimers" in by_id
