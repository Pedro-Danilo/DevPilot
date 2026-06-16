from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_57_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_E_agentops_observabilidad.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    manifest = _json("docs/functional_sprint_57_manifest.json")

    expected_paths = [
        "src/devpilot_core/observability/tracing.py",
        "tests/test_trace_context.py",
        "docs/audits/func_sprint_57_trace_context_audit.md",
        "docs/functional_sprint_57_manifest.json",
    ]
    for path in expected_paths:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-69" in readme
    assert "Siguiente hito: `FUNC-SPRINT-70" in readme
    assert "## FUNC-SPRINT-57 — TraceContext y modelo de spans" in readme
    assert "## FUNC-SPRINT-57 — Operación de TraceContext y spans internos" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-64"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-63"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-64"' in backlog
    assert "## Estado de implementación Sprint 57" in backlog
    assert 'next_sprint: "FUNC-SPRINT-70"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-57" in functional_backlog
    assert manifest["sprint"] == "FUNC-SPRINT-57"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-58")


def test_sprint_57_trace_contracts_are_explicit() -> None:
    tracing = _read("src/devpilot_core/observability/tracing.py")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    audit = _read("docs/audits/func_sprint_57_trace_context_audit.md")

    for term in ["TraceContext", "SpanRecord", "SpanStatus", "new_trace_id", "sanitize_span_payload"]:
        assert term in tracing
        assert term in readme or term in runbook or term in audit
    for term in ["trace_id", "run_id", "span_id", "parent_span_id", "duration_ms"]:
        assert term in tracing
    assert "Veredicto: `PASS`" in audit
    assert "implemented-initial" in readme


def test_sprint_57_security_boundaries_remain_closed() -> None:
    combined = "\n".join(
        _read(path)
        for path in [
            "src/devpilot_core/observability/tracing.py",
            "README.md",
            "docs/05_operations/runbook.md",
            "docs/devpilot_backlog_fase_E_agentops_observabilidad.md",
            "docs/functional_sprint_57_manifest.json",
        ]
    ).lower()

    assert "raw prompts" in combined or "prompt completo" in combined
    assert "completions" in combined or "completion" in combined
    assert "diff" in combined
    assert "patch" in combined
    assert "no se agregan dependencias externas" in combined or "dependency-free" in combined
    assert "no habilita telemetría remota" in combined or "remote_telemetry_enabled\": false" in combined
    assert "eventlogger" in combined
