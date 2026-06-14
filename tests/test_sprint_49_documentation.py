from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_49_readme_runbook_backlog_and_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_D_ia_local_gobernada.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "Último hito: `FUNC-SPRINT-60" in readme
    assert "Siguiente hito: `FUNC-SPRINT-61" in readme
    assert "## FUNC-SPRINT-49 — Prompt Registry y contratos de prompt seguro" in readme
    assert "python -m devpilot_core prompt list --json" in runbook
    assert "python -m devpilot_core prompt validate --json" in runbook
    assert "python -m devpilot_core prompt show model.generate.default --json" in runbook
    assert "## FUNC-SPRINT-49 — Prompt Registry y contratos de prompt seguro" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-56"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-55"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-56"' in backlog
    assert "## Estado de implementación Sprint 49" in backlog
    assert 'next_sprint: "FUNC-SPRINT-61"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-49" in functional_backlog
    assert "## Actualización FUNC-SPRINT-49 — Pruebas de Prompt Registry y contratos de prompt seguro" in test_strategy


def test_sprint_49_schema_prompt_registry_and_miasi_are_synchronized() -> None:
    schema_catalog = _json("docs/schemas/schema_catalog.json")
    prompt_schema = _json("docs/schemas/prompt.schema.json")
    tools = {item["tool_id"]: item for item in _json(".devpilot/miasi/tool_registry.json")["tools"]}
    policies = {item["rule_id"]: item for item in _json(".devpilot/miasi/policy_matrix.json")["rules"]}
    tool_card = _read("docs/06_miasi/tool_card.md")
    policy_card = _read("docs/06_miasi/policy_card.md")

    assert prompt_schema["title"] == "DevPilot Prompt Contract v1"
    assert any(item["schema_id"] == "SCHEMA-DEVPL-PROMPT-V1" and item["contract"] == "Prompt" for item in schema_catalog["schemas"])
    assert tools["prompt.registry.read"]["status"] == "implemented-initial"
    assert tools["prompt.contract.validate"]["status"] == "implemented-initial"
    assert tools["prompt.render.controlled"]["status"] == "implemented-initial"
    assert "PROMPT_REGISTRY_READ_ALLOW" in tools["prompt.registry.read"]["policy_rule_ids"]
    assert "PROMPT_CONTRACT_VALIDATE_ALLOW" in tools["prompt.contract.validate"]["policy_rule_ids"]
    assert "PROMPT_RENDER_CONTROLLED" in tools["prompt.render.controlled"]["policy_rule_ids"]
    assert policies["PROMPT_REGISTRY_READ_ALLOW"]["default_effect"] == "allow"
    assert policies["PROMPT_CONTRACT_VALIDATE_ALLOW"]["default_effect"] == "allow"
    assert policies["PROMPT_RENDER_CONTROLLED"]["default_effect"] == "allow"
    assert "PromptSafetyChecker" in policies["PROMPT_CONTRACT_VALIDATE_ALLOW"]["gate"]
    assert "NoRawPromptStorage" in policies["PROMPT_RENDER_CONTROLLED"]["gate"]
    assert "FUNC-SPRINT-49" in tool_card
    assert "FUNC-SPRINT-49" in policy_card


def test_sprint_49_prompt_files_manifest_and_audit_exist() -> None:
    manifest = _json("docs/functional_sprint_49_manifest.json")
    audit = _read("docs/audits/func_sprint_49_prompt_registry_audit.md")
    prompt_files = sorted((ROOT / "docs/prompts").glob("*.json"))

    assert len(prompt_files) >= 3
    assert manifest["sprint"] == "FUNC-SPRINT-49"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert "src/devpilot_core/prompts/registry.py" in manifest["created_files"]
    assert "src/devpilot_core/prompts/safety.py" in manifest["created_files"]
    assert "docs/schemas/prompt.schema.json" in manifest["created_files"]
    assert "tests/test_prompt_registry.py" in manifest["tests"]
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-50")
    assert "## Criterios PASS" in audit
    assert "## Criterios BLOCK" in audit
