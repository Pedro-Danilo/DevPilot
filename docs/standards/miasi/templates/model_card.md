---
title: "Model Card — ficha operativa de modelo y proveedor"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
updated: "2026-05-31"
related_documents:
  - "01_modelo_ingenieria_sistemas_agenticos.md"
  - "02_arquitectura_referencia.md"
  - "03_agentic_sdlc.md"
  - "04_estandares_tecnicos_transversales.md"
related_labs: "LAB-AI-001..LAB-AI-080"
related_projects:
  - "DevPilot Local"
  - "FreelanceOps Agent"
  - "MicroVenta Agent"
doc_type: "template"
scope: "engineering-model-template"
audience:
  - "arquitectos de sistemas agénticos"
  - "desarrolladores de agentes IA"
  - "responsables de seguridad, evaluación y operación"
---
# Model Card — ficha operativa de modelo y proveedor

## 1. Propósito

Documenta el uso de un modelo o familia de modelos: proveedor, modalidad mock/local/API, capacidades, límites, costos, privacidad, fallback y evaluación mínima.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Al agregar un nuevo ModelAdapter.
- Al habilitar un modelo local.
- Al permitir una API externa.
- Al comparar rutas mock/local/API.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| model_id | Identificador del modelo. | Nombre/version del modelo. |
| provider | Proveedor o runtime. | mock/ollama/lmstudio/openai/gemini/etc. |
| route | Ruta de ejecución. | mock/local/external_api. |
| capabilities | Capacidades declaradas. | text, tools, structured_output, embeddings. |
| cost_policy | Política de costo. | zero/limited/budgeted. |
| data_policy | Tratamiento de datos. | Qué puede enviarse al modelo. |
| eval_baseline | Evaluación mínima. | Resultados o thresholds. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| fallbacks | Modelos de respaldo. | Cuando falle el proveedor principal. |
| rate_limits | Rate limits. | Para APIs externas. |
| context_window | Ventana de contexto. | Para planificación de prompts/RAG. |

## 5. Ejemplo completo

```yaml
model_id: ollama.qwen2.5-3b-instruct
provider: ollama
route: local
owner: AI_agents
status: draft
capabilities: ["text_generation", "basic_reasoning"]
api_keys_required: false
cost_policy:
  external_cost: 0
  budget_usd_monthly: 0
data_policy:
  allowed_data: ["docs publicos", "repos locales sin secretos"]
  forbidden_data: ["secretos", "PII sensible", "credenciales"]
eval_baseline:
  eval_id: eval.model_adapter.local.v1
  min_pass_rate: 0.80
fallbacks: ["mock.rules.v1"]
```

## 6. Criterios de revisión

- La ruta mock/local/API está clara.
- No se envían datos prohibidos.
- Existe baseline de evaluación.
- Costos y límites están declarados.
- Fallbacks están definidos.

## 7. Criterios de rechazo o bloqueo

- No declara política de datos.
- Requiere API key sin alternativa.
- No tiene cost guard.
- No tiene evaluación.
- Promete capacidades no verificadas.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 4 — Diseño agentic | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 8 — Diseño de evaluación | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 10 — Implementación | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 16 — Operación y monitoreo | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| model_route_declared | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| api_keys_optional_or_controlled | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| cost_policy_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| data_policy_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| model_eval_pass | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

## 10. Criterios de automatización futura en DevPilot Local

- Debe poder convertirse en formulario validable.
- Debe poder serializarse a YAML/JSON.
- Debe poder enlazarse con `run_id`, `agent_id`, `tool_id`, `eval_id` o `release_id`.
- Debe poder participar en un `readiness-check` automático.
- Debe conservar historial de cambios por Git.



## 11. Referencias base

- OpenAI Agents SDK — Agents, tools, handoffs, guardrails, tracing and human review. https://developers.openai.com/api/docs/guides/agents
- LangGraph durable execution, persistence and human-in-the-loop. https://docs.langchain.com/oss/python/langgraph/durable-execution
- Model Context Protocol Specification — resources, prompts and tools. https://modelcontextprotocol.io/specification/2025-06-18
- OpenTelemetry Semantic Conventions for GenAI systems and agents. https://opentelemetry.io/docs/specs/semconv/gen-ai/
- Microsoft Foundry Agent Evaluators. https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/agent-evaluators
- OWASP Top 10 for LLM Applications. https://owasp.org/www-project-top-10-for-large-language-model-applications/
- NIST AI Risk Management Framework. https://www.nist.gov/itl/ai-risk-management-framework
- NIST SSDF SP 800-218. https://csrc.nist.gov/pubs/sp/800/218/final
- SLSA — Supply-chain Levels for Software Artifacts. https://slsa.dev/
- CycloneDX Software Bill of Materials. https://cyclonedx.org/
