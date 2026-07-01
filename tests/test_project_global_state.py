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
    assert state["last_completed_sprint"] == "POST-H-018"
    assert state["last_functional_sprint"] == "FUNC-SPRINT-99"
    assert state["next_sprint"] == "POST-H-019"
    assert state["phase_h_status"] == "closed_implemented_initial"
    assert state["industrial_baseline_ready"] is True
    assert state["global_state_owner"] == "tests/test_project_global_state.py"

    assert "Último hito cerrado: `POST-H-016" in readme
    assert "Siguiente hito: `POST-H-017" in readme
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
    assert state.get("current_micro_sprint") == "POST-H-019-D"
    assert state.get("next_micro_sprint") == "POST-H-019-E"
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
    assert any("POST-H-016-C hardens portfolio status" in note for note in state["notes"])
    assert any("POST-H-016-D adds secure CLI/API integration" in note for note in state["notes"])
    assert any("POST-H-016-E closes Workspace portfolio hardening" in note for note in state["notes"])
    assert any("POST-H-017-A approves Release reproducibility pack" in note for note in state["notes"])
    assert any("POST-H-017-A adds local release reproducibility policy" in note for note in state["notes"])
    assert "POST-H-017-A — Release reproducibility schema y policy" in readme
    assert "POST-H-017-A — Release reproducibility schema y policy" in runbook
    assert any("POST-H-017-B adds redacted ReleaseEnvironmentSnapshotBuilder" in note for note in state["notes"])
    assert "POST-H-017-B — Environment snapshot redactado" in readme
    assert "POST-H-017-B — Environment snapshot redactado" in runbook
    assert any("POST-H-017-C adds SourceArchiveManifestBuilder" in note for note in state["notes"])
    assert any("POST-H-017-D adds ReleaseReproducibilityVerifier" in note for note in state["notes"])
    assert any("POST-H-017-E adds ReleaseReproducibilityPackBuilder" in note for note in state["notes"])
    assert "POST-H-017-C — Source archive manifest y checksums" in readme
    assert "POST-H-017-D — Verifier local de reproducibilidad" in readme
    assert "POST-H-017-E — Quality gate y runbook release" in readme
    assert "POST-H-017-C — Source archive manifest y checksums" in runbook
    assert "POST-H-017-D — Verifier local de reproducibilidad" in runbook
    assert "POST-H-017-E — Quality gate y runbook release" in runbook
    assert "post-h-017-a" in changelog
    assert "post-h-017-b" in changelog
    assert "post-h-017-c" in changelog
    assert "post-h-017-d" in changelog
    assert "post-h-017-e" in changelog
    assert any("POST-H-018-A approves Connector sandbox avanzado" in note for note in state["notes"])
    assert any("POST-H-018-B adds ConnectorSandboxRunner" in note for note in state["notes"])
    assert "POST-H-018-A — Connector sandbox policy y schemas" in readme
    assert "POST-H-018-A — Connector sandbox policy y schemas" in runbook
    assert "POST-H-018-B — Sandbox runner read-only/dry-run" in readme
    assert "POST-H-018-B — Sandbox runner read-only/dry-run" in runbook
    assert "post-h-018-a" in changelog
    assert "post-h-018-b" in changelog
    assert any("POST-H-018-C adds ConnectorReplayRunner" in note for note in state["notes"])
    assert "POST-H-018-C — Replay fixtures y redacción" in readme
    assert "POST-H-018-C — Replay fixtures y redacción" in runbook
    assert "post-h-018-c" in changelog
    assert any("POST-H-018-D adds ConnectorPolicyBindingValidator" in note for note in state["notes"])
    assert "POST-H-018-D — Policy/approval/RBAC binding para conectores" in readme
    assert "POST-H-018-D — Policy/approval/RBAC binding para conectores" in runbook
    assert "post-h-018-d" in changelog
    assert any("POST-H-018-E adds ConnectorSandboxQualityGate" in note for note in state["notes"])
    assert any("POST-H-018 closes Connector sandbox avanzado" in note for note in state["notes"])
    assert any("POST-H-019 is the next prioritized hito" in note for note in state["notes"])
    assert "POST-H-018-E — Quality gate, runbook y cierre" in readme
    assert "POST-H-018-E — Quality gate, runbook y cierre" in runbook
    assert "post-h-018-e" in changelog
    assert "Siguiente hito: `POST-H-019" in readme
    assert any("POST-H-019-A approves Plugin sandbox design" in note for note in state["notes"])
    assert any("POST-H-019-B is the next micro-sprint" in note for note in state["notes"])
    assert any("POST-H-019-C adds PluginStaticValidator" in note for note in state["notes"])
    assert any("POST-H-019-D adds plugin-sandbox-design" in note for note in state["notes"])
    assert any("POST-H-019-E is the next micro-sprint" in note for note in state["notes"])
    assert "POST-H-019-A — Threat model y sandbox design" in readme
    assert "POST-H-019-A — Threat model y sandbox design" in runbook
    assert "post-h-019-a" in changelog
    assert "POST-H-019-B — Permission model y manifest hardening" in readme
    assert "POST-H-019-B — Permission model y manifest hardening" in runbook
    assert "POST-H-019-D — Quality gate plugin safety" in readme
    assert "POST-H-019-D — Quality gate plugin safety" in runbook
    assert "post-h-019-b" in changelog
    assert "post-h-019-c" in changelog
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
    assert "POST-H-016-C — Portfolio status hardening" in readme
    assert "POST-H-016-C — Portfolio status hardening" in runbook
    assert "POST-H-016-D — CLI/API integration segura" in readme
    assert "POST-H-016-D — CLI/API integration segura" in runbook
    assert "POST-H-016-E — Quality gate y runbook" in readme
    assert "POST-H-016-E — Quality gate y runbook" in runbook
    assert any("POST-H-012-A approves" in note for note in state["notes"])
    assert any("POST-H-012-C adds RBAC exposure reporting" in note for note in state["notes"])
    assert any("POST-H-012-D adds homogeneous PolicyEngine enforcement" in note for note in state["notes"])
    assert any("POST-H-012-E closes Approval/RBAC hardening" in note for note in state["notes"])


def test_project_global_state_command_result_passes() -> None:
    result = TestContractRegistry(ROOT).project_state()

    assert result.ok, result.to_dict()
    assert result.data["summary"]["last_completed_sprint"] == "POST-H-018"
    assert result.data["summary"]["next_sprint"] == "POST-H-019"
    assert result.data["summary"]["checks_passed"] == result.data["summary"]["checks_total"]
