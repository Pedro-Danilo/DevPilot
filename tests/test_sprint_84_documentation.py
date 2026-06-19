from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_sprint_84_release_agent_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog_g = _read("docs/devpilot_backlog_fase_G_productizacion_release.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")

    for path in [
        "src/devpilot_core/agents/release_agent.py",
        "docs/audits/phase_g_productization_release_closure.md",
        "docs/audits/func_sprint_84_release_agent_audit.md",
        "docs/functional_sprint_84_manifest.json",
        "tests/test_release_agent.py",
        "tests/test_sprint_84_documentation.py",
    ]:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-97" in readme
    assert "Siguiente hito: `FUNC-SPRINT-98" in readme
    assert "FUNC-SPRINT-84 — ReleaseAgent MVP dry-run y cierre Fase G" in readme
    assert "FUNC-SPRINT-84 — Operación ReleaseAgent dry-run y cierre Fase G" in runbook
    assert 'source_repo: "repo_DevPilot_Local_106.zip"' in backlog_g
    assert 'last_completed_sprint: "FUNC-SPRINT-84"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-85"' in backlog_g
    assert 'phase_g_status: "closed"' in backlog_g
    assert 'next_sprint: "FUNC-SPRINT-98"' in functional_backlog


def test_sprint_84_docs_define_release_agent_boundaries() -> None:
    audit = _read("docs/audits/func_sprint_84_release_agent_audit.md")
    closure = _read("docs/audits/phase_g_productization_release_closure.md")
    release_manifest = _read("docs/05_operations/release_manifest.md")
    artifacts_matrix = _read("docs/05_operations/release_artifacts_matrix.md")
    changelog = _read("docs/release/CHANGELOG.md")

    for text in [audit, closure, release_manifest, artifacts_matrix, changelog]:
        assert "FUNC-SPRINT-84" in text

    for marker in [
        "ReleaseAgent",
        "dry-run",
        "PolicyEngine",
        "MIASI",
        "no publica",
        "no despliega",
        "no firma",
        "no etiqueta Git",
    ]:
        assert marker in audit or marker in closure

    for marker in ["RELEASE-ASSISTANT", "PHASE-G-CLOSURE"]:
        assert marker in release_manifest
        assert marker in artifacts_matrix

    assert "FUNC-SPRINT-84` — `docs/functional_sprint_84_manifest.json`" in changelog
    assert "Range: `FUNC-SPRINT-74` → `FUNC-SPRINT-97`" in changelog


def test_sprint_84_manifest_declares_release_agent_scope() -> None:
    manifest = _json("docs/functional_sprint_84_manifest.json")

    assert manifest["sprint"] == "FUNC-SPRINT-84"
    assert manifest["status"] == "implemented"
    assert manifest["phase"] == "FASE-G-PRODUCTIZACION-RELEASE"
    assert manifest["summary"]["phase_g_closed"] is True
    assert manifest["summary"]["release_agent_registered"] is True
    assert manifest["summary"]["release_agent_cli_added"] is True
    assert manifest["summary"]["release_agent_dry_run_only"] is True
    assert manifest["summary"]["quality_gate_release_profile_added"] is True
    assert manifest["summary"]["tool_calls_auditable"] is True
    assert manifest["summary"]["miasi_integrated"] is True
    assert manifest["summary"]["policy_engine_integrated"] is True
    assert manifest["summary"]["publishes_artifacts"] is False
    assert manifest["summary"]["deploys_artifacts"] is False
    assert manifest["summary"]["git_tagging_performed"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-85")


def test_miasi_registries_include_release_agent() -> None:
    agents = _json(".devpilot/miasi/agent_registry.json")
    tools = _json(".devpilot/miasi/tool_registry.json")
    policies = _json(".devpilot/miasi/policy_matrix.json")

    release_agent = next(item for item in agents["agents"] if item["agent_id"] == "release.assistant")
    assert release_agent["status"] == "implemented-initial"
    assert "release.quality_gate" in release_agent["allowed_tools"]
    assert "RELEASE_AGENT_DRY_RUN_ALLOW" in release_agent["policy_rule_ids"]

    tool_ids = {item["tool_id"] for item in tools["tools"]}
    for expected in ["release.quality_gate", "release.manifest", "release.changelog", "release.package", "release.sbom"]:
        assert expected in tool_ids

    rule_ids = {item["rule_id"] for item in policies["rules"]}
    assert "RELEASE_AGENT_DRY_RUN_ALLOW" in rule_ids
    assert "RELEASE_PUBLISH_DEPLOY_TAG_DENY" in rule_ids
