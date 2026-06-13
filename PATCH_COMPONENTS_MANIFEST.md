# PATCH COMPONENTS — FUNC-SPRINT-54

Sprint: FUNC-SPRINT-54 — SafeRefactorAgent y TestPlannerAgent gobernados

Este ZIP contiene únicamente componentes nuevos o modificados para aplicar sobre repo_DevPilot_Local_65.zip. No incluye outputs/, SQLite runtime, providers.yaml local, caches ni artefactos temporales.

## Componentes

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
- `docs/audits/func_sprint_54_refactor_testplanner_agents_audit.md`
- `docs/devpilot_backlog_fase_D_ia_local_gobernada.md`
- `docs/functional_backlog_after_precode.md`
- `docs/functional_sprint_54_manifest.json`
- `docs/prompts/safe.refactor.agent.v1.json`
- `docs/prompts/test.planner.agent.v1.json`
- `evals/fixtures/documentation_eval_cases.json`
- `src/devpilot_core/agents/__init__.py`
- `src/devpilot_core/agents/runtime.py`
- `src/devpilot_core/agents/safe_refactor_agent.py`
- `src/devpilot_core/agents/test_planner_agent.py`
- `src/devpilot_core/evals/runner.py`
- `tests/test_refactor_testplanner_agents.py`
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
- `tests/test_sprint_53_documentation.py`
- `tests/test_sprint_54_documentation.py`

## Validación sugerida

```powershell
python -m pytest tests/test_refactor_testplanner_agents.py tests/test_sprint_54_documentation.py -q
python -m devpilot_core agent run safe-refactor --target src/devpilot_core/repo --provider mock --json
python -m devpilot_core agent run test-planner --target docs/01_requirements --provider mock --json
python -m devpilot_core eval run --json
python -m devpilot_core prompt validate --json
python -m devpilot_core miasi validate --json
python -m devpilot_core validate all --json
```
