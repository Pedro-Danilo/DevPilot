from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _post_h_number(value: str) -> int:
    match = re.fullmatch(r"POST-H-(\d+)", value)
    if match is None:
        raise AssertionError(f"Expected POST-H identifier, got {value!r}")
    return int(match.group(1))


def test_post_h_002_backlog_is_closed_and_points_to_post_h_003() -> None:
    backlog = _read("docs/backlogs/POST-H-002_maturity_dashboard_local.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    changelog = _read("docs/release/CHANGELOG.md")

    assert 'implementation_status: "closed"' in backlog
    assert 'version: "1.0.0"' in backlog
    assert "POST-H-002-E — Quality gate y documentación" in backlog
    assert "POST-H-002: closed / implemented-initial" in backlog
    assert "Siguiente hito: POST-H-003" in backlog
    assert "POST-H-002 closed" in readme
    assert "POST-H-002-E — Quality gate y documentación" in readme
    assert "POST-H-003" in readme
    assert "POST-H-002-E — Operación del quality gate del maturity dashboard" in runbook
    assert "post-h-002-e" in changelog


def test_post_h_002_manifest_and_closure_report_capture_no_go_gates() -> None:
    manifest = _read_json("docs/post_h_002_e_manifest.json")
    closure = _read("docs/audits/post_h_002_closure_report.md")
    audit = _read("docs/audits/post_h_002_e_quality_gate_documentation_report.md")

    assert manifest["id"] == "POST-H-002-E"
    assert manifest["status"] == "implemented-initial"
    assert manifest["parent_hito_status"] == "closed"
    assert manifest["next_hito"] == "POST-H-003"
    assert manifest["quality_gate_added"] is True
    assert manifest["test_contract_added"] == "post-h-002-maturity-dashboard"
    assert manifest["no_remote_execution_enabled"] is True
    assert manifest["no_connector_write_enabled"] is True
    assert manifest["no_plugin_execution_enabled"] is True
    assert manifest["no_external_apis_used"] is True
    assert "No remote execution" in closure
    assert "No connector write" in closure
    assert "No plugin execution" in closure
    assert "POST-H-003 — Test Contract Registry 2.0" in closure
    assert "maturity gate --json" in audit


def test_post_h_002_test_contract_registry_entry_exists() -> None:
    registry = _read_json(".devpilot/testing/test_contract_registry.json")
    contracts = {item["contract_id"]: item for item in registry["contracts"]}
    contract = contracts["post-h-002-maturity-dashboard"]

    assert contract["owner"] == "POST-H-002-E"
    assert contract["scope"] == "integration"
    assert contract["critical"] is True
    assert contract["mutable_global_state_allowed"] is False
    assert "tests/test_post_h_002_maturity_dashboard.py" in contract["test_files"]
    assert "tests/test_post_h_002_documentation.py" in contract["test_files"]
    assert "python -m devpilot_core maturity gate --json" in contract["recommended_commands"]


def test_post_h_002_project_state_has_advanced_beyond_post_h_002() -> None:
    state = _read_json(".devpilot/project_state.json")

    assert _post_h_number(state["last_completed_sprint"]) >= 3
    assert _post_h_number(state["next_sprint"]) >= 4
    assert any("POST-H-003 closes Test Contract Registry 2.0" in note for note in state["notes"])
