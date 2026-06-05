---
title: "Agent Card — ficha operativa de agente IA"
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
# Agent Card — ficha operativa de agente IA

## 1. Propósito

Define el contrato operativo mínimo de un agente IA: propósito, autonomía, herramientas, modelos, memoria, políticas, evaluación, seguridad, observabilidad y despliegue.

Esta plantilla es un artefacto operativo MIASI. Debe completarse antes de que el agente, herramienta, componente o control relacionado avance hacia operación controlada. No sustituye pruebas, evaluación ni revisión de seguridad; las hace trazables.

## 2. Cuándo usarla

- Al crear un nuevo agente.
- Al promover un agente de prototipo a operación controlada.
- Al auditar agentes existentes.
- Antes de exponer herramientas con efectos secundarios.

## 3. Campos obligatorios

| Campo | Descripción | Evidencia mínima |
| --- | --- | --- |
| id | Identificador único y estable. | Valor único versionado. |
| owner | Responsable técnico o funcional. | Nombre o rol responsable. |
| status | Estado documental u operativo. | draft/reviewed/approved/deprecated. |
| scope | Alcance explícito del artefacto. | Incluye inclusiones y exclusiones. |
| agent_id | Identificador estable del agente. | Convención `agent.<dominio>.<nombre>`. |
| purpose | Objetivo de negocio o técnico del agente. | Problema que resuelve y límites. |
| autonomy_level | Nivel A0-A7 según MIASI. | Justificación del nivel. |
| model_strategy | Ruta mock/local/API y fallback. | ModelAdapter declarado. |
| tools | Herramientas permitidas. | Tool Cards asociadas. |
| evaluation_plan | Métricas y datasets de evaluación. | Eval Card asociada. |
| security_policy | Controles aplicables. | Policy Card y gates. |

## 4. Campos opcionales

| Campo | Descripción | Cuándo usarlo |
| --- | --- | --- |
| tags | Etiquetas de clasificación. | Útil para búsqueda y filtros. |
| external_references | Referencias a estándares o documentación externa. | Cuando el artefacto dependa de tecnología, estándar o proveedor. |
| rag_profile | Uso de RAG y fuentes. | Cuando el agente consulta documentos. |
| memory_profile | Memoria de corto/largo plazo. | Cuando persiste estado. |
| deployment_target | Entorno de ejecución. | Para agentes operacionales. |

## 5. Ejemplo completo

```yaml
agent_id: agent.devpilot.repo_reviewer
name: RepoReviewerAgent
owner: AI_agents
autonomy_level: A3
status: draft
purpose: "Analizar un repositorio local y producir un informe de calidad, riesgos y próximos pasos."
scope:
  includes: ["lectura de archivos", "análisis estático", "generación de reporte"]
  excludes: ["modificación automática", "push remoto", "borrado de archivos"]
model_strategy:
  default_route: mock_or_local
  adapters: [MockModelAdapter, OllamaAdapter]
  api_keys_required: false
tools:
  - tool.filesystem.read_text_file
  - tool.tests.pytest_dry_run
  - tool.reports.write_markdown_report
security_policy:
  dry_run_default: true
  destructive_actions_allowed: false
  human_approval_required_for: ["write", "execute", "network"]
evaluation_plan: eval.devpilot.repo_reviewer.v1
observability:
  trace_required: true
  log_redaction: true
readiness: prototype
```

## 6. Criterios de revisión

- El propósito es verificable y no ambiguo.
- El nivel de autonomía tiene controles acordes.
- Todas las herramientas tienen Tool Card.
- Existe plan de evaluación y observabilidad.
- Se declaran límites y exclusiones.

## 7. Criterios de rechazo o bloqueo

- No declara herramientas o modelos.
- Permite acciones destructivas sin aprobación.
- No tiene evaluación mínima.
- No registra trazas.
- Confunde asistente conversacional con agente ejecutor.

## 8. Relación con Agentic SDLC

| Fase SDLC | Uso de la plantilla |
| --- | --- |
| Fase 4 — Diseño agentic | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 7 — Diseño de seguridad | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 8 — Diseño de evaluación | Debe completarse, revisarse o actualizarse en esta fase. |
| Fase 15 — Despliegue controlado | Debe completarse, revisarse o actualizarse en esta fase. |

## 9. Relación con quality gates

| Quality gate | Condición PASS | Condición FAIL/BLOCK |
| --- | --- | --- |
| agent_contract_complete | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| tools_declared | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| policy_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| eval_plan_defined | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |
| observability_enabled | Existe evidencia verificable, versionada y revisada. | Falta evidencia, hay ambigüedad crítica o el riesgo no está mitigado. |

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
