---
title: "Production Readiness Checklist — checklist de readiness productivo"
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
# Production Readiness Checklist — checklist de readiness productivo

## 1. Propósito

Consolida los criterios mínimos para decidir si un agente puede avanzar a operación controlada o producción industrial.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Antes de despliegue controlado.
- Antes de habilitar execute=true.
- Antes de exponer a usuarios reales.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| readiness_id | Identificador de revisión. | Por agente/release. |
| scope | Alcance del release. | Agente, herramientas, datos. |
| quality_gates | Gates requeridos. | Tests/evals/security/observability. |
| approval_status | Estado de aprobación. | reviewed/approved/blocked. |
| known_risks | Riesgos aceptados. | Con owner y fecha. |
| go_no_go_decision | Decisión final. | go/no-go/conditional. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| pilot_plan | Plan piloto. | Usuarios/tiempo/métricas. |
| rollback_drill | Ensayo de rollback. | Evidencia. |
| operational_slo | SLO inicial. | Disponibilidad/latencia/errores. |

## 5. Ejemplo completo

```yaml
readiness_id: readiness.devpilot.v0.1.0
scope: "RepoReviewerAgent en entorno local controlado"
quality_gates:
  tests: pass
  evals: pass
  secret_scan: pass
  sast_sbom: pass
  policy_as_code: pass
  human_approval: pass
  observability: pass
known_risks:
  - risk_id: RISK-012
    status: mitigated
approval_status: reviewed
go_no_go_decision: conditional_go
conditions:
  - "solo dry-run"
  - "sin repos productivos"
```

## 6. Criterios de revisión

- Todos los gates relevantes tienen evidencia.
- Riesgos residuales aceptados.
- Decisión go/no-go explícita.
- Condiciones de operación claras.
- Rollback definido.

## 7. Criterios de rechazo o bloqueo

- Sin evals.
- Sin seguridad.
- Sin trazas.
- Riesgos críticos abiertos.
- Producción sin aprobación.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 14 — CI/CD y release | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 15 — Despliegue controlado | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 16 — Operación y monitoreo | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| all_required_gates_pass | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| no_critical_open_risks | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| rollback_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| approval_recorded | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| go_no_go_decision_recorded | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
