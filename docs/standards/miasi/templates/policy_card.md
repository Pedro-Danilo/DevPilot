---
title: "Policy Card — ficha operativa de policy-as-code"
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
# Policy Card — ficha operativa de policy-as-code

## 1. Propósito

Define políticas declarativas para permitir, bloquear o requerir aprobación sobre acciones de agentes.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Al crear reglas de permisos.
- Al gobernar acciones con side effects.
- Al conectar entornos, usuarios, repos o herramientas.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| policy_id | Identificador de política. | Convención `policy.<dominio>.<control>`. |
| subjects | Sujetos cubiertos. | roles, usuarios, agentes. |
| actions | Acciones cubiertas. | read/write/execute/delete/network. |
| resources | Recursos cubiertos. | paths, APIs, repos, DBs. |
| decision_model | Modelo de decisión. | allow/block/require_approval. |
| default_decision | Decisión por defecto. | block o require_approval. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| exceptions | Excepciones temporales. | Con expiración y aprobador. |
| environment_rules | Reglas por ambiente. | local/test/ci/staging/prod. |
| audit_requirements | Eventos a auditar. | Para trazabilidad. |

## 5. Ejemplo completo

```yaml
policy_id: policy.devpilot.filesystem_actions
owner: AI_agents
status: draft
default_decision: block
subjects:
  roles: [developer, maintainer]
actions:
  allow:
    - {action: read, resources: ["docs/**", "src/**"], conditions: ["dry_run_any"]}
    - {action: write, resources: ["outputs/**"], conditions: ["dry_run_or_approved"]}
  block:
    - {action: delete, resources: ["**"], conditions: ["always"]}
    - {action: write, resources: [".env", ".git/**"], conditions: ["always"]}
  require_approval:
    - {action: execute, resources: ["scripts/**"]}
audit_requirements: [policy_decision, subject, action, resource, reason]
```

## 6. Criterios de revisión

- Default seguro.
- Reglas legibles.
- Acciones críticas bloqueadas o aprobadas.
- Ambientes diferenciados.
- Auditoría definida.

## 7. Criterios de rechazo o bloqueo

- Default allow.
- Excepciones sin expiración.
- Producción editable sin aprobación.
- No registra decisión.
- Reglas ambiguas.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 7 — Diseño de seguridad | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 13 — Human approval y policy-as-code | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 15 — Despliegue controlado | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| policy_default_safe | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| critical_actions_controlled | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| environment_rules_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| audit_required | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| policy_tests_pass | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
