from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_sprint_85_advanced_architecture_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog_h = _read("docs/devpilot_backlog_fase_H_capacidades_avanzadas.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")

    for path in [
        "docs/02_architecture/adrs/ADR-0016-advanced-agentic-enterprise.md",
        "docs/03_security/advanced_agentic_threat_model.md",
        "docs/audits/func_sprint_85_advanced_architecture_audit.md",
        "docs/functional_sprint_85_manifest.json",
        "tests/test_sprint_85_documentation.py",
    ]:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-89" in readme
    assert "Siguiente hito: `FUNC-SPRINT-90" in readme
    assert "FUNC-SPRINT-85 — ADR de arquitectura avanzada agentic/enterprise" in readme
    assert "FUNC-SPRINT-85 — Operación de arquitectura avanzada agentic/enterprise" in runbook
    assert 'source_repo: "repo_DevPilot_Local_114.zip"' in backlog_h
    assert 'last_completed_sprint: "FUNC-SPRINT-89"' in backlog_h
    assert 'next_sprint: "FUNC-SPRINT-90"' in backlog_h
    assert 'phase_h_status: "in_progress"' in backlog_h
    assert 'next_sprint: "FUNC-SPRINT-90"' in functional_backlog


def test_sprint_85_docs_define_advanced_agentic_boundaries() -> None:
    adr = _read("docs/02_architecture/adrs/ADR-0016-advanced-agentic-enterprise.md")
    threat = _read("docs/03_security/advanced_agentic_threat_model.md")
    c4_context = _read("docs/02_architecture/c4_context.md")
    c4_container = _read("docs/02_architecture/c4_container.md")
    c4_component = _read("docs/02_architecture/c4_component.md")
    audit = _read("docs/audits/func_sprint_85_advanced_architecture_audit.md")
    changelog = _read("docs/release/CHANGELOG.md")

    for marker in [
        "supervisor",
        "handoffs",
        "Graph orchestration",
        "Pipeline secuencial",
        "Autonomía abierta",
        "disabled",
        "experimental/future",
    ]:
        assert marker.lower() in adr.lower()

    for marker in [
        "prompt injection",
        "tool poisoning",
        "data leakage",
        "privilege escalation",
        "connector abuse",
        "deny-by-default",
    ]:
        assert marker.lower() in threat.lower()

    for text in [c4_context, c4_container, c4_component, audit, changelog]:
        assert "FUNC-SPRINT-85" in text

    assert "RemoteRunner" in c4_component
    assert "MultiAgentCoordinator" in c4_component
    assert "RAG documental local" in c4_component


def test_sprint_85_miasi_cards_are_updated_for_phase_h() -> None:
    for path in [
        "docs/06_miasi/agent_card.md",
        "docs/06_miasi/tool_card.md",
        "docs/06_miasi/policy_card.md",
        "docs/06_miasi/eval_card.md",
        "docs/06_miasi/observability_card.md",
        "docs/06_miasi/human_approval_card.md",
    ]:
        text = _read(path)
        assert "Actualización FUNC-SPRINT-85" in text
        assert "Multiagente" in text
        assert "RAG" in text
        assert "MCP" in text
        assert "deny-by-default" in text
        assert "Remote runners" in text


def test_sprint_85_manifest_declares_architecture_only_scope() -> None:
    manifest = _json("docs/functional_sprint_85_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-85"
    assert manifest["status"] == "implemented"
    assert manifest["phase"] == "FASE-H-CAPACIDADES-AVANZADAS"
    assert manifest["summary"]["fh_level"] == "FH-L0"
    assert manifest["summary"]["advanced_architecture_adr_added"] is True
    assert manifest["summary"]["advanced_threat_model_added"] is True
    assert manifest["summary"]["miasi_cards_updated"] is True
    assert manifest["summary"]["capability_states_declared"] is True
    assert manifest["summary"]["deny_by_default_declared"] is True
    assert manifest["summary"]["multiagent_runtime_added"] is False
    assert manifest["summary"]["rag_runtime_added"] is False
    assert manifest["summary"]["mcp_runtime_added"] is False
    assert manifest["summary"]["plugin_runtime_added"] is False
    assert manifest["summary"]["remote_runner_enabled"] is False
    assert manifest["summary"]["dependencies_added"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-86")
