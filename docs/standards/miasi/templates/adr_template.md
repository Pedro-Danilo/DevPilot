---
title: "ADR Template — decisión arquitectónica"
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
# ADR Template — decisión arquitectónica

## 1. Propósito

Registra decisiones arquitectónicas relevantes, su contexto, alternativas, decisión tomada, consecuencias y criterios de revisión.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Al decidir un patrón, proveedor, base de datos, modelo, política o arquitectura.
- Cuando una decisión afecta seguridad, costo u operación.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| adr_id | Identificador ADR. | ADR-NNNN. |
| context | Contexto y problema. | Qué se necesita decidir. |
| decision | Decisión tomada. | Opción seleccionada. |
| alternatives | Alternativas consideradas. | Con pros/contras. |
| consequences | Consecuencias. | Positivas, negativas, riesgos. |
| review_date | Fecha de revisión. | Cuándo revalidar. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| related_policies | Políticas relacionadas. | Si aplica. |
| migration_plan | Plan de migración. | Si reemplaza una decisión. |
| metrics | Métricas de éxito. | Para validar decisión. |

## 5. Ejemplo completo

```yaml
adr_id: ADR-0010
title: "Usar SQLite para memoria local inicial"
status: proposed
context: "DevPilot necesita memoria persistente local sin servicios externos."
alternatives:
  - name: JSON
    pros: [simple]
    cons: [concurrencia limitada]
  - name: SQLite
    pros: [transaccional, portable]
    cons: [requiere schema]
decision: "Usar SQLite para MVP local-first."
consequences:
  positive: ["sin costo", "portable", "testeable"]
  negative: ["no multiusuario industrial"]
review_date: 2026-07-01
```

## 6. Criterios de revisión

- Contexto claro.
- Alternativas reales.
- Consecuencias honestas.
- Estado definido.
- Fecha de revisión.

## 7. Criterios de rechazo o bloqueo

- Decisión sin alternativas.
- No declara consecuencias negativas.
- No versiona cambios.
- Se usa como justificación retroactiva sin evidencia.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 4 — Diseño agentic | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 6 — Datos/RAG/memoria | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 14 — CI/CD y release | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| adr_exists_for_major_decision | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| alternatives_considered | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| consequences_recorded | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| review_date_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
