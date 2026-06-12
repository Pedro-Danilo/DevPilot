---
title: "FUNC-SPRINT-51 — AgentRuntime v2 model-aware audit"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-51"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
sprint: "FUNC-SPRINT-51"
phase: "FASE-D-IA-LOCAL-GOBERNADA"
created: "2026-06-12"
updated: "2026-06-12"
approval: "approved_by_owner_direction"
---

# FUNC-SPRINT-51 — AgentRuntime v2 model-aware audit

## Propósito

Auditar la implementación inicial de `AgentRuntime v2` con capacidad model-aware en modo monoagente. El sprint busca permitir que agentes existentes usen modelos únicamente a través de `PromptRegistry`, `ModelAdapterRouter` y `BudgetLedger`, sin handoffs ni multiagente.

## Estado

Estado: `implemented-initial`.

## Funcionamiento

`AgentRuntimeConfig` acepta configuración opcional de provider, modelo, prompt, inputs, timeout y fallback. Si no se proporciona provider/prompt, los agentes mantienen ejecución rule-based sin modelos. Si se proporciona `--provider mock`, el agente renderiza un prompt versionado, llama `ModelAdapterRouter.generate`, registra un `AgentModelCall` redacted y genera un evento de presupuesto local mediante `BudgetLedger`.

## Integración

La capacidad se integra con:

- CLI `agent run` con `--provider`, `--model`, `--prompt-id`, `--prompt-input` y `--fallback-to-mock`.
- `PromptRegistry` para prompts versionados.
- `ModelAdapterRouter` para evitar llamadas directas a adapters.
- `BudgetLedger` para registrar uso sin prompts ni completions crudos.
- MIASI Tool Registry (`agent.model.generate`) y Policy Matrix (`AGENT_MODEL_CALL_GOVERNED_ALLOW`).
- `EvalRunner`, que incorpora un caso model-aware en la suite `documentation`.

## Criterios PASS

- Agentes actuales siguen en PASS sin provider y sin model calls.
- `--provider mock` produce `model_calls` con provider/model/prompt_id/version/digest.
- No se almacenan prompts, completions ni secretos crudos.
- Provider local no disponible puede usar fallback explícito a `mock`.
- `eval run --json` pasa con caso model-aware.
- `miasi validate`, `validate all` y `readiness-check` quedan en PASS.

## Criterios BLOCK

- Un agente llama adapters directamente.
- Se exige Ollama o LM Studio para la suite base.
- Se habilita API externa.
- Se persiste prompt/completion crudo en reportes, budget ledger o agent result.
- Se implementa handoff, supervisor o multiagente en Fase D Sprint 51.

## Riesgos

- La capacidad todavía se aplica a agentes documentales base, no a agentes especializados.
- El modelo `mock` valida arquitectura y trazabilidad, no calidad semántica industrial.
- El fallback debe mantenerse explícito y auditable para no ocultar fallos de providers locales.

## Veredicto

`FUNC-SPRINT-51` queda apto para cierre si `pytest`, `agent run ... --provider mock`, `eval run`, `validate all`, `miasi validate` y `readiness-check` quedan en PASS en el entorno del owner.
