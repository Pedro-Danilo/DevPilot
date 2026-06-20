from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_60_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_E_agentops_observabilidad.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    manifest = _json("docs/functional_sprint_60_manifest.json")

    expected_paths = [
        "src/devpilot_core/observability/agentops.py",
        "tests/test_agentops_instrumentation.py",
        "docs/audits/func_sprint_60_agentic_instrumentation_audit.md",
        "docs/functional_sprint_60_manifest.json",
    ]
    for path in expected_paths:
        assert (ROOT / path).exists(), path

    assert "## FUNC-SPRINT-60 — Instrumentación agentic: agentes, tools, approvals y model calls" in readme
    assert "## FUNC-SPRINT-60 — Operación de instrumentación AgentOps agentic" in runbook
    assert "## Estado de implementación Sprint 60" in backlog
    assert "## Transición posterior a FUNC-SPRINT-60" in functional_backlog
    assert manifest["sprint"] == "FUNC-SPRINT-60"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-61")


def test_sprint_60_agentops_contracts_are_explicit() -> None:
    agentops = _read("src/devpilot_core/observability/agentops.py")
    runtime = _read("src/devpilot_core/agents/runtime.py")
    models = _read("src/devpilot_core/agents/models.py")
    policy = _read("src/devpilot_core/policy/engine.py")
    approvals = _read("src/devpilot_core/approval/service.py")
    router = _read("src/devpilot_core/modeling/router.py")
    audit = _read("docs/audits/func_sprint_60_agentic_instrumentation_audit.md")

    for term in ["AgentOpsInstrumentor", "record_agent_run", "record_tool_call", "record_policy_result", "record_approval_result", "record_model_result"]:
        assert term in agentops
    assert "safe_record_agent_result" in runtime
    assert "tool_call_id" in models
    assert "_record_policy_observability" in policy
    assert "_record_approval_observability" in approvals
    assert "record_model_result" in router
    assert "Veredicto: `PASS`" in audit
    assert "implemented-initial" in audit


def test_sprint_60_security_and_scope_boundaries_remain_closed() -> None:
    combined = "\n".join(
        _read(path)
        for path in [
            "README.md",
            "docs/05_operations/runbook.md",
            "docs/05_operations/observability_plan.md",
            "docs/06_miasi/observability_card.md",
            "docs/devpilot_backlog_fase_E_agentops_observabilidad.md",
            "docs/functional_sprint_60_manifest.json",
            "src/devpilot_core/observability/agentops.py",
        ]
    ).lower()

    assert "best-effort" in combined
    assert "payload_redacted" in combined or "redacted" in combined
    assert "telemetría remota" in combined or "remote_telemetry_enabled" in combined
    assert "external_api_used" in combined
    assert "opentelemetry" in combined
    assert "multiagente" in combined or "handoffs" in combined
    for forbidden in ["prompt", "completion", "stdout", "stderr", "secretos"]:
        assert forbidden in combined
