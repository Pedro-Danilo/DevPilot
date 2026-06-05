---
title: "Risk Register — registro de riesgos agénticos"
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
# Risk Register — registro de riesgos agénticos

## 1. Propósito

Consolida riesgos técnicos, operativos, de seguridad, costo, datos, cumplimiento y modelo para un agente o sistema agéntico.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Durante intake y clasificación de riesgo.
- Antes de despliegue.
- Al revisar incidentes o cambios críticos.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| risk_id | Identificador del riesgo. | RISK-NNN. |
| risk_statement | Descripción del riesgo. | Causa-evento-impacto. |
| likelihood | Probabilidad. | low/medium/high. |
| impact | Impacto. | low/medium/high/critical. |
| mitigation | Mitigación. | Control preventivo/correctivo. |
| owner | Responsable. | Rol o persona. |
| status | Estado. | open/mitigated/accepted/closed. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| detection | Cómo detectar. | Métrica/alerta/test. |
| residual_risk | Riesgo residual. | Después de mitigación. |
| review_frequency | Frecuencia de revisión. | Semanal/mensual/release. |

## 5. Ejemplo completo

```yaml
risk_id: RISK-012
risk_statement: "Si el agente ejecuta una herramienta de escritura sin aprobación, puede modificar artefactos no revisados."
likelihood: medium
impact: high
mitigation:
  - dry_run_default
  - policy_as_code_gate
  - human_approval_for_write
owner: security_reviewer
status: open
detection:
  - policy decision events
  - tests for execute=false
residual_risk: low
```

## 6. Criterios de revisión

- Riesgo formulado con claridad.
- Mitigación verificable.
- Owner asignado.
- Riesgo residual declarado.
- Relación con quality gates.

## 7. Criterios de rechazo o bloqueo

- Riesgos genéricos.
- Sin responsable.
- Sin mitigación.
- Aceptación sin justificación.
- No se actualiza tras incidentes.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 1 — Clasificación de riesgo | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 7 — Diseño de seguridad | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 18 — Mejora continua | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| risk_register_exists | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| high_risks_mitigated | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| owners_assigned | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| residual_risk_accepted_or_low | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
