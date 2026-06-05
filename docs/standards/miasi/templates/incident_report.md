---
title: "Incident Report — reporte de incidente agéntico"
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
# Incident Report — reporte de incidente agéntico

## 1. Propósito

Estandariza el registro de incidentes de agentes: impacto, línea de tiempo, causa raíz, contención, remediación y aprendizajes.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Cuando un agente produce salida riesgosa.
- Cuando falla una política o herramienta.
- Cuando hay fuga de datos, costo anómalo o interrupción.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| incident_id | Identificador único. | Convención `INC-YYYYMMDD-NNN`. |
| severity | Severidad. | SEV-1..SEV-4. |
| impact | Impacto. | Usuarios, datos, costos, operación. |
| timeline | Línea de tiempo. | Eventos con hora. |
| root_cause | Causa raíz. | Técnica/proceso/modelo/herramienta. |
| containment | Acciones de contención. | Qué se hizo para detener impacto. |
| corrective_actions | Acciones correctivas. | Patches, controles, pruebas. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| related_run_ids | Runs relacionados. | Para trazas. |
| customer_comms | Comunicación externa. | Si impacta usuarios. |
| postmortem_date | Fecha de postmortem. | Para incidentes severos. |

## 5. Ejemplo completo

```yaml
incident_id: INC-20260531-001
severity: SEV-3
status: open
summary: "El agente generó un reporte con una ruta sensible no redactada."
impact:
  users: 1
  data_exposure: internal_path_only
  external_exposure: false
timeline:
  - time: 2026-05-31T10:00:00Z
    event: detection
  - time: 2026-05-31T10:10:00Z
    event: agent_disabled
root_cause: "Regla de redacción incompleta para rutas locales."
containment: ["desactivar publicación", "regenerar reporte"]
corrective_actions: ["agregar test de redacción", "actualizar policy card"]
```

## 6. Criterios de revisión

- Severidad justificada.
- Timeline claro.
- Causa raíz accionable.
- Contención documentada.
- Acciones correctivas verificables.

## 7. Criterios de rechazo o bloqueo

- Culpa genérica al modelo.
- Sin timeline.
- Sin acción correctiva.
- No enlaza trazas.
- No actualiza tests o políticas.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 17 — Gestión de incidentes | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 18 — Mejora continua | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 19 — Retiro o desactivación | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| incident_logged | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| impact_assessed | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| containment_done | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| root_cause_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| corrective_actions_tracked | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
