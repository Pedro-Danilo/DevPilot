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
    assert state["last_completed_sprint"] == "POST-H-015"
    assert state["last_functional_sprint"] == "FUNC-SPRINT-99"
    assert state["next_sprint"] == "POST-H-016"
    assert state["phase_h_status"] == "closed_implemented_initial"
    assert state["industrial_baseline_ready"] is True
    assert state["global_state_owner"] == "tests/test_project_global_state.py"

    assert "Último hito cerrado: `POST-H-015" in readme
    assert "Siguiente hito: `POST-H-016" in readme
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
    assert "post-h-011-b" in changelog
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
    assert any("POST-H-011-C adds deterministic RAG claim groundedness" in note for note in state["notes"])
    assert any("POST-H-011-E closes RAG groundedness evals" in note for note in state["notes"])
    assert "POST-H-011-E — Gate y documentación de límites RAG" in readme
    assert "POST-H-012-D — PolicyEngine enforcement homogéneo" in readme
    assert "POST-H-012-E — Quality gate y runbook de aprobación" in readme
    assert "POST-H-012-E — Quality gate y runbook de aprobación" in runbook
    assert "POST-H-013-A — Audit pack manifest v2 y policy" in readme
    assert "POST-H-013-A — Audit pack manifest v2 y policy" in runbook
    assert "POST-H-013-B — Builder v2 con checksums y redaction report" in readme
    assert "POST-H-013-B — Builder v2 con checksums y redaction report" in runbook
    assert "POST-H-013-C — Verifier v2 de integridad local" in readme
    assert "POST-H-013-C — Verifier v2 de integridad local" in runbook
    assert "POST-H-013-D — Firma y cifrado local opcional" in readme
    assert "POST-H-013-D — Firma y cifrado local opcional" in runbook
    assert "POST-H-013-E — Quality gate, runbook y disclaimers" in readme
    assert "POST-H-013-E — Quality gate, runbook y disclaimers" in runbook
    assert any("POST-H-013-A starts Audit pack integrity" in note for note in state["notes"])
    assert any("POST-H-013-B adds AuditPackV2Builder" in note for note in state["notes"])
    assert any("POST-H-013-C adds AuditPackV2Verifier" in note for note in state["notes"])
    assert any("POST-H-013-D adds optional local crypto" in note for note in state["notes"])
    assert any("POST-H-013-E closes Audit pack integrity" in note for note in state["notes"])
    assert any("POST-H-014 is the next prioritized hito" in note for note in state["notes"])
    assert state.get("current_micro_sprint") == "POST-H-016-B"
    assert state.get("next_micro_sprint") == "POST-H-016-C"
    assert "POST-H-014-A — Route Contract Registry y API inventory" in readme
    assert "POST-H-014-B — Response mapping y errores homogéneos" in readme
    assert "POST-H-014-C — UI Route Contract y shell de producto" in readme
    assert "POST-H-014-D — Security hardening local de API/UI" in readme
    assert "POST-H-014-E — Quality gate UI/API industrial shell" in readme
    assert "POST-H-014-A — Route Contract Registry y API inventory" in runbook
    assert "POST-H-014-B — Response mapping y errores homogéneos" in runbook
    assert "POST-H-014-C — UI Route Contract y shell de producto" in runbook
    assert "POST-H-014-D — Security hardening local de API/UI" in runbook
    assert "POST-H-014-E — Quality gate UI/API industrial shell" in runbook
    assert "post-h-014-a" in changelog
    assert "post-h-014-b" in changelog
    assert "post-h-014-c" in changelog
    assert "post-h-014-d" in changelog
    assert "post-h-014-e" in changelog
    assert any("POST-H-014-A approves UI/API industrial shell" in note for note in state["notes"])
    assert any("POST-H-014-B adds homogeneous response mapping" in note for note in state["notes"])
    assert any("POST-H-014-C adds UI Route Contract Registry" in note for note in state["notes"])
    assert any("POST-H-014-D adds local API/UI security hardening" in note for note in state["notes"])
    assert any("POST-H-014-E closes UI/API industrial shell" in note for note in state["notes"])
    assert any("POST-H-015-A approves Local operator dashboard" in note for note in state["notes"])
    assert any("POST-H-015-B adds OperatorDashboardAggregator" in note for note in state["notes"])
    assert any("POST-H-015-C adds OperatorDashboardApplicationService" in note for note in state["notes"])
    assert any("POST-H-015-D adds the Web UI Operator Dashboard" in note for note in state["notes"])
    assert any("POST-H-015-E closes Local operator dashboard" in note for note in state["notes"])
    assert any("POST-H-016-A approves Workspace portfolio hardening" in note for note in state["notes"])
    assert any("POST-H-016-B adds WorkspaceIsolationValidator" in note for note in state["notes"])
    assert "POST-H-015-A — Dashboard snapshot schema y config" in readme
    assert "POST-H-015-A — Dashboard snapshot schema y config" in runbook
    assert "POST-H-015-B — Aggregator read-only de señales operacionales" in readme
    assert "POST-H-015-B — Aggregator read-only de señales operacionales" in runbook
    assert "POST-H-015-C — ApplicationService/API integration" in readme
    assert "POST-H-015-C — ApplicationService/API integration" in runbook
    assert "POST-H-015-D — UI operator dashboard" in readme
    assert "POST-H-015-D — UI operator dashboard" in runbook
    assert "POST-H-015-E — Quality gate y runbook operacional" in readme
    assert "POST-H-015-E — Quality gate y runbook operacional" in runbook
    assert "POST-H-016-A — Registry v2 y migración compatible" in readme
    assert "POST-H-016-A — Registry v2 y migración compatible" in runbook
    assert "POST-H-016-B — Workspace isolation validator" in readme
    assert "POST-H-016-B — Workspace isolation validator" in runbook
    assert any("POST-H-012-A approves" in note for note in state["notes"])
    assert any("POST-H-012-C adds RBAC exposure reporting" in note for note in state["notes"])
    assert any("POST-H-012-D adds homogeneous PolicyEngine enforcement" in note for note in state["notes"])
    assert any("POST-H-012-E closes Approval/RBAC hardening" in note for note in state["notes"])


def test_project_global_state_command_result_passes() -> None:
    result = TestContractRegistry(ROOT).project_state()

    assert result.ok, result.to_dict()
    assert result.data["summary"]["last_completed_sprint"] == "POST-H-015"
    assert result.data["summary"]["next_sprint"] == "POST-H-016"
    assert result.data["summary"]["checks_passed"] == result.data["summary"]["checks_total"]
