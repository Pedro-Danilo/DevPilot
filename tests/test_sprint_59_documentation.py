from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_59_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_E_agentops_observabilidad.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    manifest = _json("docs/functional_sprint_59_manifest.json")

    expected_paths = [
        "src/devpilot_core/observability/metrics.py",
        "tests/test_metrics_collector.py",
        "docs/audits/func_sprint_59_metrics_collector_audit.md",
        "docs/functional_sprint_59_manifest.json",
    ]
    for path in expected_paths:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-61" in readme
    assert "Siguiente hito: `FUNC-SPRINT-62" in readme
    assert "## FUNC-SPRINT-59 — MetricsCollector para comandos, agentes, tools y modelos" in readme
    assert "## FUNC-SPRINT-59 — Operación de MetricsCollector local" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-62"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-61"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-62"' in backlog
    assert "## Estado de implementación Sprint 59" in backlog
    assert 'next_sprint: "FUNC-SPRINT-62"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-59" in functional_backlog
    assert manifest["sprint"] == "FUNC-SPRINT-59"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-60")


def test_sprint_59_metrics_contracts_are_explicit() -> None:
    metrics = _read("src/devpilot_core/observability/metrics.py")
    local_store = _read("src/devpilot_core/store/local_store.py")
    router = _read("src/devpilot_core/modeling/router.py")
    cli = _read("src/devpilot_core/cli.py")
    audit = _read("docs/audits/func_sprint_59_metrics_collector_audit.md")

    for term in ["MetricRecord", "MetricsCollector", "record_command_result", "record_model_result", "record_agent_operation", "record_tool_operation", "summary"]:
        assert term in metrics
    for term in ["0004_metrics_collector_v1", "record_metric", "list_metrics", "metrics_summary", "idx_metrics_provider"]:
        assert term in local_store
    assert "MetricsCollector" in cli
    assert "_record_model_metric" in router
    assert "Veredicto: `PASS`" in audit
    assert "implemented-initial" in audit


def test_sprint_59_security_and_scope_boundaries_remain_closed() -> None:
    combined = "\n".join(
        _read(path)
        for path in [
            "README.md",
            "docs/05_operations/runbook.md",
            "docs/05_operations/observability_plan.md",
            "docs/06_miasi/observability_card.md",
            "docs/devpilot_backlog_fase_E_agentops_observabilidad.md",
            "docs/functional_sprint_59_manifest.json",
            "src/devpilot_core/observability/metrics.py",
        ]
    ).lower()

    assert "best-effort" in combined
    assert "provider=mock" in combined or "provider mock" in combined
    assert "external_api_used=false" in combined or '"external_api_used": false' in combined
    assert "no activa" in combined or "remote_telemetry_enabled" in combined
    assert "prompt" in combined
    assert "completion" in combined
    assert "stdout" in combined
    assert "stderr" in combined
    assert "opentelemetry sdk" in combined or "opentelemetry" in combined
