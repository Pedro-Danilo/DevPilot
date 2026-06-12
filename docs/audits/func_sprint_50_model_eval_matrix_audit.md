---
title: "FUNC-SPRINT-50 — Model evaluation matrix local audit"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-50"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
sprint: "FUNC-SPRINT-50"
phase: "FASE-D-IA-LOCAL-GOBERNADA"
created: "2026-06-12"
updated: "2026-06-12"
approval: "approved_by_owner_direction"
---

# FUNC-SPRINT-50 — Model evaluation matrix local audit

## Propósito

Auditar la implementación inicial de una matriz local de evaluación de modelos para DevPilot. El sprint busca comparar proveedores `mock` y locales por tarea sin depender de APIs externas.

## Estado

Estado: `implemented-initial`.

## Funcionamiento

`ModelEvalRunner` carga fixtures desde `evals/model_fixtures/model_eval_cases.json`, renderiza prompts versionados mediante `PromptRegistry`, ejecuta tareas por `ModelAdapterRouter`, calcula métricas preliminares y registra eventos de costo en `BudgetLedger` sin guardar prompts ni completions crudos.

## Integración

La capacidad se integra con CLI `model eval run`, MIASI Tool Registry (`model.eval.run`), Policy Matrix (`MODEL_EVAL_RUN_ALLOW`), Prompt Registry, Budget Ledger y ReportEngine.

## Criterios PASS

- La suite base con `mock` pasa sin modelos locales reales.
- Providers locales deshabilitados/no disponibles se reportan como skipped/controlado.
- Reportes incluyen provider/model/prompt_id/métricas/digest redacted.
- No hay APIs externas ni secretos crudos.

## Criterios BLOCK

- La evaluación requiere Ollama o LM Studio real para pasar.
- Se llama una API externa.
- Se persisten prompts, completions o secretos crudos.
- Provider unavailable produce traceback o rompe la suite base.

## Riesgos

- Métricas todavía preliminares y pequeñas.
- No hay jueces LLM ni evaluación humana.
- Las suites deben crecer por tarea/agente en sprints posteriores.

## Veredicto

`FUNC-SPRINT-50` queda apto para cierre si `pytest`, `model eval run`, `validate all`, `miasi validate` y `readiness-check` quedan en PASS en el entorno del owner.
