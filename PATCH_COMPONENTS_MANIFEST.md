# PATCH COMPONENTS — FUNC-SPRINT-53

Este ZIP contiene los componentes nuevos o modificados para `FUNC-SPRINT-53 — CodeReviewAgent y PatchReviewAgent gobernados`.

## Componentes creados

- `src/devpilot_core/agents/code_review_agent.py`
- `src/devpilot_core/agents/patch_review_agent.py`
- `docs/prompts/code.review.agent.v1.json`
- `docs/prompts/patch.review.agent.v1.json`
- `tests/test_review_agents.py`
- `tests/test_sprint_53_documentation.py`
- `tests/fixtures/review_agents/safe_target.py`
- `tests/fixtures/review_agents/safe.patch`
- `docs/audits/func_sprint_53_review_agents_audit.md`
- `docs/functional_sprint_53_manifest.json`

## Componentes modificados

- `.devpilot/miasi/agent_registry.json`
- `.devpilot/miasi/policy_matrix.json`
- `.devpilot/miasi/tool_registry.json`
- `README.md`
- `docs/04_quality/test_strategy.md`
- `docs/05_operations/runbook.md`
- `docs/06_miasi/agent_card.md`
- `docs/06_miasi/eval_card.md`
- `docs/06_miasi/policy_card.md`
- `docs/06_miasi/tool_card.md`
- `docs/06_miasi/tool_registry.md`
- `docs/devpilot_backlog_fase_D_ia_local_gobernada.md`
- `docs/functional_backlog_after_precode.md`
- `evals/fixtures/documentation_eval_cases.json`
- `src/devpilot_core/agents/__init__.py`
- `src/devpilot_core/agents/runtime.py`
- `src/devpilot_core/cli.py`
- `src/devpilot_core/evals/runner.py`
- `tests/test_sprint_32_documentation.py`
- `tests/test_sprint_33_documentation.py`
- `tests/test_sprint_34_documentation.py`
- `tests/test_sprint_35_documentation.py`
- `tests/test_sprint_36_documentation.py`
- `tests/test_sprint_37_documentation.py`
- `tests/test_sprint_38_documentation.py`
- `tests/test_sprint_39_documentation.py`
- `tests/test_sprint_40_documentation.py`
- `tests/test_sprint_41_documentation.py`
- `tests/test_sprint_42_documentation.py`
- `tests/test_sprint_43_documentation.py`
- `tests/test_sprint_44_documentation.py`
- `tests/test_sprint_45_documentation.py`
- `tests/test_sprint_46_documentation.py`
- `tests/test_sprint_47_documentation.py`
- `tests/test_sprint_48_documentation.py`
- `tests/test_sprint_49_documentation.py`
- `tests/test_sprint_50_documentation.py`
- `tests/test_sprint_51_documentation.py`
- `tests/test_sprint_52_documentation.py`

## Exclusiones

No incluye `outputs/`, `.devpilot/devpilot.db`, `.devpilot/providers.yaml`, `.devpilot/rollback/`, `.git/`, `.venv/`, caches, logs ni artefactos temporales.
