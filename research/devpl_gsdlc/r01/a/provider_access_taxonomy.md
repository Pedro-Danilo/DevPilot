---
doc_id: "DEVPL-GSDLC-R01-A-PROVIDER-ACCESS-TAXONOMY"
title: "DEVPL-GSDLC-R01-A — Provider, model and access-route taxonomy"
status: "implemented-controlled/pending-windows-validation"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-14"
backlog_id: "DEVPL-GSDLC-R01"
micro_sprint: "DEVPL-GSDLC-R01-A"
source_repo: "repo_DevPilot_Local_342_DEVPL_GSDLC_00_PROGRAM_ACTIVATION_REBASELINE.zip"
source_git_commit: "90d4f4b76168aab1f2e74c86213cf7d4e4831186"
research_basis: "deep-research-report_DEVPL-GSDLC-R01-A-PROMP.md"
---

# Provider, model and access-route taxonomy

## 1. Purpose

Materializa, sin re-investigar ni habilitar runtime, la taxonomía definida por la investigación profunda R01-A. La regla central es:

```text
model != provider != access route != model gateway adapter != agent runtime/orchestrator != skill/tool/protocol
```

Origen/nacionalidad es metadata. Nunca constituye por sí solo una regla `allow/block`.

## 2. Baseline interpretado

R01-A parte de repo342. La investigación establece que DevPilot ya contiene contratos de ModelAdapter/provider routing, providers locales Ollama/LM Studio, política de APIs externas, Agent Runtime gobernado, tool policy, handoffs y MCP fake/read-only; **existencia de contrato no equivale a enablement**. Mock/local continúa como default y los providers externos permanecen disabled-by-default.

## 3. Model classes obligatorias

| Clase | Uso DevPilot | Regla R01-A |
|---|---|---|
| reasoning/general | requirements, arquitectura, revisión | catalogar; fitness se mide en R01-D |
| coding | generación/reparación/test | catalogar; no declarar ganador |
| multimodal/vision | análisis de UI/diagramas/evidencia visual | solo cuando el workload lo justifique |
| embeddings | RAG/indexación | preferencia inicial por rutas locales cuando sean viables |
| reranking/retrieval | calidad de recuperación | SKU exacto puede permanecer unresolved |
| tool/function-capable | herramientas tipadas | compatibilidad declarada no sustituye benchmark |

## 4. Access routes

| Route | Auth | Cost model | Region | Support semantics | Estado R01-A |
|---|---|---|---|---|---|
| local-native | local/runtime-specific | hardware local | host local | runtime/model-specific | candidato; disabled-by-default |
| local-openai-compatible | localhost/runtime-specific | hardware local | host local | compatibilidad de protocolo, no equivalencia semántica | candidato; localhost-only |
| remote-openai-compatible | route-specific | provider-specific | provider-specific | sintaxis compatible; comportamiento por medir | bloqueado hasta R01-B + enablement |
| vendor-api | provider-specific | provider-specific | provider-specific | soporte oficial por provider | bloqueado hasta R01-B + enablement |
| broker/aggregator | broker-specific | broker + downstream | broker + provider final | privacidad/routing dependen del endpoint final | research-only |
| cloud-catalog | cloud IAM | deployment-specific | deployment-specific | modelo/provider/deployment separados | bloqueado hasta R01-B |
| official-programmatic-subscription/client | provider-specific | distinguir seat/subscription de API | provider-specific | solo cuando exista soporte programático oficial | consumer-session piggyback prohibido |

## 5. Runtime local

- **Ollama**: ruta local y superficie OpenAI-compatible documentada; valor principal: localhost/offline y desacoplamiento del vendor.
- **LM Studio**: serving local compatible y operación offline; tool/MCP no se habilita automáticamente.
- **vLLM**: serving de alto throughput con superficie OpenAI-compatible; requiere perfil de hardware/sandbox específico.

La compatibilidad OpenAI no demuestra equivalencia de tool calling, structured output, context ceiling o errores. Esos puntos se miden en R01-C/D.

## 6. Global candidate set

El snapshot machine-readable conserva candidatos P0/P1/P2 de la investigación: OpenAI, Anthropic, Google, Mistral, xAI, DeepSeek, Qwen/Alibaba, Kimi/Moonshot, GLM/Z.ai, MiniMax, IBM Granite, Cohere, Meta Llama, Microsoft Phi, runtimes locales y OpenRouter como broker experimental. Prioridad significa **digno de evaluación**, no aprobado para producción.

## 7. Agentic boundary

```text
Model / Provider
    -> Access Route / Adapter
        -> Model Gateway (routing, capabilities, budget, fallback)
            -> Agent Runtime (planning, orchestration, handoffs, lifecycle)
                -> Skills / Tools / MCP / typed capabilities
```

`PolicyEngine`, approvals, CostGuard y ejecución tipada permanecen autoridades determinísticas. Un SDK agente oficial de un proveedor no convierte al Model Gateway en runtime agente ni autoriza tools externas.

## 8. No-go preservados

- external provider runtime: disabled;
- browser/DOM/cookie session piggyback: prohibited;
- real secrets in repo: prohibited;
- connector write / arbitrary plugin execution / remote execution: unchanged and disabled;
- model nationality as policy shortcut: prohibited;
- universal model winner without DevPilot workloads: prohibited.

## 9. Source and uncertainty policy

Toda afirmación cambiante debe resolver `source + retrieved_at + target_region + freshness_class`. Cuando una fuente no permite establecer license, processing region, target-region availability o exact model ID, el valor se conserva como `unknown/conditional`; R01-A no rellena huecos por inferencia.
