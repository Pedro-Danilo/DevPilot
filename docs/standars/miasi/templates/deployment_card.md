---
title: "Deployment Card — ficha de despliegue controlado"
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
# Deployment Card — ficha de despliegue controlado

## 1. Propósito

Define ambiente, artefactos, gates, rollback, monitoreo y responsabilidades para desplegar un agente o sistema agéntico.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Antes de pasar a staging o producción controlada.
- Al generar un release.
- Al auditar entornos.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| deployment_id | Identificador del despliegue. | Versión y ambiente. |
| target_environment | Ambiente destino. | local/test/ci/staging/prod. |
| artifact_refs | Artefactos desplegados. | Commit, package, image, docs. |
| pre_deploy_gates | Gates previos. | Tests, evals, SAST, approvals. |
| rollback_plan | Plan de rollback. | Comando/procedimiento. |
| monitoring_plan | Monitoreo post despliegue. | Métricas y alertas. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| feature_flags | Flags de activación. | Para releases graduales. |
| data_migrations | Migraciones. | Si cambian esquemas. |
| release_notes | Notas de release. | Para usuarios/operación. |

## 5. Ejemplo completo

```yaml
deployment_id: deploy.devpilot.local.v0.1.0
target_environment: local_controlled
artifact_refs:
  commit: abc123
  package: devpilot-0.1.0
pre_deploy_gates: [pytest_passed, eval_passed, secret_scan_passed, policy_approved]
rollback_plan:
  command: git checkout previous-stable
  data_backup_required: true
monitoring_plan:
  observe_for_minutes: 60
  metrics: [latency_ms, error_rate, policy_blocks]
release_notes: docs/releases/0.1.0.md
```

## 6. Criterios de revisión

- Gates previos cerrados.
- Rollback probado o razonable.
- Artefactos identificables.
- Monitoreo definido.
- Ambiente correcto.

## 7. Criterios de rechazo o bloqueo

- Despliegue sin rollback.
- Ambiente productivo sin aprobación.
- Artefactos no versionados.
- No hay monitoreo.
- No hay checklist pre-producción.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 14 — CI/CD y release | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 15 — Despliegue controlado | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 16 — Operación y monitoreo | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| pre_deploy_gates_pass | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| rollback_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| artifacts_versioned | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| monitoring_enabled | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| release_approved | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
