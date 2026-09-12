from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_11d_current_authority_is_repo423_and_full_is_reserved_for_11e():
    state = _json(".devpilot/project_state.json")
    registry = _json(".devpilot/docs_governance/source_registry.json")
    expected = "repo_DevPilot_Local_423_DEVPL_GSDLC_11_C_INSTALL_UPGRADE_ROLLBACK_WINDOWS_VALIDATED_CANDIDATE.zip"
    assert state["gsdlc_11_c_status"] == "CLOSED/PASS/WINDOWS-VALIDATED"
    assert state["gsdlc_11_d_source_repo"] == expected
    assert registry["gsdlc_11_d_execution_source_repo"] == expected
    assert registry["gsdlc_11_d_execution_source_sha256"] == "836c9bb2e24f547fc3bd6a61235b938557139a8730010ea5208acaf695f23099"
    assert state["gsdlc_11_d_full_regression_runs"] == 0
    assert state["gsdlc_11_full_regression_budget_consumed"] == 0
    assert state["gsdlc_11_full_regression_reserved_for"] == "DEVPL-GSDLC-11-E"


def test_11d_api_ui_and_rbac_contracts_cover_sensitive_tag_actions():
    api = _json(".devpilot/interfaces/api_route_contract_registry.json")
    ui = _json(".devpilot/interfaces/ui_route_contract_registry.json")
    rbac = _json(".devpilot/identity/server_rbac_policy_catalog.json")
    api_text = json.dumps(api, sort_keys=True)
    ui_text = json.dumps(ui, sort_keys=True)
    rbac_text = json.dumps(rbac, sort_keys=True)
    for path in [
        "/api/v1/release/metadata",
        "/api/v1/release/metadata/prepare",
        "/api/v1/release/metadata/tag-plan",
        "/api/v1/release/metadata/approve",
        "/api/v1/release/metadata/tag/execute",
    ]:
        assert path in api_text
    assert "/release/metadata" in ui_text
    assert "ui.release-metadata" in ui_text
    assert "release.metadata.tag.execute" in rbac_text
    assert "release-manager" in rbac_text
    assert "owner" in rbac_text


def test_11d_hca_and_contract_reconciliation_are_pass_without_historical_rewrite():
    hca = _json("docs/audits/devpl_gsdlc_11_d_historical_contract_sweep.json")
    sweep = _json("docs/audits/devpl_gsdlc_11_d_contract_reconciliation_sweep.json")
    assert hca["status"] == "PASS"
    assert hca["historical_evidence_rewritten"] is False
    assert sweep["status"] == "PASS"
    assert not any(sweep["checks"].values())
    assert sweep["full_regression_runs"] == 0
