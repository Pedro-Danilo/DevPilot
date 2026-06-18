from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_47_readme_runbook_backlog_and_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_D_ia_local_gobernada.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "Último hito: `FUNC-SPRINT-88" in readme
    assert "Siguiente hito: `FUNC-SPRINT-89" in readme
    assert "## FUNC-SPRINT-47 — LMStudioAdapter local OpenAI-compatible" in readme
    assert "python -m devpilot_core model health --provider lmstudio --json" in runbook
    assert "## FUNC-SPRINT-47 — LMStudioAdapter local OpenAI-compatible" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-56"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-55"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-56"' in backlog
    assert "## Estado de implementación Sprint 47" in backlog
    assert 'next_sprint: "FUNC-SPRINT-89"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-47" in functional_backlog
    assert "## Actualización FUNC-SPRINT-47 — Pruebas de LMStudioAdapter local OpenAI-compatible" in test_strategy


def test_sprint_47_miasi_and_provider_contracts_are_synchronized() -> None:
    tools = {item["tool_id"]: item for item in _json(".devpilot/miasi/tool_registry.json")["tools"]}
    policies = {item["rule_id"]: item for item in _json(".devpilot/miasi/policy_matrix.json")["rules"]}
    providers_example = _read(".devpilot/providers.yaml.example")
    tool_card = _read("docs/06_miasi/tool_card.md")

    assert tools["model.call.local"]["status"] == "implemented-initial"
    assert "MODEL_LOCAL_PROVIDER_CONTROLLED" in tools["model.call.local"]["policy_rule_ids"]
    assert tools["model.health.local"]["status"] == "implemented-initial"
    assert "MODEL_LOCAL_HEALTH_ALLOW" in tools["model.health.local"]["policy_rule_ids"]
    assert "LocalhostOnly" in policies["MODEL_LOCAL_PROVIDER_CONTROLLED"]["gate"]
    assert 'id: "lmstudio"' in providers_example
    assert 'status: "implemented-initial"' in providers_example
    assert 'endpoint: "http://localhost:1234"' in providers_example
    assert "FUNC-SPRINT-47 — LMStudioAdapter local OpenAI-compatible" in tool_card


def test_sprint_47_manifest_and_audit_exist() -> None:
    manifest = _json("docs/functional_sprint_47_manifest.json")
    audit = _read("docs/audits/func_sprint_47_lmstudio_adapter_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-47"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert "src/devpilot_core/modeling/lmstudio_adapter.py" in manifest["created_files"]
    assert "tests/test_lmstudio_adapter.py" in manifest["tests"]
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-48")
    assert "## Criterios PASS" in audit
    assert "## Criterios BLOCK" in audit
