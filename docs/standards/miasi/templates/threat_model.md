---
title: "Threat Model — modelo de amenazas para agentes IA"
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
# Threat Model — modelo de amenazas para agentes IA

## 1. Propósito

Estructura amenazas, activos, superficies de ataque, límites de confianza, escenarios y mitigaciones para sistemas agénticos.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Al diseñar agentes con herramientas.
- Cuando hay RAG, memoria, APIs externas o acciones con side effects.
- Antes de producción controlada.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| assets | Activos protegidos. | Datos, credenciales, repos, infraestructura. |
| trust_boundaries | Límites de confianza. | Usuario/agente/modelo/tool/API. |
| attack_surfaces | Superficies de ataque. | Prompts, tools, documentos, APIs. |
| threats | Amenazas. | Escenarios con impacto. |
| mitigations | Mitigaciones. | Controles específicos. |
| validation_tests | Pruebas de validación. | Tests o ejercicios. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| abuse_cases | Casos de abuso. | Para threat modeling avanzado. |
| data_flow_diagram | Diagrama de flujo de datos. | Mermaid/C4. |
| red_team_notes | Notas de pruebas adversarias. | Cuando aplique. |

## 5. Ejemplo completo

```yaml
assets: ["repo source code", "env files", "trace logs", "customer data"]
trust_boundaries:
  - user_to_agent
  - agent_to_tool
  - tool_to_filesystem
attack_surfaces:
  - prompt_input
  - retrieved_documents
  - tool_arguments
threats:
  - id: T-001
    name: prompt_injection_via_document
    impact: high
    mitigation: ["document source allowlist", "instruction hierarchy", "output validation"]
validation_tests:
  - tests/security/test_prompt_injection_docs.py
```

## 6. Criterios de revisión

- Activos y límites claros.
- Amenazas específicas.
- Mitigaciones verificables.
- Incluye prompt/tool/data threats.
- Tiene pruebas.

## 7. Criterios de rechazo o bloqueo

- Solo lista OWASP sin adaptación.
- No declara activos.
- No modela herramientas.
- No hay pruebas.
- No se actualiza con cambios.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 1 — Clasificación de riesgo | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 7 — Diseño de seguridad | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 12 — Pruebas de seguridad | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| threat_model_exists | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| assets_declared | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| trust_boundaries_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| critical_threats_mitigated | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| security_tests_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
