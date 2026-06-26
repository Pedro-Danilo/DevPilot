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
    post_h_002_backlog = read("docs/backlogs/POST-H-002_maturity_dashboard_local.md")
    post_h_005_backlog = read("docs/backlogs/POST-H-005_architecture_map_executable.md")
    post_h_roadmap = read("docs/backlogs/post_h_prioritized_roadmap.md")
    changelog = read("docs/release/CHANGELOG.md")

    assert state["current_phase"] == "POST-FASE-H"
    assert state["last_completed_sprint"] == "POST-H-010"
    assert state["last_functional_sprint"] == "FUNC-SPRINT-99"
    assert state["next_sprint"] == "POST-H-011"
    assert state["phase_h_status"] == "closed_implemented_initial"
    assert state["industrial_baseline_ready"] is True
    assert state["global_state_owner"] == "tests/test_project_global_state.py"

    assert "Último hito: `POST-H-010" in readme
    assert "Siguiente hito: `POST-H-011" in readme
    assert "POST-H-006 — CLI command registry y desacoplamiento de handlers" in readme
    assert "POST-H-005-E — Operación del reporte final ArchitectureMap" in runbook
    assert 'status: "approved"' in post_h_doc
    assert 'implementation_status: "implemented-initial"' in post_h_doc
    assert 'implementation_status: "closed"' in post_h_002_backlog
    assert 'implementation_status: "closed"' in post_h_005_backlog
    assert "POST-H-008" in readme
    assert "post-h-007-a" in changelog
    assert "post-h-007-b" in changelog
    assert "post-h-007-c" in changelog
    assert "post-h-007-d" in changelog
    assert "post-h-007-e" in changelog
    assert "post-h-008-a" in changelog
    assert "post-h-008-b" in changelog
    assert "post-h-008-d" in changelog
    assert "post-h-008-e" in changelog
    assert "post-h-009-a" in changelog
    assert "post-h-009-b" in changelog
    assert "post-h-009-c" in changelog
    assert "post-h-009-d" in changelog
    assert "post-h-009-e" in changelog
    assert "post-h-010-d" in changelog
    assert "post-h-010-e" in changelog
    assert any("POST-H-009-A starts Documentation governance" in note for note in state["notes"])
    assert any("POST-H-009-B adds Documentation governance" in note for note in state["notes"])
    assert any("POST-H-009-C adds Documentation governance" in note for note in state["notes"])
    assert any("POST-H-009-D adds Documentation governance" in note for note in state["notes"])
    assert any("POST-H-009-E closes Documentation governance" in note for note in state["notes"])
    assert "POST-H-008-A — Runtime state lifecycle" in readme
    assert "POST-H-008-B — Runtime state lifecycle" in readme
    assert "POST-H-008-D — Runtime state lifecycle" in readme
    assert "POST-H-008-E — Runtime state lifecycle" in readme
    assert "POST-H-009-A — Documentation governance" in readme
    assert "POST-H-009-B — Documentation governance" in readme
    assert "POST-H-009-C — Documentation governance" in readme
    assert "POST-H-009-D — Documentation governance" in readme
    assert "POST-H-009-E — Documentation governance" in readme
    assert "POST-H-010-A — Observability retention" in readme
    assert "POST-H-010-B — Observability retention" in readme
    assert "POST-H-010-C — Observability retention" in readme
    assert "POST-H-010-D — Observability retention" in readme
    assert "POST-H-010-E — Observability retention" in readme
    assert any("POST-H-010-A starts Observability retention" in note for note in state["notes"])
    assert any("POST-H-010-B adds Observability inventory" in note for note in state["notes"])
    assert any("POST-H-010-C adds Observability cleanup plan" in note for note in state["notes"])
    assert any("POST-H-010-D adds local redacted observability export" in note for note in state["notes"])
    assert any("POST-H-010-E closes Observability retention local" in note for note in state["notes"])


def test_project_global_state_command_result_passes() -> None:
    result = TestContractRegistry(ROOT).project_state()

    assert result.ok, result.to_dict()
    assert result.data["summary"]["last_completed_sprint"] == "POST-H-010"
    assert result.data["summary"]["next_sprint"] == "POST-H-011"
    assert result.data["summary"]["checks_passed"] == result.data["summary"]["checks_total"]
