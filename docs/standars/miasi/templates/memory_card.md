---
title: "Memory Card — ficha operativa de memoria agéntica"
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
# Memory Card — ficha operativa de memoria agéntica

## 1. Propósito

Documenta qué memoria usa un agente, qué persiste, por cuánto tiempo, con qué permisos, cómo se borra y cómo se evalúa.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Cuando un agente persiste preferencias, estado o historial.
- Al usar SQLite/PostgreSQL/vector stores.
- Al diseñar memoria por usuario/proyecto.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| memory_id | Identificador de memoria. | Convención `memory.<dominio>.<tipo>`. |
| memory_type | Tipo de memoria. | short_term/long_term/vector/event/log. |
| schema | Estructura persistida. | Campos y tipos. |
| retention_policy | Tiempo y condiciones de retención. | TTL o reglas. |
| privacy_policy | Datos permitidos/prohibidos. | PII, secretos, datos sensibles. |
| delete_policy | Cómo borrar memoria. | Comando/proceso. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| summarization_policy | Reglas de resumen. | Para reducir contexto. |
| isolation_key | Llave de aislamiento. | Usuario/proyecto/tenant. |
| migration_plan | Migración de schema. | Cuando cambia el modelo de datos. |

## 5. Ejemplo completo

```yaml
memory_id: memory.devpilot.project_state
memory_type: long_term
owner: AI_agents
status: draft
backend: sqlite
schema:
  project_id: string
  decision: string
  artifact_path: string
  created_at: datetime
retention_policy:
  default_ttl_days: 180
  purge_on_project_archive: true
privacy_policy:
  allowed: ["decisiones técnicas", "rutas de artefactos"]
  forbidden: ["secretos", "tokens", "datos personales innecesarios"]
delete_policy:
  command: devpilot memory purge --project <id>
isolation_key: project_id
```

## 6. Criterios de revisión

- Persistencia justificada.
- Datos sensibles excluidos.
- Existe borrado verificable.
- Aislamiento definido.
- Schema versionable.

## 7. Criterios de rechazo o bloqueo

- Memoria ilimitada sin propósito.
- Guarda secretos.
- No permite borrado.
- No aísla por usuario/proyecto.
- No evalúa exactitud de memoria.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 6 — Diseño de datos, memoria y RAG | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 7 — Diseño de seguridad | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 16 — Operación y monitoreo | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 19 — Retiro | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| memory_purpose_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| retention_policy_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| privacy_policy_enforced | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| delete_policy_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| memory_eval_pass | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
