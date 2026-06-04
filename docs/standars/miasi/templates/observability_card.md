---
title: "Observability Card — ficha de observabilidad agéntica"
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
# Observability Card — ficha de observabilidad agéntica

## 1. Propósito

Define eventos, trazas, logs, métricas, retención y dashboards para un agente o flujo agéntico.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Al diseñar un agente operacional.
- Al instrumentar tool calls.
- Al preparar monitoreo y diagnóstico.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| observability_id | Identificador del plan. | Convención `obs.<agente>`. |
| trace_events | Eventos trazados. | run_start, model_call, tool_call, policy_decision. |
| logs | Logs requeridos. | Niveles y redacción. |
| metrics | Métricas mínimas. | latency, errors, cost, tokens, pass_rate. |
| retention | Retención de datos. | Tiempo y ubicación. |
| redaction_policy | Redacción. | Secretos/PII. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| otel_mapping | Mapeo OpenTelemetry. | Si se exporta a OTel. |
| dashboards | Dashboards. | Paneles locales/remotos. |
| alerts | Alertas. | Umbrales operativos. |

## 5. Ejemplo completo

```yaml
observability_id: obs.devpilot.repo_reviewer
agent_id: agent.devpilot.repo_reviewer
trace_events: [run_start, model_call, tool_call, policy_decision, eval_result, run_end]
logs:
  levels: [INFO, WARNING, ERROR]
  redact: [secrets, tokens, pii]
metrics:
  - latency_ms
  - tool_error_rate
  - eval_pass_rate
  - policy_blocks
  - external_cost_usd
retention:
  traces_days: 90
  logs_days: 30
otel_mapping:
  enabled: true
  semconv: gen_ai
```

## 6. Criterios de revisión

- Cada acción crítica es observable.
- Logs no exponen secretos.
- Métricas operativas existen.
- Retención definida.
- Puede depurarse un incidente.

## 7. Criterios de rechazo o bloqueo

- Sin run_id.
- No registra tool calls.
- No registra policy decisions.
- Logs con secretos.
- No hay retención.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 9 — Diseño de observabilidad | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 16 — Operación y monitoreo | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 17 — Gestión de incidentes | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| trace_required | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| logs_redacted | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| metrics_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| retention_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| incident_debuggable | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
