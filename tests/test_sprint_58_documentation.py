from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_58_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_E_agentops_observabilidad.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    manifest = _json("docs/functional_sprint_58_manifest.json")

    expected_paths = [
        "src/devpilot_core/observability/trace_store.py",
        "tests/test_trace_store.py",
        "docs/audits/func_sprint_58_trace_store_audit.md",
        "docs/functional_sprint_58_manifest.json",
    ]
    for path in expected_paths:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-60" in readme
    assert "Siguiente hito: `FUNC-SPRINT-61" in readme
    assert "## FUNC-SPRINT-58 — TraceStore y EventLogger v2 compatible" in readme
    assert "## FUNC-SPRINT-58 — Operación de TraceStore y EventLogger v2 compatible" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-61"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-60"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-61"' in backlog
    assert "## Estado de implementación Sprint 58" in backlog
    assert 'next_sprint: "FUNC-SPRINT-61"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-58" in functional_backlog
    assert manifest["sprint"] == "FUNC-SPRINT-58"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-59")


def test_sprint_58_trace_store_contracts_are_explicit() -> None:
    trace_store = _read("src/devpilot_core/observability/trace_store.py")
    events = _read("src/devpilot_core/observability/events.py")
    local_store = _read("src/devpilot_core/store/local_store.py")
    audit = _read("docs/audits/func_sprint_58_trace_store_audit.md")

    for term in ["TraceStore", "record_span", "record_event", "list_spans", "record_smoke_trace"]:
        assert term in trace_store
    for term in ["trace_context", "TraceContext", "SpanRecord", "trace_id", "span_id"]:
        assert term in events
    for term in ["CREATE TABLE IF NOT EXISTS spans", "CREATE TABLE IF NOT EXISTS metrics", "_migrate_observability_v2"]:
        assert term in local_store
    assert "Veredicto: `PASS`" in audit
    assert "implemented-initial" in audit


def test_sprint_58_security_and_scope_boundaries_remain_closed() -> None:
    combined = "\n".join(
        _read(path)
        for path in [
            "README.md",
            "docs/05_operations/runbook.md",
            "docs/05_operations/observability_plan.md",
            "docs/devpilot_backlog_fase_E_agentops_observabilidad.md",
            "docs/functional_sprint_58_manifest.json",
            "src/devpilot_core/observability/trace_store.py",
        ]
    ).lower()

    assert "jsonl" in combined
    assert "sqlite" in combined
    assert "spans" in combined
    assert "metrics" in combined
    assert "no agrega opentelemetry" in combined or "opentelemetry sdk" in combined
    assert "no activa telemetría remota" in combined or 'remote_telemetry_enabled": false' in combined
    assert "no expone comandos" in combined or "sin cli" in combined or "no entrega todavía cli" in combined
