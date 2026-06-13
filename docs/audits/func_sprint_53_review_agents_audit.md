---
title: "FUNC-SPRINT-53 — CodeReviewAgent y PatchReviewAgent gobernados audit"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-53"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
sprint: "FUNC-SPRINT-53"
phase: "FASE-D-IA-LOCAL-GOBERNADA"
created: "2026-06-13"
updated: "2026-06-13"
approval: "approved_by_owner_direction"
---

# FUNC-SPRINT-53 — CodeReviewAgent y PatchReviewAgent gobernados audit

## Propósito

Este artefacto audita la implementación inicial de `FUNC-SPRINT-53`, cuyo objetivo es crear agentes monoagente especializados de revisión de código y revisión de patches sobre motores determinísticos existentes, sin ejecutar cambios reales y sin habilitar APIs externas.

## Estado

`FUNC-SPRINT-53` queda en estado `implemented-initial`. La implementación es una primera versión industrializable: prioriza gobierno, trazabilidad, dry-run y compatibilidad con `mock` antes de ampliar cobertura semántica o calidad de revisión asistida por modelos locales reales.

## Funcionamiento

`CodeReviewAgent` envuelve `CodeReviewEngine` y produce hallazgos, sugerencias y metadata de revisión sin modificar archivos. `PatchReviewAgent` envuelve `PatchReviewEngine` y `PatchPreflightEngine`; revisa riesgo y aplicabilidad del patch, pero nunca aplica cambios al workspace productivo.

Ambos agentes ejecutan bajo `AgentRuntime v2`, usan `PolicyEngine` antes de invocar capacidades, mantienen `monoagent=true`, `handoffs_enabled=false`, `mutations_performed=false` y opcionalmente generan una explicación gobernada vía `ModelAdapterRouter` cuando se usa `--provider mock` o un proveedor local disponible.

## Integración

La implementación queda integrada con:

- `AgentRuntime v2` para ejecución monoagente.
- `PromptRegistry` mediante `code.review.agent` y `patch.review.agent`.
- `ModelAdapterRouter` para llamadas model-aware.
- `BudgetLedger` para eventos de costo/uso redacted.
- `MIASI Agent Registry`, `Tool Registry` y `Policy Matrix`.
- `EvalRunner` con casos offline safe/risky para código y patches.

## Criterios PASS

- `code.review` y `patch.review` están registrados como `implemented-initial`.
- Ambos agentes operan en dry-run.
- Ningún agente modifica archivos ni aplica patches.
- Los hallazgos provienen de motores existentes y se priorizan como suggestions.
- Los prompts están versionados y validados por schema.
- Los evals offline cubren caso limpio/riesgoso de code review y patch review.
- `mock` permite pruebas herméticas sin Ollama, LM Studio ni APIs externas.

## Criterios BLOCK

- Bloquear cierre si `PatchReviewAgent` aplica un patch.
- Bloquear cierre si `CodeReviewAgent` modifica código.
- Bloquear cierre si cualquier agente usa provider externo.
- Bloquear cierre si los agentes llaman adapters directamente.
- Bloquear cierre si prompts, completions, patches o secretos crudos quedan persistidos en reportes.
- Bloquear cierre si se habilitan handoffs o multiagente.

## Riesgos

- La revisión inicial es heurística y no sustituye SAST/SCA ni revisión humana.
- Puede haber falsos positivos o falsos negativos por las reglas iniciales de los motores.
- `PatchPreflightEngine` valida aplicabilidad, pero no equivale a ejecutar pruebas de regresión.
- La explicación model-aware con `mock` valida arquitectura y trazabilidad; no mide calidad semántica real de modelos locales.

## Veredicto

El sprint queda implementado como primera versión gobernada. Cumple el objetivo de agregar agentes especializados de revisión sobre motores existentes sin perder las garantías de Fase D: local-first, dry-run, MIASI, PromptRegistry, BudgetLedger, evals offline, sin APIs externas y sin multiagente.
