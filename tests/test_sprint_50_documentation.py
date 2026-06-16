from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_50_readme_runbook_backlog_and_strategy_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_D_ia_local_gobernada.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    test_strategy = _read("docs/04_quality/test_strategy.md")

    assert "Último hito: `FUNC-SPRINT-72" in readme
    assert "Siguiente hito: `FUNC-SPRINT-73" in readme
    assert "## FUNC-SPRINT-50 — Model evaluation matrix local" in readme
    assert "python -m devpilot_core model eval run --provider mock --json" in runbook
    assert "python -m devpilot_core model eval run --provider mock --json --write-report" in runbook
    assert "## FUNC-SPRINT-50 — Model evaluation matrix local" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-56"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-55"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-56"' in backlog
    assert "## Estado de implementación Sprint 50" in backlog
    assert 'next_sprint: "FUNC-SPRINT-73"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-50" in functional_backlog
    assert "## Actualización FUNC-SPRINT-50 — Pruebas de Model evaluation matrix local" in test_strategy


def test_sprint_50_miasi_and_eval_card_are_synchronized() -> None:
    tools = {item["tool_id"]: item for item in _json(".devpilot/miasi/tool_registry.json")["tools"]}
    policies = {item["rule_id"]: item for item in _json(".devpilot/miasi/policy_matrix.json")["rules"]}
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")
    policy_card = _read("docs/06_miasi/policy_card.md")
    eval_card = _read("docs/06_miasi/eval_card.md")

    assert tools["model.eval.run"]["status"] == "implemented-initial"
    assert "MODEL_EVAL_RUN_ALLOW" in tools["model.eval.run"]["policy_rule_ids"]
    assert policies["MODEL_EVAL_RUN_ALLOW"]["default_effect"] == "allow"
    assert "ModelEvalRunner" in policies["MODEL_EVAL_RUN_ALLOW"]["gate"]
    assert "NoExternalAPI" in policies["MODEL_EVAL_RUN_ALLOW"]["gate"]
    assert "NoRawPrompts" in policies["MODEL_EVAL_RUN_ALLOW"]["gate"]
    assert "FUNC-SPRINT-50" in tool_card
    assert "FUNC-SPRINT-50" in tool_registry_doc
    assert "FUNC-SPRINT-50" in policy_card
    assert "FUNC-SPRINT-50" in eval_card
    assert "model-local-smoke" in eval_card


def test_sprint_50_manifest_audit_and_fixtures_exist() -> None:
    manifest = _json("docs/functional_sprint_50_manifest.json")
    audit = _read("docs/audits/func_sprint_50_model_eval_matrix_audit.md")
    fixture = _json("evals/model_fixtures/model_eval_cases.json")

    assert manifest["sprint"] == "FUNC-SPRINT-50"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert "src/devpilot_core/modeling/evals.py" in manifest["created_files"]
    assert "evals/model_fixtures/model_eval_cases.json" in manifest["created_files"]
    assert "tests/test_model_eval_runner.py" in manifest["tests"]
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-51")
    assert fixture["suite_id"] == "model-local-smoke"
    assert len(fixture["cases"]) >= 3
    assert "## Criterios PASS" in audit
    assert "## Criterios BLOCK" in audit
