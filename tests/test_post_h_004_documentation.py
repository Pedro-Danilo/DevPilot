from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]




def _post_h_number(value: str) -> int:
    match = re.fullmatch(r"POST-H-(\d+)", value)
    if match is None:
        raise AssertionError(f"Expected POST-H identifier, got {value!r}")
    return int(match.group(1))


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_004_backlog_is_closed_and_points_to_post_h_005() -> None:
    backlog = _read("docs/backlogs/POST-H-004_policy_miasi_semantic_validator.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    changelog = _read("docs/release/CHANGELOG.md")
    security_doc = _read("docs/03_security/policy_miasi_semantic_validation.md")

    assert 'implementation_status: "closed"' in backlog
    assert 'version: "1.0.0"' in backlog
    assert "POST-H-004-E — Integración con quality-gate y documentación" in backlog
    # README is cumulative: after later POST-H increments it no longer declares
    # POST-H-004 as the current hito, but it must preserve POST-H-004/005 context.
    assert "POST-H-004" in readme
    assert "POST-H-005" in readme
    assert "POST-H-004-E — Operación del cierre Policy/MIASI semantic validator" in runbook
    assert "post-h-004-e" in changelog
    assert "miasi-semantic-validate" in security_doc


def test_post_h_004_manifest_and_closure_report_capture_no_go_gates() -> None:
    manifest = _read_json("docs/post_h_004_e_manifest.json")
    closure = _read("docs/audits/post_h_004_closure_report.md")
    report = _read("docs/audits/post_h_004_e_quality_gate_documentation_report.md")

    assert manifest["id"] == "POST-H-004-E"
    assert manifest["status"] == "implemented-initial"
    assert manifest["parent_hito_status"] == "closed"
    assert manifest["next_hito"] == "POST-H-005"
    assert manifest["quality_gate_subgate_added"] == "miasi-semantic-validate"
    assert manifest["v1_contract_added"] == "post-h-004-miasi-semantic-validator"
    assert manifest["v2_contract_added"] == "post-h-004-miasi-semantic-validator"
    assert manifest["semantic_rules_total"] >= 13
    assert manifest["tests_execute_from_json"] is False
    assert manifest["agents_executed"] is False
    assert manifest["tools_executed"] is False
    assert manifest["remote_execution_enabled"] is False
    assert manifest["connector_write_enabled"] is False
    assert manifest["plugin_execution_enabled"] is False
    assert manifest["production_ready_local_declared"] is False
    assert "No remote execution" in closure
    assert "No connector write" in closure
    assert "No plugin execution" in closure
    assert "POST-H-005 — Architecture map executable" in closure
    assert "miasi-semantic-validate" in report


def test_post_h_004_contracts_exist_in_v1_and_v2() -> None:
    v1 = _read_json(".devpilot/testing/test_contract_registry.json")
    v2 = _read_json(".devpilot/testing/test_contract_registry_v2.json")
    v1_contracts = {item["contract_id"]: item for item in v1["contracts"]}
    v2_contracts = {item["contract_id"]: item for item in v2["contracts"]}

    # POST-H-004 originally closed with 89 contracts. Later POST-H increments
    # append contracts while preserving the POST-H-004 contract and v1/v2 parity.
    assert len(v1_contracts) >= 89
    assert len(v2_contracts) == len(v1_contracts)
    assert "post-h-004-miasi-semantic-validator" in v1_contracts
    assert "post-h-004-miasi-semantic-validator" in v2_contracts
    assert v1_contracts["post-h-004-miasi-semantic-validator"]["owner"] == "POST-H-004-E"
    assert v2_contracts["post-h-004-miasi-semantic-validator"]["domain"] == "governance.miasi"
    assert v2_contracts["post-h-004-miasi-semantic-validator"]["criticality"] == "P0"
    assert v2_contracts["post-h-004-miasi-semantic-validator"]["required_for_security_gate"] is True
    assert v2_contracts["post-h-004-miasi-semantic-validator"]["classification_status"] == "explicit"


def test_post_h_004_project_state_advances_to_post_h_005() -> None:
    state = _read_json(".devpilot/project_state.json")

    assert _post_h_number(state["last_completed_sprint"]) >= 4
    assert _post_h_number(state["next_sprint"]) >= 5
    assert "POST-H-004 closes the Policy/MIASI semantic validator" in "\n".join(state["notes"])
    assert "POST-H-005" in state["last_completed_sprint"] or _post_h_number(state["last_completed_sprint"]) > 4
