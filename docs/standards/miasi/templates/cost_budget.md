---
title: "Cost Budget — presupuesto y control de costos IA"
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
# Cost Budget — presupuesto y control de costos IA

## 1. Propósito

Define límites de costo, consumo, proveedor, alertas y estrategias de fallback para modelos, embeddings, APIs y servicios externos.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Antes de habilitar APIs externas.
- Al usar modelos pagos.
- Al crear flujos batch o autónomos.
- Antes de operación.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| budget_id | Identificador de presupuesto. | Por agente/proyecto/ambiente. |
| providers | Proveedores cubiertos. | OpenAI/Gemini/Mistral/etc. |
| monthly_limit | Límite mensual. | USD o moneda local. |
| per_run_limit | Límite por ejecución. | Tokens/costo/llamadas. |
| alerts | Alertas. | Umbrales y canal. |
| fallback_policy | Fallback. | mock/local/degrade. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| token_budget | Presupuesto de tokens. | Por modelo/flujo. |
| quota_reset | Reinicio de cuota. | Mensual/semanal. |
| approval_required_above | Aprobación por umbral. | Para costos altos. |

## 5. Ejemplo completo

```yaml
budget_id: cost.devpilot.external_api
owner: AI_agents
status: draft
providers:
  - openai
  - gemini
monthly_limit_usd: 10
per_run_limit_usd: 0.25
per_run_token_limit: 50000
alerts:
  - threshold_percent: 50
    action: warn
  - threshold_percent: 80
    action: require_approval
  - threshold_percent: 100
    action: block
fallback_policy:
  default: local_model
  emergency: mock_model
```

## 6. Criterios de revisión

- Límites cuantitativos.
- Fallback sin costo.
- Alertas antes del bloqueo.
- Aprobación por exceso.
- Métrica observable.

## 7. Criterios de rechazo o bloqueo

- Sin límite.
- Loops autónomos sin presupuesto.
- No hay fallback.
- API paga obligatoria.
- No registra costo por run.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 1 — Clasificación de riesgo | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 4 — Diseño agentic | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 16 — Operación y monitoreo | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| cost_budget_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| per_run_limit_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| fallback_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| cost_metrics_enabled | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| budget_exceed_blocks | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
