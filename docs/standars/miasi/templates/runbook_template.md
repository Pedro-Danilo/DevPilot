---
title: "Runbook Template — guía operativa de agente"
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
# Runbook Template — guía operativa de agente

## 1. Propósito

Define cómo operar, validar, monitorear, detener, recuperar y depurar un agente en un entorno controlado.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Antes de operación controlada.
- Cuando otro responsable debe poder ejecutar el sistema.
- Para incidentes y soporte.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| runbook_id | Identificador. | Relacionado con agente/sistema. |
| startup_procedure | Cómo iniciar. | Comandos y prechecks. |
| health_checks | Cómo verificar salud. | Comandos/métricas. |
| shutdown_procedure | Cómo detener. | Seguro y reversible. |
| rollback_procedure | Cómo revertir. | Pasos concretos. |
| troubleshooting | Problemas frecuentes. | Síntomas y acciones. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| on_call | Responsables. | Si hay operación continua. |
| dashboards | Paneles. | URLs o rutas. |
| known_limits | Límites conocidos. | Capacidad, costos, fallos. |

## 5. Ejemplo completo

```yaml
runbook_id: runbook.devpilot.local
agent_id: agent.devpilot.orchestrator
startup_procedure:
  - python -m devpilot --check-inputs
  - python -m devpilot --dry-run
health_checks:
  - pytest -q
  - python -m devpilot eval
shutdown_procedure:
  - stop worker process
  - archive latest traces
rollback_procedure:
  - git checkout last-approved-release
  - restore sqlite backup
troubleshooting:
  - symptom: "policy blocks all writes"
    action: "validate policy card and environment"
```

## 6. Criterios de revisión

- Puede ejecutarse por otra persona.
- Incluye prechecks.
- Incluye rollback.
- Incluye troubleshooting.
- No requiere conocimiento tácito.

## 7. Criterios de rechazo o bloqueo

- Solo describe teoría.
- No tiene comandos.
- No tiene rollback.
- No tiene salud/monitoreo.
- No indica cómo detener.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 15 — Despliegue controlado | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 16 — Operación y monitoreo | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 17 — Gestión de incidentes | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| runbook_exists | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| startup_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| health_checks_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| rollback_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| shutdown_safe | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
