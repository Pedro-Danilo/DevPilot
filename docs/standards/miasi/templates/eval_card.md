---
title: "Eval Card — ficha operativa de evaluación de agente"
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
# Eval Card — ficha operativa de evaluación de agente

## 1. Propósito

Define datasets, métricas, thresholds, evaluadores y criterios de regresión para un agente o capacidad agéntica.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Antes de promover un agente.
- Al cambiar modelo, prompt, herramienta o política.
- Al crear regresión de comportamiento.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| eval_id | Identificador de evaluación. | Convención `eval.<agente>.<versión>`. |
| target | Agente, herramienta o flujo evaluado. | agent_id/tool_id/rag_id. |
| dataset | Casos de prueba. | Ubicación y versión. |
| metrics | Métricas evaluadas. | task_completion/tool_accuracy/etc. |
| thresholds | Umbrales PASS. | Valores mínimos. |
| regression_policy | Política de regresión. | Qué bloquea release. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| judge_model | Modelo juez. | Solo si hay ruta local/API controlada. |
| human_review_sample | Muestra revisada por humano. | Para casos críticos. |
| golden_outputs | Salidas esperadas. | Cuando aplica comparación exacta. |

## 5. Ejemplo completo

```yaml
eval_id: eval.devpilot.repo_reviewer.v1
target: agent.devpilot.repo_reviewer
owner: AI_agents
status: draft
dataset:
  path: tests/fixtures/evals/repo_reviewer_cases.jsonl
  cases: 30
metrics:
  task_completion: {min: 0.85}
  tool_selection_accuracy: {min: 0.90}
  policy_compliance: {min: 1.00}
  groundedness: {min: 0.85}
regression_policy:
  block_on_policy_failure: true
  block_on_secret_leak: true
  max_latency_ms_p95: 5000
judge_model:
  route: mock_or_local
```

## 6. Criterios de revisión

- Métricas corresponden al riesgo.
- Thresholds son explícitos.
- Dataset está versionado.
- Hay regresión.
- Policy compliance es bloqueante.

## 7. Criterios de rechazo o bloqueo

- Sin dataset.
- Solo evaluación subjetiva.
- No bloquea fugas de secretos.
- No evalúa herramientas.
- No hay baseline anterior.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 8 — Diseño de evaluación | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 11 — Evaluación offline | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 14 — CI/CD y release | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 18 — Mejora continua | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| eval_dataset_versioned | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| metrics_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| thresholds_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| regression_policy_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| eval_pass | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
