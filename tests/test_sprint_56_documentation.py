from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_56_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_E_agentops_observabilidad.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    manifest = _json("docs/functional_sprint_56_manifest.json")

    expected_paths = [
        "docs/02_architecture/adrs/ADR-0012-observability-v2-agentops.md",
        "docs/05_operations/observability_plan.md",
        "docs/05_operations/observability_signal_catalog.md",
        "docs/06_miasi/observability_card.md",
        "docs/audits/func_sprint_56_observability_v2_audit.md",
        "docs/functional_sprint_56_manifest.json",
    ]
    for path in expected_paths:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-69" in readme
    assert "Siguiente hito: `FUNC-SPRINT-70" in readme
    assert "## FUNC-SPRINT-56 — ADR de observabilidad v2 y modelo AgentOps" in readme
    assert "## FUNC-SPRINT-56 — Operación de observabilidad v2 y AgentOps" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-64"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-63"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-64"' in backlog
    assert 'phase_e_status: "closed"' in backlog
    assert "## Estado de implementación Sprint 56" in backlog
    assert 'next_sprint: "FUNC-SPRINT-70"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-56" in functional_backlog
    assert manifest["sprint"] == "FUNC-SPRINT-56"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is True
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-57")


def test_sprint_56_observability_contracts_are_explicit() -> None:
    adr = _read("docs/02_architecture/adrs/ADR-0012-observability-v2-agentops.md")
    plan = _read("docs/05_operations/observability_plan.md")
    catalog = _read("docs/05_operations/observability_signal_catalog.md")
    card = _read("docs/06_miasi/observability_card.md")
    audit = _read("docs/audits/func_sprint_56_observability_v2_audit.md")

    for term in ["Eventos", "Trazas", "Spans", "Métricas", "Reportes"]:
        assert term in adr
    for term in ["evento", "trace", "span", "métrica", "reporte"]:
        assert term in plan.lower()
    for signal in [
        "devpilot.agent.run.started",
        "devpilot.agent.tool_call.proposed",
        "devpilot.policy.check.completed",
        "devpilot.model.call.completed",
        "devpilot_secret_redactions_total",
    ]:
        assert signal in catalog
    for term in ["agent_run_id", "tool_call_id", "model_call", "approval_id", "sandbox"]:
        assert term in card
    assert "Veredicto: `PASS`" in audit


def test_sprint_56_security_boundaries_remain_closed() -> None:
    combined = "\n".join(
        _read(path)
        for path in [
            "docs/02_architecture/adrs/ADR-0012-observability-v2-agentops.md",
            "docs/05_operations/observability_plan.md",
            "docs/05_operations/observability_signal_catalog.md",
            "docs/06_miasi/observability_card.md",
            "docs/devpilot_backlog_fase_E_agentops_observabilidad.md",
            "docs/functional_sprint_56_manifest.json",
        ]
    ).lower()

    assert "no se permite telemetría remota por defecto" in combined
    assert "opentelemetry solo" in combined or "opentelemetry queda" in combined
    assert "dry-run" in combined
    assert "sin dependencias externas" in combined or "no se agregan dependencias externas" in combined
    assert "no se habilita multiagente" in combined or "multiagente" in combined
    assert "prompt completo" in combined
    assert "completion cruda" in combined or "completions crudas" in combined
