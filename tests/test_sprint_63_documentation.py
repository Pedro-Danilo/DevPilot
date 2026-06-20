from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_63_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_E_agentops_observabilidad.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    manifest = _json("docs/functional_sprint_63_manifest.json")

    expected_paths = [
        "tests/test_agentops_gate.py",
        "tests/test_sprint_63_documentation.py",
        "docs/audits/func_sprint_63_agentops_quality_gate_audit.md",
        "docs/audits/phase_e_agentops_closure_report.md",
        "docs/functional_sprint_63_manifest.json",
    ]
    for path in expected_paths:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-99" in readme
    assert "Siguiente hito: `POST-H-001" in readme
    assert "## FUNC-SPRINT-63 — AgentOps Quality Gate y cierre Fase E" in readme
    assert "## FUNC-SPRINT-63 — Operación de AgentOps Quality Gate y cierre Fase E" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-64"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-63"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-64"' in backlog
    assert 'phase_e_status: "closed"' in backlog
    assert "## Estado de implementación Sprint 63 y cierre Fase E" in backlog
    assert 'next_sprint: "POST-H-001"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-63 — Cierre Fase E" in functional_backlog
    assert manifest["sprint"] == "FUNC-SPRINT-63"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-64")


def test_sprint_63_agentops_quality_gate_contracts_are_explicit() -> None:
    agentops = _read("src/devpilot_core/observability/agentops.py")
    cli = _read("src/devpilot_core/cli.py")
    audit = _read("docs/audits/func_sprint_63_agentops_quality_gate_audit.md")
    closure = _read("docs/audits/phase_e_agentops_closure_report.md")
    tool_registry = _read(".devpilot/miasi/tool_registry.json")
    policy_matrix = _read(".devpilot/miasi/policy_matrix.json")

    for term in ["AgentOpsQualityGate", "AgentOpsGateOptions", "REQUIRED_DOCUMENTS", "strict_runtime_signals"]:
        assert term in agentops
    for term in ["agentops_status_command", "agentops", "status", "agentops_status"]:
        assert term in cli
    assert "agentops.status" in tool_registry
    assert "AGENTOPS_STATUS_ALLOW" in policy_matrix
    assert "Veredicto: `PASS`" in audit
    assert "implemented-initial" in audit
    assert "Fase E queda cerrada" in closure


def test_sprint_63_security_and_scope_boundaries_remain_closed() -> None:
    combined = "\n".join(
        _read(path)
        for path in [
            "README.md",
            "docs/05_operations/runbook.md",
            "docs/05_operations/observability_plan.md",
            "docs/06_miasi/observability_card.md",
            "docs/06_miasi/tool_card.md",
            "docs/06_miasi/policy_matrix.md",
            "docs/devpilot_backlog_fase_E_agentops_observabilidad.md",
            "docs/functional_sprint_63_manifest.json",
            "src/devpilot_core/observability/agentops.py",
        ]
    ).lower()

    assert "commandresult" in combined
    assert "agentops status" in combined
    assert "outputs/reports" in combined
    assert "required" in combined
    assert "recommended" in combined
    assert "network_used" in combined
    assert "external_api_used" in combined
    assert "ui_required" in combined
    assert "telemetría remota" in combined or "remote_telemetry_enabled" in combined
    for term in ["prompt", "completion", "stdout", "stderr", "secret"]:
        assert term in combined
