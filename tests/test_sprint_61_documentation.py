from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_61_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_E_agentops_observabilidad.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    manifest = _json("docs/functional_sprint_61_manifest.json")

    expected_paths = [
        "src/devpilot_core/observability/trace_queries.py",
        "tests/test_observability_cli.py",
        "docs/audits/func_sprint_61_trace_metrics_cli_audit.md",
        "docs/functional_sprint_61_manifest.json",
    ]
    for path in expected_paths:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-98" in readme
    assert "Siguiente hito: `FUNC-SPRINT-99" in readme
    assert "## FUNC-SPRINT-61 — CLI de trazas y métricas: trace report, trace inspect, metrics summary" in readme
    assert "## FUNC-SPRINT-61 — Operación de CLI de trazas y métricas" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-64"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-63"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-64"' in backlog
    assert "## Estado de implementación Sprint 63" in backlog
    assert 'next_sprint: "FUNC-SPRINT-99"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-63" in functional_backlog
    assert manifest["sprint"] == "FUNC-SPRINT-61"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-62")


def test_sprint_61_trace_metrics_cli_contracts_are_explicit() -> None:
    trace_queries = _read("src/devpilot_core/observability/trace_queries.py")
    cli = _read("src/devpilot_core/cli.py")
    audit = _read("docs/audits/func_sprint_61_trace_metrics_cli_audit.md")

    for term in ["TraceQueryService", "def report", "def inspect", "def metrics_summary"]:
        assert term in trace_queries
    for term in ["trace_report_command", "trace_inspect_command", "metrics_summary_command", "trace report", "metrics_summary"]:
        assert term in cli
    assert "Veredicto: `PASS`" in audit
    assert "implemented-initial" in audit


def test_sprint_61_security_and_scope_boundaries_remain_closed() -> None:
    combined = "\n".join(
        _read(path)
        for path in [
            "README.md",
            "docs/05_operations/runbook.md",
            "docs/05_operations/observability_plan.md",
            "docs/06_miasi/observability_card.md",
            "docs/devpilot_backlog_fase_E_agentops_observabilidad.md",
            "docs/functional_sprint_61_manifest.json",
            "src/devpilot_core/observability/trace_queries.py",
        ]
    ).lower()

    assert "commandresult" in combined
    assert "outputs/reports" in combined
    assert "db vacía" in combined or "empty_db" in combined
    assert "trace_id" in combined
    assert "external_api_used" in combined
    assert "ui" in combined
    assert "opentelemetry" in combined
    assert "telemetría remota" in combined or "remote_telemetry_enabled" in combined
    for forbidden in ["prompt", "completion", "stdout", "stderr", "secretos"]:
        assert forbidden in combined
