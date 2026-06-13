---
title: "FUNC-SPRINT-52 — RepoAnalysisAgent gobernado audit"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-52"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
sprint: "FUNC-SPRINT-52"
phase: "FASE-D-IA-LOCAL-GOBERNADA"
created: "2026-06-12"
updated: "2026-06-12"
approval: "approved_by_owner_direction"
---

# FUNC-SPRINT-52 — RepoAnalysisAgent gobernado audit

## Propósito

Auditar la implementación inicial de `RepoAnalysisAgent` como primer agente especializado monoagente sobre motores de repositorio de Fase C. El sprint busca producir un resumen gobernado del estado del repositorio, sugerencias priorizadas y trazabilidad model-aware opcional sin modificar archivos ni habilitar APIs externas.

## Estado

Estado: `implemented-initial`.

## Funcionamiento

`RepoAnalysisAgent` se ejecuta mediante `AgentRuntime v2` con alias `repo-analysis`. El agente resuelve el target dentro del workspace, valida la operación con `PolicyEngine`, ejecuta motores read-only (`RepoAnalyzer`, `DependencyGraphBuilder`, `GitAdapter`, `RepoQualityGate`), consolida componentes, findings y suggestions, y devuelve artifacts con `mutations_performed=false`.

Si el operador activa `--provider mock` o un prompt explícito, el agente usa `PromptRegistry` con `repo.analysis.agent`, llama `ModelAdapterRouter` y registra metadata redacted en `AgentModelCall` y `BudgetLedger`. El resultado crudo del modelo no se expone.

## Integración

La capacidad se integra con:

- CLI `agent run repo-analysis`.
- `AgentRuntime v2` en modo monoagente.
- `PromptRegistry` y prompt `repo.analysis.agent`.
- `ModelAdapterRouter` y `BudgetLedger` para model calls opcionales.
- MIASI Agent Registry (`repo.analysis` implemented-initial).
- MIASI Tool Registry (`agent.repo_analysis.run`).
- MIASI Policy Matrix (`REPO_ANALYSIS_AGENT_GOVERNED_ALLOW`).
- `EvalRunner`, con casos `agent.repo_analysis` y `agent.repo_analysis_model_aware`.

## Criterios PASS

- `agent run repo-analysis --target . --json` ejecuta sin modelo y sin mutaciones.
- `agent run repo-analysis --target . --provider mock --json` produce `model_calls` redacted con `prompt_id=repo.analysis.agent`.
- El agente usa solo tools declaradas en MIASI.
- Los targets fuera del workspace quedan bloqueados.
- `eval run --json` incluye casos de RepoAnalysisAgent y queda en PASS.
- `miasi validate`, `validate all` y `readiness-check` quedan en PASS.

## Criterios BLOCK

- El agente modifica archivos del repo productivo.
- El agente usa tools no declaradas o adapters directos.
- Se habilita una API externa.
- Se exige Ollama o LM Studio para la suite base.
- Se implementan handoffs, supervisor o multiagente.
- Se persisten prompts, completions o secretos crudos.

## Riesgos

- El scoring del repositorio es heurístico y no reemplaza revisión humana ni SAST/SCA industrial.
- La priorización de riesgos es inicial y debe enriquecerse con métricas históricas y severidades calibradas.
- El prompt model-aware es preliminar y no debe usarse como evidencia única de cierre técnico.

## Veredicto

`FUNC-SPRINT-52` queda apto para cierre si `pytest`, `agent run repo-analysis`, `eval run`, `validate all`, `miasi validate` y `readiness-check` quedan en PASS en el entorno del owner.
