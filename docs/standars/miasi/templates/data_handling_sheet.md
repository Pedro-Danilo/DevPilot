---
title: "Data Handling Sheet — tratamiento de datos"
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
# Data Handling Sheet — tratamiento de datos

## 1. Propósito

Documenta categorías de datos, sensibilidad, uso permitido, retención, acceso, transferencia a modelos y eliminación.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Cuando el agente maneja documentos, clientes, usuarios o repos privados.
- Antes de conectar modelos externos.
- Al diseñar RAG o memoria.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| data_categories | Categorías de datos. | public/internal/confidential/PII/secrets. |
| allowed_uses | Usos permitidos. | Qué puede hacer el agente. |
| forbidden_uses | Usos prohibidos. | Qué no puede hacer. |
| model_transfer_policy | Transferencia a modelos. | local only / external allowed. |
| retention | Retención. | TTL y borrado. |
| access_control | Control de acceso. | Roles/recursos. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| anonymization | Anonimización. | Si hay datos personales. |
| data_residency | Residencia. | Si hay requerimiento geográfico. |
| consent_basis | Base de consentimiento. | Si aplica. |

## 5. Ejemplo completo

```yaml
data_sheet_id: data.devpilot.repo_analysis
data_categories:
  public: ["README", "docs públicos"]
  internal: ["source code local"]
  forbidden: [".env", "tokens", "customer PII"]
allowed_uses: ["análisis local", "resúmenes técnicos", "reportes internos"]
forbidden_uses: ["subir secretos", "enviar PII a APIs externas"]
model_transfer_policy:
  local_models: allowed
  external_models: only_public_or_redacted
retention:
  reports_days: 180
  traces_days: 90
access_control:
  roles: [developer, maintainer]
```

## 6. Criterios de revisión

- Datos clasificados.
- Transferencia a modelos controlada.
- Retención definida.
- Secretos prohibidos.
- Acceso limitado.

## 7. Criterios de rechazo o bloqueo

- No clasifica datos.
- Permite secretos en prompts.
- Sin retención.
- Sin borrado.
- APIs externas sin redacción.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 6 — Datos, memoria y RAG | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 7 — Seguridad | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 19 — Retiro | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| data_classified | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| model_transfer_controlled | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| retention_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| secrets_forbidden | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| access_control_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
