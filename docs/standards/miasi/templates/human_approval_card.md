---
title: "Human Approval Card — ficha de aprobación humana"
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
# Human Approval Card — ficha de aprobación humana

## 1. Propósito

Define el flujo de aprobación humana para acciones sensibles, incluyendo revisor, separación de funciones, TTL, evidencia, decisión y trazabilidad.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Cuando una acción requiere revisión humana.
- Antes de ejecutar acciones de alto riesgo.
- Al diseñar flujos HITL.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| approval_id | Identificador de aprobación. | Relacionado con run_id/action_id. |
| requested_action | Acción solicitada. | Descripción y recurso. |
| risk_level | Riesgo de la acción. | medium/high/critical. |
| requester | Solicitante. | Agente o usuario. |
| approver_role | Rol aprobador requerido. | maintainer/security/release. |
| ttl | Tiempo de validez. | Fecha/hora de expiración. |
| decision | Resultado. | approved/denied/expired/waiting. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| conditions | Condiciones de aprobación. | Tests, backups, dry-run. |
| rollback_plan | Plan de reversión. | Para acciones con side effects. |
| evidence_links | Evidencias. | Reportes, trazas, PRs. |

## 5. Ejemplo completo

```yaml
approval_id: approval.run_20260531_001
requested_action:
  action: write
  resource: docs/generated/release_notes.md
risk_level: medium
requester: agent.devpilot.release_agent
approver_role: maintainer
separation_of_duties: true
ttl: 2026-05-31T18:00:00Z
conditions:
  - pytest_passed
  - secret_scan_passed
  - dry_run_reviewed
decision: waiting
redaction:
  approval_token_logged: false
```

## 6. Criterios de revisión

- El aprobador tiene rol válido.
- El solicitante no aprueba su acción.
- TTL definido.
- Evidencia enlazada.
- Token redactado.

## 7. Criterios de rechazo o bloqueo

- Autoaprobación.
- Sin expiración.
- Sin evidencia.
- Token visible en logs.
- Aprueba acción destructiva sin rollback.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 13 — Human approval y policy-as-code | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 14 — CI/CD y release | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 15 — Despliegue controlado | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| approval_required_for_risky_action | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| separation_of_duties_enforced | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| ttl_valid | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| approval_trace_recorded | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| token_redacted | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
