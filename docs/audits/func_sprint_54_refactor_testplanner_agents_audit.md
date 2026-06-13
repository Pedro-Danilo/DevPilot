---
title: "FUNC-SPRINT-54 — SafeRefactorAgent y TestPlannerAgent gobernados audit"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-54"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
sprint: "FUNC-SPRINT-54"
phase: "FASE-D-IA-LOCAL-GOBERNADA"
created: "2026-06-13"
updated: "2026-06-13"
approval: "approved_by_owner_direction"
---

# FUNC-SPRINT-54 — SafeRefactorAgent y TestPlannerAgent gobernados audit

## Propósito

Este artefacto audita la implementación inicial de `FUNC-SPRINT-54`, cuyo objetivo es crear agentes monoagente especializados para planificación de refactor seguro y planificación de pruebas, sin ejecutar cambios reales, sin ejecutar pruebas por defecto y sin habilitar APIs externas.

## Estado

`FUNC-SPRINT-54` queda en estado `implemented-initial`. La implementación es deliberadamente plan-only: prioriza seguridad operacional, trazabilidad, MIASI, prompts versionados y evals offline antes de habilitar ejecución real de refactors o pruebas.

## Funcionamiento

`SafeRefactorAgent` envuelve `RefactorPlanner` y produce candidatos, plan, comandos de verificación, rollback guidance y suggestions. Declara capacidades futuras como `refactor.sandbox` y `tests.run`, pero no las ejecuta en este sprint.

`TestPlannerAgent` usa `TraceabilityEngine` y perfiles configurados de `tests.run` para producir un plan de pruebas trazable. El agente no ejecuta pytest, no acepta argumentos arbitrarios y no invoca `SafeSubprocessRunner`.

Ambos agentes ejecutan bajo `AgentRuntime v2`, usan `PolicyEngine`, mantienen `monoagent=true`, `handoffs_enabled=false`, `mutations_performed=false`, `external_api_used=false` y opcionalmente generan una explicación gobernada vía `ModelAdapterRouter` cuando se usa `--provider mock`.

## Integración

La implementación queda integrada con:

- `AgentRuntime v2` para ejecución monoagente.
- `RefactorPlanner` para planes seguros sin aplicar cambios.
- `TraceabilityEngine` para cobertura y gaps explícitos.
- `tests.run` como capacidad controlada declarada, no ejecutada por defecto.
- `PromptRegistry` mediante `safe.refactor.agent` y `test.planner.agent`.
- `ModelAdapterRouter` y `BudgetLedger` para llamadas model-aware redacted.
- `MIASI Agent Registry`, `Tool Registry` y `Policy Matrix`.
- `EvalRunner` con casos offline para refactor/test planning.

## Criterios PASS

- `safe.refactor` y `testplanner.agent` están registrados como `implemented-initial`.
- Ambos agentes ejecutan en modo monoagente.
- `SafeRefactorAgent` no ejecuta cambios reales, no genera patches aplicables automáticamente y no invoca `RefactorExecutor`.
- `TestPlannerAgent` produce plan trazable y no ejecuta `tests.run`.
- Los prompts están versionados y validados por schema.
- Los evals offline cubren refactor plan-only y test-planner.
- `mock` permite pruebas herméticas sin Ollama, LM Studio ni APIs externas.

## Criterios BLOCK

- Bloquear cierre si `safe-refactor` modifica workspace real sin approval.
- Bloquear cierre si `test-planner` ejecuta comandos arbitrarios o pytest sin aprobación.
- Bloquear cierre si los prompts no están versionados.
- Bloquear cierre si se habilitan providers externos, handoffs o multiagente.
- Bloquear cierre si prompts, completions, código fuente crudo o secretos quedan persistidos en reportes.

## Riesgos

- Los planes son heurísticos y no sustituyen revisión humana ni herramientas IDE de refactor.
- `TestPlannerAgent` depende de trazabilidad explícita; no infiere cobertura semántica profunda.
- `tests.run` permanece approval-gated para ejecución real; en Sprint 54 solo se proponen perfiles.
- La explicación model-aware con `mock` valida arquitectura y trazabilidad, no calidad semántica de un LLM local real.

## Veredicto

El sprint queda implementado como primera versión gobernada. Cumple el objetivo de agregar agentes de planificación de refactor y pruebas sin perder las garantías de Fase D: local-first, plan-only, MIASI, PromptRegistry, BudgetLedger, evals offline, sin APIs externas, sin mutaciones y sin multiagente.
