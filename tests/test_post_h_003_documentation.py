from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_003_backlog_is_closed_and_points_to_post_h_004() -> None:
    backlog = _read("docs/backlogs/POST-H-003_test_contract_registry_2.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    changelog = _read("docs/release/CHANGELOG.md")

    assert 'implementation_status: "closed"' in backlog
    assert 'version: "1.0.0"' in backlog
    assert "POST-H-003-E — Quality gate y documentación" in backlog
    assert "Siguiente hito: `POST-H-004" in readme
    assert "Último hito: `POST-H-003" in readme
    assert "POST-H-003-E — Operación del cierre Test Contract Registry 2.0" in runbook
    assert "post-h-003-e" in changelog


def test_post_h_003_manifest_and_closure_report_capture_no_go_gates() -> None:
    manifest = _read_json("docs/post_h_003_e_manifest.json")
    closure = _read("docs/audits/post_h_003_closure_report.md")
    report = _read("docs/audits/post_h_003_e_quality_gate_documentation_report.md")

    assert manifest["id"] == "POST-H-003-E"
    assert manifest["status"] == "implemented-initial"
    assert manifest["parent_hito_status"] == "closed"
    assert manifest["next_hito"] == "POST-H-004"
    assert manifest["quality_gate_subgate_added"] == "test-contract-registry-v2"
    assert manifest["v1_contract_added"] == "post-h-003-test-contract-registry-2"
    assert manifest["v2_registry_contracts_total"] == 88
    assert manifest["tests_execute_from_json"] is False
    assert manifest["remote_execution_enabled"] is False
    assert manifest["connector_write_enabled"] is False
    assert manifest["plugin_execution_enabled"] is False
    assert manifest["production_ready_local_declared"] is False
    assert "No remote execution" in closure
    assert "No connector write" in closure
    assert "No plugin execution" in closure
    assert "POST-H-004 — Policy/MIASI semantic validator ampliado" in closure
    assert "test-contract-registry-v2" in report


def test_post_h_003_contracts_exist_in_v1_and_v2() -> None:
    v1 = _read_json(".devpilot/testing/test_contract_registry.json")
    v2 = _read_json(".devpilot/testing/test_contract_registry_v2.json")
    v1_contracts = {item["contract_id"]: item for item in v1["contracts"]}
    v2_contracts = {item["contract_id"]: item for item in v2["contracts"]}

    assert len(v1_contracts) == 88
    assert len(v2_contracts) == 88
    assert "post-h-003-test-contract-registry-2" in v1_contracts
    assert "post-h-003-test-contract-registry-2" in v2_contracts
    assert v1_contracts["post-h-003-test-contract-registry-2"]["owner"] == "POST-H-003-E"
    assert v2_contracts["post-h-003-test-contract-registry-2"]["domain"] == "governance.testing"
    assert v2_contracts["post-h-003-test-contract-registry-2"]["criticality"] == "P0"
    assert v2_contracts["post-h-003-test-contract-registry-2"]["classification_status"] == "explicit"


def test_post_h_003_project_state_advances_to_post_h_004() -> None:
    state = _read_json(".devpilot/project_state.json")

    assert state["last_completed_sprint"] == "POST-H-003"
    assert state["next_sprint"] == "POST-H-004"
    assert state["source_repo"] == "repo_DevPilot_Local_149_POST_H_003_D.zip"
    assert state["current_repo"] == "repo_DevPilot_Local_150_POST_H_003_E.zip"
