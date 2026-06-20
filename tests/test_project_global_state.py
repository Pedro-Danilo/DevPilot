from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.testing import TestContractRegistry

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_project_global_state_schema_and_docs_are_synchronized() -> None:
    state = json.loads(read(".devpilot/project_state.json"))
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    post_h_doc = read("docs/POST-H-001_industrial_hardening_tests_contracts.md")
    post_h_backlog = read("docs/backlogs/post_phase_h_ideas.md")
    changelog = read("docs/release/CHANGELOG.md")

    assert state["current_phase"] == "POST-FASE-H"
    assert state["last_completed_sprint"] == "POST-H-001"
    assert state["last_functional_sprint"] == "FUNC-SPRINT-99"
    assert state["next_sprint"] == "POST-H-002"
    assert state["phase_h_status"] == "closed_implemented_initial"
    assert state["industrial_baseline_ready"] is True
    assert state["global_state_owner"] == "tests/test_project_global_state.py"

    assert "Último hito: `POST-H-001" in readme
    assert "Siguiente hito: `POST-H-002" in readme
    assert "POST-H-001 — Industrial hardening de tests y contratos" in readme
    assert "POST-H-001 — Operación de hardening industrial de tests y contratos" in runbook
    assert 'status: "approved"' in post_h_doc
    assert 'implementation_status: "implemented-initial"' in post_h_doc
    assert "POST-H-002" in post_h_backlog
    assert "POST-H-001" in changelog


def test_project_global_state_command_result_passes() -> None:
    result = TestContractRegistry(ROOT).project_state()

    assert result.ok, result.to_dict()
    assert result.data["summary"]["last_completed_sprint"] == "POST-H-001"
    assert result.data["summary"]["next_sprint"] == "POST-H-002"
    assert result.data["summary"]["checks_passed"] == result.data["summary"]["checks_total"]
