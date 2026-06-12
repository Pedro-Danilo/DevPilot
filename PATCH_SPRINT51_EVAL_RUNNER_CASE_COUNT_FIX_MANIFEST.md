# Patch — Sprint 51 pytest fix: EvalRunner case count contract

## Contexto

Después de `FUNC-SPRINT-51 — AgentRuntime v2 model-aware en modo monoagente`, la suite `documentation` del EvalRunner pasó de 8 a 9 casos porque se agregó el caso `agent-documentation-audit-model-aware-mock` para validar el path model-aware con provider `mock`.

## Causa raíz

`tests/test_eval_runner.py` conservaba asserts rígidos heredados:

- `cases_total == 8` en `test_eval_runner_documentation_suite_passes`.
- `cases_total == 8` en `test_eval_cli_run_json_and_report`.

El runtime y el fixture estaban correctos; el contrato de prueba quedó desactualizado.

## Corrección aplicada

Archivo modificado:

- `tests/test_eval_runner.py`

Cambios:

1. Se agregó helper `_documentation_case_count(root: Path)` que lee `evals/fixtures/documentation_eval_cases.json` y calcula dinámicamente el número de casos.
2. Se reemplazaron los asserts rígidos `== 8` por comparación contra el conteo real del fixture copiado al `tmp_path`.

## Validación ejecutada

```bash
PYTHONPATH=src python -m pytest tests/test_eval_runner.py -q
# DEVPL TEST SUMMARY: 5 passed, 0 failed, 0 errors, 0 skipped

PYTHONPATH=src python -m pytest tests/test_agent_runtime_v2.py -q
# DEVPL TEST SUMMARY: 5 passed, 0 failed, 0 errors, 0 skipped

PYTHONPATH=src python -m pytest tests/test_sprint_51_documentation.py -q
# DEVPL TEST SUMMARY: 3 passed, 0 failed, 0 errors, 0 skipped

PYTHONPATH=src python -m devpilot_core eval run --json
# ok=true, cases_total=9, cases_passed=9

PYTHONPATH=src python -m devpilot_core validate all --json
# ok=true, validations_failed=0, blocking_findings_total=0

PYTHONPATH=src python -m devpilot_core miasi validate --json
# ok=true, tools_total=45, policy_rules_total=31
```

## Riesgo

Bajo. El patch no cambia runtime, CLI, modelos, prompts, MIASI ni documentación funcional; solo corrige el contrato de prueba para que derive el total de casos desde el fixture fuente.
